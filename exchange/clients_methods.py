from logging import exception

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from twelvedata.exceptions import TwelveDataError

from exchange.app_logger import logger
from exchange.routers.repository.utils.utils import market_status_update
from .clients import get_td_client, get_finnhub_client


# NOTE: market_status_update(stock, db) - cannot update the price here because td.price return only the stocks price
def get_stock_price(symbol: str) -> float:
    td = get_td_client()
    try:
        stock = td.price(symbol=symbol).as_json()
    except TwelveDataError as e:
        logger.critical(f"Price not found for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Price for symbol: {symbol} not found")
    except Exception as e:
        logger.critical(f"Failed to fetch price for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return float(stock.get('price'))


def get_quote(symbols: str, db: Session) -> dict: # passing Session argument to update market status db
    td = get_td_client()
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
    td = get_td_client()
    OUTPUT_SIZE = 70 #sweet spot before filtering
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

def get_sentiment(symbol: str) -> list:
    fn = get_finnhub_client()
    try:
        sentiment = fn.recommendation_trends(symbol)
    except exception as e:
        logger.critical(f"sentiment call is not working: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="could not get sentiment at the moment")
    return sentiment