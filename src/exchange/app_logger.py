import logging
import os

handlers = [logging.StreamHandler()]
if os.getenv("APP_ENV") != "prod":
    handlers.append(logging.FileHandler("app.log"))

logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)
