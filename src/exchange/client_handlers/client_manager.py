import os
import threading

from fastapi import HTTPException, status
from finnhub import Client as FinnhubClient
from polygon import RESTClient
from twelvedata import TDClient

from src.exchange.app_logger import logger


# ClientManager is using the @classMethod decorator to act as a singleton
# Those will be the only instances of client objects
class ClientManager:
    _td_instance = None
    _pg_instance = None
    _fh_instance = None
    _lock = threading.Lock()

    @classmethod
    def get_td_client(cls) -> TDClient:
        if cls._td_instance is None:
            with cls._lock:
                if cls._td_instance is None:
                    td_api_key = cls.get_api_key("TWELVE_DATA_API_KEY")
                    cls._td_instance = TDClient(apikey=td_api_key)
                    logger.info("Twelve data client created successfully.")
        return cls._td_instance

    @classmethod
    def get_polygon_client(cls) -> RESTClient:
        if cls._pg_instance is None:
            with cls._lock:
                if cls._pg_instance is None:
                    polygon_api_key = cls.get_api_key("POLYGON_API_KEY")
                    cls._pg_instance = RESTClient(api_key=polygon_api_key)
                    logger.info("Polygon client created successfully.")
        return cls._pg_instance

    @classmethod
    def get_finnhub_client(cls) -> FinnhubClient:
        if cls._fh_instance is None:
            with cls._lock:
                if cls._fh_instance is None:
                    finnhub_api_key = cls.get_api_key("FINNHUB_API_KEY")
                    cls._fh_instance = FinnhubClient(api_key=finnhub_api_key)
                    logger.info("Finnhub client created successfully.")
        return cls._fh_instance

    @classmethod
    def reset_clients(cls):
        with cls._lock:
            cls._td_instance = None
            cls._pg_instance = None
            cls._fh_instance = None
            logger.info("All clients reset to None.")

    @classmethod
    def get_api_key(cls, client: str) -> str:
        api_key = os.getenv(client)
        if not api_key:
            logger.error(f"API key for {client} is not set.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"API key for {client} is missing"
            )

        return api_key
