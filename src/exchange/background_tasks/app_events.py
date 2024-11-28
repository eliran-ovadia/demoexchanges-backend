from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_us_stocks.fetch_us_stocks import update_stock_list
from src.exchange.background_tasks.scheduler_manager import SchedulerManager
from src.exchange.background_tasks.split_stocks.split_jobs import split_stocks
from src.exchange.client_handlers.client_manager import ClientManager
from src.exchange.database.db_conn import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    ########  Schedular start ########
    core_functions_scheduler = SchedulerManager()
    core_functions_scheduler.start()

    ########  run startup tasks ########
    db: Session = next(get_db())  # To pass for split functions
    split_stocks(db)
    update_stock_list(db)

    ########  add jobs to the schedular ########
    core_functions_scheduler.add_job(lambda: split_stocks(db), trigger="interval", days=1)
    core_functions_scheduler.add_job(ClientManager.reset_clients, trigger="interval", days=1)
    core_functions_scheduler.add_job(lambda: update_stock_list(db), trigger="interval", days=1)

    ########  close lifespan ########
    yield  # Wait for app to terminate
    core_functions_scheduler.stop()
