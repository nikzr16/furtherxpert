"""Tests for GET /health.

Locks in the chosen failure-mode contract: always HTTP 200; the "db" field in
the body is "ok" or "error" depending on DB reachability. No live Postgres is
needed — the DB session dependency is overridden with fakes.
"""

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.main import app


class _FakeSessionOk:
    def execute(self, *args, **kwargs):
        return None


class _FakeSessionError:
    def execute(self, *args, **kwargs):
        raise RuntimeError("db unreachable")


def _override_ok():
    yield _FakeSessionOk()


def _override_error():
    yield _FakeSessionError()


def test_health_returns_ok_when_db_is_up():
    app.dependency_overrides[get_db] = _override_ok
    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "db": "ok"}
    finally:
        app.dependency_overrides.clear()


def test_health_returns_200_with_db_error_when_db_is_down():
    app.dependency_overrides[get_db] = _override_error
    try:
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "db": "error"}
    finally:
        app.dependency_overrides.clear()
