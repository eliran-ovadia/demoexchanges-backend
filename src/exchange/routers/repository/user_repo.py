from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.exchange import schemas
from src.exchange.app_logger import logger
from src.exchange.database import models
from src.exchange.hashing import Hash
from src.exchange.routers.repository.utils.utils import find_user


def create_user(request: schemas.CreateUser, db: Session) -> dict[str, str]:
    if find_user(db, email=request.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already taken")
    new_user = models.User(
        id=str(uuid4()),
        name=request.name,
        last_name=request.last_name,
        email=request.email,
        password=Hash.bcrypt(request.password),
        is_admin=False,
        cash=100_000
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        logger.debug(f"a new user with email {request.email} errored at creation")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="encountered an error")
    return {"message": f"Created a new user with email: {request.email}"}


def reset_portfolio(db: Session, current_user: schemas.TokenData) -> dict[str, str]:
    user = find_user(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user not located")
    db.query(models.Portfolio).filter(models.Portfolio.user_id == user.id).delete()
    db.query(models.History).filter(models.History.user_id == user.id).delete()
    user.cash = 100_000
    db.commit()
    return {"message": "Portfolio is now empty and cash reset to $100,000"}


def delete_user(request: str, db: Session, current_user: schemas.TokenData) -> dict[str, str]:
    if not current_user.is_admin:
        logger.warning(f"Unauthorized delete attempt by {current_user.email}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authorized to delete accounts")

    try:
        user_to_delete = find_user(db, email=request)

        if user_to_delete.is_admin:
            logger.warning(f"Attempt to delete admin user {user_to_delete.email} by {current_user.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot be deleted")

        db.delete(user_to_delete)
        db.commit()

        logger.info(f"User {request} deleted by admin {current_user.email}")
        return {"message": "User has been deleted"}

    except HTTPException as http_exc:
        logger.warning(f"Failed to delete user {request}: {http_exc.detail}")
        raise http_exc
    except Exception as exc:
        logger.error(f"Unexpected error occurred while trying to delete user {request}: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
