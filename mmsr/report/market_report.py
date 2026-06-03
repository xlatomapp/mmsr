"""Canonical production-format market monitor report assembly.

This module owns the single report-document shape used by both production
workflows and the deterministic mock-data demo. Data sources may differ, but the
report pages, component ordering, metric-help handling, and packaged Jinja
rendering path should remain shared.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from html import escape
import json
import logging
from math import isfinite, sqrt
from statistics import median

from mmsr.analysis.trends import classify_trend_from_daily_values
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.presentation.labels import format_intraday_bucket_label
from mmsr.report.components import CommentaryBlock, HtmlBlock, PlotlyChart, ReportBranding, ReportDocument, ReportPage
from mmsr.report.drilldowns import (
    DEFAULT_DRILLDOWN_GROUP_KEYS,
    DrilldownReportPageOptions,
    DrilldownSelectionOptions,
    build_drilldown_report_page,
)
from mmsr.report.metric_docs import append_metric_definitions_appendix
from mmsr.report.overview import (
    ExecutiveOverviewOptions,
    build_executive_market_overview_block,
)
from mmsr.report.sections import (
    ComparisonSectionOptions,
    build_activity_intraday_distribution_chart,
    build_comparison_metric_table,
    build_comparison_report_page,
    build_heatmap,
    build_intraday_time_bucket_chart,
    build_reference_target_intraday_profile_chart,
    build_reference_target_trend_chart,
    build_summary_activity_distribution_html_block,
    build_summary_liquidity_distribution_html_block,
)
from mmsr.report.symbols import (
    DEFAULT_SYMBOL_GROUP_KEYS,
    SymbolAnomalyPageOptions,
    SymbolDetailIndexOptions,
    SymbolDetailPageOptions,
    build_symbol_anomaly_page,
    build_symbol_detail_index_block,
    build_symbol_detail_pages,
)
from mmsr.report.toxicity import (
    DEFAULT_REVERSION_HORIZON_ORDER,
    DEFAULT_REVERSION_VENUE_ORDER,
    DEFAULT_TOXICITY_CONTEXT_RANKING,
    TOXICITY_CONTEXT_RANKINGS,
    ToxicityContextRanking,
    ToxicityReversionPageOptions,
    build_toxicity_reversion_page,
)

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketReportInput:
    """Already-normalized data required by the canonical report builder.

    Production callers are expected to populate this object from kdb-backed
    metric runner output and comparison results. The offline demo populates the
    same object from deterministic mock fixtures. The report builder deliberately
    does not know which source supplied the data.
    """

    metric_definitions: Mapping[str, MetricDefinition]
    current_series: tuple[MetricTimeSeries, ...]
    comparisons: tuple[MetricComparison, ...]
    reference_series: tuple[MetricTimeSeries, ...] = ()
    symbol_series: tuple[MetricTimeSeries, ...] = ()


@dataclass(frozen=True)
class MarketReportOptions:
    """Presentation options for the canonical market monitor report."""

    title: str = "Japanese Market Microstructure Monitor"
    subtitle: str = "Japanese Market Quantitative Analysis"
    brand_name: str | None = "mmsr"
    generated_at_text: str | None = None
    universe_label: str = "TSE"
    summary_page_title: str = "Market Summary"
    detail_page_title: str = "Intraday Detail"
    executive_overview_title: str = "Executive Market Overview"
    executive_overview_help_text: str = (
        "High-level deterministic summary of already-computed comparison "
        "results across key metrics before per-bucket diagnostics."
    )
    comparison_table_title: str = "Current versus reference"
    comparison_help_text: str = (
        "Current observations compared with comparable historical reference "
        "observations for the same metric, bucket, and group."
    )
    detail_help_text: str = (
        "Metric observations are already normalized at the report boundary. "
        "Production runs source these rows from kdb-backed metric output; mock "
        "demo runs use deterministic fixture rows with the same schema."
    )
    daily_trend_page_title: str = "Reference and Target Daily Trends"
    daily_trend_help_text: str = (
        "Daily line plots built from already-normalized reference observations "
        "followed by target-period observations. The x-axis is trading day; "
        "intraday bucket and configured group context are carried as chart "
        "series so the trend runs through the reference and target periods."
    )
    activity_distribution_page_title: str = "Activity Distribution"
    activity_distribution_help_text: str = (
        "Compact Plotly diagnostics for activity metrics. Historical intraday "
        "observations are reduced to cumulative-percent box statistics by "
        "bucket; the current period is shown as a line with circle markers; "
        "session and auction shares are shown as horizontal stacked bars."
    )
    liquidity_distribution_help_text: str = (
        "Cumulative intraday distribution for liquidity-state metrics. "
        "Select metric from the left table and universe from the bottom table."
    )
    include_pts_stats_section: bool = True
    pts_stats_title: str = "PTS Stats"
    pts_stats_help_text: str = (
        "Venue-level PTS turnover relative to TSE turnover. "
        "Each point is computed as ratio-of-sums at the selected granularity."
    )
    include_activity_distribution_page: bool = True
    activity_distribution_metric_names: tuple[str, ...] = (
        "turnover",
        "volume",
        "trade_count",
    )
    max_activity_distribution_charts: int | None = 1
    displayed_liquidity_page_title: str = "Displayed Liquidity"
    displayed_liquidity_help_text: str = (
        "Compact Plotly diagnostics for displayed liquidity metrics. Historical "
        "intraday observations are reduced to per-bucket box statistics, the "
        "current period is shown as a line with circle markers, and the largest "
        "group-level current-minus-reference deltas are shown as a capped "
        "horizontal bar chart."
    )
    include_displayed_liquidity_page: bool = True
    displayed_liquidity_metric_names: tuple[str, ...] = (
        "quoted_spread_bps",
        "top_of_book_depth",
    )
    max_displayed_liquidity_charts: int | None = 1
    max_displayed_liquidity_groups: int | None = 12
    include_daily_trend_page: bool = True
    include_intraday_heatmaps: bool = False
    summary_scope_label: str = "report scope"
    include_metric_definitions_appendix: bool = True
    max_metric_cards: int = 6
    max_comments: int = 5
    max_table_rows: int | None = 12
    max_chart_points: int | None = None
    max_heatmap_cells: int | None = None
    max_overview_metrics: int = 5
    overview_top_change_diversification: str = "metric"
    max_summary_story_charts: int = 3
    include_summary_kpi_snapshot: bool = True
    include_detailed_metric_trends_section: bool = True
    include_automated_insights: bool = False
    detailed_metric_trends_granularity: str = "daily"
    detailed_metric_trends_metric_names: tuple[str, ...] = (
        "turnover",
        "quoted_spread_bps",
        "top_of_book_depth",
        "parkinson_volatility_bps",
    )
    detailed_metric_trends_default_metric: str = "turnover"
    summary_kpi_metric_names: tuple[str, ...] = (
        "turnover",
        "quoted_spread_bps",
        "top_of_book_depth",
        "primary_quote_reversion_100ms_bps",
    )
    include_primary_intraday_signal: bool = True
    primary_intraday_signal_metric_name: str = "quoted_spread_bps"
    include_toxicity_reversion_page: bool = True
    include_toxicity_reversion_metrics_in_detail_page: bool = False
    toxicity_reversion_page_title: str = "Cross-Venue Toxicity"
    toxicity_reversion_help_text: str = (
        "Primary-quote reversion by venue and horizon. The x-axis is the "
        "configured reversion horizon, the y-axis is reversion in bps, and each "
        "line is one execution venue. Positive values indicate adverse movement "
        "in the aggressive-trade direction."
    )
    max_toxicity_reversion_charts: int | None = 1
    max_toxicity_reversion_points_per_chart: int | None = None
    toxicity_reversion_context_ranking: ToxicityContextRanking = DEFAULT_TOXICITY_CONTEXT_RANKING
    toxicity_reversion_venue_order: tuple[str, ...] = DEFAULT_REVERSION_VENUE_ORDER
    toxicity_reversion_horizon_order: tuple[str, ...] = DEFAULT_REVERSION_HORIZON_ORDER
    max_toxicity_reversion_comments: int = 5
    include_symbol_anomaly_page: bool = False
    symbol_anomaly_page_title: str = "Symbol Anomalies"
    symbol_anomaly_table_title: str = "Top symbol-level anomalies"
    symbol_anomaly_help_text: str = (
        "Symbol-level anomaly rows are selected from already-computed "
        "comparison facts. When enabled, the page shows the worst comparison per "
        "symbol using status, adverse-tail diagnostics, z-score magnitude, and "
        "absolute percentage change as deterministic ranking inputs."
    )
    max_symbol_anomalies: int = 12
    symbol_group_keys: tuple[str, ...] = DEFAULT_SYMBOL_GROUP_KEYS
    include_symbol_detail_pages: bool = False
    include_symbol_detail_index: bool = False
    symbol_detail_index_title: str = "Symbol Detail Index"
    symbol_detail_index_help_text: str = (
        "Compact navigation for emitted per-symbol detail pages. The rows are "
        "selected from already-computed symbol comparison facts and link to the "
        "matching detail page anchors in the same HTML report."
    )
    symbol_detail_page_title_template: str = "Symbol {symbol} Detail"
    symbol_detail_help_text: str = (
        "Per-symbol detail pages render existing symbol-scoped metric time "
        "series for selected anomaly symbols when explicitly enabled. Production runs should provide "
        "these rows from normalized kdb-backed metric output; the report layer "
        "does not fetch or calculate additional metrics."
    )
    max_symbol_detail_pages: int = 5
    include_drilldown_page: bool = True
    drilldown_page_title: str = "Sector, Segment, and Market-Cap Drilldowns"
    drilldown_table_title: str = "Top group-level drilldowns"
    drilldown_help_text: str = (
        "Sector, segment, and market-cap drilldown rows are selected from "
        "already-computed comparison facts. The page does not calculate new "
        "metrics, query kdb+, or call an LLM."
    )
    max_drilldown_rows: int | None = 12
    drilldown_group_keys: tuple[str, ...] = DEFAULT_DRILLDOWN_GROUP_KEYS

    def __post_init__(self) -> None:
        _require_non_empty(self.title, "title")
        _require_non_empty(self.subtitle, "subtitle")
        _require_non_empty(self.universe_label, "universe_label")
        _require_optional_non_empty(self.brand_name, "brand_name")
        _require_optional_non_empty(self.generated_at_text, "generated_at_text")
        _require_non_empty(self.summary_page_title, "summary_page_title")
        _require_non_empty(self.detail_page_title, "detail_page_title")
        _require_non_empty(self.comparison_table_title, "comparison_table_title")
        _require_non_empty(self.executive_overview_title, "executive_overview_title")
        _require_non_empty(
            self.executive_overview_help_text,
            "executive_overview_help_text",
        )
        _require_non_empty(self.comparison_help_text, "comparison_help_text")
        _require_non_empty(self.detail_help_text, "detail_help_text")
        _require_non_empty(self.daily_trend_page_title, "daily_trend_page_title")
        _require_non_empty(self.daily_trend_help_text, "daily_trend_help_text")
        _require_non_empty(
            self.activity_distribution_page_title,
            "activity_distribution_page_title",
        )
        _require_non_empty(
            self.activity_distribution_help_text,
            "activity_distribution_help_text",
        )
        _require_metric_name_sequence(
            self.activity_distribution_metric_names,
            "activity_distribution_metric_names",
        )
        _require_optional_non_negative(
            self.max_activity_distribution_charts,
            "max_activity_distribution_charts",
        )
        _require_non_empty(
            self.displayed_liquidity_page_title,
            "displayed_liquidity_page_title",
        )
        _require_non_empty(
            self.displayed_liquidity_help_text,
            "displayed_liquidity_help_text",
        )
        _require_non_empty(self.pts_stats_title, "pts_stats_title")
        _require_non_empty(self.pts_stats_help_text, "pts_stats_help_text")
        _require_metric_name_sequence(
            self.displayed_liquidity_metric_names,
            "displayed_liquidity_metric_names",
        )
        _require_optional_non_negative(
            self.max_displayed_liquidity_charts,
            "max_displayed_liquidity_charts",
        )
        _require_optional_non_negative(
            self.max_displayed_liquidity_groups,
            "max_displayed_liquidity_groups",
        )
        _require_non_empty(self.summary_scope_label, "summary_scope_label")
        _require_non_empty(self.symbol_anomaly_page_title, "symbol_anomaly_page_title")
        _require_non_empty(
            self.symbol_anomaly_table_title,
            "symbol_anomaly_table_title",
        )
        _require_non_empty(self.symbol_anomaly_help_text, "symbol_anomaly_help_text")
        _require_non_negative(self.max_metric_cards, "max_metric_cards")
        _require_non_negative(self.max_comments, "max_comments")
        _require_optional_non_negative(self.max_table_rows, "max_table_rows")
        _require_optional_non_negative(self.max_chart_points, "max_chart_points")
        _require_optional_non_negative(self.max_heatmap_cells, "max_heatmap_cells")
        _require_non_negative(self.max_overview_metrics, "max_overview_metrics")
        if self.overview_top_change_diversification not in {"metric", "family"}:
            raise ValueError("overview_top_change_diversification must be one of: metric, family")
        _require_non_negative(self.max_summary_story_charts, "max_summary_story_charts")
        _require_metric_name_sequence(
            self.detailed_metric_trends_metric_names,
            "detailed_metric_trends_metric_names",
        )
        _require_non_empty(
            self.detailed_metric_trends_default_metric,
            "detailed_metric_trends_default_metric",
        )
        _require_one_of(
            self.detailed_metric_trends_granularity,
            "detailed_metric_trends_granularity",
            ("daily", "weekly", "monthly", "quarterly", "yearly"),
        )
        _require_metric_name_sequence(self.summary_kpi_metric_names, "summary_kpi_metric_names")
        _require_non_empty(self.primary_intraday_signal_metric_name, "primary_intraday_signal_metric_name")
        _require_non_empty(
            self.toxicity_reversion_page_title,
            "toxicity_reversion_page_title",
        )
        _require_non_empty(
            self.toxicity_reversion_help_text,
            "toxicity_reversion_help_text",
        )
        _require_optional_non_negative(
            self.max_toxicity_reversion_charts,
            "max_toxicity_reversion_charts",
        )
        _require_optional_non_negative(
            self.max_toxicity_reversion_points_per_chart,
            "max_toxicity_reversion_points_per_chart",
        )
        _require_toxicity_context_ranking(
            self.toxicity_reversion_context_ranking,
            "toxicity_reversion_context_ranking",
        )
        _require_reversion_order(
            self.toxicity_reversion_venue_order,
            "toxicity_reversion_venue_order",
        )
        _require_reversion_order(
            self.toxicity_reversion_horizon_order,
            "toxicity_reversion_horizon_order",
        )
        _require_non_negative(
            self.max_toxicity_reversion_comments,
            "max_toxicity_reversion_comments",
        )
        _require_non_negative(self.max_symbol_anomalies, "max_symbol_anomalies")
        _require_symbol_group_keys(self.symbol_group_keys)
        _require_non_empty(
            self.symbol_detail_page_title_template,
            "symbol_detail_page_title_template",
        )
        _require_non_empty(self.symbol_detail_help_text, "symbol_detail_help_text")
        _require_non_empty(self.symbol_detail_index_title, "symbol_detail_index_title")
        _require_non_empty(
            self.symbol_detail_index_help_text,
            "symbol_detail_index_help_text",
        )
        _require_non_negative(self.max_symbol_detail_pages, "max_symbol_detail_pages")
        _require_non_empty(self.drilldown_page_title, "drilldown_page_title")
        _require_non_empty(self.drilldown_table_title, "drilldown_table_title")
        _require_non_empty(self.drilldown_help_text, "drilldown_help_text")
        _require_optional_non_negative(self.max_drilldown_rows, "max_drilldown_rows")
        _require_drilldown_group_keys(self.drilldown_group_keys)


@dataclass(frozen=True)
class _MetricAggregatePayload:
    metric_name: str
    daily_current: tuple[tuple[date, float], ...]
    daily_reference: tuple[tuple[date, float], ...]
    bucketed_current: tuple[tuple[tuple[int, ...], str, float], ...]
    bucketed_reference: tuple[tuple[tuple[int, ...], str, float], ...]
    spark_points: tuple[tuple[str, float], ...]
    target_mean: float | None
    benchmark_mean: float | None
    delta_pct: float | None


def _observation_level(observation: MetricObservation) -> str:
    raw_level = observation.metadata.get("level")
    if raw_level is not None:
        text = str(raw_level).strip().lower()
        if text in {"intraday", "daily"}:
            return text
    bucket = observation.time_bucket
    if bucket is None:
        return "daily"
    bucket_text = str(bucket).strip().upper()
    if bucket_text in {"DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "PERIOD"}:
        return "daily"
    return "intraday"


def _series_for_level(series: MetricTimeSeries, level: str) -> MetricTimeSeries:
    return MetricTimeSeries(
        metric_name=series.metric_name,
        observations=tuple(
            observation
            for observation in series.observations
            if _observation_level(observation) == level
        ),
        metadata=series.metadata,
    )


def build_market_monitor_report(
    report_input: MarketReportInput,
    *,
    options: MarketReportOptions | None = None,
) -> ReportDocument:
    """Build the canonical production-format report document.

    The same builder must be used by production and by the mock-data demo. It
    accepts normalized metric series and precomputed comparisons only; it does
    not query kdb+, import PyKX, calculate metrics from raw data, or call an LLM.
    """

    resolved_options = options or MarketReportOptions()
    definitions = dict(report_input.metric_definitions)
    summary_page = _build_summary_page(
        report_input,
        definitions,
        options=resolved_options,
    )

    pages = [summary_page]

    document = ReportDocument(
        title=resolved_options.title.strip(),
        pages=pages,
        branding=ReportBranding(
            brand_name=(None if resolved_options.brand_name is None else resolved_options.brand_name.strip())
        ),
        generated_at_text=(
            None if resolved_options.generated_at_text is None else resolved_options.generated_at_text.strip()
        ),
        header_meta=_build_document_header_meta(report_input, options=resolved_options),
    )
    if not resolved_options.include_metric_definitions_appendix:
        return document
    return append_metric_definitions_appendix(document)


def _build_summary_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage:
    summary_comparisons = _aggregate_market_summary_comparisons(
        report_input.comparisons,
        symbol_group_keys=options.symbol_group_keys,
    )
    summary_metric_card_comparisons = _select_metric_level_summary_comparisons(summary_comparisons)
    meta_strip_block = _build_summary_meta_strip_block(
        summary_comparisons,
        options=options,
    )

    comparison_options = ComparisonSectionOptions(
        max_metric_cards=options.max_metric_cards,
        max_comments=options.max_comments,
        section_summary_scope_label=options.summary_scope_label,
    )
    base_page = build_comparison_report_page(
        options.summary_page_title,
        summary_metric_card_comparisons,
        definitions,
        options=comparison_options,
    )
    market_overview_block = _build_market_overview_cards_block(
        report_input,
        summary_metric_card_comparisons,
        definitions,
    )
    detailed_trends_block = _build_detailed_metric_trends_block(
        report_input,
        definitions,
        options=options,
    )
    turnover_block = _build_turnover_distribution_summary_block(report_input, definitions, options=options)
    liquidity_block = _build_liquidity_distribution_summary_block(report_input, definitions, options=options)
    pts_stats_block = _build_pts_stats_block(report_input, definitions, options=options)
    return ReportPage(
        title=base_page.title,
        html_blocks=(
            ([meta_strip_block] if meta_strip_block is not None else [])
            + ([market_overview_block] if market_overview_block is not None else [])
            + ([detailed_trends_block] if detailed_trends_block is not None else [])
            + ([turnover_block] if turnover_block is not None else [])
            + ([liquidity_block] if liquidity_block is not None else [])
            + ([pts_stats_block] if pts_stats_block is not None else [])
        ),
        metric_cards=base_page.metric_cards,
        plotly_charts=[],
        metric_tables=[],
        commentary_blocks=[],
    )


def _build_turnover_distribution_summary_block(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> HtmlBlock | None:
    if not report_input.reference_series:
        return None
    current_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    target_series = current_by_metric.get("turnover")
    reference_series = reference_by_metric.get("turnover")
    if target_series is None or reference_series is None:
        return None
    definition = definitions.get("turnover")
    if definition is None:
        return None
    return build_summary_activity_distribution_html_block(
        "Intraday Turnover Distribution",
        reference_series=reference_series,
        target_series=target_series,
        metric_definition=definition,
        help_text=options.activity_distribution_help_text,
        cumulative_figure_height=380,
        share_figure_height=150,
    )


def _build_liquidity_distribution_summary_block(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> HtmlBlock | None:
    if not report_input.reference_series:
        return None
    current_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    metric_names = ["quoted_spread_bps", "top_of_book_depth", "parkinson_volatility_bps"]
    missing: list[str] = []
    for metric_name in metric_names:
        if metric_name not in current_by_metric:
            missing.append(f"{metric_name} (current)")
        if metric_name not in reference_by_metric:
            missing.append(f"{metric_name} (reference)")
        if metric_name not in definitions:
            missing.append(f"{metric_name} (definition)")
    if missing:
        raise ValueError(
            "Intraday Liquidity Distribution requires explicit metrics with no fallback: "
            + ", ".join(missing)
        )
    target = {metric_name: current_by_metric[metric_name] for metric_name in metric_names}
    reference = {metric_name: reference_by_metric[metric_name] for metric_name in metric_names}
    metric_defs = {metric_name: definitions[metric_name] for metric_name in metric_names}
    default_metric = "quoted_spread_bps" if "quoted_spread_bps" in metric_defs else metric_names[0]
    payload = _build_liquidity_distribution_payload(
        target_by_metric=target,
        reference_by_metric=reference,
        metric_definitions=metric_defs,
        default_metric=default_metric,
        figure_height=380,
    )
    return build_summary_liquidity_distribution_html_block(
        "Intraday Liquidity Distribution",
        payload=payload,
        help_text=(
            options.liquidity_distribution_help_text
            + " Methodology: "
            + " ".join(
                f"{_liquidity_metric_label(metric_name, metric_defs[metric_name])}: {_metric_aggregation_methodology(metric_name)}"
                for metric_name in metric_names
            )
        ),
    )


def _liquidity_metric_label(metric_name: str, metric_definition: MetricDefinition) -> str:
    if metric_name == "quoted_spread_bps":
        return "Spread"
    if metric_name == "top_of_book_depth":
        return "Top book depth"
    if metric_name == "parkinson_volatility_bps":
        return "Volatility"
    return metric_definition.label


def _metric_help_icon_html(*, title: str, help_text: str) -> str:
    return (
        '<details class="metric-help">'
        f'<summary class="metric-help__summary metric-info" aria-label="Metric definition: {escape(title)}">'
        '<span class="metric-help__icon" aria-hidden="true">i</span>'
        "</summary>"
        '<div class="metric-help__body">'
        f'<strong class="metric-help__title">{escape(title)}</strong>'
        f"<p>{escape(help_text)}</p>"
        "</div></details>"
    )


def _build_pts_stats_block(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> HtmlBlock | None:
    if not options.include_pts_stats_section:
        return None

    current_by_metric = {series.metric_name: series for series in report_input.current_series}
    reference_by_metric = {series.metric_name: series for series in report_input.reference_series}
    pts_series = current_by_metric.get("pts_turnover")
    turnover_series = current_by_metric.get("turnover")
    reference_pts_series = reference_by_metric.get("pts_turnover")
    reference_turnover_series = reference_by_metric.get("turnover")
    if pts_series is None or turnover_series is None:
        return None

    pts_series = _series_for_level(pts_series, "daily")
    turnover_series = _series_for_level(turnover_series, "daily")
    reference_pts_series = None if reference_pts_series is None else _series_for_level(reference_pts_series, "daily")
    reference_turnover_series = (
        None if reference_turnover_series is None else _series_for_level(reference_turnover_series, "daily")
    )
    denominator_daily = _metric_daily_rollups("turnover", turnover_series)
    if not denominator_daily:
        return None

    granularity = options.detailed_metric_trends_granularity
    denominator_by_bucket: dict[tuple[int, ...], float] = {}
    for obs_date, value in denominator_daily:
        bucket_key = _time_bucket_key(obs_date, granularity)
        denominator_by_bucket[bucket_key] = denominator_by_bucket.get(bucket_key, 0.0) + float(value)

    numerator_by_bucket_venue: dict[tuple[tuple[int, ...], str], float] = {}
    for observation in pts_series.observations:
        if observation.value is None:
            continue
        value = float(observation.value)
        if not isfinite(value):
            continue
        venue = observation.group.get("venue")
        if venue is None:
            continue
        bucket_key = _time_bucket_key(observation.date, granularity)
        row_key = (bucket_key, str(venue))
        numerator_by_bucket_venue[row_key] = numerator_by_bucket_venue.get(row_key, 0.0) + value

    if not numerator_by_bucket_venue:
        return None

    ordered_bucket_keys = sorted(
        bucket_key for bucket_key, denominator in denominator_by_bucket.items() if denominator > 0.0
    )
    if not ordered_bucket_keys:
        return None
    labels = [_time_bucket_label(bucket_key, granularity) for bucket_key in ordered_bucket_keys]

    venue_totals: dict[str, float] = {}
    for (_, venue), value in numerator_by_bucket_venue.items():
        venue_text = str(venue).strip()
        if not venue_text:
            continue
        venue_totals[venue_text] = venue_totals.get(venue_text, 0.0) + value
    current_denominator_total = sum(float(value) for value in denominator_by_bucket.values() if value > 0.0)
    current_share_by_venue = {
        venue: ((total / current_denominator_total) * 100.0) if current_denominator_total > 0.0 else None
        for venue, total in venue_totals.items()
    }

    reference_share_by_venue: dict[str, float | None] = {}
    if reference_pts_series is not None and reference_turnover_series is not None:
        reference_denominator_daily = _metric_daily_rollups("turnover", reference_turnover_series)
        reference_denominator_total = sum(float(value) for _, value in reference_denominator_daily if value is not None and isfinite(float(value)))
        reference_venue_totals: dict[str, float] = {}
        for observation in reference_pts_series.observations:
            if observation.value is None:
                continue
            numeric_value = float(observation.value)
            if not isfinite(numeric_value):
                continue
            venue = str(observation.group.get("venue", "")).strip()
            if not venue:
                continue
            reference_venue_totals[venue] = reference_venue_totals.get(venue, 0.0) + numeric_value
        reference_share_by_venue = {
            venue: ((total / reference_denominator_total) * 100.0) if reference_denominator_total > 0.0 else None
            for venue, total in reference_venue_totals.items()
        }

    ordered_venues = [
        venue
        for venue, _ in sorted(
            {**venue_totals, **{venue: 0.0 for venue in reference_share_by_venue}}.items(),
            key=lambda item: (
                -float(current_share_by_venue.get(item[0]) or reference_share_by_venue.get(item[0]) or 0.0),
                item[0],
            ),
        )
    ]
    ordered_venues = [venue for venue in ordered_venues if venue.strip()]
    if not ordered_venues:
        return None

    traces: list[dict[str, object]] = []
    for venue in ordered_venues:
        y_values: list[float | None] = []
        for bucket_key in ordered_bucket_keys:
            denominator = denominator_by_bucket.get(bucket_key, 0.0)
            if denominator <= 0:
                y_values.append(None)
                continue
            numerator = numerator_by_bucket_venue.get((bucket_key, venue), 0.0)
            y_values.append((numerator / denominator) * 100.0)
        traces.append(
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": venue,
                "x": labels,
                "y": y_values,
                "line": {"width": 2},
                "marker": {"size": 6},
                "hovertemplate": "%{x}<br>%{fullData.name}: %{y:.2f}%<extra></extra>",
            }
        )

    pts_definition = MetricDefinition(
        name="pts_turnover_share_pct",
        label="PTS Turnover % of TSE",
        category="PTS",
        description="PTS venue turnover expressed as a percentage of aggregate TSE turnover.",
        formula="100 * sum(pts_turnover_venue) / sum(tse_turnover)",
        formula_latex=r"100 \cdot \frac{\sum \mathrm{PTS\ turnover}_{venue}}{\sum \mathrm{TSE\ turnover}}",
        interpretation="Higher values indicate more turnover is executing on the selected PTS venue relative to TSE.",
        unit="%",
        higher_is_better=None,
        default_aggregation="ratio_of_sums",
        supports_intraday=False,
        supports_symbol_level=False,
        required_tables=["pts_trades", "trades"],
        required_columns=["venue", "tradePrice", "tradeSize"],
        caveats=[
            "Numerator is summed PTS turnover for the selected venue.",
            "Denominator is summed TSE turnover across the full universe.",
        ],
    )
    figure = {
        "data": traces,
        "layout": {
            "template": "plotly_white",
            "autosize": True,
            "height": 360,
            "margin": {"l": 56, "r": 24, "t": 24, "b": 72},
            "xaxis": {"title": granularity.title(), "type": "category"},
            "yaxis": {"title": "PTS turnover as % of TSE turnover", "ticksuffix": "%"},
            "legend": {"orientation": "h", "y": -0.28},
            "hovermode": "x unified",
        },
        "config": {
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
        },
    }
    figure_json = json.dumps(figure, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")

    supplemental_symbol_observations = turnover_series.metadata.get("supplemental_symbol_observations", ())
    turnover_symbol_observations = (
        supplemental_symbol_observations
        if supplemental_symbol_observations
        else turnover_series.observations
    )
    tse_turnover_by_symbol: dict[str, float] = {}
    for observation in turnover_symbol_observations:
        symbol = str(observation.group.get("sym", "")).strip()
        if not symbol or observation.value is None:
            continue
        numeric_value = float(observation.value)
        if not isfinite(numeric_value):
            continue
        tse_turnover_by_symbol[symbol] = tse_turnover_by_symbol.get(symbol, 0.0) + numeric_value

    stock_rows_by_venue: dict[str, list[tuple[str, float, float | None]]] = {}
    for venue in ordered_venues:
        by_symbol: dict[str, float] = {}
        for observation in pts_series.observations:
            venue_name = str(observation.group.get("venue", "")).strip()
            symbol = str(observation.group.get("sym", "")).strip()
            if venue_name != venue or not symbol or observation.value is None:
                continue
            numeric_value = float(observation.value)
            if not isfinite(numeric_value):
                continue
            by_symbol[symbol] = by_symbol.get(symbol, 0.0) + numeric_value
        stock_rows_by_venue[venue] = [
            (
                symbol,
                turnover_value,
                None
                if tse_turnover_by_symbol.get(symbol, 0.0) <= 0.0
                else (turnover_value / tse_turnover_by_symbol[symbol]) * 100.0,
            )
            for symbol, turnover_value in sorted(by_symbol.items(), key=lambda item: (-item[1], item[0]))[:5]
        ]

    venue_sections = []
    for venue in ordered_venues:
        rows = stock_rows_by_venue.get(venue, [])
        row_html = "".join(
            (
                "<tr>"
                f"<td>{escape(symbol)}</td>"
                f"<td>{escape(_format_metric_value(turnover_value, 'JPY'))}</td>"
                f"<td>{'n/a' if share_pct is None else escape(f'{share_pct:.2f}%')}</td>"
                "</tr>"
            )
            for symbol, turnover_value, share_pct in rows
        )
        if not row_html:
            row_html = '<tr><td colspan="3">n/a</td></tr>'
        venue_sections.append(
            '<section class="turnover-distribution__card pts-stats__venue-card">'
            '<div class="plotly-chart__card-header">'
            f'<div class="turnover-distribution__card-title">{escape(venue)}</div>'
            "</div>"
            '<div class="pts-stats__venue-table-wrap">'
            '<table class="pts-stats__venue-table">'
            '<thead><tr><th>Stock</th><th>Turnover</th><th>% of TSE</th></tr></thead>'
            f"<tbody>{row_html}</tbody>"
            "</table></div></section>"
        )
    venue_grid_help_html = _metric_help_icon_html(
        title="PTS Top Stocks by Venue",
        help_text=(
            "Top 5 stocks by summed PTS turnover within each venue over the current report period. "
            "Percentages are each stock's PTS turnover divided by that same stock's aggregate TSE turnover over the same period."
        ),
    )
    plot_help_html = _metric_help_icon_html(title=pts_definition.label, help_text=pts_definition.help_text())
    summary_table_help_html = _metric_help_icon_html(
        title="PTS Venue Share Summary",
        help_text=(
            "Reference and current are total venue PTS turnover over the selected period divided by total TSE turnover "
            "over the same period. Delta is the change in percentage points from reference to current."
        ),
    )

    summary_rows_html = []
    for venue in ordered_venues:
        current_share = current_share_by_venue.get(venue)
        reference_share = reference_share_by_venue.get(venue)
        delta_value = None
        if current_share is not None and reference_share is not None:
            delta_value = current_share - reference_share
        delta_class = (
            "turnover-distribution__heatmap-delta--neutral"
            if delta_value is None or delta_value == 0
            else "turnover-distribution__heatmap-delta--up"
            if delta_value > 0
            else "turnover-distribution__heatmap-delta--down"
        )
        summary_rows_html.append(
            "<tr>"
            f"<th>{escape(venue)}</th>"
            f"<td>{escape('n/a' if reference_share is None else f'{reference_share:.2f}%')}</td>"
            f"<td>{escape('n/a' if current_share is None else f'{current_share:.2f}%')}</td>"
            f'<td class="{delta_class}">{escape("n/a" if delta_value is None else f"{delta_value:+.2f}pp")}</td>'
            "</tr>"
        )

    section_help_html = (
        '<details class="metric-help turnover-distribution__help">'
        f'<summary class="metric-help__summary metric-info" aria-label="Section help: {escape(options.pts_stats_title)}">'
        '<span class="metric-help__icon" aria-hidden="true">i</span>'
        "</summary>"
        '<div class="metric-help__body">'
        f'<strong class="metric-help__title">Section help: {escape(options.pts_stats_title)}</strong>'
        f"<p>{escape(options.pts_stats_help_text)} Methodology: each line is one PTS venue numerator; denominator is aggregate TSE turnover; weekly/monthly/quarterly values are computed as sum(numerator) / sum(denominator) within each bucket.</p>"
        "</div></details>"
    )
    body_html = (
        '<section class="pts-stats turnover-distribution">'
        '<div class="turnover-distribution__header">'
        f'<h3 class="turnover-distribution__title">PTS Stats</h3>'
        f"{section_help_html}"
        "</div>"
        '<div class="pts-stats__stack">'
        '<div class="pts-stats__summary-row">'
        '<section class="turnover-distribution__card pts-stats__summary-card">'
        '<div class="plotly-chart__card-header">'
        '<div class="turnover-distribution__card-title">Venue Summary</div>'
        f"{summary_table_help_html}"
        "</div>"
        '<div class="pts-stats__summary-table-wrap">'
        '<table class="pts-stats__summary-table">'
        '<thead><tr><th>Venue</th><th>Reference</th><th>Current</th><th>Delta</th></tr></thead>'
        f"<tbody>{''.join(summary_rows_html)}</tbody>"
        '</table></div></section>'
        '<section class="pts-stats__plot-surface">'
        '<div class="plotly-chart__card-header">'
        '<div class="pts-stats__plot-header">'
        f'<div class="turnover-distribution__card-title pts-stats__plot-title">{escape(pts_definition.label)}</div>'
        f"{plot_help_html}"
        '</div>'
        "</div>"
        '<div class="plotly-chart__visual" role="img" aria-label="PTS Turnover % of TSE Plotly chart">'
        '<div class="plotly-chart__figure" data-mmsr-plotly></div>'
        f'<script type="application/json" class="plotly-chart__spec">{figure_json}</script>'
        '</div></section></div>'
        '<div class="pts-stats__venues">'
        '<div class="plotly-chart__card-header">'
        '<div class="turnover-distribution__card-title">Top 5 Stocks by Venue</div>'
        f"{venue_grid_help_html}"
        "</div>"
        f"<div class=\"pts-stats__venue-grid\">{''.join(venue_sections)}</div>"
        "</div></div></section>"
    )
    return HtmlBlock(title=options.pts_stats_title, body_html=body_html, help_text=None)


def _metric_aggregation_methodology(metric_name: str) -> str:
    if metric_name in {"turnover", "volume", "trade_count"}:
        return (
            "Intraday: sum within each symbol and time bucket, then summed across the selected scope. "
            "Daily: sum within each symbol-day, then summed across the selected scope. "
            "Period: average of daily scope totals."
        )
    if metric_name == "quoted_spread_bps":
        return (
            "Intraday: time-weighted average spread within each symbol bucket, then average across the selected scope. "
            "Daily: time-weighted average spread within each symbol-day, then average across the selected scope. "
            "Period: average of daily scope values."
        )
    if metric_name == "top_of_book_depth":
        return (
            "Intraday: median top-of-book depth within each symbol bucket, then average across the selected scope. "
            "Daily: median top-of-book depth within each symbol-day, then average across the selected scope. "
            "Period: average of daily scope values."
        )
    if metric_name == "parkinson_volatility_bps":
        return (
            "Intraday: Parkinson high-low range within each symbol bucket, requiring at least two trades, then average across the selected scope. "
            "Daily: Parkinson high-low range within each symbol-day, requiring at least two trades, then average across the selected scope. "
            "Period: RMS of daily scope volatility values."
        )
    return "Metric-specific rollup."


def _metric_help_text(definition: MetricDefinition | None, metric_name: str) -> str:
    methodology = _metric_aggregation_methodology(metric_name)
    if definition is None:
        return methodology
    unit_text = definition.unit.strip() or "n/a"
    description = definition.description.strip() or "No definition available."
    return f"{description} Unit: {unit_text}. Aggregation methodology: {methodology}"


def _liquidity_group_bucket(group: Mapping[str, object]) -> str | None:
    topix_keys = ("topixCapGrp", "topix_cap_group")
    has_topix_key = any(key in group for key in topix_keys)
    for key in topix_keys:
        value = group.get(key)
        if value is None:
            continue
        text = str(value).strip().casefold()
        if not text:
            continue
        if "non" in text and "topix" in text:
            return "Non-TOPIX"
        if "large" in text:
            return "TOPIX Large"
        if "mid" in text:
            return "TOPIX Mid"
        if "small" in text:
            return "TOPIX Small"
    if has_topix_key:
        return "Non-TOPIX"
    for key in ("market_cap_bucket", "marketCapBucket"):
        value = group.get(key)
        if value is None:
            continue
        text = str(value).strip().casefold()
        if not text:
            continue
        if "large" in text:
            return "TOPIX Large"
        if "mid" in text:
            return "TOPIX Mid"
        if "small" in text:
            return "TOPIX Small"
    return None


def _filter_series_for_liquidity_row(series: MetricTimeSeries, row: str) -> MetricTimeSeries:
    if row == "TSE":
        return series
    filtered = tuple(
        observation
        for observation in series.observations
        if _liquidity_group_bucket(observation.group) == row
    )
    return MetricTimeSeries(metric_name=series.metric_name, observations=filtered)


def _liquidity_aggregate_from_bucket_series(metric_name: str, values_by_bucket: Mapping[str, float]) -> float | None:
    values = [value for value in values_by_bucket.values() if isfinite(value)]
    if not values:
        return None
    return _aggregate_values(metric_name, values)


def _aggregate_values(metric_name: str, values: list[float]) -> float | None:
    if not values:
        return None
    if metric_name in {"quoted_spread_bps", "top_of_book_depth"}:
        return float(median(values))
    if metric_name == "parkinson_volatility_bps":
        return sqrt(sum(value * value for value in values) / len(values))
    return sum(values) / len(values)


def _bucket_label(bucket: object | None) -> str:
    label = format_intraday_bucket_label(bucket)
    if label is None:
        return "Full day"
    return str(label)


def _liquidity_daily_bucket_values(metric_name: str, series: MetricTimeSeries) -> dict[object, dict[str, float]]:
    raw: dict[object, dict[str, list[float]]] = {}
    for observation in series.observations:
        if observation.value is None:
            continue
        numeric = float(observation.value)
        if not isfinite(numeric):
            continue
        bucket = _bucket_label(observation.time_bucket)
        raw.setdefault(observation.date, {}).setdefault(bucket, []).append(numeric)
    return {
        day: {
            bucket: value
            for bucket, bucket_values in by_bucket.items()
            if (value := _aggregate_values(metric_name, bucket_values)) is not None
        }
        for day, by_bucket in raw.items()
    }


def _liquidity_period_bucket_values(
    metric_name: str,
    values_by_date_bucket: Mapping[object, Mapping[str, float]],
) -> dict[str, float]:
    bucket_values: dict[str, list[float]] = {}
    for by_bucket in values_by_date_bucket.values():
        for bucket, value in by_bucket.items():
            bucket_values.setdefault(bucket, []).append(value)
    return {
        bucket: value
        for bucket, values in bucket_values.items()
        if (value := _aggregate_values(metric_name, values)) is not None
    }


def _liquidity_bucket_sort_key(label: str) -> tuple[int, int, int, str]:
    key = label.strip().upper()
    if key == "AMO":
        return (0, 0, 0, key)
    if key == "AMC":
        return (2, 0, 0, key)
    if key == "PMO":
        return (3, 0, 0, key)
    if key == "PMC":
        return (5, 0, 0, key)
    if ":" in key:
        try:
            hh, mm = key.split(":", 1)
            return (1 if int(hh) < 12 else 4, int(hh), int(mm), key)
        except ValueError:
            return (6, 0, 0, key)
    return (6, 0, 0, key)


def _build_liquidity_bin_value_figure(
    *,
    metric_definition: MetricDefinition,
    current_by_bucket: Mapping[str, float],
    reference_by_bucket: Mapping[str, float],
    figure_height: int,
) -> dict[str, object]:
    bucket_labels = sorted(set(current_by_bucket.keys()) | set(reference_by_bucket.keys()), key=_liquidity_bucket_sort_key)
    current_values = [current_by_bucket.get(bucket) for bucket in bucket_labels]
    reference_values = [reference_by_bucket.get(bucket) for bucket in bucket_labels]
    return {
        "data": [
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Reference",
                "x": bucket_labels,
                "y": reference_values,
                "marker": {"symbol": "square", "size": 7, "color": "#8ea4bd"},
                "line": {"width": 2, "color": "#8ea4bd"},
                "hovertemplate": "%{x}<br>%{y:.4g}<extra>Reference</extra>",
            },
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Current",
                "x": bucket_labels,
                "y": current_values,
                "marker": {"symbol": "circle", "size": 8, "color": "#2d5d93"},
                "line": {"width": 3, "color": "#2d5d93"},
                "hovertemplate": "%{x}<br>%{y:.4g}<extra>Current</extra>",
            },
        ],
        "layout": {
            "template": "plotly_white",
            "height": figure_height,
            "margin": {"l": 70, "r": 20, "t": 20, "b": 108},
            "showlegend": True,
            "legend": {"orientation": "h", "x": 0.5, "xanchor": "center", "y": -0.26},
            "xaxis": {
                "anchor": "y",
                "type": "category",
                "categoryorder": "array",
                "categoryarray": bucket_labels,
                "showticklabels": True,
            },
            "yaxis": {
                "anchor": "x",
                "title": metric_definition.unit or metric_definition.label,
            },
        },
        "config": {"displaylogo": False, "responsive": True},
    }


def _delta_pct(current: float | None, reference: float | None) -> float | None:
    if current is None or reference is None or reference == 0:
        return None
    return (current - reference) / reference


def _delta_bucket(delta_pct: float | None) -> str:
    if delta_pct is None:
        return "na"
    if delta_pct <= -0.05:
        return "n4"
    if delta_pct < -0.03:
        return "n3"
    if delta_pct < -0.01:
        return "n2"
    if delta_pct < 0:
        return "n1"
    if delta_pct == 0:
        return "z0"
    if delta_pct < 0.01:
        return "p1"
    if delta_pct < 0.03:
        return "p2"
    if delta_pct < 0.05:
        return "p3"
    return "p4"


def _delta_class(delta_pct: float | None) -> str:
    if delta_pct is None:
        return "neutral"
    if delta_pct > 0:
        return "up"
    if delta_pct < 0:
        return "down"
    return "neutral"


def _build_liquidity_distribution_payload(
    *,
    target_by_metric: Mapping[str, MetricTimeSeries],
    reference_by_metric: Mapping[str, MetricTimeSeries],
    metric_definitions: Mapping[str, MetricDefinition],
    default_metric: str,
    figure_height: int,
) -> dict[str, object]:
    rows = ("TSE", "TOPIX Large", "TOPIX Mid", "TOPIX Small", "Non-TOPIX")
    metric_names = tuple(metric_definitions.keys())
    row_figure_payload: dict[str, dict[str, dict[str, object]]] = {}
    metric_rows_by_universe: dict[str, list[dict[str, str]]] = {}
    universe_rows: list[dict[str, object]] = []

    for row in rows:
        row_metrics: dict[str, dict[str, object]] = {}
        metric_rows: list[dict[str, str]] = []
        universe_cells: list[dict[str, str]] = []
        for metric_name in metric_names:
            definition = metric_definitions[metric_name]
            row_target = _filter_series_for_liquidity_row(target_by_metric[metric_name], row)
            row_reference = _filter_series_for_liquidity_row(reference_by_metric[metric_name], row)
            current_by_bucket = _liquidity_period_bucket_values(
                metric_name,
                _liquidity_daily_bucket_values(metric_name, row_target),
            )
            reference_by_bucket = _liquidity_period_bucket_values(
                metric_name,
                _liquidity_daily_bucket_values(metric_name, row_reference),
            )
            line_figure = _build_liquidity_bin_value_figure(
                metric_definition=definition,
                current_by_bucket=current_by_bucket,
                reference_by_bucket=reference_by_bucket,
                figure_height=figure_height,
            )
            row_metrics[metric_name] = {
                "title": f"Universe: {row} | Intraday {_liquidity_metric_label(metric_name, definition)} Curve",
                "line_title": f"Intraday {_liquidity_metric_label(metric_name, definition)} Curve",
                "line_figure": line_figure,
            }

            current_value = _liquidity_aggregate_from_bucket_series(metric_name, current_by_bucket)
            reference_value = _liquidity_aggregate_from_bucket_series(metric_name, reference_by_bucket)
            delta_pct = _delta_pct(current_value, reference_value)
            metric_rows.append(
                {
                    "metric_name": metric_name,
                    "label": _liquidity_metric_label(metric_name, definition),
                    "reference_text": _format_metric_value(reference_value, definition.unit),
                    "current_text": _format_metric_value(current_value, definition.unit),
                    "help_html": _metric_help_icon_html(
                        title=_liquidity_metric_label(metric_name, definition),
                        help_text=definition.help_text(),
                    ),
                }
            )
            universe_cells.append(
                {
                    "metric_name": metric_name,
                    "current_text": _format_metric_value(current_value, definition.unit),
                    "delta_text": "n/a" if delta_pct is None else f"{delta_pct:+.2%}",
                    "delta_bucket": _delta_bucket(delta_pct),
                    "delta_class": _delta_class(delta_pct),
                }
            )
        row_figure_payload[row] = row_metrics
        metric_rows_by_universe[row] = metric_rows
        universe_rows.append(
            {
                "row": row,
                "label": row,
                "selected": row == "TSE",
                "cells": universe_cells,
            }
        )

    return {
        "default_row": "TSE",
        "default_metric": default_metric,
        "rows": row_figure_payload,
        "metric_columns": [
            {"metric_name": metric_name, "label": _liquidity_metric_label(metric_name, metric_definitions[metric_name])}
            for metric_name in metric_names
        ],
        "metric_rows_by_universe": metric_rows_by_universe,
        "universe_rows": universe_rows,
    }


def _build_summary_meta_strip_block(
    summary_comparisons: tuple[MetricComparison, ...],
    *,
    options: MarketReportOptions,
) -> HtmlBlock:
    dates = sorted({comparison.date for comparison in summary_comparisons if comparison.date is not None})
    period_text = _format_period_text(dates)
    reference_method = _dominant_reference_method(summary_comparisons)
    scope_text = options.summary_scope_label.strip()
    run_tag = (options.generated_at_text or "production run").strip()

    fields = (
        ("Period", period_text),
        ("Universe", scope_text),
        ("Benchmark", reference_method),
        ("Run Tag", run_tag),
    )
    items = "".join(
        (
            '<article class="report-meta-strip__item">'
            f'<p class="report-meta-strip__label">{escape(label)}</p>'
            f'<p class="report-meta-strip__value">{escape(value)}</p>'
            "</article>"
        )
        for label, value in fields
    )
    body_html = (
        '  <section class="report-meta-strip report-control-strip">'
        f"{items}"
        '<div class="report-meta-strip__action">'
        '<a class="report-export-link" aria-label="Export report PDF" href="#" role="button">Export PDF</a>'
        "</div>"
        "</section>"
    )
    return HtmlBlock(
        title="Report Meta",
        help_text="Page-1 run metadata for period, reference method, scope, and run tag.",
        body_html=body_html,
    )


def _build_document_header_meta(
    report_input: MarketReportInput,
    *,
    options: MarketReportOptions,
) -> dict[str, str]:
    current_dates = sorted(
        {observation.date for series in report_input.current_series for observation in series.observations}
    )
    reference_dates = sorted(
        {observation.date for series in report_input.reference_series for observation in series.observations}
    )
    return {
        "subtitle": options.subtitle.strip(),
        "period_text": _format_period_text(current_dates),
        "benchmark_period_text": _format_period_text(reference_dates),
        "universe": options.universe_label.strip(),
    }


def _format_period_text(dates: list[date]) -> str:
    if not dates:
        return "n/a"
    if len(dates) == 1:
        return f"{dates[0].isoformat()} (1 day)"
    return f"{dates[0].isoformat()} to {dates[-1].isoformat()} ({len(dates)} days)"


def _dominant_reference_method(comparisons: tuple[MetricComparison, ...]) -> str:
    methods = [comparison.comparison_method for comparison in comparisons if comparison.comparison_method]
    if not methods:
        return "same_intraday_bucket"
    counts: dict[str, int] = {}
    for method in methods:
        counts[method] = counts.get(method, 0) + 1
    return max(counts.items(), key=lambda item: item[1])[0]


def _build_primary_intraday_signal_chart(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> PlotlyChart | None:
    if not options.include_primary_intraday_signal or not report_input.reference_series:
        return None

    metric_name = options.primary_intraday_signal_metric_name
    current_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    target_series = current_by_metric.get(metric_name)
    reference_series = reference_by_metric.get(metric_name)
    if target_series is None or reference_series is None:
        return None
    definition = _require_definition(metric_name, definitions)
    return build_reference_target_intraday_profile_chart(
        f"Primary Intraday Signal — {definition.label}",
        reference_series=reference_series,
        target_series=target_series,
        metric_definition=definition,
        group_by=("topixCapGrp", "market_cap_bucket", "segment", "sector"),
        max_groups=options.max_displayed_liquidity_groups,
        help_text="Primary intraday target-versus-reference diagnostic for page-1 market monitoring.",
    )


def _build_primary_intraday_insight_callout(
    summary_comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> CommentaryBlock | None:
    metric_name = options.primary_intraday_signal_metric_name
    metric_rows = [comparison for comparison in summary_comparisons if comparison.metric_name == metric_name]
    if not metric_rows:
        return None
    definition = definitions.get(metric_name)
    if definition is None:
        return None

    alert_count = sum(1 for comparison in metric_rows if comparison.status == "alert")
    watch_count = sum(1 for comparison in metric_rows if comparison.status == "watch")
    change_pcts = [comparison.change_pct for comparison in metric_rows if comparison.change_pct is not None]
    avg_change_pct = (sum(change_pcts) / len(change_pcts)) if change_pcts else None
    direction = "up" if (avg_change_pct or 0.0) >= 0 else "down"
    pct_text = "n/a" if avg_change_pct is None else f"{abs(avg_change_pct):.1%}"
    comment = (
        f"{definition.label} is {direction} {pct_text} versus reference. "
        f"Status mix: {alert_count} alerts, {watch_count} watch rows across {len(metric_rows)} market contexts."
    )
    return CommentaryBlock(title="Insight Callout", comments=[comment])


def _build_market_kpi_snapshot_block(
    summary_metric_comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
):
    if not options.include_summary_kpi_snapshot:
        return None

    comparisons_by_metric = {comparison.metric_name: comparison for comparison in summary_metric_comparisons}
    cards_html: list[str] = []
    for metric_name in options.summary_kpi_metric_names:
        comparison = comparisons_by_metric.get(metric_name)
        if comparison is None:
            continue
        definition = definitions.get(metric_name)
        if definition is None:
            continue
        value_text = _format_metric_value(comparison.value, definition.unit)
        change_text = _format_change_text(comparison.change_abs, comparison.change_pct, definition.unit)
        status = comparison.status if comparison.status in {"alert", "watch", "comparison_only", "normal"} else "normal"
        cards_html.append(
            '    <article class="kpi-snapshot__card">'
            f'<p class="kpi-snapshot__label">{escape(definition.label)}</p>'
            f'<p class="kpi-snapshot__value">{escape(value_text)}</p>'
            f'<p class="kpi-snapshot__change kpi-snapshot__change--{escape(status)}">{escape(change_text)}</p>'
            f'<div class="kpi-snapshot__mini kpi-snapshot__mini--{escape(status)}" '
            'aria-hidden="true"><span></span></div>'
            "</article>"
        )

    if not cards_html:
        return None

    return HtmlBlock(
        title="Market KPI Snapshot",
        help_text=(
            "Market-level daily snapshot for core metrics. Values are summary-level "
            "comparisons aggregated by market context and date."
        ),
        body_html='  <section class="kpi-snapshot">\n' + "\n".join(cards_html) + "\n  </section>",
    )


def _build_market_overview_cards_block(
    report_input: MarketReportInput,
    summary_metric_comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> HtmlBlock | None:
    comparisons_by_metric = {comparison.metric_name: comparison for comparison in summary_metric_comparisons}
    volatility_metric_name = _pick_volatility_metric_name(comparisons_by_metric)
    aggregate_by_metric = _build_metric_aggregate_payloads(
        report_input,
        metric_names=(
            "turnover",
            "quoted_spread_bps",
            "top_of_book_depth",
            *(() if volatility_metric_name is None else (volatility_metric_name,)),
        ),
        granularity="daily",
    )

    card_specs = (
        ("Daily Turnover", "turnover"),
        ("Quoted Spread", "quoted_spread_bps"),
        ("Top of book Depth", "top_of_book_depth"),
        ("Volatility", volatility_metric_name),
    )
    cards_html: list[str] = []
    card_payloads: list[dict[str, str]] = []
    for card_label, metric_name in card_specs:
        aggregation_text = _overview_card_aggregation_text(card_label)
        definition = None if metric_name is None else definitions.get(metric_name)
        aggregate = None if metric_name is None else aggregate_by_metric.get(metric_name)
        if card_label == "Volatility" and definition is None:
            definition = _parkinson_volatility_definition_fallback()
        if definition is None or aggregate is None or aggregate.target_mean is None:
            value_text = "n/a"
            delta_text = "no comparison"
            delta_class = "flat"
        else:
            value_text = _format_overview_card_value(aggregate.target_mean, definition.unit)
            delta_text = _format_overview_delta_text(aggregate.delta_pct)
            delta_class = _delta_direction_class(aggregate.delta_pct)
            LOGGER.info(
                "Market Overview card [%s]: target_mean=%.6g benchmark_mean=%.6g "
                "delta_pct=%.6g delta_text=%s value_text=%s "
                "(daily_current=%d points, daily_reference=%d points)",
                card_label,
                aggregate.target_mean,
                aggregate.benchmark_mean,
                aggregate.delta_pct,
                delta_text,
                value_text,
                len(aggregate.daily_current),
                len(aggregate.daily_reference),
            )
        cards_html.append(
            '    <article class="market-overview-card">'
            '<div class="market-overview-card__heading">'
            f'<p class="market-overview-card__label">{escape(card_label)}</p>'
            f'{_overview_metric_help_html(card_label, definition, aggregation_text)}'
            "</div>"
            f'<p class="market-overview-card__value">{escape(value_text)}</p>'
            f'<p class="market-overview-card__delta market-overview-card__delta--{escape(delta_class)}">{escape(delta_text)}</p>'
            f'{_overview_spark_bar_html(aggregate)}'
            "</article>"
        )
        card_payloads.append(
            {
                "label": card_label,
                "metric_name": "" if metric_name is None else metric_name,
                "value_text": value_text,
                "delta_text": delta_text,
                "delta_class": delta_class,
            }
        )

    return HtmlBlock(
        title="Market Overview",
        help_text="Top-level market cards for daily turnover, spread, top-of-book depth, and volatility.",
        body_html=(
            '  <section class="market-overview-grid">\n'
            + "\n".join(cards_html)
            + "\n  </section>"
            + f'<script type="application/json" data-market-overview-spec>{_safe_json_script({"cards": card_payloads})}</script>'
        ),
    )


def _build_detailed_metric_trends_block(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
    market_scope_only: bool = False,
) -> HtmlBlock | None:
    if not options.include_detailed_metric_trends_section:
        return None
    current_by_metric = {series.metric_name: series for series in report_input.current_series}
    reference_by_metric = {series.metric_name: series for series in report_input.reference_series}
    available_metric_names = set(current_by_metric) | set(reference_by_metric)
    if not available_metric_names:
        return None

    volatility_name = _pick_volatility_metric_name(
        {comparison.metric_name: comparison for comparison in report_input.comparisons}
    )
    metric_names: list[str] = []
    configured_metric_names = list(options.detailed_metric_trends_metric_names)
    for configured in configured_metric_names:
        resolved = configured
        if configured == "parkinson_volatility_bps" and configured not in available_metric_names and volatility_name is not None:
            resolved = volatility_name
        if resolved in available_metric_names and resolved not in metric_names:
            metric_names.append(resolved)

    if not metric_names:
        return None

    aggregate_by_metric = _build_metric_aggregate_payloads(
        report_input,
        metric_names=metric_names,
        granularity=options.detailed_metric_trends_granularity,
        market_scope_only=market_scope_only,
    )

    payload_metrics: dict[str, dict[str, object]] = {}
    for metric_name in metric_names:
        aggregate = aggregate_by_metric.get(metric_name)
        if aggregate is None:
            continue
        current_points = list(aggregate.bucketed_current)
        reference_points = list(aggregate.bucketed_reference)

        labels = [label for _, label, _ in reference_points] + [label for _, label, _ in current_points]
        values = [value for _, _, value in reference_points] + [value for _, _, value in current_points]
        period_flags = (["benchmark"] * len(reference_points)) + (["target"] * len(current_points))
        benchmark_mean = aggregate.benchmark_mean
        target_mean = aggregate.target_mean
        definition = definitions.get(metric_name)
        metric_help = "No definition available."
        metric_description = "No definition available."
        metric_unit = ""
        metric_formula_latex = ""
        if definition is not None:
            unit_text = definition.unit.strip() or "n/a"
            metric_help = _metric_help_text(definition, metric_name)
            metric_description = definition.description.strip()
            metric_unit = unit_text
            metric_formula_latex = "" if definition.formula_latex is None else definition.formula_latex
        payload_metrics[metric_name] = {
            "metric_label": metric_name if definition is None else definition.label,
            "unit": "" if definition is None else definition.unit,
            "labels": labels,
            "values": values,
            "period_flags": period_flags,
            "benchmark_mean": benchmark_mean,
            "target_mean": target_mean,
            "help_text": metric_help,
            "description": metric_description,
            "unit_text": metric_unit,
            "formula_latex": metric_formula_latex,
            "aggregation_text": _metric_aggregation_methodology(metric_name),
            "insights": _metric_trend_comments(
                metric_name,
                list(aggregate.daily_current),
                list(aggregate.daily_reference),
            ),
        }

    if not payload_metrics:
        return None

    default_metric = options.detailed_metric_trends_default_metric
    if (
        default_metric == "parkinson_volatility_bps"
        and default_metric not in payload_metrics
        and volatility_name is not None
        and volatility_name in payload_metrics
    ):
        default_metric = volatility_name
    if default_metric not in payload_metrics:
        default_metric = next(iter(payload_metrics))
    ordered_metric_keys = [
        metric_name
        for metric_name in ("turnover", "quoted_spread_bps", "top_of_book_depth", "parkinson_volatility_bps")
        if metric_name in payload_metrics
    ] + [metric_name for metric_name in payload_metrics if metric_name not in {"turnover", "quoted_spread_bps", "top_of_book_depth", "parkinson_volatility_bps"}]
    select_options = "".join(
        (
            f'<option value="{escape(metric_name)}"'
            + (' selected' if metric_name == default_metric else "")
            + f'>{escape(str(payload["metric_label"]))}</option>'
        )
        for metric_name, payload in ((metric_name, payload_metrics[metric_name]) for metric_name in ordered_metric_keys)
    )
    payload = {
        "granularity": options.detailed_metric_trends_granularity,
        "default_metric": default_metric,
        "metrics": payload_metrics,
        "ordered_metrics": ordered_metric_keys,
        "section_help": (
            "Trend chart across benchmark then target period. "
            "Rollups: traded value sum; quoted spread median; top-of-book depth median; "
            "volatility RMS over daily volatility values."
        ),
    }
    body_parts = [
        '<section class="detailed-trends" data-detailed-trends>',
        '<div class="detailed-trends__header">',
        '<h3 class="detailed-trends__title">Detailed Metric Trends</h3>',
        '<details class="metric-help detailed-trends__help">',
        '<summary class="metric-help__summary metric-info" aria-label="Section help: Detailed Metric Trends">',
        '<span class="metric-help__icon" aria-hidden="true">i</span>',
        "</summary>",
        '<div class="metric-help__body" data-detailed-trends-section-help>',
        '<strong class="metric-help__title">Section help: Detailed Metric Trends</strong>',
        '<p data-detailed-trends-section-help-text></p>',
        "</div>",
        "</details>",
        '<button type="button" class="detailed-trends__toggle" data-detailed-trends-toggle>Focused</button>',
        "</div>",
        '<div class="detailed-trends__grid" data-detailed-trends-grid></div>',
    ]
    if options.include_automated_insights:
        body_parts.extend(
            [
                '<section class="automated-insight automated-insight--inline" data-detailed-trends-insights-grid>',
                '<div class="automated-insight__icon" aria-hidden="true">i</div>',
                '<div class="automated-insight__content">',
                '<h4 class="automated-insight__title">Automated Insight Summary</h4>',
                '<div class="automated-insight__grid" data-detailed-trends-insights-grid-content></div>',
                "</div>",
                "</section>",
            ]
        )
    body_parts.extend(
        [
            '<section class="detailed-trends__detail" data-detailed-trends-detail hidden>',
            '<div class="detailed-trends__controls">',
            '<label class="detailed-trends__label" for="detailed-trends-metric-select">Metric</label>',
            f'<select id="detailed-trends-metric-select" class="detailed-trends__select" data-detailed-trends-select>{select_options}</select>',
            "</div>",
            '<div class="detailed-trends__chart" role="img" aria-label="Detailed metric trend chart">',
            '<div class="plotly-chart__figure" data-detailed-trends-chart></div>',
            "</div>",
        ]
    )
    if options.include_automated_insights:
        body_parts.extend(
            [
                '<section class="automated-insight automated-insight--inline" data-detailed-trends-insight-focus hidden>',
                '<div class="automated-insight__icon" aria-hidden="true">i</div>',
                '<div class="automated-insight__content">',
                '<h4 class="automated-insight__title">Automated Insight Summary</h4>',
                '<div data-detailed-trends-insight-focus-content></div>',
                "</div>",
                "</section>",
            ]
        )
    body_parts.extend(
        [
            "</section>",
            f'<script type="application/json" data-detailed-trends-spec>{_safe_json_script(payload)}</script>',
            "</section>",
        ]
    )
    body_html = "".join(body_parts)
    return HtmlBlock(
        title="Detailed Metric Trends",
        help_text=(
            "Continuous benchmark-to-target timeline for the selected metric at configured "
            f"{options.detailed_metric_trends_granularity} granularity. Rollups: traded value sum; "
            "quoted spread median; top-of-book depth median; volatility RMS of daily volatility values."
        ),
        body_html=body_html,
    )


def _build_automated_insight_summary_block(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> HtmlBlock | None:
    metric_names = (
        "turnover",
        "quoted_spread_bps",
        "top_of_book_depth",
        "parkinson_volatility_bps",
    )
    current_by_metric = {series.metric_name: series for series in report_input.current_series}
    reference_by_metric = {series.metric_name: series for series in report_input.reference_series}
    entries: list[str] = []
    for metric_name in metric_names:
        series = current_by_metric.get(metric_name)
        if series is None:
            continue
        definition = definitions.get(metric_name)
        metric_label = metric_name if definition is None else definition.label
        current_daily = _metric_daily_rollups(metric_name, series)
        reference_series = reference_by_metric.get(metric_name)
        reference_daily = [] if reference_series is None else _metric_daily_rollups(metric_name, reference_series)
        comments = _metric_trend_comments(metric_name, current_daily, reference_daily)
        if not comments:
            continue
        comment_html = " ".join(f"{escape(comment)}" for comment in comments[:2])
        entries.append(
            '<article class="automated-insight__item">'
            f'<h4 class="automated-insight__metric">{escape(metric_label)}</h4>'
            f'<p class="automated-insight__comment">{comment_html}</p>'
            "</article>"
        )
    if not entries:
        return None
    body_html = (
        '<section class="automated-insight">'
        '<div class="automated-insight__icon" aria-hidden="true">i</div>'
        '<div class="automated-insight__content">'
        '<h4 class="automated-insight__title">Automated Insight Summary</h4>'
        '<div class="automated-insight__grid">'
        + "".join(entries)
        + "</div></div></section>"
    )
    return HtmlBlock(
        title="Automated Insight Summary",
        help_text="Deterministic trend commentary generated from benchmark and target series.",
        body_html=body_html,
    )


def _metric_daily_rollups(metric_name: str, series: MetricTimeSeries) -> list[tuple[date, float]]:
    series = _series_for_level(series, "daily")
    if metric_name == "quoted_spread_bps":
        return _spread_daily_rollups(series)
    per_date: dict[date, list[float]] = {}
    for observation in series.observations:
        if observation.value is None:
            continue
        value = float(observation.value)
        if not isfinite(value):
            continue
        per_date.setdefault(observation.date, []).append(value)
    rolled: list[tuple[date, float]] = []
    for obs_date, values in per_date.items():
        rollup = _metric_rollup(metric_name, values, is_daily=True)
        if rollup is None or not isfinite(rollup):
            continue
        rolled.append((obs_date, rollup))
    rolled.sort(key=lambda item: item[0])
    return rolled


def _spread_daily_rollups(series: MetricTimeSeries) -> list[tuple[date, float]]:
    per_date_symbol: dict[tuple[date, str], list[float]] = {}
    for observation in series.observations:
        if observation.value is None:
            continue
        value = float(observation.value)
        if not isfinite(value):
            continue
        symbol = _observation_symbol(observation)
        key = (observation.date, symbol)
        per_date_symbol.setdefault(key, []).append(value)

    per_date_symbol_avg: dict[date, list[float]] = {}
    for (obs_date, _), bucket_values in per_date_symbol.items():
        if not bucket_values:
            continue
        per_date_symbol_avg.setdefault(obs_date, []).append(sum(bucket_values) / len(bucket_values))

    rolled: list[tuple[date, float]] = []
    for obs_date, symbol_values in per_date_symbol_avg.items():
        if not symbol_values:
            continue
        rolled.append((obs_date, sum(symbol_values) / len(symbol_values)))
    rolled.sort(key=lambda item: item[0])
    return rolled


def _observation_symbol(observation: MetricObservation) -> str:
    for key in ("sym", "symbol"):
        value = observation.group.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return "__unknown__"


def _metric_trend_comments(
    metric_name: str,
    current_daily: list[tuple[date, float]],
    reference_daily: list[tuple[date, float]],
) -> list[str]:
    if not current_daily:
        return []
    current_dates = [obs_date for obs_date, _ in current_daily]
    current_values = [value for _, value in current_daily]
    comments: list[str] = []
    trend = classify_trend_from_daily_values(current_dates, current_values)
    comments.append(trend.summary_text)

    if reference_daily:
        current_mean = sum(current_values) / len(current_values)
        reference_values = [value for _, value in reference_daily]
        reference_mean = sum(reference_values) / len(reference_values)
        if reference_mean != 0:
            vs_pct = (current_mean - reference_mean) / abs(reference_mean)
            metric_direction = _metric_interpretation_direction(metric_name, vs_pct)
            comments.append(
                f"Target-period mean is {abs(vs_pct):.1%} {metric_direction} benchmark mean."
            )
        else:
            comments.append("Benchmark mean is zero, so relative mean comparison is not computed.")
    return comments


def _series_period_mean(
    rolled_points: tuple[tuple[tuple[int, ...], str, float], ...],
    *,
    metric_name: str = "?",
    label: str = "?",
    market_scope_only: bool = False,
) -> float | None:
    if not rolled_points:
        LOGGER.info(
            "mean[%s] %s market_scope_only=%s: no points → mean=None",
            metric_name, label, market_scope_only,
        )
        return None
    total = sum(value for _, _, value in rolled_points)
    count = len(rolled_points)
    mean_value = total / count
    LOGGER.info(
        "mean[%s] %s market_scope_only=%s: sum(values) / n = %s / %d = %s",
        metric_name, label, market_scope_only, total, count, mean_value,
    )
    return mean_value


def _period_delta_pct(
    target_mean: float | None,
    benchmark_mean: float | None,
    *,
    metric_name: str = "?",
    market_scope_only: bool = False,
) -> float | None:
    if target_mean is None or benchmark_mean is None or benchmark_mean == 0:
        LOGGER.info(
            "delta_pct[%s] market_scope_only=%s: target_mean=%s benchmark_mean=%s → delta_pct=None",
            metric_name, market_scope_only, target_mean, benchmark_mean,
        )
        return None
    delta = (target_mean - benchmark_mean) / benchmark_mean
    LOGGER.info(
        "delta_pct[%s] market_scope_only=%s: (target_mean - benchmark_mean) / benchmark_mean = "
        "(%s - %s) / %s = %s / %s = %s",
        metric_name, market_scope_only, target_mean, benchmark_mean, benchmark_mean,
        target_mean - benchmark_mean, benchmark_mean, delta,
    )
    return delta


def _build_metric_aggregate_payloads(
    report_input: MarketReportInput,
    *,
    metric_names: Iterable[str],
    granularity: str,
    market_scope_only: bool = False,
) -> dict[str, _MetricAggregatePayload]:
    current_by_metric = {series.metric_name: series for series in report_input.current_series}
    reference_by_metric = {series.metric_name: series for series in report_input.reference_series}
    payloads: dict[str, _MetricAggregatePayload] = {}
    for metric_name in metric_names:
        current_series = current_by_metric.get(metric_name)
        reference_series = reference_by_metric.get(metric_name)
        current_series = None if current_series is None else _series_for_level(current_series, "daily")
        reference_series = None if reference_series is None else _series_for_level(reference_series, "daily")
        if market_scope_only:
            current_series = None if current_series is None else _filter_series_for_market_scope(current_series)
            reference_series = None if reference_series is None else _filter_series_for_market_scope(reference_series)
        daily_current = tuple(() if current_series is None else _metric_daily_rollups(metric_name, current_series))
        daily_reference = tuple(() if reference_series is None else _metric_daily_rollups(metric_name, reference_series))
        bucketed_current = tuple(
            _aggregate_metric_trend_series(
                current_series,
                metric_name=metric_name,
                granularity=granularity,
            )
        )
        bucketed_reference = tuple(
            _aggregate_metric_trend_series(
                reference_series,
                metric_name=metric_name,
                granularity=granularity,
            )
        )
        spark_points = tuple(_bin_trend_points(list(daily_current)))
        target_mean = _series_period_mean(
            bucketed_current, metric_name=metric_name, label="target",
            market_scope_only=market_scope_only,
        )
        benchmark_mean = _series_period_mean(
            bucketed_reference, metric_name=metric_name, label="benchmark",
            market_scope_only=market_scope_only,
        )
        delta_pct = _period_delta_pct(
            target_mean, benchmark_mean,
            metric_name=metric_name, market_scope_only=market_scope_only,
        )
        LOGGER.info(
            "aggregate[%s] market_scope_only=%s granularity=%s: "
            "target_mean=%s benchmark_mean=%s delta_pct=%s "
            "(daily_current=%d points, daily_reference=%d points, "
            "bucketed_current=%d buckets, bucketed_reference=%d buckets)",
            metric_name, market_scope_only, granularity,
            target_mean, benchmark_mean, delta_pct,
            len(daily_current), len(daily_reference),
            len(bucketed_current), len(bucketed_reference),
        )
        payloads[metric_name] = _MetricAggregatePayload(
            metric_name=metric_name,
            daily_current=daily_current,
            daily_reference=daily_reference,
            bucketed_current=bucketed_current,
            bucketed_reference=bucketed_reference,
            spark_points=spark_points,
            target_mean=target_mean,
            benchmark_mean=benchmark_mean,
            delta_pct=delta_pct,
        )
    return payloads


def _filter_series_for_market_scope(series: MetricTimeSeries) -> MetricTimeSeries:
    supplemental_market_observations = series.metadata.get("supplemental_market_observations", ())
    source_observations = (
        supplemental_market_observations
        if supplemental_market_observations
        else series.observations
    )
    filtered = tuple(
        observation
        for observation in source_observations
        if _is_market_scope_observation(observation)
    )
    LOGGER.info(
        "filter_market_scope[%s]: supplemental=%d regular=%d source=%d filtered=%d",
        series.metric_name,
        len(supplemental_market_observations) if supplemental_market_observations else 0,
        len(series.observations),
        len(source_observations),
        len(filtered),
    )
    return MetricTimeSeries(
        metric_name=series.metric_name,
        observations=filtered,
        metadata=series.metadata,
    )


def _is_market_scope_observation(observation: MetricObservation) -> bool:
    if observation.group:
        return False
    aggregation_level = str(observation.metadata.get("aggregationLevel") or "").strip().lower()
    if aggregation_level:
        return aggregation_level == "market"
    group_type = str(observation.metadata.get("groupType") or "").strip().lower()
    if group_type:
        return group_type == "market"
    group_value = str(observation.metadata.get("groupValue") or "").strip().upper()
    if group_value:
        return group_value in {"TSE", "ALL"}
    return True


def _metric_interpretation_direction(metric_name: str, pct: float) -> str:
    if metric_name in {"quoted_spread_bps", "parkinson_volatility_bps"}:
        if pct >= 0:
            return "above"
        return "below"
    if pct >= 0:
        return "above"
    return "below"


def _aggregate_metric_trend_series(
    series: MetricTimeSeries | None,
    *,
    metric_name: str,
    granularity: str,
) -> list[tuple[tuple[int, ...], str, float]]:
    if series is None:
        return []
    daily_values: dict[date, list[float]] = {}
    for observation in series.observations:
        if observation.value is None:
            continue
        value = float(observation.value)
        if not isfinite(value):
            continue
        daily_values.setdefault(observation.date, []).append(value)
    if not daily_values:
        return []

    by_bucket: dict[tuple[int, ...], list[float]] = {}
    for obs_date, values in daily_values.items():
        daily_rollup = _metric_rollup(metric_name, values, is_daily=True)
        if daily_rollup is None:
            continue
        bucket_key = _time_bucket_key(obs_date, granularity)
        by_bucket.setdefault(bucket_key, []).append(daily_rollup)

    result: list[tuple[tuple[int, ...], str, float]] = []
    for bucket_key, values in by_bucket.items():
        rollup = _metric_rollup(metric_name, values, is_daily=False)
        if rollup is None:
            continue
        result.append((bucket_key, _time_bucket_label(bucket_key, granularity), rollup))
    result.sort(key=lambda item: item[0])
    return result


def _metric_rollup(metric_name: str, values: list[float], *, is_daily: bool) -> float | None:
    if not values:
        return None
    if metric_name == "turnover":
        return sum(values)
    if metric_name in {"quoted_spread_bps", "top_of_book_depth"}:
        return float(median(values))
    if "volatility" in metric_name:
        if is_daily:
            return sum(values) / len(values)
        return _rms_value(values)
    return sum(values) / len(values)


def _time_bucket_key(obs_date: date, granularity: str) -> tuple[int, ...]:
    if granularity == "daily":
        return (obs_date.year, obs_date.month, obs_date.day)
    if granularity == "weekly":
        iso = obs_date.isocalendar()
        return (iso.year, iso.week)
    if granularity == "monthly":
        return (obs_date.year, obs_date.month)
    if granularity == "quarterly":
        quarter = ((obs_date.month - 1) // 3) + 1
        return (obs_date.year, quarter)
    return (obs_date.year,)


def _time_bucket_label(bucket_key: tuple[int, ...], granularity: str) -> str:
    if granularity == "daily":
        year, month, day = bucket_key
        return f"{year:04d}-{month:02d}-{day:02d}"
    if granularity == "weekly":
        year, week = bucket_key
        return f"{year}-W{week:02d}"
    if granularity == "monthly":
        year, month = bucket_key
        return f"{year}-{month:02d}"
    if granularity == "quarterly":
        year, quarter = bucket_key
        return f"{year}-Q{quarter}"
    year = bucket_key[0]
    return str(year)


def _safe_json_script(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        .replace("</", "<\\/")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _pick_volatility_metric_name(comparisons_by_metric: Mapping[str, MetricComparison]) -> str | None:
    preferred = ("realized_volatility", "return_volatility", "volatility")
    for metric_name in preferred:
        if metric_name in comparisons_by_metric:
            return metric_name
    for metric_name in comparisons_by_metric:
        if "volatility" in metric_name:
            return metric_name
    return None


def _rms_value(values: list[float]) -> float | None:
    if not values:
        return None
    return sqrt(sum(value * value for value in values) / len(values))


def _format_overview_card_value(value: float | int | None, unit: str) -> str:
    if value is None:
        return "n/a"
    numeric = float(value)
    if unit == "JPY":
        abs_value = abs(numeric)
        if abs_value >= 1_000_000_000_000:
            return f"{numeric / 1_000_000_000_000:.2f}T JPY"
        if abs_value >= 1_000_000_000:
            return f"{numeric / 1_000_000_000:.2f}B JPY"
        if abs_value >= 1_000_000:
            return f"{numeric / 1_000_000:.2f}M JPY"
        return f"{numeric:,.0f} JPY"
    if unit == "shares":
        abs_value = abs(numeric)
        if abs_value >= 1_000_000_000:
            return f"{numeric / 1_000_000_000:.2f}B"
        if abs_value >= 1_000_000:
            return f"{numeric / 1_000_000:.2f}M"
        if abs_value >= 1_000:
            return f"{numeric / 1_000:.2f}K"
        return f"{numeric:,.0f}"
    if unit == "bps":
        return f"{numeric:.2f} bps"
    return _format_metric_value(value, unit)


def _format_overview_delta_text(change_pct: float | None) -> str:
    if change_pct is None:
        return "no comparison"
    if change_pct == 0:
        return "0.0%"
    arrow = "↑" if change_pct > 0 else "↓"
    return f"{arrow} {abs(change_pct):.1%}"


def _delta_direction_class(change_pct: float | None) -> str:
    if change_pct is None or change_pct == 0:
        return "flat"
    return "up" if change_pct > 0 else "down"


def _overview_card_aggregation_text(card_label: str) -> str:
    metric_name = {
        "Daily Turnover": "turnover",
        "Quoted Spread": "quoted_spread_bps",
        "Top of book Depth": "top_of_book_depth",
        "Volatility": "parkinson_volatility_bps",
    }.get(card_label)
    if metric_name is not None:
        if metric_name == "turnover":
            return (
                "Aggregation: Daily market-level turnover is summed within each trading day. "
                "The displayed period value is the simple average of those daily market totals."
            )
        return (
            "Aggregation: Values are first rolled to daily market-level observations. "
            "The displayed period value is the simple average of those daily values."
        )
    return "Aggregation: Period summary"


def _overview_metric_help_html(
    card_label: str,
    definition: MetricDefinition | None,
    aggregation_text: str | None = None,
) -> str:
    if definition is None:
        return ""
    summary = definition.description.strip() or "No definition available."
    formula_latex = definition.formula_latex
    unit_text = definition.unit.strip() if definition.unit.strip() else "n/a"
    aggregation_value = ""
    if aggregation_text:
        aggregation_value = aggregation_text.removeprefix("Aggregation: ").strip()
    aggregation_value_html = escape(aggregation_value)
    if card_label == "Volatility":
        aggregation_value_html = aggregation_value_html.replace(
            "sqrt(mean(v^2))",
            r"\(\sqrt{\mathrm{mean}(\sigma^2)}\)",
        )
    aggregation_html = (
        ""
        if not aggregation_value
        else f'<p class="metric-help__meta"><strong>Aggregation:</strong> {aggregation_value_html}</p>'
    )
    formula_html = (
        ""
        if formula_latex is None
        else (
            '<div class="metric-help__formula-wrap">'
            '<p class="metric-help__formula-label">Formula</p>'
            f'<p class="metric-help__formula">\\({formula_latex}\\)</p>'
            "</div>"
        )
    )
    return (
        '<details class="metric-help">'
        '<summary class="metric-help__summary" aria-label="Metric definition">'
        '<span class="metric-help__icon">i</span>'
        "</summary>"
        '<div class="metric-help__body">'
        f"<strong>{escape(card_label)}</strong>"
        f"<p>{escape(summary)}</p>"
        f"{aggregation_html}"
        f'<p class="metric-help__meta"><strong>Unit:</strong> {escape(unit_text)}</p>'
        f"{formula_html}"
        "</div>"
        "</details>"
    )

def _overview_spark_bar_html(aggregate: _MetricAggregatePayload | None) -> str:
    if aggregate is None or not aggregate.spark_points:
        return '<div class="market-overview-card__spark" aria-hidden="true"></div>'
    values = [value for _, value in aggregate.spark_points]
    min_value = min(values)
    max_value = max(values)
    spread = max_value - min_value
    benchmark_mean = aggregate.benchmark_mean
    bars: list[str] = []
    for _, value in aggregate.spark_points:
        if spread <= 0:
            height_pct = 55.0
        else:
            height_pct = 28.0 + (68.0 * (value - min_value) / spread)
        bars.append(f'<span class="market-overview-card__bar" style="height:{height_pct:.1f}%"></span>')
    mean_line_html = ""
    if benchmark_mean is not None:
        if spread <= 0:
            mean_pct = 55.0
        else:
            mean_pct = 28.0 + (68.0 * (benchmark_mean - min_value) / spread)
            mean_pct = max(0.0, min(100.0, mean_pct))
        mean_line_html = (
            f'<span class="market-overview-card__spark-mean" style="bottom:{mean_pct:.1f}%"></span>'
        )
    return '<div class="market-overview-card__spark" aria-hidden="true">' + mean_line_html + "".join(bars) + "</div>"


def _bin_trend_points(points: list[tuple[date, float]]) -> list[tuple[str, float]]:
    if len(points) <= 30:
        return [(bucket_date.isoformat(), value) for bucket_date, value in points]

    by_week: dict[tuple[int, int], list[float]] = {}
    for bucket_date, value in points:
        iso = bucket_date.isocalendar()
        by_week.setdefault((iso.year, iso.week), []).append(value)
    weekly = sorted((key, sum(values) / len(values)) for key, values in by_week.items())
    if len(weekly) <= 30:
        return [(f"{year}-W{week:02d}", value) for (year, week), value in weekly]

    by_month: dict[tuple[int, int], list[float]] = {}
    for bucket_date, value in points:
        by_month.setdefault((bucket_date.year, bucket_date.month), []).append(value)
    monthly = sorted((key, sum(values) / len(values)) for key, values in by_month.items())
    if len(monthly) <= 30:
        return [(f"{year}-{month:02d}", value) for (year, month), value in monthly]

    by_quarter: dict[tuple[int, int], list[float]] = {}
    for bucket_date, value in points:
        quarter = ((bucket_date.month - 1) // 3) + 1
        by_quarter.setdefault((bucket_date.year, quarter), []).append(value)
    quarterly = sorted((key, sum(values) / len(values)) for key, values in by_quarter.items())
    return [(f"{year}-Q{quarter}", value) for (year, quarter), value in quarterly]


def _parkinson_volatility_definition_fallback() -> MetricDefinition:
    return MetricDefinition(
        name="parkinson_volatility_bps",
        label="Parkinson Vola",
        category="Liquidity",
        description="Parkinson volatility: range-based estimator derived from bid/ask high-low ranges.",
        formula=(
            "10000 * sqrt(mean((log(high/low))^2) / (4 * log(2))) "
            "where high=max(askPrice), low=min(bidPrice)"
        ),
        formula_latex=(
            r"10000 \cdot \sqrt{\frac{1}{4\ln 2}\mathbb{E}\left[\left(\ln\!\left(\frac{H}{L}\right)\right)^2\right]}"
        ),
        interpretation=(
            "Higher values indicate wider intrabucket price ranges and potentially "
            "higher short-horizon market-state volatility."
        ),
        unit="bps",
        higher_is_better=False,
        default_aggregation="mean",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=["quotes"],
        required_columns=["bidPrice", "askPrice"],
    )


def _format_metric_value(value: float | int | None, unit: str) -> str:
    if value is None:
        return "n/a"
    if unit == "JPY":
        return f"{value:,.0f} JPY"
    if unit == "count":
        return f"{value:,.0f}"
    if unit == "shares":
        return f"{value:,.0f} shares"
    return f"{value:,.2f} {unit}".strip()


def _format_change_text(change_abs: float | None, change_pct: float | None, unit: str) -> str:
    if change_abs is None and change_pct is None:
        return "no comparison"
    parts: list[str] = []
    if change_abs is not None:
        if unit == "JPY":
            parts.append(f"{change_abs:+,.0f} JPY")
        elif unit == "shares" or unit == "count":
            parts.append(f"{change_abs:+,.0f}")
        else:
            parts.append(f"{change_abs:+,.2f} {unit}".strip())
    if change_pct is not None:
        parts.append(f"{change_pct:+.2%}")
    return "change " + " ".join(parts)


def _aggregate_market_summary_comparisons(
    comparisons: tuple[MetricComparison, ...],
    *,
    symbol_group_keys: tuple[str, ...],
) -> tuple[MetricComparison, ...]:
    symbol_keys = {key.casefold() for key in symbol_group_keys} | {"sym", "symbol", "ticker", "ric", "isin"}
    grouped: dict[tuple[str, object, tuple[tuple[str, str], ...]], list[MetricComparison]] = {}
    for comparison in comparisons:
        if any(str(group_key).casefold() in symbol_keys for group_key in comparison.group):
            continue
        group_items = tuple(sorted((str(key), str(value)) for key, value in comparison.group.items()))
        key = (comparison.metric_name, comparison.date, group_items)
        grouped.setdefault(key, []).append(comparison)

    aggregated: list[MetricComparison] = []
    for (metric_name, aggregate_date, group_items), group_rows in grouped.items():
        representative = min(
            group_rows,
            key=lambda row: (
                _summary_status_priority(row.status),
                -(abs(row.z_score or 0.0)),
                -(abs(row.change_pct or 0.0)),
            ),
        )
        avg_value = _aggregate_metric_central_value(metric_name, (row.value for row in group_rows))
        avg_reference_value = _aggregate_metric_central_value(metric_name, (row.reference_value for row in group_rows))
        change_abs = None
        change_pct = None
        if avg_value is not None and avg_reference_value is not None:
            change_abs = avg_value - avg_reference_value
            if avg_reference_value != 0:
                change_pct = change_abs / avg_reference_value
        aggregated.append(
            MetricComparison(
                metric_name=metric_name,
                value=avg_value,
                reference_value=avg_reference_value,
                change_abs=change_abs,
                change_pct=change_pct,
                z_score=representative.z_score,
                percentile=representative.percentile,
                status=representative.status,
                group=dict(group_items),
                date=aggregate_date,
                time_bucket=None,
                metadata={},
                reference_sample_size=sum(
                    row.reference_sample_size or 0 for row in group_rows if row.reference_sample_size is not None
                )
                or None,
                comparison_confidence=representative.comparison_confidence,
                comparison_method=representative.comparison_method,
            )
        )

    return tuple(
        sorted(
            aggregated,
            key=lambda row: (
                _summary_status_priority(row.status),
                -(abs(row.z_score or 0.0)),
                -(abs(row.change_pct or 0.0)),
                row.metric_name,
                tuple(sorted((str(key), str(value)) for key, value in row.group.items())),
            ),
        )
    )


def _select_metric_level_summary_comparisons(
    comparisons: tuple[MetricComparison, ...],
) -> tuple[MetricComparison, ...]:
    best_by_metric: dict[str, MetricComparison] = {}
    for comparison in comparisons:
        current = best_by_metric.get(comparison.metric_name)
        if current is None:
            best_by_metric[comparison.metric_name] = comparison
            continue
        if (
            _summary_status_priority(comparison.status),
            -(abs(comparison.z_score or 0.0)),
            -(abs(comparison.change_pct or 0.0)),
        ) < (
            _summary_status_priority(current.status),
            -(abs(current.z_score or 0.0)),
            -(abs(current.change_pct or 0.0)),
        ):
            best_by_metric[comparison.metric_name] = comparison
    return tuple(
        sorted(
            best_by_metric.values(),
            key=lambda row: (
                _summary_status_priority(row.status),
                -(abs(row.z_score or 0.0)),
                -(abs(row.change_pct or 0.0)),
                row.metric_name,
            ),
        )
    )


def _summary_status_priority(status: str) -> int:
    if status == "alert":
        return 0
    if status == "watch":
        return 1
    if status == "comparison_only":
        return 2
    return 3


def _avg_numeric(values: Iterable[float | int | None]) -> float | None:
    observed: list[float] = []
    for value in values:
        if value is None:
            continue
        numeric = float(value)
        if isfinite(numeric):
            observed.append(numeric)
    if not observed:
        return None
    return sum(observed) / len(observed)


def _aggregate_metric_central_value(metric_name: str, values: Iterable[float | int | None]) -> float | None:
    observed: list[float] = []
    for value in values:
        if value is None:
            continue
        numeric = float(value)
        if isfinite(numeric):
            observed.append(numeric)
    if not observed:
        return None
    if "volatility" in metric_name:
        variance = sum(item * item for item in observed) / len(observed)
        return sqrt(variance)
    return sum(observed) / len(observed)


def _build_summary_story_charts(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> list[PlotlyChart]:
    if not report_input.reference_series or options.max_summary_story_charts == 0:
        return []

    current_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: _series_for_level(series, "intraday")
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }

    charts = []

    for metric_name in options.activity_distribution_metric_names:
        target_series = current_by_metric.get(metric_name)
        reference_series = reference_by_metric.get(metric_name)
        if target_series is None or reference_series is None:
            continue
        definition = _require_definition(metric_name, definitions)
        charts.append(
            build_activity_intraday_distribution_chart(
                f"Intraday {definition.label} Distribution",
                reference_series=reference_series,
                target_series=target_series,
                metric_definition=definition,
                help_text=options.activity_distribution_help_text,
            )
        )
        if len(charts) >= options.max_summary_story_charts:
            return charts

    for metric_name in options.displayed_liquidity_metric_names:
        target_series = current_by_metric.get(metric_name)
        reference_series = reference_by_metric.get(metric_name)
        if target_series is None or reference_series is None:
            continue
        definition = _require_definition(metric_name, definitions)
        charts.append(
            build_reference_target_intraday_profile_chart(
                f"{definition.label} intraday profile",
                reference_series=reference_series,
                target_series=target_series,
                metric_definition=definition,
                group_by=("market_cap_bucket", "segment", "sector", "venue"),
                max_groups=options.max_displayed_liquidity_groups,
                help_text=options.displayed_liquidity_help_text,
            )
        )
        if len(charts) >= options.max_summary_story_charts:
            return charts

    return charts


def _build_activity_distribution_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_activity_distribution_page or not report_input.reference_series:
        return None

    current_by_metric = {
        series.metric_name: series
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: series
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    charts = []
    for metric_name in options.activity_distribution_metric_names:
        target_series = current_by_metric.get(metric_name)
        reference_series = reference_by_metric.get(metric_name)
        if target_series is None or reference_series is None:
            continue
        definition = _require_definition(metric_name, definitions)
        charts.append(
            build_activity_intraday_distribution_chart(
                f"Intraday {definition.label} Distribution",
                reference_series=reference_series,
                target_series=target_series,
                metric_definition=definition,
                help_text=options.activity_distribution_help_text,
            )
        )
        if (
            options.max_activity_distribution_charts is not None
            and len(charts) >= options.max_activity_distribution_charts
        ):
            break

    if not charts:
        return None
    return ReportPage(
        title=options.activity_distribution_page_title.strip(),
        plotly_charts=charts,
    )


def _build_displayed_liquidity_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_displayed_liquidity_page or not report_input.reference_series:
        return None

    current_by_metric = {
        series.metric_name: series
        for series in report_input.current_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    reference_by_metric = {
        series.metric_name: series
        for series in report_input.reference_series
        if not _series_has_symbol_scope(series, options.symbol_group_keys)
    }
    charts = []
    for metric_name in options.displayed_liquidity_metric_names:
        target_series = current_by_metric.get(metric_name)
        reference_series = reference_by_metric.get(metric_name)
        if target_series is None or reference_series is None:
            continue
        definition = _require_definition(metric_name, definitions)
        charts.append(
            build_reference_target_intraday_profile_chart(
                f"{definition.label} intraday profile",
                reference_series=reference_series,
                target_series=target_series,
                metric_definition=definition,
                group_by=("market_cap_bucket", "segment", "sector", "venue"),
                max_groups=options.max_displayed_liquidity_groups,
                help_text=options.displayed_liquidity_help_text,
            )
        )
        if options.max_displayed_liquidity_charts is not None and len(charts) >= options.max_displayed_liquidity_charts:
            break

    if not charts:
        return None
    return ReportPage(
        title=options.displayed_liquidity_page_title.strip(),
        plotly_charts=charts,
    )


def _build_daily_trend_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_daily_trend_page or not report_input.reference_series:
        return None

    reference_by_metric = {
        series.metric_name: _series_for_level(series, "daily")
        for series in report_input.reference_series
    }
    charts = []
    for target_series in report_input.current_series:
        if _is_toxicity_reversion_metric(target_series.metric_name):
            continue
        target_series = _series_for_level(target_series, "daily")
        definition = _require_definition(target_series.metric_name, definitions)
        charts.append(
            build_reference_target_trend_chart(
                f"{definition.label} daily reference-to-target trend",
                reference_series=reference_by_metric.get(target_series.metric_name),
                target_series=target_series,
                metric_definition=definition,
                group_by=("market_cap_bucket",),
                y_axis_label=_metric_axis_label(definition),
                help_text=options.daily_trend_help_text,
                max_points=options.max_chart_points,
                x_axis_label="Trading day",
            )
        )

    if not charts:
        return None

    return ReportPage(
        title=options.daily_trend_page_title.strip(),
        time_series_charts=charts,
    )


def _build_toxicity_reversion_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_toxicity_reversion_page:
        return None
    return build_toxicity_reversion_page(
        report_input.current_series,
        definitions,
        comparisons=report_input.comparisons,
        options=ToxicityReversionPageOptions(
            title=options.toxicity_reversion_page_title,
            help_text=options.toxicity_reversion_help_text,
            max_charts=options.max_toxicity_reversion_charts,
            max_points_per_chart=options.max_toxicity_reversion_points_per_chart,
            context_ranking=options.toxicity_reversion_context_ranking,
            venue_order=options.toxicity_reversion_venue_order,
            horizon_order=options.toxicity_reversion_horizon_order,
            max_comments=options.max_toxicity_reversion_comments,
        ),
    )


def _build_symbol_anomaly_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    symbol_detail_pages: tuple[ReportPage, ...],
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_symbol_anomaly_page:
        return None
    page = build_symbol_anomaly_page(
        report_input.comparisons,
        definitions,
        options=SymbolAnomalyPageOptions(
            title=options.symbol_anomaly_page_title,
            table_title=options.symbol_anomaly_table_title,
            help_text=options.symbol_anomaly_help_text,
            max_symbols=options.max_symbol_anomalies,
            symbol_group_keys=options.symbol_group_keys,
        ),
    )
    if page is None or not options.include_symbol_detail_index:
        return page

    index_block = build_symbol_detail_index_block(
        report_input.comparisons,
        symbol_detail_pages,
        definitions,
        options=SymbolDetailIndexOptions(
            title=options.symbol_detail_index_title,
            help_text=options.symbol_detail_index_help_text,
            max_symbols=options.max_symbol_detail_pages,
            symbol_group_keys=options.symbol_group_keys,
        ),
    )
    if index_block is None:
        return page
    return ReportPage(
        title=page.title,
        metric_cards=page.metric_cards,
        metric_tables=page.metric_tables,
        time_series_charts=page.time_series_charts,
        plotly_charts=page.plotly_charts,
        heatmaps=page.heatmaps,
        commentary_blocks=page.commentary_blocks,
        html_blocks=[*page.html_blocks, index_block],
        anchor_id=page.anchor_id,
    )


def _build_symbol_detail_pages(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> tuple[ReportPage, ...]:
    if not options.include_symbol_detail_pages:
        return ()
    return build_symbol_detail_pages(
        report_input.comparisons,
        (*report_input.current_series, *report_input.symbol_series),
        definitions,
        options=SymbolDetailPageOptions(
            title_template=options.symbol_detail_page_title_template,
            help_text=options.symbol_detail_help_text,
            max_symbols=options.max_symbol_detail_pages,
            symbol_group_keys=options.symbol_group_keys,
            max_chart_points=options.max_chart_points,
            max_heatmap_cells=options.max_heatmap_cells,
            include_heatmaps=options.include_intraday_heatmaps,
        ),
    )


def _build_drilldown_page(
    report_input: MarketReportInput,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage | None:
    if not options.include_drilldown_page:
        return None
    return build_drilldown_report_page(
        report_input.comparisons,
        definitions,
        options=DrilldownReportPageOptions(
            title=options.drilldown_page_title,
            table_title=options.drilldown_table_title,
            help_text=options.drilldown_help_text,
            selection=DrilldownSelectionOptions(
                group_keys=options.drilldown_group_keys,
                max_rows=options.max_drilldown_rows,
                symbol_group_keys=options.symbol_group_keys,
            ),
        ),
    )


def _detail_current_series(
    current_series: tuple[MetricTimeSeries, ...],
    *,
    options: MarketReportOptions,
    toxicity_reversion_page_present: bool,
) -> tuple[MetricTimeSeries, ...]:
    if not toxicity_reversion_page_present or options.include_toxicity_reversion_metrics_in_detail_page:
        return current_series
    return tuple(series for series in current_series if not _is_toxicity_reversion_metric(series.metric_name))


def _build_detail_page(
    current_series: tuple[MetricTimeSeries, ...],
    definitions: Mapping[str, MetricDefinition],
    *,
    options: MarketReportOptions,
) -> ReportPage:
    charts = []
    heatmaps = []
    for series in current_series:
        definition = _require_definition(series.metric_name, definitions)
        charts.append(
            build_intraday_time_bucket_chart(
                f"{definition.label} intraday time-bucket trend",
                series,
                definition,
                group_by=("market_cap_bucket",),
                y_axis_label=_metric_axis_label(definition),
                help_text=options.detail_help_text,
                max_points=options.max_chart_points,
            )
        )
        if options.include_intraday_heatmaps:
            heatmaps.append(
                build_heatmap(
                    f"{definition.label} bucket × market-cap view",
                    series,
                    definition,
                    group_by=("market_cap_bucket",),
                    y_axis_label="Market cap bucket",
                    help_text=options.detail_help_text,
                    max_cells=options.max_heatmap_cells,
                )
            )

    return ReportPage(
        title=options.detail_page_title.strip(),
        time_series_charts=charts,
        heatmaps=heatmaps,
    )


def _series_has_symbol_scope(
    series: MetricTimeSeries,
    symbol_group_keys: tuple[str, ...],
) -> bool:
    symbol_keys = {key.casefold() for key in symbol_group_keys}
    for observation in series.observations:
        if symbol_keys.intersection(key.casefold() for key in observation.group):
            return True
    return False


def _is_toxicity_reversion_metric(metric_name: str) -> bool:
    return metric_name.startswith("primary_quote_reversion_") and metric_name.endswith("_bps")


def _require_definition(
    metric_name: str,
    definitions: Mapping[str, MetricDefinition],
) -> MetricDefinition:
    try:
        return definitions[metric_name]
    except KeyError as exc:
        raise ValueError(f"metric definition is required for market report metric: {metric_name}") from exc


def _metric_axis_label(definition: MetricDefinition) -> str:
    if definition.unit:
        return f"{definition.label} ({definition.unit})"
    return definition.label


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_optional_non_empty(value: str | None, field_name: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"{field_name} must not be empty when supplied")


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_symbol_group_keys(symbol_group_keys: tuple[str, ...]) -> None:
    if not symbol_group_keys:
        raise ValueError("symbol_group_keys must not be empty")
    for key in symbol_group_keys:
        if not key.strip():
            raise ValueError("symbol_group_keys must not contain empty values")


def _require_toxicity_context_ranking(value: str, field_name: str) -> None:
    if value not in TOXICITY_CONTEXT_RANKINGS:
        raise ValueError(f"{field_name} must be one of: " + ", ".join(TOXICITY_CONTEXT_RANKINGS))


def _require_reversion_order(values: tuple[str, ...], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        if not value.strip():
            raise ValueError(f"{field_name} must not contain empty values")


def _require_drilldown_group_keys(drilldown_group_keys: tuple[str, ...]) -> None:
    if not drilldown_group_keys:
        raise ValueError("drilldown_group_keys must not be empty")
    for key in drilldown_group_keys:
        if not key.strip():
            raise ValueError("drilldown_group_keys must not contain empty values")


def _require_metric_name_sequence(values: tuple[str, ...], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        if not value.strip():
            raise ValueError(f"{field_name} must not contain empty values")


def _require_one_of(value: str, field_name: str, allowed_values: tuple[str, ...]) -> None:
    normalized = value.strip().lower()
    if normalized not in allowed_values:
        raise ValueError(f"{field_name} must be one of: " + ", ".join(allowed_values))


__all__ = [
    "MarketReportInput",
    "MarketReportOptions",
    "build_market_monitor_report",
]
