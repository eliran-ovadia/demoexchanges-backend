from functools import lru_cache
from typing import Any, Optional

from src.exchange.external_client_handlers.client_requests import fetch_sentiment


class SentimentHandler:

    def __init__(self, sentiment: Optional[list[Any]] = None):
        self.sentiment = sentiment[0] if sentiment is not None else None

    def get_sentiment(self) -> dict[str, Any]:
        return self.sentiment


# Factory cache - use LRU to swap entries
@lru_cache(maxsize=100)
def get_sentiment_handler(request: str = '') -> SentimentHandler:
    return SentimentHandler(sentiment=fetch_sentiment(request))
