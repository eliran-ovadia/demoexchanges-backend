from fastapi import FastAPI

from src.exchange.background_tasks.app_events import lifespan

app = FastAPI(lifespan=lifespan)
