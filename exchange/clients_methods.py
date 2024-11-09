from logging import exception
from typing import Any
from twelvedata.exceptions import TwelveDataError

from exchange.routers.repository.utils.client_methods_utils import *
from exchange.routers.repository.utils.utils import market_status_update
from .clients import get_td_client, get_finnhub_client, get_polygon_client


# NOTE: market_status_update(stock, db) - cannot update the price here because td.price return only the stocks price
# Twelve data fetch
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


# Twelve data fetch
def get_quote(symbols: str, db: Session) -> dict:  # passing Session argument to update market status db
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


# Twelve data fetch
def get_search_result(prompt: str):
    td = get_td_client()
    OUTPUT_SIZE = 70  # sweet spot before filtering
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


# Finnhub fetch
def get_sentiment(symbol: str) -> list:
    fn = get_finnhub_client()
    try:
        sentiment = fn.recommendation_trends(symbol)
    except exception as e:
        logger.critical(f"sentiment call is not working: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="could not get sentiment at the moment")
    return sentiment


# Polygon fetch
def apply_splits(db: Session):
    last_split_date = get_last_split_date(db)
    missing_split_time = datetime.now() - last_split_date
    missing_split_days = missing_split_time.days

    if missing_split_days > 0:
        formatted_last_split_date = last_split_date.strftime("%Y-%m-%d")
        formatted_now = datetime.now().strftime("%Y-%m-%d")
        unique_stocks_list = get_unique_stocks_list(db)
        pg = get_polygon_client()
        for stock in unique_stocks_list:
            split_history = pg.list_splits(reverse_split=True, sort='execution_date', order='desc',ticker=stock,
                                           execution_date_gt=formatted_last_split_date,
                                           execution_date_lte=formatted_now)
            if not split_history['results']:
                pass
            for split in split_history:
                stock_rows = db.query(Portfolio.symbol).filter(Portfolio.symbol == stock).all()
                for row in stock_rows:
                    row.amount = row.amount /







