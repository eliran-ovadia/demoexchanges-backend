from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.rate_limiter import limiter
from src.exchange.schemas.schemas import TokenData, CreateUser
from .repository import user_repo

router = APIRouter(tags=['users'], prefix='/api')
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.post('/CreateUser', response_model=dict[str, str], status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_user(request: Request, body: CreateUser, db: AsyncSession = check_db) -> dict[str, str]:
    return await user_repo.create_user(body, db)


@router.patch('/ResetPortfolio/', response_model=dict[str, str], status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def reset_portfolio(
    request: Request,
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> dict[str, str]:
    return await user_repo.reset_portfolio(db, current_user)


@router.delete('/DeleteUser/', response_model=dict[str, str], status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    email: str,
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> dict[str, str]:
    return await user_repo.delete_user(email, db, current_user)
