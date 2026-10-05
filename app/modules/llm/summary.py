"""Job 2 (spec §5): ScoreCards → cited prose. The model narrates; it never ranks or computes."""

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.llm.grounding import GroundingResult, validate
from app.modules.llm.models import LlmInteraction
from app.modules.llm.provider import LlmError, LlmProvider, Message

PROMPT_VERSION = "summary-v1"
TOP_N = 3

SYSTEM = """You write a short briefing for a tax professional about a holding-jurisdiction \
ranking produced by a deterministic engine. You receive the engine output as JSON.

Rules — breaking any of them gets your text rejected:
1. Use ONLY facts and numbers present in the JSON. Never compute, round differently, estimate \
or add outside knowledge (no rates, dates, lists or countries that are not in the JSON).
2. After every sentence that states a rate, a list status, a treaty or a rule, put the \
supporting citation ids from the JSON in square brackets, e.g. [12] or [3][18].
3. Mention points flagged "interpretation_required": true as needing professional review.
4. Do not recommend; describe what the figures show. Plain prose, 120–220 words, no headings, \
no bullet lists, no markdown."""


@dataclass(frozen=True)
class Summary:
    text: str
    status: str  # "pass" | "repaired" | "template"
    model: str | None
    citations: tuple[int, ...]
    note: str | None = None


def build_payload(cards: list[dict[str, Any]], names: dict[str, str]) -> dict[str, Any]:
    complete = [c for c in cards if c["complete"]][:TOP_N]
    return {
        "score_scale": 100,
        "data_asof": cards[0]["data_asof"] if cards else None,
        "ranked_candidates": [
            {
                "rank": c["rank"],
                "jurisdiction": c["jurisdiction"],
                "name": names.get(c["jurisdiction"], c["jurisdiction"]),
                "overall_score": c["overall_score"],
                "factors": {
                    k: {"score": f["score"], "weight": f["weight"], "citations": f["citations"]}
                    for k, f in c["factors"].items()
                },
                "flow_breakdown": c["flow_breakdown"],
                "guardrails": [g["message"] for g in c["guardrail_flags"]],
                "flags": [
                    {
                        "message": f["message"],
                        "interpretation_required": f["interpretation_required"],
                    }
                    for f in {
                        (f["code"], f["message"]): f
                        for fs in c["factors"].values()
                        for f in fs["flags"]
                    }.values()
                ],
            }
            for c in complete
        ],
        "incomplete_candidates": [
            {
                "jurisdiction": c["jurisdiction"],
                "name": names.get(c["jurisdiction"], c["jurisdiction"]),
            }
            for c in cards
            if not c["complete"]
        ],
    }


def payload_citations(payload: dict[str, Any]) -> set[int]:
    cites: set[int] = set()
    for c in payload["ranked_candidates"]:
        for f in c["factors"].values():
            cites.update(f["citations"])
        for line in c["flow_breakdown"]:
            cites.update(line["citations"])
    return cites


def template_summary(payload: dict[str, Any]) -> str:
    """Deterministic fallback: same facts, fixed wording."""
    ranked = payload["ranked_candidates"]
    if not ranked:
        return "No candidate could be scored with the data recorded for this date."
    parts = []
    for c in ranked:
        cites = sorted({i for f in c["factors"].values() for i in f["citations"]})
        tag = "".join(f"[{i}]" for i in cites[:6])
        scores = ", ".join(
            f"{k.replace('_', ' ')} {f['score']}" for k, f in c["factors"].items()
        )
        parts.append(
            f"{c['name']} ranks #{c['rank']} with {c['overall_score']} out of 100 "
            f"({scores}).{(' ' + tag) if tag else ''}"
        )
        review = [f["message"] for f in c["flags"] if f["interpretation_required"]]
        if review:
            label = f"Points needing professional review for {c['name']}: "
            parts.append(label + "; ".join(review))
        if c["guardrails"]:
            parts.append(" ".join(c["guardrails"]))
    if payload["incomplete_candidates"]:
        names = ", ".join(c["name"] for c in payload["incomplete_candidates"])
        parts.append(f"Not scored for lack of recorded data: {names}.")
    return " ".join(parts)


class SummaryService:
    def __init__(self, session: Session, provider: LlmProvider | None) -> None:
        self.session = session
        self.provider = provider

    def summarize(
        self, cards: list[dict[str, Any]], *, org_id: int | None, input_ref: str
    ) -> Summary:
        jurisdictions = {j.code: j.name for j in JurisdictionRepository(self.session).list()}
        payload = build_payload(cards, jurisdictions)
        cites = payload_citations(payload)
        in_input = {
            c["jurisdiction"]: c["name"]
            for c in (*payload["ranked_candidates"], *payload["incomplete_candidates"])
        }
        # Counterparties appear in flow legs (e.g. "FR→AE dividend"); they are input too.
        for c in payload["ranked_candidates"]:
            for line in c["flow_breakdown"]:
                for code in jurisdictions:
                    if code in line["leg"]:
                        in_input.setdefault(code, jurisdictions[code])

        if self.provider is None:
            return Summary(template_summary(payload), "template", None, tuple(sorted(cites)),
                           "no LLM provider configured")

        def check(text: str) -> GroundingResult:
            return validate(text, payload, cites, in_input, jurisdictions)

        messages = [
            Message("system", SYSTEM),
            Message("user", json.dumps(payload, ensure_ascii=False)),
        ]
        for attempt in (1, 2):
            try:
                out = self.provider.complete(messages)
            except LlmError as exc:
                self._audit(org_id, input_ref, attempt, None, "error", [str(exc)], [], None)
                break
            result = check(out.text)
            if result.ok:
                status = "pass" if attempt == 1 else "repaired"
            else:
                status = "rejected"
            self._audit(
                org_id, input_ref, attempt, out.text, status, list(result.errors),
                list(result.citations), out,
            )
            if result.ok:
                return Summary(out.text.strip(), status, out.model, result.citations)
            messages += [
                Message("assistant", out.text),
                Message(
                    "user",
                    "Your text failed validation:\n- "
                    + "\n- ".join(result.errors)
                    + "\nRewrite it following the rules; use only numbers and citation ids "
                    "present in the JSON.",
                ),
            ]
        return Summary(template_summary(payload), "template", None, tuple(sorted(cites)),
                       "AI narration rejected by the grounding validator")

    def _audit(
        self,
        org_id: int | None,
        input_ref: str,
        attempt: int,
        text: str | None,
        status: str,
        errors: list[str],
        citations: list[int],
        out: Any,
    ) -> None:
        self.session.add(
            LlmInteraction(
                org_id=org_id,
                kind="summary",
                input_ref=input_ref,
                model=out.model if out else getattr(self.provider, "model", "unknown"),
                prompt_version=PROMPT_VERSION,
                attempt=attempt,
                output=text,
                grounding_status=status,
                grounding_errors=errors,
                citations=citations,
                latency_ms=out.latency_ms if out else None,
                prompt_tokens=out.prompt_tokens if out else None,
                completion_tokens=out.completion_tokens if out else None,
            )
        )
        self.session.flush()
