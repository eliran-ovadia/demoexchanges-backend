from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from ...hashing import Hash
from uuid import uuid4



def create_user(request: schemas.CreateUser, db: Session):
    new_user = models.User(id = str(uuid4()),name = request.name, email = request.email, password = Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refreshing the new_user to be able to return the newly created user
    return new_user


def get_user(email: str, db: Session):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with id of {id} is not in the database")
    return user

def delete_user(email: str, db: Session):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with email of {email} is not found")
    
    userPortfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).all()
    if not userPortfolio:
        no_portfolio_messege = ", this user did not had stocks in his portfolio"

    for portfolio in userPortfolio:
        db.delete(portfolio)
    db.delete(user)
    db.commit()
    return f"deleted user with email: {email}" + no_portfolio_messege