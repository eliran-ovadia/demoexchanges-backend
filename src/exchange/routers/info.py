from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.routers.repository.info_repo import parsed_quote, market_status, stock_search, stock_sentiment, \
    market_movers
from src.exchange.schemas import TokenData, Pagination

router = APIRouter(tags=['info'], prefix="/api")
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.get('/ParsedQuote', response_model=dict, status_code=status.HTTP_200_OK)
def get_parsed_quote(request: str, current_user: TokenData = check_auth) -> dict:
    return parsed_quote(request)


@router.get('/MarketStatus', response_model=dict[str, Any], status_code=status.HTTP_200_OK)
def get_market_status(db: Session = check_db, current_user: TokenData = check_auth) -> dict[str, Any]:
    return market_status(db)


@router.get('/StockSearch', response_model=dict[str, Any], status_code=status.HTTP_200_OK)
def get_stock_search(request: str,
                     pagination: Pagination = Depends(),
                     current_user: TokenData = check_auth, ) -> dict[str, Any]:
    return stock_search(request, pagination.page, pagination.page_size)


@router.get('/MarketMovers', response_model=dict[str, Any], status_code=status.HTTP_200_OK)
def get_market_movers(current_user: TokenData = check_auth) -> dict[str, Any]:
    return market_movers()


@router.get('/StockSentiment', response_model=dict[str, Any], status_code=status.HTTP_200_OK)
def get_stock_sentiment(request: str, current_user: TokenData = check_auth) -> list[dict[str, Any]]:
    return stock_sentiment(request)
