from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from typing import List

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
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


# def update(id: int, db: Session, request: schemas.Portfolio):
#     Portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == id)
#     if not Portfolio:
#         raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"blog id number {id} not found")
#     Portfolio.update({models.Portfolio.title: request.title, models.Portfolio.body: request.body})
#     db.commit()
#     return db.query(models.Portfolio).filter(models.Portfolio.id == id).first()


def getPortfolio(email: str, db: Session):
    requestedUser: schemas.User = db.query(models.User).filter(models.User.email == email).first()
    portfolio = requestedUser.portfolio
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"portfolio for account: {email} - not found")
    return portfolio
