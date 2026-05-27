"""Configuration models for report generation."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_DURATION_RE = re.compile(r"^[1-9][0-9]*(?:ms|s|m|h)$")
_Q_NAMESPACE_RE = re.compile(
    r"^\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$"
)
_Q_FUNCTION_RE = re.compile(
    r"^(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*|"
    r"[A-Za-z_][A-Za-z0-9_]*)$"
)
_REVERSION_METRIC_RE = re.compile(
    r"^primary_quote_reversion_(?:[1-9][0-9]*(?:ms|s|m|h))_bps$"
)


def _validate_duration(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _DURATION_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must be a duration such as '10ms', '100ms', or '1s'"
        )


def _validate_q_namespace(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _Q_NAMESPACE_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must be a q namespace such as '.mmsr' or '.sb.mmsr'"
        )


def _validate_q_function(value: str, field_name: str) -> None:
    if not isinstance(value, str) or _Q_FUNCTION_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must be a q function name such as 'getTrade' "
            "or '.sb.mmsr.getTrade'"
        )


def _qualified_q_function(namespace: str, function_name: str, field_name: str) -> str:
    _validate_q_function(function_name, field_name)
    if function_name.startswith("."):
        return function_name
    return f"{namespace}.{function_name}"


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
    """Trading calendar function configuration.

    Production report runs should use a user-owned kdb calendar function so
    holidays, half days, emergency closures, and exchange-specific sessions come
    from a controlled data source instead of weekday assumptions.
    """

    source: str = "kdb"
    namespace: str = ".mmsr"
    function: str = "getTradingCalendar"
    date_column: str = "date"

    def __post_init__(self) -> None:
        _validate_q_namespace(self.namespace, "calendar.namespace")
        _validate_q_function(self.function, "calendar.function")
        if not isinstance(self.date_column, str) or not self.date_column:
            raise ValueError("calendar.date_column must be a non-empty string")

    def qualified_function(self) -> str:
        """Return the configured calendar function as a fully-qualified q name."""

        return _qualified_q_function(
            self.namespace,
            self.function,
            "calendar.function",
        )


@dataclass(frozen=True)
class SymbolUniverseConfig:
    """Symbol-universe function configuration.

    Production report runs should use a user-owned kdb function to decide which
    symbols are in scope for each trading day. The raw trade/quote functions then
    receive only ``date`` and the selected ``syms`` vector.
    """

    source: str = "kdb"
    namespace: str = ".mmsr"
    function: str = "getSymbols"
    symbol_column: str = "sym"

    def __post_init__(self) -> None:
        _validate_q_namespace(self.namespace, "symbols.namespace")
        _validate_q_function(self.function, "symbols.function")
        if not isinstance(self.symbol_column, str) or not self.symbol_column:
            raise ValueError("symbols.symbol_column must be a non-empty string")

    def qualified_function(self) -> str:
        """Return the configured symbol-universe function as a qualified q name."""

        return _qualified_q_function(
            self.namespace,
            self.function,
            "symbols.function",
        )


@dataclass(frozen=True)
class ReferenceDataConfig:
    """Reference-data function configuration.

    The user-owned reference function returns day-specific symbol metadata such
    as TOPIX grouping, market-cap bucket, and lot size. MMSR q templates join
    this table to raw trade/quote rows inside kdb before calculating grouped
    metrics.
    """

    source: str = "kdb"
    namespace: str = ".mmsr"
    function: str = "getRef"
    symbol_column: str = "sym"

    def __post_init__(self) -> None:
        _validate_q_namespace(self.namespace, "reference_data.namespace")
        _validate_q_function(self.function, "reference_data.function")
        if not isinstance(self.symbol_column, str) or not self.symbol_column:
            raise ValueError("reference_data.symbol_column must be a non-empty string")

    def qualified_function(self) -> str:
        """Return the configured reference-data function as a qualified q name."""

        return _qualified_q_function(
            self.namespace,
            self.function,
            "reference_data.function",
        )


@dataclass(frozen=True)
class KdbRawDataFunctionsConfig:
    """User-defined raw data functions called by MMSR q calculations.

    These functions are the production data-access boundary. Each function must
    accept ``date`` and ``syms`` positional arguments and return a canonical raw
    table for at most the requested day/symbol slice; MMSR-owned q templates then
    calculate metrics inside the configured calculation namespace.
    """

    namespace: str = ".mmsr"
    trade: str = "getTrade"
    quote: str = "getQuote"
    venue_trade: str | None = None
    primary_quote: str | None = None
    reference_data: str = "getRef"

    def __post_init__(self) -> None:
        _validate_q_namespace(self.namespace, "raw_data_functions.namespace")
        _validate_q_function(self.trade, "raw_data_functions.trade")
        _validate_q_function(self.quote, "raw_data_functions.quote")
        if self.venue_trade is not None:
            _validate_q_function(
                self.venue_trade,
                "raw_data_functions.venue_trade",
            )
        if self.primary_quote is not None:
            _validate_q_function(
                self.primary_quote,
                "raw_data_functions.primary_quote",
            )
        _validate_q_function(
            self.reference_data,
            "raw_data_functions.reference_data",
        )

    def to_source_functions(self) -> dict[str, str]:
        """Return source-function names keyed by logical template source role."""

        venue_trade = self.trade if self.venue_trade is None else self.venue_trade
        primary_quote = self.quote if self.primary_quote is None else self.primary_quote
        return {
            "trades": _qualified_q_function(
                self.namespace,
                self.trade,
                "raw_data_functions.trade",
            ),
            "quotes": _qualified_q_function(
                self.namespace,
                self.quote,
                "raw_data_functions.quote",
            ),
            "venue_trades": _qualified_q_function(
                self.namespace,
                venue_trade,
                "raw_data_functions.venue_trade",
            ),
            "primary_quotes": _qualified_q_function(
                self.namespace,
                primary_quote,
                "raw_data_functions.primary_quote",
            ),
            "reference_data": _qualified_q_function(
                self.namespace,
                self.reference_data,
                "raw_data_functions.reference_data",
            ),
        }


@dataclass(frozen=True)
class KdbExecutionConfig:
    """kdb execution namespace and raw source-function configuration.

    Production execution is date-bounded by default. Optional symbol chunking can
    further limit the ``syms`` vector passed to user-defined source functions
    while MMSR-owned q calculations still run inside ``calculation_namespace``.
    """

    calculation_namespace: str = ".mmsr"
    raw_data_functions: KdbRawDataFunctionsConfig = field(
        default_factory=KdbRawDataFunctionsConfig
    )
    enforce_daily_raw_scope: bool = True
    symbol_chunk_size: int | None = None

    def __post_init__(self) -> None:
        _validate_q_namespace(
            self.calculation_namespace,
            "kdb.calculation_namespace",
        )
        if self.symbol_chunk_size is not None and self.symbol_chunk_size < 1:
            raise ValueError("kdb.symbol_chunk_size must be positive when provided")

    def source_functions(self) -> dict[str, str]:
        """Return the configured raw data source-function mapping."""

        return self.raw_data_functions.to_source_functions()


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
    symbols: SymbolUniverseConfig = field(default_factory=SymbolUniverseConfig)
    reference_data: ReferenceDataConfig = field(default_factory=ReferenceDataConfig)
    intraday: IntradayConfig = field(default_factory=IntradayConfig)
    reference: ReferenceComparisonConfig = field(
        default_factory=ReferenceComparisonConfig
    )
    toxicity: ToxicityConfig = field(default_factory=ToxicityConfig)
    kdb: KdbExecutionConfig = field(default_factory=KdbExecutionConfig)

    def metric_parameters_for(self, metric_name: str) -> dict[str, Any]:
        """Return metric-family parameters for a configured metric run."""

        if _REVERSION_METRIC_RE.fullmatch(metric_name) is not None:
            return self.toxicity.to_metric_run_parameters()
        return {}
