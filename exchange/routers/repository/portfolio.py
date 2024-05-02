from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from typing import List

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
    return portfolios

def create(request: schemas.Portfolio, db: Session):
    new_blog = models.Portfolio(title = request.title, body = request.body, user_id = 1)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

def destroy(id: int, db: Session):
    Portfolio = db.query(models.Portfolio).filter(models.Portfolio.id ==id)
    if not Portfolio:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Blog with id {id} not found")
    Portfolio.delete(synchronize_session=False)
    db.commit()
    return {'detail': f'deleted blog number {id}'}


def update(id: int, db: Session, request: schemas.Portfolio):
    Portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == id)
    if not Portfolio:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"blog id number {id} not found")
    Portfolio.update({models.Portfolio.title: request.title, models.Portfolio.body: request.body})
    db.commit()
    return db.query(models.Portfolio).filter(models.Portfolio.id == id).first()


def getPortfolio(email: str, db: Session, current_user: schemas.User):
    requestedUser: schemas.User = db.query(models.User).filter(models.User.email == email).first()
    portfolio = requestedUser.portfolio
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"portfolio for account: {current_user.name} - not found")
    return portfolio
