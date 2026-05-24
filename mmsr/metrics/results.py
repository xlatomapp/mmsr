"""Metric result containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Any, Iterable, Iterator


@dataclass(frozen=True)
class MetricObservation:
    """Single normalized metric observation."""

    metric_name: str
    date: date
    time_bucket: time | str | None
    group: dict[str, str]
    value: float | int | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MetricTimeSeries:
    """Ordered normalized observations for one metric.

    The class is intentionally lightweight so it can sit between kdb-backed
    metric execution and report rendering without pulling raw market data into
    Python. It preserves the input observation order and validates that every
    observation belongs to the same metric.
    """

    metric_name: str
    observations: tuple[MetricObservation, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        metric_name = self.metric_name.strip()
        if not metric_name:
            raise ValueError("metric_name must not be empty")

        observations = tuple(self.observations)
        for observation in observations:
            if observation.metric_name != metric_name:
                raise ValueError(
                    "all observations in a MetricTimeSeries must have the same metric_name"
                )

        object.__setattr__(self, "metric_name", metric_name)
        object.__setattr__(self, "observations", observations)

    @classmethod
    def from_observations(
        cls,
        observations: Iterable[MetricObservation],
        *,
        metric_name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "MetricTimeSeries":
        """Build a time series and infer the metric name when omitted."""

        observation_tuple = tuple(observations)
        resolved_metric_name = metric_name
        if resolved_metric_name is None:
            if not observation_tuple:
                raise ValueError("metric_name is required for an empty MetricTimeSeries")
            resolved_metric_name = observation_tuple[0].metric_name

        return cls(
            metric_name=resolved_metric_name,
            observations=observation_tuple,
            metadata={} if metadata is None else metadata,
        )

    def __iter__(self) -> Iterator[MetricObservation]:
        return iter(self.observations)

    def __len__(self) -> int:
        return len(self.observations)

    @property
    def dates(self) -> tuple[date, ...]:
        """Observation dates in stored order."""

        return tuple(observation.date for observation in self.observations)

    @property
    def time_buckets(self) -> tuple[time | str | None, ...]:
        """Observation time buckets in stored order."""

        return tuple(observation.time_bucket for observation in self.observations)

    @property
    def values(self) -> tuple[float | int | None, ...]:
        """Observation values in stored order."""

        return tuple(observation.value for observation in self.observations)


@dataclass(frozen=True)
class MetricComparison:
    """Current metric observation compared against a reference.

    Z-score related fields are optional because some valid comparisons, such as
    previous-day comparisons or short reference windows, do not have enough
    repeated comparable observations for a reliable statistical score.
    """

    metric_name: str
    value: float | int | None
    reference_value: float | int | None
    change_abs: float | None
    change_pct: float | None
    z_score: float | None
    percentile: float | None
    status: str
    group: dict[str, str] = field(default_factory=dict)
    date: date | None = None
    time_bucket: time | str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    reference_sample_size: int | None = None
    comparison_confidence: str | None = None
    comparison_method: str | None = None
    normal_score_percentile: float | None = None
    normal_score_adverse_tail_probability: float | None = None
    empirical_percentile: float | None = None
    empirical_adverse_tail_probability: float | None = None
    range_position_score: float | None = None
