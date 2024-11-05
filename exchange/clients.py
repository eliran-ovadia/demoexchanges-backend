from twelvedata import TDClient
from polygon import RESTClient
from finnhub import Client as FinnhubClient
from exchange.app_logger import logger
from .routers.repository.utils.utils import get_api_key


td = None
pg = None
fh = None

def get_td_client() -> TDClient:
    global td
    if td is None:
        td_api_key = get_api_key("TWELVE_DATA_API_KEY")
        td = TDClient(apikey=td_api_key)
        logger.info("Twelve data client created successfully.")
    return td


def get_polygon_client() -> RESTClient:
    global pg
    if pg is None:
        polygon_api_key = get_api_key("POLYGON_API_KEY")
        pg = RESTClient(api_key=polygon_api_key)
        logger.info("Polygon client created successfully.")
    return pg


def get_finnhub_client() -> FinnhubClient:
    global fh
    if fh is None:
        finnhub_api_key = get_api_key("FINNHUB_API_KEY")
        fh = FinnhubClient(api_key=finnhub_api_key)
        logger.info("finnhub client created successfully.")
    return fh