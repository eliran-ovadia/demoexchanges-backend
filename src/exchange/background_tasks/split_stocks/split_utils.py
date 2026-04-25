import math
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.exchange.app_logger import logger
from src.exchange.database.models import LastSplitDate, Portfolio


def get_last_split_date(db: Session, current_time: datetime) -> LastSplitDate:
    """Returns the LastSplitDate row, creating it if it doesn't exist yet."""
    row = db.query(LastSplitDate).first()
    if row is None:
        row = LastSplitDate(last_split_check=current_time)
        db.add(row)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.critical(f"Database commit failed when trying to update split table: {e}")
    return row


def get_unique_stocks_list(db: Session) -> list[str]:
    return [stock[0] for stock in db.query(Portfolio.symbol).group_by(Portfolio.symbol).all()]


def split_handler(db: Session, split: dict) -> None:
    """
    Adjust portfolio rows for a split event using a single bulk UPDATE.
    FMP split dict: {"symbol": "AAPL", "numerator": 4, "denominator": 1, "date": "..."}
    split_multiplier = numerator / denominator  (e.g. 4.0 for a 4-for-1 split)
    """
    symbol = split["symbol"]
    split_multiplier = split["numerator"] / split["denominator"]

    db.query(Portfolio).filter(Portfolio.symbol == symbol).update(
        {
            Portfolio.amount: func.ceil(Portfolio.amount * split_multiplier),
            Portfolio.price: Portfolio.price / split_multiplier,
        },
        synchronize_session=False,
    )
    db.commit()
