"""Domain models for report periods and intraday buckets."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, time

_BUCKET_RE = re.compile(r"^(?P<size>[1-9][0-9]*)(?P<unit>[mhd])$")


@dataclass(frozen=True)
class TradingSession:
    """A continuous trading session within a trading day.

    The ``name`` field is optional because many tests and configs only need start/end
    times. When two sessions are supplied for Japan cash equity monitoring, the
    convention is usually ``AM`` for the morning continuous session and ``PM`` for
    the afternoon continuous session.
    """

    start: time
    end: time
    name: str | None = None

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError("TradingSession.start must be before end")


@dataclass(frozen=True)
class IntradayBucketSpec:
    """Configurable intraday bucket specification, for example 1m/5m/30m."""

    value: str

    def __post_init__(self) -> None:
        if not _BUCKET_RE.match(self.value):
            raise ValueError("bucket size must look like '1m', '5m', '30m', '1h'")

    @property
    def unit(self) -> str:
        """Return bucket unit."""
        match = _BUCKET_RE.match(self.value)
        assert match is not None
        return match.group("unit")

    @property
    def size(self) -> int:
        """Return bucket size as an integer."""
        match = _BUCKET_RE.match(self.value)
        assert match is not None
        return int(match.group("size"))


@dataclass(frozen=True)
class TimeBucket:
    """One row in the intraday bucket grid used for sorting and reporting.

    Auction buckets such as ``AMO`` and ``PMC`` are represented explicitly so that
    report outputs can preserve the true market sequence instead of relying on
    string sorting. Continuous buckets have a start and end time. Auction buckets
    use the auction event time for both start and end.
    """

    label: str
    sort_order: int
    start: time | None
    end: time | None
    session: str
    phase: str
    is_auction: bool = False
    auction_code: str | None = None

    def as_record(self) -> dict[str, object]:
        """Return a dictionary representation suitable for tables/templates."""
        return {
            "label": self.label,
            "sort_order": self.sort_order,
            "start": self.start,
            "end": self.end,
            "session": self.session,
            "phase": self.phase,
            "is_auction": self.is_auction,
            "auction_code": self.auction_code,
        }


@dataclass(frozen=True)
class AuctionBucketLabels:
    """Configurable auction bucket labels for the standard JPX day shape."""

    morning_open: str = "AMO"
    morning_close: str = "AMC"
    afternoon_open: str = "PMO"
    afternoon_close: str = "PMC"

    def open_label_for_session(self, index: int) -> str:
        """Return the opening auction label for a zero-based session index."""
        if index == 0:
            return self.morning_open
        if index == 1:
            return self.afternoon_open
        return f"S{index + 1}O"

    def close_label_for_session(self, index: int) -> str:
        """Return the closing auction label for a zero-based session index."""
        if index == 0:
            return self.morning_close
        if index == 1:
            return self.afternoon_close
        return f"S{index + 1}C"


@dataclass(frozen=True)
class ReportPeriod:
    """A report period represented as a date range and bucket size.

    ``sessions`` is retained for legacy/offline bucket-grid use, but production
    kdb runs no longer derive session state from static config. Production
    trade/quote source rows must carry their own ``session`` and ``auction``
    columns because sessions can vary by symbol and trading day.
    """

    start_date: date
    end_date: date
    sessions: list[TradingSession] = field(default_factory=list)
    bucket: IntradayBucketSpec = field(default_factory=lambda: IntradayBucketSpec("5m"))
    timezone: str = "Asia/Tokyo"
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start_date > self.end_date:
            raise ValueError("ReportPeriod.start_date must be on or before end_date")
