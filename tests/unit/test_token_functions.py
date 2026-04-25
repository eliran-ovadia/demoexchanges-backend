from datetime import timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from src.exchange.Auth.token_functions import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    create_refresh_token,
    verify_token,
    verify_refresh_token,
    validate_auth_config,
)

CLAIMS = {
    "sub": "user-uuid-123",
    "is_admin": False,
    "name": "Test",
    "email": "test@example.com",
}

_EXC = HTTPException(status_code=401, detail="bad token")


# ── create_access_token / verify_token ──────────────────────────────────────

def test_access_token_round_trip():
    token = create_access_token(data=CLAIMS)
    token_data, jti = verify_token(token, _EXC)

    assert token_data.id == CLAIMS["sub"]
    assert token_data.email == CLAIMS["email"]
    assert token_data.name == CLAIMS["name"]
    assert token_data.is_admin is False
    assert jti  # non-empty UUID


def test_access_token_has_type_claim():
    token = create_access_token(data=CLAIMS)
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["type"] == "access"


def test_access_token_has_unique_jti():
    t1 = create_access_token(data=CLAIMS)
    t2 = create_access_token(data=CLAIMS)
    p1 = jwt.decode(t1, SECRET_KEY, algorithms=[ALGORITHM])
    p2 = jwt.decode(t2, SECRET_KEY, algorithms=[ALGORITHM])
    assert p1["jti"] != p2["jti"]


def test_expired_access_token_raises():
    token = create_access_token(data=CLAIMS, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        verify_token(token, _EXC)
    assert exc_info.value.status_code == 401


def test_tampered_access_token_raises():
    token = create_access_token(data=CLAIMS)
    bad_token = token[:-5] + "XXXXX"
    with pytest.raises(HTTPException):
        verify_token(bad_token, _EXC)


def test_refresh_token_rejected_by_verify_token():
    refresh_token, _ = create_refresh_token(data=CLAIMS)
    with pytest.raises(HTTPException):
        verify_token(refresh_token, _EXC)


# ── create_refresh_token / verify_refresh_token ─────────────────────────────

def test_refresh_token_round_trip():
    token, jti = create_refresh_token(data=CLAIMS)
    payload, returned_jti = verify_refresh_token(token, _EXC)

    assert payload["sub"] == CLAIMS["sub"]
    assert returned_jti == jti
    assert payload["type"] == "refresh"


def test_refresh_token_unique_jti():
    _, jti1 = create_refresh_token(data=CLAIMS)
    _, jti2 = create_refresh_token(data=CLAIMS)
    assert jti1 != jti2


def test_access_token_rejected_by_verify_refresh_token():
    access_token = create_access_token(data=CLAIMS)
    with pytest.raises(HTTPException):
        verify_refresh_token(access_token, _EXC)


def test_expired_refresh_token_raises():
    import os
    from unittest.mock import patch
    from datetime import datetime, timezone, timedelta
    from jose import jwt as jose_jwt

    claims = CLAIMS.copy()
    claims.update({
        "jti": "test-jti",
        "type": "refresh",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    })
    expired_token = jose_jwt.encode(claims, SECRET_KEY, algorithm=ALGORITHM)
    with pytest.raises(HTTPException):
        verify_refresh_token(expired_token, _EXC)


# ── validate_auth_config ────────────────────────────────────────────────────

def test_validate_auth_config_passes_when_vars_set(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "some-key")
    monkeypatch.setenv("ALGORITHM", "HS256")
    validate_auth_config()  # should not raise


def test_validate_auth_config_raises_when_secret_key_missing(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_auth_config()
