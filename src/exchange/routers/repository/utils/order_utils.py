from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.app_logger import logger
from src.exchange.database import models
from src.exchange.schemas import schemas


# Sell logic ---------
async def sell_handler(
    request: schemas.Order,
    db: AsyncSession,
    current_user: schemas.TokenData,
    symbol: str,
    price: float,
    value: float,
) -> schemas.AfterOrder:
    total_owned_stock = (await db.execute(
        select(func.sum(models.Portfolio.amount)).where(
            models.Portfolio.user_id == current_user.id,
            models.Portfolio.symbol == symbol,
        )
    )).scalar() or 0

    if total_owned_stock < request.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Short selling is not supported. You can sell a maximum of {total_owned_stock} shares.",
        )

    total_profit = await sell(current_user, db, price, request, symbol, value)

    return schemas.AfterOrder(
        symbol=symbol,
        price=round(price, 2),
        amount=request.amount,
        type=request.type,
        value=round(value, 2),
        profit=round(total_profit, 2),
    )


async def sell(
    current_user: schemas.TokenData,
    db: AsyncSession,
    price: float,
    request: schemas.Order,
    symbol: str,
    value: float,
) -> float:
    portfolio_entries = (await db.execute(
        select(models.Portfolio)
        .where(
            models.Portfolio.user_id == current_user.id,
            models.Portfolio.symbol == symbol,
        )
        .order_by(models.Portfolio.created_at.asc())
    )).scalars().all()

    remaining_to_sell = request.amount
    total_profit = 0.0

    for entry in portfolio_entries:
        if remaining_to_sell <= 0:
            break
        if entry.amount <= remaining_to_sell:
            total_profit += (price - float(entry.price)) * entry.amount
            remaining_to_sell -= entry.amount
            await db.delete(entry)
        else:
            total_profit += (price - float(entry.price)) * remaining_to_sell
            entry.amount -= remaining_to_sell
            remaining_to_sell = 0

    await db.execute(
        update(models.User)
        .where(models.User.id == current_user.id)
        .values(cash=models.User.cash + value)
    )
    db.add(models.History(
        symbol=symbol,
        price=price,
        amount=request.amount,
        type=request.type,
        value=value,
        profit=total_profit,
        user_id=current_user.id,
    ))
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database commit failed when trying to sell: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the transaction",
        )
    return total_profit


# Buy logic ---------
async def buy_handler(
    request: schemas.Order,
    db: AsyncSession,
    current_user: schemas.TokenData,
    symbol: str,
    price: float,
    value: float,
) -> schemas.AfterOrder:
    result = await db.execute(
        update(models.User)
        .where(models.User.id == current_user.id, models.User.cash >= value)
        .values(cash=models.User.cash - value)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,
                            detail=f"Insufficient funds to buy {symbol}")

    db.add_all([
        models.Portfolio(
            symbol=symbol,
            amount=request.amount,
            price=price,
            user_id=current_user.id,
        ),
        models.History(
            symbol=symbol,
            price=price,
            amount=request.amount,
            type=request.type,
            value=value,
            profit=0.0,
            user_id=current_user.id,
        ),
    ])
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database commit failed when trying to buy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the transaction",
        )

    return schemas.AfterOrder(
        symbol=symbol,
        price=round(price, 2),
        amount=request.amount,
        type=request.type,
        value=round(value, 2),
        profit=0.0,
    )
