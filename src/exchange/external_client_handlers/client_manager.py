import asyncio
import os
import threading

import httpx
from fastapi import HTTPException, status

from src.exchange.app_logger import logger

_CONNECT_TIMEOUT = 3   # seconds to establish TCP connection
_READ_TIMEOUT = 10     # seconds to wait for FMP response
_MAX_RETRIES = 2       # retries on 5xx / connection errors
_RETRY_BACKOFF = 0.3   # base backoff in seconds (doubles each retry)


class FMPClient:
    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=_CONNECT_TIMEOUT, read=_READ_TIMEOUT),
        )

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        all_params = dict(params or {})
        all_params["apikey"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"

        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = await self._client.get(url, params=all_params)
                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as e:
                code = e.response.status_code
                if code < 500 or attempt == _MAX_RETRIES:
                    logger.error(f"FMP {endpoint} → {code}: {e.response.text[:200]}")
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                                        detail="Market data unavailable")
                logger.warning(f"FMP {endpoint} → {code}, retrying ({attempt + 1}/{_MAX_RETRIES})")

            except httpx.ConnectError as e:
                if attempt == _MAX_RETRIES:
                    logger.critical(f"FMP connection failed for {endpoint}: {e}")
                    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                        detail="Market data service unreachable")
                logger.warning(f"FMP connection error, retrying ({attempt + 1}/{_MAX_RETRIES})")

            except httpx.TimeoutException:
                if attempt == _MAX_RETRIES:
                    logger.critical(f"FMP timed out for {endpoint}")
                    raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                                        detail="Market data request timed out")
                logger.warning(f"FMP timeout, retrying ({attempt + 1}/{_MAX_RETRIES})")

            await asyncio.sleep(_RETRY_BACKOFF * 2 ** attempt)  # 0.3s, then 0.6s

    async def close(self):
        await self._client.aclose()


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
    async def reset_clients(cls):
        with cls._lock:
            if cls._client:
                await cls._client.close()
            cls._client = None
            logger.info("FMP client reset.")
