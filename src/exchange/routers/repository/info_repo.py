from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.external_client_handlers.client_requests import fetch_quote, fetch_market_status, fetch_search, \
    fetch_sentiment
from src.exchange.external_client_handlers.client_response_models.market_status_model import MarketStatusModel
from src.exchange.external_client_handlers.client_response_models.quote_model import QuoteResponseModel
from src.exchange.external_client_handlers.client_response_models.search_handler import SearchHandler


def parsed_quote(request: str) -> dict[str, Any]:
    return QuoteResponseModel(fetch_quote(request)).to_parsed_quotes()


def market_status(db: Session) -> dict[str, Any]:
    return MarketStatusModel(**fetch_market_status()).market_status()


def stock_search(request: str, page: int, page_size: int):
    return SearchHandler(fetch_search(request)).search(page, page_size)


def market_movers() -> dict[str, Any]:
    movers = MarketMoversManager.get_market_movers()
    if movers is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market movers not yet available — try again shortly"
        )
    return movers


def stock_sentiment(request: str) -> list[dict[str, Any]]:
    return fetch_sentiment(request)
