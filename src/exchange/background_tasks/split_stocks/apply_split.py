from datetime import datetime

from sqlalchemy.orm import Session

from src.exchange.background_tasks.split_stocks.split_logic import get_last_split_date, get_unique_stocks_list, \
    split_handler
from src.exchange.client_handlers.client_manager import ClientManager
from src.exchange.database.models import LastSplitDate


def apply_splits(db: Session):
    current_time = datetime.now()
    previous_split_date = get_last_split_date(db, current_time)
    delta_time = current_time - previous_split_date
    delta_days = delta_time.days

    if delta_days > 0:
        formatted_last_split_date = previous_split_date.strftime("%Y-%m-%d")
        formatted_now = current_time.strftime("%Y-%m-%d")
        unique_symbol_list = get_unique_stocks_list(db)
        pg = ClientManager.get_polygon_client()

        for symbol in unique_symbol_list:
            # Convert the generator to a list and access the first item
            response = next(pg.list_splits(reverse_split=True, sort='execution_date', order='desc', ticker=symbol,
                                           execution_date_gt=formatted_last_split_date,
                                           execution_date_lte=formatted_now), None)
            # Check if response is None or results are empty
            if not response or not response.get('results'):
                continue

            for split in response['results']:
                split_handler(db, split, symbol)

        last_split_date_row = db.query(LastSplitDate).first()
        last_split_date_row.last_split_check = current_time
        db.commit()
