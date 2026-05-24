"""Reference period and observation-unit configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceSpec:
    """Definition of how current observations should be compared.

    The reference observation unit defines the final aggregation level used to
    build a reference distribution. The default is one trading day, meaning raw
    observations are first aggregated to one value per day and comparable key set
    before percentile or z-score style statistics are calculated.
    """

    method: str = "same_intraday_bucket"
    lookback_days: int = 20
    statistic: str = "median"
    observation_unit: str = "trading_day"
    comparable_keys: tuple[str, ...] = ("metric_name", "time_bucket", "group")
    min_samples_for_z_score: int = 30
    min_samples_for_empirical_percentile: int = 10

    def __post_init__(self) -> None:
        if self.lookback_days <= 0:
            raise ValueError("lookback_days must be positive")
        if not self.observation_unit:
            raise ValueError("observation_unit must be non-empty")
        if not self.comparable_keys:
            raise ValueError("comparable_keys must contain at least one key")
        if self.min_samples_for_z_score < 2:
            raise ValueError("min_samples_for_z_score must be at least 2")
        if self.min_samples_for_empirical_percentile < 1:
            raise ValueError("min_samples_for_empirical_percentile must be positive")
