from .clients_functions import apply_splits
from .database import get_db
from .scheduler_manager import add_job


def run_daily_split():
    db = next(get_db())
    apply_splits(db)


def run_startup_split():
    db = next(get_db())
    apply_splits(db)


add_job(run_daily_split, trigger="interval", days=1)
