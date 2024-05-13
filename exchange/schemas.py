#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel
from typing import List
from datetime import datetime


class ShowPortfolioForPool(BaseModel): #get a stock
    stock_id: int
    user_id: str
    symbol: str
    amount: int
    costPrice: float | None = None
    lastPrice: float | None = None
    totalValue: float | None = None
    profit: float | None = None


class ShowPortfolio(BaseModel): #get stocks
    symbol: str
    amount: int
    exchange: str | None = None
    open: float | None = None
    previous_close: float | None = None
    avg_price: float | None = None
    last_price: float | None = None
    total_value: float | None = None
    profit: float | None = None
    bid: float | None = None
    ask: float | None = None
    range_low: float | None = None
    range_high: float | None = None
    total_return: float | None = None
    next_report: datetime | None = None #deal with it later
    
    # class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version

class market_open(BaseModel):
    is_market_open: bool | None = None

    
class CreateUser(BaseModel):
    name: str
    email: str
    password: str


class User(BaseModel):
    id: str
    name: str
    email: str
    password: str
    cash: float
    is_admin: bool
    portfolio: List[ShowPortfolioForPool]

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