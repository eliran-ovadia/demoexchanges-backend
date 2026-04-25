from datetime import datetime

from sqlalchemy.orm import Session

from src.exchange.background_tasks.split_stocks.split_utils import get_last_split_date, get_unique_stocks_list, \
    split_handler
from src.exchange.external_client_handlers.client_requests import fetch_splits_calendar


def split_stocks(db: Session) -> None:
    current_time = datetime.now()
    last_split_row = get_last_split_date(db, current_time)
    delta_days = (current_time - last_split_row.last_split_check).days

    if delta_days > 0:
        from_date = last_split_row.last_split_check.strftime("%Y-%m-%d")
        to_date = current_time.strftime("%Y-%m-%d")

        held_symbols = set(get_unique_stocks_list(db))
        splits = fetch_splits_calendar(from_date, to_date)

        for split in splits:
            if split.get("symbol") in held_symbols:
                split_handler(db, split)

        last_split_row.last_split_check = current_time
        db.commit()
