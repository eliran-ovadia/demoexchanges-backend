from fastapi import APIRouter, Depends , status
from .. import database, schemas
from sqlalchemy.orm import Session, backref
from .repository import user
from ..oauth2 import get_current_user


router = APIRouter(tags = ['users'], prefix = '/users')
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.post('/createUser', response_model = str, status_code = status.HTTP_201_CREATED)
def create_user(request: schemas.CreateUser, db: Session = check_db):
    return user.create_user(request, db)

@router.get('/getUser', response_model = schemas.User, status_code = status.HTTP_200_OK) # not really a nessecery endpoint
def get_user(db: Session = check_db, current_user: schemas.TokenData = check_auth):
    return user.get_user(db, current_user)


@router.patch('/resetPortfolio/', status_code = status.HTTP_202_ACCEPTED)
def resetPortfolio(db: Session = check_db, current_user: schemas.TokenData = check_auth):
    return user.resetPortfolio(db, current_user)

@router.delete('/deleteUser/', status_code = status.HTTP_202_ACCEPTED)
def delete_user(email: str, db: Session = check_db, current_user: schemas.TokenData = check_auth):
    return user.delete_user(email, db, current_user)