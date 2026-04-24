import os
import threading

import requests
from fastapi import HTTPException, status

from src.exchange.app_logger import logger


class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._session = requests.Session()

    def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        all_params = dict(params or {})
        all_params["apikey"] = self.api_key
        try:
            response = self._session.get(f"{self.BASE_URL}/{endpoint}", params=all_params)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            logger.error(f"FMP {endpoint} returned {e.response.status_code}: {e.response.text[:200]}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Market data unavailable"
            )
        except requests.RequestException as e:
            logger.critical(f"FMP request failed for {endpoint}: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Market data service unreachable"
            )

    def close(self):
        self._session.close()


class ClientManager:
    _client: FMPClient | None = None
    _lock = threading.Lock()

    @classmethod
    def get_client(cls) -> FMPClient:
        if cls._client is None:
            with cls._lock:
                if cls._client is None:
                    api_key = os.getenv("FMP_API_KEY")
                    if not api_key:
                        logger.error("FMP_API_KEY is not set")
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="API key missing"
                        )
                    cls._client = FMPClient(api_key)
                    logger.info("FMP client created successfully.")
        return cls._client

    @classmethod
    def reset_clients(cls):
        with cls._lock:
            if cls._client:
                cls._client.close()
            cls._client = None
            logger.info("FMP client reset.")
