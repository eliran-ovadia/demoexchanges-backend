from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.order_utils import *
from exchange.models import History as modelHistory
from exchange.models import MarketStatus
from exchange.schemas import History as schemaHistory
from exchange.schemas import Pagination
from exchange.routers.repository.utils.get_parsed_portfolio_utils import process_single_quote
from sqlalchemy.orm import Session
from typing import Dict, Any


def order(request: schemas.Order, db: Session, current_user: schemas.TokenData) -> schemas.AfterOrder:
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot buy/sell more than one stock at once")
    price = get_stock_price(symbol, db)
    value = price * request.amount

    if request.amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be 0")
    if request.type == 'Buy':
        return buy_handler(request, db, current_user, symbol, price, value)
    else:
        return sell_handler(request, db, current_user, symbol, price, value)


def get_portfolio(db: Session, current_user: schemas.TokenData, page: int, page_size: int) -> dict:
    portfolio_data = fetch_portfolio_data(db, current_user, page, page_size)

    if not portfolio_data:
        return handle_empty_portfolio(db, current_user)  # If no stocks, return balance with zeroes

    symbols = list(portfolio_data.keys())
    quotes = fetch_quotes(symbols, db)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return build_portfolio_response(db, current_user, detailed_portfolio_data)


def get_history(db: Session, current_user: schemas.TokenData, page: int, page_size: int) -> Dict[str, Any]:
    total_items = db.query(modelHistory).filter(modelHistory.user_id == current_user.id).count()

    if not total_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No order history")
    history_array = (
        db.query(modelHistory)
        .filter(modelHistory.user_id == current_user.id)
        .order_by(modelHistory.time_stamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    if not history_array:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No records for this page, there are {total_items} records total for the account")

    history_to_return = [
        schemaHistory(
            symbol=history.symbol,
            price=round(history.price, 2),
            amount=history.amount,
            type=history.type,
            value=round(history.value, 2),
            profit=round(history.profit, 2),
            time_stamp=history.time_stamp,
        )
        for history in history_array
    ]

    return {
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
        "history": history_to_return,
    }


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
