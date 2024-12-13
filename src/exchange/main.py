from fastapi import FastAPI

from src.exchange.background_tasks.app_events import lifespan
from src.exchange.database import models
from src.exchange.database.db_conn import engine
from src.exchange.routers.auth import router as auth_router
from src.exchange.routers.info import router as info_router
from src.exchange.routers.portfolio import router as portfolio_router
from src.exchange.routers.user import router as user_router

# We imported the app from app_instance instead of define it here, to be able to import it without circular imports

models.Base.metadata.create_all(engine)  # every time we find a new base we create the table for it

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(info_router)
app.include_router(portfolio_router)
app.include_router(user_router)
