#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List


class ShowPortfolio(BaseModel): #get a stock object
    symbol: str
    amount: int
    costPrice: float
    lastPrice: float
    totalValue: float
    profit: float
    #class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version
    
    
class User(BaseModel):
    id: str
    name: str
    email: str
    password: str
    portfolio: List[ShowPortfolio]

        
class Portfolio(BaseModel): #buy/sell stocks for a user
    symbol: str
    amount: int
    
    
class GetPortfolio(BaseModel): #get a users portfolio
    stoks: List[ShowPortfolio]
    

class Login(BaseModel):
    username: str
    password: str
    
    
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None