#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List


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
    portfolio: List[ShowPortfolio]

        
class Order(BaseModel): #buy/sell stocks for a user
    symbol: str
    amount: int
    


class Login(BaseModel):
    username: str
    password: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None