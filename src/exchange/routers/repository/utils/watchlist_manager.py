from fastapi import HTTPException, status
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exchange.database.models import WatchlistItem


class WatchlistManager:

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def _symbol_exists(self, symbol: str) -> bool:
        from src.exchange.external_client_handlers.client_requests import fetch_stock_price
        try:
            price = await fetch_stock_price(symbol)
            return price > 0
        except HTTPException:
            return False

    async def add_to_watchlist(self, symbol: str) -> dict:
        if not await self._symbol_exists(symbol):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Symbol '{symbol}' not found")
        self.db.add(WatchlistItem(symbol=symbol, user_id=self.user_id))
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"'{symbol}' is already in your watchlist")
        return {"message": "Stock added successfully to your watchlist"}

    async def delete_from_watchlist(self, symbol: str) -> dict:
        result = await self.db.execute(
            delete(WatchlistItem).where(
                WatchlistItem.symbol == symbol,
                WatchlistItem.user_id == self.user_id,
            )
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"'{symbol}' is not in your watchlist")
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"An error occurred while removing '{symbol}'")
        return {"message": "Stock deleted successfully from your watchlist"}

    async def get_watchlist(self, page: int, page_size: int) -> dict:
        total_items = (await self.db.execute(
            select(func.count(WatchlistItem.id)).where(WatchlistItem.user_id == self.user_id)
        )).scalar()

        watchlist = (await self.db.execute(
            select(WatchlistItem)
            .where(WatchlistItem.user_id == self.user_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )).scalars().all()

        return {
            "total_items": total_items,
            "page": page,
            "page_size": page_size,
            "watchlist": [item.symbol for item in watchlist],
        }
