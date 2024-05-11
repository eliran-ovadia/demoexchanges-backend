from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from typing import List
from twelvedata import TDClient

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolios table is empty")
    return portfolios

def order(email:str, request: schemas.Order, db: Session):
    new_order = models.Portfolio(symbol = request.symbol.upper(), amount = request.amount, user_id = db.query(models.User).filter(models.User.email == email).first().id)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order

def deleteportfolio(email: str, db: Session):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User with email {email} not found")
    if user.id == "admin":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Admin is not deletable.")
    
    userPortfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).all()
    if not userPortfolio:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolio for the user: {email} not found")
    for portfolio in userPortfolio:
        db.delete(portfolio)
    db.commit()
    return {'detail': f'deleted the entire portfolio for user: {email}'}

def getPortfolio(db: Session, current_user: schemas.TokenData):
    portfolios = List[schemas.ShowPortfolio]
    for portfolio in portfolios:
        portfolio.price = get_stock_price(portfolio.symbol)
    return portfolios
    pass
    


def get_stock_price(symbol: str):
    
    td = TDClient(apikey="375f5ab7748a4ddb807d4c810bae5cf2")
    stock = td.price(symbol = symbol).as_json()
    if not stock:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"stock with symbol: {symbol} - not found")
    return str(stock['price'])