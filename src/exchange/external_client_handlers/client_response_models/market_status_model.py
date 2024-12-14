from typing import Optional, Any


class MarketStatusModel:
    def __init__(self, exchange: Optional[str] = None, holiday: Optional[str] = None, isOpen: Optional[bool] = None,
                 session: Optional[str] = None, **kwargs) -> None:
        self.exchange = exchange
        self.holiday = holiday
        self.isOpen = isOpen
        self.session = session

    def market_status(self) -> dict[str, Any]:
        return {
            'exchange': self.exchange,
            'holiday': self.holiday,
            'isOpen': self.isOpen,
            'session': self.session
        }
