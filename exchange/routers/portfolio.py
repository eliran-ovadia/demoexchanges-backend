from typing import List
from fastapi import APIRouter, Depends, status
from .. import schemas, database
from sqlalchemy.orm import Session
from .repository import portfolio
from ..oauth2 import get_current_user


router = APIRouter(tags = ['portfolios'], prefix = "/portfolio")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.get('/getpool', response_model = List[schemas.ShowPortfolioForPool]) #return all portfolios-----done!
def all(db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.get_all(db)

@router.get('/getportfolio/', status_code = 200, response_model = List[schemas.ShowPortfolio]) #return portfolio for logged in user
def getPortfolio(db: Session = check_db, current_user: schemas.User = Depends(get_current_user)):
    return portfolio.getPortfolio(db, current_user)




@router.post('/Order/', response_model = str, status_code=status.HTTP_201_CREATED) #buy/sell stocks
def order(request: schemas.Order, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.order(request, db, current_user)







#for testing purpose--------------------------------------------------------------------------------------------

@router.get('/{symbol}', status_code = status.HTTP_200_OK) #just for me to check the stock price
def get_stock_price(symbol: str):
    return portfolio.get_stock_price(symbol)


@router.get('/getQuote{symbols}', status_code = status.HTTP_200_OK) #just for me to check the quote
def get_quote(symbols: str):
    return portfolio.get_quote(symbols)