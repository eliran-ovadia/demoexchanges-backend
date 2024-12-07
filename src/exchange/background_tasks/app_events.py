from contextlib import asynccontextmanager

from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.background_tasks.fetch_us_stocks.fetch_us_stocks import update_stock_list
from src.exchange.background_tasks.scheduler_manager import SchedulerManager
from src.exchange.background_tasks.split_stocks.split_stocks import split_stocks
from src.exchange.database.db_conn import get_db
from src.exchange.external_client_handlers.client_manager import ClientManager
from src.exchange.external_client_handlers.client_response_models.market_status_model import refresh_market_status


@asynccontextmanager
async def lifespan(app: FastAPI):
    ########  Schedular start ########
    core_functions_scheduler = SchedulerManager()
    core_functions_scheduler.start()

    ########  startup tasks and variables ########
    refresh_market_status(app)
    db: Session = next(get_db())

    ########  add jobs to the schedular ########
    core_functions_scheduler.add_job(lambda: split_stocks(db), trigger="interval", days=1)
    core_functions_scheduler.add_job(ClientManager.reset_clients, trigger="interval", days=1)
    core_functions_scheduler.add_job(lambda: update_stock_list(db), trigger="interval", days=1)
    core_functions_scheduler.add_job(MarketMoversManager.update_market_movers(), trigger="interval", days=1)
    core_functions_scheduler.add_job(lambda: refresh_market_status(app), trigger=CronTrigger(minute='0,30'))

    ########  close lifespan ########
    yield  # Wait for app to terminate
    core_functions_scheduler.stop()
