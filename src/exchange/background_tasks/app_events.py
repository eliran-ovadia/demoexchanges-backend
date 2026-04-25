from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.exchange.Auth.token_functions import validate_auth_config
from src.exchange.background_tasks.fetch_market_movers.market_movers_handler import MarketMoversManager
from src.exchange.background_tasks.fetch_us_stocks.fetch_us_stocks import update_stock_list
from src.exchange.background_tasks.scheduler_manager import SchedulerManager
from src.exchange.background_tasks.split_stocks.split_stocks import split_stocks
from src.exchange.database.db_conn import AsyncSessionLocal
from src.exchange.external_client_handlers.client_manager import ClientManager
from src.exchange.redis_manager import RedisManager


async def _job_split_stocks() -> None:
    async with AsyncSessionLocal() as db:
        await split_stocks(db)


async def _job_update_stock_list() -> None:
    async with AsyncSessionLocal() as db:
        await update_stock_list(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_auth_config()
    RedisManager.get_client()  # ensure Redis connection is valid at startup

    scheduler = SchedulerManager()
    scheduler.start()

    await MarketMoversManager.update_market_movers()

    scheduler.add_job(_job_split_stocks, trigger="cron", hour=4, minute=0)
    scheduler.add_job(_job_update_stock_list, trigger="cron", hour=4, minute=2)
    scheduler.add_job(MarketMoversManager.update_market_movers, trigger="cron", hour=4, minute=3)
    scheduler.add_job(ClientManager.reset_clients, trigger="cron", hour=0, minute=1)

    yield

    scheduler.stop()
