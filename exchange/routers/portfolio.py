from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from exchange import database
from exchange.schemas import AfterOrder, TokenData, Order, Pagination
from sqlalchemy.orm import Session
from .repository import portfolio
from exchange.oauth2 import get_current_user
from ..models import MarketStatus

router = APIRouter(tags=['portfolio'], prefix="/api")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)


@router.post('/getPortfolio', response_model=dict, status_code=status.HTTP_200_OK)
def get_portfolio(pagination: Pagination, db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return portfolio.get_portfolio(db, current_user, pagination.page, pagination.page_size)


@router.post('/order', response_model=AfterOrder, status_code=status.HTTP_201_CREATED)
def order(request: Order, db: Session = check_db, current_user: TokenData = check_auth) -> AfterOrder:
    return portfolio.order(request, db, current_user)


@router.post('/getHistory', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_history(pagination: Pagination,
                db: Session = check_db,
                current_user: TokenData = check_auth
                ) -> Dict[str, Any]:
    return portfolio.get_history(db, current_user, pagination.page, pagination.page_size)


@router.get('/parsedQuote', response_model=dict, status_code=status.HTTP_200_OK)
def get_parsed_quote(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return portfolio.get_parsed_quote(request, db)


@router.get('/marketStatus', response_model=bool, status_code=status.HTTP_200_OK)
def fetch_market_status(db: Session = check_db, current_user: TokenData = check_auth) -> MarketStatus:
    return portfolio.fetch_market_status(db)