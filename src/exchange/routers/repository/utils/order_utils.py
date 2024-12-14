from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func

from src.exchange.app_logger import logger
from src.exchange.database import models
from src.exchange.routers.repository.utils.find_user import *
from src.exchange.schemas import schemas


##################### Sell logic #####################
def sell_handler(request: schemas.Order, db: Session, current_user: schemas.TokenData, symbol: str, price: float,
                 value: float):
    total_owned_stock = db.query(func.sum(models.Portfolio.amount)).filter(
        models.Portfolio.user_id == current_user.id,
        models.Portfolio.symbol == symbol
    ).scalar() or 0

    if total_owned_stock < request.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Short selling is not supported at the moment,"
                                   f"you can sell a maximum of {total_owned_stock} stocks""")

    total_profit = sell(current_user, db, price, request, symbol, value)

    return schemas.AfterOrder(
        symbol=symbol,
        price=round(price, 2),
        amount=request.amount,
        type=request.type,
        value=round(value, 2),
        profit=round(total_profit, 2)
    )


def sell(current_user: schemas.TokenData, db: Session, price: float, request: schemas.Order, symbol: str, value: float):
    portfolio_entries = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == current_user.id,
        models.Portfolio.symbol == symbol
    ).order_by(models.Portfolio.time_stamp.asc()).yield_per(100)
    remaining_amount_to_sell = request.amount
    total_profit = 0.0
    for entry in portfolio_entries:
        if remaining_amount_to_sell <= 0:
            break

        if entry.amount <= remaining_amount_to_sell:
            total_profit += (price - entry.price) * entry.amount
            remaining_amount_to_sell -= entry.amount
            db.delete(entry)  # Delete entire row
        else:
            total_profit += (price - entry.price) * remaining_amount_to_sell
            entry.amount -= remaining_amount_to_sell  # Update entry amount
            remaining_amount_to_sell = 0
    db.query(models.User).filter(models.User.id == current_user.id).update(
        {models.User.cash: models.User.cash + value}
    )
    transaction_time = datetime.now()
    db.add(
        models.History(
            symbol=symbol,
            price=price,
            amount=request.amount,
            type=request.type,
            value=value,
            profit=total_profit,
            time_stamp=transaction_time,
            user_id=current_user.id
        )
    )
    try:
        db.commit()  # Atomic action
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed when trying to sell: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the transaction"
        )
    return total_profit


##################### Buy logic #####################
def buy_handler(request: schemas.Order, db: Session, current_user: schemas.TokenData, symbol: str, price: float,
                value: float):
    affected_rows = (
        db.query(models.User)
        .filter(models.User.id == current_user.id, models.User.cash >= value)
        .update({models.User.cash: models.User.cash - value})
    )
    if affected_rows == 0:
        logger.error(f"User {current_user.email} attempted to buy with insufficient cash.")
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=f"Insufficient cash for buying {symbol}")

    # Insert portfolio and history rows
    transaction_time = datetime.now()
    new_portfolio_entry = models.Portfolio(symbol=symbol, amount=request.amount, time_stamp=transaction_time,
                                           price=price,
                                           user_id=current_user.id
                                           )

    transaction_history = models.History(symbol=symbol, price=price, amount=request.amount, type=request.type,
                                         value=value,
                                         profit=0.0,  # No profit for buy order
                                         time_stamp=transaction_time,
                                         user_id=current_user.id
                                         )

    db.add_all([new_portfolio_entry, transaction_history])
    try:
        db.commit()  # Atomic action
    except Exception as e:
        db.rollback()
        logger.error(f"Database commit failed when trying to buy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the transaction"
        )

    return schemas.AfterOrder(symbol=symbol,
                              price=round(price, 2),
                              amount=request.amount,
                              type=request.type,
                              value=round(value, 2),
                              profit=0.0
                              )
