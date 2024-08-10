from fastapi import FastAPI
from dotenv import load_dotenv
from . import models
from .database import engine
from .routers import portfolio, user, authentication

app = FastAPI()

load_dotenv()
models.Base.metadata.create_all(engine) #every time we find a new base we create the table for it


app.include_router(authentication.router)
app.include_router(portfolio.router)
app.include_router(user.router)