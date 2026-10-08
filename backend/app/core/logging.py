"""
Structured logging configuration.
Uses Python standard logging with JSON formatting for production.
"""

import logging
import sys
from app.core.config import settings


def configure_logging() -> None:
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    handler = logging.StreamHandler(sys.stdout)

    if settings.DEBUG:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
    else:
        # Production: structured JSON logging
        try:
            import json

            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    return json.dumps({
                        "level": record.levelname,
                        "logger": record.name,
                        "message": record.getMessage(),
                        "time": self.formatTime(record),
                    })

            handler.setFormatter(JsonFormatter())
        except Exception:
            pass  # fallback to default formatting

    logging.basicConfig(level=level, handlers=[handler])
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
