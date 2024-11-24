import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator, constr, confloat, PositiveInt, Field


class Pagination(BaseModel):
    page: int = Field(1, ge=1, description="Page number (must be 1 or greater)")
    page_size: int = Field(10, ge=1, le=100, description="Number of items per page (must be between 1 and 100)")


class Stock(BaseModel):
    symbol: str = Field(..., description="Stock symbol (1 to 5 alphabetic characters)")

    @field_validator("symbol")
    def uppercase_symbol_and_length(cls, v):
        v = v.upper()  # Convert to uppercase
        if not (1 <= len(v) <= 5 and v.isalpha()):
            raise ValueError("Symbol must be between 1 and 5 alphabetic characters")
        return v


class ParsedRawQuote(BaseModel):
    symbol: constr(max_length=5) = Field(..., description="Stock symbol (max length: 5 characters)")
    full_name: constr(max_length=50) = Field(..., description="Full name of the stock (max length: 50 characters)")
    exchange: constr(max_length=10) = Field(..., description="Stock exchange name (max length: 10 characters)")
    currency: constr(max_length=6) = Field(..., description="Currency code (max length: 6 characters)")
    open: confloat(gt=0) = Field(..., description="Opening price of the stock")
    high: confloat(gt=0) = Field(..., description="Highest price of the stock during the period")
    low: confloat(gt=0) = Field(..., description="Lowest price of the stock during the period")
    close: confloat(gt=0) = Field(..., description="Closing price of the stock")
    volume: int = Field(..., description="Number of shares traded during the period")
    change: float = Field(..., description="Change in stock price")
    percent_change: float = Field(..., description="Percentage change in stock price")
    avg_volume: int = Field(..., description="Average volume of shares traded")
    year_range_high: confloat(gt=0) = Field(..., description="52-week high price of the stock")
    year_range_low: confloat(gt=0) = Field(..., description="52-week low price of the stock")


class MarketOpen(BaseModel):  # Needs route to be developed
    is_market_open: bool | None = Field(None, description="Indicates whether the market is currently open")


class ShowStock(BaseModel):
    symbol: constr(max_length=5) = Field(..., description="Stock symbol (max length: 5 characters)")
    full_name: constr(max_length=50) = Field(..., description="Full name of the stock (max length: 50 characters)")
    amount: int = Field(..., description="Amount of stocks owned")
    exchange: constr(max_length=10) = Field(..., description="Stock exchange name (max length: 10 characters)")
    open: confloat(gt=0) = Field(..., description="Opening price of the stock")
    previous_close: confloat(gt=0) = Field(..., description="Previous closing price of the stock")
    avg_price: confloat(gt=0) = Field(..., description="Average purchase price of the stock")
    last_price: confloat(gt=0) = Field(..., description="Last traded price of the stock")
    total_value: confloat(gt=0) = Field(..., description="Total value of the stock owned")
    bid: confloat(gt=0) = Field(..., description="Current bid price of the stock")
    ask: confloat(gt=0) = Field(..., description="Current ask price of the stock")
    year_range_low: confloat(gt=0) = Field(..., description="52-week low price of the stock")
    year_range_high: confloat(gt=0) = Field(..., description="52-week high price of the stock")
    total_return: float = Field(..., description="Total profit/loss from the stock in absolute terms")
    total_return_percent: float = Field(..., description="Total profit/loss from the stock in percentage terms")


class CreateUser(BaseModel):
    name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    password: constr(min_length=8) = Field(..., description="Password (must meet security requirements)")

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
    id: constr(min_length=1) = Field(..., description="Unique identifier of the user")
    name: constr(min_length=1) = Field(..., description="User's full name")
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="Hashed password of the user")
    cash: confloat(ge=0) = Field(..., description="Available cash balance for the user")
    is_admin: bool = Field(..., description="Indicates if the user has administrative privileges")


class Order(BaseModel):
    symbol: str = Field(..., description="Stock symbol to trade")
    amount: PositiveInt = Field(..., description="Number of stocks to trade (must be positive)")
    type: str = Field(..., description="Type of order ('buy' or 'sell')")

    @field_validator('type')
    def validate_type(cls, v):
        if v.lower() not in ['buy', 'sell']:
            raise ValueError("Type must be either 'buy' or 'sell'")
        return v.capitalize()


class Login(BaseModel):
    username: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class History(BaseModel):
    symbol: str = Field(..., description="Stock symbol involved in the transaction")
    price: float = Field(..., description="Price per stock at the time of transaction")
    amount: int = Field(..., description="Number of stocks involved in the transaction")
    type: str = Field(..., description="Type of transaction ('buy' or 'sell')")
    value: float = Field(..., description="Total value of the transaction")
    profit: float = Field(..., description="Profit/loss from the transaction")
    time_stamp: datetime = Field(..., description="Timestamp of the transaction")


class AfterOrder(BaseModel):
    symbol: str = Field(..., description="Stock symbol involved in the order")
    price: float = Field(..., description="Price per stock after the order")
    amount: int = Field(..., description="Number of stocks involved in the order")
    type: str = Field(..., description="Type of order ('buy' or 'sell')")
    value: float = Field(..., description="Total value of the order")
    profit: float = Field(..., description="Profit/loss from the order")


# --------------------------Token--------------------------

class Token(BaseModel):
    access_token: constr(min_length=1)
    token_type: constr(min_length=1)


class TokenData(BaseModel):
    id: constr(min_length=1)
    is_admin: bool
    email: EmailStr
    name: constr(min_length=1)
