from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.order_utils import *
from exchange.models import History as modelHistory
from exchange.models import MarketStatus
from exchange.schemas import History as schemaHistory
from exchange.schemas import RawQuote
from exchange.routers.repository.utils.get_parsed_portfolio_utils import process_single_quote
from sqlalchemy.orm import Session


def order(request: schemas.Order, db: Session, current_user: schemas.TokenData) -> schemas.AfterOrder:
    symbol = request.symbol.upper()
    if ',' or ';' or '--' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Cannot buy/sell more than one stock at once")
    price = float(get_stock_price(symbol, db)['price'])
    print(price)
    value = price * request.amount
    if request.amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be 0")
    if request.type == 'Buy':
        return buy_handler(request, db, current_user, symbol, price, value)
    else:
        return sell_handler(request, db, current_user, symbol, price, value)


def get_portfolio(db: Session, current_user: schemas.TokenData) -> dict:
    portfolio_data = fetch_portfolio_data(db, current_user)

    if not portfolio_data:
        return handle_empty_portfolio(db, current_user)  # If no stocks, return balance with zeroes

    symbols = list(portfolio_data.keys())
    quotes = fetch_quotes(symbols, db)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return build_portfolio_response(db, current_user, detailed_portfolio_data)


def get_history(db: Session, current_user: schemas.TokenData) -> list[schemaHistory]:
    history_array = db.query(modelHistory).filter(modelHistory.user_id == current_user.id).order_by(
        modelHistory.time_stamp.desc()).all()
    if not history_array:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No order history")

    history_to_return = []
    for history in history_array:
        history_schema = schemaHistory(
            symbol = history.symbol,
            price = round(history.price, 2),
            amount = history.amount,
            type = history.type,
            value = round(history.value, 2),
            profit = round(history.profit, 2),
            time = history.time_stamp
        )
        history_to_return.append(history_schema)

    return history_to_return


def get_parsed_quote(request: str, db: Session) -> RawQuote | dict:
    raw_quotes = get_quote(request, db)

    parsed_quotes_to_return = {}
    if 'symbol' in raw_quotes:  # Check for single dictionary
        parsed_quotes_to_return = process_single_quote(raw_quotes).model_dump()
    else:
        for symbol, raw_quote in raw_quotes.items():
            parsed_quote = process_single_quote(raw_quote)
            parsed_quotes_to_return[symbol] = parsed_quote

    return parsed_quotes_to_return


def fetch_market_status(db: Session) -> MarketStatus:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if not market:
        raise HTTPException(status_code=404, detail="Market status not found")
    return market
