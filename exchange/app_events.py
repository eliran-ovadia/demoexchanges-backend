from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from .clients import ClientManager
from .database import get_db
from .scheduler_manager import start_scheduler, stop_scheduler, add_job
from .split_scheduler import run_startup_split, run_daily_split


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()

    db: Session = next(get_db())  # To pass for split functions
    run_startup_split(db)
    add_job(lambda: run_daily_split(db), trigger="interval", days=1)
    add_job(ClientManager.reset_clients, trigger="interval", days=1)

    yield
    stop_scheduler()
