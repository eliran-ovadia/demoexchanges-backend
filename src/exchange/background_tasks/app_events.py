from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from src.exchange.background_tasks.scheduler_manager import SchedulerManager
from src.exchange.client_handlers.client_manager import ClientManager
from src.exchange.database.db_conn import get_db
from src.exchange.split_logic.splits_jobs import run_startup_split, run_daily_split


@asynccontextmanager
async def lifespan(app: FastAPI):
    core_functions_scheduler = SchedulerManager()
    core_functions_scheduler.start()

    db: Session = next(get_db())  # To pass for split functions
    run_startup_split(db)
    core_functions_scheduler.add_job(lambda: run_daily_split(db), trigger="interval", days=1)
    core_functions_scheduler.add_job(ClientManager.reset_clients, trigger="interval", days=1)

    yield
    core_functions_scheduler.stop()
