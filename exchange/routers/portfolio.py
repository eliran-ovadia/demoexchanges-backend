from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from exchange import database
from exchange.schemas import AfterOrder, TokenData, Order, Pagination, Stock
from sqlalchemy.orm import Session
from exchange.oauth2 import get_current_user
from .repository import portfolio_repo

router = APIRouter(tags=['portfolio'], prefix="/api")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.get('/getPortfolio', response_model=dict, status_code=status.HTTP_200_OK)
def get_portfolio(pagination: Pagination = Depends(),
                  db: Session = check_db,
                  current_user: TokenData = check_auth) -> dict:
    return portfolio_repo.get_portfolio(db, current_user, pagination.page, pagination.page_size)


@router.post('/order', response_model=AfterOrder, status_code=status.HTTP_201_CREATED)
def order(request: Order, db: Session = check_db, current_user: TokenData = check_auth) -> AfterOrder:
    return portfolio_repo.order(request, db, current_user)


@router.get('/getHistory', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_history(pagination: Pagination = Depends(),
                db: Session = check_db,
                current_user: TokenData = check_auth
                ) -> Dict[str, Any]:
    return portfolio_repo.get_history(db, current_user, pagination.page, pagination.page_size)


@router.post('/addToWatchlist', status_code=status.HTTP_200_OK)
def add_to_watchlist(request: Stock = Depends(), db: Session = check_db, current_user: TokenData = check_auth):
    return portfolio_repo.add_to_watchlist(request, db, current_user)

@router.post('/deleteFromWatchlist', status_code=status.HTTP_200_OK)
def delete_from_watchlist(request: Stock = Depends(), db: Session = check_db, current_user: TokenData = check_auth):
    return portfolio_repo.delete_from_watchlist(request, db, current_user)


@router.get('/getWatchlist', response_model=list[str], status_code=status.HTTP_200_OK)
def get_watchlist(pagination: Pagination = Depends(),
                  db: Session = check_db,
                  current_user: TokenData = check_auth) -> list[str]:
    return portfolio_repo.get_watchlist(db, pagination.page, pagination.page_size, current_user)