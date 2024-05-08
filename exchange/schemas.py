#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List
from datetime import datetime


class ShowPortfolioForPool(BaseModel): #get a stock object
    stock_id: int
    user_id: str
    symbol: str
    amount: int
    costPrice: float | None = None
    lastPrice: float | None = None
    totalValue: float | None = None
    profit: float | None = None


class ShowPortfolio(BaseModel): #get a stock object
    symbol: str
    amount: int
    costPrice: float | None = None
    lastPrice: float | None = None
    totalValue: float | None = None
    profit: float | None = None
    #class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version
    
class CreateUser(BaseModel):
    name: str
    email: str
    password: str


class User(BaseModel):
    id: str
    name: str
    email: str
    password: str
    is_admin: bool

class Order(BaseModel): #buy/sell stocks for a user
    symbol: str
    amount: int
    


class Login(BaseModel):
    username: str
    password: str
    
class History(BaseModel):
    order_id: int | None = None
    symbol: str | None = None
    price: float | None = None
    amount: int | None = None
    type: str | None = None
    value: float | None = None
    profit: float | None = None
    date: datetime | None = None
    user_id: str | None = None

    
#--------------------------Token--------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str
    is_admin: bool
    email: str
    name: str