from datetime import date, time

import pytest

from mmsr.analysis.comparison import (
    ComparisonPolicy,
    ReferenceObservationSpec,
    compare_metric_timeseries,
    compare_reversion_metric_timeseries,
    compare_to_reference_distribution,
    reference_distribution_stats,
    robust_reference_stats,
    standard_reference_stats,
)
from mmsr.metrics.results import MetricObservation, MetricTimeSeries


def test_standard_z_score_formula_can_be_tested_with_explicit_small_threshold() -> None:
    stats = standard_reference_stats(13.0, [10.0, 11.0, 12.0], min_sample_size=3)

    assert stats.reference_value == pytest.approx(11.0)
    assert stats.z_score == pytest.approx(2.0)
    assert stats.sample_size == 3


def test_robust_z_score_formula_can_be_tested_with_explicit_small_threshold() -> None:
    stats = robust_reference_stats(13.0, [10.0, 11.0, 12.0], min_sample_size=3)

    assert stats.reference_value == pytest.approx(11.0)
    assert stats.z_score == pytest.approx(2.0 / 1.4826)


def test_default_policy_does_not_report_z_score_for_one_reference_observation() -> None:
    comparison = compare_to_reference_distribution(
        metric_name="quoted_spread_bps",
        value=13.0,
        reference_values=[10.0],
        higher_is_better=False,
    )

    assert comparison.reference_value == pytest.approx(10.0)
    assert comparison.change_abs == pytest.approx(3.0)
    assert comparison.z_score is None
    assert comparison.reference_sample_size == 1
    assert comparison.comparison_confidence == "insufficient"
    assert comparison.status == "comparison_only"


def test_reference_distribution_uses_empirical_rank_but_no_headline_z_below_policy_minimum() -> None:
    values = [float(item) for item in range(1, 21)]
    stats = reference_distribution_stats(
        19.0,
        values,
        method="robust",
        higher_is_better=False,
    )

    assert stats.sample_size == 20
    assert stats.confidence == "weak"
    assert stats.z_score is None
    assert stats.empirical_percentile == pytest.approx(19 / 20)
    assert stats.empirical_adverse_tail_probability == pytest.approx(2 / 20)
    assert stats.range_position_score is not None
    assert "low-confidence" in (stats.message or "")


def test_reference_distribution_reports_normal_score_percentile_when_policy_minimum_is_met() -> None:
    values = [10.0 + (item % 5) for item in range(30)]
    stats = reference_distribution_stats(
        14.0,
        values,
        method="standard",
        higher_is_better=False,
    )

    assert stats.sample_size == 30
    assert stats.confidence == "normal"
    assert stats.z_score is not None
    assert stats.normal_score_percentile is not None
    assert 0.0 <= stats.normal_score_percentile <= 1.0
    assert stats.normal_score_adverse_tail_probability == pytest.approx(1.0 - stats.normal_score_percentile)


def test_higher_is_better_direction_uses_lower_tail_as_adverse_tail() -> None:
    values = [float(item) for item in range(1, 31)]
    high_is_bad = reference_distribution_stats(
        29.0,
        values,
        method="standard",
        higher_is_better=False,
    )
    low_is_bad = reference_distribution_stats(
        2.0,
        values,
        method="standard",
        higher_is_better=True,
    )

    assert high_is_bad.normal_score_adverse_tail_probability is not None
    assert low_is_bad.normal_score_adverse_tail_probability is not None
    assert high_is_bad.normal_score_adverse_tail_probability < 0.10
    assert low_is_bad.normal_score_adverse_tail_probability < 0.10


def test_reference_observation_spec_requires_comparable_keys() -> None:
    spec = ReferenceObservationSpec(
        observation_unit="trading_day",
        comparable_keys=("metric_name", "time_bucket", "market_cap_bucket"),
    )

    assert spec.observation_unit == "trading_day"
    assert "time_bucket" in spec.comparable_keys


def test_comparison_policy_validates_sample_thresholds() -> None:
    with pytest.raises(ValueError, match="min_samples_for_z_score"):
        ComparisonPolicy(min_samples_for_z_score=1)


def test_compare_metric_timeseries_matches_reference_by_bucket_and_group() -> None:
    current = [
        MetricObservation(
            metric_name="quoted_spread_bps",
            date=date(2026, 5, 24),
            time_bucket=time(9, 0),
            group={"venue": "TSE", "segment": "Prime"},
            value=13.0,
        )
    ]
    reference = [
        MetricObservation(
            metric_name="quoted_spread_bps",
            date=date(2026, 5, day),
            time_bucket=time(9, 0),
            group={"venue": "TSE", "segment": "Prime"},
            value=float(10 + day),
        )
        for day in range(1, 6)
    ] + [
        MetricObservation(
            metric_name="quoted_spread_bps",
            date=date(2026, 5, day),
            time_bucket=time(9, 1),
            group={"venue": "TSE", "segment": "Prime"},
            value=999.0,
        )
        for day in range(1, 6)
    ]

    comparisons = compare_metric_timeseries(
        current,
        reference,
        metric_directions={"quoted_spread_bps": False},
        policy=ComparisonPolicy(
            min_samples_for_z_score=5,
            min_samples_for_empirical_percentile=2,
        ),
    )

    assert len(comparisons) == 1
    comparison = comparisons[0]
    assert comparison.date == date(2026, 5, 24)
    assert comparison.time_bucket == time(9, 0)
    assert comparison.group == {"venue": "TSE", "segment": "Prime"}
    assert comparison.reference_sample_size == 5
    assert comparison.reference_value == pytest.approx(13.0)
    assert comparison.metadata["reference_observation_unit"] == "trading_day"


