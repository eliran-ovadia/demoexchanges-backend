# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A FastAPI stock trading simulation backend. Users register, receive $100,000 virtual cash, and can buy/sell stocks with live market data. Supports portfolios, transaction history, watchlists, and analyst sentiment. Deployed targeting AWS RDS in production.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
uvicorn src.exchange.main:app --reload

# Run production server
uvicorn src.exchange.main:app --host 0.0.0.0 --port 8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic current
```

No test suite or linter is currently configured.

## Environment Setup

Create a `.env` file at the project root:

```
APP_ENV=dev                          # "dev" uses DATABASE_DEV_URL, "prod" uses DATABASE_PROD_URL
DATABASE_DEV_URL=postgresql://...
DATABASE_PROD_URL=postgresql://...   # AWS RDS
SECRET_KEY=<jwt_secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
TWELVE_DATA_API_KEY=<key>
POLYGON_API_KEY=<key>
FINNHUB_API_KEY=<key>
```

## Architecture

### Request Flow

```
Route handler (routers/*.py)
  → Repository function (routers/repository/*_repo.py)
    → SQLAlchemy ORM (database/models.py) + External API clients
```

Route handlers are thin — they validate auth, call a repository function, and return the result. All business logic lives in the repository layer.

### Key Modules

| Path | Purpose |
|------|---------|
| `src/exchange/main.py` | App entry point; creates tables on startup |
| `src/exchange/routers/` | Four routers: `auth`, `info`, `portfolio`, `user` |
| `src/exchange/routers/repository/` | Business logic: `portfolio_repo`, `info_repo`, `user_repo`, `auth_repo` |
| `src/exchange/database/models.py` | SQLAlchemy ORM models for all 6 tables |
| `src/exchange/database/db_conn.py` | Engine + session factory; env-based URL selection |
| `src/exchange/Auth/` | JWT token creation/verification, bcrypt hashing, OAuth2 dependency |
| `src/exchange/external_client_handlers/` | API client singletons (TwelveData, Polygon, Finnhub) and response parsers |
| `src/exchange/background_tasks/` | APScheduler jobs wired via FastAPI lifespan context manager |

### Database Schema

Six tables: `users`, `portfolio` (current holdings), `history` (transactions), `watchlist_items`, `us_stocks` (cached symbol metadata), `last_split_date`. User deletion cascades to portfolio, history, and watchlist.

`models.Base.metadata.create_all(engine)` runs on every startup — new models get their tables automatically. Alembic handles schema changes for existing tables.

### External API Clients

`ClientManager` (`external_client_handlers/client_manager.py`) provides class-level singletons for TwelveData, Polygon, and Finnhub. Clients are lazily initialized on first use and optionally reset daily by a background job. Raw API calls live in `client_requests.py`; response parsing lives in `client_response_models/`.

### Background Tasks

Registered via `app_events.py` lifespan; all run on APScheduler:
- **4:00 AM UTC** — Detect stock splits (Polygon), adjust user portfolio share counts
- **4:02 AM UTC** — Refresh `us_stocks` table from TwelveData
- **4:03 AM UTC** — Update in-memory market movers cache

### Authentication

OAuth2 Bearer tokens (JWT). `/Token` endpoint accepts `username` (email) + `password` form data. Protected routes depend on `get_current_user` from `Auth/oauth2.py`. Admin-only routes check `is_admin` from token payload.

### Order Execution

`portfolio_repo.py` fetches a live price from TwelveData, validates cash/shares, updates the `portfolio` row (unique per user+symbol), and writes to `history` with profit/loss. All in one DB session.