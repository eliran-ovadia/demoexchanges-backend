#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List


class User(BaseModel):
    name: str
    email: str
    password: str
    
    
class Blog(BaseModel):
    title: str
    body: str
    
    
    
    
class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[Blog]
    


class ShowBlog(BaseModel):
    title: str # return in the response only the title of the blog
    body: str
    creator: ShowUser
    #class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version



class Login(BaseModel):
    username: str
    password: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None