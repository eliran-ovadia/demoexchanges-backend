from fastapi import HTTPException, status

from src.exchange.app_logger import logger


class QuoteParser:
    def __init__(self, symbol=None, name=None, exchange=None, currency=None, open=None, high=None, low=None, close=None,
                 volume=None, change=None, percent_change=None, average_volume=None, fifty_two_week=None, **kwargs):
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
        self.fifty_two_week_high = fifty_two_week.get('high', None)
        self.fifty_two_week_low = fifty_two_week.get('low', None)


    def to_parsed_quote(self) -> dict:
        try:
            parsed_quote = {
                "symbol": self.symbol,
                "full_name": self.name,
                "exchange": self.exchange,
                "currency": self.currency,
                "open": round(float(self.open), 2),
                "high": round(float(self.high), 2),
                "low": round(float(self.low), 2),
                "close": round(float(self.close), 2),
                "volume": int(self.volume),
                "change": round(float(self.change), 2),
                "percent_change": round(float(self.percent_change), 2),
                "avg_volume": int(self.average_volume),
                "year_range_high": round(float(self.fifty_two_week.get("high", 0)), 2) if self.fifty_two_week.get(
                    "high") else None,
                "year_range_low": round(float(self.fifty_two_week.get("low", 0)), 2) if self.fifty_two_week.get("low") else None,
            }

            # Logging for Debug - log missing keys
            missing_keys = [key for key, value in parsed_quote.items() if value is None]
            if missing_keys:
                logger.critical(f"Missing keys in quote for {self.symbol}: {missing_keys} - from QuoteParser")

            return parsed_quote

        except (ValueError, TypeError) as e:
            logger.critical(f"Error parsing quote for {self.symbol}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing quote data for symbol {self.symbol}"
            )
