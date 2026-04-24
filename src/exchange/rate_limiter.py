import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_redis_url() -> str:
    env = os.getenv("APP_ENV", "dev")
    url_key = "REDIS_PROD_URL" if env == "prod" else "REDIS_DEV_URL"
    return os.getenv(url_key, "redis://localhost:6379")


limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_get_redis_url(),
)
