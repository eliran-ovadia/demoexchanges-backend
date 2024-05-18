#--------------------------------schemas is reffering to the way the API interracts with the responses/requests------------------------------------
from pydantic import BaseModel, EmailStr, field_validator
from typing import List
from datetime import datetime
import re

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
    full_name: str | None = None
    amount: int
    exchange: str | None = None
    open: float | None = None
    previous_close: float | None = None
    avg_price: float | None = None
    last_price: float | None = None
    total_value: float | None = None
    bid: float | None = None
    ask: float | None = None
    year_range: str | None = None
    total_return: float | None = None
    total_return_percent: float | None = None
    
    # class Config(): #I dont need it for my version
    #    orm_mode = True #I dont need it for my version

class market_open(BaseModel):
    is_market_open: bool | None = None

    
class CreateUser(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    password: str
    
    @field_validator("password")
    def password_check(cls, v: str):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[\W_]', v):
            raise ValueError('Password must contain at least one special character')
        if re.search(r'(.)\1\1', v):
            raise ValueError('Password must not contain the same character three times in a row')
        return v.title()


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
    symbol: str | None = None
    price: float | None = None
    amount: int | None = None
    type: str | None = None
    value: float | None = None
    profit: float | None = None
    time_stamp: datetime | None = None
    
class Quotes(BaseModel):
    name: str

    
#--------------------------Token--------------------------
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str
    is_admin: bool
    email: str
    name: str