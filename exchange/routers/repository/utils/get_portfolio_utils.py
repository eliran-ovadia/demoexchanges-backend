from sqlalchemy import func
from exchange.models import Portfolio
from exchange.schemas import TokenData, ShowStock
from .utils import *


def fetch_portfolio_data(db: Session, current_user: TokenData) -> dict:
    # Query the database to get the symbols, total amounts, and average prices for the current user
    result = db.query(
        Portfolio.symbol,
        func.sum(Portfolio.amount).label('total_amount'),
        func.avg(Portfolio.price).label('avg_price')
    ).filter(
        Portfolio.user_id == current_user.id
    ).group_by(
        Portfolio.symbol
    ).all()
    return {symbol: {'total_amount': total_amount, 'avg_price': avg_price} for symbol, total_amount, avg_price in
            result} if result else None


def handle_empty_portfolio(db: Session, current_user: TokenData) -> dict:
    user = find_user(db, current_user.id)
    # in the case of no stock, all values are 0
    balances_dict = {
        'Buying_power': round(user.cash, 2),
        'portfolio_value': 0.00,
        'total_return': 0.00,
        'total_return_percent': 0.00,
        'account_value': round(user.cash, 2)
    }
    return dict(balance=balances_dict, portfolio=[])


def fetch_quotes(symbols: list) -> str | dict:
    try:
        quotes_response = get_quote(",".join(symbols))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    if len(symbols) == 1:
        return {symbols[0]: quotes_response}
    return quotes_response


def process_portfolio_data(portfolio_data: dict, quotes: dict) -> list[ShowStock]:
    detailed_portfolio_data = []

    for symbol, data in portfolio_data.items():
        quote_data = quotes.get(symbol, {})
        if not quote_data:
            logger.warning(f"No quote data found for symbol: {symbol}")
            continue

        stock_data = create_stock_data(symbol, data, quote_data)
        detailed_portfolio_data.append(stock_data)

    detailed_portfolio_data.sort(key=lambda x: x.total_value, reverse=True)
    return detailed_portfolio_data


def create_stock_data(symbol: str, data: dict, quote_data: dict) -> ShowStock:
    total_amount = data['total_amount']
    last_price = round(parse_price(quote_data), 2)
    open_price, previous_close, bid_price, ask_price = extract_prices(quote_data, last_price)
    avg_price = round(data['avg_price'], 2)
    total_value = round(last_price * total_amount, 2) if last_price is not None else 0
    total_return = round((last_price - avg_price) * total_amount,
                         2) if last_price is not None and avg_price is not None else 0
    total_return_percent = round((total_return / avg_price) * 100, 2) if total_return and avg_price else 0
    year_range_low, year_range_high = extract_year_range(quote_data)

    return ShowStock(
        symbol=symbol,
        full_name=quote_data.get('name', ''),
        amount=total_amount,
        exchange=quote_data.get('exchange', ''),
        open=open_price,
        previous_close=previous_close,
        avg_price=avg_price,
        last_price=last_price,
        total_value=total_value,
        bid=bid_price,
        ask=ask_price,
        year_range_low=year_range_low,
        year_range_high=year_range_high,
        total_return=total_return,
        total_return_percent=total_return_percent
    )


def extract_prices(quote_data: dict, last_price: float) -> tuple:
    open_price = round(float(quote_data.get('open', 0.0)), 2)
    previous_close = round(float(quote_data.get('previous_close', 0.0)), 2)
    bid_price = round(float(quote_data.get('bid', last_price)), 2)
    ask_price = round(float(quote_data.get('ask', last_price)), 2)
    return open_price, previous_close, bid_price, ask_price


def extract_year_range(quote_data: dict) -> tuple:
    year_range_str = quote_data.get('fifty_two_week', {}).get('range', "")
    if year_range_str:
        year_range_low, year_range_high = map(float, year_range_str.split(" - "))
        return round(year_range_low, 2), round(year_range_high, 2)
    return None, None


def parse_price(quote_data: dict) -> float | None:
    last_price_str = quote_data.get('last', None)
    if last_price_str is None:
        last_price_str = quote_data.get('close', None)

    try:
        return float(last_price_str) if last_price_str is not None else None
    except (TypeError, ValueError):
        return None


def build_portfolio_response(db: Session, current_user: TokenData, portfolio_data: list[ShowStock]) -> dict:
    user = find_user(db, current_user.id)

    portfolio_value = round(sum([x.total_value for x in portfolio_data]), 2)
    total_return = round(sum([x.total_return for x in portfolio_data]), 2)
    total_invested = round(sum([(x.avg_price * x.amount) for x in portfolio_data]), 2)
    total_return_percent = round((total_return / total_invested) * 100, 2) if total_invested > 0 else 0

    balances_dict = {
        'Buying_power': round(user.cash, 2),
        'portfolio_value': portfolio_value,
        'total_return': total_return,
        'total_return_percent': total_return_percent,
        'account_value': round(user.cash + portfolio_value, 2)
    }
    return dict(balance=balances_dict, portfolio=portfolio_data)
