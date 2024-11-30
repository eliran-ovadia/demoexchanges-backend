from functools import lru_cache
from typing import Any

from src.exchange.external_client_handlers.client_requests import get_sentiment


class SentimentHandler:

    def __init__(self, request: str = ''):
        self.sentiment = get_sentiment(request)

    def get_sentiment(self) -> dict[str, Any]:
        return self.sentiment


# Factory cache - use LRU to swap entries
@lru_cache(maxsize=100)
def get_sentiment_handler(request: str = '') -> SentimentHandler:
    return SentimentHandler(request)
