#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List


class User(BaseModel):
    name: str
    email: str
    password: str
    
    
class Portfolio(BaseModel):
    symbol: str
    amount: int
    
    
class ShowPortfolio(BaseModel):
    symbol: str
    amount: int
    costPrice: float
    lastPrice: float
    totalValue: float
    profit: float
    user_id: int
    #class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version
    
    
class ShowUser(BaseModel):
    name: str
    email: str
    blogs: List[ShowPortfolio]
    

class Login(BaseModel):
    username: str
    password: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None