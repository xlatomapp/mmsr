"""Deterministic report section builders."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import isfinite
from typing import Any

from mmsr.analysis.commentary import (
    CommentaryFact,
    TemplateCommentaryEngine,
    commentary_facts_from_comparisons,
    section_summary_fact_from_comparisons,
)
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.report.components import (
    CommentaryBlock,
    Heatmap,
    HeatmapCell,
    MetricCard,
    MetricTable,
    MetricTableRow,
    PlotlyChart,
    ReportPage,
    TimeSeriesChart,
    TimeSeriesChartPoint,
)
from mmsr.presentation.labels import (
    format_comparison_scope_label,
    format_group_label,
    format_intraday_bucket_label,
)


@dataclass(frozen=True)
class ComparisonSectionOptions:
    """Presentation limits for deterministic comparison report sections."""

    commentary_title: str = "Commentary"
    max_metric_cards: int = 6
    max_comments: int = 5
    include_section_summary: bool = True
    section_summary_scope_label: str = "all comparisons"

    def __post_init__(self) -> None:
        if not self.commentary_title.strip():
            raise ValueError("commentary_title must not be empty")
        if self.max_metric_cards < 0:
            raise ValueError("max_metric_cards must be non-negative")
        if self.max_comments < 0:
            raise ValueError("max_comments must be non-negative")
        if not self.section_summary_scope_label.strip():
            raise ValueError("section_summary_scope_label must not be empty")


def build_comparison_report_page(
    title: str,
    comparisons: Sequence[MetricComparison],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    commentary_facts: Sequence[CommentaryFact] | None = None,
    options: ComparisonSectionOptions | None = None,
    commentary_engine: TemplateCommentaryEngine | None = None,
) -> ReportPage:
    """Build a deterministic report page from metric comparisons.

    The builder is intentionally report-layer glue. It does not calculate new
    analytics or call an LLM; it formats already-computed comparisons into
    metric cards with metric help text, then renders deterministic commentary
    from supplied or derived ``CommentaryFact`` objects.
    """

    page_title = title.strip()
    if not page_title:
        raise ValueError("title must not be empty")

    resolved_options = options or ComparisonSectionOptions()
    definitions = _metric_definition_map(metric_definitions)

    ordered_comparisons = tuple(
        sorted(
            comparisons,
            key=lambda comparison: _comparison_sort_key(comparison, definitions),
        )
    )
    _require_metric_definitions(ordered_comparisons, definitions)

    metric_cards = [
        _metric_card_from_comparison(comparison, definitions[comparison.metric_name])
        for comparison in ordered_comparisons[: resolved_options.max_metric_cards]
    ]

    facts = (
        tuple(commentary_facts)
        if commentary_facts is not None
        else _comparison_commentary_facts(
            page_title,
            ordered_comparisons,
            definitions,
            resolved_options,
        )
    )
    engine = commentary_engine or TemplateCommentaryEngine()
    comments = engine.generate(list(facts), max_comments=resolved_options.max_comments)

    commentary_blocks = (
        [CommentaryBlock(title=resolved_options.commentary_title, comments=comments)]
        if comments
        else []
    )
    return ReportPage(
        title=page_title,
        metric_cards=metric_cards,
        commentary_blocks=commentary_blocks,
    )


def build_comparison_metric_table(
    title: str,
    comparisons: Sequence[MetricComparison],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    max_rows: int | None = None,
    help_text: str | None = None,
) -> MetricTable:
    """Build a deterministic metric table from already-computed comparisons.

    Rows are sorted with the same severity-first ordering used for metric cards.
    The table is report-layer formatting only: it does not calculate metrics,
    comparisons, z-scores, or commentary.
    """

    table_title = title.strip()
    if not table_title:
        raise ValueError("title must not be empty")
    if max_rows is not None and max_rows < 0:
        raise ValueError("max_rows must be non-negative")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    definitions = _metric_definition_map(metric_definitions)
    ordered_comparisons = tuple(
        sorted(
            comparisons,
            key=lambda comparison: _comparison_sort_key(comparison, definitions),
        )
    )
    _require_metric_definitions(ordered_comparisons, definitions)

    selected_comparisons = (
        ordered_comparisons if max_rows is None else ordered_comparisons[:max_rows]
    )
    return MetricTable(
        title=table_title,
        rows=[
            _metric_table_row_from_comparison(
                comparison,
                definitions[comparison.metric_name],
            )
            for comparison in selected_comparisons
        ],
        help_text=None if help_text is None else help_text.strip(),
    )


def build_time_series_chart(
    title: str,
    series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None = None,
    max_points: int | None = None,
    x_axis_label: str = "Report period / bucket",
    y_axis_label: str | None = None,
    help_text: str | None = None,
) -> TimeSeriesChart:
    """Build a deterministic time-series chart.

    The builder formats already-normalized ``MetricTimeSeries`` observations for
    report rendering. It preserves observation order, date, time-bucket, group
    context, and numeric values for deterministic inline SVG rendering; it does
    not calculate metrics or invoke an external charting backend.
    """

    chart_title = title.strip()
    if not chart_title:
        raise ValueError("title must not be empty")
    if series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match series.metric_name: "
            f"{metric_definition.name} != {series.metric_name}"
        )
    if max_points is not None and max_points < 0:
        raise ValueError("max_points must be non-negative")
    if not x_axis_label.strip():
        raise ValueError("x_axis_label must not be empty")
    if y_axis_label is not None and not y_axis_label.strip():
        raise ValueError("y_axis_label must not be empty when supplied")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    observations = (
        series.observations if max_points is None else series.observations[:max_points]
    )
    return TimeSeriesChart(
        title=chart_title,
        metric=metric_definition,
        points=[
            _time_series_chart_point_from_observation(
                observation,
                metric_definition,
                group_by=group_by,
            )
            for observation in observations
        ],
        x_axis_label=x_axis_label.strip(),
        y_axis_label=None if y_axis_label is None else y_axis_label.strip(),
        help_text=None if help_text is None else help_text.strip(),
    )


def build_intraday_time_bucket_chart(
    title: str,
    series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None = None,
    max_points: int | None = None,
    x_axis_label: str = "Intraday time bucket",
    y_axis_label: str | None = None,
    help_text: str | None = None,
) -> TimeSeriesChart:
    """Build a deterministic intraday line chart with bucket labels on the x-axis.

    This visual is designed for dense intraday grids such as 1-minute buckets:
    the SVG keeps a fixed width, samples x-axis tick labels, and preserves every
    rendered observation in the backing data table. It avoids the unbounded
    width growth that a bucket-by-group heatmap can create for hundreds of
    buckets.
    """

    chart_title = title.strip()
    if not chart_title:
        raise ValueError("title must not be empty")
    if series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match series.metric_name: "
            f"{metric_definition.name} != {series.metric_name}"
        )
    if max_points is not None and max_points < 0:
        raise ValueError("max_points must be non-negative")
    if not x_axis_label.strip():
        raise ValueError("x_axis_label must not be empty")
    if y_axis_label is not None and not y_axis_label.strip():
        raise ValueError("y_axis_label must not be empty when supplied")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    observations = (
        series.observations if max_points is None else series.observations[:max_points]
    )
    return TimeSeriesChart(
        title=chart_title,
        metric=metric_definition,
        points=[
            _intraday_chart_point_from_observation(
                observation,
                metric_definition,
                group_by=group_by,
            )
            for observation in observations
        ],
        x_axis_label=x_axis_label.strip(),
        y_axis_label=None if y_axis_label is None else y_axis_label.strip(),
        help_text=None if help_text is None else help_text.strip(),
    )


def build_reference_target_trend_chart(
    title: str,
    *,
    reference_series: MetricTimeSeries | None,
    target_series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    group_by: Sequence[str] | None = None,
    max_points: int | None = None,
    x_axis_label: str = "Trading day",
    y_axis_label: str | None = None,
    help_text: str | None = None,
) -> TimeSeriesChart:
    """Build a daily line chart spanning reference and target observations.

    The report layer does not aggregate or recalculate metrics here. It simply
    places already-normalized reference rows before target rows, uses the
    observation date as the x-axis, and keeps intraday bucket plus configured
    group context in the series label.
    """

    chart_title = title.strip()
    if not chart_title:
        raise ValueError("title must not be empty")
    if target_series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match target_series.metric_name: "
            f"{metric_definition.name} != {target_series.metric_name}"
        )
    if (
        reference_series is not None
        and reference_series.metric_name != metric_definition.name
    ):
        raise ValueError(
            "metric_definition.name must match reference_series.metric_name: "
            f"{metric_definition.name} != {reference_series.metric_name}"
        )
    if max_points is not None and max_points < 0:
        raise ValueError("max_points must be non-negative")
    if not x_axis_label.strip():
        raise ValueError("x_axis_label must not be empty")
    if y_axis_label is not None and not y_axis_label.strip():
        raise ValueError("y_axis_label must not be empty when supplied")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    period_observations: list[tuple[MetricObservation, str]] = []
    if reference_series is not None:
        period_observations.extend(
            (observation, "reference")
            for observation in reference_series.observations
        )
    period_observations.extend(
        (observation, "target") for observation in target_series.observations
    )
    if max_points is not None:
        period_observations = period_observations[:max_points]

    return TimeSeriesChart(
        title=chart_title,
        metric=metric_definition,
        points=[
            _reference_target_chart_point_from_observation(
                observation,
                metric_definition,
                period_label=period_label,
                group_by=group_by,
            )
            for observation, period_label in period_observations
        ],
        x_axis_label=x_axis_label.strip(),
        y_axis_label=None if y_axis_label is None else y_axis_label.strip(),
        help_text=None if help_text is None else help_text.strip(),
    )


def build_activity_intraday_distribution_chart(
    title: str,
    *,
    reference_series: MetricTimeSeries,
    target_series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    help_text: str | None = None,
) -> PlotlyChart:
    """Build a compact Plotly activity-distribution diagnostic.

    The visual is designed for high-volume activity metrics such as turnover,
    volume, and trade count. It emits only derived arrays: current cumulative
    percent by intraday bucket, historical cumulative-percent box statistics by
    bucket, and reference/current session-share bars. It does not embed raw
    metric observation rows or create symbol-level plots.
    """

    chart_title = title.strip()
    if not chart_title:
        raise ValueError("title must not be empty")
    if target_series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match target_series.metric_name: "
            f"{metric_definition.name} != {target_series.metric_name}"
        )
    if reference_series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match reference_series.metric_name: "
            f"{metric_definition.name} != {reference_series.metric_name}"
        )
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    prepared = _prepare_activity_distribution_inputs(
        target_series=target_series,
        reference_series=reference_series,
    )
    figure = _activity_distribution_figure(
        title=chart_title,
        metric_definition=metric_definition,
        prepared=prepared,
    )
    return PlotlyChart(
        title=chart_title,
        metric=metric_definition,
        figure=figure,
        x_axis_label="Intraday bucket and session share",
        y_axis_label="Percent",
        help_text=None if help_text is None else help_text.strip(),
        data_summary=_activity_distribution_data_summary(prepared, figure),
    )


@dataclass(frozen=True)
class _ActivityDistributionInputs:
    bucket_labels: tuple[str, ...]
    current_cumulative_pct: tuple[float, ...]
    reference_cumulative_pct_by_bucket: Mapping[str, tuple[float, ...]]
    current_session_pct: Mapping[str, float]
    reference_session_pct: Mapping[str, float]
    reference_date_count: int


def _prepare_activity_distribution_inputs(
    *,
    target_series: MetricTimeSeries,
    reference_series: MetricTimeSeries,
) -> _ActivityDistributionInputs:
    current_values_by_date_bucket = _sum_observation_values_by_date_bucket(
        target_series.observations
    )
    reference_values_by_date_bucket = _sum_observation_values_by_date_bucket(
        reference_series.observations
    )
    current_bucket_values = _mean_values_by_bucket(current_values_by_date_bucket)

    bucket_labels = _ordered_activity_buckets(
        [*current_bucket_values.keys()]
        + [
            bucket
            for values_by_bucket in reference_values_by_date_bucket.values()
            for bucket in values_by_bucket
        ]
    )
    current_cumulative_pct = _cumulative_bucket_percentages(
        current_bucket_values,
        bucket_labels,
    )
    reference_cumulative_pct_by_bucket = _reference_cumulative_percentages_by_bucket(
        reference_values_by_date_bucket,
        bucket_labels,
    )

    return _ActivityDistributionInputs(
        bucket_labels=bucket_labels,
        current_cumulative_pct=current_cumulative_pct,
        reference_cumulative_pct_by_bucket=reference_cumulative_pct_by_bucket,
        current_session_pct=_mean_daily_session_share_percentages(
            target_series.observations
        ),
        reference_session_pct=_mean_daily_session_share_percentages(
            reference_series.observations
        ),
        reference_date_count=len(reference_values_by_date_bucket),
    )


def _activity_distribution_figure(
    *,
    title: str,
    metric_definition: MetricDefinition,
    prepared: _ActivityDistributionInputs,
) -> dict[str, Any]:
    q1: list[float | None] = []
    median: list[float | None] = []
    q3: list[float | None] = []
    lower: list[float | None] = []
    upper: list[float | None] = []
    for bucket in prepared.bucket_labels:
        values = prepared.reference_cumulative_pct_by_bucket.get(bucket, ())
        if values:
            q1.append(_percentile(values, 25))
            median.append(_percentile(values, 50))
            q3.append(_percentile(values, 75))
            lower.append(min(values))
            upper.append(max(values))
        else:
            q1.append(None)
            median.append(None)
            q3.append(None)
            lower.append(None)
            upper.append(None)

    traces: list[dict[str, Any]] = [
        {
            "type": "box",
            "name": "Reference cumulative % distribution",
            "x": list(prepared.bucket_labels),
            "q1": q1,
            "median": median,
            "q3": q3,
            "lowerfence": lower,
            "upperfence": upper,
            "boxpoints": False,
            "xaxis": "x",
            "yaxis": "y",
            "hovertemplate": (
                "%{x}<br>Q1 %{q1:.2f}%<br>Median %{median:.2f}%"
                "<br>Q3 %{q3:.2f}%<extra>Reference</extra>"
            ),
        },
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Current mean cumulative %",
            "x": list(prepared.bucket_labels),
            "y": list(prepared.current_cumulative_pct),
            "marker": {"symbol": "circle", "size": 8},
            "line": {"width": 3},
            "xaxis": "x",
            "yaxis": "y",
            "hovertemplate": "%{x}<br>%{y:.2f}%<extra>Current mean</extra>",
        },
    ]

    period_labels = ["Reference period", "Current period"]
    for session in _ACTIVITY_SESSION_ORDER:
        reference_pct = prepared.reference_session_pct.get(session, 0.0)
        current_pct = prepared.current_session_pct.get(session, 0.0)
        if reference_pct == 0.0 and current_pct == 0.0:
            continue
        traces.append(
            {
                "type": "bar",
                "name": session,
                "orientation": "h",
                "x": [reference_pct, current_pct],
                "y": period_labels,
                "xaxis": "x2",
                "yaxis": "y2",
                "hovertemplate": (
                    "%{y}<br>" + session + ": %{x:.2f}%<extra></extra>"
                ),
            }
        )

    return {
        "data": traces,
        "layout": {
            "template": "plotly_white",
            "height": 640,
            "margin": {"l": 80, "r": 24, "t": 24, "b": 104},
            "barmode": "stack",
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.2},
            "xaxis": {
                "domain": [0.0, 1.0],
                "anchor": "y",
                "title": "Intraday bucket",
                "type": "category",
                "categoryorder": "array",
                "categoryarray": list(prepared.bucket_labels),
            },
            "yaxis": {
                "domain": [0.42, 1.0],
                "anchor": "x",
                "title": "Cumulative percent of " + metric_definition.label,
                "ticksuffix": "%",
                "range": [0, 100],
            },
            "xaxis2": {
                "domain": [0.0, 1.0],
                "anchor": "y2",
                "title": "Percent of period",
                "ticksuffix": "%",
                "range": [0, 100],
            },
            "yaxis2": {
                "domain": [0.0, 0.24],
                "anchor": "x2",
                "title": "",
                "categoryorder": "array",
                "categoryarray": period_labels,
            },
            "annotations": [
                {
                    "text": title,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 1.08,
                    "showarrow": False,
                    "font": {"size": 14},
                    "xanchor": "left",
                },
                {
                    "text": "Session / auction share",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 0.31,
                    "showarrow": False,
                    "font": {"size": 13},
                    "xanchor": "left",
                },
            ],
        },
        "config": {"displaylogo": False, "responsive": True},
    }


def _activity_distribution_data_summary(
    prepared: _ActivityDistributionInputs,
    figure: Mapping[str, Any],
) -> str:
    traces = figure.get("data", ())
    trace_count = len(traces) if isinstance(traces, Sequence) else 0
    return (
        f"{len(prepared.bucket_labels):,} intraday buckets; "
        f"{prepared.reference_date_count:,} reference dates reduced to "
        "null-filtered percentile box statistics; current period rendered as "
        f"mean cumulative percentages; {trace_count:,} Plotly traces embedded. "
        "Raw observation rows and full value tables are omitted from the HTML."
    )


def build_reference_target_intraday_profile_chart(
    title: str,
    *,
    reference_series: MetricTimeSeries,
    target_series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    group_by: Sequence[str] | None = None,
    max_groups: int | None = 12,
    help_text: str | None = None,
) -> PlotlyChart:
    """Build a compact current-vs-history intraday profile visual.

    This visual is intended for non-additive market-state metrics such as quoted
    spread and top-of-book depth. It embeds historical per-bucket box statistics,
    a current-period bucket profile, and a capped group-level current-minus-
    reference delta bar. It deliberately avoids raw observation tables.
    """

    chart_title = title.strip()
    if not chart_title:
        raise ValueError("title must not be empty")
    if target_series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match target_series.metric_name: "
            f"{metric_definition.name} != {target_series.metric_name}"
        )
    if reference_series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match reference_series.metric_name: "
            f"{metric_definition.name} != {reference_series.metric_name}"
        )
    if max_groups is not None and max_groups < 0:
        raise ValueError("max_groups must be non-negative")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    prepared = _prepare_intraday_profile_inputs(
        target_series=target_series,
        reference_series=reference_series,
        group_by=group_by,
        max_groups=max_groups,
    )
    figure = _intraday_profile_figure(
        title=chart_title,
        metric_definition=metric_definition,
        prepared=prepared,
    )
    return PlotlyChart(
        title=chart_title,
        metric=metric_definition,
        figure=figure,
        x_axis_label="Intraday bucket and group delta",
        y_axis_label=metric_definition.unit or metric_definition.label,
        help_text=None if help_text is None else help_text.strip(),
        data_summary=_intraday_profile_data_summary(prepared, figure),
    )


@dataclass(frozen=True)
class _IntradayProfileInputs:
    bucket_labels: tuple[str, ...]
    current_values_by_bucket: Mapping[str, float]
    reference_values_by_bucket: Mapping[str, tuple[float, ...]]
    group_labels: tuple[str, ...]
    group_current_values: tuple[float, ...]
    group_reference_values: tuple[float, ...]
    reference_date_count: int


def _prepare_intraday_profile_inputs(
    *,
    target_series: MetricTimeSeries,
    reference_series: MetricTimeSeries,
    group_by: Sequence[str] | None,
    max_groups: int | None,
) -> _IntradayProfileInputs:
    current_bucket_values = _mean_observation_values_by_bucket(
        target_series.observations
    )
    reference_values_by_date_bucket = _mean_observation_values_by_date_bucket(
        reference_series.observations
    )
    bucket_labels = _ordered_activity_buckets(
        [*current_bucket_values.keys()]
        + [
            bucket
            for values_by_bucket in reference_values_by_date_bucket.values()
            for bucket in values_by_bucket
        ]
    )
    reference_values_by_bucket = _reference_profile_values_by_bucket(
        reference_values_by_date_bucket,
        bucket_labels,
    )
    group_rows = _profile_group_delta_rows(
        target_series.observations,
        reference_series.observations,
        group_by=() if group_by is None else group_by,
        max_groups=max_groups,
    )
    return _IntradayProfileInputs(
        bucket_labels=bucket_labels,
        current_values_by_bucket=current_bucket_values,
        reference_values_by_bucket=reference_values_by_bucket,
        group_labels=tuple(row[0] for row in group_rows),
        group_current_values=tuple(row[1] for row in group_rows),
        group_reference_values=tuple(row[2] for row in group_rows),
        reference_date_count=len(reference_values_by_date_bucket),
    )


def _intraday_profile_figure(
    *,
    title: str,
    metric_definition: MetricDefinition,
    prepared: _IntradayProfileInputs,
) -> dict[str, Any]:
    q1: list[float | None] = []
    median: list[float | None] = []
    q3: list[float | None] = []
    lower: list[float | None] = []
    upper: list[float | None] = []
    current_values: list[float | None] = []
    for bucket in prepared.bucket_labels:
        values = prepared.reference_values_by_bucket.get(bucket, ())
        if values:
            q1.append(_percentile(values, 25))
            median.append(_percentile(values, 50))
            q3.append(_percentile(values, 75))
            lower.append(min(values))
            upper.append(max(values))
        else:
            q1.append(None)
            median.append(None)
            q3.append(None)
            lower.append(None)
            upper.append(None)
        current_values.append(prepared.current_values_by_bucket.get(bucket))

    traces: list[dict[str, Any]] = [
        {
            "type": "box",
            "name": "Reference percentile distribution",
            "x": list(prepared.bucket_labels),
            "q1": q1,
            "median": median,
            "q3": q3,
            "lowerfence": lower,
            "upperfence": upper,
            "boxpoints": False,
            "xaxis": "x",
            "yaxis": "y",
            "hovertemplate": (
                "%{x}<br>Q1 %{q1:.4f}<br>Median %{median:.4f}"
                "<br>Q3 %{q3:.4f}<extra>Reference</extra>"
            ),
        },
        {
            "type": "scatter",
            "mode": "lines+markers",
            "name": "Current mean profile",
            "x": list(prepared.bucket_labels),
            "y": current_values,
            "marker": {"symbol": "circle", "size": 8},
            "line": {"width": 3},
            "xaxis": "x",
            "yaxis": "y",
            "hovertemplate": "%{x}<br>%{y:.4f}<extra>Current mean</extra>",
        },
    ]

    if prepared.group_labels:
        deltas = [
            current - reference
            for current, reference in zip(
                prepared.group_current_values,
                prepared.group_reference_values,
                strict=True,
            )
        ]
        traces.append(
            {
                "type": "bar",
                "name": "Current − reference",
                "orientation": "h",
                "x": deltas,
                "y": list(prepared.group_labels),
                "customdata": [
                    [current, reference]
                    for current, reference in zip(
                        prepared.group_current_values,
                        prepared.group_reference_values,
                        strict=True,
                    )
                ],
                "xaxis": "x2",
                "yaxis": "y2",
                "hovertemplate": (
                    "%{y}<br>Δ %{x:.4f}<br>Current %{customdata[0]:.4f}"
                    "<br>Reference %{customdata[1]:.4f}<extra></extra>"
                ),
            }
        )

    axis_unit = metric_definition.unit or metric_definition.label
    return {
        "data": traces,
        "layout": {
            "template": "plotly_white",
            "height": 640,
            "margin": {"l": 96, "r": 24, "t": 24, "b": 104},
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.2},
            "xaxis": {
                "domain": [0.0, 1.0],
                "anchor": "y",
                "title": "Intraday bucket",
                "type": "category",
                "categoryorder": "array",
                "categoryarray": list(prepared.bucket_labels),
            },
            "yaxis": {
                "domain": [0.42, 1.0],
                "anchor": "x",
                "title": axis_unit,
            },
            "xaxis2": {
                "domain": [0.0, 1.0],
                "anchor": "y2",
                "title": "Current minus reference (" + axis_unit + ")",
                "zeroline": True,
            },
            "yaxis2": {
                "domain": [0.0, 0.24],
                "anchor": "x2",
                "title": "",
                "autorange": "reversed",
            },
            "annotations": [
                {
                    "text": title,
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 1.08,
                    "showarrow": False,
                    "font": {"size": 14},
                    "xanchor": "left",
                },
                {
                    "text": "Largest group deltas",
                    "xref": "paper",
                    "yref": "paper",
                    "x": 0,
                    "y": 0.31,
                    "showarrow": False,
                    "font": {"size": 13},
                    "xanchor": "left",
                },
            ],
        },
        "config": {"displaylogo": False, "responsive": True},
    }


def _intraday_profile_data_summary(
    prepared: _IntradayProfileInputs,
    figure: Mapping[str, Any],
) -> str:
    traces = figure.get("data", ())
    trace_count = len(traces) if isinstance(traces, Sequence) else 0
    return (
        f"{len(prepared.bucket_labels):,} intraday buckets; "
        f"{prepared.reference_date_count:,} reference dates reduced to "
        "null-filtered percentile box statistics; current period rendered as "
        f"per-bucket means; {len(prepared.group_labels):,} capped group "
        f"deltas; {trace_count:,} Plotly traces embedded. Raw observation rows "
        "and full value tables are omitted from the HTML."
    )


def _mean_observation_values_by_bucket(
    observations: Sequence[MetricObservation],
) -> dict[str, float]:
    values_by_bucket: dict[str, list[float]] = {}
    for observation in observations:
        value = _finite_observation_value(observation)
        if value is None:
            continue
        bucket = _format_bucket_text(observation.time_bucket) or "Full day"
        values_by_bucket.setdefault(bucket, []).append(value)
    return {
        bucket: sum(values) / len(values)
        for bucket, values in values_by_bucket.items()
        if values
    }


def _mean_observation_values_by_date_bucket(
    observations: Sequence[MetricObservation],
) -> dict[object, dict[str, float]]:
    values: dict[object, dict[str, list[float]]] = {}
    for observation in observations:
        value = _finite_observation_value(observation)
        if value is None:
            continue
        bucket = _format_bucket_text(observation.time_bucket) or "Full day"
        values.setdefault(observation.date, {}).setdefault(bucket, []).append(value)
    return {
        observation_date: {
            bucket: sum(bucket_values) / len(bucket_values)
            for bucket, bucket_values in bucket_values_by_bucket.items()
            if bucket_values
        }
        for observation_date, bucket_values_by_bucket in values.items()
    }


def _reference_profile_values_by_bucket(
    values_by_date_bucket: Mapping[object, Mapping[str, float]],
    bucket_labels: Sequence[str],
) -> dict[str, tuple[float, ...]]:
    values_by_bucket: dict[str, list[float]] = {bucket: [] for bucket in bucket_labels}
    for bucket_values in values_by_date_bucket.values():
        for bucket in bucket_labels:
            value = bucket_values.get(bucket)
            if value is not None:
                values_by_bucket[bucket].append(value)
    return {
        bucket: tuple(values)
        for bucket, values in values_by_bucket.items()
        if values
    }


def _profile_group_delta_rows(
    target_observations: Sequence[MetricObservation],
    reference_observations: Sequence[MetricObservation],
    *,
    group_by: Sequence[str],
    max_groups: int | None,
) -> tuple[tuple[str, float, float], ...]:
    current_by_group = _mean_observation_values_by_group(target_observations, group_by)
    reference_by_group = _mean_reference_values_by_group(
        reference_observations,
        group_by,
    )
    rows = [
        (group, current_value, reference_by_group[group])
        for group, current_value in current_by_group.items()
        if group in reference_by_group
    ]
    rows.sort(
        key=lambda row: (
            -abs(row[1] - row[2]),
            row[0],
        )
    )
    if max_groups is None:
        return tuple(rows)
    return tuple(rows[:max_groups])


def _mean_observation_values_by_group(
    observations: Sequence[MetricObservation],
    group_by: Sequence[str],
) -> dict[str, float]:
    values_by_group: dict[str, list[float]] = {}
    for observation in observations:
        value = _finite_observation_value(observation)
        if value is None:
            continue
        group = _profile_group_label(observation.group, group_by)
        values_by_group.setdefault(group, []).append(value)
    return {
        group: sum(values) / len(values)
        for group, values in values_by_group.items()
        if values
    }


def _mean_reference_values_by_group(
    observations: Sequence[MetricObservation],
    group_by: Sequence[str],
) -> dict[str, float]:
    values_by_date_group: dict[tuple[object, str], list[float]] = {}
    for observation in observations:
        value = _finite_observation_value(observation)
        if value is None:
            continue
        group = _profile_group_label(observation.group, group_by)
        values_by_date_group.setdefault((observation.date, group), []).append(value)

    daily_group_means: dict[str, list[float]] = {}
    for (_, group), values in values_by_date_group.items():
        if not values:
            continue
        daily_group_means.setdefault(group, []).append(sum(values) / len(values))
    return {
        group: sum(values) / len(values)
        for group, values in daily_group_means.items()
        if values
    }


def _profile_group_label(group: Mapping[str, str], group_by: Sequence[str]) -> str:
    selected = {
        key: group[key]
        for key in group_by
        if key in group and str(group[key]).strip()
    }
    if selected:
        return format_group_label(selected)
    return "Report aggregate"


def _finite_observation_value(observation: MetricObservation) -> float | None:
    if observation.value is None:
        return None
    value = float(observation.value)
    if not isfinite(value):
        return None
    return value


def _sum_observation_values_by_date_bucket(
    observations: Sequence[MetricObservation],
) -> dict[object, dict[str, float]]:
    values: dict[object, dict[str, float]] = {}
    for observation in observations:
        value = _numeric_observation_value(observation)
        if value is None:
            continue
        bucket = _format_bucket_text(observation.time_bucket) or "Full day"
        date_values = values.setdefault(observation.date, {})
        date_values[bucket] = date_values.get(bucket, 0.0) + value
    return values


def _mean_values_by_bucket(
    values_by_date_bucket: Mapping[object, Mapping[str, float]],
) -> dict[str, float]:
    values_by_bucket: dict[str, list[float]] = {}
    for values_by_bucket_for_date in values_by_date_bucket.values():
        for bucket, value in values_by_bucket_for_date.items():
            values_by_bucket.setdefault(bucket, []).append(value)
    return {
        bucket: sum(values) / len(values)
        for bucket, values in values_by_bucket.items()
        if values
    }


def _mean_daily_session_share_percentages(
    observations: Sequence[MetricObservation],
) -> dict[str, float]:
    values_by_date_session: dict[object, dict[str, float]] = {}
    for observation in observations:
        value = _numeric_observation_value(observation)
        if value is None:
            continue
        session = _activity_session_label(observation.time_bucket)
        date_values = values_by_date_session.setdefault(observation.date, {})
        date_values[session] = date_values.get(session, 0.0) + value

    daily_shares = [
        _session_share_percentages(values_by_session)
        for values_by_session in values_by_date_session.values()
    ]
    if not daily_shares:
        return {session: 0.0 for session in _ACTIVITY_SESSION_ORDER}

    return {
        session: sum(shares[session] for shares in daily_shares) / len(daily_shares)
        for session in _ACTIVITY_SESSION_ORDER
    }


def _numeric_observation_value(observation: MetricObservation) -> float | None:
    if observation.value is None:
        return None
    value = float(observation.value)
    if not isfinite(value) or value < 0:
        return None
    return value


def _ordered_activity_buckets(labels: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(dict.fromkeys(labels), key=_activity_bucket_sort_key))


def _cumulative_bucket_percentages(
    values_by_bucket: Mapping[str, float],
    bucket_labels: Sequence[str],
) -> tuple[float, ...]:
    total = sum(values_by_bucket.values())
    if total <= 0:
        return tuple(0.0 for _ in bucket_labels)
    running = 0.0
    result: list[float] = []
    for bucket in bucket_labels:
        running += values_by_bucket.get(bucket, 0.0)
        result.append(running / total * 100)
    return tuple(result)


def _reference_cumulative_percentages_by_bucket(
    values_by_date_bucket: Mapping[object, Mapping[str, float]],
    bucket_labels: Sequence[str],
) -> dict[str, tuple[float, ...]]:
    bucket_values: dict[str, list[float]] = {bucket: [] for bucket in bucket_labels}
    for values_by_bucket in values_by_date_bucket.values():
        cumulative = _cumulative_bucket_percentages(values_by_bucket, bucket_labels)
        for bucket, value in zip(bucket_labels, cumulative, strict=True):
            bucket_values[bucket].append(value)
    return {
        bucket: tuple(values)
        for bucket, values in bucket_values.items()
        if values
    }


def _session_share_percentages(
    values_by_session: Mapping[str, float],
) -> dict[str, float]:
    total = sum(values_by_session.values())
    if total <= 0:
        return {session: 0.0 for session in _ACTIVITY_SESSION_ORDER}
    return {
        session: values_by_session.get(session, 0.0) / total * 100
        for session in _ACTIVITY_SESSION_ORDER
    }


_ACTIVITY_SESSION_ORDER = (
    "AM opening auction",
    "AM continuous session",
    "AM closing auction",
    "PM opening auction",
    "PM continuous session",
    "PM closing auction",
    "Other",
)


def _activity_session_label(bucket: object | None) -> str:
    raw = "" if bucket is None else str(bucket).strip()
    upper = raw.upper()
    if upper == "AMO":
        return "AM opening auction"
    if upper == "AMC":
        return "AM closing auction"
    if upper == "PMO":
        return "PM opening auction"
    if upper == "PMC":
        return "PM closing auction"

    label = _format_bucket_text(bucket) or raw
    label_lower = label.casefold()
    if "opening auction" in label_lower:
        return "AM opening auction" if "am" in label_lower else "PM opening auction"
    if "closing auction" in label_lower:
        return "AM closing auction" if "am" in label_lower else "PM closing auction"

    hour_minute = _leading_hour_minute(raw) or _leading_hour_minute(label)
    if hour_minute is None:
        return "Other"
    hour, minute = hour_minute
    if (hour, minute) < (12, 0):
        return "AM continuous session"
    return "PM continuous session"


def _leading_hour_minute(text: str) -> tuple[int, int] | None:
    match = re.match(r"^(?P<hour>[0-2]?[0-9]):(?P<minute>[0-5][0-9])", text)
    if match is None:
        return None
    return (int(match.group("hour")), int(match.group("minute")))


def _activity_bucket_sort_key(label: str) -> tuple[int, str]:
    canonical = label.casefold()
    if "am opening auction" in canonical:
        return (0, label)
    if "am closing auction" in canonical:
        return (200, label)
    if "pm opening auction" in canonical:
        return (300, label)
    if "pm closing auction" in canonical:
        return (500, label)
    hour_minute = _leading_hour_minute(label)
    if hour_minute is not None:
        hour, minute = hour_minute
        return (100 + hour * 60 + minute, label)
    return (900, label)


def _percentile(values: Sequence[float | None], percentile: float) -> float:
    ordered = sorted(_clean_finite_values(values))
    if not ordered:
        raise ValueError("values must contain at least one finite number")
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile / 100
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = position - lower_index
    return ordered[lower_index] + (
        ordered[upper_index] - ordered[lower_index]
    ) * fraction


def _clean_finite_values(values: Sequence[float | None]) -> tuple[float, ...]:
    cleaned: list[float] = []
    for value in values:
        if value is None:
            continue
        numeric = float(value)
        if isfinite(numeric):
            cleaned.append(numeric)
    return tuple(cleaned)


def build_heatmap(
    title: str,
    series: MetricTimeSeries,
    metric_definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None = None,
    max_cells: int | None = None,
    x_axis_label: str = "Intraday bucket",
    y_axis_label: str = "Group",
    help_text: str | None = None,
) -> Heatmap:
    """Build a deterministic heatmap visual.

    The builder formats already-normalized ``MetricTimeSeries`` observations
    into cells for report rendering. It preserves report date, intraday/auction
    bucket, group, metadata context, and numeric values; it does not calculate
    metrics or use backend-specific visualisation dependencies.
    """

    heatmap_title = title.strip()
    if not heatmap_title:
        raise ValueError("title must not be empty")
    if series.metric_name != metric_definition.name:
        raise ValueError(
            "metric_definition.name must match series.metric_name: "
            f"{metric_definition.name} != {series.metric_name}"
        )
    if max_cells is not None and max_cells < 0:
        raise ValueError("max_cells must be non-negative")
    if not x_axis_label.strip():
        raise ValueError("x_axis_label must not be empty")
    if not y_axis_label.strip():
        raise ValueError("y_axis_label must not be empty")
    if help_text is not None and not help_text.strip():
        raise ValueError("help_text must not be empty when supplied")

    observations = (
        series.observations if max_cells is None else series.observations[:max_cells]
    )
    return Heatmap(
        title=heatmap_title,
        metric=metric_definition,
        cells=[
            _heatmap_cell_from_observation(
                observation,
                metric_definition,
                group_by=group_by,
            )
            for observation in observations
        ],
        x_axis_label=x_axis_label.strip(),
        y_axis_label=y_axis_label.strip(),
        help_text=None if help_text is None else help_text.strip(),
    )


def _comparison_commentary_facts(
    page_title: str,
    comparisons: Sequence[MetricComparison],
    definitions: Mapping[str, MetricDefinition],
    options: ComparisonSectionOptions,
) -> tuple[CommentaryFact, ...]:
    metric_facts = commentary_facts_from_comparisons(
        comparisons,
        metric_definitions=definitions,
    )
    if not options.include_section_summary:
        return metric_facts
    return (
        section_summary_fact_from_comparisons(
            page_title,
            comparisons,
            scope_label=options.section_summary_scope_label,
        ),
        *metric_facts,
    )


def _metric_card_from_comparison(
    comparison: MetricComparison,
    definition: MetricDefinition,
) -> MetricCard:
    unit = definition.unit
    reference_text = None
    if comparison.reference_value is not None:
        reference_text = _format_metric_value(comparison.reference_value, unit)
        change_text = _format_change(comparison, unit)
        if change_text is not None:
            reference_text = f"{reference_text} ({change_text})"

    return MetricCard(
        metric=definition,
        value_text=_format_metric_value(comparison.value, unit),
        reference_text=reference_text,
        status=comparison.status,
    )


def _metric_table_row_from_comparison(
    comparison: MetricComparison,
    definition: MetricDefinition,
) -> MetricTableRow:
    unit = definition.unit
    reference_text = (
        None
        if comparison.reference_value is None
        else _format_metric_value(comparison.reference_value, unit)
    )
    return MetricTableRow(
        metric=definition,
        value_text=_format_metric_value(comparison.value, unit),
        reference_text=reference_text,
        change_text=_format_change(comparison, unit),
        status=comparison.status,
        group_text=_format_comparison_scope(comparison),
    )


def _intraday_chart_point_from_observation(
    observation: MetricObservation,
    definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None,
) -> TimeSeriesChartPoint:
    date_text = observation.date.isoformat()
    bucket_text = _format_bucket_text(observation.time_bucket)
    return TimeSeriesChartPoint(
        x_text=_format_intraday_chart_x_text(date_text, bucket_text),
        date_text=date_text,
        time_bucket_text=bucket_text,
        series_text=_format_series_text(observation.group, group_by=group_by),
        value_text=_format_metric_value(observation.value, definition.unit),
        metadata_text=_format_metadata_text(observation.metadata),
        value=observation.value,
    )


def _reference_target_chart_point_from_observation(
    observation: MetricObservation,
    definition: MetricDefinition,
    *,
    period_label: str,
    group_by: Sequence[str] | None,
) -> TimeSeriesChartPoint:
    date_text = observation.date.isoformat()
    bucket_text = _format_bucket_text(observation.time_bucket)
    metadata = {"period": period_label, **observation.metadata}
    return TimeSeriesChartPoint(
        x_text=date_text,
        date_text=date_text,
        time_bucket_text=bucket_text,
        series_text=_format_reference_target_series_text(
            observation,
            bucket_text=bucket_text,
            group_by=group_by,
        ),
        value_text=_format_metric_value(observation.value, definition.unit),
        metadata_text=_format_metadata_text(metadata),
        value=observation.value,
    )


def _time_series_chart_point_from_observation(
    observation: MetricObservation,
    definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None,
) -> TimeSeriesChartPoint:
    date_text = observation.date.isoformat()
    bucket_text = _format_bucket_text(observation.time_bucket)
    return TimeSeriesChartPoint(
        x_text=_format_chart_x_text(date_text, bucket_text),
        date_text=date_text,
        time_bucket_text=bucket_text,
        series_text=_format_series_text(observation.group, group_by=group_by),
        value_text=_format_metric_value(observation.value, definition.unit),
        metadata_text=_format_metadata_text(observation.metadata),
        value=observation.value,
    )


def _heatmap_cell_from_observation(
    observation: MetricObservation,
    definition: MetricDefinition,
    *,
    group_by: Sequence[str] | None,
) -> HeatmapCell:
    date_text = observation.date.isoformat()
    bucket_text = _format_bucket_text(observation.time_bucket)
    group_text = _format_series_text(observation.group, group_by=group_by)
    return HeatmapCell(
        x_text=_format_heatmap_x_text(date_text, bucket_text),
        y_text=group_text or "all",
        date_text=date_text,
        time_bucket_text=bucket_text,
        group_text=group_text,
        value_text=_format_metric_value(observation.value, definition.unit),
        metadata_text=_format_metadata_text(observation.metadata),
        value=observation.value,
    )


def _format_heatmap_x_text(date_text: str, bucket_text: str | None) -> str:
    if bucket_text:
        return bucket_text
    return date_text


def _format_intraday_chart_x_text(date_text: str, bucket_text: str | None) -> str:
    if bucket_text:
        return bucket_text
    return date_text


def _format_reference_target_series_text(
    observation: MetricObservation,
    *,
    bucket_text: str | None,
    group_by: Sequence[str] | None,
) -> str | None:
    parts: list[str] = []
    group_text = _format_series_text(observation.group, group_by=group_by)
    if group_text:
        parts.append(group_text)
    if bucket_text:
        parts.append(f"Intraday bucket: {bucket_text}")
    return ", ".join(parts) if parts else None


def _format_chart_x_text(date_text: str, bucket_text: str | None) -> str:
    if bucket_text:
        return f"{date_text} {bucket_text}"
    return date_text


def _format_bucket_text(bucket: object | None) -> str | None:
    return format_intraday_bucket_label(bucket)


def _format_series_text(
    group: Mapping[str, str],
    *,
    group_by: Sequence[str] | None,
) -> str | None:
    return format_group_label(
        group,
        group_by=None if group_by is None else tuple(group_by),
    )


def _format_metadata_text(metadata: Mapping[str, object]) -> str | None:
    return format_group_label(metadata)


def _metric_definition_map(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
) -> dict[str, MetricDefinition]:
    if isinstance(metric_definitions, Mapping):
        return dict(metric_definitions)
    return {definition.name: definition for definition in metric_definitions}


def _require_metric_definitions(
    comparisons: Sequence[MetricComparison],
    definitions: Mapping[str, MetricDefinition],
) -> None:
    missing = sorted(
        {comparison.metric_name for comparison in comparisons}
        - set(definitions.keys())
    )
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(
            "metric definitions are required for report components: "
            f"{missing_text}"
        )


def _comparison_sort_key(
    comparison: MetricComparison,
    definitions: Mapping[str, MetricDefinition],
) -> tuple[int, float, str, str, str, str]:
    priority = {"alert": 0, "watch": 1, "comparison_only": 2, "normal": 3}
    z_magnitude = -abs(comparison.z_score) if comparison.z_score is not None else 0.0
    definition = definitions.get(comparison.metric_name)
    label = comparison.metric_name if definition is None else definition.label
    date_key = "" if comparison.date is None else comparison.date.isoformat()
    bucket_key = "" if comparison.time_bucket is None else str(comparison.time_bucket)
    return (
        priority.get(comparison.status, 99),
        z_magnitude,
        label,
        date_key,
        bucket_key,
        repr(sorted(comparison.group.items())),
    )


def _format_comparison_scope(comparison: MetricComparison) -> str | None:
    return format_comparison_scope_label(
        observation_date=comparison.date,
        time_bucket=comparison.time_bucket,
        group=comparison.group,
    )


def _format_metric_value(value: float | int | None, unit: str) -> str:
    if value is None:
        return "not available"

    numeric = float(value)
    if not isfinite(numeric):
        return "not available"

    if unit == "ratio":
        return f"{numeric:.4f}"
    if unit == "count":
        return f"{numeric:,.0f}"
    if unit == "JPY":
        return f"{numeric:,.0f} JPY"
    if unit:
        return f"{numeric:,.4f} {unit}"
    return f"{numeric:,.4f}"


def _format_change(comparison: MetricComparison, unit: str) -> str | None:
    parts: list[str] = []
    if comparison.change_abs is not None:
        formatted_change = _format_signed_metric_value(comparison.change_abs, unit)
        parts.append(f"change {formatted_change}")
    if comparison.change_pct is not None:
        parts.append(f"{comparison.change_pct:+.1%}")
    return " ".join(parts) if parts else None


def _format_signed_metric_value(value: float, unit: str) -> str:
    if not isfinite(float(value)):
        return "not available"
    if unit == "ratio":
        return f"{value:+.4f}"
    if unit == "count":
        return f"{value:+,.0f}"
    if unit == "JPY":
        return f"{value:+,.0f} JPY"
    if unit:
        return f"{value:+,.4f} {unit}"
    return f"{value:+,.4f}"
