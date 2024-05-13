from sqlalchemy.orm import Session
from sqlalchemy import func
from ... import models, schemas
from fastapi import HTTPException, status
from typing import List
from twelvedata import TDClient
from datetime import datetime

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolios table is empty")
    return portfolios



    '''_summary_
    thing to check:
    order value is not bigger than cash
    check for a large negative value
    check if can get the price for my symbol
    check if the value is taken from users cash
    '''

def order(request: schemas.Order, db: Session, current_user: schemas.TokenData):
    user_id = current_user.id
    symbol = request.symbol.upper()
    amount = request.amount
    price = float(get_stock_price(symbol))
    timestamp = datetime.now()
    value = price * amount
    user = db.query(models.User).filter(models.User.id == user_id).first()
    availbale_cash = user.cash
    
    if amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be 0")
    

    #Sell order-----------------------------------------------------------------------------------------------------------
    if amount < 0:
        type = "Sell"
        value *= -1
        amount *= -1
        
        #calculated total stocks amount for symbol
        user_total_amount_of_stcok = db.query(func.sum(models.Portfolio.amount)).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
            ).scalar()
        
        if user_total_amount_of_stcok is None or user_total_amount_of_stcok < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock for selling")
        
        portfolio_entries = db.query(models.Portfolio).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).order_by(models.Portfolio.time_stamp.asc()).all()
        
        amount_copy = amount
        for entry in portfolio_entries:
            if amount_copy <= 0:
                break
            if entry.amount <= amount_copy:
                amount_copy -= entry.amount
                db.delete(entry)
                db.commit()
            else:
                entry.amount -= amount_copy
                amount_copy = 0
        user.cash += value
    else: #Buy order------------------------------------------------------------------------------------------------------
        type = "Buy"
        
        if user.cash < value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")

        new_portfolio = models.Portfolio(
            symbol=symbol, amount=amount, time_stamp=timestamp, user_id=user_id
        )
        db.add(new_portfolio)
        user.cash -= value
#-------------------------------------------------------------------------------------------------------------------------

    new_history = models.History(
        symbol=symbol, price=price, amount=amount, type=type,
        value=value, time_stamp=timestamp, user_id=user_id)
    
    db.add(new_history)
    db.commit()
    return f"stock: {symbol}   type: {type}    amount: {amount}    price: {price}    value: {value}"
        


def getPortfolio(db: Session, current_user: schemas.TokenData):
    portfolios = List[schemas.ShowPortfolio]
    portfolios = db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).all()
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolio table is empty")
    return portfolios
    
    


def get_stock_price(symbol: str):
    
    td = TDClient(apikey="375f5ab7748a4ddb807d4c810bae5cf2")
    stock = td.price(symbol = symbol).as_json()
    if not stock:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"stock with symbol: {symbol} - not found")
    return str(stock['price'])