"""Canonical production-format market monitor report assembly.

This module owns the single report-document shape used by both production
workflows and the deterministic mock-data demo. Data sources may differ, but the
report pages, component ordering, metric-help handling, and packaged Jinja
rendering path should remain shared.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison, MetricTimeSeries
from mmsr.report.components import ReportBranding, ReportDocument, ReportPage
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
    brand_name: str | None = "mmsr"
    generated_at_text: str | None = None
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
    include_activity_distribution_page: bool = True
    activity_distribution_metric_names: tuple[str, ...] = (
        "turnover",
        "volume",
        "trade_count",
    )
    max_activity_distribution_charts: int | None = None
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
    max_displayed_liquidity_charts: int | None = None
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
    include_toxicity_reversion_page: bool = True
    include_toxicity_reversion_metrics_in_detail_page: bool = False
    toxicity_reversion_page_title: str = "Cross-Venue Toxicity"
    toxicity_reversion_help_text: str = (
        "Primary-quote reversion by venue and horizon. The x-axis is the "
        "configured reversion horizon, the y-axis is reversion in bps, and each "
        "line is one execution venue. Positive values indicate adverse movement "
        "in the aggressive-trade direction."
    )
    max_toxicity_reversion_charts: int | None = 6
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
    activity_distribution_page = _build_activity_distribution_page(
        report_input,
        definitions,
        options=resolved_options,
    )
    if activity_distribution_page is not None:
        pages.append(activity_distribution_page)
    displayed_liquidity_page = _build_displayed_liquidity_page(
        report_input,
        definitions,
        options=resolved_options,
    )
    if displayed_liquidity_page is not None:
        pages.append(displayed_liquidity_page)
    daily_trend_page = _build_daily_trend_page(
        report_input,
        definitions,
        options=resolved_options,
    )
    if daily_trend_page is not None:
        pages.append(daily_trend_page)
    toxicity_reversion_page = _build_toxicity_reversion_page(
        report_input,
        definitions,
        options=resolved_options,
    )
    if toxicity_reversion_page is not None:
        pages.append(toxicity_reversion_page)
    detail_series = _detail_current_series(
        report_input.current_series,
        options=resolved_options,
        toxicity_reversion_page_present=toxicity_reversion_page is not None,
    )
    detail_page = _build_detail_page(
        detail_series,
        definitions,
        options=resolved_options,
    )
    symbol_detail_pages = _build_symbol_detail_pages(
        report_input,
        definitions,
        options=resolved_options,
    )
    symbol_anomaly_page = _build_symbol_anomaly_page(
        report_input,
        definitions,
        symbol_detail_pages=symbol_detail_pages,
        options=resolved_options,
    )
    if symbol_anomaly_page is not None:
        pages.append(symbol_anomaly_page)
    pages.extend(symbol_detail_pages)
    drilldown_page = _build_drilldown_page(
        report_input,
        definitions,
        options=resolved_options,
    )
    if drilldown_page is not None:
        pages.append(drilldown_page)
    pages.append(detail_page)

    document = ReportDocument(
        title=resolved_options.title.strip(),
        pages=pages,
        branding=ReportBranding(
            brand_name=(None if resolved_options.brand_name is None else resolved_options.brand_name.strip())
        ),
        generated_at_text=(
            None if resolved_options.generated_at_text is None else resolved_options.generated_at_text.strip()
        ),
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
    comparison_options = ComparisonSectionOptions(
        max_metric_cards=options.max_metric_cards,
        max_comments=options.max_comments,
        section_summary_scope_label=options.summary_scope_label,
    )
    base_page = build_comparison_report_page(
        options.summary_page_title,
        report_input.comparisons,
        definitions,
        options=comparison_options,
    )
    executive_overview = build_executive_market_overview_block(
        report_input.comparisons,
        definitions,
        options=ExecutiveOverviewOptions(
            title=options.executive_overview_title,
            help_text=options.executive_overview_help_text,
            max_metric_summaries=options.max_overview_metrics,
        ),
    )
    comparison_table = build_comparison_metric_table(
        options.comparison_table_title,
        report_input.comparisons,
        definitions,
        max_rows=options.max_table_rows,
        help_text=options.comparison_help_text,
    )
    return ReportPage(
        title=base_page.title,
        html_blocks=[executive_overview],
        metric_cards=base_page.metric_cards,
        metric_tables=[comparison_table],
        commentary_blocks=base_page.commentary_blocks,
    )


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
                f"{definition.label} cumulative intraday distribution",
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

    reference_by_metric = {series.metric_name: series for series in report_input.reference_series}
    charts = []
    for target_series in report_input.current_series:
        if _is_toxicity_reversion_metric(target_series.metric_name):
            continue
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


__all__ = [
    "MarketReportInput",
    "MarketReportOptions",
    "build_market_monitor_report",
]
