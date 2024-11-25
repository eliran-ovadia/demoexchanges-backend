from sqlalchemy.orm import Session

from src.exchange.client_handlers.clients_functions import apply_splits


def run_daily_split(db: Session):
    apply_splits(db)


def run_startup_split(db: Session):
    apply_splits(db)
