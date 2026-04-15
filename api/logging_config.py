from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

_BASE_LOG_RECORD_KEYS = frozenset(logging.makeLogRecord({}).__dict__) | {
    "asctime",
    "message",
}

_logging_configured = False


class JsonFormatter(logging.Formatter):
    """Render log records as compact JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key in _BASE_LOG_RECORD_KEYS or key.startswith("_"):
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """Install JSON logging once per process."""

    global _logging_configured
    if _logging_configured:
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(
        level=level,
        handlers=[handler],
        force=True,
    )
    _logging_configured = True
