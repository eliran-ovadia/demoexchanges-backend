from fastapi import FastAPI
from . import models
from .database import engine
from .routers import portfolio, user, authentication, front
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://yourfrontend.com",
    # Add other origins as needed
]

# Add CORS middleware to the FastAPI application
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

models.Base.metadata.create_all(engine) #evey time we find a new base we create the table for it

app.mount("/static", StaticFiles(directory="exchange/templates/static"), name="static")#mount the static folder for frontend

app.include_router(authentication.router)
app.include_router(portfolio.router)
app.include_router(user.router)
app.include_router(front.router)
