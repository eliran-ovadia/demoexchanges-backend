from typing import Any

from sqlalchemy.exc import IntegrityError

from src.exchange.client_handlers.client_requests import get_stock_price
from src.exchange.database.models import History as modelHistory
from src.exchange.routers.repository.utils.order_utils import *
from src.exchange.schemas import History as schemaHistory
from src.exchange.schemas import Stock
from .utils.get_portfolio_utils import fetch_portfolio_data, handle_empty_portfolio, fetch_quotes, \
    process_portfolio_data, build_portfolio_response


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
    total_stocks, portfolio_data = fetch_portfolio_data(db, current_user, page, page_size)

    if not portfolio_data:
        return handle_empty_portfolio(db, current_user)  # If no stocks, return balance with zeroes

    symbols = list(portfolio_data.keys())
    quotes = fetch_quotes(symbols, db)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return build_portfolio_response(db, current_user, detailed_portfolio_data, total_stocks)


def get_history(db: Session, current_user: schemas.TokenData, page: int, page_size: int) -> dict[str, Any]:
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"No records for this page, there are {total_items} records total for the account")

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
        "history": history_to_return
    }


def add_to_watchlist(request: Stock, db: Session, current_user: schemas.TokenData):
    raise_if_not_stock = get_stock_price(request.symbol)
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


def delete_from_watchlist(request: Stock, db: Session, current_user: schemas.TokenData):
    item = (db.query(models.WatchlistItem)
            .filter(models.WatchlistItem.symbol == request.symbol, models.WatchlistItem.user_id == current_user.id)
            .first())

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stock symbol '{request.symbol}' is not in your watchlist."
        )

    db.delete(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An error occurred while attempting to delete {item}."
        )


def get_watchlist(db: Session, page: int, page_size: int, current_user: schemas.TokenData) -> list[str]:
    watchlist = (db.query(models.WatchlistItem).filter(models.WatchlistItem.user_id == current_user.id)
                 .offset((page - 1) * page_size)
                 .limit(page_size)
                 .all())

    watchlist_to_return = [item.symbol for item in watchlist]

    return watchlist_to_return
