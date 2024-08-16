from exchange.app_logger import logger
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from exchange import models, schemas
from .utils import *

def fetch_portfolio_data(db: Session, current_user: schemas.TokenData) -> dict:
    # Query the database to get the symbols, total amounts, and average prices for the current user
    result = db.query(
        models.Portfolio.symbol,
        func.sum(models.Portfolio.amount).label('total_amount'),
        func.avg(models.Portfolio.price).label('avg_price')
    ).filter(
        models.Portfolio.user_id == current_user.id
    ).group_by(
        models.Portfolio.symbol
    ).all()
    return {symbol: {'total_amount': total_amount, 'avg_price': avg_price} for symbol, total_amount, avg_price in result} if result else None

def handle_empty_portfolio(db: Session, current_user: schemas.TokenData) -> dict:
    user = get_user(db, current_user.id)

    balances_dict = {
        'Buying_power': user.cash,
        'portfolio_value': 0,  # No stocks, so portfolio value is 0
        'total_return': 0,      # No stocks, so total return is 0
        'total_return_percent': 0,  # No stocks, so total return percent is 0
        'account_value': user.cash
    }
    return dict(balance=balances_dict, portfolio=[])

def fetch_quotes(symbols: list) -> dict:
    try:
        quotes_response = get_quote(",".join(symbols))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    if len(symbols) == 1:
        return {symbols[0]: quotes_response}
    return quotes_response

def process_portfolio_data(portfolio_data: dict, quotes: dict) -> list:
    detailed_portfolio_data = []

    for symbol, data in portfolio_data.items():
        quote_data = quotes.get(symbol, {})
        if not quote_data:
            logger.warning(f"No quote data found for symbol: {symbol}")
            continue
        last_price = parse_price(quote_data)

        total_amount = data['total_amount']
        avg_price = data['avg_price']
        total_value = last_price * total_amount if last_price is not None else 0
        total_return = (last_price - avg_price) * total_amount if last_price is not None and avg_price is not None else 0
        range = quote_data.get('fifty_two_week', {}).get('range', None)
        total_return_percent = (total_return / avg_price) if total_return and avg_price else 0

        detailed_portfolio_data.append({
            'symbol': symbol,
            'full_name': quote_data.get('name', None),
            'amount': total_amount,
            'exchange': quote_data.get('exchange', None),
            'open': quote_data.get('open', None),
            'previous_close': quote_data.get('previous_close', None),
            'avg_price': avg_price,
            'last_price': last_price,
            'total_value': total_value,
            'bid': quote_data.get('bid', last_price),
            'ask': quote_data.get('ask', last_price),
            'year_range': range,
            'total_return': total_return,
            'total_return_percent': total_return_percent
        })

    detailed_portfolio_data.sort(key=lambda x: x['total_value'], reverse=True)
    return detailed_portfolio_data

def parse_price(quote_data: dict) -> float:
    last_price_str = quote_data.get('last', None)
    if last_price_str is None:
        last_price_str = quote_data.get('close', None)

    try:
        return float(last_price_str) if last_price_str is not None else None
    except (TypeError, ValueError):
        return None

def build_portfolio_response(db: Session, current_user: schemas.TokenData, portfolio_data: list) -> dict:
    user = get_user(db, current_user.id)

    portfolio_value = sum([x['total_value'] for x in portfolio_data])
    total_return = sum([x['total_return'] for x in portfolio_data])
    total_invested = sum([(x['avg_price'] * x['amount']) for x in portfolio_data])
    total_return_percent = (total_return / total_invested) if total_invested > 0 else 0

    balances_dict = {
        'Buying_power': user.cash,
        'portfolio_value': portfolio_value,
        'total_return': total_return,
        'total_return_percent': total_return_percent,
        'account_value': user.cash + portfolio_value
    }
    return dict(balance=balances_dict, portfolio=portfolio_data)