from typing import Tuple, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.app_logger import logger
from src.exchange.database.models import Portfolio
from src.exchange.external_client_handlers.client_requests import fetch_quote
from src.exchange.schemas.fmp_schemas import QuoteSchema
from src.exchange.schemas.schemas import TokenData, ShowStock, PortfolioResponse, PortfolioBalance
from .find_user import find_user


async def fetch_portfolio_data(
    db: AsyncSession,
    current_user: TokenData,
    page: int,
    page_size: int,
) -> Tuple[int, Optional[Dict[str, Any]]]:
    rows = (await db.execute(
        select(
            Portfolio.symbol,
            func.sum(Portfolio.amount).label("total_amount"),
            func.avg(Portfolio.price).label("avg_price"),
        )
        .where(Portfolio.user_id == current_user.id)
        .group_by(Portfolio.symbol)
        .order_by(Portfolio.symbol.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )).all()

    total_stocks = (await db.execute(
        select(func.count(Portfolio.symbol.distinct()))
        .where(Portfolio.user_id == current_user.id)
    )).scalar()

    data = (
        {symbol: {"total_amount": total_amount, "avg_price": avg_price}
         for symbol, total_amount, avg_price in rows}
        if rows else None
    )
    return total_stocks, data


async def fetch_quotes(symbols: list[str]) -> dict[str, QuoteSchema]:
    try:
        return await fetch_quote(",".join(symbols))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


async def handle_empty_portfolio(db: AsyncSession, current_user: TokenData, total_stocks: int) -> PortfolioResponse:
    user = await find_user(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return PortfolioResponse(
        balance=PortfolioBalance(
            buying_power=round(float(user.cash), 2),
            portfolio_value=0.00,
            total_return=0.00,
            total_return_percent=0.00,
            account_value=round(float(user.cash), 2),
            total_stocks=total_stocks,
        ),
        portfolio=[],
    )


def process_portfolio_data(portfolio_data: dict, quotes: dict[str, QuoteSchema]) -> list[ShowStock]:
    result = []
    for symbol, data in portfolio_data.items():
        q = quotes.get(symbol)
        if not q:
            logger.warning(f"No quote data found for symbol: {symbol}")
            continue
        result.append(_build_show_stock(symbol, data, q))
    result.sort(key=lambda x: x.total_value, reverse=True)
    return result


def _build_show_stock(symbol: str, data: dict, q: QuoteSchema) -> ShowStock:
    total_amount = data["total_amount"]
    last_price = round(q.price, 2)
    avg_price = round(float(data["avg_price"]), 2)
    total_value = round(last_price * total_amount, 2)
    total_return = round((last_price - avg_price) * total_amount, 2)
    total_return_percent = round((total_return / avg_price) * 100, 2) if avg_price else 0

    return ShowStock(
        symbol=symbol,
        full_name=q.name,
        amount=total_amount,
        exchange=q.exchange,
        open=round(q.open, 2),
        previous_close=round(q.previous_close, 2),
        avg_price=avg_price,
        last_price=last_price,
        total_value=total_value,
        bid=last_price,
        ask=last_price,
        year_range_low=round(q.year_low, 2) if q.year_low else None,
        year_range_high=round(q.year_high, 2) if q.year_high else None,
        total_return=total_return,
        total_return_percent=total_return_percent,
    )


async def build_portfolio_response(
    db: AsyncSession,
    current_user: TokenData,
    portfolio_data: list[ShowStock],
    total_stocks: int,
) -> PortfolioResponse:
    user = await find_user(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    portfolio_value = round(sum(x.total_value for x in portfolio_data), 2)
    total_return = round(sum(x.total_return for x in portfolio_data), 2)
    total_invested = round(sum(x.avg_price * x.amount for x in portfolio_data), 2)
    total_return_percent = round((total_return / total_invested) * 100, 2) if total_invested > 0 else 0

    return PortfolioResponse(
        balance=PortfolioBalance(
            buying_power=round(float(user.cash), 2),
            portfolio_value=portfolio_value,
            total_return=total_return,
            total_return_percent=total_return_percent,
            account_value=round(float(user.cash) + portfolio_value, 2),
            total_stocks=total_stocks,
        ),
        portfolio=portfolio_data,
    )
