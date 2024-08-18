from exchange.routers.repository.utils.get_portfolio_utils import *
from exchange.routers.repository.utils.order_utils import *
from exchange.app_logger import logger


def order(request: schemas.Order, db: Session, current_user: schemas.TokenData) -> schemas.AfterOrder:
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot buy/sell more than one stock at once")
    price = float(get_stock_price(symbol)['price'])
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
    quotes = fetch_quotes(symbols)
    detailed_portfolio_data = process_portfolio_data(portfolio_data, quotes)

    return build_portfolio_response(db, current_user, detailed_portfolio_data)

def get_history(db: Session, current_user: schemas.TokenData) -> list:
    history = db.query(models.History).filter(models.History.user_id == current_user.id).order_by(models.History.time_stamp.desc()).all()
    if not history:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"History table is empty")
    return history