from dotenv import load_dotenv
from fastapi import FastAPI

from src.exchange.background_tasks.app_events import lifespan
from src.exchange.database.db_conn import engine
from src.exchange.routers import info
from .database import models
from .routers import portfolio, user, auth

load_dotenv()
app = FastAPI(lifespan=lifespan)  # Lifespan for app events with apscheduler

models.Base.metadata.create_all(engine)  # every time we find a new base we create the table for it

app.include_router(auth.router)
app.include_router(info.router)
app.include_router(portfolio.router)
app.include_router(user.router)
