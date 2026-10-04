from fastapi.testclient import TestClient

from app.db import get_session
from app.deps import require_api_key
from app.main import create_app
from app.modules.core.models import Jurisdiction


def _client_with_session(db_session) -> TestClient:
    app = create_app()

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[require_api_key] = lambda: 1
    return TestClient(app)


def test_list_requires_api_key():
    client = TestClient(create_app())
    assert client.get("/v1/jurisdictions").status_code == 401


def test_list_returns_jurisdictions(db_session):
    db_session.add(Jurisdiction(code="AE", name="United Arab Emirates"))
    db_session.flush()
    client = _client_with_session(db_session)
    resp = client.get("/v1/jurisdictions")
    assert resp.status_code == 200
    assert {"code": "AE", "name": "United Arab Emirates"} in [
        {"code": j["code"], "name": j["name"]} for j in resp.json()
    ]


def test_get_unknown_id_is_404(db_session):
    client = _client_with_session(db_session)
    resp = client.get("/v1/jurisdictions/999999")
    assert resp.status_code == 404
    assert resp.json() == {"detail": "jurisdiction not found"}
