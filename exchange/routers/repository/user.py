from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from ...hashing import Hash
from uuid import uuid4



def create_user(request: schemas.CreateUser, db: Session):
    new_user = models.User(id = str(uuid4()),name = request.name, email = request.email, password = Hash.bcrypt(request.password), is_admin = request.is_admin)
    same_email_user = db.query(models.User).filter(models.User.email == request.email).first()
    if same_email_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"a user with the same email is already exists in the exchange")
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refreshing the new_user to be able to return the newly created user
    return new_user


def get_user(current_user: schemas.TokenData, db: Session):
    user = db.query(models.User).filter(models.User.email == current_user.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with id of {current_user.email} is not in the database")
    return user

def delete_user(email: str, db: Session):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with email of {email} is not found")
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"Admin user is not deletable")
    
    userPortfolio = db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).all()
    if not userPortfolio:
        no_portfolio_messege = ", this user did not had stocks in his portfolio"

    for portfolio in userPortfolio:
        db.delete(portfolio)
    db.delete(user)
    db.commit()
    return f"deleted user with email: {email}" + no_portfolio_messege