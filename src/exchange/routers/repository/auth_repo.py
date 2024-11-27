from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.exchange.Auth import token
from src.exchange.Auth.hashing import Hash
from src.exchange.database.models import User
from src.exchange.schemas import Token


def get_bearer_token(*, username: str,
                     password: str,
                     db: Session) -> Token:
    user = db.query(User).filter(User.email == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credentials")
    if not Hash.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid credentials")

    access_token = token.create_access_token(data={
        "sub": user.id,
        "is_admin": user.is_admin,
        "name": user.name,
        "email": user.email})

    return Token(access_token=access_token, token_type="bearer")
