"""Trading calendar abstractions.

Production trading calendars should come from a dedicated data source. For this
project, that source is expected to be a user-owned kdb+ function. The weekday
helper remains available only for offline examples and unit tests; production
report generation should use ``KdbTradingCalendarSource`` or another explicit
``TradingCalendarSource``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Protocol

LOGGER = logging.getLogger(__name__)


class TradingCalendarSource(Protocol):
    """Interface for retrieving trading days from a dedicated source."""

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return trading days between two dates, inclusive."""


@dataclass(frozen=True)
class KdbTradingCalendarSource:
    """Trading calendar source backed by a user-defined kdb+ function.

    The configured function must accept two positional arguments,
    ``start`` and ``end``, and return either a date vector or a table/dict with
    ``date_column``.
    """

    client: Any
    function: str = ".mmsr.getTradingCalendar"
    date_column: str = "date"
    calculation_namespace: str = ".mmsr"

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return trading days by querying the configured calendar function."""
        if start > end:
            raise ValueError("start must be on or before end")

        function_name = _q_function_identifier(self.function)
        calculation_namespace = _q_namespace_identifier(self.calculation_namespace)
        query = f"{{[start;end] {calculation_namespace}.callTradingCalendar[{function_name};start;end]}}"
        LOGGER.info(
            "Calling kdb trading calendar function %s for %s..%s",
            self.function,
            start,
            end,
        )
        result = self.client.execute(query, start, end)
        days = _coerce_calendar_dates(result, self.date_column)
        LOGGER.info("Trading calendar returned %s day(s)", len(days))
        return days


def _coerce_calendar_dates(result: Any, date_column: str) -> list[date]:
    """Coerce common kdb/PyKX-like results into Python dates.

    The exact PyKX return type depends on the query and installed PyKX version, so
    this function intentionally handles simple dict/list shapes for unit tests and
    keeps production-specific conversion details isolated.
    """
    if result is None:
        return []

    if isinstance(result, dict):
        values = result.get(date_column, [])
        return list(values)

    if isinstance(result, list):
        if not result:
            return []
        if isinstance(result[0], dict):
            return [row[date_column] for row in result]
        return list(result)

    if isinstance(result, tuple):
        return list(result)

    if hasattr(result, "py"):
        return _coerce_calendar_dates(result.py(), date_column)

    raise TypeError(f"unsupported calendar result type: {type(result)!r}")


def _q_function_identifier(value: str) -> str:
    """Validate and return a q function identifier used in a calendar call."""

    if not isinstance(value, str) or not value:
        raise ValueError("calendar function must be a non-empty q function name")
    candidate = value[1:] if value.startswith(".") else value
    parts = candidate.split(".")
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"invalid calendar function: {value!r}")
    for part in parts:
        if not part.replace("_", "a").isalnum() or part[0].isdigit():
            raise ValueError(f"invalid calendar function: {value!r}")
    return value


def _q_namespace_identifier(value: str) -> str:
    """Validate and return a q namespace used for MMSR calendar dispatch."""

    if not isinstance(value, str) or not value:
        raise ValueError("calculation namespace must be a non-empty q namespace")
    if not value.startswith("."):
        raise ValueError("calculation namespace must start with '.'")
    candidate = value[1:]
    parts = candidate.split(".")
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"invalid calculation namespace: {value!r}")
    for part in parts:
        if not part.replace("_", "a").isalnum() or part[0].isdigit():
            raise ValueError(f"invalid calculation namespace: {value!r}")
    return value


def weekdays_between(start: date, end: date) -> list[date]:
    """Return weekdays between two dates, inclusive.

    This helper is for synthetic/offline examples only. Production code should use
    a dedicated trading calendar source, normally ``KdbTradingCalendarSource``.
    """
    if start > end:
        raise ValueError("start must be on or before end")
    out: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            out.append(current)
        current += timedelta(days=1)
    return out
