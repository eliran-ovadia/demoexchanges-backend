from typing import Any

from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.external_client_handlers.client_response_models.quote_model import get_cached_quotes
from src.exchange.external_client_handlers.client_response_models.search_handler import SearchHandler, \
    get_search_handler
from src.exchange.external_client_handlers.client_response_models.sentiment_handler import SentimentHandler, \
    get_sentiment_handler
from src.exchange.app_instanse import app

# This function can handle one of multiple symbol requests, with the help of QuoteHandler
def get_parsed_quote(request: str, db: Session) -> dict[str, Any]:
    return get_cached_quotes(request)


def market_status(db: Session) -> dict[str, Any]:
    return app.state.market_status


def stock_search(request: str, page: int, page_size: int):
    search_handler: SearchHandler = get_search_handler(request=request)
    return search_handler.search(page=page, page_size=page_size)


def market_movers():
    return MarketMoversManager.get_market_movers()


def stock_sentiment(request: str) -> dict[str, Any]:
    sentiment_handler: SentimentHandler = get_sentiment_handler(request)
    return sentiment_handler.get_sentiment()
