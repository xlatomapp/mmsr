from datetime import date, time

import pytest

from mmsr.periods import (
    IntradayBucketSpec,
    ReportPeriod,
    TradingSession,
    build_intraday_bucket_grid,
)


def test_bucket_spec_accepts_minutes() -> None:
    spec = IntradayBucketSpec("5m")
    assert spec.size == 5
    assert spec.unit == "m"


def test_bucket_spec_rejects_invalid_value() -> None:
    with pytest.raises(ValueError):
        IntradayBucketSpec("five_minutes")


def test_report_period_allows_no_static_sessions_for_production_kdb() -> None:
    period = ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 2),
        sessions=[],
        bucket=IntradayBucketSpec("5m"),
    )

    assert period.sessions == []


def test_trading_session_requires_start_before_end() -> None:
    with pytest.raises(ValueError):
        TradingSession(start=time(11, 30), end=time(9, 0))


def test_intraday_bucket_grid_includes_auction_buckets_and_sort_order() -> None:
    grid = build_intraday_bucket_grid(
        sessions=[
            TradingSession(start=time(9, 0), end=time(9, 2), name="AM"),
            TradingSession(start=time(12, 30), end=time(12, 32), name="PM"),
        ],
        bucket=IntradayBucketSpec("1m"),
    )

    assert [bucket.label for bucket in grid] == [
        "AMO",
        "9:00-9:01",
        "9:01-9:02",
        "AMC",
        "PMO",
        "12:30-12:31",
        "12:31-12:32",
        "PMC",
    ]
    assert [bucket.sort_order for bucket in grid] == list(range(1, 9))
    assert grid[0].is_auction is True
    assert grid[1].is_auction is False
    assert grid[-1].auction_code == "PMC"


def test_intraday_bucket_grid_can_exclude_auction_buckets() -> None:
    grid = build_intraday_bucket_grid(
        sessions=[TradingSession(start=time(9, 0), end=time(9, 2))],
        bucket=IntradayBucketSpec("1m"),
        include_auction_buckets=False,
    )

    assert [bucket.label for bucket in grid] == ["9:00-9:01", "9:01-9:02"]
    assert [bucket.sort_order for bucket in grid] == [1, 2]
