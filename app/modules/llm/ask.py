"""Job 1 (spec §5): free-form question → structured QueryIntent → the same deterministic engine.

The model chooses *what* to ask; the engine decides *what the answer is*. The prose returned is
rendered from the engine result by a fixed template, so it cannot contain anything unsourced.
"""

import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.modules.core.repository import JurisdictionRepository
from app.modules.engine.types import WhtResult
from app.modules.engine.withholding import WithholdingEngine
from app.modules.llm.models import LlmInteraction
from app.modules.llm.provider import LlmError, LlmProvider, Message

PROMPT_VERSION = "nl-parse-v1"
CATEGORIES = ("DIVIDEND", "INTEREST", "ROYALTY")

SYSTEM = """You translate a tax professional's question into a JSON query for a withholding-tax \
engine. Do not answer the question. Reply with one JSON object only:

{"intent": "withholding_tax", "source": "<payer's jurisdiction code>", \
"recipient": "<recipient's jurisdiction code>", "income_category": "DIVIDEND|INTEREST|ROYALTY", \
"holding_pct": <number or null>, "on_date": "<YYYY-MM-DD or null>"}

or, if the question is not about withholding tax on a cross-border dividend, interest or \
royalty payment between two of the listed jurisdictions:

{"intent": "unsupported", "reason": "<short reason>"}

Use only these jurisdiction codes: """


class AskError(ValueError):
    pass


@dataclass(frozen=True)
class QueryIntent:
    source: str
    recipient: str
    income_category: str
    holding_pct: Decimal | None
    on_date: date


def parse_intent(raw: str, known: set[str], default_date: date) -> QueryIntent:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AskError("the model did not return JSON") from exc
    if not isinstance(data, dict):
        raise AskError("the model did not return a JSON object")
    if data.get("intent") != "withholding_tax":
        raise AskError(str(data.get("reason") or "question not supported"))
    source, recipient = str(data.get("source", "")).upper(), str(data.get("recipient", "")).upper()
    category = str(data.get("income_category", "")).upper()
    if source not in known or recipient not in known:
        raise AskError("question names a jurisdiction that is not covered")
    if category not in CATEGORIES:
        raise AskError("income category must be dividend, interest or royalty")
    holding: Decimal | None = None
    if data.get("holding_pct") is not None:
        try:
            holding = Decimal(str(data["holding_pct"]))
        except InvalidOperation as exc:
            raise AskError("holding percentage is not a number") from exc
        if not Decimal("0") <= holding <= Decimal("100"):
            raise AskError("holding percentage out of range")
    on = default_date
    if data.get("on_date"):
        try:
            on = date.fromisoformat(str(data["on_date"]))
        except ValueError as exc:
            raise AskError("date is not YYYY-MM-DD") from exc
    return QueryIntent(source, recipient, category, holding, on)


def render(r: WhtResult, names: dict[str, str]) -> str:
    """Fixed-wording prose from an engine result."""
    s, t = names.get(r.source, r.source), names.get(r.recipient, r.recipient)
    cat = r.income_category.lower()
    cites = "".join(f"[{c}]" for c in r.citations)
    if not r.complete:
        reason = "; ".join(f.message for f in r.flags) or "data not recorded"
        return f"No figure can be given for a {cat} paid from {s} to {t} on {r.on_date}: {reason}."
    parts = [
        f"For a {cat} paid by a {s} company to a {t} recipient on {r.on_date}, "
        f"the {s} domestic rate is {r.domestic_rate}%."
    ]
    if r.effective_domestic_rate != r.domestic_rate:
        parts.append(f"A list-triggered rate of {r.effective_domestic_rate}% applies instead.")
    if r.treaty_cap is not None:
        parts.append(f"Under {r.treaty_name} the cap is {r.treaty_cap}%.")
    parts.append(
        f"Withheld at payment: {r.withheld_at_payment}%; final rate after relief: {r.final_rate}%."
    )
    return " ".join(parts) + (f" {cites}" if cites else "")


class AskService:
    def __init__(self, session: Session, provider: LlmProvider) -> None:
        self.session = session
        self.provider = provider
        self.tokens = 0  # tokens of the last model call, for metering

    def ask(
        self, question: str, *, org_id: int | None, default_date: date
    ) -> tuple[QueryIntent, WhtResult, str]:
        jurisdictions = {j.code: j.name for j in JurisdictionRepository(self.session).list()}
        listing = ", ".join(f"{c} ({n})" for c, n in jurisdictions.items())
        messages = [Message("system", SYSTEM + listing), Message("user", question)]
        try:
            out = self.provider.complete(messages, json_mode=True)
            self.tokens = (out.prompt_tokens or 0) + (out.completion_tokens or 0)
        except LlmError as exc:
            self._audit(org_id, None, "error", [str(exc)], None)
            raise AskError("the language model is unavailable") from exc
        try:
            intent = parse_intent(out.text, set(jurisdictions), default_date)
        except AskError as exc:
            self._audit(org_id, out.text, "rejected", [str(exc)], out)
            raise
        self._audit(org_id, out.text, "pass", [], out)
        result = WithholdingEngine(self.session).compute(
            intent.source, intent.recipient, intent.income_category, intent.on_date,
            intent.holding_pct,
        )
        return intent, result, render(result, jurisdictions)

    def _audit(
        self, org_id: int | None, text: str | None, status: str, errors: list[str], out: Any
    ) -> None:
        self.session.add(
            LlmInteraction(
                org_id=org_id,
                kind="nl_parse",
                model=out.model if out else self.provider.model,
                prompt_version=PROMPT_VERSION,
                output=text,
                grounding_status=status,
                grounding_errors=errors,
                citations=[],
                latency_ms=out.latency_ms if out else None,
                prompt_tokens=out.prompt_tokens if out else None,
                completion_tokens=out.completion_tokens if out else None,
            )
        )
        self.session.flush()
