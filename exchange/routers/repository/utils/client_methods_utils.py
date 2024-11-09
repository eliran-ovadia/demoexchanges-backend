import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from exchange.app_logger import logger
from exchange.models import lastSplitDate, Portfolio


def get_api_key(client: str) -> str:  # API key extractor from env file
    api_key = os.getenv(client)
    if not api_key:
        logger.error(f"API key for {client} is not set.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"API key for {client} is missing"
        )

    return api_key


def get_last_split_date(db: Session) -> datetime:
    row = db.query(lastSplitDate).first()
    if row is None: # Handle a new empty table with no rows, in case of table delete
        row = lastSplitDate(last_split_check=datetime.now())
        db.add(row)
        db.commit()

    return row.last_split_check


def get_unique_stocks_list(db: Session):
    unique_stocks_list = [stock[0] for stock in db.query(Portfolio.symbol)
                    .group_by(Portfolio.symbol).all()] # Handle the list of Tuples (representing rows)
                                                        # I get from the query - result in a list of symbols
    return unique_stocks_list