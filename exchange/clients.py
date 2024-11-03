import os
from fastapi import HTTPException, status
from twelvedata import TDClient
from polygon import RESTClient
from exchange.app_logger import logger


td = None
pg = None

def get_td_client() -> TDClient:
    global td
    if td is None:
        api_key = os.getenv("TWELVE_DATA_API_KEY")
        if not api_key:
            logger.critical("API key for TwelveData is not set.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key for TwelveData is not set"
            )
        td = TDClient(apikey=os.getenv("TWELVE_DATA_API_KEY"))
        logger.info("TDClient created successfully.")
    return td

def get_polygon_client() -> RESTClient:
    global pg
    if pg is None:
        api_key = os.getenv("POLYGON_API_KEY")
        if not api_key:
            logger.critical("API key for Polygon is not set.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="API key for Polygon is not set"
            )
        pg = RESTClient(api_key=os.getenv("POLYGON_API_KEY"))
        logger.info("Polygon RESTClient created successfully.")
    return pg



