from fastapi import FastAPI
from . import models
from .database import engine
from .routers import portfolio, user, authentication, front
from fastapi.staticfiles import StaticFiles


app = FastAPI()

models.Base.metadata.create_all(engine) #evey time we find a new base we create the table for it

app.mount("/static", StaticFiles(directory="exchange/templates/static"), name="static")#mount the static folder for frontend


app.include_router(authentication.router)
app.include_router(portfolio.router)
app.include_router(user.router)
app.include_router(front.router)
