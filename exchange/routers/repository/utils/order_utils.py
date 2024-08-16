from exchange import models, schemas
from fastapi import HTTPException, status
from datetime import datetime
from sqlalchemy import func
from exchange.routers.repository.utils.utils import *

def sell_handler(request: schemas.Order, db: Session, user_id, symbol, price, value, user):
    user = get_user(db, user_id)
    value *= -1
    request.amount *= -1
        # Calculate total stock amount for the symbol
    user_total_amount_of_stock = db.query(func.sum(models.Portfolio.amount)).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).scalar()
        
    if user_total_amount_of_stock is None or user_total_amount_of_stock < request.amount:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stocks for selling")
        
    portfolio_entries = db.query(models.Portfolio).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).order_by(models.Portfolio.time_stamp.asc()).all()
        
    amount_copy = request.amount
    for entry in portfolio_entries:
        if amount_copy <= 0:
            break
        if entry.amount <= amount_copy:
            sell_profit += (price - entry.price) * entry.amount
            amount_copy -= entry.amount
            db.delete(entry)
            db.commit()
        else:
            sell_profit += (price - entry.price) * amount_copy
            entry.amount -= amount_copy
            amount_copy = 0
    user.cash += value
    timestamp = datetime.now()
    
    
    

def buy_handler(request, db, current_user, user_id, symbol, price, value, user): #check user and user id to be sent
    user = get_user(db, user_id)
    if user.cash < 0:
        logger.error(f"email: {current_user.email} tried to buy with negative cash")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Negavite amount of cash")
    if user.cash < value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")

    new_portfolio = models.Portfolio(
            symbol=symbol, amount=request.amount, time_stamp=timestamp, price=price, user_id=user_id
        )
    db.add(new_portfolio)
    user.cash -= value
    timestamp = datetime.now()