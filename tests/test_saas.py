from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import get_session
from app.deps import get_llm_provider
from app.main import create_app
from app.modules.saas import service
from app.modules.saas.models import AuditEvent, OrganisationAccount, Plan, UsageEvent, UserSession
from app.modules.saas.security import hash_password, password_problem, verify_password

PASSWORD = "correct horse battery"
REC = {
    "profile": {"parent": "FR", "flows": [{"income_category": "DIVIDEND", "source": "FR"}]},
    "on_date": "2026-10-01",
    "candidates": ["AE"],
}


@pytest.fixture
def env(seeded_session):
    org = OrganisationAccount(name="Acme")
    other = OrganisationAccount(name="Other")
    seeded_session.add_all([org, other])
    seeded_session.flush()
    admin = service.create_user(
        seeded_session, org_id=org.id, email="Admin@Acme.test", name="A", role="admin",
        password=PASSWORD, actor_id=None,
    )
    app = create_app()

    def _override():
        yield seeded_session

    app.dependency_overrides[get_session] = _override
    app.dependency_overrides[get_llm_provider] = lambda: None
    return TestClient(app), seeded_session, org, other, admin


def _login(client, email="admin@acme.test", password=PASSWORD):
    resp = client.post("/v1/auth/login", json={"email": email, "password": password})
    return resp


def _bearer(client, **kw):
    resp = _login(client, **kw)
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['token']}"}


def test_password_hashing():
    h = hash_password(PASSWORD)
    assert h.startswith("scrypt$") and PASSWORD not in h
    assert verify_password(PASSWORD, h) and not verify_password("wrong", h)
    assert hash_password(PASSWORD) != h  # salted
    assert password_problem("short") and password_problem(PASSWORD) is None


def test_login_me_logout(env):
    client, session, org, _, _ = env
    headers = _bearer(client)  # email is case-insensitive
    me = client.get("/v1/auth/me", headers=headers).json()
    assert me["role"] == "admin" and me["organisation"]["name"] == "Acme"
    assert me["plan"]["code"] == "standard"
    assert client.post("/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/v1/auth/me", headers=headers).status_code == 401
    actions = [e.action for e in session.scalars(select(AuditEvent).order_by(AuditEvent.id))]
    assert actions[-2:] == ["login", "logout"]


def test_wrong_password_and_lockout(env):
    client, *_ = env
    for _ in range(5):
        assert _login(client, password="nope").status_code == 401
    locked = _login(client)
    assert locked.status_code == 429 and locked.headers["Retry-After"]


def test_expired_session_is_rejected(env):
    client, session, *_ = env
    headers = _bearer(client)
    for s in session.scalars(select(UserSession)):
        s.expires_at = service.now() - timedelta(seconds=1)
    session.flush()
    assert client.get("/v1/auth/me", headers=headers).status_code == 401


def test_roles_on_keys(env):
    client, session, org, _, _ = env
    viewer, _ = service.create_api_key(session, org_id=org.id, name="v", role="viewer",
                                       actor_id=None)
    analyst, _ = service.create_api_key(session, org_id=org.id, name="a", role="analyst",
                                        actor_id=None)
    session.flush()
    v, a = {"X-API-Key": viewer}, {"X-API-Key": analyst}
    assert client.get("/v1/browse/jurisdictions/AE", headers=v).status_code == 200
    assert client.post("/v1/analyze/holding-recommendation", json=REC, headers=v).status_code == 403
    assert client.post("/v1/analyze/holding-recommendation", json=REC, headers=a).status_code == 200
    assert client.get("/v1/admin/users", headers=a).status_code == 403


def test_admin_manages_users_and_keys(env):
    client, session, org, other, admin = env
    h = _bearer(client)
    created = client.post(
        "/v1/admin/users",
        json={"email": "ana@acme.test", "name": "Ana", "role": "analyst", "password": PASSWORD},
        headers=h,
    )
    assert created.status_code == 201
    dup = client.post(
        "/v1/admin/users",
        json={"email": "ANA@acme.test", "role": "analyst", "password": PASSWORD},
        headers=h,
    )
    assert dup.status_code == 422
    weak = client.post(
        "/v1/admin/users", json={"email": "b@acme.test", "password": "short"}, headers=h
    )
    assert weak.status_code == 422
    assert {u["email"] for u in client.get("/v1/admin/users", headers=h).json()} == {
        "admin@acme.test",
        "ana@acme.test",
    }
    # the last admin cannot be demoted or deactivated
    last = client.patch(f"/v1/admin/users/{admin.id}", json={"role": "analyst"}, headers=h)
    assert last.status_code == 422
    # deactivating a user ends their sessions
    ana_headers = _bearer(client, email="ana@acme.test")
    uid = created.json()["id"]
    assert client.patch(f"/v1/admin/users/{uid}", json={"active": False}, headers=h).json()[
        "active"
    ] is False
    assert client.get("/v1/auth/me", headers=ana_headers).status_code == 401

    key = client.post("/v1/admin/api-keys", json={"name": "ci", "role": "viewer"}, headers=h)
    raw, key_id = key.json()["key"], key.json()["id"]
    assert client.get("/v1/auth/me", headers={"X-API-Key": raw}).json()["role"] == "viewer"
    assert client.delete(f"/v1/admin/api-keys/{key_id}", headers=h).status_code == 204
    assert client.get("/v1/auth/me", headers={"X-API-Key": raw}).status_code == 401


def test_admin_cannot_touch_another_org(env):
    client, session, org, other, _ = env
    outsider = service.create_user(
        session, org_id=other.id, email="x@other.test", name=None, role="analyst",
        password=PASSWORD, actor_id=None,
    )
    session.flush()
    h = _bearer(client)
    assert client.patch(
        f"/v1/admin/users/{outsider.id}", json={"active": False}, headers=h
    ).status_code == 404


def test_password_change_revokes_other_sessions(env):
    client, *_ = env
    a, b = _bearer(client), _bearer(client)
    resp = client.post(
        "/v1/auth/password",
        json={"current_password": PASSWORD, "new_password": "a much better passphrase"},
        headers=a,
    )
    assert resp.status_code == 204
    assert client.get("/v1/auth/me", headers=b).status_code == 401
    assert _login(client, password="a much better passphrase").status_code == 200


def test_metering_and_rate_limit(env):
    client, session, org, _, _ = env
    plan = Plan(code="tiny", name="Tiny", analyses_per_day=100, analyses_per_minute=1,
                llm_calls_per_day=0)
    session.add(plan)
    session.flush()
    org.plan_id = plan.id
    session.flush()
    h = _bearer(client)
    first = client.post("/v1/analyze/holding-recommendation", json=REC, headers=h)
    assert first.status_code == 200
    second = client.post("/v1/analyze/holding-recommendation", json=REC, headers=h)
    assert second.status_code == 429 and second.headers["Retry-After"] == "60"
    events = session.scalars(select(UsageEvent).where(UsageEvent.org_id == org.id)).all()
    assert [(e.kind, e.user_id is not None) for e in events] == [("analysis", True)]
    usage = client.get("/v1/admin/usage", headers=h).json()
    assert usage["usage"]["analysis"]["events"] == 1 and usage["plan"]["code"] == "tiny"
