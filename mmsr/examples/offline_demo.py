"""Deterministic mock-data demo report assembly.

This module adapts synthetic fixture data into the canonical production-format
report builder. The demo and production report share one report-document shape
and one packaged Jinja template; only the data source changes.
"""

from __future__ import annotations

from dataclasses import dataclass

from mmsr.examples.offline_fixtures import (
    OfflineSampleMetrics,
    build_offline_sample_metrics,
)
from mmsr.report.components import ReportDocument
from mmsr.report.market_report import (
    MarketReportInput,
    MarketReportOptions,
    build_market_monitor_report,
)


@dataclass(frozen=True)
class OfflineDemoReportOptions:
    """Presentation options for the deterministic mock-data demo report.

    These options intentionally map onto ``MarketReportOptions`` so the demo can
    exercise the same report layout that production kdb-backed runs will use.
    """

    title: str = "Japanese Market Microstructure Monitor — Mock Data Demo"
    brand_name: str = "mmsr mock data sample"
    generated_at_text: str = "deterministic mock data sample"
    summary_page_title: str = "Market Summary"
    detail_page_title: str = "Intraday Detail"
    comparison_table_title: str = "Current versus reference"
    comparison_help_text: str = (
        "Mock current observations compared with 30 historical trading-day "
        "reference observations for the same metric, bucket, and group."
    )
    detail_help_text: str = (
        "Mock fixture observations are already normalized and use the same "
        "report-boundary schema expected from production kdb-backed metric runs."
    )
    daily_trend_page_title: str = "Reference and Target Daily Trends"
    daily_trend_help_text: str = (
        "Mock reference observations followed by the target report date. The "
        "line visual keeps the trading day on the x-axis and carries bucket and "
        "market-cap context as series."
    )
    include_daily_trend_page: bool = True
    include_intraday_heatmaps: bool = False
    include_metric_definitions_appendix: bool = True
    max_metric_cards: int = 6
    max_comments: int = 5
    max_table_rows: int | None = 12
    max_chart_points: int | None = None
    max_heatmap_cells: int | None = None
    include_drilldown_page: bool = True
    max_drilldown_rows: int | None = 12
    include_automated_insights: bool = False
    detailed_metric_trends_granularity: str = "daily"

    def __post_init__(self) -> None:
        _require_non_empty(self.title, "title")
        _require_non_empty(self.brand_name, "brand_name")
        _require_non_empty(self.generated_at_text, "generated_at_text")
        _require_non_empty(self.summary_page_title, "summary_page_title")
        _require_non_empty(self.detail_page_title, "detail_page_title")
        _require_non_empty(self.comparison_table_title, "comparison_table_title")
        _require_non_empty(self.comparison_help_text, "comparison_help_text")
        _require_non_empty(self.detail_help_text, "detail_help_text")
        _require_non_empty(self.daily_trend_page_title, "daily_trend_page_title")
        _require_non_empty(self.daily_trend_help_text, "daily_trend_help_text")
        _require_non_negative(self.max_metric_cards, "max_metric_cards")
        _require_non_negative(self.max_comments, "max_comments")
        _require_optional_non_negative(self.max_table_rows, "max_table_rows")
        _require_optional_non_negative(self.max_chart_points, "max_chart_points")
        _require_optional_non_negative(self.max_heatmap_cells, "max_heatmap_cells")
        _require_optional_non_negative(self.max_drilldown_rows, "max_drilldown_rows")
        _require_one_of(
            self.detailed_metric_trends_granularity,
            "detailed_metric_trends_granularity",
            ("daily", "weekly", "monthly", "quarterly", "yearly"),
        )

    def to_market_report_options(self) -> MarketReportOptions:
        """Return equivalent canonical report options for the mock-data demo."""

        return MarketReportOptions(
            title=self.title,
            brand_name=self.brand_name,
            generated_at_text=self.generated_at_text,
            summary_page_title=self.summary_page_title,
            detail_page_title=self.detail_page_title,
            comparison_table_title=self.comparison_table_title,
            comparison_help_text=self.comparison_help_text,
            detail_help_text=self.detail_help_text,
            daily_trend_page_title=self.daily_trend_page_title,
            daily_trend_help_text=self.daily_trend_help_text,
            include_daily_trend_page=self.include_daily_trend_page,
            include_intraday_heatmaps=self.include_intraday_heatmaps,
            summary_scope_label="mock data sample",
            include_metric_definitions_appendix=(self.include_metric_definitions_appendix),
            max_metric_cards=self.max_metric_cards,
            max_comments=self.max_comments,
            max_table_rows=self.max_table_rows,
            max_chart_points=self.max_chart_points,
            max_heatmap_cells=self.max_heatmap_cells,
            include_drilldown_page=self.include_drilldown_page,
            max_drilldown_rows=self.max_drilldown_rows,
            include_automated_insights=self.include_automated_insights,
            detailed_metric_trends_granularity=self.detailed_metric_trends_granularity,
        )


def build_offline_demo_report(
    sample_metrics: OfflineSampleMetrics | None = None,
    *,
    options: OfflineDemoReportOptions | None = None,
) -> ReportDocument:
    """Build the production-format report document from mock fixture metrics.

    The builder is an adapter only: it creates ``MarketReportInput`` from
    deterministic fixtures, then delegates to ``build_market_monitor_report``.
    It does not maintain a separate offline-only report layout.
    """

    sample = sample_metrics or build_offline_sample_metrics()
    resolved_options = options or OfflineDemoReportOptions()
    return build_market_monitor_report(
        MarketReportInput(
            metric_definitions=sample.metric_definitions,
            current_series=sample.current_series,
            comparisons=sample.comparisons,
            reference_series=sample.reference_series,
            symbol_series=sample.symbol_current_series,
        ),
        options=resolved_options.to_market_report_options(),
    )


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_one_of(value: str, field_name: str, allowed_values: tuple[str, ...]) -> None:
    if value.strip().lower() not in allowed_values:
        raise ValueError(f"{field_name} must be one of: " + ", ".join(allowed_values))


__all__ = [
    "OfflineDemoReportOptions",
    "build_offline_demo_report",
]
