import pytest
from fastapi.testclient import TestClient

from app.db import get_session
from app.deps import get_principal
from app.main import create_app
from app.modules.recommender.builder import InvalidAnswers, build_profile
from app.modules.saas.models import OrganisationAccount
from app.modules.saas.service import Principal

ANSWERS = {
    "size": "sme",
    "activity": "saas_ip",
    "flows": ["ROYALTY", "DIVIDEND"],
    "sources": ["FR"],
    "parent": "FR",
}


@pytest.fixture
def seeded(seeded_session):
    return seeded_session


def _client(session, org_name="org a") -> TestClient:
    org = OrganisationAccount(name=org_name)
    session.add(org)
    session.flush()
    app = create_app()

    def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[get_principal] = lambda: Principal(org_id=org.id, role="admin")
    return TestClient(app)


def test_builder_maps_answers(seeded):
    answers, profile = build_profile(seeded, ANSWERS)
    assert answers.flows == ("DIVIDEND", "ROYALTY")  # normalised order
    assert profile.substance_capacity == "medium"
    assert [(f.income_category, f.source) for f in profile.flows] == [
        ("DIVIDEND", "FR"),
        ("ROYALTY", "FR"),
    ]


@pytest.mark.parametrize(
    "bad",
    [
        {**ANSWERS, "size": "gigantic"},
        {**ANSWERS, "flows": ["CAPITAL_GAIN"]},  # offered but disabled
        {**ANSWERS, "flows": []},
        {**ANSWERS, "sources": []},
        {**ANSWERS, "parent": "ZZ"},
        {k: v for k, v in ANSWERS.items() if k != "activity"},
    ],
)
def test_builder_rejects_bad_answers(seeded, bad):
    with pytest.raises(InvalidAnswers):
        build_profile(seeded, bad)


def test_questions_endpoint(seeded):
    body = _client(seeded).get("/v1/onboarding/questions").json()
    assert [q["code"] for q in body["questions"]] == ["size", "activity", "flows"]
    assert {"code": "AE", "name": "United Arab Emirates"} in body["jurisdictions"]


def test_profile_then_recommendation(seeded):
    client = _client(seeded)
    resp = client.post("/v1/profiles", json={"answers": ANSWERS})
    assert resp.status_code == 201
    profile_id = resp.json()["id"]
    assert client.get(f"/v1/profiles/{profile_id}").json()["derived"]["parent"] == "FR"

    rec = client.post(
        "/v1/analyze/holding-recommendation",
        json={"profile_id": profile_id, "on_date": "2026-10-01", "candidates": ["AE", "FR"]},
    )
    assert rec.status_code == 200, rec.text
    assert rec.json()["scorecards"][0]["jurisdiction"] == "AE"


def test_profile_is_org_scoped(seeded):
    resp = _client(seeded, "org a").post("/v1/profiles", json={"answers": ANSWERS})
    other = _client(seeded, "org b")
    assert other.get(f"/v1/profiles/{resp.json()['id']}").status_code == 404


def test_profile_validation_error(seeded):
    resp = _client(seeded).post("/v1/profiles", json={"answers": {**ANSWERS, "size": "x"}})
    assert resp.status_code == 422


def test_recommendation_needs_exactly_one_profile_input(seeded):
    resp = _client(seeded).post(
        "/v1/analyze/holding-recommendation", json={"on_date": "2026-10-01"}
    )
    assert resp.status_code == 422


def test_browse_jurisdiction(seeded):
    body = _client(seeded).get(
        "/v1/browse/jurisdictions/ae", params={"on_date": "2024-06-30"}
    ).json()
    assert body["code"] == "AE"
    cit = next(r for r in body["domestic_rules"] if r["tax_type"] == "CIT")
    assert [b["rate"] for b in cit["brackets"]] == ["0.000", "9.000"]
    assert body["holding_regime"]["min_subject_to_tax_rate"] == "9.000"
    assert {item["list_code"] for item in body["lists"]} == {"EU_AML_HIGH_RISK"}
    treaty = next(t for t in body["treaties"] if t["counterparties"] == ["FR"])
    assert treaty["in_force"]
    assert {r["income_category"] for r in treaty["rates"]} == {"DIVIDEND", "INTEREST", "ROYALTY"}


def test_browse_unknown_is_404(seeded):
    assert _client(seeded).get("/v1/browse/jurisdictions/ZZ").status_code == 404


def test_lists_and_evidence(seeded):
    client = _client(seeded)
    lists = client.get("/v1/lists", params={"on_date": "2025-06-01"}).json()
    etnc = next(item for item in lists if item["code"] == "FR_ETNC")
    assert [m["jurisdiction"] for m in etnc["members"]] == ["PA", "VU"]
    ev = client.get(f"/v1/evidence/{etnc['citation']}").json()
    assert ev["document_url"].startswith("https://www.legifrance.gouv.fr")
    assert client.get("/v1/evidence/999999").status_code == 404


def test_browse_corporate_tax_map(seeded):
    body = _client(seeded).get("/v1/browse/corporate-tax", params={"on_date": "2026-10-06"}).json()
    rows = {r["code"]: r for r in body["jurisdictions"]}
    assert rows["AE"]["rate"] == "9.000" and rows["AE"]["min_rate"] == "0.000"
    assert rows["AE"]["bracketed"] is True and rows["AE"]["citation"]
    assert rows["FR"]["rate"] == "25.000" and rows["FR"]["min_rate"] is None
    assert rows["IE"]["rate"] == "12.500"  # trading rate, not the 25% passive-income rules
    assert rows["PA"]["rate"] is None  # no corporate tax rule recorded
    fr = rows["FR"]["summary"]
    assert fr["wht"]["DIVIDEND"]["max"] and fr["participation_exemption"]["dividends"] is True
    assert fr["treaties_in_force"] > 50
    assert "EU_TAX_ANNEX_I" in {x["code"] for x in rows["PA"]["summary"]["lists"]}
