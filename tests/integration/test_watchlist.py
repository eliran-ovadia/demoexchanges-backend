"""Watchlist: add, get, delete."""
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

_FETCH_PRICE = "src.exchange.external_client_handlers.client_requests.fetch_stock_price"


async def _add(client, headers, symbol="TSLA", price=200.0):
    with patch(_FETCH_PRICE, new_callable=AsyncMock, return_value=price):
        return await client.post(
            "/api/AddToWatchlist",
            params={"symbol": symbol},
            headers=headers,
        )


# ── POST /api/AddToWatchlist ──────────────────────────────────────────────────

async def test_add_to_watchlist_returns_200(client, auth_headers):
    resp = await _add(client, auth_headers)
    assert resp.status_code == 200
    assert "added" in resp.json()["message"].lower()


async def test_add_duplicate_symbol_returns_409(client, auth_headers):
    await _add(client, auth_headers)
    resp = await _add(client, auth_headers)
    assert resp.status_code == 409


async def test_add_unknown_symbol_returns_404(client, auth_headers):
    with patch(_FETCH_PRICE, new_callable=AsyncMock,
               side_effect=HTTPException(status_code=404, detail="Symbol not found")):
        resp = await client.post(
            "/api/AddToWatchlist",
            params={"symbol": "ZZZZ"},
            headers=auth_headers,
        )
    assert resp.status_code == 404


async def test_add_watchlist_requires_auth(client):
    resp = await client.post("/api/AddToWatchlist", params={"symbol": "AAPL"})
    assert resp.status_code == 401


# ── GET /api/GetWatchlist ─────────────────────────────────────────────────────

async def test_get_watchlist_empty_returns_empty_list(client, auth_headers):
    resp = await client.get("/api/GetWatchlist", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["watchlist"] == []
    assert body["total_items"] == 0


async def test_get_watchlist_shows_added_symbol(client, auth_headers):
    await _add(client, auth_headers, symbol="TSLA")
    await _add(client, auth_headers, symbol="NVDA", price=800.0)

    resp = await client.get("/api/GetWatchlist", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_items"] == 2
    assert "TSLA" in body["watchlist"]
    assert "NVDA" in body["watchlist"]


async def test_get_watchlist_pagination(client, auth_headers):
    for symbol, price in [("AAPL", 150.0), ("TSLA", 200.0), ("NVDA", 800.0)]:
        await _add(client, auth_headers, symbol=symbol, price=price)

    resp = await client.get("/api/GetWatchlist?page=1&page_size=2", headers=auth_headers)
    body = resp.json()
    assert body["total_items"] == 3
    assert len(body["watchlist"]) == 2


# ── DELETE /api/DeleteFromWatchlist ──────────────────────────────────────────

async def test_delete_from_watchlist_returns_200(client, auth_headers):
    await _add(client, auth_headers, symbol="TSLA")
    resp = await client.delete(
        "/api/DeleteFromWatchlist",
        params={"symbol": "TSLA"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()


async def test_delete_removes_symbol_from_list(client, auth_headers):
    await _add(client, auth_headers, symbol="TSLA")
    await client.delete(
        "/api/DeleteFromWatchlist",
        params={"symbol": "TSLA"},
        headers=auth_headers,
    )
    resp = await client.get("/api/GetWatchlist", headers=auth_headers)
    assert "TSLA" not in resp.json()["watchlist"]


async def test_delete_symbol_not_in_watchlist_returns_404(client, auth_headers):
    resp = await client.delete(
        "/api/DeleteFromWatchlist",
        params={"symbol": "AAPL"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_watchlist_is_user_scoped(client, registered_user, auth_headers, db_session):
    """Symbols added by user A must not appear for user B."""
    import uuid
    from src.exchange.Auth.hashing import Hash
    from src.exchange.database.models import User

    user_b = User(
        id=str(uuid.uuid4()),
        name="User",
        last_name="B",
        email="userb@example.com",
        password=Hash.bcrypt("UserB#Pass9"),
        is_admin=False,
        cash=100_000,
    )
    db_session.add(user_b)
    await db_session.commit()

    resp_b_token = await client.post(
        "/Token",
        data={"username": "userb@example.com", "password": "UserB#Pass9"},
    )
    headers_b = {"Authorization": f"Bearer {resp_b_token.json()['access_token']}"}

    await _add(client, auth_headers, symbol="TSLA")

    resp = await client.get("/api/GetWatchlist", headers=headers_b)
    assert "TSLA" not in resp.json()["watchlist"]
