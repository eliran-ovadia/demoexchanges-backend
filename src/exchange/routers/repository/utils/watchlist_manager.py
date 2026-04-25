from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.exchange.database.models import WatchlistItem


class WatchlistManager:

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def _symbol_exists(self, symbol: str) -> bool:
        """Validate the symbol against FMP — avoids depending on the us_stocks cache."""
        from src.exchange.external_client_handlers.client_requests import fetch_stock_price
        try:
            price = fetch_stock_price(symbol)
            return price > 0
        except HTTPException:
            return False

    def add_to_watchlist(self, symbol: str) -> dict:
        if not self._symbol_exists(symbol):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Symbol '{symbol}' not found")
        new_entry = WatchlistItem(symbol=symbol, user_id=self.user_id)
        self.db.add(new_entry)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"'{symbol}' is already in your watchlist")
        return {"message": "Stock added successfully to your watchlist"}

    def delete_from_watchlist(self, symbol: str) -> dict:
        deleted = (
            self.db.query(WatchlistItem)
            .filter(WatchlistItem.symbol == symbol, WatchlistItem.user_id == self.user_id)
            .delete(synchronize_session=False)
        )
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"'{symbol}' is not in your watchlist")
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"An error occurred while removing '{symbol}'")
        return {"message": "Stock deleted successfully from your watchlist"}

    def get_watchlist(self, page: int, page_size: int) -> dict:
        total_items = (
            self.db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == self.user_id)
            .count()
        )
        watchlist = (
            self.db.query(WatchlistItem)
            .filter(WatchlistItem.user_id == self.user_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {
            "total_items": total_items,
            "page": page,
            "page_size": page_size,
            "watchlist": [item.symbol for item in watchlist],
        }
