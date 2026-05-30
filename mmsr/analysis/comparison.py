"""Reference comparison utilities.

The comparison engine treats z-scores as optional anomaly diagnostics over a
reference distribution made from repeated, comparable aggregated observations.
For daily reports, the usual observation unit is one trading day. For intraday
views, this means one value per ``date x time_bucket x group x metric`` before
comparing the current value with the historical values for the same keys.

Do not calculate statistical scores from raw quote/trade ticks unless the caller
has deliberately configured a different reference observation unit. Quote and
trade observations are highly autocorrelated, so raw tick counts should not be
mistaken for independent sample size.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, time
from math import erf, floor, sqrt
from statistics import mean, median
from typing import Any

from mmsr.metrics.results import (
    MetricComparison,
    MetricObservation,
    MetricTimeSeries,
)

REVERSION_METRIC_PREFIX = "primary_quote_reversion_"
REVERSION_REFERENCE_COMPARABLE_KEYS: tuple[str, ...] = (
    "metric_name",
    "time_bucket",
    "venue",
    "horizon",
    "group",
)


@dataclass(frozen=True)
class ReferenceObservationSpec:
    """How reference distributions are formed before scoring.

    ``observation_unit`` is usually ``trading_day``. The comparison engine should
    first aggregate raw observations to one value per observation unit and per
    comparable key. For example, quoted spread should usually be aggregated to one
    median value per ``date x time_bucket x market_cap_bucket`` before scoring.
    """

    observation_unit: str = "trading_day"
    comparable_keys: tuple[str, ...] = (
        "metric_name",
        "time_bucket",
        "group",
    )

    def __post_init__(self) -> None:
        if not self.observation_unit:
            raise ValueError("observation_unit must be non-empty")
        if not self.comparable_keys:
            raise ValueError("comparable_keys must contain at least one key")


@dataclass(frozen=True)
class ComparisonPolicy:
    """Policy controlling which comparison statistics are considered reliable."""

    reference_observation: ReferenceObservationSpec = field(default_factory=ReferenceObservationSpec)
    min_samples_for_z_score: int = 30
    min_samples_for_empirical_percentile: int = 10
    min_samples_for_range_score: int = 2
    fallback_when_insufficient: str = "change_only"
    range_lower_percentile: float = 5.0
    range_upper_percentile: float = 95.0

    def __post_init__(self) -> None:
        if self.min_samples_for_z_score < 2:
            raise ValueError("min_samples_for_z_score must be at least 2")
        if self.min_samples_for_empirical_percentile < 1:
            raise ValueError("min_samples_for_empirical_percentile must be positive")
        if self.min_samples_for_range_score < 2:
            raise ValueError("min_samples_for_range_score must be at least 2")
        if not 0 <= self.range_lower_percentile < self.range_upper_percentile <= 100:
            raise ValueError("range percentiles must satisfy 0 <= lower < upper <= 100")


@dataclass(frozen=True)
class ReferenceStats:
    """Summary of a comparable historical reference distribution."""

    reference_value: float | None
    z_score: float | None
    sample_size: int
    method: str
    confidence: str
    reference_mean: float | None = None
    reference_std: float | None = None
    reference_median: float | None = None
    reference_min: float | None = None
    reference_max: float | None = None
    reference_p5: float | None = None
    reference_p95: float | None = None
    empirical_percentile: float | None = None
    empirical_adverse_tail_probability: float | None = None
    normal_score_percentile: float | None = None
    normal_score_adverse_tail_probability: float | None = None
    range_position_score: float | None = None
    message: str | None = None


def _clean_values(values: list[float | int | None]) -> list[float]:
    return [float(value) for value in values if value is not None]


def _sample_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    mu = mean(values)
    variance = sum((value - mu) ** 2 for value in values) / (len(values) - 1)
    return sqrt(variance)


def _normal_cdf(z_score: float) -> float:
    return 0.5 * (1.0 + erf(z_score / sqrt(2.0)))


def _percentile_value(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (percentile / 100.0) * (len(ordered) - 1)
    lower_index = floor(rank)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = rank - lower_index
    return ordered[lower_index] * (1.0 - weight) + ordered[upper_index] * weight


def _empirical_percentile(value: float, reference_values: list[float]) -> float:
    return sum(item <= value for item in reference_values) / len(reference_values)


def _adverse_tail_from_values(
    value: float,
    reference_values: list[float],
    *,
    higher_is_better: bool | None,
) -> float:
    if higher_is_better is False:
        return sum(item >= value for item in reference_values) / len(reference_values)
    if higher_is_better is True:
        return sum(item <= value for item in reference_values) / len(reference_values)

    med = median(reference_values)
    distance = abs(value - med)
    return sum(abs(item - med) >= distance for item in reference_values) / len(reference_values)


def _adverse_tail_from_z(
    z_score: float,
    *,
    higher_is_better: bool | None,
) -> float:
    cdf = _normal_cdf(z_score)
    if higher_is_better is False:
        return 1.0 - cdf
    if higher_is_better is True:
        return cdf
    return 2.0 * min(cdf, 1.0 - cdf)


def _range_position_score(
    value: float,
    reference_values: list[float],
    *,
    lower_percentile: float,
    upper_percentile: float,
) -> tuple[float | None, float | None, float | None]:
    lower = _percentile_value(reference_values, lower_percentile)
    upper = _percentile_value(reference_values, upper_percentile)
    if lower is None or upper is None or lower == upper:
        return None, lower, upper
    return 100.0 * (value - lower) / (upper - lower), lower, upper


def _sample_confidence(sample_size: int, policy: ComparisonPolicy) -> str:
    if sample_size < policy.min_samples_for_empirical_percentile:
        return "insufficient"
    if sample_size < policy.min_samples_for_z_score:
        return "weak"
    return "normal"


def standard_reference_stats(
    value: float | int | None,
    reference_values: list[float | int | None],
    *,
    min_sample_size: int = 30,
) -> ReferenceStats:
    """Calculate a standard z-score from comparable historical aggregates.

    The formula is ``(current - mean(reference_values)) / std(reference_values)``.
    The default minimum sample size is 30 comparable observations. Pass a lower
    threshold only for low-level formula tests or explicitly labelled diagnostics.
    """
    values = _clean_values(reference_values)
    ref_mean = mean(values) if values else None
    ref_median = median(values) if values else None
    ref_std = _sample_std(values)
    confidence = "normal" if len(values) >= min_sample_size else "weak" if len(values) >= 2 else "insufficient"
    if value is None or len(values) < min_sample_size or ref_std in (None, 0):
        message = (
            "insufficient reference history for standard z-score"
            if len(values) < min_sample_size
            else "zero reference dispersion"
        )
        return ReferenceStats(
            reference_value=ref_mean,
            z_score=None,
            sample_size=len(values),
            method="standard",
            confidence=confidence,
            reference_mean=ref_mean,
            reference_std=ref_std,
            reference_median=ref_median,
            reference_min=min(values) if values else None,
            reference_max=max(values) if values else None,
            message=message,
        )

    z_score = (float(value) - ref_mean) / ref_std
    return ReferenceStats(
        reference_value=ref_mean,
        z_score=z_score,
        sample_size=len(values),
        method="standard",
        confidence=confidence,
        reference_mean=ref_mean,
        reference_std=ref_std,
        reference_median=ref_median,
        reference_min=min(values),
        reference_max=max(values),
    )


def robust_reference_stats(
    value: float | int | None,
    reference_values: list[float | int | None],
    *,
    min_sample_size: int = 30,
) -> ReferenceStats:
    """Calculate a robust z-score using median and scaled MAD.

    The formula is ``(current - median(reference_values)) / (1.4826 * MAD)``.
    The default minimum sample size is 30 comparable observations. For smaller
    reference windows, report empirical rank/range instead of treating the robust
    z-score as a reliable headline statistic.
    """
    values = _clean_values(reference_values)
    ref_median = median(values) if values else None
    ref_mean = mean(values) if values else None
    ref_std = _sample_std(values)
    confidence = "normal" if len(values) >= min_sample_size else "weak" if len(values) >= 2 else "insufficient"
    if value is None or len(values) < min_sample_size:
        return ReferenceStats(
            reference_value=ref_median,
            z_score=None,
            sample_size=len(values),
            method="robust",
            confidence=confidence,
            reference_mean=ref_mean,
            reference_std=ref_std,
            reference_median=ref_median,
            reference_min=min(values) if values else None,
            reference_max=max(values) if values else None,
            message="insufficient reference history for robust z-score",
        )

    med = median(values)
    mad = median([abs(item - med) for item in values])
    scaled_mad = 1.4826 * mad
    if scaled_mad == 0:
        return ReferenceStats(
            reference_value=med,
            z_score=None,
            sample_size=len(values),
            method="robust",
            confidence=confidence,
            reference_mean=ref_mean,
            reference_std=ref_std,
            reference_median=med,
            reference_min=min(values),
            reference_max=max(values),
            message="zero robust reference dispersion",
        )

    return ReferenceStats(
        reference_value=med,
        z_score=(float(value) - med) / scaled_mad,
        sample_size=len(values),
        method="robust",
        confidence=confidence,
        reference_mean=ref_mean,
        reference_std=ref_std,
        reference_median=med,
        reference_min=min(values),
        reference_max=max(values),
    )


def reference_distribution_stats(
    value: float | int | None,
    reference_values: list[float | int | None],
    *,
    method: str = "robust",
    higher_is_better: bool | None = None,
    policy: ComparisonPolicy | None = None,
) -> ReferenceStats:
    """Build user-facing and diagnostic statistics for one comparison.

    This is the preferred entry point. It calculates z-scores only when the policy
    minimum sample size is met. For smaller samples, it falls back to comparison
    facts such as current-vs-reference, empirical rank, and range position.
    """
    policy = policy or ComparisonPolicy()
    values = _clean_values(reference_values)
    current = None if value is None else float(value)

    if method == "standard":
        stats = standard_reference_stats(value, reference_values, min_sample_size=policy.min_samples_for_z_score)
    elif method == "robust":
        stats = robust_reference_stats(value, reference_values, min_sample_size=policy.min_samples_for_z_score)
    else:
        raise ValueError("method must be 'standard' or 'robust'")

    confidence = _sample_confidence(len(values), policy)
    empirical_pct = None
    empirical_tail = None
    range_score = None
    p5 = _percentile_value(values, policy.range_lower_percentile) if values else None
    p95 = _percentile_value(values, policy.range_upper_percentile) if values else None

    if current is not None and values and len(values) >= policy.min_samples_for_empirical_percentile:
        empirical_pct = _empirical_percentile(current, values)
        empirical_tail = _adverse_tail_from_values(current, values, higher_is_better=higher_is_better)

    if current is not None and len(values) >= policy.min_samples_for_range_score:
        range_score, p5, p95 = _range_position_score(
            current,
            values,
            lower_percentile=policy.range_lower_percentile,
            upper_percentile=policy.range_upper_percentile,
        )

    normal_pct = None
    normal_tail = None
    if stats.z_score is not None:
        normal_pct = _normal_cdf(stats.z_score)
        normal_tail = _adverse_tail_from_z(stats.z_score, higher_is_better=higher_is_better)

    message = stats.message
    if len(values) == 1:
        message = "comparison only: one reference observation, so z-score is undefined"
    elif len(values) < policy.min_samples_for_z_score:
        message = (
            f"low-confidence comparison: {len(values)} reference observations; "
            f"{policy.min_samples_for_z_score} required for headline z-score"
        )

    return ReferenceStats(
        reference_value=stats.reference_value,
        z_score=stats.z_score,
        sample_size=len(values),
        method=stats.method,
        confidence=confidence,
        reference_mean=stats.reference_mean,
        reference_std=stats.reference_std,
        reference_median=stats.reference_median,
        reference_min=min(values) if values else None,
        reference_max=max(values) if values else None,
        reference_p5=p5,
        reference_p95=p95,
        empirical_percentile=empirical_pct,
        empirical_adverse_tail_probability=empirical_tail,
        normal_score_percentile=normal_pct,
        normal_score_adverse_tail_probability=normal_tail,
        range_position_score=range_score,
        message=message,
    )


def compare_scalar(
    metric_name: str,
    value: float | None,
    reference_value: float | None,
    z_score: float | None = None,
    percentile: float | None = None,
    group: dict[str, str] | None = None,
    *,
    date: date | None = None,
    time_bucket: time | str | None = None,
    metadata: dict[str, Any] | None = None,
    reference_sample_size: int | None = None,
    comparison_confidence: str | None = None,
    comparison_method: str | None = None,
    normal_score_percentile: float | None = None,
    normal_score_adverse_tail_probability: float | None = None,
    empirical_percentile: float | None = None,
    empirical_adverse_tail_probability: float | None = None,
    range_position_score: float | None = None,
) -> MetricComparison:
    """Compare one scalar value against one reference value."""
    change_abs: float | None = None
    change_pct: float | None = None
    if value is not None and reference_value is not None:
        change_abs = value - reference_value
        if reference_value != 0:
            change_pct = change_abs / reference_value

    status = "normal"
    tail = normal_score_adverse_tail_probability or empirical_adverse_tail_probability
    if comparison_confidence == "insufficient" and z_score is None:
        status = "comparison_only"
    elif tail is not None:
        if tail <= 0.025:
            status = "alert"
        elif tail <= 0.10:
            status = "watch"
    elif z_score is not None:
        if abs(z_score) >= 2.0:
            status = "alert"
        elif abs(z_score) >= 1.5:
            status = "watch"

    return MetricComparison(
        metric_name=metric_name,
        value=value,
        reference_value=reference_value,
        change_abs=change_abs,
        change_pct=change_pct,
        z_score=z_score,
        percentile=percentile,
        status=status,
        group=group or {},
        date=date,
        time_bucket=time_bucket,
        metadata=metadata or {},
        reference_sample_size=reference_sample_size,
        comparison_confidence=comparison_confidence,
        comparison_method=comparison_method,
        normal_score_percentile=normal_score_percentile,
        normal_score_adverse_tail_probability=normal_score_adverse_tail_probability,
        empirical_percentile=empirical_percentile,
        empirical_adverse_tail_probability=empirical_adverse_tail_probability,
        range_position_score=range_position_score,
    )


def compare_to_reference_distribution(
    metric_name: str,
    value: float | None,
    reference_values: list[float | int | None],
    *,
    method: str = "robust",
    percentile: float | None = None,
    group: dict[str, str] | None = None,
    date: date | None = None,
    time_bucket: time | str | None = None,
    metadata: dict[str, Any] | None = None,
    higher_is_better: bool | None = None,
    policy: ComparisonPolicy | None = None,
) -> MetricComparison:
    """Compare a current value to a comparable reference distribution."""
    stats = reference_distribution_stats(
        value,
        reference_values,
        method=method,
        higher_is_better=higher_is_better,
        policy=policy,
    )
    display_percentile = percentile if percentile is not None else stats.empirical_percentile

    return compare_scalar(
        metric_name=metric_name,
        value=value,
        reference_value=stats.reference_value,
        z_score=stats.z_score,
        percentile=display_percentile,
        group=group,
        date=date,
        time_bucket=time_bucket,
        metadata=metadata,
        reference_sample_size=stats.sample_size,
        comparison_confidence=stats.confidence,
        comparison_method=stats.method,
        normal_score_percentile=stats.normal_score_percentile,
        normal_score_adverse_tail_probability=stats.normal_score_adverse_tail_probability,
        empirical_percentile=stats.empirical_percentile,
        empirical_adverse_tail_probability=stats.empirical_adverse_tail_probability,
        range_position_score=stats.range_position_score,
    )


def _observation_unit_key(
    observation: MetricObservation,
    policy: ComparisonPolicy,
) -> Hashable:
    """Return the reference observation-unit key for one normalized observation."""
    unit = policy.reference_observation.observation_unit
    if unit == "trading_day":
        return observation.date
    return _observation_field(observation, unit)


def _observation_field(observation: MetricObservation, name: str) -> Hashable:
    """Extract a top-level, group, or metadata field for comparison grouping."""
    if name == "metric_name":
        return observation.metric_name
    if name == "date":
        return observation.date
    if name == "time_bucket":
        return observation.time_bucket
    if name == "group":
        return tuple(sorted(observation.group.items()))
    if name == "value":
        return observation.value
    if name in observation.group:
        return observation.group[name]
    if name in observation.metadata:
        value = observation.metadata[name]
        if not isinstance(value, Hashable):
            raise ValueError(f"metadata field is not hashable: {name}")
        return value
    raise ValueError(f"observation does not contain comparable key: {name}")


def _comparison_key(
    observation: MetricObservation,
    policy: ComparisonPolicy,
) -> tuple[Hashable, ...]:
    """Return the comparable-history key for one normalized observation."""
    return tuple(_observation_field(observation, key) for key in policy.reference_observation.comparable_keys)


def _aggregate_observation_values(
    values: Sequence[float | int | None],
    *,
    aggregation: str,
) -> float | None:
    """Aggregate duplicate rows within one reference observation unit.

    The comparison engine counts observation units, not raw rows. If multiple
    normalized rows are supplied for the same comparable key and trading day, they
    are folded into one deterministic value before the reference distribution is
    scored.
    """
    cleaned = _clean_values(list(values))
    if not cleaned:
        return None
    if aggregation == "mean":
        return mean(cleaned)
    if aggregation == "median":
        return median(cleaned)
    if aggregation == "sum":
        return sum(cleaned)
    if aggregation == "first":
        return cleaned[0]
    if aggregation == "last":
        return cleaned[-1]
    raise ValueError("reference_observation_aggregation must be one of 'mean', 'median', 'sum', 'first', or 'last'")


def _sorted_reference_units(
    reference_by_unit: Mapping[Hashable, Sequence[float | int | None]],
) -> list[Hashable]:
    """Sort reference observation-unit keys deterministically."""
    return sorted(reference_by_unit, key=lambda item: repr(item))


def compare_metric_timeseries(
    current_observations: Sequence[MetricObservation],
    reference_observations: Sequence[MetricObservation],
    *,
    method: str = "robust",
    metric_directions: Mapping[str, bool | None] | None = None,
    policy: ComparisonPolicy | None = None,
    reference_observation_aggregation: str = "mean",
) -> list[MetricComparison]:
    """Compare normalized metric observations against comparable history.

    Current and reference rows are matched using
    ``policy.reference_observation.comparable_keys``. The default key is
    ``metric_name x time_bucket x group``. Reference rows are then collapsed to
    one value per reference observation unit, which defaults to one trading day,
    before percentile and z-score diagnostics are calculated.

    This keeps raw row counts from being mistaken for independent reference
    sample sizes and gives each current observation a comparison built from the
    same metric, bucket, venue/horizon/report group, and other configured keys.
    """
    policy = policy or ComparisonPolicy()
    directions = metric_directions or {}

    reference_index: dict[
        tuple[Hashable, ...],
        dict[Hashable, list[float | int | None]],
    ] = {}
    for observation in reference_observations:
        key = _comparison_key(observation, policy)
        unit = _observation_unit_key(observation, policy)
        reference_index.setdefault(key, {}).setdefault(unit, []).append(observation.value)

    comparisons: list[MetricComparison] = []
    for observation in current_observations:
        key = _comparison_key(observation, policy)
        reference_by_unit = reference_index.get(key, {})
        reference_values = [
            _aggregate_observation_values(
                reference_by_unit[unit],
                aggregation=reference_observation_aggregation,
            )
            for unit in _sorted_reference_units(reference_by_unit)
        ]

        comparisons.append(
            compare_to_reference_distribution(
                metric_name=observation.metric_name,
                value=observation.value,
                reference_values=reference_values,
                method=method,
                group=observation.group,
                date=observation.date,
                time_bucket=observation.time_bucket,
                metadata={
                    **observation.metadata,
                    "reference_observation_unit": (policy.reference_observation.observation_unit),
                    "reference_observation_aggregation": (reference_observation_aggregation),
                },
                higher_is_better=directions.get(observation.metric_name),
                policy=policy,
            )
        )

    return comparisons


def compare_reversion_metric_timeseries(
    current_series: MetricTimeSeries | Iterable[MetricTimeSeries],
    reference_series: MetricTimeSeries | Iterable[MetricTimeSeries],
    *,
    method: str = "robust",
    policy: ComparisonPolicy | None = None,
    reference_observation_aggregation: str = "mean",
) -> tuple[MetricComparison, ...]:
    """Compare primary-quote reversion results by venue and horizon.

    Reversion metrics are direction-aware: positive values mean the primary mid
    moved in the aggressive trade direction, so higher values are worse. This
    wrapper therefore always passes ``higher_is_better=False`` for the reversion
    metric family and uses comparable keys that keep venue, horizon, intraday
    bucket, and any remaining report group dimensions separate.
    """

    current_observations = _observations_from_series_input(current_series)
    reference_observations = _observations_from_series_input(reference_series)
    _validate_reversion_observations(current_observations)
    _validate_reversion_observations(reference_observations)

    comparison_policy = policy or ComparisonPolicy(
        reference_observation=ReferenceObservationSpec(comparable_keys=REVERSION_REFERENCE_COMPARABLE_KEYS)
    )
    metric_names = {observation.metric_name for observation in (*current_observations, *reference_observations)}

    return tuple(
        compare_metric_timeseries(
            current_observations,
            reference_observations,
            method=method,
            metric_directions={metric_name: False for metric_name in metric_names},
            policy=comparison_policy,
            reference_observation_aggregation=reference_observation_aggregation,
        )
    )


def _observations_from_series_input(
    series_input: MetricTimeSeries | Iterable[MetricTimeSeries],
) -> tuple[MetricObservation, ...]:
    if isinstance(series_input, MetricTimeSeries):
        return series_input.observations

    observations: list[MetricObservation] = []
    for series in series_input:
        observations.extend(series.observations)
    return tuple(observations)


def _validate_reversion_observations(
    observations: Sequence[MetricObservation],
) -> None:
    for observation in observations:
        if not observation.metric_name.startswith(REVERSION_METRIC_PREFIX):
            raise ValueError(
                "compare_reversion_metric_timeseries only accepts metrics whose "
                f"name starts with {REVERSION_METRIC_PREFIX!r}"
            )
        for group_key in ("venue", "horizon"):
            value = observation.group.get(group_key)
            if value is None or not str(value):
                raise ValueError(f"reversion comparison observations must include group {group_key!r}")
