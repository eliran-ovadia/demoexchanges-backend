from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.database.models import UsStocks

_CHUNK_SIZE = 500


class FetchStocksHandler:
    """
    Syncs the us_stocks table with fresh data from FMP using PostgreSQL upsert.
    Avoids loading the entire table into memory.
    """

    def __init__(self, stock_data: list):
        self.stock_data = stock_data

    def update_stocks_in_db(self, db: Session) -> None:
        if not self.stock_data:
            return

        valid = [s for s in self.stock_data if s.get("symbol")]
        incoming_symbols = [s["symbol"] for s in valid]

        try:
            self._upsert_chunks(db, valid)
            self._delete_removed(db, incoming_symbols)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.critical(f"Failed to sync us_stocks: {e}")

    def _upsert_chunks(self, db: Session, stocks: list) -> None:
        for i in range(0, len(stocks), _CHUNK_SIZE):
            chunk = stocks[i: i + _CHUNK_SIZE]
            stmt = insert(UsStocks).values([
                {
                    "symbol": s["symbol"],
                    "name": s.get("name", ""),
                    "currency": s.get("currency", ""),
                    "exchange": s.get("exchange", ""),
                    "mic_code": s.get("mic_code", ""),
                    "country": s.get("country", ""),
                    "type": s.get("type", ""),
                    "figi_code": s.get("figi_code", ""),
                }
                for s in chunk
            ])
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "name": stmt.excluded.name,
                    "exchange": stmt.excluded.exchange,
                    "type": stmt.excluded.type,
                },
            )
            db.execute(stmt)

    @staticmethod
    def _delete_removed(db: Session, incoming_symbols: list[str]) -> None:
        db.query(UsStocks).filter(
            UsStocks.symbol.notin_(incoming_symbols)
        ).delete(synchronize_session=False)
