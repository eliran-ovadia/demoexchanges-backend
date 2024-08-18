import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class MarketOpen(BaseModel):  # needs route to be developed
    is_market_open: bool | None = None


class ShowStock(BaseModel):
    symbol: str
    full_name: str
    amount: int
    exchange: str
    open: float
    previous_close: float
    avg_price: float
    last_price: float
    total_value: float
    bid: float
    ask: float
    year_range_low: float
    year_range_high: float
    total_return: float
    total_return_percent: float


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


class Order(BaseModel):
    symbol: str
    amount: int
    type: str

    @field_validator('type')
    def validate_type(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError("Type must be either 'buy' or 'sell'")
        return v.capitalize()

    @field_validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v


class Login(BaseModel):
    username: str
    password: str


class History(BaseModel):
    symbol: str
    price: float
    amount: int
    type: str
    value: float
    profit: float
    time_stamp: datetime


class AfterOrder(BaseModel):
    symbol: str
    price: float
    amount: int
    type: str
    value: float
    profit: float


#--------------------------Token--------------------------


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: str
    is_admin: bool
    email: str
    name: str
