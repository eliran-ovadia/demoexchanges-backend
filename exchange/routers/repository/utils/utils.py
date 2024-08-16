from exchange.app_logger import logger
from twelvedata import TDClient
from twelvedata.exceptions import TwelveDataError
from exchange import models
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
import os

def get_user(db: Session, user_id: int) -> models.User:
    return db.query(models.User).filter(models.User.id == user_id).first()

#### twelvedata handlers ####

def create_td_client() -> TDClient:
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="API key for TwelveData is not set")
    return TDClient(apikey=api_key)

def get_stock_price(symbol: str) -> str:
    api_key = os.getenv("TWELVE_DATA_API_KEY")
    td = TDClient(apikey=api_key)
    try:
        stock = td.price(symbol=symbol).as_json()
    except TwelveDataError as e:
        logger.critical(f"Price not found for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Price for symbol: {symbol} - not found")
    except Exception as e:
        logger.critical(f"Failed to fetch price for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return stock

def get_quote(symbols: str) -> str:
    td = create_td_client()
    try:
        stock = td.quote(symbol=symbols).as_json()
    except TwelveDataError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quote for one of the symbols: {symbols} - not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return stock