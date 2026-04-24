from typing import Optional, Any

from fastapi import HTTPException, status

from src.exchange.app_logger import logger


class SingleQuoteModel:
    """Wraps one normalized internal quote dict and formats it for the /ParsedQuote response."""

    def __init__(self, symbol: Optional[str] = None, name: Optional[str] = None,
                 exchange: Optional[str] = None, currency: Optional[str] = None,
                 price: Optional[float] = None, open: Optional[float] = None,
                 high: Optional[float] = None, low: Optional[float] = None,
                 previous_close: Optional[float] = None, change: Optional[float] = None,
                 percent_change: Optional[float] = None, volume: Optional[int] = None,
                 avg_volume: Optional[int] = None, year_high: Optional[float] = None,
                 year_low: Optional[float] = None, **kwargs):
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.currency = currency
        self.price = price
        self.open = open
        self.high = high
        self.low = low
        self.previous_close = previous_close
        self.change = change
        self.percent_change = percent_change
        self.volume = volume
        self.avg_volume = avg_volume
        self.year_high = year_high
        self.year_low = year_low

    def to_parsed_quote(self) -> dict:
        try:
            parsed = {
                "full_name": self.name,
                "exchange": self.exchange,
                "currency": self.currency,
                "open": round(float(self.open), 2) if self.open else None,
                "high": round(float(self.high), 2) if self.high else None,
                "low": round(float(self.low), 2) if self.low else None,
                "close": round(float(self.price), 2) if self.price else None,
                "volume": int(self.volume) if self.volume else None,
                "change": round(float(self.change), 2) if self.change is not None else None,
                "percent_change": round(float(self.percent_change), 2) if self.percent_change is not None else None,
                "avg_volume": int(self.avg_volume) if self.avg_volume else None,
                "year_range_high": round(float(self.year_high), 2) if self.year_high else None,
                "year_range_low": round(float(self.year_low), 2) if self.year_low else None,
            }

            missing_keys = [k for k, v in parsed.items() if v is None]
            if missing_keys:
                logger.warning(f"Missing keys in quote for {self.symbol}: {missing_keys}")

            return parsed

        except (ValueError, TypeError) as e:
            logger.critical(f"Error parsing quote for {self.symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing quote data for symbol {self.symbol}",
            )


class QuoteResponseModel:
    """
    Accepts the output of fetch_quote() — either a single normalized dict
    or a {symbol: normalized_dict} mapping — and produces the /ParsedQuote response.
    """

    def __init__(self, data: dict = None):
        if next(iter(data)) != "symbol":  # Multiple quotes: first key is a ticker
            self.data = {
                key.upper(): SingleQuoteModel(**value).to_parsed_quote()
                for key, value in data.items()
            }
        else:  # Single quote: first key is the literal string "symbol"
            self.data = {data["symbol"]: SingleQuoteModel(**data).to_parsed_quote()}

    def to_parsed_quotes(self) -> dict[str, Any]:
        return self.data
