import json
import os
import uuid
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ── Set env vars before any app module is imported ─────────────────────────
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-minimum-32-chars!!")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "120")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "7")
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("REDIS_DEV_URL", "redis://localhost:6379")       # mocked — never used
os.environ.setdefault("DATABASE_DEV_URL", "postgresql://placeholder/placeholder")  # overridden
os.environ.setdefault("FMP_API_KEY", "test-fmp-key")

from src.exchange.Auth.hashing import Hash
from src.exchange.Auth.token_functions import create_access_token, create_refresh_token
from src.exchange.database.db_conn import Base, get_db
from src.exchange.database.models import User
from src.exchange.main import app
from src.exchange.rate_limiter import limiter
from src.exchange.redis_manager import RedisClient, RedisManager
from src.exchange.schemas.fmp_schemas import QuoteSchema


# ── Database ────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def db_engine():
    unique = uuid.uuid4().hex
    url = f"sqlite+aiosqlite:///file:{unique}?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(url, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    Session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session


# ── Redis ───────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def fake_redis():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
def redis_client(fake_redis):
    client = RedisClient.__new__(RedisClient)
    client._redis = fake_redis
    return client


# ── HTTP client with all dependencies overridden ───────────────────────────

@pytest_asyncio.fixture
async def client(db_engine, redis_client):
    async def override_get_db():
        Session = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with Session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch.object(RedisManager, "get_client", return_value=redis_client),
        patch(
            "src.exchange.background_tasks.app_events.MarketMoversManager.update_market_movers",
            new_callable=AsyncMock,
        ),
        patch.object(limiter, "enabled", False),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c

    app.dependency_overrides.clear()


# ── User / auth helpers ────────────────────────────────────────────────────

USER_EMAIL = "testuser@example.com"
USER_PASSWORD = "Secure#Pass9"
USER_PAYLOAD = {
    "name": "Test",
    "last_name": "User",
    "email": USER_EMAIL,
    "password": USER_PASSWORD,
    "password_confirm": USER_PASSWORD,
}

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "AdminSecure#9"


@pytest_asyncio.fixture
async def registered_user(client):
    await client.post("/api/users", json=USER_PAYLOAD)
    return USER_PAYLOAD


@pytest_asyncio.fixture
async def auth_tokens(client, registered_user):
    resp = await client.post(
        "/token",
        data={"username": USER_EMAIL, "password": USER_PASSWORD},
    )
    data = resp.json()
    return data["access_token"], data["refresh_token"]


@pytest_asyncio.fixture
def auth_headers(auth_tokens):
    return {"Authorization": f"Bearer {auth_tokens[0]}"}


@pytest_asyncio.fixture
async def admin_user(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Admin",
        last_name="User",
        email=ADMIN_EMAIL,
        password=Hash.bcrypt(ADMIN_PASSWORD),
        is_admin=True,
        cash=100_000,
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def admin_headers(client, admin_user):
    resp = await client.post(
        "/token",
        data={"username": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── FMP mock helpers ────────────────────────────────────────────────────────

def make_quote(symbol: str = "AAPL", price: float = 150.0) -> QuoteSchema:
    return QuoteSchema(
        symbol=symbol,
        name=f"{symbol} Corp.",
        exchange="NASDAQ",
        currency="USD",
        price=price,
        open=price - 1,
        high=price + 2,
        low=price - 2,
        previous_close=price - 1,
        change=1.0,
        percent_change=0.67,
        volume=1_000_000,
        avg_volume=900_000,
        year_high=price + 50,
        year_low=price - 50,
    )


MOCK_MARKET_MOVERS = {
    "stocks": [
        {"symbol": "AAPL", "name": "Apple Inc.", "price": 150.0, "change": 2.0, "percent_change": 1.35},
        {"symbol": "NVDA", "name": "NVIDIA Corp.", "price": 800.0, "change": -5.0, "percent_change": -0.62},
    ]
}
