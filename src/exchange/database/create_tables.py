import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

from src.exchange.database.db_conn import engine, Base
from src.exchange.database.models import User, History, Portfolio, WatchlistItem, UsStocks, LastSplitDate


def init_db():
    print("\nstarting to create tables...")

    print("Deleting old tables if there are")
    Base.metadata.drop_all(bind=engine)

    print("Creating clean new tables")
    Base.metadata.create_all(bind=engine)

    print("\nCreated successfully!")


if __name__ == "__main__":
    current_env = os.getenv("APP_ENV", "dev")

    if current_env == "prod":
        print("\nCritical!, you are trying to reset the production tables, this will delete everything")

        confirm = input("Continue anyway?: ")

        if confirm.lower() == 'yes':
            init_db()
        else:
            print("Cancelled")
    else:
        init_db()