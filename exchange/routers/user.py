from fastapi import APIRouter, Depends , status
from exchange import database, schemas
from sqlalchemy.orm import Session
from .repository import user
from exchange.oauth2 import get_current_user


router = APIRouter(tags = ['users'], prefix = '/api')
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.post('/createUser', response_model = str, status_code = status.HTTP_201_CREATED)
def create_user(request: schemas.CreateUser, db: Session = check_db) -> str:
    return user.create_user(request, db)

@router.patch('/resetPortfolio/', status_code = status.HTTP_200_OK)
def reset_portfolio(db: Session = check_db, current_user: schemas.TokenData = check_auth) -> str:
    return user.reset_portfolio(db, current_user)

@router.delete('/deleteUser/', status_code = status.HTTP_202_ACCEPTED)
def delete_user(email: str, db: Session = check_db, current_user: schemas.TokenData = check_auth) -> dict:
    return user.delete_user(email, db, current_user)