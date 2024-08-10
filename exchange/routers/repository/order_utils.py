from datetime import datetime
from sqlalchemy import func
from utils import *

def validate_symbol(symbol: str) -> str:
    symbol = symbol.upper()
    logger.debug(f"Validating symbol: {symbol}")
    if ',' in symbol:
        logger.error(f"Multiple symbols provided: {symbol}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot buy/sell more than one stock at once")
    if len(symbol) > 4:
        logger.error(f"Symbol {symbol} is longer than 4 characters")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock symbol cannot be longer than 4 characters")
    return symbol

def handle_buy_order(user: models.User, symbol: str, amount: int, price: str, timestamp: datetime, db: Session):
    value = price * amount
    logger.info(f"Handling buy order: {amount} {type(amount)} of {symbol} at {price} {type(price)} with the value {value} {type(value)} for user {user.id} with cash of {user.cash} {type(user.cash)}")
    
    if user.cash < value:
        logger.error(f"Insufficient cash for user {user.id}. Available: {user.cash}, Required: {value}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")
    
    new_portfolio = models.Portfolio(
        symbol=symbol, amount=amount, time_stamp=timestamp, price=price, user_id=user.id
    )
    db.add(new_portfolio)
    user.cash -= value
    logger.info(f"Buy order completed: {amount} of {symbol} at {price} for user {user.id}")

def handle_sell_order(user: models.User, symbol: str, amount: int, price: float, timestamp: datetime, db: Session):
    value = price * amount
    logger.info(f"Handling sell order: {amount} of {symbol} at {price} for user {user.id}")
    
    total_stock = get_user_total_stock(db, user.id, symbol)
    
    if total_stock is None or total_stock < amount:
        logger.error(f"Insufficient stocks for user {user.id} to sell. Available: {total_stock}, Attempted: {amount}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stocks for selling")
    
    sell_profit = calculate_sell_profit(db, user.id, symbol, amount, price)
    user.cash += value
    user.sell_profit = sell_profit  # Temporarily store profit for history recording
    
    logger.info(f"Sell order completed: {amount} of {symbol} at {price} for user {user.id} with profit {sell_profit}")

def get_user_total_stock(db: Session, user_id: int, symbol: str) -> int:
    total_stock = db.query(func.sum(models.Portfolio.amount)).filter(
        models.Portfolio.user_id == user_id, models.Portfolio.symbol == symbol
    ).scalar()
    logger.debug(f"Total stock for user {user_id}: {total_stock} of {symbol}")
    return total_stock

def calculate_sell_profit(db: Session, user_id: int, symbol: str, amount: int, price: float) -> float:
    sell_profit = 0
    logger.info(f"Calculating sell profit for user {user_id}: {amount} of {symbol} at {price}")
    
    portfolio_entries = db.query(models.Portfolio).filter(
        models.Portfolio.user_id == user_id, models.Portfolio.symbol == symbol
    ).order_by(models.Portfolio.time_stamp.asc()).all()
    
    amount_copy = amount
    for entry in portfolio_entries:
        if amount_copy <= 0:
            break
        if entry.amount <= amount_copy:
            sell_profit += (price - entry.price) * entry.amount
            amount_copy -= entry.amount
            db.delete(entry)
            logger.debug(f"Deleted portfolio entry for user {user_id}: {entry.amount} of {symbol} at {entry.price}")
        else:
            sell_profit += (price - entry.price) * amount_copy
            entry.amount -= amount_copy
            amount_copy = 0
            logger.debug(f"Updated portfolio entry for user {user_id}: remaining {entry.amount} of {symbol} at {entry.price}")
    
    logger.info(f"Total sell profit for user {user_id}: {sell_profit}")
    return sell_profit

def record_history(db: Session, user_id: int, symbol: str, price: float, amount: int, order_type: str, timestamp: datetime):
    profit = 0 if order_type == 'Buy' else user.sell_profit
    logger.info(f"Recording history for user {user_id}: {order_type} {amount} of {symbol} at {price}, profit: {profit}")
    
    new_history = models.History(
        symbol=symbol, price=price, amount=amount, type=order_type, profit=profit,
        value=price * amount, time_stamp=timestamp, user_id=user_id
    )
    db.add(new_history)
    logger.debug(f"History recorded for user {user_id}: {order_type} {amount} of {symbol} at {price}")