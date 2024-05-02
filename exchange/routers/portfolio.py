from typing import List
from fastapi import APIRouter, Depends, status
from .. import schemas, database
from sqlalchemy.orm import Session
from .repository import portfolio
from ..oauth2 import get_current_user


router = APIRouter(tags = ['portfolios'], prefix = "/portfolio")
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.get('/', response_model = List[schemas.ShowPortfolio])
def all(db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.get_all(db)

@router.get('/getportfolio/{email}', status_code = 200, response_model = List[schemas.ShowPortfolio])
def getPortfolio(email: str, db: Session = check_db, current_user: schemas.User = Depends(get_current_user)):
    return portfolio.getPortfolio(email, db)

@router.post('/Order/{email}', response_model = schemas.ShowPortfolio, status_code=status.HTTP_201_CREATED)
def order(email: str, request: schemas.Order, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.order(email, request, db)

@router.put('/{id}', status_code = status.HTTP_202_ACCEPTED)
def update(id,request: schemas.Order, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.update(id, db, request)


@router.delete('/{id}',status_code = status.HTTP_204_NO_CONTENT)
def destroy(id, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.destroy(id, db)