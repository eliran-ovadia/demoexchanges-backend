import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()
environment = os.getenv("APP_ENV", "dev")

if environment == "prod":
    print("Starting in PRODUCTION mode (CLOUD AWS RDS)")
    SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_PROD_URL", "default connections string")
else:
    print("Starting in DEV mode (Local Docker container)")
    SQLALCHEMY_DATABASE_URL: str = os.getenv("DATABASE_DEV_URL", "default connections string")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # drops stale connections before use
    pool_recycle=1800,   # recycle connections every 30 min — important for RDS
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    pass