# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A FastAPI stock trading simulation backend. Users register, receive $100,000 virtual cash, and can buy/sell stocks with live market data. Supports portfolios, transaction history, watchlists, and analyst sentiment. Deployed targeting AWS RDS (Postgres) + ElastiCache (Redis) in production.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server (auto-reload)
uvicorn src.exchange.main:app --reload

# Run production server (single process)
uvicorn src.exchange.main:app --host 0.0.0.0 --port 8000

# Run production server (multi-process, recommended for AWS)
gunicorn src.exchange.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic current
```

No test suite or linter is currently configured.

## Environment Setup

Create a `.env` file at the project root:

```
APP_ENV=dev                          # "dev" uses *_DEV_URL vars, "prod" uses *_PROD_URL vars
DATABASE_DEV_URL=postgresql://...
DATABASE_PROD_URL=postgresql://...   # AWS RDS
SECRET_KEY=<jwt_secret>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
FMP_API_KEY=<key>                    # Financial Modeling Prep — single provider for all market data
REDIS_DEV_URL=redis://localhost:6379
REDIS_PROD_URL=rediss://your-elasticache-endpoint:6379   # TLS required for ElastiCache
```

`SECRET_KEY` and `ALGORITHM` are validated at startup — the app raises `RuntimeError` and refuses to start if either is missing.

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
| `src/exchange/main.py` | App entry point; wires slowapi rate limiter |
| `src/exchange/routers/` | Four routers: `auth`, `info`, `portfolio`, `user` |
| `src/exchange/routers/repository/` | Business logic: `portfolio_repo`, `info_repo`, `user_repo`, `auth_repo` |
| `src/exchange/database/models.py` | SQLAlchemy ORM models for all 6 tables |
| `src/exchange/database/db_conn.py` | Engine + session factory; env-based URL selection |
| `src/exchange/Auth/` | JWT token creation/verification, bcrypt hashing, OAuth2 dependency |
| `src/exchange/redis_manager.py` | `RedisClient` / `RedisManager` singleton; blacklist + cache helpers |
| `src/exchange/rate_limiter.py` | `slowapi` `Limiter` instance with Redis storage backend |
| `src/exchange/external_client_handlers/` | FMP API client singleton (`ClientManager`) and typed response parsers |
| `src/exchange/background_tasks/` | APScheduler jobs wired via FastAPI lifespan context manager |

### Database Schema

Six tables: `users`, `portfolio` (current holdings), `history` (transactions), `watchlist_items`, `us_stocks` (cached symbol metadata), `last_split_date`. User deletion cascades to portfolio, history, and watchlist. Alembic manages all schema migrations.

### External API — FMP

`ClientManager` (`external_client_handlers/client_manager.py`) provides a lazily-initialized `FMPClient` singleton backed by `requests.Session`. All calls go through `client_requests.py` which maps raw FMP JSON to internal Pydantic schemas (`schemas/fmp_schemas.py`). The client is reset daily at midnight by a background job.

### Redis Usage

`RedisManager` selects `REDIS_DEV_URL` or `REDIS_PROD_URL` based on `APP_ENV`. It is used for:
- **Token blacklist**: `blacklist:{jti}` keys with TTL = remaining token lifetime (logout support)
- **Rate limiting**: `slowapi` uses Redis as backing store for `/Token` (5 req/minute per IP)
- **Market movers cache**: JSON blob stored at key `market_movers`, TTL 25 hours

Redis failures are fail-open for blacklist reads (logged but user is not locked out).

### Background Tasks

Registered via `app_events.py` lifespan; all run on APScheduler:
- **4:00 AM UTC** — Detect stock splits (FMP), adjust user portfolio share counts
- **4:02 AM UTC** — Refresh `us_stocks` table from FMP
- **4:03 AM UTC** — Update market movers cache in Redis
- **12:01 AM UTC** — Reset FMP HTTP client session

### Authentication

OAuth2 Bearer tokens (JWT, HS256). Each token includes a `jti` (UUID4) claim.
- `/Token` — login, rate-limited to 5/min per IP
- `/Logout` — blacklists the token's `jti` in Redis with remaining-TTL expiry
- `get_current_user` checks Redis blacklist on every protected request
- Admin-only routes re-verify `is_admin` from DB, not just the JWT claim
- Timing attack prevented: a dummy bcrypt hash is always checked when the user doesn't exist

### Order Execution

`portfolio_repo.py` fetches a live price from FMP, validates cash/shares, updates the `portfolio` row (unique per user+symbol), and writes to `history` with profit/loss. All in one DB session.
