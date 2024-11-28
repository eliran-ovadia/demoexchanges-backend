from sqlalchemy.orm import Session

from src.exchange.background_tasks.split_stocks.apply_split import apply_splits


def split_stocks(db: Session):
    apply_splits(db)
