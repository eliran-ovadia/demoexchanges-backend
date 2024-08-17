from typing import List
from fastapi import APIRouter, Depends, status
from exchange import schemas, database
from sqlalchemy.orm import Session
from .repository import portfolio
from exchange.oauth2 import get_current_user

router = APIRouter(tags = ['portfolio'], prefix = "/api")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.get('/getPortfolio', status_code = status.HTTP_200_OK, response_model = dict)
def getPortfolio(db: Session = check_db, current_user: schemas.User = check_auth) -> dict:
    return portfolio.getPortfolio(db, current_user)

@router.post('/Order', response_model = schemas.AfterOrder, status_code=status.HTTP_201_CREATED)
def order(request: schemas.Order, db: Session = check_db, current_user: schemas.User = check_auth)  -> schemas.AfterOrder:
    return portfolio.order(request, db, current_user)

@router.get('/getHistory',response_model = List[schemas.History], status_code = status.HTTP_200_OK)
def getHistory(db: Session = check_db, current_user: schemas.User = check_auth) -> List[schemas.History]:
    return portfolio.getHistory(db, current_user)

