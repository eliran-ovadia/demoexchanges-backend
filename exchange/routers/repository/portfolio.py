from sqlalchemy.orm import Session
from sqlalchemy import func
from ... import models, schemas
from fastapi import HTTPException, status
from twelvedata import TDClient
from datetime import datetime
import os
from dotenv import load_dotenv
import time

def get_all(db: Session):
    portfolios = db.query(models.Portfolio).all() #for some reson i cannot just return the db object
    if not portfolios:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"Portfolios table is empty")
    return portfolios

def order(request: schemas.Order, db: Session, current_user: schemas.TokenData):
    user_id = current_user.id
    symbol = request.symbol.upper()
    if ',' in symbol:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = "cannot buy/sell more than one stock at once")
    amount = request.amount
    price = float(get_stock_price(symbol)['price'])
    timestamp = datetime.now()
    value = price * amount
    user = db.query(models.User).filter(models.User.id == user_id).first()
    availbale_cash = user.cash
    sell_profit = 0
    
    if amount == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount cannot be 0")  

    #Sell order
    if amount < 0:
        type = "Sell"
        value *= -1
        amount *= -1
        #calculated total stocks amount for symbol
        user_total_amount_of_stcok = db.query(func.sum(models.Portfolio.amount)).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
            ).scalar()
        
        if user_total_amount_of_stcok is None or user_total_amount_of_stcok < amount:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stocks for selling")
        
        portfolio_entries = db.query(models.Portfolio).filter(
            models.Portfolio.user_id == user_id,
            models.Portfolio.symbol == symbol
        ).order_by(models.Portfolio.time_stamp.asc()).all()
        
        amount_copy = amount
        for entry in portfolio_entries:
            if amount_copy <= 0:
                break
            if entry.amount <= amount_copy:
                sell_profit += (price - entry.price) * entry.amount
                amount_copy -= entry.amount
                db.delete(entry)
                db.commit()
            else:
                sell_profit += (price - entry.price) * amount_copy
                entry.amount -= amount_copy
                amount_copy = 0
        user.cash += value
    else: #Buy order
        type = "Buy"
        
        if user.cash < value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient cash for buying")

        new_portfolio = models.Portfolio(
            symbol = symbol, amount = amount, time_stamp = timestamp,price = price, user_id = user_id
        )
        db.add(new_portfolio)
        user.cash -= value


    new_history = models.History(
        symbol=symbol, price=price, amount=amount, type=type, profit = sell_profit,
        value=value, time_stamp=timestamp, user_id=user_id)
    
    db.add(new_history)
    db.commit()
    return schemas.AfterOrder(symbol=symbol, price=price, amount=amount, type=type, value=value, profit=sell_profit)
def getPortfolio(db: Session, current_user: schemas.TokenData):
    # Create a TD client to get quotes
    td = TDClient(apikey="375f5ab7748a4ddb807d4c810bae5cf2")
    
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
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio is empty")
    # Convert the result into a dictionary
    summary = {symbol: {'total_amount': total_amount, 'avg_price': avg_price} for symbol, total_amount, avg_price in result}

    # Get all the symbols
    symbols = list(summary.keys())
    
    # Fetch the quotes for all the symbols
    try:
        quotes_response = td.quote(symbol=",".join(symbols)).as_json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    if len(symbols) == 1:
        symbol = symbols[0]
        quotes = {symbol: quotes_response}
    else:
        quotes = quotes_response
    # Combine the quote data with the total amounts and average prices
    portfolio_data = []
    for symbol in symbols:
        quote_data = quotes.get(symbol, {})
        last_price_str = quote_data.get('last', None)
        if last_price_str is None:
            last_price_str = quote_data.get('close', None)
        
        try:
            last_price = float(last_price_str) if last_price_str is not None else None
        except (TypeError, ValueError):
            last_price = None
        
        total_amount = summary[symbol]['total_amount']
        avg_price = summary[symbol]['avg_price']
        total_value = last_price * total_amount if last_price is not None else None
        total_return = (last_price - avg_price) * total_amount if last_price is not None and avg_price is not None else None
        range = quote_data['fifty_two_week']['range'] if 'fifty_two_week' in quote_data else None
        total_return_percent = total_return / avg_price if total_return is not None and avg_price is not None else None
        show_portfolio_data = {
            'symbol': symbol,
            'full_name': quote_data.get('name', None),
            'amount': total_amount,
            'exchange': quote_data.get('exchange', None),
            'open': quote_data.get('open', None),
            'previous_close': quote_data.get('previous_close', None),
            'avg_price': avg_price,
            'last_price': last_price,
            'total_value': total_value,
            'bid': quote_data.get('bid', None),
            'ask': quote_data.get('ask', None),
            'year_range': range,
            'total_return': total_return,
            'total_return_percent': total_return_percent
        }
        portfolio_data.append(show_portfolio_data)

    portfolio_data.sort(key=lambda x: x['total_value'], reverse=True)
    
    #add balances values
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    
    portfolio_value = sum([x['total_value'] for x in portfolio_data]) if portfolio_data else 0
    total_return = sum([x['total_return'] for x in portfolio_data]) if portfolio_data else 0
    total_invested = sum([(x['avg_price'] * x['amount']) for x in portfolio_data]) if portfolio_data else 0
    total_return_percent = (total_return / total_invested) if total_invested > 0 else 0
    
    balances_dict = {
        'Buying_power': user.cash,
        'portfolio_value': portfolio_value,
        'total_return': total_return,
        'total_return_percent': total_return_percent,
        'account_value': user.cash + portfolio_value
        }
    
    get_portfolio = dict(balance = balances_dict, portfolio = portfolio_data)
    
    return get_portfolio

def event_stream(db: Session, current_user: schemas.User, duration: int = 100, interval: int = 5):
    flag = 0
    while flag < duration:
        try:
            portfolio_data = getPortfolio(db, current_user)
            yield f"data: {portfolio_data}\n\n"
        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"
        
        time.sleep(interval)
        flag += interval

    # Send a final event indicating the end of the stream
    yield f"data: {{'message': 'Stream ended after {duration} seconds'}}\n\n"

def getHistory(db: Session, current_user: schemas.TokenData):
    history = db.query(models.History).filter(models.History.user_id == current_user.id).order_by(models.History.time_stamp.desc()).all()
    if not history:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"History table is empty")
    return history

#TwelveData handlers-------
def get_stock_price(symbol: str):
    load_dotenv()
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    td = TDClient(apikey = api_key)
    try:
        stock = td.price(symbol = symbol).as_json()
    except:
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail = f"price for symbol: {symbol} - not found")
    return stock

def get_quote(symbols: str):
    load_dotenv()
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    td = TDClient(apikey = api_key)
    try:
        stock = td.quote(symbol=symbols).as_json()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"quote for one of the symbols: {symbols} - not found")
    return stock