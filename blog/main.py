from typing import List
from fastapi import FastAPI, Depends, status , HTTPException, Response
from pydantic  import BaseModel
from . import schemas, models, hashing
from .database import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI()

models.Base.metadata.create_all(engine) #evey time we find a new base we create the table for it

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post('/blog', status_code=status.HTTP_201_CREATED, tags = ['blogs'])
def create(request: schemas.Blog, db: Session = Depends(get_db)):
    new_blog = models.Blog(title = request.title, body = request.body)
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    return new_blog

@app.delete('/blog/{id}',status_code = status.HTTP_204_NO_CONTENT, tags = ['blogs'])
def destroy(id, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id ==id)
    if not blog:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Blog with id {id} not found")
    blog.delete(synchronize_session=False)
    db.commit()
    return {'detail': f'deleted blog number {id}'}


@app.put('/blog/{id}', status_code = status.HTTP_202_ACCEPTED, tags = ['blogs'])
def update(id,request: schemas.Blog, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id)
    if not blog:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"blog id number {id} not found")
    blog.update({models.Blog.title: request.title, models.Blog.body: request.body})
    db.commit()
    return db.query(models.Blog).filter(models.Blog.id == id).first()
    


@app.get('/blog', response_model = List[schemas.ShowBlog], tags = ['blogs'])
def all(db: Session = Depends(get_db)):
    blogs = db.query(models.Blog).all()
    return blogs

@app.get('/blog/{id}', status_code = 200, response_model = schemas.ShowBlog, tags = ['blogs'])
def show(id,response: Response, db: Session = Depends(get_db)):
    blog = db.query(models.Blog).filter(models.Blog.id == id).first()
    if not blog:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"blog with id of {id} is not in the database")
    return blog
    
    

@app.post('/user', response_model = schemas.ShowUser, tags = ['users'])
def create_user(request: schemas.User, db: Session = Depends(get_db)):
    new_user = models.User(name = request.name, email = request.email, password = hashing.Hash.bcrypt(request.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user) #refreshing the new_user to be able to return the newly created user
    return new_user

@app.get('/user/{id}', response_model = schemas.ShowUser, tags = ['users'])
def get_user(id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = f"User with id of {id} is not in the database")
    return user