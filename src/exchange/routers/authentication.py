from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.exchange.Auth import token
from src.exchange.database.db_conn import get_db
from src.exchange.database.models import User
from src.exchange.hashing import Hash
from src.exchange.schemas import Token

router = APIRouter(tags=['Authentication'])
check_db = Depends(get_db)


@router.post('/token')
def get_token(request: OAuth2PasswordRequestForm = Depends(), db: Session = check_db) -> Token:
    user = db.query(User).filter(User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credentials 1")
    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credentials 2")

    access_token = token.create_access_token(data={
        "sub": user.id,
        "is_admin": user.is_admin,
        "name": user.name,
        "email": user.email})

    return Token(access_token=access_token, token_type="bearer")
