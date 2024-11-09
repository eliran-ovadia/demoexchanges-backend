from contextlib import asynccontextmanager

from fastapi import FastAPI

from .scheduler_manager import start_scheduler, stop_scheduler
from .split_scheduler import run_startup_split


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_startup_split()
    start_scheduler()
    yield  # Wait until shutdown
    stop_scheduler()
