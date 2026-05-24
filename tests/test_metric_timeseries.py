from datetime import date, time

import pytest

from mmsr.metrics import MetricTimeSeries
from mmsr.metrics.results import MetricObservation


def test_metric_timeseries_from_observations_infers_metric_name() -> None:
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 24),
                time_bucket=time(9, 0),
                group={"segment": "Prime"},
                value=11.5,
            )
        ]
    )

    assert series.metric_name == "quoted_spread_bps"
    assert len(series) == 1


def test_metric_timeseries_preserves_dates_time_buckets_groups_and_order() -> None:
    first = MetricObservation(
        metric_name="turnover",
        date=date(2026, 5, 23),
        time_bucket="AMO",
        group={"segment": "Prime", "venue": "TSE"},
        value=100.0,
    )
    second = MetricObservation(
        metric_name="turnover",
        date=date(2026, 5, 24),
        time_bucket=time(9, 0),
        group={"segment": "Prime", "venue": "ODX"},
        value=120.0,
    )

    series = MetricTimeSeries(metric_name="turnover", observations=(first, second))

    assert tuple(series) == (first, second)
    assert series.dates == (date(2026, 5, 23), date(2026, 5, 24))
    assert series.time_buckets == ("AMO", time(9, 0))
    assert series.observations[0].group == {"segment": "Prime", "venue": "TSE"}
    assert series.observations[1].group == {"segment": "Prime", "venue": "ODX"}
    assert series.values == (100.0, 120.0)


def test_metric_timeseries_rejects_inconsistent_metric_names() -> None:
    with pytest.raises(ValueError, match="same metric_name"):
        MetricTimeSeries.from_observations(
            [
                MetricObservation(
                    metric_name="turnover",
                    date=date(2026, 5, 24),
                    time_bucket=None,
                    group={},
                    value=10.0,
                ),
                MetricObservation(
                    metric_name="volume",
                    date=date(2026, 5, 24),
                    time_bucket=None,
                    group={},
                    value=20.0,
                ),
            ]
        )


def test_metric_timeseries_requires_metric_name_for_empty_series() -> None:
    with pytest.raises(ValueError, match="metric_name is required"):
        MetricTimeSeries.from_observations([])

    empty = MetricTimeSeries.from_observations([], metric_name="turnover")
    assert empty.metric_name == "turnover"
    assert empty.observations == ()


def test_metric_timeseries_normalizes_list_observations_to_tuple() -> None:
    observation = MetricObservation(
        metric_name="trade_count",
        date=date(2026, 5, 24),
        time_bucket=None,
        group={},
        value=5,
    )

    series = MetricTimeSeries(metric_name=" trade_count ", observations=[observation])  # type: ignore[arg-type]

    assert series.metric_name == "trade_count"
    assert series.observations == (observation,)
