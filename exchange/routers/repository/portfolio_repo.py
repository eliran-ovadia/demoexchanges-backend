from exchange.clients_methods import get_stock_price
from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.order_utils import *
from exchange.models import History as modelHistory
from exchange.schemas import History as schemaHistory
from exchange.schemas import Stock
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import Dict, Any


def order(request: schemas.Order, db: Session, current_user: schemas.TokenData) -> schemas.AfterOrder:
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot buy/sell more than one stock at once")
    price = get_stock_price(symbol)
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
        "history": history_to_return # there was a ',' here...
    }


def delete_from_watchlist(request: Stock, db: Session, current_user: schemas.TokenData):
    item = (db.query(models.WatchlistItem)
            .filter(models.WatchlistItem.symbol == request.symbol , models.WatchlistItem.user_id == current_user.id)
            .first())

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{request.symbol}' is not in your watchlist."
        )

    db.delete(item)
    db.commit()


def get_watchlist(db: Session, page: int, page_size: int, current_user: schemas.TokenData) -> list[str]:
    watchlist = (db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == current_user.id)
                 .offset((page - 1) * page_size)
                 .limit(page_size)
                 .all())

    watchlist_to_return = [item.symbol for item in watchlist]

    return watchlist_to_return