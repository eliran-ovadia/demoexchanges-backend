import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

load_dotenv()
environment = os.getenv("APP_ENV", "dev")

if environment == "prod":
    print("Starting in PRODUCTION mode (CLOUD AWS RDS)")
    _url = os.getenv("DATABASE_PROD_URL", "")
    _connect_args = {"ssl": "require"}
else:
    print("Starting in DEV mode (Local Docker container)")
    _url = os.getenv("DATABASE_DEV_URL", "")
    _connect_args = {}

# asyncpg requires the postgresql+asyncpg:// scheme
SQLALCHEMY_DATABASE_URL = _url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as db:
        yield db
