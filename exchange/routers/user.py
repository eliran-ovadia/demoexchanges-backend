from fastapi import APIRouter, Depends , status
from .. import database, schemas, models
from sqlalchemy.orm import Session
from .repository import user
from ..oauth2 import get_current_user


router = APIRouter(tags = ['users'], prefix = '/users')
check_db = Depends(database.get_db)
check_auth = Depends(get_current_user)

@router.post('/', response_model = schemas.User, status_code = status.HTTP_201_CREATED)
def create_user(request: schemas.CreateUser, db: Session = check_db, current_user: schemas.User = check_auth):
    return user.create_user(request, db)

@router.get('/{email}', response_model = schemas.User, status_code = status.HTTP_200_OK)
def get_user(email: str, db: Session = check_db, current_user: schemas.User = check_auth):
    return user.get_user(email, db)

@router.delete('/delete/{email}', status_code = status.HTTP_202_ACCEPTED)
def delete_user(email: str, db: Session = check_db, current_user: schemas.User = check_auth):
    return user.delete_user(email, db)