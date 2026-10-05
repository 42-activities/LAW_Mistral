from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.dialects.postgresql import Range

from app.db import get_session
from app.deps import get_principal
from app.main import create_app
from app.modules.core.repository import JurisdictionRepository
from app.modules.recommender.models import Scorecard, ScoringRun
from app.modules.risk.models import ListMembership
from app.modules.risk.repository import ListDefinitionRepository
from app.modules.saas.models import OrganisationAccount
from app.modules.saas.service import Principal
from app.modules.scoring.repository import card_to_dict
from app.modules.scoring.scorer import Scorer, normalise_weights
from app.modules.scoring.types import ProfileFlow, ScoringProfile
from app.modules.seed.france_uae import seed
from app.modules.source.models import SourceDocument, SourceEvidence

D = date(2026, 10, 1)

PROFILE = ScoringProfile(
    parent="FR",
    flows=(ProfileFlow("DIVIDEND", "FR"), ProfileFlow("ROYALTY", "FR")),
    holding_pct=Decimal("100"),
    holding_months=24,
    substance_capacity="medium",
)


@pytest.fixture
def seeded(db_session):
    seed(db_session)
    db_session.flush()
    return db_session


def _cards(session, candidates=("AE", "FR", "VU", "PA"), weights=None, profile=PROFILE):
    return {c.jurisdiction: c for c in Scorer(session).rank(profile, list(candidates), D, weights)}


def codes(flags):
    return {f.code for f in flags}


def test_france_uae_snapshot(seeded):
    cards = _cards(seeded)
    ae = cards["AE"]
    assert ae.complete
    # dividend leakage 0, royalty 9 → average 4.5 → 100 − 9 = 91
    assert ae.factors["tax_efficiency"].score == Decimal("91.00")
    assert ae.factors["compliance"].score == Decimal("100.00")  # off FATF/EU AML lists by 2026
    assert ae.factors["treaty_breadth"].score == Decimal("100.00")
    # −30 substance not recorded, −40 French CFC (9% < 60% × 25% = 15%)
    assert ae.factors["substance_burden"].score == Decimal("30.00")
    assert "cfc_exposure" in codes(ae.factors["substance_burden"].flags)
    # 0.45×91 + 0.2×100 + 0.2×100 + 0.15×30
    assert ae.overall_score == Decimal("85.45")
    assert ae.citations

    fr = cards["FR"]
    # FR as its own holding: dividend 1.25 (95% exemption), royalty 25 → avg 13.125 → 73.75
    assert fr.factors["tax_efficiency"].score == Decimal("73.75")
    assert fr.factors["substance_burden"].score == Decimal("70.00")  # no CFC on itself
    assert ae.rank < fr.rank


def test_incomplete_candidates_rank_last(seeded):
    cards = _cards(seeded)
    for code in ("VU", "PA"):  # no CIT data recorded
        assert not cards[code].complete and cards[code].overall_score is None
    ranks = sorted(cards.values(), key=lambda c: c.rank)
    assert [c.complete for c in ranks] == [True, True, False, False]
    assert [c.jurisdiction for c in ranks[2:]] == ["PA", "VU"]  # tie broken by code


def test_reproducible(seeded):
    a = [card_to_dict(c) for c in Scorer(seeded).rank(PROFILE, ["AE", "FR"], D)]
    b = [card_to_dict(c) for c in Scorer(seeded).rank(PROFILE, ["FR", "AE", "AE"], D)]
    assert a == b


def test_weights_normalised_and_validated():
    w = normalise_weights({"tax_efficiency": Decimal("9"), "compliance": Decimal("1")})
    assert w["tax_efficiency"] == Decimal("0.9000") and w["treaty_breadth"] == Decimal("0")
    with pytest.raises(ValueError):
        normalise_weights({"bogus": Decimal("1")})
    with pytest.raises(ValueError):
        normalise_weights({"compliance": Decimal("-1")})
    with pytest.raises(ValueError):
        normalise_weights({})


