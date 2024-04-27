from fastapi import APIRouter, Depends, status, HTTPException
from .. import database, schemas, routers, models
from sqlalchemy.orm import Session
from ..hashing import Hash



router = APIRouter()
check_db = Depends(database.get_db)


@router.post('/user', response_model = schemas.ShowUser, tags = ['users'])
def create_user(request: schemas.User, db: Session = check_db):
    new_user = models.User(name = request.name, email = request.email, password = Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refreshing the new_user to be able to return the newly created user
    return new_user

@router.get('/user/{id}', response_model = schemas.ShowUser, tags = ['users'])
def get_user(id: int, db: Session = check_db):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with id of {id} is not in the database")
    return user