import os
import threading
from typing import Optional

import redis.asyncio as redis

from src.exchange.app_logger import logger


class RedisClient:
    def __init__(self, url: str):
        self._redis = redis.from_url(url, decode_responses=True)

    # ------------------------------------------------------------------
    # Access token blacklist (fail-open: Redis down → token passes through)
    # ------------------------------------------------------------------

    async def blacklist_token(self, jti: str, ttl_seconds: int) -> None:
        try:
            await self._redis.setex(f"blacklist:{jti}", ttl_seconds, "1")
        except redis.RedisError as e:
            logger.error(f"Redis blacklist write failed: {e}")

    async def is_blacklisted(self, jti: str) -> bool:
        try:
            return await self._redis.exists(f"blacklist:{jti}") > 0
        except redis.RedisError as e:
            logger.error(f"Redis blacklist read failed: {e}")
            return False  # fail-open: Redis down should not lock out all users

    # ------------------------------------------------------------------
    # Refresh token whitelist (fail-secure: Redis down → token rejected)
    # ------------------------------------------------------------------

    async def store_refresh_token(self, jti: str, ttl_seconds: int) -> None:
        try:
            await self._redis.setex(f"refresh:{jti}", ttl_seconds, "1")
        except redis.RedisError as e:
            logger.error(f"Redis refresh token store failed: {e}")

    async def is_valid_refresh_token(self, jti: str) -> bool:
        try:
            return await self._redis.exists(f"refresh:{jti}") > 0
        except redis.RedisError as e:
            logger.error(f"Redis refresh token check failed: {e}")
            return False  # fail-secure: Redis down invalidates refresh tokens

    async def revoke_refresh_token(self, jti: str) -> None:
        try:
            await self._redis.delete(f"refresh:{jti}")
        except redis.RedisError as e:
            logger.error(f"Redis refresh token revoke failed: {e}")

    # ------------------------------------------------------------------
    # Generic cache
    # ------------------------------------------------------------------

    async def cache_set(self, key: str, value: str, ttl_seconds: int) -> None:
        try:
            await self._redis.setex(key, ttl_seconds, value)
        except redis.RedisError as e:
            logger.error(f"Redis cache set failed for key={key}: {e}")

    async def cache_get(self, key: str) -> Optional[str]:
        try:
            return await self._redis.get(key)
        except redis.RedisError as e:
            logger.error(f"Redis cache get failed for key={key}: {e}")
            return None

    async def ping(self) -> bool:
        try:
            return await self._redis.ping()
        except redis.RedisError:
            return False

    async def close(self) -> None:
        await self._redis.aclose()


class RedisManager:
    _client: Optional[RedisClient] = None
    _lock = threading.Lock()

    @classmethod
    def get_client(cls) -> RedisClient:
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    cls._client = cls._create_client()
        return cls._client

    @classmethod
    def _create_client(cls) -> RedisClient:
        env = os.getenv("APP_ENV", "dev")
        url_key = "REDIS_PROD_URL" if env == "prod" else "REDIS_DEV_URL"
        url = os.getenv(url_key)
        if not url:
            raise RuntimeError(f"{url_key} environment variable is not set")
        client = RedisClient(url)
        logger.info(f"Redis client created (env={env})")
        return client

    @classmethod
    async def reset(cls) -> None:
        with cls._lock:
            if cls._client:
                await cls._client.close()
            cls._client = None
            logger.info("Redis client reset.")
