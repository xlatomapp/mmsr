"""Configuration models for report generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_DURATION_RE = re.compile(r"^[1-9][0-9]*(?:ms|s|m|h)$")
_REVERSION_METRIC_RE = re.compile(
    r"^primary_quote_reversion_(?:[1-9][0-9]*(?:ms|s|m|h))_bps$"
)


def _validate_duration(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _DURATION_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must be a duration such as '10ms', '100ms', or '1s'"
        )


def _as_non_empty_tuple(
    values: tuple[str, ...] | list[str],
    field_name: str,
) -> tuple[str, ...]:
    if isinstance(values, tuple):
        result = values
    elif isinstance(values, list):
        result = tuple(values)
    else:
        raise ValueError(f"{field_name} must be a non-empty sequence of strings")

    if not result or any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    return result


@dataclass(frozen=True)
class BrandingConfig:
    """Branding values used by the HTML report template."""

    brand_name: str | None = None
    logo_image_src: str | None = None
    header_image_src: str | None = None
    footer_image_src: str | None = None
    footer_text: str | None = None


@dataclass(frozen=True)
class HtmlTemplateConfig:
    """HTML template selection and override settings."""

    template: str = "default"
    custom_template_dir: str | None = None
    branding: BrandingConfig = field(default_factory=BrandingConfig)


@dataclass(frozen=True)
class CalendarConfig:
    """Trading calendar configuration.

    Production report runs should use the kdb-backed calendar source so holidays,
    half days, emergency closures, and exchange-specific sessions come from a
    controlled data source instead of weekday assumptions.
    """

    source: str = "kdb"
    table: str = "trading_calendar"
    date_column: str = "date"
    is_trading_day_column: str = "is_trading_day"


@dataclass(frozen=True)
class AuctionBucketConfig:
    """Auction bucket labels included in the intraday grid."""

    enabled: bool = True
    morning_open: str = "AMO"
    morning_close: str = "AMC"
    afternoon_open: str = "PMO"
    afternoon_close: str = "PMC"


@dataclass(frozen=True)
class IntradayConfig:
    """Intraday bucketing configuration."""

    bucket_size: str = "5m"
    align_to_session: bool = True
    auction_buckets: AuctionBucketConfig = field(default_factory=AuctionBucketConfig)


@dataclass(frozen=True)
class ReferenceComparisonConfig:
    """Reference comparison policy.

    The default observation unit is one trading day. Statistical scores should be
    calculated after raw observations have been aggregated to one comparable
    value per observation unit and key set.
    """

    method: str = "same_intraday_bucket"
    lookback_days: int = 20
    statistic: str = "median"
    observation_unit: str = "trading_day"
    comparable_keys: tuple[str, ...] = ("metric_name", "time_bucket", "group")
    min_samples_for_z_score: int = 30
    min_samples_for_empirical_percentile: int = 10
    default_user_facing_score: str = "empirical_percentile"
    default_technical_score: str = "robust_z_score"

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


@dataclass(frozen=True)
class ToxicityVisualConfig:
    """Default visual settings for the cross-venue reversion section."""

    type: str = "venue_reversion_curve"
    x_axis: str = "horizon"
    y_axis: str = "reversion_bps"
    series: str = "venue"


@dataclass(frozen=True)
class ToxicityEventClusteringConfig:
    """Aggressive-trade event clustering settings for reversion metrics."""

    enabled: bool = True
    window: str = "100ms"

    def __post_init__(self) -> None:
        _validate_duration(self.window, "event_clustering.window")


@dataclass(frozen=True)
class ToxicityFiltersConfig:
    """Filters applied before calculating cross-venue reversion metrics."""

    exclude_auction: bool = True
    exclude_stale_primary_quote: bool = True
    max_primary_quote_age: str = "1s"

    def __post_init__(self) -> None:
        _validate_duration(self.max_primary_quote_age, "filters.max_primary_quote_age")


@dataclass(frozen=True)
class ToxicityConfidenceConfig:
    """Sample-size thresholds for flagging low-confidence reversion results."""

    min_trade_count: int = 100
    min_notional: float = 100_000_000.0

    def __post_init__(self) -> None:
        if self.min_trade_count < 1:
            raise ValueError("confidence.min_trade_count must be positive")
        if self.min_notional < 0:
            raise ValueError("confidence.min_notional must be non-negative")


@dataclass(frozen=True)
class ToxicityConfig:
    """Cross-venue toxicity/reversion report configuration."""

    enabled: bool = True
    section_title: str = "Cross-Venue Toxicity"
    primary_venue: str = "TSE"
    venues: tuple[str, ...] | list[str] = ("TSE", "SBIJ", "ODX")
    reversion_horizons: tuple[str, ...] | list[str] = (
        "10ms",
        "100ms",
        "500ms",
        "1s",
        "5s",
        "10s",
    )
    default_visual: ToxicityVisualConfig = field(default_factory=ToxicityVisualConfig)
    side_source: str = "feed"
    event_clustering: ToxicityEventClusteringConfig = field(
        default_factory=ToxicityEventClusteringConfig
    )
    filters: ToxicityFiltersConfig = field(default_factory=ToxicityFiltersConfig)
    confidence: ToxicityConfidenceConfig = field(
        default_factory=ToxicityConfidenceConfig
    )

    def __post_init__(self) -> None:
        if not self.section_title:
            raise ValueError("section_title must be non-empty")
        if not self.primary_venue:
            raise ValueError("primary_venue must be non-empty")

        venues = _as_non_empty_tuple(self.venues, "venues")
        horizons = _as_non_empty_tuple(self.reversion_horizons, "reversion_horizons")
        for horizon in horizons:
            _validate_duration(horizon, "reversion_horizons")

        if self.primary_venue not in venues:
            raise ValueError("primary_venue must be present in venues")
        if self.side_source not in {"feed", "inferred"}:
            raise ValueError("side_source must be 'feed' or 'inferred'")

        object.__setattr__(self, "venues", venues)
        object.__setattr__(self, "reversion_horizons", horizons)

    def to_metric_run_parameters(self) -> dict[str, Any]:
        """Return parameters suitable for ``MetricRunRequest.parameters``.

        The kdb runner currently consumes primary venue, venue filter, and stale
        primary-quote age. The additional fields are included so downstream
        query/rendering layers can apply confidence and filtering policy without
        reparsing report config.
        """

        return {
            "primary_venue": self.primary_venue,
            "venues": self.venues,
            "max_primary_quote_age": self.filters.max_primary_quote_age,
            "side_source": self.side_source,
            "event_clustering_enabled": self.event_clustering.enabled,
            "event_clustering_window": self.event_clustering.window,
            "exclude_auction": self.filters.exclude_auction,
            "exclude_stale_primary_quote": self.filters.exclude_stale_primary_quote,
            "min_trade_count": self.confidence.min_trade_count,
            "min_notional": self.confidence.min_notional,
        }

    def reversion_metric_names(self) -> tuple[str, ...]:
        """Return configured primary-quote reversion metric names."""

        return tuple(
            f"primary_quote_reversion_{horizon}_bps"
            for horizon in self.reversion_horizons
        )


@dataclass(frozen=True)
class ReportConfig:
    """Top-level report configuration."""

    title: str
    metrics: list[str]
    group_by: list[str] = field(default_factory=list)
    commentary_mode: str = "template"
    html: HtmlTemplateConfig = field(default_factory=HtmlTemplateConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    intraday: IntradayConfig = field(default_factory=IntradayConfig)
    reference: ReferenceComparisonConfig = field(
        default_factory=ReferenceComparisonConfig
    )
    toxicity: ToxicityConfig = field(default_factory=ToxicityConfig)

    def metric_parameters_for(self, metric_name: str) -> dict[str, Any]:
        """Return metric-family parameters for a configured metric run."""

        if _REVERSION_METRIC_RE.fullmatch(metric_name) is not None:
            return self.toxicity.to_metric_run_parameters()
        return {}
