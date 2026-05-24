"""Deterministic offline demo report assembly.

This module wires the synthetic fixture data into report-layer components without
connecting to kdb+, importing PyKX, writing output files, or calling an LLM.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricTimeSeries
from mmsr.report.components import ReportBranding, ReportDocument, ReportPage
from mmsr.report.metric_docs import append_metric_definitions_appendix
from mmsr.report.sections import (
    ComparisonSectionOptions,
    build_comparison_metric_table,
    build_comparison_report_page,
    build_heatmap,
    build_time_series_chart,
)

from mmsr.examples.offline_fixtures import (
    OfflineSampleMetrics,
    build_offline_sample_metrics,
)


@dataclass(frozen=True)
class OfflineDemoReportOptions:
    """Presentation options for the deterministic offline demo report."""

    title: str = "Japanese Market Microstructure Monitor — Offline Demo"
    brand_name: str = "mmsr offline sample"
    generated_at_text: str = "deterministic offline sample"
    summary_page_title: str = "Offline Market Summary"
    detail_page_title: str = "Offline Intraday Detail"
    comparison_table_title: str = "Current versus synthetic reference"
    comparison_help_text: str = (
        "Synthetic current observations compared with 30 historical trading-day "
        "reference observations for the same metric, bucket, and group."
    )
    detail_help_text: str = (
        "Offline fixture observations are already normalized and are used only "
        "to demonstrate report assembly without a live kdb connection."
    )
    include_metric_definitions_appendix: bool = True
    max_metric_cards: int = 6
    max_comments: int = 5
    max_table_rows: int | None = None
    max_chart_points: int | None = None
    max_heatmap_cells: int | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.title, "title")
        _require_non_empty(self.brand_name, "brand_name")
        _require_non_empty(self.generated_at_text, "generated_at_text")
        _require_non_empty(self.summary_page_title, "summary_page_title")
        _require_non_empty(self.detail_page_title, "detail_page_title")
        _require_non_empty(self.comparison_table_title, "comparison_table_title")
        _require_non_empty(self.comparison_help_text, "comparison_help_text")
        _require_non_empty(self.detail_help_text, "detail_help_text")
        _require_non_negative(self.max_metric_cards, "max_metric_cards")
        _require_non_negative(self.max_comments, "max_comments")
        _require_optional_non_negative(self.max_table_rows, "max_table_rows")
        _require_optional_non_negative(self.max_chart_points, "max_chart_points")
        _require_optional_non_negative(self.max_heatmap_cells, "max_heatmap_cells")


def build_offline_demo_report(
    sample_metrics: OfflineSampleMetrics | None = None,
    *,
    options: OfflineDemoReportOptions | None = None,
) -> ReportDocument:
    """Build a deterministic report document from offline sample metrics.

    The builder is a pure report assembly path. It consumes synthetic
    ``MetricTimeSeries`` and precomputed ``MetricComparison`` objects, then
    produces a ``ReportDocument`` with cards, a comparison table, deterministic
    template commentary, chart/heatmap placeholders, and an optional metric
    definitions appendix.
    """

    sample = sample_metrics or build_offline_sample_metrics()
    resolved_options = options or OfflineDemoReportOptions()
    definitions = dict(sample.metric_definitions)

    summary_page = _build_summary_page(
        sample,
        definitions,
        options=resolved_options,
    )
    detail_page = _build_detail_page(
        sample.current_series,
        definitions,
        options=resolved_options,
    )

    document = ReportDocument(
        title=resolved_options.title.strip(),
        pages=[summary_page, detail_page],
        branding=ReportBranding(brand_name=resolved_options.brand_name.strip()),
        generated_at_text=resolved_options.generated_at_text.strip(),
    )
    if not resolved_options.include_metric_definitions_appendix:
        return document
    return append_metric_definitions_appendix(document)


def _build_summary_page(
    sample: OfflineSampleMetrics,
    definitions: Mapping[str, MetricDefinition],
    *,
    options: OfflineDemoReportOptions,
) -> ReportPage:
    comparison_options = ComparisonSectionOptions(
        max_metric_cards=options.max_metric_cards,
        max_comments=options.max_comments,
        section_summary_scope_label="offline synthetic sample",
    )
    base_page = build_comparison_report_page(
        options.summary_page_title,
        sample.comparisons,
        definitions,
        options=comparison_options,
    )
    comparison_table = build_comparison_metric_table(
        options.comparison_table_title,
        sample.comparisons,
        definitions,
        max_rows=options.max_table_rows,
        help_text=options.comparison_help_text,
    )
    return ReportPage(
        title=base_page.title,
        metric_cards=base_page.metric_cards,
        metric_tables=[comparison_table],
        commentary_blocks=base_page.commentary_blocks,
    )


def _build_detail_page(
    current_series: tuple[MetricTimeSeries, ...],
    definitions: Mapping[str, MetricDefinition],
    *,
    options: OfflineDemoReportOptions,
) -> ReportPage:
    charts = []
    heatmaps = []
    for series in current_series:
        definition = _require_definition(series.metric_name, definitions)
        charts.append(
            build_time_series_chart(
                f"{definition.label} current observations",
                series,
                definition,
                group_by=("market_cap_bucket",),
                y_axis_label=_metric_axis_label(definition),
                help_text=options.detail_help_text,
                max_points=options.max_chart_points,
            )
        )
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


def _require_definition(
    metric_name: str,
    definitions: Mapping[str, MetricDefinition],
) -> MetricDefinition:
    try:
        return definitions[metric_name]
    except KeyError as exc:
        raise ValueError(
            "metric definition is required for offline demo report metric: "
            f"{metric_name}"
        ) from exc


def _metric_axis_label(definition: MetricDefinition) -> str:
    if definition.unit:
        return f"{definition.label} ({definition.unit})"
    return definition.label


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


__all__ = [
    "OfflineDemoReportOptions",
    "build_offline_demo_report",
]
