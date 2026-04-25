"""Auth flow: login, refresh, logout, token blacklist."""
from datetime import timedelta
from unittest.mock import patch, AsyncMock

import pytest

from src.exchange.Auth.token_functions import create_access_token

CLAIMS = {
    "sub": "fake-user-id",
    "is_admin": False,
    "name": "Test",
    "email": "test@example.com",
}


# ── /Token ──────────────────────────────────────────────────────────────────

async def test_login_returns_token_pair(client, registered_user):
    resp = await client.post(
        "/Token",
        data={"username": registered_user["email"], "password": registered_user["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client, registered_user):
    resp = await client.post(
        "/Token",
        data={"username": registered_user["email"], "password": "WrongPass#1"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client):
    resp = await client.post(
        "/Token",
        data={"username": "nobody@example.com", "password": "Secure#Pass9"},
    )
    assert resp.status_code == 401


# ── /Refresh ─────────────────────────────────────────────────────────────────

async def test_refresh_returns_new_token_pair(client, auth_tokens):
    _, refresh_token = auth_tokens
    resp = await client.post("/Refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body


async def test_refresh_invalidates_old_refresh_token(client, auth_tokens):
    _, refresh_token = auth_tokens
    await client.post("/Refresh", json={"refresh_token": refresh_token})

    # Using the old refresh token again should fail (replay attack prevention)
    resp = await client.post("/Refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 401


async def test_refresh_with_garbage_token_returns_401(client):
    resp = await client.post("/Refresh", json={"refresh_token": "not.a.token"})
    assert resp.status_code == 401


async def test_refresh_with_access_token_returns_401(client, auth_tokens):
    access_token, _ = auth_tokens
    resp = await client.post("/Refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401


# ── /Logout ───────────────────────────────────────────────────────────────────

async def test_logout_returns_204(client, auth_tokens, auth_headers):
    _, refresh_token = auth_tokens
    resp = await client.post(
        "/Logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers,
    )
    assert resp.status_code == 204


async def test_blacklisted_token_is_rejected(client, auth_tokens, auth_headers):
    _, refresh_token = auth_tokens
    await client.post(
        "/Logout",
        json={"refresh_token": refresh_token},
        headers=auth_headers,
    )

    # Blacklisted access token should now be rejected on any protected route
    resp = await client.get("/api/GetPortfolio", headers=auth_headers)
    assert resp.status_code == 401
    assert "revoked" in resp.json()["detail"].lower()


async def test_expired_access_token_is_rejected(client):
    expired_token = create_access_token(data=CLAIMS, expires_delta=timedelta(seconds=-1))
    resp = await client.get(
        "/api/GetPortfolio",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


async def test_unauthenticated_request_returns_401(client):
    resp = await client.get("/api/GetPortfolio")
    assert resp.status_code == 401
