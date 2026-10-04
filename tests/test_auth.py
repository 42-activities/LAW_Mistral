from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.deps import require_api_key
from app.modules.saas.models import ApiKey, OrganisationAccount
from app.modules.saas.security import generate_api_key, hash_api_key


def test_hash_is_deterministic():
    assert hash_api_key("abc") == hash_api_key("abc")
    assert len(hash_api_key("abc")) == 64


def _app_with_protected_route() -> FastAPI:
    app = FastAPI()

    @app.get("/protected")
    def protected(org_id: int = Depends(require_api_key)) -> dict[str, int]:
        return {"org_id": org_id}

    return app


def test_missing_key_is_401():
    client = TestClient(_app_with_protected_route())
    assert client.get("/protected").status_code == 401


def _client(db_session) -> TestClient:
    from app.db import get_session

    def _override():
        yield db_session

    app = _app_with_protected_route()
    app.dependency_overrides[get_session] = _override
    return TestClient(app)


def _add_key(db_session, active: bool) -> tuple[int, str]:
    org = OrganisationAccount(name="Acme Tax")
    db_session.add(org)
    db_session.flush()
    raw, key_hash = generate_api_key()
    db_session.add(ApiKey(org_id=org.id, key_hash=key_hash, active=active))
    db_session.flush()
    return org.id, raw


def test_valid_key_authenticates(db_session):
    org_id, raw = _add_key(db_session, active=True)
    resp = _client(db_session).get("/protected", headers={"X-API-Key": raw})
    assert resp.status_code == 200
    assert resp.json() == {"org_id": org_id}


def test_unknown_key_is_401(db_session):
    resp = _client(db_session).get("/protected", headers={"X-API-Key": "does-not-exist"})
    assert resp.status_code == 401


def test_inactive_key_is_401(db_session):
    _, raw = _add_key(db_session, active=False)
    resp = _client(db_session).get("/protected", headers={"X-API-Key": raw})
    assert resp.status_code == 401
