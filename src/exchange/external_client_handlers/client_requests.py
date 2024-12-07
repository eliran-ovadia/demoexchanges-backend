from logging import exception

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from twelvedata.exceptions import TwelveDataError

from .client_manager import ClientManager
from .client_response_models.market_status_handler import get_cached_market_status
from ..app_logger import logger
from ..database.db_conn import get_db


# NOTE: market_status_update(stock, db) - cannot update the price here because td.price return only the stocks price
# Twelve data fetch - stock price data
def get_stock_price(symbol: str) -> float:
    td = ClientManager.get_td_client()
    try:
        stock = td.price(symbol=symbol).as_json()
    except TwelveDataError as e:
        logger.critical(f"Price not found for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"info for symbol: {symbol} not found")
    except Exception as e:
        logger.critical(f"Failed to fetch price for symbol: {symbol} - {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    return float(stock.get('price', 0.0))


def get_quote(symbols: str, db: Session = get_db()) -> dict:
    td = ClientManager.get_td_client()
    try:
        stocks = td.quote(symbol=symbols).as_json()
    except TwelveDataError as e:
        logger.error(f"Quote not found for symbols: {symbols} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote for one of the symbols: {symbols} not found"
        )
    except Exception as e:
        logger.critical(f"Unexpected error fetching quote for symbols: {symbols} - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error occurred while fetching quotes"
        )
    return stocks


# Twelve data fetch - search result raw data
def get_search_result(prompt: str) -> list:
    td = ClientManager.get_td_client()
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

    return [result for result in results if result["exchange"] in {"NYSE", "NASDAQ"}]


# Finnhub fetch - stock sentiment raw data
def get_sentiment(symbol: str) -> dict:
    fn = ClientManager.get_finnhub_client()
    try:
        sentiment = fn.recommendation_trends(symbol)
    except exception as e:
        logger.critical(f"sentiment call is not working for symbol {symbol}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="could not get sentiment at the moment")
    if not sentiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Please request sentiment to a valid symbol")
    return sentiment[0]


def get_all_stocks(*, country='USA') -> list:
    td = ClientManager.get_td_client()
    stocks = []
    try:
        stocks = td.get_stocks_list(country=country).as_json()
    except TwelveDataError as e:
        logger.error(f"failed to fetch all {country} stocks: {str(e)}")
    except Exception as e:
        logger.critical(f"Unexpected error fetching all {country} stocks: {str(e)}")
    return stocks


def get_market_movers() -> dict:
    api_key = ClientManager.get_api_key("ALPHA_VANTAGE_API_KEY")
    url = f'https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey={api_key}'
    try:
        response = requests.get(url)
        response.raise_for_status()  # raise if not 200
        json_response = response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"alphavantage TOP_GAINERS_LOSERS call failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot access market movers at the moment"
        )
    if 'most_actively_traded' not in json_response or 'last_updated' not in json_response:
        logger.critical(
            "alphavantage TOP_GAINERS_LOSERS call is not containing *most_actively_traded* or *last_updated*")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"cannot access market movers at the moment"
        )
    useful_data = {
        'last_updated': json_response['last_updated'],
        'stocks': sorted([stock for stock in json_response['most_actively_traded'] if float(stock['price']) > 1],
                         key=lambda x: int(x['volume']),
                         reverse=True
                         )
    }
    return useful_data


def get_market_status() -> dict:
    return get_cached_market_status()
