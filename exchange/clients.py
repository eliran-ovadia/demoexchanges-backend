from twelvedata import TDClient
from polygon import RESTClient
from exchange.app_logger import logger
from .routers.repository.utils.utils import get_api_key


td = None
pg = None

def get_td_client() -> TDClient:
    global td
    if td is None:
        td_api_key = get_api_key("TWELVE_DATA_API_KEY")
        td = TDClient(apikey=td_api_key)
        logger.info("TDClient created successfully.")
    return td

def get_polygon_client() -> RESTClient:
    global pg
    if pg is None:
        polygon_api_key = get_api_key("POLYGON_API_KEY")
        pg = RESTClient(api_key=polygon_api_key)
        logger.info("Polygon RESTClient created successfully.")
    return pg



