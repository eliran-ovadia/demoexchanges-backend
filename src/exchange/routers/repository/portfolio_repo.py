from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.database.models import History as modelHistory
from src.exchange.external_client_handlers.client_requests import fetch_stock_price
from src.exchange.routers.repository.utils.order_utils import buy_handler, sell_handler
from src.exchange.routers.repository.utils.watchlist_manager import WatchlistManager
from src.exchange.schemas.schemas import History as schemaHistory, Stock
from src.exchange.schemas import schemas
from .utils.get_portfolio_utils import (
    fetch_portfolio_data, handle_empty_portfolio, fetch_quotes,
    process_portfolio_data, build_portfolio_response,
)
from fastapi import HTTPException, status


async def order(request: schemas.Order, db: AsyncSession, current_user: schemas.TokenData) -> schemas.AfterOrder:
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot buy/sell more than one stock at once")
    if request.amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Value of trade cannot be 0")

    price = await fetch_stock_price(symbol)
    value = price * request.amount

    if request.type == 'Buy':
        return await buy_handler(request, db, current_user, symbol, price, value)
    else:
        return await sell_handler(request, db, current_user, symbol, price, value)


async def get_portfolio(db: AsyncSession, current_user: schemas.TokenData, page: int, page_size: int) -> dict:
    total_stocks, portfolio_data = await fetch_portfolio_data(db, current_user, page, page_size)

    if not portfolio_data:
        return await handle_empty_portfolio(db, current_user, total_stocks)

    symbols = list(portfolio_data.keys())
    quotes = await fetch_quotes(symbols)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return await build_portfolio_response(db, current_user, detailed_portfolio_data, total_stocks)


async def get_history(db: AsyncSession, current_user: schemas.TokenData, page: int, page_size: int) -> dict[str, Any]:
    from sqlalchemy import func
    total_items = (await db.execute(
        select(func.count(modelHistory.order_id)).where(modelHistory.user_id == current_user.id)
    )).scalar()

    if not total_items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No order history")

    history_array = (await db.execute(
        select(modelHistory)
        .where(modelHistory.user_id == current_user.id)
        .order_by(modelHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).scalars().all()

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
            time_stamp=history.created_at,
        )
        for history in history_array
    ]

    return {
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
        "history": history_to_return,
    }


async def add_to_watchlist(request: Stock, db: AsyncSession, current_user: schemas.TokenData):
    return await WatchlistManager(db, current_user.id).add_to_watchlist(request.symbol)


async def delete_from_watchlist(request: Stock, db: AsyncSession, current_user: schemas.TokenData):
    return await WatchlistManager(db, current_user.id).delete_from_watchlist(request.symbol)


async def get_watchlist(db: AsyncSession, page: int, page_size: int, current_user: schemas.TokenData) -> dict:
    return await WatchlistManager(db, current_user.id).get_watchlist(page, page_size)
