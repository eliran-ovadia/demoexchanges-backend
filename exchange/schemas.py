import re
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, constr, confloat, PositiveInt



class MarketOpen(BaseModel):  # needs route to be developed
    is_market_open: bool | None = None


class ShowStock(BaseModel):
    symbol: constr(max_length=10)
    full_name: constr(max_length=100)
    amount: int
    exchange: constr(max_length=10)
    open: confloat(gt=0)
    previous_close: confloat(gt=0)
    avg_price: confloat(gt=0)
    last_price: confloat(gt=0)
    total_value: confloat(gt=0)
    bid: confloat(gt=0)
    ask: confloat(gt=0)
    year_range_low: confloat(gt=0)
    year_range_high: confloat(gt=0)
    total_return: float
    total_return_percent: float


class CreateUser(BaseModel):
    name: str
    last_name: str
    email: EmailStr
    password: constr(min_length=8)

    @field_validator("password")
    def password_check(cls, v: str):
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
        return v


class User(BaseModel):
    id: constr(min_length=1)
    name: constr(min_length=1)
    email: EmailStr
    password: str
    cash: confloat(ge=0)
    is_admin: bool



class Order(BaseModel):
    symbol: str
    amount: PositiveInt
    type: str

    @field_validator('type')
    def validate_type(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError("Type must be either 'buy' or 'sell'")
        return v.capitalize()

    @field_validator('amount')
    def validate_amount(cls, v):
        if v > 10_000:
            raise ValueError("Cannot buy more than 10,000 stocks a once")
        return v

class Login(BaseModel):
    username: EmailStr
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
    access_token: constr(min_length=1)
    token_type: constr(min_length=1)

class TokenData(BaseModel):
    id: constr(min_length=1)
    is_admin: bool
    email: EmailStr
    name: constr(min_length=1)
