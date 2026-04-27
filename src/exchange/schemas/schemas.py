import re
from datetime import datetime
from typing import Annotated, ClassVar, Optional

from pydantic import BaseModel, EmailStr, field_validator, Field, model_validator, PositiveInt


# ---------------------------------------------------------------------------
# Reusable constrained types
# ---------------------------------------------------------------------------
SymbolStr = Annotated[str, Field(max_length=5)]
NameStr = Annotated[str, Field(max_length=50)]
ExchangeStr = Annotated[str, Field(max_length=10)]
CurrencyStr = Annotated[str, Field(max_length=6)]
PositiveFloat = Annotated[float, Field(gt=0)]
NonNegativeFloat = Annotated[float, Field(ge=0)]


# ---------------------------------------------------------------------------
# Shared
# ---------------------------------------------------------------------------
class Pagination(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=100)


class Stock(BaseModel):
    symbol: str = Field(..., description="Stock symbol (1–5 alphabetic characters)")

    @field_validator("symbol")
    def uppercase_and_validate(cls, v: str) -> str:
        v = v.upper()
        if not (1 <= len(v) <= 5 and v.isalpha()):
            raise ValueError("Symbol must be 1–5 alphabetic characters")
        return v


# ---------------------------------------------------------------------------
# Market data responses
# ---------------------------------------------------------------------------
class ParsedRawQuote(BaseModel):
    symbol: SymbolStr
    full_name: NameStr
    exchange: ExchangeStr
    currency: CurrencyStr
    open: PositiveFloat
    high: PositiveFloat
    low: PositiveFloat
    close: PositiveFloat
    volume: int
    change: float
    percent_change: float
    avg_volume: int
    year_range_high: Optional[PositiveFloat] = None
    year_range_low: Optional[PositiveFloat] = None


class MarketOpen(BaseModel):
    is_market_open: Optional[bool] = None


class ShowStock(BaseModel):
    symbol: SymbolStr
    full_name: NameStr
    amount: int
    exchange: ExchangeStr
    open: NonNegativeFloat
    previous_close: NonNegativeFloat
    avg_price: PositiveFloat
    last_price: PositiveFloat
    total_value: NonNegativeFloat
    bid: NonNegativeFloat
    ask: NonNegativeFloat
    year_range_low: Optional[PositiveFloat] = None
    year_range_high: Optional[PositiveFloat] = None
    total_return: float
    total_return_percent: float


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------
class CreateUser(BaseModel):
    NAME_REGEX: ClassVar[str] = r"^[A-Za-zÀ-ÿ ,.'-]+$"
    COMMON_PASSWORDS: ClassVar[set[str]] = {"password", "12345678", "qwerty", "abc123", "letmein"}

    name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: EmailStr
    password: str = Field(..., description="Password (must meet security requirements)")
    password_confirm: str

    @field_validator("name", "last_name")
    def validate_name(cls, v: str, info) -> str:
        if not (1 <= len(v.strip()) <= 50):
            raise ValueError(f"{info.field_name} must be between 1 and 50 characters")
        if not re.match(cls.NAME_REGEX, v):
            raise ValueError(f"{info.field_name} contains invalid characters")
        return v.strip()

    @field_validator("password", "password_confirm")
    def validate_password_length(cls, v: str, info) -> str:
        if not (8 <= len(v.strip()) <= 128):
            raise ValueError(f"{info.field_name} must be 8–128 characters")
        return v.strip()

    @field_validator("password")
    def validate_password_strength(cls, v: str) -> str:
        return cls._check_strength(v)

    @model_validator(mode="before")
    @classmethod
    def passwords_match(cls, values: dict) -> dict:
        if values.get("password_confirm") != values.get("password"):
            raise ValueError("password_confirm must match password")
        return values

    @model_validator(mode="before")
    @classmethod
    def no_personal_info_in_password(cls, values: dict) -> dict:
        password = values.get("password", "").lower()
        if values.get("name", "").lower() in password:
            raise ValueError("Password must not contain your first name")
        if values.get("last_name", "").lower() in password:
            raise ValueError("Password must not contain your last name")
        email_local = values.get("email", "").lower().split("@")[0]
        if email_local and email_local in password:
            raise ValueError("Password must not contain parts of your email")
        return values

    def dict(self, **kwargs):
        return super().model_dump(exclude={"password"}, **kwargs)

    def json(self, **kwargs):
        return super().model_dump(exclude={"password"}, **kwargs)

    model_config = {"extra": "forbid"}

    @staticmethod
    def _check_strength(password: str) -> str:
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[\W_]", password):
            raise ValueError("Password must contain at least one special character")
        if re.search(r"(.)\1\1", password):
            raise ValueError("Password must not repeat the same character three times in a row")
        if password.lower() in CreateUser.COMMON_PASSWORDS:
            raise ValueError("Password is too common")
        return password


class User(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    email: EmailStr
    password: str
    cash: NonNegativeFloat
    is_admin: bool


# ---------------------------------------------------------------------------
# Trading
# ---------------------------------------------------------------------------
class Order(BaseModel):
    symbol: str
    amount: PositiveInt
    type: str

    @field_validator("type")
    def validate_type(cls, v: str) -> str:
        if v.lower() not in ("buy", "sell"):
            raise ValueError("type must be 'buy' or 'sell'")
        return v.capitalize()


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


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------
class MessageResponse(BaseModel):
    message: str


class PortfolioBalance(BaseModel):
    buying_power: float
    portfolio_value: float
    total_return: float
    total_return_percent: float
    account_value: float
    total_stocks: int


class PortfolioResponse(BaseModel):
    balance: PortfolioBalance
    portfolio: list["ShowStock"]


class HistoryResponse(BaseModel):
    total_items: int
    page: int
    page_size: int
    history: list["History"]


class WatchlistResponse(BaseModel):
    total_items: int
    page: int
    page_size: int
    watchlist: list[str]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class Login(BaseModel):
    username: EmailStr
    password: str


class Token(BaseModel):
    access_token: Annotated[str, Field(min_length=1)]
    refresh_token: Annotated[str, Field(min_length=1)]
    token_type: Annotated[str, Field(min_length=1)]


class RefreshRequest(BaseModel):
    refresh_token: Annotated[str, Field(min_length=1)]


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    id: Annotated[str, Field(min_length=1)]
    is_admin: bool
    email: EmailStr
    name: Annotated[str, Field(min_length=1)]
