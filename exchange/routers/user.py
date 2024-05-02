from fastapi import APIRouter, Depends
from .. import database, schemas
from sqlalchemy.orm import Session
from .repository import user



router = APIRouter(tags = ['users'], prefix = '/users')
check_db = Depends(database.get_db)


@router.post('/', response_model = schemas.User)
def create_user(request: schemas.User, db: Session = check_db):
    return user.create_user(request, db)

@router.get('/{email}', response_model = schemas.User)
def get_user(email: str, db: Session = check_db):
    return user.get_user(email, db)