from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.database.models import MarketStatus
from src.exchange.schemas import TokenData, Pagination
from .repository import info_repo

router = APIRouter(tags=['info'], prefix="/api")
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.get('/parsedQuote', response_model=dict, status_code=status.HTTP_200_OK)
def get_parsed_quote(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return info_repo.get_parsed_quote(request, db)


@router.get('/marketStatus', response_model=bool, status_code=status.HTTP_200_OK)
def fetch_market_status(db: Session = check_db, current_user: TokenData = check_auth) -> MarketStatus:
    return info_repo.fetch_market_status(db)


@router.get('/stockSearch', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def stock_search(prompt: str,
                 pagination: Pagination = Depends(),
                 current_user: TokenData = check_auth) -> Dict[str, Any]:
    return info_repo.stock_search(prompt, pagination.page, pagination.page_size)


@router.get('/marketMovers', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def market_movers(current_user: TokenData = check_auth) -> Dict[str, Any]:
    return info_repo.market_movers()


@router.get('/stockSentiment', response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def stock_sentiment(symbol: str, current_user: TokenData = check_auth) -> Dict[str, Any]:
    return info_repo.stock_sentiment(symbol)
