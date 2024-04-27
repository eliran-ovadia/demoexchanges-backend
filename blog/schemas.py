#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------

from pydantic import BaseModel



class Blog(BaseModel):
    title: str
    body: str


class ShowBlog(BaseModel):
    title: str # return in the response only the title of the blog
    
    #class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version
    
    

class User(BaseModel):
    name: str
    email: str
    password: str
    
    
class ShowUser(BaseModel):
    name: str
    email: str