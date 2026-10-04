from unittest.mock import patch

from fastapi.testclient import TestClient


def test_health_is_ok_without_db(client: TestClient):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ready_returns_503_when_db_unreachable(client: TestClient):
    with patch("app.api.v1.health.check_database", return_value=False):
        resp = client.get("/health/ready")
    assert resp.status_code == 503
    assert resp.json() == {"status": "unavailable"}
