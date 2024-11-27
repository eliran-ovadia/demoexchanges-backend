from sqlalchemy.orm import Session

from src.exchange.split_logic.apply_splits import apply_splits


def run_daily_split(db: Session):
    apply_splits(db)


def run_startup_split(db: Session):
    apply_splits(db)
