from __future__ import annotations

"""
Structured logging configuration.

Output format is controlled by LOG_FORMAT env var:
  - "json"  → JSON lines for log aggregation (production)
  - "text"  → human-readable text (dev, default)

Usage:
    from streaming.common.logging_config import get_logger
    log = get_logger(__name__)
    log.info("processing batch", extra={"topic": "binlog", "count": 500})
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            payload["exception"] = str(record.exc_info[1])
        # Include extra fields passed via log.info(..., extra={...})
        for key in ("topic", "count", "database", "table", "dt", "duration_ms",
                     "trace_id", "offset", "partition"):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        return json.dumps(payload, ensure_ascii=False, default=str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger configured for the current environment."""
    logger = logging.getLogger(name)

    # Only configure once
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    log_format = os.environ.get("LOG_FORMAT", "text")

    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))

    logger.addHandler(handler)

    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level, logging.INFO))

    # Don't propagate to root logger
    logger.propagate = False

    return logger
