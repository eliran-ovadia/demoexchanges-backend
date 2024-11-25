from fastapi import HTTPException, status

from src.exchange.app_logger import logger


class QuoteParser:
    def __init__(self, **kwargs):
        self.raw_data = kwargs

    def get(self, key, default=None):
        return self.raw_data.get(key, default)

    def to_parsed_quote(self) -> dict:
        try:
            fifty_two_week = self.get('fifty_two_week', {})

            parsed_quote = {
                "symbol": self.get("symbol", ""),
                "full_name": self.get("name"),
                "exchange": self.get("exchange"),
                "currency": self.get("currency"),
                "open": round(float(self.get("open", 0)), 2) if self.get("open") else None,
                "high": round(float(self.get("high", 0)), 2) if self.get("high") else None,
                "low": round(float(self.get("low", 0)), 2) if self.get("low") else None,
                "close": round(float(self.get("close", 0)), 2) if self.get("close") else None,
                "volume": int(self.get("volume", 0)) if self.get("volume") else None,
                "change": round(float(self.get("change", 0)), 2) if self.get("change") else None,
                "percent_change": round(float(self.get("percent_change", 0)), 2) if self.get(
                    "percent_change") else None,
                "avg_volume": int(self.get("average_volume", 0)) if self.get("average_volume") else None,
                "year_range_high": round(float(fifty_two_week.get("high", 0)), 2) if fifty_two_week.get(
                    "high") else None,
                "year_range_low": round(float(fifty_two_week.get("low", 0)), 2) if fifty_two_week.get("low") else None,
            }

            # Logging for Debug
            missing_keys = [key for key, value in parsed_quote.items() if value is None]
            if missing_keys:
                logger.warning(f"Missing keys in quote for {self.get('symbol', 'unknown')}: {missing_keys}")

            return parsed_quote

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing quote for {self.get('symbol', 'unknown')}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error parsing quote data for symbol {self.get('symbol', 'unknown')}"
            )

    def __repr__(self):
        return f"QuoteParser({self.raw_data})"
