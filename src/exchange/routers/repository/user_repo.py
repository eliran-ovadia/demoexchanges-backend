from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.Auth.hashing import Hash
from src.exchange.app_logger import logger
from src.exchange.database import models
from src.exchange.routers.repository.utils.find_user import find_user
from src.exchange.schemas import schemas
from src.exchange.schemas.schemas import MessageResponse


async def create_user(request: schemas.CreateUser, db: AsyncSession) -> MessageResponse:
    new_user = models.User(
        id=str(uuid4()),
        name=request.name,
        last_name=request.last_name,
        email=request.email,
        password=Hash.bcrypt(request.password),
        is_admin=False,
        cash=100_000,
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already taken")
    return MessageResponse(message=f"Created a new user with email: {request.email}")


async def reset_portfolio(db: AsyncSession, current_user: schemas.TokenData) -> MessageResponse:
    user = await find_user(db, user_id=current_user.id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not located")
    await db.execute(delete(models.Portfolio).where(models.Portfolio.user_id == user.id))
    await db.execute(delete(models.History).where(models.History.user_id == user.id))
    user.cash = 100_000
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An error occurred while attempting to reset the portfolio.")
    return MessageResponse(message="Portfolio is now empty and cash reset to $100,000")


async def delete_user(request: str, db: AsyncSession, current_user: schemas.TokenData) -> MessageResponse:
    requesting_user = await find_user(db, user_id=current_user.id)
    if not requesting_user or not requesting_user.is_admin:
        logger.warning(f"Unauthorized delete attempt by {current_user.email}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete accounts")

    try:
        user_to_delete = await find_user(db, email=request)
        if not user_to_delete:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if user_to_delete.is_admin:
            logger.warning(f"Attempt to delete admin user {user_to_delete.email} by {current_user.email}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin users cannot be deleted")

        await db.delete(user_to_delete)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"An error occurred while attempting to delete {user_to_delete.email}")

        logger.info(f"User {request} deleted by admin {current_user.email}")
        return MessageResponse(message="User has been deleted")

    except HTTPException as e:
        logger.warning(f"Failed to delete user {request}: {e.detail}")
        raise e
    except Exception as exc:
        logger.error(f"Unexpected error while deleting user {request}: {str(exc)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
