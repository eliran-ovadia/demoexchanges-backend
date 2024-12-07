from typing import Optional, Any

from fastapi import FastAPI

from src.exchange.external_client_handlers.client_requests import get_market_status


class MarketStatusModel:
    def __init__(self, exchange: Optional[str] = None, holiday: Optional[str] = None, isOpen: Optional[bool] = None,
                 session: Optional[str] = None, **kwargs) -> None:
        self.exchange = exchange
        self.holiday = holiday
        self.isOpen = isOpen
        self.session = session

    def get_market_status(self) -> dict[str, Any]:
        return {
            'exchange': self.exchange,
            'holiday': self.holiday,
            'isOpen': self.isOpen,
            'session': self.session
        }


def refresh_market_status(app: FastAPI) -> None:
    handler = MarketStatusModel(**get_market_status())
    app.state.market_status = handler.get_market_status()
