from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def update_stocks_in_db(self, db: AsyncSession) -> None:
        if not self.stock_data:
            return

        valid = [s for s in self.stock_data if s.get("symbol")]
        incoming_symbols = [s["symbol"] for s in valid]

        try:
            await self._upsert_chunks(db, valid)
            await self._delete_removed(db, incoming_symbols)
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.critical(f"Failed to sync us_stocks: {e}")

    async def _upsert_chunks(self, db: AsyncSession, stocks: list) -> None:
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
            await db.execute(stmt)

    @staticmethod
    async def _delete_removed(db: AsyncSession, incoming_symbols: list[str]) -> None:
        from sqlalchemy import delete
        await db.execute(
            delete(UsStocks).where(UsStocks.symbol.notin_(incoming_symbols))
        )
