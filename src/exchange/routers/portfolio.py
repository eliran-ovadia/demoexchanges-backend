from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.rate_limiter import limiter
from src.exchange.schemas.schemas import AfterOrder, TokenData, Order, Pagination, Stock
from .repository import portfolio_repo

router = APIRouter(tags=['portfolio'], prefix="/api")
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.get('/GetPortfolio', response_model=dict, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_portfolio(
    request: Request,
    pagination: Pagination = Depends(),
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> dict:
    return await portfolio_repo.get_portfolio(db, current_user, pagination.page, pagination.page_size)


@router.post('/Order', response_model=AfterOrder, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def order(
    request: Request,
    body: Order,
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> AfterOrder:
    return await portfolio_repo.order(body, db, current_user)


@router.get('/GetHistory', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_history(
    request: Request,
    pagination: Pagination = Depends(),
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> Dict[str, Any]:
    return await portfolio_repo.get_history(db, current_user, pagination.page, pagination.page_size)


@router.post('/AddToWatchlist', response_model=dict, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def add_to_watchlist(
    request: Request,
    stock: Stock = Depends(),
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
):
    return await portfolio_repo.add_to_watchlist(stock, db, current_user)


@router.delete('/DeleteFromWatchlist', response_model=dict, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def delete_from_watchlist(
    request: Request,
    stock: Stock = Depends(),
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
):
    return await portfolio_repo.delete_from_watchlist(stock, db, current_user)


@router.get('/GetWatchlist', response_model=dict, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_watchlist(
    request: Request,
    pagination: Pagination = Depends(),
    db: AsyncSession = check_db,
    current_user: TokenData = check_auth,
) -> dict:
    return await portfolio_repo.get_watchlist(db, pagination.page, pagination.page_size, current_user)
