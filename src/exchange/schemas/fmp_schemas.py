"""
Pydantic models for data flowing from Financial Modeling Prep through the system.

QuoteSchema      — internal normalized quote; produced by fetch_quote, consumed everywhere
All others       — shapes returned directly to API callers
"""
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Internal — produced by fetch_quote, consumed by portfolio and info layers
# ---------------------------------------------------------------------------
class QuoteSchema(BaseModel):
    symbol: str
    name: str
    exchange: str
    currency: str = "USD"
    price: float
    open: float
    high: float
    low: float
    previous_close: float
    change: float
    percent_change: float
    volume: int
    avg_volume: int
    year_high: float
    year_low: float


# ---------------------------------------------------------------------------
# API response shapes
# ---------------------------------------------------------------------------
class ParsedQuoteResponse(BaseModel):
    full_name: str
    exchange: str
    currency: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    percent_change: float
    avg_volume: int
    year_range_high: Optional[float] = None
    year_range_low: Optional[float] = None


class SearchResult(BaseModel):
    country: str
    currency: str
    exchange: str
    instrument_name: str
    symbol: str


class SearchResponse(BaseModel):
    total_results: int
    page: int
    page_size: int
    results: list[SearchResult]


class MarketStatusResponse(BaseModel):
    exchange: Optional[str] = None
    is_open: Optional[bool] = None
    # open_time = Optional[str] = None
    # close_time = Optional[str] = None


class SentimentEntry(BaseModel):
    symbol: Optional[str] = None
    period: Optional[str] = None
    strongBuy: int = 0
    buy: int = 0
    hold: int = 0
    sell: int = 0
    strongSell: int = 0


class MarketMoverEntry(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    percent_change: float


class MarketMoversResponse(BaseModel):
    stocks: list[MarketMoverEntry]
