from exchange.app_logger import logger
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError
from exchange.models import User, MarketStatus
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os


def find_user(db: Session, user_id: str = None, email: str = None) -> User | bool:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
    else:
        raise ValueError("Either user_id or email must be provided.")

    if not user:
        return False

    return user


def market_status_update(quotes: dict, db: Session) -> bool:
    market = db.query(MarketStatus).filter(MarketStatus.exchange_name == 'NYSE').first()
    if 'is_market_open' in quotes:
        market.is_market_open = quotes.get('is_market_open')
        db.commit()
        return quotes.get('is_market_open')
    else:
        first_stock = next(iter(quotes.values())) # get the first element in the dict
        market.is_market_open = first_stock.get('is_market_open') # apply to database
        db.commit()
        return first_stock.get('is_market_open')

#### twelvedata handlers ####

def create_td_client() -> TDClient:
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        logger.critical("API key for TwelveData is not set.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="API key for TwelveData is not set")
    return TDClient(apikey=api_key)


def get_stock_price(symbol: str, db: Session) -> float: # passing Session argument to update market status db
    td = create_td_client()
    try:
        stock = td.price(symbol=symbol).as_json()
    except TwelveDataError as e:
        logger.critical(f"Price not found for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Price for symbol: {symbol} not found")
    except Exception as e:
        logger.critical(f"Failed to fetch price for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # market_status_update(stock, db) - cannot update the price here because td.price return only the stocks price
    return float(stock.get('price'))


def get_quote(symbols: str, db: Session) -> dict: # passing Session argument to update market status db
    td = create_td_client()
    try:
        stocks = td.quote(symbol=symbols).as_json()
    except TwelveDataError as e:
        logger.critical(f"Quote not found for symbols: {symbols} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Quote for one of the symbols: {symbols} not found")
    except Exception as e:
        logger.critical(f"Failed to fetch quote for symbols: {symbols} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    market_status_update(stocks, db)

    return stocks


def get_search_result(prompt: str):
    OUTPUT_SIZE = 70 #sweet spot before filtering
    td = create_td_client()
    try:
        results = td.symbol_search(symbol=str(prompt), outputsize=OUTPUT_SIZE).as_json()
    except TwelveDataError as e:
        logger.critical(f"search result not found for the search prompt: {prompt} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"result for the search prompt: {prompt} not found")
    except Exception as e:
        logger.critical(f"Failed to find results for search prompt: {prompt} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return results