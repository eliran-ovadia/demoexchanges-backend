from sqlalchemy.orm import Session
from sqlalchemy import func
from exchange import models, schemas
from fastapi import HTTPException, status
from datetime import datetime
from .portfolio_utils import *
from .utils import *
from exchange.app_logger import logger

def order(request: schemas.Order, db: Session, current_user: schemas.TokenData):
    user_id = current_user.id
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot buy/sell more than one stock at once")
    amount = request.amount
    price = float(get_stock_price(symbol)['price'])
    timestamp = datetime.now()
    value = price * amount
    user = db.query(models.User).filter(models.User.id == user_id).first()
    available_cash = user.cash
    sell_profit = 0
    
    if amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be 0")  

    # Sell order
    if amount < 0:
        type = "Sell"
        value *= -1
        amount *= -1
        # Calculate total stock amount for the symbol
        user_total_amount_of_stock = db.query(func.sum(models.Portfolio.amount)).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).scalar()
        
        if user_total_amount_of_stock is None or user_total_amount_of_stock < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stocks for selling")
        
        portfolio_entries = db.query(models.Portfolio).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).order_by(models.Portfolio.time_stamp.asc()).all()
        
        amount_copy = amount
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
    else:  # Buy order
        type = "Buy"
        
        if user.cash < value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")

        new_portfolio = models.Portfolio(
            symbol=symbol, amount=amount, time_stamp=timestamp, price=price, user_id=user_id
        )
        db.add(new_portfolio)
        user.cash -= value

    new_history = models.History(
        symbol=symbol, price=price, amount=amount, type=type, profit=sell_profit,
        value=value, time_stamp=timestamp, user_id=user_id
    )
    
    db.add(new_history)
    db.commit()
    
    return schemas.AfterOrder(symbol=symbol, price=price, amount=amount, type=type, value=value, profit=sell_profit)

def getPortfolio(db: Session, current_user: schemas.TokenData) -> dict:
    portfolio_data = fetch_portfolio_data(db, current_user)

    if not portfolio_data:
        return handle_empty_portfolio(db, current_user)  # If no stocks, return balance with zeroes

    symbols = list(portfolio_data.keys())
    quotes = fetch_quotes(symbols)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return build_portfolio_response(db, current_user, detailed_portfolio_data)

def getHistory(db: Session, current_user: schemas.TokenData) -> list:
    history = db.query(models.History).filter(models.History.user_id == current_user.id).order_by(models.History.time_stamp.desc()).all()
    if not history:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"History table is empty")
    return history