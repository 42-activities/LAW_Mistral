from fastapi.testclient import TestClient

from app.db import get_session
from app.deps import require_api_key
from app.main import create_app
from app.modules.seed.france_uae import seed


def _client(db_session) -> TestClient:
    seed(db_session)
    db_session.flush()
    app = create_app()

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[require_api_key] = lambda: 1
    return TestClient(app)


def test_analyze_requires_api_key():
    client = TestClient(create_app())
    body = {
        "source": "FR",
        "recipient": "AE",
        "income_category": "DIVIDEND",
        "on_date": "2024-06-30",
    }
    assert client.post("/v1/analyze/withholding-tax", json=body).status_code == 401


def test_withholding_tax_endpoint(db_session):
    resp = _client(db_session).post(
        "/v1/analyze/withholding-tax",
        json={
            "source": "FR",
            "recipient": "AE",
            "income_category": "DIVIDEND",
            "on_date": "2024-06-30",
            "holding_pct": 100,
            "holding_days": 730,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["complete"] is True
    assert body["domestic_rate"] == "25.000"
    assert body["withheld_at_payment"] == "25.000"
    assert body["final_rate"] == "0.000"  # exclusive residence taxation
    assert body["citations"]
    assert "refund_cash_flow" in {f["code"] for f in body["flags"]}


def test_unknown_jurisdiction_is_404(db_session):
    resp = _client(db_session).post(
        "/v1/analyze/withholding-tax",
        json={
            "source": "FR",
            "recipient": "ZZ",
            "income_category": "DIVIDEND",
            "on_date": "2024-06-30",
        },
    )
    assert resp.status_code == 404


def test_jurisdiction_risk_endpoint(db_session):
    resp = _client(db_session).get(
        "/v1/analyze/jurisdiction-risk", params={"jurisdiction": "AE", "on_date": "2023-06-01"}
    )
    assert resp.status_code == 200
    lists = {m["list_code"] for m in resp.json()["memberships"]}
    assert lists == {"FATF_GREY", "EU_AML_HIGH_RISK"}


def test_flow_endpoint(db_session):
    resp = _client(db_session).post(
        "/v1/analyze/flow",
        json={
            "income_category": "ROYALTY",
            "source": "FR",
            "holding": "AE",
            "parent": "FR",
            "on_date": "2024-06-30",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_leakage_pct"] == "9.000"
    assert [leg["kind"] for leg in body["legs"]] == ["wht", "cit", "wht"]
