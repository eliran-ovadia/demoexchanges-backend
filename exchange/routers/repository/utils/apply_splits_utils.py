import math
from datetime import datetime

from sqlalchemy.orm import Session

from exchange.models import lastSplitDate, Portfolio


def get_last_split_date(db: Session, current_time: datetime) -> datetime:
    row = db.query(lastSplitDate).first()
    if row is None:  # Handle a new empty table with no rows, in case of table delete
        row = lastSplitDate(last_split_check=current_time)
        db.add(row)
        db.commit()

    return row.last_split_check


def get_unique_stocks_list(db: Session):
    unique_stocks_list = [stock[0] for stock in db.query(Portfolio.symbol)
    .group_by(Portfolio.symbol).all()]  # Handle the list of Tuples (representing rows)
    # I get from the query - result in a list of symbols
    return unique_stocks_list


def split_handler(db: Session, split, symbol):
    stock_rows = db.query(Portfolio).filter(Portfolio.symbol == symbol).all()

    split_multiplier = split['split_to'] / split['split_from']

    for row in stock_rows:
        row.amount = math.ceil(row.amount * split_multiplier)
        row.price = row.price / split_multiplier

    db.commit()
