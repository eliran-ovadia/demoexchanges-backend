"""Portfolio: buy, sell, get portfolio, get history."""
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import make_quote

AAPL_PRICE = 150.0
AAPL_QUOTE = make_quote("AAPL", AAPL_PRICE)

_FETCH_PRICE = "src.exchange.routers.repository.portfolio_repo.fetch_stock_price"
_FETCH_QUOTE = "src.exchange.routers.repository.utils.get_portfolio_utils.fetch_quote"


# ── GET /api/GetPortfolio — empty ────────────────────────────────────────────

async def test_get_portfolio_empty_returns_100k_balance(client, auth_headers):
    resp = await client.get("/api/GetPortfolio", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["balance"]["buying_power"] == 100_000.0
    assert body["balance"]["total_stocks"] == 0
    assert body["portfolio"] == []


# ── POST /api/Order — buy ────────────────────────────────────────────────────

async def test_buy_stock_returns_201_with_order_details(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        resp = await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 2, "type": "buy"},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["symbol"] == "AAPL"
    assert body["amount"] == 2
    assert body["price"] == AAPL_PRICE
    assert body["value"] == AAPL_PRICE * 2
    assert body["type"] == "Buy"


async def test_buy_deducts_cash_from_balance(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 2, "type": "buy"},
            headers=auth_headers,
        )

    with patch(_FETCH_QUOTE, new_callable=AsyncMock, return_value={"AAPL": AAPL_QUOTE}):
        resp = await client.get("/api/GetPortfolio", headers=auth_headers)

    assert resp.status_code == 200
    balance = resp.json()["balance"]
    assert balance["buying_power"] == round(100_000.0 - AAPL_PRICE * 2, 2)
    assert balance["total_stocks"] == 1


async def test_buy_insufficient_funds_returns_406(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=200_000.0):
        resp = await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 1, "type": "buy"},
            headers=auth_headers,
        )
    assert resp.status_code == 406
    assert "insufficient" in resp.json()["detail"].lower()


async def test_buy_invalid_symbol_with_comma_returns_400(client, auth_headers):
    resp = await client.post(
        "/api/Order",
        json={"symbol": "AAPL,NVDA", "amount": 1, "type": "buy"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ── POST /api/Order — sell ───────────────────────────────────────────────────

async def _buy_aapl(client, auth_headers, amount=5):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": amount, "type": "buy"},
            headers=auth_headers,
        )


async def test_sell_stock_returns_201(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=5)

    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        resp = await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 2, "type": "sell"},
            headers=auth_headers,
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["type"] == "Sell"
    assert body["amount"] == 2


async def test_sell_adds_cash_back(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=5)
    cash_after_buy = 100_000.0 - AAPL_PRICE * 5

    sell_price = 160.0
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=sell_price):
        await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 3, "type": "sell"},
            headers=auth_headers,
        )

    with patch(_FETCH_QUOTE, new_callable=AsyncMock, return_value={"AAPL": make_quote("AAPL", sell_price)}):
        resp = await client.get("/api/GetPortfolio", headers=auth_headers)

    expected_cash = round(cash_after_buy + sell_price * 3, 2)
    assert resp.json()["balance"]["buying_power"] == expected_cash


async def test_sell_more_than_owned_returns_400(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=3)

    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        resp = await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 10, "type": "sell"},
            headers=auth_headers,
        )
    assert resp.status_code == 400
    assert "maximum" in resp.json()["detail"].lower()


async def test_sell_stock_not_owned_returns_400(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        resp = await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 1, "type": "sell"},
            headers=auth_headers,
        )
    assert resp.status_code == 400


# ── GET /api/GetPortfolio — with holdings ───────────────────────────────────

async def test_get_portfolio_shows_holdings_after_buy(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=5)

    with patch(_FETCH_QUOTE, new_callable=AsyncMock, return_value={"AAPL": AAPL_QUOTE}):
        resp = await client.get("/api/GetPortfolio", headers=auth_headers)

    assert resp.status_code == 200
    portfolio = resp.json()["portfolio"]
    assert len(portfolio) == 1
    assert portfolio[0]["symbol"] == "AAPL"
    assert portfolio[0]["amount"] == 5


async def test_get_portfolio_sell_all_clears_holding(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=2)

    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        await client.post(
            "/api/Order",
            json={"symbol": "AAPL", "amount": 2, "type": "sell"},
            headers=auth_headers,
        )

    resp = await client.get("/api/GetPortfolio", headers=auth_headers)
    assert resp.json()["portfolio"] == []
    assert resp.json()["balance"]["total_stocks"] == 0


# ── GET /api/GetHistory ──────────────────────────────────────────────────────

async def test_get_history_no_trades_returns_404(client, auth_headers):
    resp = await client.get("/api/GetHistory", headers=auth_headers)
    assert resp.status_code == 404


async def test_get_history_after_buy_returns_record(client, auth_headers):
    await _buy_aapl(client, auth_headers, amount=3)

    resp = await client.get("/api/GetHistory", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_items"] == 1
    assert body["history"][0]["symbol"] == "AAPL"
    assert body["history"][0]["type"] == "Buy"


async def test_get_history_pagination(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=AAPL_PRICE):
        for _ in range(3):
            await client.post(
                "/api/Order",
                json={"symbol": "AAPL", "amount": 1, "type": "buy"},
                headers=auth_headers,
            )

    resp = await client.get("/api/GetHistory?page=1&page_size=2", headers=auth_headers)
    body = resp.json()
    assert body["total_items"] == 3
    assert len(body["history"]) == 2
