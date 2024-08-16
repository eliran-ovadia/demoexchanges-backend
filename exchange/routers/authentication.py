from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from exchange import schemas, database, models, token
from sqlalchemy.orm import Session
from exchange.hashing import Hash

router = APIRouter(tags = ['Authentication'])
check_db = Depends(database.get_db)

@router.post('/token')
def get_token(request: OAuth2PasswordRequestForm = Depends(), db: Session = check_db) -> schemas.Token:
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"Invalid credentials 1")
    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"Invalid credentials 2")
    

    access_token = token.create_access_token(data={"sub": user.id , "is_admin": user.is_admin, "name": user.name, "email": user.email})
    return schemas.Token(access_token=access_token, token_type="bearer")