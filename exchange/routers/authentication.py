from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .. import schemas, database, models, token
from sqlalchemy.orm import Session
from ..hashing import Hash


router = APIRouter(tags = ['Authentication'])
check_db = Depends(database.get_db)

@router.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = check_db):
    #---------finding_the_user_in_the_database------------------
    user = db.query(models.User).filter(models.User.email == request.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"Invalid credentials 1")
    if not Hash.verify(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"Invalid credentials 2")
    
    #---------creating_access_token----------------------------
    access_token = token.create_access_token(data={"sub": user.email})
    return schemas.Token(access_token=access_token, token_type="bearer")