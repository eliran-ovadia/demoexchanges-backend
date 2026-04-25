from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.external_client_handlers.client_requests import (
    fetch_quote, fetch_market_status, fetch_search, fetch_sentiment
)
from src.exchange.schemas.fmp_schemas import (
    ParsedQuoteResponse, SearchResult, SearchResponse,
    MarketStatusResponse, SentimentEntry, MarketMoversResponse
)


def parsed_quote(symbols: str) -> dict[str, ParsedQuoteResponse]:
    quote = fetch_quote(symbols)
    return {
        symbol: ParsedQuoteResponse(
            full_name=q.name,
            exchange=q.exchange,
            currency=q.currency,
            open=round(q.open, 2),
            high=round(q.high, 2),
            low=round(q.low, 2),
            close=round(q.price, 2),
            volume=q.volume,
            change=round(q.change, 2),
            percent_change=round(q.percent_change, 2),
            avg_volume=q.avg_volume,
            year_range_high=round(q.year_high, 2) if q.year_high else None,
            year_range_low=round(q.year_low, 2) if q.year_low else None,
        ).model_dump()
        for symbol, q in quote.items()
    }


def market_status(db: Session) -> dict[str, Any]:
    data = fetch_market_status()
    return MarketStatusResponse(
        exchange=data.get("exchange"),
        is_open=data.get("isMarketOpen"),
        # open_time=data.get("openingHour"),
        # close_time = data.get("closingHour")
    ).model_dump()


def stock_search(request: str, page: int, page_size: int) -> SearchResponse:
    raw = fetch_search(request)
    results = [
        SearchResult(
            country="US",
            currency=item.get("currency", "USD*"), # * BECAUSE IT MAY NOT BE USD
            exchange=item.get("exchange", ""),
            instrument_name=item.get("name", ""),
            symbol=item.get("symbol", ""),
        )
        for item in raw
        if item.get("exchange") in {"NYSE", "NASDAQ"}
    ]
    page_start = (page - 1) * page_size
    return SearchResponse(
        total_results=len(results),
        page=page,
        page_size=page_size,
        results=results[page_start: page_start + page_size],
    ).model_dump()


def market_movers() -> MarketMoversResponse:
    movers = MarketMoversManager.get_market_movers()
    if movers is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market movers not yet available — try again shortly"
        )
    stocks_list: list[dict] = movers.get("stocks")
    return MarketMoversResponse(stocks=stocks_list).model_dump()


def stock_sentiment(symbol: str) -> list[dict[str, Any]]:
    raw = fetch_sentiment(symbol)
    return [SentimentEntry(**item).model_dump() for item in raw]
