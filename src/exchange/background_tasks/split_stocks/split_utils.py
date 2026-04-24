import math
from datetime import datetime

from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.database.models import LastSplitDate, Portfolio


def get_last_split_date(db: Session, current_time: datetime) -> datetime:
    row = db.query(LastSplitDate).first()
    if row is None:
        row = LastSplitDate(last_split_check=current_time)
        db.add(row)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.critical(f"Database commit failed when trying to update split table: {e}")

    return row.last_split_check


def get_unique_stocks_list(db: Session) -> list[str]:
    return [stock[0] for stock in db.query(Portfolio.symbol).group_by(Portfolio.symbol).all()]


def split_handler(db: Session, split: dict):
    """
    Adjust portfolio rows for a split event.
    FMP split dict: {"symbol": "AAPL", "numerator": 4, "denominator": 1, "date": "..."}
    split_multiplier = numerator / denominator  (e.g. 4.0 for a 4-for-1 split)
    """
    symbol = split["symbol"]
    split_multiplier = split["numerator"] / split["denominator"]

    stock_rows = db.query(Portfolio).filter(Portfolio.symbol == symbol).all()
    for row in stock_rows:
        row.amount = math.ceil(row.amount * split_multiplier)
        row.price = row.price / split_multiplier

    db.commit()
