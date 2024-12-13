from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.database.models import UsStocks
from src.exchange.external_client_handlers.client_requests import fetch_all_stocks


class FetchStocksHandler:
    def __init__(self):
        self.new_stock_data: list = fetch_all_stocks()

    # delete only the relevant stocks from the db
    # the goal was to prevent a lot of writes to the db
    def update_stocks_in_db(self, db: Session) -> None:
        existing_stock_records = {  # read all the existing stocks to a symbol:object dictionary
            stock.symbol: stock for stock in db.query(UsStocks).all()
        }
        processed_symbols, stocks_to_add, stocks_to_update = self.process_entries(existing_stock_records)

        stocks_to_delete = [
            existing_stock
            for symbol, existing_stock in existing_stock_records.items()
            if symbol not in processed_symbols  # A list of symbols that exist in the db bt not in fetched data
        ]
        self.attempt_to_commit(db, stocks_to_add, stocks_to_delete, stocks_to_update)

    def process_entries(self, existing_stock_records):
        stocks_to_add = []  # Will store all of new stocks that arrived
        stocks_to_update = []  # Will store stock that need to update
        processed_symbols = set()  # Will store all of
        for incoming_stock in self.new_stock_data:
            stock_symbol = incoming_stock.get('symbol')

            if not stock_symbol:  # Log abnormal behavior where a stock does not have a symbol and continue
                logger.critical(f"missing stock symbol {incoming_stock}")
                continue

            processed_symbols.add(stock_symbol)

            # Check if this stock needs an update to one of its fields
            if stock_symbol in existing_stock_records:  # Check if new symbol in db
                existing_stock = existing_stock_records[stock_symbol]  # Save the whole existing stock information
                if self.is_not_identical(existing_stock, incoming_stock):  # Check all same fields, if not: update them
                    self.update_stock(existing_stock, incoming_stock, stocks_to_update)  # Update stock with new data
            else:
                new_stock_record = self.create_new_record(incoming_stock)
                stocks_to_add.append(new_stock_record)
        return processed_symbols, stocks_to_add, stocks_to_update

    def attempt_to_commit(self, db, stocks_to_add, stocks_to_delete, stocks_to_update):
        try:
            db.add_all(stocks_to_add)
            db.bulk_save_objects(stocks_to_update)
            for stock_to_remove in stocks_to_delete:
                db.delete(stock_to_remove)

            db.commit()
        except Exception as error:
            db.rollback()
            logger.critical(f"An error occurred while updating {self.country} stocks in the database: {str(error)}")

    @staticmethod
    def create_new_record(incoming_stock):
        new_stock_record = UsStocks(
            symbol=incoming_stock.get('symbol', ''),
            name=incoming_stock.get('name', ''),
            currency=incoming_stock.get('currency', ''),
            exchange=incoming_stock.get('exchange', ''),
            mic_code=incoming_stock.get('mic_code', ''),
            country=incoming_stock.get('country', ''),
            type=incoming_stock.get('type', ''),
            figi_code=incoming_stock.get('figi_code', ''),
        )
        return new_stock_record

    @staticmethod
    def update_stock(existing_stock, incoming_stock, stocks_to_update):  # will almost never happen
        existing_stock.name = incoming_stock.get('name', '')
        existing_stock.currency = incoming_stock.get('currency', '')
        existing_stock.exchange = incoming_stock.get('exchange', '')
        existing_stock.mic_code = incoming_stock.get('mic_code', '')
        existing_stock.country = incoming_stock.get('country', '')
        existing_stock.type = incoming_stock.get('type', '')
        existing_stock.figi_code = incoming_stock.get('figi_code', '')
        stocks_to_update.append(existing_stock)

    @staticmethod
    def is_not_identical(existing_stock, incoming_stock) -> bool:
        return (existing_stock.name != incoming_stock.get('name') or
                existing_stock.currency != incoming_stock.get('currency') or
                existing_stock.exchange != incoming_stock.get('exchange') or
                existing_stock.mic_code != incoming_stock.get('mic_code') or
                existing_stock.country != incoming_stock.get('country') or
                existing_stock.type != incoming_stock.get('type') or
                existing_stock.figi_code != incoming_stock.get('figi_code'))
