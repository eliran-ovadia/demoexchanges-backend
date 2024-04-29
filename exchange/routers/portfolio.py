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

@router.get('/{id}', status_code = 200, response_model = schemas.ShowPortfolio)
def show(id, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.show(id, db)

@router.post('/', status_code=status.HTTP_201_CREATED)
def create(request: schemas.Portfolio, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.create(request, db)

@router.put('/{id}', status_code = status.HTTP_202_ACCEPTED)
def update(id,request: schemas.Portfolio, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.update(id, db, request)


@router.delete('/{id}',status_code = status.HTTP_204_NO_CONTENT)
def destroy(id, db: Session = check_db, current_user: schemas.User = check_auth):
    return portfolio.destroy(id, db)