def test_reweighting_changes_ranking(seeded):
    only_substance = {"substance_burden": Decimal("1")}
    cards = _cards(seeded, ("AE", "FR"), only_substance)
    assert cards["FR"].rank == 1  # FR has no CFC penalty


def _ev(session) -> int:
    doc = SourceDocument(
        title="t", url="https://example.test/l", retrieved_at=datetime.now(UTC), content_hash="h"
    )
    session.add(doc)
    session.flush()
    ev = SourceEvidence(document_id=doc.id, quoted_text="q", review_status="human_verified")
    session.add(ev)
    session.flush()
    return ev.id


def _list(session, jurisdiction, list_code, classification):
    defs = ListDefinitionRepository(session)
    j = JurisdictionRepository(session).get_by_code(jurisdiction)
    session.add(
        ListMembership(
            list_definition_id=defs.get(list_code).id,
            jurisdiction_id=j.id,
            classification=classification,
            source_evidence_id=_ev(session),
            valid_period=Range(date(2026, 1, 1), None, bounds="[)"),
        )
    )
    session.flush()


def test_guardrail_fatf_black_caps_score(seeded):
    _list(seeded, "AE", "FATF_BLACK", "call_for_action")
    ae = _cards(seeded, ("AE",))["AE"]
    assert ae.overall_score == Decimal("20")
    assert "guardrail_fatf_black" in codes(ae.guardrail_flags)
    assert ae.factors["compliance"].score == Decimal("0.00")


def test_guardrail_etnc_for_counterparty(seeded):
    _list(seeded, "AE", "FR_ETNC", "full_measures")
    ae = _cards(seeded, ("AE",))["AE"]
    assert "guardrail_etnc_counterparty" in codes(ae.guardrail_flags)
    assert ae.overall_score <= Decimal("20")


def test_etnc_not_a_guardrail_when_france_is_not_a_counterparty(seeded):
    _list(seeded, "FR", "FR_ETNC", "full_measures")  # synthetic: FR is not ETNC for itself
    profile = ScoringProfile(parent="AE", flows=(ProfileFlow("DIVIDEND", "AE"),))
    fr = _cards(seeded, ("FR",), profile=profile)["FR"]
    assert fr.guardrail_flags == ()


def _client(session) -> TestClient:
    org = OrganisationAccount(name="test org")
    session.add(org)
    session.flush()
    app = create_app()

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[get_principal] = lambda: Principal(org_id=org.id, role="admin")
    return TestClient(app)


BODY = {
    "profile": {
        "parent": "FR",
        "flows": [
            {"income_category": "DIVIDEND", "source": "FR"},
            {"income_category": "ROYALTY", "source": "FR"},
        ],
    },
    "on_date": "2026-10-01",
    "candidates": ["AE", "FR"],
}


def test_recommendation_endpoint_persists_run(seeded):
    resp = _client(seeded).post("/v1/analyze/holding-recommendation", json=BODY)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["weight_set"] == "default-v1"
    assert [c["jurisdiction"] for c in body["scorecards"]] == ["AE", "FR"]
    assert body["scorecards"][0]["overall_score"] == "85.45"
    run = seeded.get(ScoringRun, body["scoring_run_id"])
    assert run.engine_version == "1.0.0"
    assert seeded.query(Scorecard).filter_by(scoring_run_id=run.id).count() == 2


def test_recommendation_custom_weights_and_errors(seeded):
    client = _client(seeded)
    resp = client.post(
        "/v1/analyze/holding-recommendation",
        json={**BODY, "weights": {"substance_burden": 1}},
    )
    assert resp.status_code == 200 and resp.json()["scorecards"][0]["jurisdiction"] == "FR"
    bad = client.post(
        "/v1/analyze/holding-recommendation", json={**BODY, "weights": {"bogus": 1}}
    )
    assert bad.status_code == 422
    missing = client.post(
        "/v1/analyze/holding-recommendation", json={**BODY, "candidates": ["ZZ"]}
    )
    assert missing.status_code == 404
