import io
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.db import get_session
from app.deps import get_llm_provider, get_principal
from app.main import create_app
from app.modules.llm.ask import AskError, parse_intent
from app.modules.llm.models import LlmInteraction
from app.modules.llm.provider import Completion, LlmError, Message, MistralProvider
from app.modules.llm.summary import SummaryService
from app.modules.saas.models import OrganisationAccount
from app.modules.saas.service import Principal
from app.modules.scoring.repository import card_to_dict
from app.modules.scoring.scorer import Scorer
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.france_uae import seed

D = date(2026, 10, 1)
PROFILE = ScoringProfile(
    parent="FR", flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR"))
)


class FakeProvider:
    model = "fake-model"

    def __init__(self, *outputs: str | Exception) -> None:
        self.outputs = list(outputs)
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message], *, json_mode: bool = False) -> Completion:
        self.calls.append(messages)
        out = self.outputs.pop(0)
        if isinstance(out, Exception):
            raise out
        return Completion(out, self.model, 5, 100, 50)


@pytest.fixture
def seeded(db_session):
    seed(db_session)
    db_session.flush()
    return db_session


@pytest.fixture
def cards(seeded):
    return [card_to_dict(c) for c in Scorer(seeded).rank(PROFILE, ["AE", "FR"], D)]


def _royalty_cit_cite(cards) -> int:
    ae = cards[0]
    line = next(
        x for x in ae["flow_breakdown"] if x["leg"] == "AE corporate tax" and x["rate"] == "9.000"
    )
    return line["citations"][0]


def _grounded(cards) -> str:
    c = _royalty_cit_cite(cards)
    return (
        f"United Arab Emirates ranks first with 85.45 out of 100, ahead of France at 83.69. "
        f"Royalties routed through the UAE bear 9% corporate tax there [{c}]. "
        "The French CFC exposure needs professional review."
    )


def _audit(session):
    return session.query(LlmInteraction).order_by(LlmInteraction.id).all()


def test_grounded_summary_passes(seeded, cards):
    s = SummaryService(seeded, FakeProvider(_grounded(cards))).summarize(
        cards, org_id=None, input_ref="t"
    )
    assert s.status == "pass" and s.model == "fake-model"
    rows = _audit(seeded)
    assert [r.grounding_status for r in rows] == ["pass"]
    assert rows[0].prompt_tokens == 100 and rows[0].cost is None


@pytest.mark.parametrize(
    ("bad", "error"),
    [
        ("United Arab Emirates ranks first with 85.45. Royalties bear 7.5% tax [{c}].", "7.5"),
        ("United Arab Emirates ranks first with 85.45 [99999].", "citation [99999]"),
        (
            "United Arab Emirates ranks first with 85.45; royalties bear 9% tax.",
            "percentage without",
        ),
        ("Vanuatu would rank higher than the United Arab Emirates [{c}].", "VU"),
        ("The UAE was removed from the FATF grey list [{c}].", "FATF"),
        ("The 2027-01-01 reform changes the 85.45 score [{c}].", "date 2027-01-01"),
        ("Flags indicate no treaty between France and the United Arab Emirates [{c}].",
         "absence stated as fact"),
    ],
)
def test_hallucination_is_caught_then_repaired(seeded, cards, bad, error):
    c = _royalty_cit_cite(cards)
    provider = FakeProvider(bad.format(c=c), _grounded(cards))
    s = SummaryService(seeded, provider).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "repaired"
    first, second = _audit(seeded)
    assert first.grounding_status == "rejected"
    assert any(error in e for e in first.grounding_errors), first.grounding_errors
    assert second.grounding_status == "repaired"
    # the repair request quotes the validation errors back to the model
    assert "failed validation" in provider.calls[1][-1].content


def test_twice_ungrounded_falls_back_to_template(seeded, cards):
    bad = "The UAE charges 3% on everything."
    s = SummaryService(seeded, FakeProvider(bad, bad)).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "template" and s.model is None
    assert "85.45" in s.text and "3%" not in s.text
    assert [r.grounding_status for r in _audit(seeded)] == ["rejected", "rejected"]


def test_provider_error_falls_back_to_template(seeded, cards):
    s = SummaryService(seeded, FakeProvider(LlmError("timeout"))).summarize(
        cards, org_id=None, input_ref="t"
    )
    assert s.status == "template"
    assert [r.grounding_status for r in _audit(seeded)] == ["error"]


def test_no_provider_uses_template_without_audit(seeded, cards):
    s = SummaryService(seeded, None).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "template" and "United Arab Emirates ranks #1" in s.text
    assert _audit(seeded) == []


# --- NL query parsing --------------------------------------------------------------------------


def test_parse_intent_validates():
    known = {"FR", "AE"}
    ok = parse_intent(
        '{"intent":"withholding_tax","source":"fr","recipient":"AE","income_category":"royalty",'
        '"holding_pct":null,"on_date":"2025-01-01"}',
        known,
        D,
    )
    assert (ok.source, ok.income_category, ok.on_date) == ("FR", "ROYALTY", date(2025, 1, 1))
    for raw in (
        "not json",
        '{"intent":"unsupported","reason":"VAT question"}',
        '{"intent":"withholding_tax","source":"FR","recipient":"LU","income_category":"DIVIDEND"}',
        '{"intent":"withholding_tax","source":"FR","recipient":"AE","income_category":"VAT"}',
        '{"intent":"withholding_tax","source":"FR","recipient":"AE","income_category":"DIVIDEND",'
        '"holding_pct":150}',
    ):
        with pytest.raises(AskError):
            parse_intent(raw, known, D)


