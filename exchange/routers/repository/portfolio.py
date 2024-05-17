from sqlalchemy.orm import Session
from sqlalchemy import func
from ... import models, schemas
from fastapi import HTTPException, status
from typing import List
from twelvedata import TDClient
from datetime import datetime
from fastapi.responses import JSONResponse
def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolios table is empty")
    return portfolios


def order(request: schemas.Order, db: Session, current_user: schemas.TokenData):
    user_id = current_user.id
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "cannot buy/sell more than one stock at once")
    amount = request.amount
    price = float(get_stock_price(symbol)['price'])
    timestamp = datetime.now()
    value = price * amount
    user = db.query(models.User).filter(models.User.id == user_id).first()
    availbale_cash = user.cash
    sell_profit = 0
    
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
    else: #Buy order------------------------------------------------------------------------------------------------------
        type = "Buy"
        
        if user.cash < value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")

        new_portfolio = models.Portfolio(
            symbol = symbol, amount = amount, time_stamp = timestamp,price = price, user_id = user_id
        )
        db.add(new_portfolio)
        user.cash -= value
#-------------------------------------------------------------------------------------------------------------------------

    new_history = models.History(
        symbol=symbol, price=price, amount=amount, type=type, profit = sell_profit,
        value=value, time_stamp=timestamp, user_id=user_id)
    
    db.add(new_history)
    db.commit()
    return f"stock: {symbol}   type: {type}    amount: {amount}    price: {price}    value: {value}   profit: {sell_profit}"
        


def getPortfolio(db: Session, current_user: schemas.TokenData):
    portfolios = List[schemas.ShowPortfolio]
    portfolios = db.query(models.Portfolio).filter(models.Portfolio.user_id == current_user.id).all()
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolio table is empty")
    return portfolios
    
    
def getHistory(db: Session, current_user: schemas.TokenData):
    history = db.query(models.History).filter(models.History.user_id == current_user.id).order_by(models.History.time_stamp.desc()).all()
    if not history:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"History table is empty")
    return history




#TwelveData handlers---------------------------------------------------------------------

def get_stock_price(symbol: str):
    
    td = TDClient(apikey="375f5ab7748a4ddb807d4c810bae5cf2")
    try:
        stock = td.price(symbol = symbol).as_json()
    except:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"price for symbol: {symbol} - not found")
    return stock



def get_quote(symbols: str):
    td = TDClient(apikey="375f5ab7748a4ddb807d4c810bae5cf2")
    try:
        stock = td.quote(symbol=symbols).as_json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quote for one of the symbols: {symbols} - not found")
    return stock