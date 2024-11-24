import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, constr, confloat, PositiveInt, Field, ValidationError


class Pagination(BaseModel):
    page: int = Field(1, ge=1, description="Page number (must be 1 or greater)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page (must be between 1 and 100)")


class Stock(BaseModel):
    symbol: str = Field(..., description="Stock symbol")

    @field_validator("symbol")
    def uppercase_symbol_and_length(cls, v):
        v = v.upper()  # Convert to uppercase
        if not (1 <= len(v) <= 5 and v.isalpha()):
            raise ValueError("Symbol must be between 1 and 5 alphabetic characters")
        return v


class ParsedRawQuote(BaseModel):
    symbol: constr(max_length=4)
    full_name: constr(max_length=50)
    exchange: constr(max_length=10)
    currency: constr(max_length=6)
    open: confloat(gt=0)
    high: confloat(gt=0)
    low: confloat(gt=0)
    close: confloat(gt=0)
    volume: int
    change: float
    percent_change: float
    avg_volume: int
    year_range_high: confloat(gt=0)
    year_range_low: confloat(gt=0)


class MarketOpen(BaseModel):  # Needs route to be developed
    is_market_open: bool | None = None


class ShowStock(BaseModel):
    symbol: constr(max_length=4)
    full_name: constr(max_length=50)
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


# --------------------------Token--------------------------

class Token(BaseModel):
    access_token: constr(min_length=1)
    token_type: constr(min_length=1)


class TokenData(BaseModel):
    id: constr(min_length=1)
    is_admin: bool
    email: EmailStr
    name: constr(min_length=1)
