"""Report-size and component-budget helpers.

These utilities keep default report output bounded for desk review usability.
They are deterministic and operate on already-built report documents and HTML.
"""

from __future__ import annotations

from dataclasses import dataclass

from mmsr.report.components import ReportDocument


@dataclass(frozen=True)
class ReportBudgetSnapshot:
    """Measured report footprint and component counts."""

    page_count: int
    html_size_bytes: int
    metric_table_count: int
    metric_row_count: int
    time_series_chart_count: int
    plotly_chart_count: int
    heatmap_count: int

    @property
    def total_chart_count(self) -> int:
        return self.time_series_chart_count + self.plotly_chart_count + self.heatmap_count


@dataclass(frozen=True)
class ReportBudgetLimits:
    """Hard limits for bounded default report growth."""

    max_html_size_bytes: int = 1_500_000
    max_total_chart_count: int = 32
    max_metric_table_count: int = 12
    max_metric_row_count: int = 400
    max_page_count: int = 16


def snapshot_report_budget(document: ReportDocument, html: str) -> ReportBudgetSnapshot:
    """Return deterministic footprint measurements for one rendered report."""

    metric_table_count = 0
    metric_row_count = 0
    time_series_chart_count = 0
    plotly_chart_count = 0
    heatmap_count = 0
    for page in document.pages:
        metric_table_count += len(page.metric_tables)
        metric_row_count += sum(len(table.rows) for table in page.metric_tables)
        time_series_chart_count += len(page.time_series_charts)
        plotly_chart_count += len(page.plotly_charts)
        heatmap_count += len(page.heatmaps)

    return ReportBudgetSnapshot(
        page_count=len(document.pages),
        html_size_bytes=len(html.encode("utf-8")),
        metric_table_count=metric_table_count,
        metric_row_count=metric_row_count,
        time_series_chart_count=time_series_chart_count,
        plotly_chart_count=plotly_chart_count,
        heatmap_count=heatmap_count,
    )


def evaluate_report_budget(
    snapshot: ReportBudgetSnapshot,
    limits: ReportBudgetLimits,
) -> tuple[str, ...]:
    """Return deterministic violation messages for exceeded limits."""

    violations: list[str] = []
    if snapshot.page_count > limits.max_page_count:
        violations.append(f"page_count {snapshot.page_count} exceeds {limits.max_page_count}")
    if snapshot.html_size_bytes > limits.max_html_size_bytes:
        violations.append(f"html_size_bytes {snapshot.html_size_bytes} exceeds {limits.max_html_size_bytes}")
    if snapshot.total_chart_count > limits.max_total_chart_count:
        violations.append(f"total_chart_count {snapshot.total_chart_count} exceeds {limits.max_total_chart_count}")
    if snapshot.metric_table_count > limits.max_metric_table_count:
        violations.append(f"metric_table_count {snapshot.metric_table_count} exceeds {limits.max_metric_table_count}")
    if snapshot.metric_row_count > limits.max_metric_row_count:
        violations.append(f"metric_row_count {snapshot.metric_row_count} exceeds {limits.max_metric_row_count}")
    return tuple(violations)
