from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.schemas import TokenData, Pagination
from src.exchange.routers.repository.info_repo import get_parsed_quote, market_status,  stock_search, stock_sentiment

router = APIRouter(tags=['info'], prefix="/api")
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.get('/parsedQuote', response_model=dict, status_code=status.HTTP_200_OK)
def get_parsed_quote(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return get_parsed_quote(request, db)


@router.get('/marketStatus', response_model=dict[str, Any], status_code=status.HTTP_200_OK)
def market_status(db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return market_status(db)


@router.get('/stockSearch', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def stock_search(request: str,
                 pagination: Pagination = Depends(),
                 current_user: TokenData = check_auth, ) -> Dict[str, Any]:
    return stock_search(request, pagination.page, pagination.page_size)


@router.get('/marketMovers', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def market_movers(current_user: TokenData = check_auth) -> Dict[str, Any]:
    return market_movers()


@router.get('/stockSentiment', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def stock_sentiment(request: str, current_user: TokenData = check_auth) -> Dict[str, Any]:
    return stock_sentiment(request)
