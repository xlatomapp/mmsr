"""Trading calendar abstractions.

Production trading calendars should come from a dedicated data source. For this
project, that source is expected to be kdb+. The weekday helper remains available
only for offline examples and unit tests; production report generation should use
``KdbTradingCalendarSource`` or another explicit ``TradingCalendarSource``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Protocol


class TradingCalendarSource(Protocol):
    """Interface for retrieving trading days from a dedicated source."""

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return trading days between two dates, inclusive."""


@dataclass(frozen=True)
class KdbTradingCalendarSource:
    """Trading calendar source backed by a kdb+ calendar table."""

    client: Any
    table: str = "trading_calendar"
    date_column: str = "date"
    is_trading_day_column: str = "is_trading_day"

    def trading_days(self, start: date, end: date) -> list[date]:
        """Return trading days by querying the configured kdb calendar table."""
        if start > end:
            raise ValueError("start must be on or before end")

        query = (
            f"select {self.date_column} from {self.table} "
            f"where {self.date_column} within (start;end), "
            f"{self.is_trading_day_column}"
        )
        result = self.client.execute(query, start, end)
        return _coerce_calendar_dates(result, self.date_column)


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
