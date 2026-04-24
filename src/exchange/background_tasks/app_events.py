from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session

from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.background_tasks.fetch_us_stocks.fetch_us_stocks import update_stock_list
from src.exchange.background_tasks.scheduler_manager import SchedulerManager
from src.exchange.background_tasks.split_stocks.split_stocks import split_stocks
from src.exchange.database.db_conn import get_db
from src.exchange.external_client_handlers.client_manager import ClientManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    core_functions_scheduler = SchedulerManager()
    core_functions_scheduler.start()

    db: Session = next(get_db())

    # Populate market movers cache on startup so the endpoint works immediately
    MarketMoversManager.update_market_movers()

    # Daily refresh jobs
    core_functions_scheduler.add_job(lambda: update_stock_list(db), trigger="cron", hour=4, minute=2)
    core_functions_scheduler.add_job(MarketMoversManager.update_market_movers, trigger="cron", hour=4, minute=3)
    core_functions_scheduler.add_job(lambda: split_stocks(db), trigger="cron", hour=4, minute=0)
    core_functions_scheduler.add_job(ClientManager.reset_clients, trigger="cron", hour=0, minute=1)

    yield
    core_functions_scheduler.stop()
