"""Deterministic report section builders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

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
