from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from exchange import database
from exchange.oauth2 import get_current_user
from exchange.schemas import TokenData, CreateUser
from .repository import user_repo

router = APIRouter(tags=['users'], prefix='/api')
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)


@router.post('/createUser', response_model=dict[str, str], status_code=status.HTTP_201_CREATED)
def create_user(request: CreateUser, db: Session = check_db) -> dict[str, str]:
    return user_repo.create_user(request, db)


@router.patch('/resetPortfolio/',response_model=dict[str, str] , status_code=status.HTTP_200_OK)
def reset_portfolio(db: Session = check_db, current_user: TokenData = check_auth) -> dict[str, str]:
    return user_repo.reset_portfolio(db, current_user)


@router.delete('/deleteUser/', response_model=dict[str, str], status_code=status.HTTP_200_OK)
def delete_user(request: str, db: Session = check_db, current_user: TokenData = check_auth) -> dict[str, str]:
    return user_repo.delete_user(request, db, current_user)
