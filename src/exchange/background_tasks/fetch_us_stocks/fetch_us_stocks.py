from sqlalchemy.orm import Session

from src.exchange.external_client_handlers.client_response_models.fetch_stocks_handler import FetchStocks


def update_stock_list(db: Session):
    stock_handler = FetchStocks()
    stock_handler.update_stocks_in_db(db)
