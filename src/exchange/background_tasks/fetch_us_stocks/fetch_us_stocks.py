from sqlalchemy.orm import Session

from src.exchange.external_client_handlers.client_requests import fetch_all_stocks
from src.exchange.external_client_handlers.client_response_models.fetch_stocks_handler import FetchStocksHandler


def update_stock_list(db: Session) -> None:
    stock_data = fetch_all_stocks()
    FetchStocksHandler(stock_data).update_stocks_in_db(db)
