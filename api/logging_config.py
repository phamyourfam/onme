"""Aesthetic logging configuration for OnMe.

Local dev  → colorized, emoji-annotated single-line output via loguru.
Production → structured JSON output via loguru serialization.

All stdlib loggers (including Uvicorn) are intercepted and routed
through loguru so there is exactly ONE handler and ZERO double-logging.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from loguru import logger

_logging_configured = False

# ── Emoji icons per log level ──────────────────────────────────────────
_LEVEL_ICONS: dict[str, str] = {
    "TRACE": "🔬",
    "DEBUG": "🐛",
    "INFO": "🟢",
    "SUCCESS": "✅",
    "WARNING": "🟡",
    "ERROR": "🔴",
    "CRITICAL": "💀",
}


class _InterceptHandler(logging.Handler):
    """Bridge stdlib logging → loguru.

    Captures every log record emitted by stdlib loggers (uvicorn,
    sqlalchemy, etc.) and re-emits them through loguru so a single
    handler pipeline formats all output.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Map stdlib level to loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find the caller frame that originated the log call
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def _local_format(record: dict[str, Any]) -> str:
    """Build a beautiful, colored single-line log for local terminals.

    Format:
      HH:MM:SS.mmm │ 🟢 INFO     │ onme.api ▸ startup_checks_passed
    """
    icon = _LEVEL_ICONS.get(record["level"].name, "  ")
    # Loguru uses {}-style formatting in format strings
    return (
        "<dim>{time:HH:mm:ss.SSS}</dim> "
        "<dim>│</dim> "
        f"{icon} "
        "<level>{level: <8}</level> "
        "<dim>│</dim> "
        "<cyan>{name}</cyan> <dim>▸</dim> "
        "<level>{message}</level>"
        "\n{exception}"
    )


def _json_sink(message: Any) -> None:
    """Serialize a loguru record to compact JSON for production."""
    record = message.record
    payload: dict[str, Any] = {
        "timestamp": datetime.fromtimestamp(
            record["time"].timestamp(), tz=timezone.utc
        ).isoformat(),
        "level": record["level"].name.lower(),
        "logger": record["name"],
        "event": record["message"],
    }

    # Include any extra fields bound via logger.bind(...)
    if record["extra"]:
        payload["extra"] = record["extra"]

    if record["exception"] is not None:
        payload["exception"] = str(record["exception"])

    sys.stderr.write(json.dumps(payload, default=str) + "\n")


def configure_logging(*, environment: str = "local") -> None:
    """Install aesthetic logging once per process.

    Parameters
    ----------
    environment
        When ``"local"``, use colorized emoji output.
        Otherwise, use structured JSON output.
    """
    global _logging_configured
    if _logging_configured:
        return

    # ── Wipe loguru defaults ──────────────────────────────────────
    logger.remove()

    is_local = environment == "local"

    if is_local:
        logger.add(
            sys.stderr,
            format=_local_format,
            level="DEBUG",
            colorize=True,
            backtrace=True,
            diagnose=True,
        )
    else:
        logger.add(
            _json_sink,
            format="{message}",
            level="INFO",
            serialize=False,  # We handle serialization ourselves
        )

    # ── Intercept all stdlib loggers ──────────────────────────────
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)

    # Silence overly chatty stdlib loggers
    for noisy_logger in ("asyncio", "aiosqlite", "multipart"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)

    # ── Tame Uvicorn's loggers ────────────────────────────────────
    # Remove Uvicorn's own handlers so they don't double-print.
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(uvicorn_logger_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True

    _logging_configured = True
