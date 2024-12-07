from typing import Optional, Any

from cachetools import TTLCache
from fastapi import HTTPException, status

from src.exchange.app_logger import logger
from src.exchange.external_client_handlers.client_requests import get_quote

quote_cache = TTLCache(maxsize=1000, ttl=20)


class SingleQuoteModel:
    def __init__(self, symbol: Optional[str] = None, name: Optional[str] = None, exchange: Optional[str] = None,
                 currency: Optional[str] = None, open: Optional[str] = None, high: Optional[str] = None,
                 low: Optional[str] = None, close: Optional[float] = None, volume: Optional[str] = None,
                 change: Optional[str] = None, percent_change: Optional[str] = None,
                 average_volume: Optional[str] = None,
                 fifty_two_week: Optional[dict] = None, **kwargs):
        self.symbol = symbol
        self.name = name
        self.exchange = exchange
        self.currency = currency
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.change = change
        self.percent_change = percent_change
        self.average_volume = average_volume
        self.fifty_two_week = fifty_two_week
        self.fifty_two_week_high = fifty_two_week.get("high") if fifty_two_week else None
        self.fifty_two_week_low = fifty_two_week.get("low") if fifty_two_week else None

    def to_parsed_quote(self) -> dict:
        try:
            parsed_quote = {
                "symbol": self.symbol,
                "full_name": self.name,
                "exchange": self.exchange,
                "currency": self.currency,
                "open": round(float(self.open), 2) if self.open else None,
                "high": round(float(self.high), 2) if self.high else None,
                "low": round(float(self.low), 2) if self.low else None,
                "close": round(float(self.close), 2) if self.close else None,
                "volume": int(self.volume) if self.volume else None,
                "change": round(float(self.change), 2) if self.change else None,
                "percent_change": round(float(self.percent_change), 2) if self.percent_change else None,
                "avg_volume": int(self.average_volume) if self.average_volume else None,
                "year_range_high": round(float(self.fifty_two_week_high), 2)
                if self.fifty_two_week_high
                else None,
                "year_range_low": round(float(self.fifty_two_week_low), 2)
                if self.fifty_two_week_low
                else None,
            }

            # Log missing keys
            missing_keys = [key for key, value in parsed_quote.items() if value is None]
            if missing_keys:
                logger.warning(f"Missing keys in quote for {self.symbol}: {missing_keys}")

            return parsed_quote

        except (ValueError, TypeError) as e:
            logger.critical(f"Error parsing quote for {self.symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing quote data for symbol {self.symbol}",
            )


class QuoteResponseModel:

    def __init__(self, data=None):
        first_key = next(iter(data))
        if isinstance(data[first_key], str):  # Signle quote
            self.data = {data["symbol"]: SingleQuoteModel(**data)}
        else:  # Multiple quotes
            self.data = {}
            for key, value in data.items():
                self.data[key] = SingleQuoteModel(**value)

    def get_quote_for_symbol(self, symbol: str) -> Optional[dict]:
        if symbol in self.data:
            return self.data[symbol].to_parsed_quote()

    def to_parsed_quotes(self) -> dict[str, dict]:
        return {symbol: quote.to_parsed_quote() for symbol, quote in self.data.items()}


def get_cached_quotes(symbols: str) -> dict[str, Any]:
    symbols_list = set(symbols.upper().split(","))
    quotes_to_return = {}
    missed_symbols = []
    for symbol in symbols_list:  # Cache hit
        if symbol in quote_cache:
            quotes_to_return[symbol] = quote_cache[symbol]
        else:  # Cache miss
            missed_symbols.append(symbol)
    # Instead of calling every symbol to the client, we request all symbols in one call.
    all_missing_quotes = get_quote(",".join(missed_symbols))  # call client api for all missing quotes at once!
    missing_quotes_parser = QuoteResponseModel(all_missing_quotes)  # Init model class
    quotes_to_return.update(missing_quotes_parser.to_parsed_quotes())  # Parse all missed quotes with the model

    return quotes_to_return
