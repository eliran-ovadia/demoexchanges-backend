from fastapi import APIRouter, Depends , status
from exchange import database
from exchange.schemas import TokenData, CreateUser
from sqlalchemy.orm import Session
from .repository import user_repo
from exchange.oauth2 import get_current_user


router = APIRouter(tags=['users'], prefix='/api')
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)


@router.post('/createUser', response_model=str, status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUser, db: Session = check_db) -> str:
    return user_repo.create_user(request, db)


@router.patch('/resetPortfolio/', status_code=status.HTTP_200_OK)
def reset_portfolio(db: Session = check_db, current_user: TokenData = check_auth) -> str:
    return user_repo.reset_portfolio(db, current_user)


@router.delete('/deleteUser/',response_model=str, status_code=status.HTTP_200_OK)
def delete_user(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> dict:
    return user_repo.delete_user(request, db, current_user)
