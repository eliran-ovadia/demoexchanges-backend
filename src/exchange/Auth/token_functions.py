import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from jose import JWTError, jwt

from src.exchange.schemas import schemas


def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Required environment variable '{key}' is not set")
    return val


def validate_auth_config() -> None:
    """Call at startup to fail fast if auth env vars are missing."""
    _require_env("SECRET_KEY")
    _require_env("ALGORITHM")


SECRET_KEY: str = os.getenv("SECRET_KEY", "")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 1))


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    jti = str(uuid.uuid4())
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> Tuple[str, str]:
    """Returns (encoded_token, jti). Caller must store jti in Redis."""
    to_encode = data.copy()
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def verify_token(token: str, credentials_exception) -> Tuple[schemas.TokenData, str]:
    """Returns (TokenData, jti). Raises credentials_exception on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        token_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if token_id is None or jti is None:
            raise credentials_exception
        token_data = schemas.TokenData(
            id=token_id,
            is_admin=payload.get("is_admin"),
            email=payload.get("email"),
            name=payload.get("name"),
        )
    except JWTError:
        raise credentials_exception
    return token_data, jti


def verify_refresh_token(token: str, credentials_exception) -> Tuple[dict, str]:
    """Returns (raw payload dict, jti). Raises credentials_exception on any failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        jti: str = payload.get("jti")
        if not jti or not payload.get("sub"):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return payload, jti
