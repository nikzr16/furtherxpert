"""Tests for accounts: register, login, refresh, logout, /me (PRD T3, T4).

Runs against a real, separate PostgreSQL database (see tests/conftest.py for
the isolation strategy) -- acceptance check 4 (PRD section "Acceptance
checks"): wrong password rejected, expired login rejected, no cross-user
access.
"""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from app.core.security import JWT_ALGORITHM


def _register(client, make_register_payload, **overrides):
    return client.post("/auth/register", json=make_register_payload(**overrides))


def _login(client, email: str, password: str):
    return client.post("/auth/login", json={"email": email, "password": password})


def test_register_login_me_happy_path(client, make_register_payload):
    payload = make_register_payload()

    register_response = _register(client, make_register_payload, **payload)
    assert register_response.status_code == 201
    body = register_response.json()
    assert body["email"] == payload["email"].lower()
    assert body["is_citizen"] is True
    assert body["race"] == "Melayu"
    assert body["spm_year"] == 2025
    assert "password" not in body
    assert "password_hash" not in body

    login_response = _login(client, payload["email"], payload["password"])
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["token_type"] == "bearer"
    access_token = login_body["access_token"]
    assert access_token
    assert "refresh_token" in login_response.cookies

    me_response = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == payload["email"].lower()


def test_register_rejects_duplicate_email(client, make_register_payload):
    payload = make_register_payload(email="dup@example.com")
    first = _register(client, make_register_payload, **payload)
    assert first.status_code == 201

    second = _register(client, make_register_payload, **payload)
    assert second.status_code == 409


def test_login_wrong_password_is_generic(client, make_register_payload):
    payload = make_register_payload()
    _register(client, make_register_payload, **payload)

    response = _login(client, payload["email"], "totally-wrong-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong email or password"


def test_login_unknown_email_is_generic(client):
    response = _login(client, "nobody-registered@example.com", "whatever-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "Wrong email or password"


def test_expired_access_token_is_rejected(client, make_register_payload):
    payload = make_register_payload()
    register_response = _register(client, make_register_payload, **payload)
    user_id = register_response.json()["id"]

    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {"sub": user_id, "type": "access", "iat": now - timedelta(minutes=20), "exp": now - timedelta(minutes=5)},
        settings.JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = client.get("/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401


def test_refresh_token_rejected_as_access_token(client, make_register_payload):
    payload = make_register_payload()
    _register(client, make_register_payload, **payload)
    login_response = _login(client, payload["email"], payload["password"])
    refresh_token = login_response.cookies["refresh_token"]

    response = client.get("/me", headers={"Authorization": f"Bearer {refresh_token}"})
    assert response.status_code == 401


def test_access_token_rejected_as_refresh_token(client, make_register_payload):
    payload = make_register_payload()
    _register(client, make_register_payload, **payload)
    login_response = _login(client, payload["email"], payload["password"])
    access_token = login_response.json()["access_token"]

    client.cookies.set("refresh_token", access_token, path="/auth")
    response = client.post("/auth/refresh")
    assert response.status_code == 401
    # A well-formed but wrong-type token, not a missing cookie.
    assert response.json()["detail"] == "Invalid or expired token"


def test_refresh_issues_new_valid_access_token(client, make_register_payload):
    payload = make_register_payload()
    _register(client, make_register_payload, **payload)
    login_response = _login(client, payload["email"], payload["password"])
    assert "refresh_token" in login_response.cookies

    refresh_response = client.post("/auth/refresh")
    assert refresh_response.status_code == 200
    new_access_token = refresh_response.json()["access_token"]
    assert new_access_token

    me_response = client.get("/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert me_response.status_code == 200
    assert me_response.json()["email"] == payload["email"].lower()


def test_delete_me_removes_row_and_blocks_reuse_without_affecting_other_users(client, make_register_payload):
    payload_a = make_register_payload()
    payload_b = make_register_payload()
    _register(client, make_register_payload, **payload_a)
    _register(client, make_register_payload, **payload_b)

    login_a = _login(client, payload_a["email"], payload_a["password"])
    token_a = login_a.json()["access_token"]
    login_b = _login(client, payload_b["email"], payload_b["password"])
    token_b = login_b.json()["access_token"]

    delete_response = client.delete("/me", headers={"Authorization": f"Bearer {token_a}"})
    assert delete_response.status_code == 204

    # user A's old access token no longer works (row is gone).
    stale_me_response = client.get("/me", headers={"Authorization": f"Bearer {token_a}"})
    assert stale_me_response.status_code == 401

    # a fresh login attempt for the deleted user also fails.
    relogin_a = _login(client, payload_a["email"], payload_a["password"])
    assert relogin_a.status_code == 401

    # user B is completely unaffected: still logged in, still exists.
    me_b_response = client.get("/me", headers={"Authorization": f"Bearer {token_b}"})
    assert me_b_response.status_code == 200
    assert me_b_response.json()["email"] == payload_b["email"].lower()


def test_login_rate_limit_trips_on_sixth_attempt(client, make_register_payload):
    payload = make_register_payload()
    _register(client, make_register_payload, **payload)

    for _ in range(5):
        response = _login(client, payload["email"], "wrong-password")
        assert response.status_code == 401

    sixth_response = _login(client, payload["email"], "wrong-password")
    assert sixth_response.status_code == 429


def test_register_rejects_missing_consent(client, make_register_payload):
    response = _register(client, make_register_payload, consent=False)
    assert response.status_code == 422


def test_register_rejects_unknown_race(client, make_register_payload):
    response = _register(client, make_register_payload, race="Not A Real Race")
    assert response.status_code == 422
