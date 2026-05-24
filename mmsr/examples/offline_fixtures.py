"""Synthetic offline fixtures for demo reports.

The fixtures in this module are deliberately small and deterministic. They build
already-normalized metric observations and comparisons for examples and tests
without importing PyKX, connecting to kdb+, or calculating metrics from raw
trade/quote data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping

from mmsr.analysis.comparison import ComparisonPolicy, compare_metric_timeseries
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.registry import build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries


SAMPLE_REPORT_DATE = date(2026, 5, 22)
SAMPLE_REFERENCE_DATES: tuple[date, ...] = (
    date(2026, 4, 6),
    date(2026, 4, 7),
    date(2026, 4, 8),
    date(2026, 4, 9),
    date(2026, 4, 10),
    date(2026, 4, 13),
    date(2026, 4, 14),
    date(2026, 4, 15),
    date(2026, 4, 16),
    date(2026, 4, 17),
    date(2026, 4, 20),
    date(2026, 4, 21),
    date(2026, 4, 22),
    date(2026, 4, 23),
    date(2026, 4, 24),
    date(2026, 4, 27),
    date(2026, 4, 28),
    date(2026, 4, 30),
    date(2026, 5, 1),
    date(2026, 5, 7),
    date(2026, 5, 8),
    date(2026, 5, 11),
    date(2026, 5, 12),
    date(2026, 5, 13),
    date(2026, 5, 14),
    date(2026, 5, 15),
    date(2026, 5, 18),
    date(2026, 5, 19),
    date(2026, 5, 20),
    date(2026, 5, 21),
)


@dataclass(frozen=True)
class OfflineSampleMetrics:
    """Synthetic normalized metrics for offline demos and tests.

    ``current_series`` and ``reference_series`` are ready to feed into the
    comparison engine. ``comparisons`` is precomputed with the same deterministic
    policy so example report builders can render without a live kdb connection.
    """

    report_date: date
    metric_definitions: Mapping[str, MetricDefinition]
    current_series: tuple[MetricTimeSeries, ...]
    reference_series: tuple[MetricTimeSeries, ...]
    comparisons: tuple[MetricComparison, ...]


def build_offline_metric_time_series() -> tuple[MetricTimeSeries, ...]:
    """Return deterministic current-period sample metric time series."""

    return tuple(
        MetricTimeSeries.from_observations(
            observations,
            metric_name=metric_name,
            metadata={"fixture": "offline_sample", "role": "current"},
        )
        for metric_name, observations in _current_observations_by_metric().items()
    )


def build_offline_reference_time_series() -> tuple[MetricTimeSeries, ...]:
    """Return deterministic historical sample metric time series."""

    return tuple(
        MetricTimeSeries.from_observations(
            observations,
            metric_name=metric_name,
            metadata={"fixture": "offline_sample", "role": "reference"},
        )
        for metric_name, observations in _reference_observations_by_metric().items()
    )


def build_offline_metric_comparisons() -> tuple[MetricComparison, ...]:
    """Return deterministic comparisons for the offline sample metrics."""

    registry = build_default_registry()
    current = build_offline_metric_time_series()
    reference = build_offline_reference_time_series()
    definitions = {
        metric_name: registry.get(metric_name)
        for metric_name in _SAMPLE_METRIC_NAMES
    }
    directions = {
        name: definition.higher_is_better for name, definition in definitions.items()
    }
    comparisons = compare_metric_timeseries(
        _flatten_observations(current),
        _flatten_observations(reference),
        metric_directions=directions,
        policy=ComparisonPolicy(),
    )
    return tuple(comparisons)


def build_offline_sample_metrics() -> OfflineSampleMetrics:
    """Build all synthetic data needed by the first offline report examples."""

    registry = build_default_registry()
    definitions = {
        metric_name: registry.get(metric_name)
        for metric_name in _SAMPLE_METRIC_NAMES
    }
    current = build_offline_metric_time_series()
    reference = build_offline_reference_time_series()
    comparisons = build_offline_metric_comparisons()
    return OfflineSampleMetrics(
        report_date=SAMPLE_REPORT_DATE,
        metric_definitions=definitions,
        current_series=current,
        reference_series=reference,
        comparisons=comparisons,
    )


_SAMPLE_METRIC_NAMES: tuple[str, ...] = (
    "quoted_spread_bps",
    "volume",
    "top_of_book_depth",
)


def _current_observations_by_metric() -> dict[str, tuple[MetricObservation, ...]]:
    return {
        "quoted_spread_bps": (
            _observation(
                "quoted_spread_bps",
                SAMPLE_REPORT_DATE,
                "AMO",
                {"market_segment": "Prime", "market_cap_bucket": "Large"},
                11.2,
                sample_size=160,
            ),
            _observation(
                "quoted_spread_bps",
                SAMPLE_REPORT_DATE,
                "09:00-09:05",
                {"market_segment": "Prime", "market_cap_bucket": "Small"},
                42.1,
                sample_size=92,
            ),
        ),
        "volume": (
            _observation(
                "volume",
                SAMPLE_REPORT_DATE,
                "AMO",
                {"market_segment": "Prime", "market_cap_bucket": "Large"},
                1_250_000,
                sample_size=180,
            ),
            _observation(
                "volume",
                SAMPLE_REPORT_DATE,
                "09:00-09:05",
                {"market_segment": "Prime", "market_cap_bucket": "Small"},
                420_000,
                sample_size=75,
            ),
        ),
        "top_of_book_depth": (
            _observation(
                "top_of_book_depth",
                SAMPLE_REPORT_DATE,
                "AMO",
                {"market_segment": "Prime", "market_cap_bucket": "Large"},
                38_000,
                sample_size=160,
            ),
            _observation(
                "top_of_book_depth",
                SAMPLE_REPORT_DATE,
                "09:00-09:05",
                {"market_segment": "Prime", "market_cap_bucket": "Small"},
                9_500,
                sample_size=92,
            ),
        ),
    }


def _reference_observations_by_metric() -> dict[str, tuple[MetricObservation, ...]]:
    rows: dict[str, list[MetricObservation]] = {
        metric_name: [] for metric_name in _SAMPLE_METRIC_NAMES
    }

    for index, reference_date in enumerate(SAMPLE_REFERENCE_DATES):
        rows["quoted_spread_bps"].extend(
            (
                _observation(
                    "quoted_spread_bps",
                    reference_date,
                    "AMO",
                    {"market_segment": "Prime", "market_cap_bucket": "Large"},
                    _cycle_value(10.4, index, amplitude=0.7),
                    sample_size=145 + (index % 10),
                ),
                _observation(
                    "quoted_spread_bps",
                    reference_date,
                    "09:00-09:05",
                    {"market_segment": "Prime", "market_cap_bucket": "Small"},
                    _cycle_value(30.8, index, amplitude=1.8),
                    sample_size=82 + (index % 9),
                ),
            )
        )
        rows["volume"].extend(
            (
                _observation(
                    "volume",
                    reference_date,
                    "AMO",
                    {"market_segment": "Prime", "market_cap_bucket": "Large"},
                    round(_cycle_value(1_170_000, index, amplitude=55_000)),
                    sample_size=165 + (index % 8),
                ),
                _observation(
                    "volume",
                    reference_date,
                    "09:00-09:05",
                    {"market_segment": "Prime", "market_cap_bucket": "Small"},
                    round(_cycle_value(390_000, index, amplitude=23_000)),
                    sample_size=70 + (index % 7),
                ),
            )
        )
        rows["top_of_book_depth"].extend(
            (
                _observation(
                    "top_of_book_depth",
                    reference_date,
                    "AMO",
                    {"market_segment": "Prime", "market_cap_bucket": "Large"},
                    round(_cycle_value(40_500, index, amplitude=2_300)),
                    sample_size=145 + (index % 10),
                ),
                _observation(
                    "top_of_book_depth",
                    reference_date,
                    "09:00-09:05",
                    {"market_segment": "Prime", "market_cap_bucket": "Small"},
                    round(_cycle_value(14_500, index, amplitude=1_400)),
                    sample_size=82 + (index % 9),
                ),
            )
        )

    return {metric_name: tuple(observations) for metric_name, observations in rows.items()}


def _observation(
    metric_name: str,
    observation_date: date,
    time_bucket: str,
    group: dict[str, str],
    value: float | int,
    *,
    sample_size: int,
) -> MetricObservation:
    return MetricObservation(
        metric_name=metric_name,
        date=observation_date,
        time_bucket=time_bucket,
        group=group,
        value=value,
        metadata={
            "fixture": "offline_sample",
            "source": "synthetic",
            "sample_size": sample_size,
        },
    )


def _cycle_value(base: float, index: int, *, amplitude: float) -> float:
    """Return a deterministic, bounded value around ``base``."""

    pattern = (-3, -2, -1, 0, 1, 2, 3, 2, 1, 0)
    return base + amplitude * pattern[index % len(pattern)] / 3.0


def _flatten_observations(
    series_collection: tuple[MetricTimeSeries, ...],
) -> tuple[MetricObservation, ...]:
    return tuple(
        observation
        for series in series_collection
        for observation in series.observations
    )


__all__ = [
    "OfflineSampleMetrics",
    "SAMPLE_REFERENCE_DATES",
    "SAMPLE_REPORT_DATE",
    "build_offline_metric_comparisons",
    "build_offline_metric_time_series",
    "build_offline_reference_time_series",
    "build_offline_sample_metrics",
]
