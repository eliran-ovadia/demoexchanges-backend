from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.database.models import UsStocks


class FetchStocksHandler:
    """
    Syncs the us_stocks table with fresh data from FMP.
    Stock data is passed in explicitly — no HTTP calls in the constructor.
    """

    def __init__(self, stock_data: list):
        self.stock_data = stock_data

    def update_stocks_in_db(self, db: Session) -> None:
        existing = {stock.symbol: stock for stock in db.query(UsStocks).all()}
        processed, to_add, to_update = self._process_entries(existing)
        to_delete = [s for sym, s in existing.items() if sym not in processed]
        self._commit(db, to_add, to_update, to_delete)

    def _process_entries(self, existing: dict) -> tuple[set, list, list]:
        processed = set()
        to_add, to_update = [], []

        for stock in self.stock_data:
            symbol = stock.get("symbol")
            if not symbol:
                logger.critical(f"Incoming stock record missing symbol: {stock}")
                continue

            processed.add(symbol)

            if symbol in existing:
                if self._has_changed(existing[symbol], stock):
                    self._apply_update(existing[symbol], stock)
                    to_update.append(existing[symbol])
            else:
                to_add.append(self._new_record(stock))

        return processed, to_add, to_update

    @staticmethod
    def _commit(db: Session, to_add: list, to_update: list, to_delete: list) -> None:
        try:
            db.add_all(to_add)
            db.bulk_save_objects(to_update)
            for record in to_delete:
                db.delete(record)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.critical(f"Failed to sync us_stocks: {e}")

    @staticmethod
    def _new_record(stock: dict) -> UsStocks:
        return UsStocks(
            symbol=stock.get("symbol", ""),
            name=stock.get("name", ""),
            currency=stock.get("currency", ""),
            exchange=stock.get("exchange", ""),
            mic_code=stock.get("mic_code", ""),
            country=stock.get("country", ""),
            type=stock.get("type", ""),
            figi_code=stock.get("figi_code", ""),
        )

    @staticmethod
    def _apply_update(record: UsStocks, stock: dict) -> None:
        record.name = stock.get("name", "")
        record.exchange = stock.get("exchange", "")
        record.type = stock.get("type", "")

    @staticmethod
    def _has_changed(record: UsStocks, stock: dict) -> bool:
        # Only check fields FMP actually provides; currency/mic_code/figi_code are always ""
        return (
            record.name != stock.get("name")
            or record.exchange != stock.get("exchange")
            or record.type != stock.get("type")
        )