def _client(session, provider) -> TestClient:
    org = OrganisationAccount(name="llm org")
    session.add(org)
    session.flush()
    app = create_app()

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[get_principal] = lambda: Principal(org_id=org.id, role="admin")
    app.dependency_overrides[get_llm_provider] = lambda: provider
    return TestClient(app)


def test_ask_endpoint_runs_the_engine(seeded):
    intent = json.dumps(
        {"intent": "withholding_tax", "source": "FR", "recipient": "AE",
         "income_category": "DIVIDEND", "holding_pct": 100, "on_date": "2024-06-30"}
    )
    resp = _client(seeded, FakeProvider(intent)).post(
        "/v1/ask", json={"question": "What WHT applies to French dividends paid to a UAE parent?"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["result"]["final_rate"] == "0.000"
    assert body["result"]["withheld_at_payment"] == "25.000"
    assert "final rate after relief: 0.000%" in body["answer"]
    assert [r.kind for r in _audit(seeded)] == ["nl_parse"]


def test_ask_unsupported_and_disabled(seeded):
    unsupported = '{"intent":"unsupported","reason":"not a withholding question"}'
    resp = _client(seeded, FakeProvider(unsupported)).post(
        "/v1/ask", json={"question": "What is the VAT rate in France?"}
    )
    assert resp.status_code == 422 and "withholding" in resp.json()["detail"]
    assert _audit(seeded)[0].grounding_status == "rejected"
    off = _client(seeded, None).post("/v1/ask", json={"question": "anything at all"})
    assert off.status_code == 503


def test_recommendation_with_summary(seeded):
    resp = _client(seeded, None).post(
        "/v1/analyze/holding-recommendation",
        json={
            "profile": {
                "parent": "FR",
                "flows": [
                    {"income_category": "DIVIDEND", "source": "FR"},
                    {"income_category": "ROYALTY", "source": "FR"},
                ],
            },
            "on_date": "2026-10-01",
            "candidates": ["AE", "FR"],
            "summarize": True,
        },
    )
    assert resp.status_code == 200
    summary = resp.json()["summary"]
    assert summary["status"] == "template" and summary["note"] == "no LLM provider configured"


# --- Mistral HTTP client -----------------------------------------------------------------------


def test_mistral_provider_request_shape(monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout):
        seen["url"] = req.full_url
        seen["auth"] = req.get_header("Authorization")
        seen["body"] = json.loads(req.data)
        payload = {
            "model": "mistral-large-2411",
            "choices": [{"message": {"content": "{}"}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3},
        }
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    p = MistralProvider("secret", "mistral-large-latest", "https://api.example/v1/", 5)
    out = p.complete([Message("user", "hi")], json_mode=True)
    assert seen["url"] == "https://api.example/v1/chat/completions"
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["response_format"] == {"type": "json_object"}
    assert seen["body"]["temperature"] == 0
    assert (out.model, out.prompt_tokens, out.completion_tokens) == ("mistral-large-2411", 12, 3)


def test_cfc_flag_restated_with_its_citations_passes(seeded, cards):
    from app.modules.llm.summary import build_payload

    ae = build_payload(cards, {})["ranked_candidates"][0]
    cfc = next(f for f in ae["flags"] if "CFC" in f["message"])
    assert cfc["citations"]
    tags = "".join(f"[{i}]" for i in cfc["citations"])
    text = (
        "United Arab Emirates ranks first with 85.45. Under CGI art. 209 B / 238 A the French "
        f"CFC rule may apply because 9.000% is below the 15.00% threshold {tags}."
    )
    s = SummaryService(seeded, FakeProvider(text)).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "pass", _audit(seeded)[0].grounding_errors


def test_citation_lists_are_normalised_and_checked(seeded, cards):
    from app.modules.llm.grounding import normalize_citations

    assert normalize_citations("x [1, 2; 3] y []. z") == "x [1][2][3] y. z"
    c = _royalty_cit_cite(cards)
    good = f"United Arab Emirates ranks first with 85.45; royalties bear 9% tax [{c}, {c}]."
    s = SummaryService(seeded, FakeProvider(good)).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "pass" and f"[{c}][{c}]" in s.text
    bad = f"United Arab Emirates ranks first with 85.45; royalties bear 9% tax [{c}, 99999]."
    s = SummaryService(seeded, FakeProvider(bad, bad)).summarize(cards, org_id=None, input_ref="t")
    assert s.status == "template"
    assert any("[99999]" in e for e in _audit(seeded)[1].grounding_errors)


@pytest.mark.parametrize(
    ("sentence", "ok"),
    [
        ("Flags indicate no treaty between QA and CY.", False),
        ("There are no substance rules for Cyprus.", False),
        ("No treaty between QA and CY is recorded in the database.", True),
        ("No substance-rule data is recorded for Cyprus.", True),
        ("The treaty caps royalties.", True),
    ],
)
def test_absence_claims_must_say_not_recorded(sentence, ok):
    from app.modules.llm.grounding import ABSENCE, QUALIFIED

    assert (not ABSENCE.search(sentence) or bool(QUALIFIED.search(sentence))) is ok
