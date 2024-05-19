from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from ... import models, schemas
from fastapi import HTTPException, status
from ...hashing import Hash
from uuid import uuid4

def create_user(request: schemas.CreateUser, db: Session):
    Hashed_password = Hash.bcrypt(request.password)
    new_user = models.User(
        id=str(uuid4()),
        name=request.name,
        last_name=request.last_name,
        email=request.email,
        password = Hashed_password,
        cash=100_000,
        is_admin=False
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail=f"Email {request.email} is already taken by another user")
    
    return f"Created a new user with email: {request.email}"


def get_user(email: str, db: Session, current_user: schemas.TokenData): # endpoint for admin
    user_to_return = db.query(models.User).filter(models.User.email == email).first()
    if current_user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail = "Needs admin permission to perform this action")
    if not user_to_return:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user not located in the database")
    return user_to_return



def resetPortfolio(db: Session, current_user: schemas.TokenData):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user not located in the database")
    db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).delete()
    db.query(models.History).filter(models.History.user_id == user.id).delete()
    user.cash = 100_000
    db.commit()
    return "Portfolio is now empty and cash reset to $100,000"

def delete_user(email: str, db: Session, current_user: schemas.TokenData): # FIX TO CHECK IF USER IS ADMIN + CHECK USER EMAIL GIVEN BY ADMIN
    user = db.query(models.User).filter(models.User.email == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")

    # Check if the user is an admin
    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot be deleted")

    # Delete the user
    db.delete(user)
    db.commit()

    return {"message": f"User has been deleted"}