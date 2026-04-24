from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from src.exchange.Auth.hashing import Hash
from src.exchange.Auth.token_functions import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    SECRET_KEY,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from src.exchange.database.models import User
from src.exchange.redis_manager import RedisManager
from src.exchange.schemas.schemas import Token

# Pre-computed hash used when the user doesn't exist, so the response time
# is indistinguishable from a valid-user-wrong-password path.
_DUMMY_HASH: str = Hash.bcrypt("__timing_guard__")

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_INVALID_REFRESH = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired refresh token",
    headers={"WWW-Authenticate": "Bearer"},
)


def _issue_token_pair(user: User) -> Token:
    """Creates a new access + refresh token pair and stores the refresh jti in Redis."""
    claims = {
        "sub": user.id,
        "is_admin": user.is_admin,
        "name": user.name,
        "email": user.email,
    }
    access_token = create_access_token(data=claims)
    refresh_token, refresh_jti = create_refresh_token(data=claims)

    redis = RedisManager.get_client()
    redis.store_refresh_token(refresh_jti, REFRESH_TOKEN_EXPIRE_DAYS * 86400)

    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


def get_bearer_token(*, username: str, password: str, db: Session) -> Token:
    user = db.query(User).filter(User.email == username).first()
    hash_to_check = user.password if user else _DUMMY_HASH
    password_correct = Hash.verify(password, hash_to_check)

    if not user or not password_correct:
        raise _INVALID_CREDENTIALS

    return _issue_token_pair(user)


def refresh_tokens(refresh_token: str, db: Session) -> Token:
    payload, old_jti = verify_refresh_token(refresh_token, _INVALID_REFRESH)

    redis = RedisManager.get_client()
    if not redis.is_valid_refresh_token(old_jti):
        raise _INVALID_REFRESH

    user_id: str = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        redis.revoke_refresh_token(old_jti)
        raise _INVALID_REFRESH

    # Rotate: revoke old refresh token before issuing new pair
    redis.revoke_refresh_token(old_jti)
    return _issue_token_pair(user)


def logout(access_token: str, refresh_token: str | None) -> None:
    # Revoke access token
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        jti: str = payload.get("jti")
        exp: int = payload.get("exp")
        if jti and exp:
            now = int(datetime.now(timezone.utc).timestamp())
            ttl = max(exp - now, 1)
            RedisManager.get_client().blacklist_token(jti, ttl)
    except JWTError:
        pass  # already-expired access tokens are harmless

    # Revoke refresh token if provided
    if refresh_token:
        try:
            payload, refresh_jti = verify_refresh_token(refresh_token, Exception())
            RedisManager.get_client().revoke_refresh_token(refresh_jti)
        except Exception:
            pass  # invalid/expired refresh tokens are harmless to ignore on logout
