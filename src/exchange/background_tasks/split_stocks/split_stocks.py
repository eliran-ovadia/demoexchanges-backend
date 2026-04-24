from datetime import datetime

from sqlalchemy.orm import Session

from src.exchange.background_tasks.split_stocks.split_utils import get_last_split_date, get_unique_stocks_list, \
    split_handler
from src.exchange.database.models import LastSplitDate
from src.exchange.external_client_handlers.client_requests import fetch_splits_calendar


def split_stocks(db: Session):
    current_time = datetime.now()
    previous_split_date = get_last_split_date(db, current_time)
    delta_days = (current_time - previous_split_date).days

    if delta_days > 0:
        from_date = previous_split_date.strftime("%Y-%m-%d")
        to_date = current_time.strftime("%Y-%m-%d")

        # One API call for all splits in the window, then filter to held symbols
        held_symbols = set(get_unique_stocks_list(db))
        splits = fetch_splits_calendar(from_date, to_date)

        for split in splits:
            if split.get("symbol") in held_symbols:
                split_handler(db, split)

        last_split_date_row = db.query(LastSplitDate).first()
        last_split_date_row.last_split_check = current_time
        db.commit()
