import os
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# ENV ----------
load_dotenv()
PROD_URL = os.getenv("DATABASE_PROD_URL", "default connections string")
DEV_URL = os.getenv("DATABASE_DEV_URL", "default connections string")
# --------------

# Configuration -------------
DAYS_TO_SYNC = 7
TABLES_TO_SYNC = [
    # --- Tables without dependencies ---
    {"name": "users", "date_column": None},
    {"name": "us_stocks", "date_column": None},
    {"name": "last_split_date", "date_column": "last_split_check"},
    # --- Tables with dependencies ---
    {"name": "history", "date_column": "time_stamp"},
    {"name": "portfolio", "date_column": "time_stamp"},
    {"name": "watchlist_items", "date_column": None}
]
# --------------------------

def sync_multiple_tables():
    print(f"Syncing to production database: syncing the last {DAYS_TO_SYNC} days, syncing tables: {TABLES_TO_SYNC}")

    prod_engine = create_engine(PROD_URL)
    dev_engine = create_engine(DEV_URL)

    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_SYNC)
    cutoff_str = cutoff_date.strftime("%Y-%m-%d")

    for table in TABLES_TO_SYNC:

        table_name = table["name"]
        date_col = table["date_column"]

        # Redundant code to handle tables without date column
        if date_col:
            query = f"SELECT * FROM {table_name} WHERE {date_col} >= '{cutoff_str}'"
        else:
            query = f"SELECT * FROM {table_name}"

        print(f"Processing table: '{table_name}'...")
        query = f"SELECT * FROM {table_name} WHERE {date_col} >= '{cutoff_str}'"

        try:
            df = pd.read_sql(query, prod_engine)

            if df.empty:
                print(f"No new data to sync")
                continue

            df.to_sql(table_name, dev_engine, if_exists='append', index=False)

        except Exception as e:
            print(f"Error for table: '{table_name}': {e}")
            raise e # We raise to alert a critical problem

    print("\nDEV and PROD database sync completed!")


if __name__ == "__main__":
    sync_multiple_tables()