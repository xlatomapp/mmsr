"""YAML configuration loading helpers for production CLI commands."""

from __future__ import annotations

from datetime import date, time
from pathlib import Path
from typing import Any, Mapping

import yaml

from mmsr.config.models import (
    AuctionBucketConfig,
    BrandingConfig,
    CalendarConfig,
    HtmlTemplateConfig,
    IntradayConfig,
    KdbExecutionConfig,
    KdbRawDataFunctionsConfig,
    ReferenceComparisonConfig,
    ReferenceDataConfig,
    ReportConfig,
    SymbolUniverseConfig,
    ToxicityConfig,
    ToxicityConfidenceConfig,
    ToxicityEventClusteringConfig,
    ToxicityFiltersConfig,
    ToxicityVisualConfig,
)
from mmsr.periods.models import IntradayBucketSpec, ReportPeriod, TradingSession


class ConfigLoadError(ValueError):
    """Raised when a report YAML file cannot be loaded into typed config."""


def load_report_config_file(path: str | Path) -> tuple[ReportConfig, ReportPeriod]:
    """Load typed report config and report period from a YAML file."""

    config_path = Path(path)
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigLoadError(f"unable to read config file: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"invalid YAML in config file: {config_path}") from exc

    if not isinstance(raw, Mapping):
        raise ConfigLoadError("config file must contain a YAML mapping")

    return report_config_from_mapping(raw), report_period_from_mapping(raw)


def report_config_from_mapping(raw: Mapping[str, Any]) -> ReportConfig:
    """Build ``ReportConfig`` from the repository YAML shape."""

    report_section = _mapping(raw.get("report", {}), "report")
    data_section = _mapping(raw.get("data", {}), "data")
    kdb_section = _mapping(data_section.get("kdb", {}), "data.kdb")
    intraday_section = _mapping(raw.get("intraday", {}), "intraday")
    reference_section = _mapping(raw.get("reference", {}), "reference")
    commentary_section = _mapping(raw.get("commentary", {}), "commentary")
    toxicity_section = _mapping(raw.get("toxicity", {}), "toxicity")
    calendar_section = _mapping(raw.get("calendar", {}), "calendar")
    reference_data_section = _mapping(raw.get("reference_data", {}), "reference_data")
    raw_functions_section = _mapping(
        kdb_section.get("raw_data_functions", {}),
        "data.kdb.raw_data_functions",
    )

    metrics = raw.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ConfigLoadError("metrics must be a non-empty list")

    groups = raw.get("groups", [])
    if not isinstance(groups, list):
        raise ConfigLoadError("groups must be a list when provided")

    return ReportConfig(
        title=str(report_section.get("title", "Japanese Market Microstructure Monitor")),
        metrics=[str(metric) for metric in metrics],
        group_by=[str(group) for group in groups],
        commentary_mode=str(commentary_section.get("mode", "template")),
        html=_html_config(report_section),
        calendar=CalendarConfig(
            source=str(calendar_section.get("source", "kdb")),
            namespace=str(calendar_section.get("namespace", ".mmsr")),
            function=str(calendar_section.get("function", "getTradingCalendar")),
            date_column=str(calendar_section.get("date_column", "date")),
        ),
        reference_data=ReferenceDataConfig(
            source=str(reference_data_section.get("source", "kdb")),
            namespace=str(
                reference_data_section.get(
                    "namespace",
                    raw_functions_section.get("namespace", ".mmsr"),
                )
            ),
            function=str(reference_data_section.get("function", "getRef")),
            symbol_column=str(reference_data_section.get("symbol_column", "sym")),
            ric_column=str(reference_data_section.get("ric_column", "ric")),
        ),
        symbols=SymbolUniverseConfig(
            source=str(reference_data_section.get("source", "kdb")),
            namespace=str(
                reference_data_section.get(
                    "namespace",
                    raw_functions_section.get("namespace", ".mmsr"),
                )
            ),
            function=str(reference_data_section.get("function", "getRef")),
            symbol_column=str(reference_data_section.get("symbol_column", "sym")),
        ),
        intraday=_intraday_config(intraday_section),
        reference=ReferenceComparisonConfig(
            method=str(reference_section.get("method", "same_intraday_bucket")),
            lookback_days=int(reference_section.get("lookback_days", 20)),
            statistic=str(reference_section.get("statistic", "median")),
            observation_unit=str(reference_section.get("observation_unit", "trading_day")),
            comparable_keys=tuple(
                str(value)
                for value in reference_section.get(
                    "comparable_keys", ["metric_name", "time_bucket", "group"]
                )
            ),
            min_samples_for_z_score=int(
                reference_section.get("min_samples_for_z_score", 30)
            ),
            min_samples_for_empirical_percentile=int(
                reference_section.get("min_samples_for_empirical_percentile", 10)
            ),
            default_user_facing_score=str(
                reference_section.get(
                    "default_user_facing_score", "empirical_percentile"
                )
            ),
            default_technical_score=str(
                reference_section.get("default_technical_score", "robust_z_score")
            ),
        ),
        toxicity=_toxicity_config(toxicity_section),
        kdb=_kdb_config(kdb_section, reference_data_section),
    )


def report_period_from_mapping(raw: Mapping[str, Any]) -> ReportPeriod:
    """Build ``ReportPeriod`` from the repository YAML shape."""

    period_section = _mapping(raw.get("period", {}), "period")
    intraday_section = _mapping(raw.get("intraday", {}), "intraday")
    sessions_raw = period_section.get("trading_sessions", [])
    if sessions_raw is None:
        sessions_raw = []
    if not isinstance(sessions_raw, list):
        raise ConfigLoadError("period.trading_sessions must be a list when provided")

    sessions: list[TradingSession] = []
    for index, session_raw in enumerate(sessions_raw):
        if (
            not isinstance(session_raw, list)
            and not isinstance(session_raw, tuple)
        ) or len(session_raw) < 2:
            raise ConfigLoadError(
                "period.trading_sessions entries must be [start, end] pairs"
            )
        sessions.append(
            TradingSession(
                start=_parse_time(str(session_raw[0]), f"period.trading_sessions[{index}][0]"),
                end=_parse_time(str(session_raw[1]), f"period.trading_sessions[{index}][1]"),
            )
        )

    return ReportPeriod(
        start_date=_parse_date(period_section.get("start_date"), "period.start_date"),
        end_date=_parse_date(period_section.get("end_date"), "period.end_date"),
        sessions=sessions,
        bucket=IntradayBucketSpec(str(intraday_section.get("bucket_size", "5m"))),
        timezone=str(period_section.get("timezone", "Asia/Tokyo")),
    )


def _html_config(report_section: Mapping[str, Any]) -> HtmlTemplateConfig:
    branding = _mapping(report_section.get("branding", {}), "report.branding")
    return HtmlTemplateConfig(
        template=str(report_section.get("template", "default")),
        custom_template_dir=_optional_string(report_section.get("custom_template_dir")),
        branding=BrandingConfig(
            brand_name=_optional_string(branding.get("brand_name")),
            logo_image_src=_optional_string(branding.get("logo_image_src")),
            header_image_src=_optional_string(branding.get("header_image_src")),
            footer_image_src=_optional_string(branding.get("footer_image_src")),
            footer_text=_optional_string(branding.get("footer_text")),
        ),
    )


def _intraday_config(section: Mapping[str, Any]) -> IntradayConfig:
    auction = _mapping(section.get("auction_buckets", {}), "intraday.auction_buckets")
    labels = _mapping(auction.get("labels", {}), "intraday.auction_buckets.labels")
    return IntradayConfig(
        bucket_size=str(section.get("bucket_size", "5m")),
        align_to_session=bool(section.get("align_to_session", True)),
        auction_buckets=AuctionBucketConfig(
            enabled=bool(auction.get("enabled", True)),
            morning_open=str(labels.get("morning_open", "AMO")),
            morning_close=str(labels.get("morning_close", "AMC")),
            afternoon_open=str(labels.get("afternoon_open", "PMO")),
            afternoon_close=str(labels.get("afternoon_close", "PMC")),
        ),
    )


def _kdb_config(
    section: Mapping[str, Any],
    reference_data_section: Mapping[str, Any] | None = None,
) -> KdbExecutionConfig:
    raw_functions = _mapping(
        section.get("raw_data_functions", {}), "data.kdb.raw_data_functions"
    )
    reference_data_section = reference_data_section or {}
    reference_function = raw_functions.get(
        "reference_data", reference_data_section.get("function", "getRef")
    )
    return KdbExecutionConfig(
        calculation_namespace=str(section.get("calculation_namespace", ".mmsr")),
        raw_data_functions=KdbRawDataFunctionsConfig(
            namespace=str(raw_functions.get("namespace", ".mmsr")),
            trade=str(raw_functions.get("trade", "getTrade")),
            quote=str(raw_functions.get("quote", "getQuote")),
            pts_trade=_optional_string(raw_functions.get("pts_trade")),
            pts_quote=_optional_string(raw_functions.get("pts_quote")),
            primary_quote=_optional_string(raw_functions.get("primary_quote")),
            reference_data=str(reference_function),
            venue_trade=_optional_string(raw_functions.get("venue_trade")),
            venue_quote=_optional_string(raw_functions.get("venue_quote")),
        ),
        enforce_daily_raw_scope=bool(section.get("enforce_daily_raw_scope", True)),
        symbol_chunk_size=(
            None
            if section.get("symbol_chunk_size") is None
            else int(section["symbol_chunk_size"])
        ),
        symbol_chunk_group_by=_string_sequence(
            section.get("symbol_chunk_group_by", ["sym"]),
            "data.kdb.symbol_chunk_group_by",
        ),
        aggregation_levels=_string_sequence(
            section.get(
                "aggregation_levels",
                [
                    "market",
                    "market_bucket",
                    "topix_cap_group",
                    "topix_cap_group_bucket",
                ],
            ),
            "data.kdb.aggregation_levels",
        ),
    )


def _toxicity_config(section: Mapping[str, Any]) -> ToxicityConfig:
    visual = _mapping(section.get("default_visual", {}), "toxicity.default_visual")
    clustering = _mapping(section.get("event_clustering", {}), "toxicity.event_clustering")
    filters = _mapping(section.get("filters", {}), "toxicity.filters")
    confidence = _mapping(section.get("confidence", {}), "toxicity.confidence")
    return ToxicityConfig(
        enabled=bool(section.get("enabled", True)),
        section_title=str(section.get("section_title", "Cross-Venue Toxicity")),
        primary_venue=str(section.get("primary_venue", "TSE")),
        venues=(
            None
            if "venues" not in section or section.get("venues") is None
            else tuple(str(value) for value in section["venues"])
        ),
        reversion_horizons=tuple(
            str(value)
            for value in section.get(
                "reversion_horizons",
                ["10ms", "100ms", "500ms", "1s", "5s", "10s"],
            )
        ),
        default_visual=ToxicityVisualConfig(
            type=str(visual.get("type", "venue_reversion_curve")),
            x_axis=str(visual.get("x_axis", "horizon")),
            y_axis=str(visual.get("y_axis", "reversion_bps")),
            series=str(visual.get("series", "venue")),
        ),
        side_source=str(section.get("side_source", "inferred")),
        event_clustering=ToxicityEventClusteringConfig(
            enabled=bool(clustering.get("enabled", True)),
            window=str(clustering.get("window", "100ms")),
        ),
        filters=ToxicityFiltersConfig(
            exclude_auction=bool(filters.get("exclude_auction", True)),
            exclude_stale_primary_quote=bool(filters.get("exclude_stale_primary_quote", True)),
            max_primary_quote_age=str(filters.get("max_primary_quote_age", "1s")),
            max_pts_quote_age=_optional_string(filters.get("max_pts_quote_age")),
        ),
        confidence=ToxicityConfidenceConfig(
            min_trade_count=int(confidence.get("min_trade_count", 100)),
            min_notional=float(confidence.get("min_notional", 100_000_000.0)),
        ),
    )


def _mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ConfigLoadError(f"{field_name} must be a mapping")
    return value


def _string_sequence(value: Any, field_name: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigLoadError(f"{field_name} must be a list of strings")
    result = tuple(str(item) for item in value)
    if any(not item for item in result):
        raise ConfigLoadError(f"{field_name} must contain only non-empty strings")
    return result


def _parse_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ConfigLoadError(f"{field_name} must be an ISO date string")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ConfigLoadError(f"{field_name} must be an ISO date string") from exc


def _parse_time(value: str, field_name: str) -> time:
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ConfigLoadError(f"{field_name} must be an ISO time string") from exc


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
