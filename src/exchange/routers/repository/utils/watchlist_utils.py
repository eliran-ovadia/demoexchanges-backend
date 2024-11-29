from http.client import HTTPException

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.exchange.database.db_conn import get_db
from src.exchange.database.models import WatchlistItem, UsStocks


class WatchlistHandler:

    def __init__(self, db: Session=get_db(), user_id: str = ''):
        self.db = db
        self.user_id = user_id


    def is_listed(self, request) -> bool:
        listing = self.db.query(UsStocks.symbol).filter(UsStocks.symbol==request).first()
        if listing is None:
            return False
        else:
            return True

    def add_to_watchlist(self, request:str) -> dict:
        if not self.is_listed(request):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail='Cannot add non existent stock to watchlist')
        else:
            new_entry = WatchlistItem(symbol=request, user_id=self.user_id)
            self.db.add(new_entry)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                    detail=f"Stock symbol '{request}' is already in your watchlist.")

            return {'message': 'Stock added successfully to your watchlist'}

    def delete_from_watchlist(self, request) -> dict:
        entry = (self.db.query(WatchlistItem)
                 .filter(WatchlistItem.symbol == request, WatchlistItem.user_id == self.user_id)
                 .first())

        if entry is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Stock symbol '{request}' is not in your watchlist.")
        else:
            self.db.delete(entry)
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"An error occurred while attempting to delete {self.request}."
                )
            return {'message': 'Stock deleted successfully from your watchlist'}

    def get_watchlist(self, page, page_size) -> dict:
        watchlist = (self.db.query(WatchlistItem)
                     .filter(WatchlistItem.user_id == self.user_id)
                     .offset((page - 1) * page_size).limit(page_size)
                     .all())

        watchlist_to_return = [item.symbol for item in watchlist]

        return {"watchlist": watchlist_to_return}
