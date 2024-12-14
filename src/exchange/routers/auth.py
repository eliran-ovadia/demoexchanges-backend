from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.exchange.database.db_conn import get_db
from src.exchange.routers.repository.auth_repo import get_bearer_token
from src.exchange.schemas.schemas import Token

router = APIRouter(tags=['Authentication'])
check_db = Depends(get_db)


@router.post('/Token')
def get_token(request: OAuth2PasswordRequestForm = Depends(), db: Session = check_db) -> Token:
    return get_bearer_token(username=request.username, password=request.password, db=db)
