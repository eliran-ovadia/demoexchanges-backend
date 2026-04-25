from datetime import datetime, timezone

from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


async def _issue_token_pair(user: User) -> Token:
    claims = {
        "sub": user.id,
        "is_admin": user.is_admin,
        "name": user.name,
        "email": user.email,
    }
    access_token = create_access_token(data=claims)
    refresh_token, refresh_jti = create_refresh_token(data=claims)
    await RedisManager.get_client().store_refresh_token(refresh_jti, REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


async def get_bearer_token(*, username: str, password: str, db: AsyncSession) -> Token:
    result = await db.execute(select(User).where(User.email == username))
    user = result.scalar_one_or_none()

    hash_to_check = user.password if user else _DUMMY_HASH
    password_correct = Hash.verify(password, hash_to_check)

    if not user or not password_correct:
        raise _INVALID_CREDENTIALS

    return await _issue_token_pair(user)


async def refresh_tokens(refresh_token: str, db: AsyncSession) -> Token:
    payload, old_jti = verify_refresh_token(refresh_token, _INVALID_REFRESH)

    redis = RedisManager.get_client()
    if not await redis.is_valid_refresh_token(old_jti):
        raise _INVALID_REFRESH

    user_id: str = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        await redis.revoke_refresh_token(old_jti)
        raise _INVALID_REFRESH

    await redis.revoke_refresh_token(old_jti)
    return await _issue_token_pair(user)


async def logout(access_token: str, refresh_token: str | None) -> None:
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        jti: str = payload.get("jti")
        exp: int = payload.get("exp")
        if jti and exp:
            now = int(datetime.now(timezone.utc).timestamp())
            ttl = max(exp - now, 1)
            await RedisManager.get_client().blacklist_token(jti, ttl)
    except JWTError:
        pass

    if refresh_token:
        try:
            _, refresh_jti = verify_refresh_token(refresh_token, Exception())
            await RedisManager.get_client().revoke_refresh_token(refresh_jti)
        except Exception:
            pass
