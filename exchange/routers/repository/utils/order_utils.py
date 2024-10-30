from datetime import datetime
from sqlalchemy import func
from exchange import schemas, models
from exchange.routers.repository.utils.utils import *


def sell_handler(request: schemas.Order, db: Session, current_user: schemas.TokenData, symbol: str, price: float,
                 value: float):
    user = find_user(db, current_user.id)

    total_owned_stock = db.query(func.sum(models.Portfolio.amount)).filter(
        models.Portfolio.user_id == user.id,
        models.Portfolio.symbol == symbol
    ).scalar() or 0

    if total_owned_stock < request.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Short selling is not supported at the moment, you can sell a maximum of {total_owned_stock} stocks")

    portfolio_entries = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == user.id,
        models.Portfolio.symbol == symbol
    ).order_by(models.Portfolio.time_stamp.asc()).all()

    remaining_amount_to_sell = request.amount
    total_profit = 0.0

    for entry in portfolio_entries:
        if remaining_amount_to_sell <= 0:
            break

        if entry.amount <= remaining_amount_to_sell:
            total_profit += (price - entry.price) * entry.amount
            remaining_amount_to_sell -= entry.amount
            db.delete(entry)  #delete entire row
        else:
            total_profit += (price - entry.price) * remaining_amount_to_sell
            entry.amount -= remaining_amount_to_sell  #delete part of the row
            remaining_amount_to_sell = 0

    user.cash += value

    transaction_time = datetime.now()
    transaction_history = models.History(
        symbol=symbol,
        price=price,
        amount=request.amount,
        type=request.type,
        value=value,
        profit=total_profit,
        time_stamp=transaction_time,
        user_id=user.id
    )
    db.add(transaction_history)
    db.commit()

    return schemas.AfterOrder(
        symbol=symbol,
        price=round(price, 2),
        amount=request.amount,
        type=request.type,
        value=round(value, 2),
        profit=round(total_profit, 2)
    )


def buy_handler(request: schemas.Order, db: Session, current_user: schemas.TokenData, symbol: str, price: float,
                value: float):
    user = find_user(db, current_user.id, )

    if user.cash < value:
        logger.error(f"User {current_user.email} attempted to buy with insufficient cash.")
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Insufficient cash for buying")

    user.cash -= value

    # insert portfolio and history rows
    transaction_time = datetime.now()
    new_portfolio_entry = models.Portfolio(
        symbol=symbol,
        amount=request.amount,
        time_stamp=transaction_time,
        price=price,
        user_id=user.id
    )
    db.add(new_portfolio_entry)

    transaction_history = models.History(
        symbol=symbol,
        price=price,
        amount=request.amount,
        type=request.type,
        value=value,
        profit=0.0,  # No profit for buy order
        time_stamp=transaction_time,
        user_id=user.id
    )
    db.add(transaction_history)
    db.commit()

    return schemas.AfterOrder(
        symbol=symbol,
        price=round(price, 2),
        amount=request.amount,
        type=request.type,
        value=round(value, 2),
        profit=0.0
    )
