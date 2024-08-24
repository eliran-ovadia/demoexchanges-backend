from exchange.app_logger import logger
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError
from exchange.models import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os


def find_user(db: Session, user_id: str = None, email: str = None) -> User:
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
    elif email:
        user = db.query(User).filter(User.email == email).first()
    else:
        raise ValueError("Either user_id or email must be provided.")

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


#### twelvedata handlers ####

def create_td_client() -> TDClient:
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        logger.critical("API key for TwelveData is not set.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="API key for TwelveData is not set")
    return TDClient(apikey=api_key)


def get_stock_price(symbol: str) -> dict:
    td = create_td_client()
    try:
        stock = td.price(symbol=symbol).as_json()
    except TwelveDataError as e:
        logger.critical(f"Price not found for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Price for symbol: {symbol} not found")
    except Exception as e:
        logger.critical(f"Failed to fetch price for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return stock


def get_quote(symbols: str) -> dict:
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
    return stocks
