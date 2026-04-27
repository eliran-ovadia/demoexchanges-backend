import logging
import os
from logging import LogRecord


class _JsonFormatter(logging.Formatter):
    def format(self, record: LogRecord) -> str:
        import json
        return json.dumps({
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        })


def _build_logger() -> logging.Logger:
    is_prod = os.getenv("APP_ENV") == "prod"
    level = logging.INFO if is_prod else logging.DEBUG

    handler: logging.Handler
    if is_prod:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonFormatter())
    else:
        handler = logging.FileHandler("app.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logging.basicConfig(level=level, handlers=[handler])
    return logging.getLogger(__name__)


logger = _build_logger()
