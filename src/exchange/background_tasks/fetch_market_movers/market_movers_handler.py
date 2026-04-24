import threading

from src.exchange.app_logger import logger


class MarketMoversManager:
    """Caches most-active stocks in RAM; updated by the daily background job."""

    _movers: dict | None = None
    _lock = threading.Lock()

    @classmethod
    def update_market_movers(cls):
        from src.exchange.external_client_handlers.client_requests import fetch_market_movers
        try:
            movers = fetch_market_movers()
            with cls._lock:
                cls._movers = movers
            logger.info("Market movers cache updated.")
        except Exception as e:
            logger.error(f"Failed to update market movers: {e}")

    @classmethod
    def get_market_movers(cls) -> dict | None:
        with cls._lock:
            return cls._movers
