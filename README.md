# Stock Trading Exchange API

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136.1-009688?style=flat&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?style=flat&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-asyncio-DC382D?style=flat&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?style=flat&logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate-FF9900?style=flat&logo=amazonaws&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-92%20passing-brightgreen?style=flat&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-76%25-yellow?style=flat)
![Release](https://img.shields.io/github/v/release/eliran-ovadia/demo_stock_trading_full_backend?style=flat)

A production-grade async REST API simulating a stock trading exchange. Users start with **$100,000 virtual cash** and can trade real US stocks with live market data, manage portfolios, track transaction history, and follow analyst sentiment — all backed by a secure JWT authentication system with refresh token rotation.

---

## Features

1. Live market data : real-time quotes, market movers, stock search, and analyst sentiment via Financial Modeling Prep
2. Paper trading : buy and sell US stocks at live prices with profit/loss calculated on every trade
3. Portfolio management : paginated holdings with live valuations, average cost basis, and total return
4. Transaction history : full audit trail of every order with timestamps and realized P&L
5. Watchlist : track symbols without trading them
6. Secure auth : JWT access tokens (15 min) with refresh token rotation; logout blacklists tokens in Redis
7. Rate limiting : per-IP on all endpoints, Redis-backed, with stricter limits on auth routes
8. Stock split detection : nightly background job adjusts share counts automatically
9. Fully async : asyncpg, httpx, and redis.asyncio throughout for high concurrency

---

## System Architecture

```mermaid
graph TB
    Client(["Client (Browser / App)"])

    subgraph AWS ["AWS Cloud"]
        ALB["Application Load Balancer\n(HTTPS · ACM Certificate)"]

        subgraph ECS ["ECS Fargate"]
            API["FastAPI App\n(Gunicorn + Uvicorn workers)"]
        end

        RDS[("PostgreSQL\nAWS RDS")]
        REDIS[("Redis\nAWS ElastiCache")]
        SECRETS["Secrets Manager\n(env vars at boot)"]
    end

    FMP["Financial Modeling Prep\n(Live Market Data)"]

    Client -->|"HTTPS"| ALB
    ALB -->|"HTTP :8000"| API
    API -->|"async SQLAlchemy"| RDS
    API -->|"redis.asyncio"| REDIS
    API -->|"httpx async"| FMP
    SECRETS -.->|"injected at startup"| API
```

### Request Flow

```
HTTP Request
  └─ ALB (SSL termination)
       └─ FastAPI middleware (request logger)
            └─ slowapi rate limiter (Redis-backed)
                 └─ OAuth2 dependency (JWT verify + Redis blacklist check)
                      └─ Router handler (thin — validates input, calls repo)
                           └─ Repository layer (all business logic)
                                ├─ SQLAlchemy AsyncSession (PostgreSQL)
                                └─ FMP API client (httpx)
```

### Component Responsibilities

| Component | Role |
|---|---|
| **Routers** (`routers/*.py`) | Declare endpoints, apply auth/rate-limit decorators, call repository |
| **Repository** (`routers/repository/*_repo.py`) | All business logic — DB queries, external API calls, validation |
| **Auth** (`Auth/`) | JWT encode/decode, bcrypt hashing, OAuth2 dependency, timing-attack prevention |
| **Redis Manager** (`redis_manager.py`) | Token blacklist, refresh token store, market movers cache |
| **FMP Client** (`external_client_handlers/`) | Lazy singleton HTTP client, retry logic, response parsing |
| **Background Tasks** (`background_tasks/`) | APScheduler jobs — split detection, stock list refresh, cache warm-up |
| **Rate Limiter** (`rate_limiter.py`) | slowapi Limiter with Redis storage, per-IP keying |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Server | Gunicorn + Uvicorn workers |
| Database ORM | SQLAlchemy 2.0 (async) |
| Database driver | asyncpg |
| Cache / Broker | Redis (redis.asyncio) |
| Auth | JWT (python-jose) + bcrypt |
| Market data | Financial Modeling Prep REST API (httpx) |
| Background jobs | APScheduler |
| Rate limiting | slowapi |
| Migrations | Alembic |
| Containerization | Docker |
| Cloud | AWS ECS Fargate, RDS, ElastiCache, ALB, ACM, Secrets Manager |
| Testing | pytest-asyncio, fakeredis, aiosqlite (92 tests, 76% coverage) |

---

## API Endpoints

### Authentication
| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/Token` | Login — returns access + refresh token | No |
| `POST` | `/Refresh` | Exchange refresh token for new token pair | No |
| `POST` | `/Logout` | Blacklist access token, revoke refresh token | Yes |

### Users
| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/api/CreateUser` | Register new user (starts with $100k) | No |
| `PATCH` | `/api/ResetPortfolio` | Reset holdings and cash to defaults | Yes |
| `DELETE` | `/api/DeleteUser` | Delete a user account (admin only) | Yes (admin) |

### Portfolio & Trading
| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/api/GetPortfolio` | Paginated holdings with live valuations | Yes |
| `POST` | `/api/Order` | Buy or sell shares at live market price | Yes |
| `GET` | `/api/GetHistory` | Paginated transaction history with P&L | Yes |
| `POST` | `/api/AddToWatchlist` | Add a symbol to watchlist | Yes |
| `DELETE` | `/api/DeleteFromWatchlist` | Remove a symbol from watchlist | Yes |
| `GET` | `/api/GetWatchlist` | Paginated watchlist | Yes |

### Market Data
| Method | Path | Description | Auth |
|---|---|---|---|
| `GET` | `/api/ParsedQuote` | Full quote for a symbol | Yes |
| `GET` | `/api/StockSearch` | Search stocks by symbol or name | Yes |
| `GET` | `/api/MarketStatus` | Whether the US market is currently open | Yes |
| `GET` | `/api/MarketMovers` | Top gaining/losing stocks today (cached) | Yes |
| `GET` | `/api/StockSentiment` | Analyst buy/sell/hold consensus | Yes |

Interactive docs available at `/docs` when the server is running.

---

## Security Design

1. JWT access tokens : 15-minute TTL, signed with HS256; user data embedded so protected routes require no DB hit per request
2. Refresh token rotation : each token is single-use; reuse of a consumed token triggers immediate invalidation
3. Logout blacklist : revoked JTIs stored in Redis with exact remaining TTL, cleaned up automatically on expiry
4. Timing attack prevention : bcrypt always runs even when the user doesn't exist
5. Admin verification : admin status re-checked from DB on admin routes, not trusted from the JWT claim
6. Password policy : requires uppercase, lowercase, digit, and special character; blocks common passwords and personal info

---

## Background Jobs (UTC)

| Time | Job |
|---|---|
| 04:00 | Detect stock splits via FMP, adjust all user share counts |
| 04:02 | Refresh `us_stocks` symbol metadata table from FMP |
| 04:03 | Update market movers Redis cache (25-hour TTL) |
| 00:01 | Reset FMP HTTP client session |

---

## Database Schema

```mermaid
erDiagram
    users ||--o{ history : "has many"
    users ||--o{ portfolio : "owns"
    users ||--o{ watchlist_items : "tracks"

    users {
        String id PK
        String name
        String last_name
        String email
        String password
        Numeric cash
        Boolean is_admin
        DateTime created_at
        DateTime updated_at
    }
    history {
        Integer order_id PK
        String user_id FK
        String symbol
        Numeric price
        Integer amount
        String type
        Numeric value
        Numeric profit
        DateTime created_at
        DateTime updated_at
    }
    portfolio {
        Integer stock_id PK
        String user_id FK
        String symbol
        Integer amount
        Numeric price
        DateTime created_at
        DateTime updated_at
    }
    watchlist_items {
        Integer id PK
        String user_id FK
        String symbol
        DateTime created_at
        DateTime updated_at
    }
    us_stocks {
        Integer id PK
        String symbol
        String name
        String currency
        String exchange
        String mic_code
        String country
        String type
        String figi_code
        DateTime created_at
        DateTime updated_at
    }
    last_split_date {
        Integer id PK
        DateTime last_split_check
        DateTime created_at
        DateTime updated_at
    }
```

---

## Getting Started

Requires Python 3.14+, PostgreSQL, and Redis.

### Local Setup (without Docker)

```bash
# Clone and install
pip install -r requirements.txt

# Create .env file
cp .env.example .env   # then fill in your values

# Run migrations
alembic upgrade head

# Start dev server
uvicorn src.exchange.main:app --reload
```

### Local Setup (Docker)

```bash
# Build and start Postgres, Redis, and the API
docker compose up --build
```

The `migrate` service runs `alembic upgrade head` automatically before the API starts. On subsequent runs with an existing volume, it is a no-op if the schema is already up to date.

### Environment Variables

```env
APP_ENV=dev
DATABASE_DEV_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
SECRET_KEY=your-secret-key-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
FMP_API_KEY=your-fmp-api-key
REDIS_DEV_URL=redis://localhost:6379
```

### Running Tests

```bash
pip install -r requirements-test.txt
pytest tests/ -q                        # all 92 tests
pytest tests/unit/ -q                   # unit tests only
pytest tests/integration/ -q            # integration tests only
pytest tests/ --cov=src --cov-report=html  # with coverage report
```

---

## Cloud Deployment

Deployed on **AWS ECS Fargate** behind an **Application Load Balancer** with HTTPS termination via ACM. Environment variables are injected from **AWS Secrets Manager** at container boot. CI/CD via GitHub Actions: tests must pass before any image is built or deployed.

### Migrations on AWS

Migrations are intentionally not run on every container start — doing so would race across multiple ECS tasks scaling up simultaneously. Instead, run migrations once as a one-off ECS task before each deployment:

```bash
aws ecs run-task \
  --cluster <your-cluster> \
  --task-definition <your-task-definition> \
  --overrides '{"containerOverrides":[{"name":"api","command":["alembic","upgrade","head"]}]}' \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>]}"
```
