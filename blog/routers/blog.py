from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Response
from .. import schemas, database, models
from sqlalchemy.orm import Session

router = APIRouter(tags = ['blogs'], prefix = "/blog")
check_db = Depends(database.get_db)


@router.get('/', response_model = List[schemas.ShowBlog])
def all(db: Session = check_db):
    blogs = db.query(models.Blog).all()
    return blogs

@router.get('/{id}', status_code = 200, response_model = schemas.ShowBlog)
def show(id, db: Session = check_db):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"blog with id of {id} is not in the database")
    return blog


@router.post('/', status_code=status.HTTP_201_CREATED)
def create(request: schemas.Blog, db: Session = check_db):
    new_blog = models.Blog(title = request.title, body = request.body, user_id = 1)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@router.put('/{id}', status_code = status.HTTP_202_ACCEPTED)
def update(id,request: schemas.Blog, db: Session = check_db):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"blog id number {id} not found")
    blog.update({models.Blog.title: request.title, models.Blog.body: request.body})
    db.commit()
    return db.query(models.Blog).filter(models.Blog.id == id).first()


@router.delete('/{id}',status_code = status.HTTP_204_NO_CONTENT)
def destroy(id, db: Session = check_db):
    blog = db.query(models.Blog).filter(models.Blog.id ==id)
    if not blog:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Blog with id {id} not found")
    blog.delete(synchronize_session=False)
    db.commit()
    return {'detail': f'deleted blog number {id}'}