from typing import Any

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.Auth.oauth2 import get_current_user
from src.exchange.database.db_conn import get_db
from src.exchange.rate_limiter import limiter
from src.exchange.routers.repository.info_repo import parsed_quote, market_status, stock_search, stock_sentiment, \
    market_movers
from src.exchange.schemas.fmp_schemas import SearchResponse, MarketStatusResponse, ParsedQuoteResponse, \
    MarketMoversResponse, SentimentEntry
from src.exchange.schemas.schemas import TokenData, Pagination

router = APIRouter(tags=['info'], prefix="/api")
check_db = Depends(get_db)
check_auth = Depends(get_current_user)


@router.get('/quote', response_model=dict[str, ParsedQuoteResponse], status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def get_parsed_quote(request: Request, symbol: str, current_user: TokenData = check_auth) -> dict[str, ParsedQuoteResponse]:
    return await parsed_quote(symbol)


@router.get('/market-status', response_model=MarketStatusResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def get_market_status(request: Request, db: AsyncSession = check_db, current_user: TokenData = check_auth) -> dict[str, Any]:
    return await market_status(db)


@router.get('/search', response_model=SearchResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def get_stock_search(
    request: Request,
    symbol: str,
    pagination: Pagination = Depends(),
    current_user: TokenData = check_auth,
) -> SearchResponse:
    return await stock_search(symbol, pagination.page, pagination.page_size)


@router.get('/market-movers', response_model=MarketMoversResponse, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def get_market_movers(request: Request, current_user: TokenData = check_auth) -> MarketMoversResponse:
    return await market_movers()


@router.get('/sentiment', response_model=SentimentEntry, status_code=status.HTTP_200_OK)
@limiter.limit("20/minute")
async def get_stock_sentiment(request: Request, symbol: str, current_user: TokenData = check_auth) -> dict[str, Any]:
    return await stock_sentiment(symbol)
