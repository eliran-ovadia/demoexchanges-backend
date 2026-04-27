"""User management: CreateUser, ResetPortfolio, DeleteUser."""
import uuid

from src.exchange.Auth.hashing import Hash
from src.exchange.database.models import User, Portfolio, History

VALID_PAYLOAD = {
    "name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "password": "Secure#Pass9",
    "password_confirm": "Secure#Pass9",
}


# ── POST /api/CreateUser ─────────────────────────────────────────────────────

async def test_create_user_returns_201(client):
    resp = await client.post("/api/users", json=VALID_PAYLOAD)
    assert resp.status_code == 201
    assert "jane@example.com" in resp.json()["message"]


async def test_create_user_starts_with_100k_cash(client, db_session):
    await client.post("/api/users", json=VALID_PAYLOAD)
    from sqlalchemy import select
    user = (await db_session.execute(
        select(User).where(User.email == VALID_PAYLOAD["email"])
    )).scalar_one_or_none()
    assert user is not None
    assert float(user.cash) == 100_000.0


async def test_create_user_duplicate_email_returns_400(client):
    await client.post("/api/users", json=VALID_PAYLOAD)
    resp = await client.post("/api/users", json=VALID_PAYLOAD)
    assert resp.status_code == 400
    assert "taken" in resp.json()["detail"].lower()


async def test_create_user_weak_password_returns_422(client):
    resp = await client.post("/api/users", json={
        **VALID_PAYLOAD,
        "password": "weakpassword",
        "password_confirm": "weakpassword",
    })
    assert resp.status_code == 422


async def test_create_user_passwords_mismatch_returns_422(client):
    resp = await client.post("/api/users", json={
        **VALID_PAYLOAD,
        "password_confirm": "Different#Pass9",
    })
    assert resp.status_code == 422


async def test_create_user_invalid_email_returns_422(client):
    resp = await client.post("/api/users", json={**VALID_PAYLOAD, "email": "bad-email"})
    assert resp.status_code == 422


# ── PATCH /api/ResetPortfolio/ ───────────────────────────────────────────────

async def test_reset_portfolio_clears_holdings_and_restores_cash(client, registered_user, auth_headers, db_session):
    from sqlalchemy import select, insert
    from src.exchange.database.models import Portfolio, History, User

    # Directly put portfolio + history rows into the DB to simulate prior trades
    user_row = (await db_session.execute(
        select(User).where(User.email == registered_user["email"])
    )).scalar_one()

    db_session.add_all([
        Portfolio(symbol="AAPL", amount=5, price=150.0, user_id=user_row.id),
        History(symbol="AAPL", price=150.0, amount=5, type="Buy",
                value=750.0, profit=0.0, user_id=user_row.id),
    ])
    user_row.cash = 99_250
    await db_session.commit()

    resp = await client.patch("/api/portfolio/reset", headers=auth_headers)
    assert resp.status_code == 200
    assert "$100,000" in resp.json()["message"]

    await db_session.refresh(user_row)
    assert float(user_row.cash) == 100_000.0

    portfolio = (await db_session.execute(
        select(Portfolio).where(Portfolio.user_id == user_row.id)
    )).scalars().all()
    assert portfolio == []


async def test_reset_portfolio_requires_auth(client):
    resp = await client.patch("/api/portfolio/reset")
    assert resp.status_code == 401


# ── DELETE /api/DeleteUser/ ──────────────────────────────────────────────────

async def test_delete_user_by_non_admin_returns_403(client, registered_user, auth_headers):
    resp = await client.delete(
        "/api/users",
        params={"email": "someone@example.com"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


async def test_delete_user_by_admin_returns_200(client, admin_headers, db_session):
    # Create a regular user to be deleted
    target = User(
        id=str(uuid.uuid4()),
        name="Target",
        last_name="User",
        email="target@example.com",
        password=Hash.bcrypt("SomePass#1"),
        is_admin=False,
        cash=100_000,
    )
    db_session.add(target)
    await db_session.commit()

    resp = await client.delete(
        "/api/users",
        params={"email": "target@example.com"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert "deleted" in resp.json()["message"].lower()


async def test_delete_nonexistent_user_returns_404(client, admin_headers):
    resp = await client.delete(
        "/api/users",
        params={"email": "nobody@example.com"},
        headers=admin_headers,
    )
    assert resp.status_code == 404


async def test_admin_cannot_delete_another_admin(client, admin_headers, db_session):
    other_admin = User(
        id=str(uuid.uuid4()),
        name="Other",
        last_name="Admin",
        email="other_admin@example.com",
        password=Hash.bcrypt("OtherAdmin#1"),
        is_admin=True,
        cash=100_000,
    )
    db_session.add(other_admin)
    await db_session.commit()

    resp = await client.delete(
        "/api/users",
        params={"email": "other_admin@example.com"},
        headers=admin_headers,
    )
    assert resp.status_code == 403
