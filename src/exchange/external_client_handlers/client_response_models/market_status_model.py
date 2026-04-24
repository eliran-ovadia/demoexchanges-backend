from typing import Optional, Any


class MarketStatusModel:
    """
    Wraps the FMP /is-the-market-open response.
    FMP fields: isTheStockMarketOpen, stockExchangeName, stockMarketHolidays, ...
    """

    def __init__(self, isTheStockMarketOpen: Optional[bool] = None,
                 stockExchangeName: Optional[str] = None, **kwargs) -> None:
        self.isOpen = isTheStockMarketOpen
        self.exchange = stockExchangeName

    def market_status(self) -> dict[str, Any]:
        return {
            "exchange": self.exchange,
            "holiday": None,
            "isOpen": self.isOpen,
            "session": None,
        }
