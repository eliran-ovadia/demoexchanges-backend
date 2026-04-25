import json

from src.exchange.app_logger import logger

_CACHE_KEY = "market_movers"
_CACHE_TTL = 25 * 3600  # 25 hours: survives a missed daily refresh


class MarketMoversManager:
    """Caches most-active stocks in Redis; updated by the daily background job."""

    @classmethod
    async def update_market_movers(cls) -> None:
        from src.exchange.external_client_handlers.client_requests import fetch_market_movers
        from src.exchange.redis_manager import RedisManager
        try:
            movers = await fetch_market_movers()
            await RedisManager.get_client().cache_set(_CACHE_KEY, json.dumps(movers), _CACHE_TTL)
            logger.info("Market movers cache updated in Redis.")
        except Exception as e:
            logger.error(f"Failed to update market movers: {e}")

    @classmethod
    async def get_market_movers(cls) -> dict | None:
        from src.exchange.redis_manager import RedisManager
        raw = await RedisManager.get_client().cache_get(_CACHE_KEY)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError) as e:
            logger.critical(f"Failed to deserialize market movers from Redis: {e}")
            return None