def test_compare_metric_timeseries_keeps_venue_and_horizon_histories_separate() -> None:
    current = [
        MetricObservation(
            metric_name="primary_quote_reversion_10ms_bps",
            date=date(2026, 5, 24),
            time_bucket="AMO",
            group={"venue": "TSE", "horizon": "10ms"},
            value=4.0,
        ),
        MetricObservation(
            metric_name="primary_quote_reversion_10ms_bps",
            date=date(2026, 5, 24),
            time_bucket="AMO",
            group={"venue": "ODX", "horizon": "10ms"},
            value=9.0,
        ),
    ]
    reference = [
        MetricObservation(
            metric_name="primary_quote_reversion_10ms_bps",
            date=date(2026, 5, day),
            time_bucket="AMO",
            group={"venue": "TSE", "horizon": "10ms"},
            value=1.0,
        )
        for day in range(1, 4)
    ] + [
        MetricObservation(
            metric_name="primary_quote_reversion_10ms_bps",
            date=date(2026, 5, day),
            time_bucket="AMO",
            group={"venue": "ODX", "horizon": "10ms"},
            value=8.0,
        )
        for day in range(1, 4)
    ]

    comparisons = compare_metric_timeseries(
        current,
        reference,
        policy=ComparisonPolicy(
            reference_observation=ReferenceObservationSpec(
                comparable_keys=("metric_name", "time_bucket", "venue", "horizon")
            ),
            min_samples_for_z_score=3,
            min_samples_for_empirical_percentile=2,
        ),
    )

    by_venue = {comparison.group["venue"]: comparison for comparison in comparisons}
    assert by_venue["TSE"].reference_value == pytest.approx(1.0)
    assert by_venue["ODX"].reference_value == pytest.approx(8.0)
    assert by_venue["TSE"].time_bucket == "AMO"


def test_compare_metric_timeseries_counts_trading_days_not_duplicate_rows() -> None:
    current = [
        MetricObservation(
            metric_name="turnover",
            date=date(2026, 5, 24),
            time_bucket=None,
            group={"segment": "Prime"},
            value=20.0,
        )
    ]
    reference = [
        MetricObservation(
            metric_name="turnover",
            date=date(2026, 5, 20),
            time_bucket=None,
            group={"segment": "Prime"},
            value=10.0,
        ),
        MetricObservation(
            metric_name="turnover",
            date=date(2026, 5, 20),
            time_bucket=None,
            group={"segment": "Prime"},
            value=14.0,
        ),
        MetricObservation(
            metric_name="turnover",
            date=date(2026, 5, 21),
            time_bucket=None,
            group={"segment": "Prime"},
            value=30.0,
        ),
    ]

    comparisons = compare_metric_timeseries(
        current,
        reference,
        reference_observation_aggregation="mean",
        policy=ComparisonPolicy(
            min_samples_for_z_score=3,
            min_samples_for_empirical_percentile=2,
        ),
    )

    comparison = comparisons[0]
    assert comparison.reference_sample_size == 2
    assert comparison.reference_value == pytest.approx(21.0)
    assert comparison.z_score is None
    assert comparison.comparison_confidence == "weak"


def test_compare_reversion_metric_timeseries_uses_venue_horizon_and_group_policy() -> None:
    current = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 24),
                time_bucket="09:00-09:05",
                group={"venue": "ODX", "horizon": "10ms", "sym": "7203"},
                value=31.0,
            )
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )
    reference = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 4, day),
                time_bucket="09:00-09:05",
                group={"venue": "ODX", "horizon": "10ms", "sym": "7203"},
                value=float(day),
            )
            for day in range(1, 31)
        ]
        + [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 4, day),
                time_bucket="09:00-09:05",
                group={"venue": "ODX", "horizon": "10ms", "sym": "9984"},
                value=999.0,
            )
            for day in range(1, 31)
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    (comparison,) = compare_reversion_metric_timeseries(current, reference)

    assert comparison.reference_sample_size == 30
    assert comparison.reference_value == pytest.approx(15.5)
    assert comparison.group == {"venue": "ODX", "horizon": "10ms", "sym": "7203"}
    assert comparison.metadata["reference_observation_unit"] == "trading_day"
    assert comparison.metadata["reference_observation_aggregation"] == "mean"
    assert comparison.normal_score_adverse_tail_probability is not None
    assert comparison.normal_score_adverse_tail_probability < 0.10
    assert comparison.status in {"watch", "alert"}


def test_compare_reversion_metric_timeseries_accepts_collections() -> None:
    current = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_1s_bps",
                date=date(2026, 5, 24),
                time_bucket="AMO",
                group={"venue": "TSE", "horizon": "1s"},
                value=2.0,
            )
        ],
        metric_name="primary_quote_reversion_1s_bps",
    )
    reference = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_1s_bps",
                date=date(2026, 5, day),
                time_bucket="AMO",
                group={"venue": "TSE", "horizon": "1s"},
                value=1.0,
            )
            for day in range(1, 3)
        ],
        metric_name="primary_quote_reversion_1s_bps",
    )

    comparisons = compare_reversion_metric_timeseries(
        [current],
        [reference],
        policy=ComparisonPolicy(
            min_samples_for_z_score=3,
            min_samples_for_empirical_percentile=2,
        ),
    )

    assert len(comparisons) == 1
    assert comparisons[0].reference_sample_size == 2
    assert comparisons[0].comparison_confidence == "weak"


def test_compare_reversion_metric_timeseries_requires_reversion_metrics() -> None:
    current = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 24),
                time_bucket="AMO",
                group={"venue": "TSE", "horizon": "10ms"},
                value=1.0,
            )
        ],
        metric_name="quoted_spread_bps",
    )

    with pytest.raises(ValueError, match="primary_quote_reversion_"):
        compare_reversion_metric_timeseries(current, current)
