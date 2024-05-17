from sqlalchemy.orm import Session
from ... import models, schemas
from fastapi import HTTPException, status
from ...hashing import Hash
from uuid import uuid4



def create_user(request: schemas.CreateUser, db: Session):
    new_user = models.User(id = str(uuid4()),name = request.name, email = request.email, password = Hash.bcrypt(request.password),cash = 100_000, is_admin = False)
    same_email_user = db.query(models.User).filter(models.User.email == request.email).first()
    if same_email_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail = f"a user with the same email is already exists in the exchange")
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refreshing the new_user to be able to return the newly created user
    return "Created a new user"


def get_user(db: Session, current_user: schemas.TokenData): # not really a nessecery endpoint
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user not located in the database")
    return user



def resetPortfolio(db: Session, current_user: schemas.TokenData):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user not located in the database")
    db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).delete()
    db.query(models.History).filter(models.History.user_id == user.id).delete()
    user.cash = 100_000
    db.commit()
    return "Portfolio is now empty and cash reset to $100,000"

def delete_user(db: Session, current_user: schemas.TokenData):
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