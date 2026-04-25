"""Market info endpoints: ParsedQuote, MarketStatus, StockSearch, MarketMovers, StockSentiment."""
import json
from unittest.mock import AsyncMock, patch

from tests.conftest import make_quote, MOCK_MARKET_MOVERS

_FETCH_QUOTE = "src.exchange.routers.repository.info_repo.fetch_quote"
_FETCH_STATUS = "src.exchange.routers.repository.info_repo.fetch_market_status"
_FETCH_SEARCH = "src.exchange.routers.repository.info_repo.fetch_search"
_FETCH_SENTIMENT = "src.exchange.routers.repository.info_repo.fetch_sentiment"
_GET_MOVERS = "src.exchange.routers.repository.info_repo.MarketMoversManager.get_market_movers"


# ── GET /api/ParsedQuote ──────────────────────────────────────────────────────

async def test_parsed_quote_returns_200(client, auth_headers):
    with patch(_FETCH_QUOTE, new_callable=AsyncMock, return_value={"AAPL": make_quote("AAPL", 150.0)}):
        resp = await client.get("/api/ParsedQuote?symbol=AAPL", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert "AAPL" in body
    assert body["AAPL"]["close"] == 150.0
    assert body["AAPL"]["exchange"] == "NASDAQ"


async def test_parsed_quote_requires_auth(client):
    resp = await client.get("/api/ParsedQuote?symbol=AAPL")
    assert resp.status_code == 401


# ── GET /api/MarketStatus ─────────────────────────────────────────────────────

async def test_market_status_returns_200(client, auth_headers):
    with patch(_FETCH_STATUS, new_callable=AsyncMock, return_value={
        "exchange": "NASDAQ",
        "isMarketOpen": False,
    }):
        resp = await client.get("/api/MarketStatus", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["exchange"] == "NASDAQ"
    assert body["is_open"] is False


# ── GET /api/StockSearch ──────────────────────────────────────────────────────

SEARCH_RAW = [
    {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "currency": "USD"},
    {"symbol": "AAPLX", "name": "Some Fund", "exchange": "NYSE", "currency": "USD"},
    {"symbol": "TSX", "name": "Toronto Stock", "exchange": "TSX", "currency": "CAD"},
]


async def test_stock_search_filters_to_us_exchanges(client, auth_headers):
    with patch(_FETCH_SEARCH, new_callable=AsyncMock, return_value=SEARCH_RAW):
        resp = await client.get("/api/StockSearch?symbol=AAPL&page=1&page_size=10", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    symbols = [r["symbol"] for r in body["results"]]
    assert "TSX" not in symbols          # filtered out (not NYSE/NASDAQ)
    assert "AAPL" in symbols


async def test_stock_search_pagination(client, auth_headers):
    many_results = [
        {"symbol": f"SYM{i}", "name": f"Company {i}", "exchange": "NASDAQ", "currency": "USD"}
        for i in range(8)
    ]
    with patch(_FETCH_SEARCH, new_callable=AsyncMock, return_value=many_results):
        resp = await client.get("/api/StockSearch?symbol=SYM&page=1&page_size=3", headers=auth_headers)

    body = resp.json()
    assert body["total_results"] == 8
    assert len(body["results"]) == 3


# ── GET /api/MarketMovers ─────────────────────────────────────────────────────

async def test_market_movers_returns_cached_data(client, auth_headers, fake_redis):
    await fake_redis.setex("market_movers", 3600, json.dumps(MOCK_MARKET_MOVERS))

    resp = await client.get("/api/MarketMovers", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["stocks"]) == 2
    assert body["stocks"][0]["symbol"] == "AAPL"


async def test_market_movers_unavailable_returns_503(client, auth_headers):
    with patch(_GET_MOVERS, new_callable=AsyncMock, return_value=None):
        resp = await client.get("/api/MarketMovers", headers=auth_headers)
    assert resp.status_code == 503


# ── GET /api/StockSentiment ───────────────────────────────────────────────────

SENTIMENT_RAW = {
    "symbol": "AAPL",
    "strongBuy": 10,
    "buy": 25,
    "hold": 5,
    "sell": 2,
    "strongSell": 0,
    "consensus": "Buy",
}


async def test_stock_sentiment_returns_200(client, auth_headers):
    with patch(_FETCH_SENTIMENT, new_callable=AsyncMock, return_value=SENTIMENT_RAW):
        resp = await client.get("/api/StockSentiment?symbol=AAPL", headers=auth_headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert body["consensus"] == "Buy"
    assert body["buy"] == 25


async def test_stock_sentiment_requires_auth(client):
    resp = await client.get("/api/StockSentiment?symbol=AAPL")
    assert resp.status_code == 401
