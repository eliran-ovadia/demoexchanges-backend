from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from .. import schemas, database
from sqlalchemy.orm import Session
from .repository import portfolio
from ..oauth2 import get_current_user


router = APIRouter(tags = ['portfolio'], prefix = "/api/portfolio")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)
        

@router.get('/getPool', response_model = List[schemas.ShowPortfolioForPool]) #returns the portfolio table - testing only
def all(db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.get_all(db)

@router.get('/getPortfolio', status_code = 200, response_model = dict)
def getPortfolio(db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.getPortfolio(db, current_user)

@router.get('/getPortfolioStream', status_code=200)
def get_portfolio_stream(db: Session = check_db, current_user: schemas.User = check_auth):
    return StreamingResponse(portfolio.event_stream(db, current_user), media_type="text/event-stream")

@router.post('/Order', response_model = schemas.AfterOrder, status_code=status.HTTP_201_CREATED)
def order(request: schemas.Order, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.order(request, db, current_user)

@router.get('/getHistory',response_model = List[schemas.History], status_code = status.HTTP_200_OK)
def getHistory(db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.getHistory(db, current_user)



#for testing purpose--------------------------------------------------------------------------------------------

@router.get('/getStockPrice', status_code = status.HTTP_200_OK) #just for me to check the stock price
def get_stock_price(symbol: str):
    return portfolio.get_stock_price(symbol)


@router.get('/getQuote', status_code = status.HTTP_200_OK) #just for me to check the quote
def get_quote(symbols: str):
    return portfolio.get_quote(symbols)