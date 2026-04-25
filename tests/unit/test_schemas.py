import pytest
from pydantic import ValidationError

from src.exchange.schemas.schemas import CreateUser, Order, Pagination, Stock

VALID_USER = {
    "name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "password": "Secure#Pass9",
    "password_confirm": "Secure#Pass9",
}


# ── CreateUser ──────────────────────────────────────────────────────────────

def test_create_user_valid():
    user = CreateUser(**VALID_USER)
    assert user.email == "john@example.com"
    assert user.name == "John"


def test_create_user_passwords_mismatch():
    with pytest.raises(ValidationError, match="password_confirm must match password"):
        CreateUser(**{**VALID_USER, "password_confirm": "Different#1"})


def test_create_user_weak_password_no_uppercase():
    with pytest.raises(ValidationError, match="uppercase"):
        CreateUser(**{**VALID_USER, "password": "secure#pass9", "password_confirm": "secure#pass9"})


def test_create_user_weak_password_no_digit():
    with pytest.raises(ValidationError, match="digit"):
        CreateUser(**{**VALID_USER, "password": "Secure#Pass!", "password_confirm": "Secure#Pass!"})


def test_create_user_weak_password_no_special_char():
    with pytest.raises(ValidationError, match="special character"):
        CreateUser(**{**VALID_USER, "password": "SecurePass99", "password_confirm": "SecurePass99"})


def test_create_user_weak_password_too_short():
    with pytest.raises(ValidationError, match="8"):
        CreateUser(**{**VALID_USER, "password": "Sh#1", "password_confirm": "Sh#1"})


def test_create_user_password_contains_first_name():
    with pytest.raises(ValidationError, match="first name"):
        CreateUser(**{**VALID_USER, "password": "John#Secure9", "password_confirm": "John#Secure9"})


def test_create_user_password_contains_email_local():
    with pytest.raises(ValidationError, match="email"):
        CreateUser(**{
            **VALID_USER,
            "email": "myemail@example.com",
            "password": "Myemail#99Secure",
            "password_confirm": "Myemail#99Secure",
        })


def test_create_user_password_repeated_chars():
    with pytest.raises(ValidationError, match="repeat"):
        CreateUser(**{**VALID_USER, "password": "Saaa#Pass9", "password_confirm": "Saaa#Pass9"})


def test_create_user_name_invalid_chars():
    with pytest.raises(ValidationError, match="invalid characters"):
        CreateUser(**{**VALID_USER, "name": "J0hn!"})


def test_create_user_invalid_email():
    with pytest.raises(ValidationError):
        CreateUser(**{**VALID_USER, "email": "not-an-email"})


def test_create_user_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        CreateUser(**{**VALID_USER, "extra_field": "should_fail"})


# ── Order ───────────────────────────────────────────────────────────────────

def test_order_buy_capitalizes_type():
    order = Order(symbol="AAPL", amount=5, type="buy")
    assert order.type == "Buy"


def test_order_sell_capitalizes_type():
    order = Order(symbol="AAPL", amount=5, type="sell")
    assert order.type == "Sell"


def test_order_invalid_type():
    with pytest.raises(ValidationError, match="'buy' or 'sell'"):
        Order(symbol="AAPL", amount=5, type="hold")


def test_order_zero_amount_rejected():
    with pytest.raises(ValidationError):
        Order(symbol="AAPL", amount=0, type="buy")


def test_order_negative_amount_rejected():
    with pytest.raises(ValidationError):
        Order(symbol="AAPL", amount=-1, type="buy")


# ── Stock ───────────────────────────────────────────────────────────────────

def test_stock_symbol_uppercased():
    stock = Stock(symbol="aapl")
    assert stock.symbol == "AAPL"


def test_stock_symbol_too_long():
    with pytest.raises(ValidationError, match="1–5"):
        Stock(symbol="TOOLONG")


def test_stock_symbol_non_alpha():
    with pytest.raises(ValidationError, match="1–5"):
        Stock(symbol="AA1")


# ── Pagination ──────────────────────────────────────────────────────────────

def test_pagination_defaults():
    p = Pagination()
    assert p.page == 1
    assert p.page_size == 10


def test_pagination_page_size_max():
    with pytest.raises(ValidationError):
        Pagination(page=1, page_size=101)


def test_pagination_page_min():
    with pytest.raises(ValidationError):
        Pagination(page=0, page_size=10)
