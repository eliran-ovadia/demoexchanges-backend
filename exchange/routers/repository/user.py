from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from exchange import models, schemas
from fastapi import HTTPException, status
from exchange.app_logger import logger
from exchange.hashing import Hash
from uuid import uuid4
from exchange.routers.repository.utils.utils import find_user

def create_user(request: schemas.CreateUser, db: Session) -> str:
    if find_user(db, email=request.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already taken")
    new_user = models.User(
        id = str(uuid4()),
        name = request.name,
        last_name = request.last_name,
        email = request.email,
        password = Hash.bcrypt(request.password),
        is_admin = False,
        cash = 100_000
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        logger.debug(f"a new user with email {request.email} errored at creation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail = "encountered an error")
    return f"Created a new user with email: {request.email}"

def reset_portfolio(db: Session, current_user: schemas.TokenData) -> str:
    user = find_user(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"user not located")
    db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).delete()
    db.query(models.History).filter(models.History.user_id == user.id).delete()
    user.cash = 100_000
    db.commit()
    return "Portfolio is now empty and cash reset to $100,000"

def delete_user(email: str, db: Session, current_user: schemas.TokenData) -> dict: # FIX TO CHECK IF USER IS ADMIN + CHECK USER EMAIL GIVEN BY ADMIN
    user_to_delete = db.query(models.User).filter(models.User.email == email).first()
    if not user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User not found")
    # Check if the user is an admin
    if user_to_delete.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot be deleted")

    db.delete(user_to_delete)
    db.commit()
    return {"message": f"User with email: {email} - has been deleted"}