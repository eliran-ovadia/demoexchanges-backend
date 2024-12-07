from typing import Optional, Any

from cachetools import TTLCache

from src.exchange.external_client_handlers.client_manager import ClientManager

market_status_cache = TTLCache(maxsize=1, ttl=1800)  # Cache the status for the next 30 minutes


class MarketStatusHandler:
    def __init__(self, exchange: Optional[str] = None, holiday: Optional[str] = None, isOpen: Optional[bool] = None,
                 session: Optional[str] = None, **kwargs) -> None:
        self.exchange = exchange
        self.holiday = holiday
        self.isOpen = isOpen
        self.session = session

    def get_market_status(self) -> dict[str, Any]:
        return {
            'exchange': self.exchange,
            'holiday': self.holiday,
            'isOpen': self.isOpen,
            'session': self.session
        }


def get_cached_market_status() -> dict[str, Any]:
    status = market_status_cache.get('status', None)

    if status is None:  # Cache miss
        # Fetching market status to return and save to cache
        fn = ClientManager.get_finnhub_client()
        raw_status = fn.market_status(exchange='US')
        market_status_handler = MarketStatusHandler(**raw_status)
        status = market_status_handler.get_market_status()
        # Store the result in the cache
        market_status_cache['status'] = status

    return status
