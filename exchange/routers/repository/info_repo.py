from sqlalchemy.exc import IntegrityError
from exchange.clients_methods import get_search_result
from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.order_utils import *
from exchange.models import MarketStatus
from exchange.schemas import Stock
from exchange.routers.repository.utils.process_raw_quote import process_single_quote
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any


def get_parsed_quote(request: str, db: Session) -> dict:
    raw_quotes = get_quote(request, db)

    parsed_quotes_to_return = {}
    if 'symbol' in raw_quotes:  # Check for single dictionary
        parsed_quotes_to_return = process_single_quote(raw_quotes)
    else:
        for symbol, raw_quote in raw_quotes.items():
            parsed_quote = process_single_quote(raw_quote)
            parsed_quotes_to_return[symbol] = parsed_quote

    return parsed_quotes_to_return


def fetch_market_status(db: Session) -> MarketStatus:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if not market:
        raise HTTPException(status_code=404, detail="Market status not found")
    return market.is_market_open


def stock_search(prompt: str, page: int, page_size: int) -> Dict[str, Any]:
    unfiltered_results = get_search_result(prompt)

    filtered_results = [result for result in unfiltered_results if
                        result["exchange"] == "NYSE" or result["exchange"] == "NASDAQ"]

    total_results = len(filtered_results)

    return {"total_results": total_results,
            "page": page,
            "page_size": page_size,
            "results": filtered_results[(page - 1) * page_size: page * page_size]
            }


def add_to_watchlist(request: Stock, db: Session, current_user: schemas.TokenData):
    item = models.WatchlistItem(symbol=request.symbol, user_id=current_user.id)
    db.add(item)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Stock symbol '{request.symbol}' is already in your watchlist."
        )