from sqlalchemy.orm import Session

from src.exchange.external_client_handlers.client_response_models.fetch_stocks_handler import FetchStocksHandler


def update_stock_list(db: Session):
    stock_handler = FetchStocksHandler()
    stock_handler.update_stocks_in_db(db)
