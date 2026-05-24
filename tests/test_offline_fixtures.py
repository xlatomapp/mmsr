from datetime import date

from mmsr.examples import (
    SAMPLE_REFERENCE_DATES,
    SAMPLE_REPORT_DATE,
    build_offline_metric_comparisons,
    build_offline_metric_time_series,
    build_offline_reference_time_series,
    build_offline_sample_metrics,
)
from mmsr.metrics.results import MetricComparison, MetricTimeSeries


def test_offline_metric_fixtures_build_current_and_reference_series() -> None:
    current = build_offline_metric_time_series()
    reference = build_offline_reference_time_series()

    assert [series.metric_name for series in current] == [
        "quoted_spread_bps",
        "volume",
        "top_of_book_depth",
    ]
    assert [series.metric_name for series in reference] == [
        "quoted_spread_bps",
        "volume",
        "top_of_book_depth",
    ]
    assert all(isinstance(series, MetricTimeSeries) for series in current)
    assert all(series.metadata["role"] == "current" for series in current)
    assert all(series.metadata["role"] == "reference" for series in reference)
    assert len(current[0].observations) == 2
    assert len(reference[0].observations) == 2 * len(SAMPLE_REFERENCE_DATES)

    first = current[0].observations[0]
    assert first.date == SAMPLE_REPORT_DATE
    assert first.time_bucket == "AMO"
    assert first.group == {
        "market_segment": "Prime",
        "market_cap_bucket": "Large",
    }
    assert first.metadata["fixture"] == "offline_sample"
    assert first.metadata["source"] == "synthetic"


def test_offline_reference_dates_are_explicit_historical_observation_units() -> None:
    assert len(SAMPLE_REFERENCE_DATES) == 30
    assert SAMPLE_REFERENCE_DATES[0] == date(2026, 4, 6)
    assert SAMPLE_REFERENCE_DATES[-1] == date(2026, 5, 21)
    assert SAMPLE_REPORT_DATE not in SAMPLE_REFERENCE_DATES
    assert SAMPLE_REFERENCE_DATES == tuple(sorted(SAMPLE_REFERENCE_DATES))


def test_offline_metric_comparisons_are_precomputed_and_comparable() -> None:
    comparisons = build_offline_metric_comparisons()

    assert len(comparisons) == 6
    assert all(isinstance(comparison, MetricComparison) for comparison in comparisons)
    assert {comparison.reference_sample_size for comparison in comparisons} == {30}
    assert {comparison.comparison_confidence for comparison in comparisons} == {
        "normal"
    }
    assert all(comparison.z_score is not None for comparison in comparisons)
    assert all(
        comparison.metadata["reference_observation_unit"] == "trading_day"
        for comparison in comparisons
    )
    assert any(
        comparison.metric_name == "quoted_spread_bps"
        and comparison.time_bucket == "09:00-09:05"
        and comparison.status == "alert"
        for comparison in comparisons
    )


def test_offline_sample_metrics_bundles_definitions_series_and_comparisons() -> None:
    sample = build_offline_sample_metrics()

    assert sample.report_date == SAMPLE_REPORT_DATE
    assert tuple(sample.metric_definitions) == (
        "quoted_spread_bps",
        "volume",
        "top_of_book_depth",
    )
    assert tuple(series.metric_name for series in sample.current_series) == tuple(
        sample.metric_definitions
    )
    assert tuple(series.metric_name for series in sample.reference_series) == tuple(
        sample.metric_definitions
    )
    assert len(sample.comparisons) == 6
    assert sample.metric_definitions["quoted_spread_bps"].label == "Quoted Spread"
