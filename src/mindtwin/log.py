"""Logging helpers. Library code only calls ``get_logger``; applications call ``setup_logging``."""

from __future__ import annotations

import logging

LOGGER_NAME = "mindtwin"
FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

logging.getLogger(LOGGER_NAME).addHandler(logging.NullHandler())


def get_logger(name: str | None = None) -> logging.Logger:
    """Logger under the ``mindtwin`` namespace, e.g. ``get_logger(__name__)``."""
    if not name or name == LOGGER_NAME:
        return logging.getLogger(LOGGER_NAME)
    if not name.startswith(LOGGER_NAME + "."):
        name = f"{LOGGER_NAME}.{name}"
    return logging.getLogger(name)


def setup_logging(level: str | int | None = None) -> logging.Logger:
    """Send mindtwin logs to stderr. Level defaults to the configured ``log_level``."""
    if level is None:
        from mindtwin.config import get_settings

        level = get_settings().log_level
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    if not any(getattr(h, "_mindtwin", False) for h in logger.handlers):
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(FORMAT))
        handler._mindtwin = True  # type: ignore[attr-defined]
        logger.addHandler(handler)
    return logger
