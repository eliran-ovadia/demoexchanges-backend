from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all()
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


def show(id: int, db = Session):
    Portfolio = db.query(models.Portfolio).filter(models.Portfolio.id == id).first()
    if not Portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"blog with id of {id} is not in the database")
    return Portfolio
