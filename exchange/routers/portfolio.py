from typing import List
from fastapi import APIRouter, Depends, status
from exchange import database
from exchange.schemas import AfterOrder, History, TokenData, Order, RawQuote
from sqlalchemy.orm import Session
from .repository import portfolio
from exchange.oauth2 import get_current_user

router = APIRouter(tags=['portfolio'], prefix="/api")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)


@router.get('/getPortfolio', response_model=dict, status_code=status.HTTP_200_OK)
def get_portfolio(db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return portfolio.get_portfolio(db, current_user)


@router.post('/order', response_model=AfterOrder, status_code=status.HTTP_201_CREATED)
def order(request: Order, db: Session = check_db, current_user: TokenData = check_auth) -> AfterOrder:
    return portfolio.order(request, db, current_user)


@router.get('/getHistory',response_model=List[History], status_code=status.HTTP_200_OK) #change to Dict
def get_history(db: Session = check_db, current_user: TokenData = check_auth) -> List[History]:
    return portfolio.get_history(db, current_user)


@router.get('/parsedQuote', response_model=RawQuote, status_code=status.HTTP_200_OK)
def get_parsed_quote(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> RawQuote:
    return portfolio.get_parsed_quote(request, db)