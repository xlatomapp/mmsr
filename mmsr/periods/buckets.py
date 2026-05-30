"""Utilities for building deterministic intraday bucket grids."""

from __future__ import annotations

from datetime import datetime, time, timedelta

from mmsr.periods.models import (
    AuctionBucketLabels,
    IntradayBucketSpec,
    TimeBucket,
    TradingSession,
)

_BASE_DATE = datetime(2000, 1, 1)


def _bucket_delta(spec: IntradayBucketSpec) -> timedelta:
    if spec.unit == "m":
        return timedelta(minutes=spec.size)
    if spec.unit == "h":
        return timedelta(hours=spec.size)
    if spec.unit == "d":
        return timedelta(days=spec.size)
    raise ValueError(f"unsupported bucket unit: {spec.unit}")


def _to_datetime(value: time) -> datetime:
    return datetime.combine(_BASE_DATE.date(), value)


def _format_time(value: time) -> str:
    return f"{value.hour}:{value.minute:02d}"


def _session_name(session: TradingSession, index: int) -> str:
    if session.name:
        return session.name
    if index == 0:
        return "AM"
    if index == 1:
        return "PM"
    return f"S{index + 1}"


def build_intraday_bucket_grid(
    sessions: list[TradingSession],
    bucket: IntradayBucketSpec,
    *,
    include_auction_buckets: bool = True,
    auction_labels: AuctionBucketLabels | None = None,
) -> list[TimeBucket]:
    """Build a sortable grid of auction and continuous intraday buckets.

    For a standard Japanese cash equity day with sessions ``09:00-11:30`` and
    ``12:30-15:30``, a one-minute bucket spec produces rows such as::

        AMO          sort_order=1
        9:00-9:01   sort_order=2
        9:01-9:02   sort_order=3
        ...
        AMC          sort_order=N
        PMO          sort_order=N+1
        12:30-12:31 sort_order=N+2
        ...
        PMC          sort_order=last

    The explicit ``sort_order`` column should be used in report outputs and kdb
    result joins instead of sorting bucket labels lexicographically.
    """
    if not sessions:
        raise ValueError("at least one trading session is required")

    labels = auction_labels or AuctionBucketLabels()
    delta = _bucket_delta(bucket)
    if delta <= timedelta(0):
        raise ValueError("bucket duration must be positive")

    rows: list[TimeBucket] = []
    sort_order = 1

    for session_index, session in enumerate(sessions):
        session_label = _session_name(session, session_index)

        if include_auction_buckets:
            code = labels.open_label_for_session(session_index)
            rows.append(
                TimeBucket(
                    label=code,
                    sort_order=sort_order,
                    start=session.start,
                    end=session.start,
                    session=session_label,
                    phase="auction_open",
                    is_auction=True,
                    auction_code=code,
                )
            )
            sort_order += 1

        current = _to_datetime(session.start)
        session_end = _to_datetime(session.end)
        while current < session_end:
            end = min(current + delta, session_end)
            start_time = current.time()
            end_time = end.time()
            rows.append(
                TimeBucket(
                    label=f"{_format_time(start_time)}-{_format_time(end_time)}",
                    sort_order=sort_order,
                    start=start_time,
                    end=end_time,
                    session=session_label,
                    phase="continuous",
                )
            )
            sort_order += 1
            current = end

        if include_auction_buckets:
            code = labels.close_label_for_session(session_index)
            rows.append(
                TimeBucket(
                    label=code,
                    sort_order=sort_order,
                    start=session.end,
                    end=session.end,
                    session=session_label,
                    phase="auction_close",
                    is_auction=True,
                    auction_code=code,
                )
            )
            sort_order += 1

    return rows


def bucket_grid_as_records(buckets: list[TimeBucket]) -> list[dict[str, object]]:
    """Convert a bucket grid to dictionaries for serialization or templates."""
    return [bucket.as_record() for bucket in buckets]
