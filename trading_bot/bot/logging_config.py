"""Logging configuration for API requests, responses, and errors."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "trading_bot.log"


class JsonFormatter(logging.Formatter):
    """Format records as JSON lines for easier review and parsing."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key in ("event", "method", "url", "params", "status_code", "response", "error"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(log_file: Path = LOG_FILE) -> None:
    """Configure file logging once for the application."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if any(isinstance(handler, logging.FileHandler) and handler.baseFilename == str(log_file.resolve()) for handler in root_logger.handlers):
        return

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

