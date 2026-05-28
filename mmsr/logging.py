"""Logging configuration helpers for MMSR CLI and production execution."""

from __future__ import annotations

import logging


_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
_DEFAULT_LEVEL = logging.WARNING


def configure_logging(*, verbose: bool = False, log_level: str | None = None) -> int:
    """Configure process logging and return the selected numeric level.

    ``--verbose`` is intentionally simple: it maps to DEBUG. ``--log-level`` is
    available when a user wants INFO-only status logs without full rendered q
    snippets.
    """

    level = _coerce_log_level(log_level) if log_level else (
        logging.DEBUG if verbose else _DEFAULT_LEVEL
    )
    logging.basicConfig(level=level, format=_LOG_FORMAT, force=True)
    logging.getLogger("mmsr").setLevel(level)
    return level


def _coerce_log_level(value: str) -> int:
    normalized = value.strip().upper()
    level = getattr(logging, normalized, None)
    if not isinstance(level, int):
        valid = ", ".join(("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"))
        raise ValueError(f"invalid log level {value!r}; expected one of: {valid}")
    return level
