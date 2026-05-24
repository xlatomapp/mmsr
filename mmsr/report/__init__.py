"""Report component and section-building helpers."""

from mmsr.report.components import (
    CommentaryBlock,
    Heatmap,
    HeatmapCell,
    HtmlBlock,
    MetricCard,
    MetricTable,
    MetricTableRow,
    ReportBranding,
    ReportDocument,
    ReportPage,
    TimeSeriesChart,
    TimeSeriesChartPoint,
)
from mmsr.report.metric_docs import (
    MetricDefinitionsAppendixOptions,
    append_metric_definitions_appendix,
    build_metric_definitions_appendix_page,
    collect_metric_definitions_from_pages,
    metric_definitions_markdown,
)
from mmsr.report.sections import (
    ComparisonSectionOptions,
    build_comparison_metric_table,
    build_comparison_report_page,
    build_heatmap,
    build_time_series_chart,
)

__all__ = [
    "CommentaryBlock",
    "ComparisonSectionOptions",
    "Heatmap",
    "HeatmapCell",
    "HtmlBlock",
    "MetricCard",
    "MetricTable",
    "MetricTableRow",
    "TimeSeriesChart",
    "TimeSeriesChartPoint",
    "MetricDefinitionsAppendixOptions",
    "ReportBranding",
    "ReportDocument",
    "ReportPage",
    "append_metric_definitions_appendix",
    "build_comparison_metric_table",
    "build_comparison_report_page",
    "build_heatmap",
    "build_metric_definitions_appendix_page",
    "build_time_series_chart",
    "collect_metric_definitions_from_pages",
    "metric_definitions_markdown",
]
