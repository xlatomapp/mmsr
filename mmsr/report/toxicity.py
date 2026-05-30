"""Production report builders for cross-venue toxicity/reversion visuals."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, time
from math import isfinite
from typing import Literal

from mmsr.analysis.commentary import TemplateCommentaryEngine
from mmsr.config.models import ToxicityConfidenceConfig
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison, MetricTimeSeries
from mmsr.presentation.labels import (
    format_comparison_scope_label,
    format_group_label,
    format_intraday_bucket_label,
)
from mmsr.report.components import (
    CommentaryBlock,
    MetricTable,
    PlotlyChart,
    ReportPage,
)
from mmsr.report.sections import build_comparison_metric_table
from mmsr.visuals.toxicity import (
    ReversionCurvePoint,
    reversion_commentary_facts_from_curve_points,
    reversion_curve_points_from_timeseries_collection,
)

REVERSION_METRIC_PREFIX = "primary_quote_reversion_"
REVERSION_METRIC_SUFFIX = "_bps"
DEFAULT_REVERSION_VENUE_ORDER: tuple[str, ...] = ("TSE", "SBIJ", "ODX")
DEFAULT_REVERSION_HORIZON_ORDER: tuple[str, ...] = (
    "10ms",
    "100ms",
    "500ms",
    "1s",
    "5s",
    "10s",
)
ToxicityContextRanking = Literal[
    "max_positive_reversion",
    "max_absolute_reversion",
    "lowest_confidence",
    "context_sort_order",
    "chronological",
]
TOXICITY_CONTEXT_RANKINGS: tuple[ToxicityContextRanking, ...] = (
    "max_positive_reversion",
    "max_absolute_reversion",
    "lowest_confidence",
    "context_sort_order",
    "chronological",
)
DEFAULT_TOXICITY_CONTEXT_RANKING: ToxicityContextRanking = "max_positive_reversion"


@dataclass(frozen=True)
class ToxicityReversionPageOptions:
    """Presentation options for the production cross-venue toxicity page.

    The page formats normalized kdb-backed reversion metric output. It assumes
    the upstream q templates already produced one aggregate value per
    ``date × time_bucket × group × venue × horizon`` and does not calculate or
    query additional metrics in Python.
    """

    title: str = "Cross-Venue Toxicity"
    help_text: str = (
        "Primary-quote reversion by venue and horizon. The x-axis is the "
        "configured reversion horizon, the y-axis is reversion in bps, and each "
        "line is one execution venue. Positive values indicate movement in "
        "the aggressive-trade direction under the configured future-mid denominator."
    )
    max_charts: int | None = 6
    max_points_per_chart: int | None = None
    context_ranking: ToxicityContextRanking = DEFAULT_TOXICITY_CONTEXT_RANKING
    venue_order: tuple[str, ...] = DEFAULT_REVERSION_VENUE_ORDER
    horizon_order: tuple[str, ...] = DEFAULT_REVERSION_HORIZON_ORDER
    confidence: ToxicityConfidenceConfig | None = field(default_factory=ToxicityConfidenceConfig)
    comparison_table_title: str = "Reversion current versus reference"
    comparison_table_help_text: str = (
        "Precomputed normalized comparison rows for the reversion metric family. "
        "Rows preserve current value, comparable reference value, absolute and "
        "percentage change, and status. Positive current values and positive "
        "changes mean more aggressive-direction primary-quote reversion under "
        "the future-mid denominator convention."
    )
    max_comparison_rows: int | None = 0
    max_comparison_diagnostics: int | None = 12
    max_comments: int = 5
    max_commentary_headline_points: int = 3
    max_low_confidence_warnings: int = 3
    watch_threshold_bps: float = 0.5
    alert_threshold_bps: float = 2.0

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")
        _require_optional_non_negative(self.max_charts, "max_charts")
        _require_optional_non_negative(
            self.max_points_per_chart,
            "max_points_per_chart",
        )
        _require_context_ranking(self.context_ranking)
        _require_non_empty_sequence(self.venue_order, "venue_order")
        _require_non_empty_sequence(self.horizon_order, "horizon_order")
        _require_non_empty(self.comparison_table_title, "comparison_table_title")
        _require_non_empty(
            self.comparison_table_help_text,
            "comparison_table_help_text",
        )
        _require_optional_non_negative(
            self.max_comparison_rows,
            "max_comparison_rows",
        )
        _require_optional_non_negative(
            self.max_comparison_diagnostics,
            "max_comparison_diagnostics",
        )
        _require_non_negative(self.max_comments, "max_comments")
        _require_non_negative(
            self.max_commentary_headline_points,
            "max_commentary_headline_points",
        )
        _require_non_negative(
            self.max_low_confidence_warnings,
            "max_low_confidence_warnings",
        )
        if self.watch_threshold_bps < 0:
            raise ValueError("watch_threshold_bps must be non-negative")
        if self.alert_threshold_bps < self.watch_threshold_bps:
            raise ValueError("alert_threshold_bps must be >= watch_threshold_bps")


def build_toxicity_reversion_page(
    current_series: Sequence[MetricTimeSeries],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    comparisons: Sequence[MetricComparison] = (),
    options: ToxicityReversionPageOptions | None = None,
) -> ReportPage | None:
    """Build the production cross-venue toxicity/reversion report page.

    The builder is presentation-only. It consumes normalized reversion
    ``MetricTimeSeries`` rows that production callers should source from
    kdb-backed metric execution, preserves venue/horizon grouping, and renders
    compact Plotly horizon curves through the standard report component model.
    When supplied, existing normalized ``MetricComparison`` rows for the same
    metric family are rendered as capped Plotly diagnostics and, only when
    explicitly requested through ``max_comparison_rows``, a tiny comparison
    table without recalculating comparisons in Python.
    """

    resolved_options = options or ToxicityReversionPageOptions()
    definitions = _metric_definition_map(metric_definitions)
    reversion_series = tuple(series for series in current_series if _is_reversion_metric(series.metric_name))
    if not reversion_series:
        return None

    _require_metric_definitions(reversion_series, definitions)
    points = reversion_curve_points_from_timeseries_collection(
        reversion_series,
        venue_order=resolved_options.venue_order,
        horizon_order=resolved_options.horizon_order,
        confidence=resolved_options.confidence,
    )
    if not points:
        return None

    curve_metric = _curve_metric_definition(reversion_series, definitions)
    charts = [
        _plotly_chart_from_context_points(
            context_points,
            curve_metric,
            options=resolved_options,
        )
        for context_points in _selected_context_points(
            points,
            max_contexts=resolved_options.max_charts,
            context_ranking=resolved_options.context_ranking,
        )
    ]

    facts = reversion_commentary_facts_from_curve_points(
        points,
        max_headline_points=resolved_options.max_commentary_headline_points,
        max_low_confidence_warnings=resolved_options.max_low_confidence_warnings,
        watch_threshold_bps=resolved_options.watch_threshold_bps,
        alert_threshold_bps=resolved_options.alert_threshold_bps,
    )
    comments = TemplateCommentaryEngine().generate(
        list(facts),
        max_comments=resolved_options.max_comments,
    )
    comparison_table = _build_reversion_comparison_table(
        comparisons,
        definitions,
        options=resolved_options,
    )
    comparison_diagnostic_chart = _build_reversion_comparison_diagnostic_chart(
        comparisons,
        curve_metric,
        options=resolved_options,
    )

    return ReportPage(
        title=resolved_options.title.strip(),
        metric_tables=[] if comparison_table is None else [comparison_table],
        plotly_charts=[
            *charts,
            *([] if comparison_diagnostic_chart is None else [comparison_diagnostic_chart]),
        ],
        commentary_blocks=([CommentaryBlock(title="Toxicity commentary", comments=comments)] if comments else []),
    )


def _build_reversion_comparison_table(
    comparisons: Sequence[MetricComparison],
    definitions: Mapping[str, MetricDefinition],
    *,
    options: ToxicityReversionPageOptions,
) -> MetricTable | None:
    reversion_comparisons = tuple(
        comparison for comparison in comparisons if _is_reversion_metric(comparison.metric_name)
    )
    if not reversion_comparisons or options.max_comparison_rows == 0:
        return None
    return build_comparison_metric_table(
        options.comparison_table_title,
        reversion_comparisons,
        definitions,
        max_rows=options.max_comparison_rows,
        help_text=options.comparison_table_help_text,
    )


def _selected_context_points(
    points: Sequence[ReversionCurvePoint],
    *,
    max_contexts: int | None,
    context_ranking: ToxicityContextRanking,
) -> tuple[tuple[ReversionCurvePoint, ...], ...]:
    grouped: dict[_ReversionContextKey, list[ReversionCurvePoint]] = defaultdict(list)
    for point in points:
        grouped[_context_key(point)].append(point)

    context_groups = tuple((key, tuple(grouped[key])) for key in sorted(grouped, key=_context_sort_key))
    ordered_groups = tuple(
        context_points
        for _, context_points in sorted(
            context_groups,
            key=lambda item: _context_ranking_sort_key(
                item[1],
                item[0],
                context_ranking,
            ),
        )
    )
    if max_contexts is None:
        return ordered_groups
    return ordered_groups[:max_contexts]


@dataclass(frozen=True)
class _ReversionContextKey:
    observation_date: date | None
    time_bucket: time | str | None
    group: tuple[tuple[str, str], ...]


def _context_key(point: ReversionCurvePoint) -> _ReversionContextKey:
    return _ReversionContextKey(
        observation_date=point.date,
        time_bucket=point.time_bucket,
        group=tuple(sorted(point.group.items())),
    )


def _context_sort_key(key: _ReversionContextKey) -> tuple[int, int, str, str]:
    return (
        0 if key.observation_date is None else key.observation_date.toordinal(),
        _time_bucket_rank(key.time_bucket),
        "" if key.time_bucket is None else str(key.time_bucket),
        repr(key.group),
    )


def _context_ranking_sort_key(
    points: Sequence[ReversionCurvePoint],
    key: _ReversionContextKey,
    context_ranking: ToxicityContextRanking,
) -> tuple[float | int | str, ...]:
    chronological_key = _context_sort_key(key)
    if context_ranking == "chronological":
        return chronological_key
    if context_ranking == "max_positive_reversion":
        return (
            -_context_max_positive_reversion(points),
            -_context_max_absolute_reversion(points),
            *chronological_key,
        )
    if context_ranking == "max_absolute_reversion":
        return (
            -_context_max_absolute_reversion(points),
            -_context_max_positive_reversion(points),
            *chronological_key,
        )
    if context_ranking == "lowest_confidence":
        return (
            -_context_low_confidence_count(points),
            -_context_low_confidence_ratio(points),
            -_context_max_positive_reversion(points),
            -_context_max_absolute_reversion(points),
            *chronological_key,
        )
    if context_ranking == "context_sort_order":
        return (
            *_context_sort_order_rank(points),
            -_context_max_positive_reversion(points),
            -_context_max_absolute_reversion(points),
            *chronological_key,
        )
    raise ValueError("context_ranking must be one of: " + ", ".join(TOXICITY_CONTEXT_RANKINGS))


def _context_max_positive_reversion(points: Sequence[ReversionCurvePoint]) -> float:
    return max((max(point.reversion_bps, 0.0) for point in points), default=0.0)


def _context_max_absolute_reversion(points: Sequence[ReversionCurvePoint]) -> float:
    return max((abs(point.reversion_bps) for point in points), default=0.0)


def _context_low_confidence_count(points: Sequence[ReversionCurvePoint]) -> int:
    return sum(1 for point in points if point.low_confidence)


def _context_low_confidence_ratio(points: Sequence[ReversionCurvePoint]) -> float:
    if not points:
        return 0.0
    return _context_low_confidence_count(points) / len(points)


def _context_sort_order_rank(points: Sequence[ReversionCurvePoint]) -> tuple[int, int]:
    orders = [point.context_sort_order for point in points if point.context_sort_order is not None]
    if not orders:
        return (1, 0)
    return (0, min(orders))


def _time_bucket_rank(value: time | str | None) -> int:
    if value is None:
        return 0
    if isinstance(value, time):
        return value.hour * 3_600_000_000 + value.minute * 60_000_000 + value.second * 1_000_000 + value.microsecond
    return 0


def _plotly_chart_from_context_points(
    points: Sequence[ReversionCurvePoint],
    metric_definition: MetricDefinition,
    *,
    options: ToxicityReversionPageOptions,
) -> PlotlyChart:
    context = _context_label(points[0])
    selected_points = (
        tuple(points) if options.max_points_per_chart is None else tuple(points)[: options.max_points_per_chart]
    )
    return PlotlyChart(
        title=f"{context} reversion horizon curve",
        metric=metric_definition,
        figure=_reversion_curve_figure(selected_points, metric_definition),
        x_axis_label="Horizon",
        y_axis_label="Reversion (bps)",
        help_text=options.help_text.strip(),
        data_summary=_reversion_curve_data_summary(selected_points),
    )


def _reversion_curve_figure(
    points: Sequence[ReversionCurvePoint],
    metric_definition: MetricDefinition,
) -> dict[str, object]:
    return {
        "data": _reversion_curve_traces(points),
        "layout": {
            "template": "plotly_white",
            "autosize": True,
            "height": 380,
            "margin": {"l": 58, "r": 24, "t": 24, "b": 72},
            "xaxis": {"title": "Horizon", "type": "category"},
            "yaxis": {"title": metric_definition.unit or "bps", "zeroline": True},
            "legend": {"orientation": "h", "y": -0.28},
            "hovermode": "x unified",
        },
        "config": {"displaylogo": False, "responsive": True},
    }


def _reversion_curve_traces(
    points: Sequence[ReversionCurvePoint],
) -> list[dict[str, object]]:
    traces: list[dict[str, object]] = []
    for venue in _ordered_unique(point.venue for point in points):
        venue_points = [point for point in points if point.venue == venue]
        traces.append(
            {
                "type": "scatter",
                "mode": "lines+markers",
                "name": venue,
                "x": [point.horizon for point in venue_points],
                "y": [point.reversion_bps for point in venue_points],
                "text": [_point_hover_text(point) for point in venue_points],
                "marker": {"symbol": ["circle-open" if point.low_confidence else "circle" for point in venue_points]},
                "hovertemplate": ("%{text}<br><b>%{y:+.4f} bps</b><extra>%{fullData.name}</extra>"),
            }
        )
    return traces


def _point_hover_text(point: ReversionCurvePoint) -> str:
    parts = [
        f"<b>{point.venue} {point.horizon}</b>",
        f"Reversion: {point.reversion_bps:+.4f} bps",
    ]
    if point.date is not None:
        parts.append(f"Date: {point.date.isoformat()}")
    bucket_label = format_intraday_bucket_label(point.time_bucket)
    if bucket_label is not None:
        parts.append(f"Bucket: {bucket_label}")
    metadata = _point_metadata_text(point)
    if metadata is not None:
        parts.append(metadata)
    return "<br>".join(parts)


def _reversion_curve_data_summary(points: Sequence[ReversionCurvePoint]) -> str:
    low_confidence_count = sum(1 for point in points if point.low_confidence)
    parts = [
        f"{len(points):,} aggregated venue/horizon points",
        f"{len(_ordered_unique(point.venue for point in points)):,} venues",
        f"{len(_ordered_unique(point.horizon for point in points)):,} horizons",
    ]
    if low_confidence_count:
        parts.append(f"{low_confidence_count:,} low-confidence markers")
    return "; ".join(parts) + ". Compact Plotly arrays only; raw trade or quote rows are not embedded."


def _build_reversion_comparison_diagnostic_chart(
    comparisons: Sequence[MetricComparison],
    metric_definition: MetricDefinition,
    *,
    options: ToxicityReversionPageOptions,
) -> PlotlyChart | None:
    rows = _selected_reversion_comparisons(
        comparisons,
        max_rows=options.max_comparison_diagnostics,
    )
    if not rows:
        return None

    return PlotlyChart(
        title="Reversion current-minus-reference diagnostics",
        metric=metric_definition,
        figure={
            "data": [
                {
                    "type": "bar",
                    "orientation": "h",
                    "name": "Current − reference",
                    "x": [_comparison_delta_bps(comparison) for comparison in rows],
                    "y": [_comparison_diagnostic_label(comparison) for comparison in rows],
                    "text": [_comparison_hover_text(comparison) for comparison in rows],
                    "hovertemplate": ("%{text}<br><b>%{x:+.4f} bps</b><extra>Current − reference</extra>"),
                }
            ],
            "layout": {
                "template": "plotly_white",
                "autosize": True,
                "height": max(320, 38 * len(rows) + 130),
                "margin": {"l": 190, "r": 24, "t": 24, "b": 54},
                "xaxis": {"title": "Current minus reference (bps)", "zeroline": True},
                "yaxis": {"title": "Venue / horizon context", "automargin": True},
                "showlegend": False,
            },
            "config": {"displaylogo": False, "responsive": True},
        },
        x_axis_label="Current minus reference (bps)",
        y_axis_label="Venue / horizon context",
        help_text=(
            "Capped diagnostic view of precomputed reversion comparisons. Bars "
            "show current minus comparable reference in bps; rows are ranked by "
            "status severity and absolute delta so the report remains visual and compact."
        ),
        data_summary=(
            f"{len(rows):,} capped reversion comparison diagnostics embedded from "
            "normalized comparison facts; full comparison rows are not rendered."
        ),
    )


def _selected_reversion_comparisons(
    comparisons: Sequence[MetricComparison],
    *,
    max_rows: int | None,
) -> tuple[MetricComparison, ...]:
    reversion_comparisons = tuple(
        comparison
        for comparison in comparisons
        if _is_reversion_metric(comparison.metric_name)
        and _finite_number(_comparison_delta_bps(comparison)) is not None
    )
    ordered = tuple(sorted(reversion_comparisons, key=_comparison_diagnostic_sort_key))
    if max_rows is None:
        return ordered
    return ordered[:max_rows]


def _comparison_diagnostic_sort_key(
    comparison: MetricComparison,
) -> tuple[int, float, str]:
    return (
        _status_severity_rank(comparison.status),
        -abs(_comparison_delta_bps(comparison)),
        _comparison_diagnostic_label(comparison),
    )


def _status_severity_rank(status: str) -> int:
    if status == "alert":
        return 0
    if status == "watch":
        return 1
    return 2


def _comparison_delta_bps(comparison: MetricComparison) -> float:
    if comparison.change_abs is not None:
        return float(comparison.change_abs)
    if comparison.reference_value is None:
        return 0.0
    return float(comparison.value) - float(comparison.reference_value)


def _comparison_diagnostic_label(comparison: MetricComparison) -> str:
    group_label = format_group_label(comparison.group)
    scope_label = format_comparison_scope_label(
        observation_date=comparison.date,
        time_bucket=comparison.time_bucket,
        group={},
    )
    parts = []
    if group_label is not None:
        parts.append(group_label)
    if scope_label is not None:
        parts.append(scope_label)
    return " | ".join(parts) if parts else comparison.metric_name


def _comparison_hover_text(comparison: MetricComparison) -> str:
    parts = [
        f"<b>{_comparison_diagnostic_label(comparison)}</b>",
        f"Current: {comparison.value:.4f} bps",
    ]
    if comparison.reference_value is not None:
        parts.append(f"Reference: {comparison.reference_value:.4f} bps")
    parts.append(f"Change: {_comparison_delta_bps(comparison):+.4f} bps")
    parts.append(f"Status: {comparison.status.replace('_', ' ')}")
    if comparison.percentile is not None:
        parts.append(f"Percentile: {comparison.percentile:.1%}")
    if comparison.z_score is not None:
        parts.append(f"z-score: {comparison.z_score:+.2f}")
    return "<br>".join(parts)


def _finite_number(value: object) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if isfinite(numeric) else None


def _ordered_unique(values: Iterable[object]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        ordered.append(text)
    return tuple(ordered)


def _context_label(point: ReversionCurvePoint) -> str:
    label = format_comparison_scope_label(
        observation_date=point.date,
        time_bucket=point.time_bucket,
        group=point.group,
    )
    return "Overall" if label is None else label


def _point_metadata_text(point: ReversionCurvePoint) -> str | None:
    parts: list[str] = []
    group_label = format_group_label(point.group)
    if group_label is not None:
        parts.append(group_label)
    if point.trade_count is not None:
        parts.append(f"Trade count: {point.trade_count:,}")
    if point.notional is not None:
        parts.append(f"Notional: {point.notional:,.0f}")
    if point.context_sort_order is not None:
        parts.append(f"Context sort order: {point.context_sort_order}")
    if point.low_confidence:
        if point.confidence_reasons:
            parts.append("Low confidence: " + "; ".join(point.confidence_reasons))
        else:
            parts.append("Low confidence")
    return " | ".join(parts) if parts else None


def _curve_metric_definition(
    series: Sequence[MetricTimeSeries],
    definitions: Mapping[str, MetricDefinition],
) -> MetricDefinition:
    first_metric_name = series[0].metric_name
    first_definition = definitions[first_metric_name]
    return replace(
        first_definition,
        name="primary_quote_reversion_curve_bps",
        label="Cross-Venue Reversion Curve",
        description=(
            "Primary-quote reversion across configured horizons for each "
            "execution venue, using kdb-computed aggregate reversion rows."
        ),
        formula=(
            "For each venue and horizon: "
            "side * 10000 * (primary_mid[t + horizon] - primary_mid[t-]) "
            "/ primary_mid[t + horizon], aggregated by the upstream kdb query."
        ),
        interpretation=(
            "Positive values indicate the primary quote moved in the aggressive "
            "trade direction after execution, consistent with adverse selection. "
            "Compare the line shape across horizons and venues."
        ),
        unit="bps",
        default_aggregation="kdb-provided aggregate by venue and horizon",
        caveats=(
            first_definition.caveats
            + [
                "This page assumes the production kdb query has already applied "
                "the configured event filters, quote-age controls, and grouping.",
                "Low-confidence markers are based on supplied aggregate sample "
                "metadata such as trade_count and notional.",
            ]
        ),
    )


def _metric_definition_map(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
) -> dict[str, MetricDefinition]:
    if isinstance(metric_definitions, Mapping):
        return dict(metric_definitions)
    return {definition.name: definition for definition in metric_definitions}


def _require_metric_definitions(
    series: Sequence[MetricTimeSeries],
    definitions: Mapping[str, MetricDefinition],
) -> None:
    missing = sorted({item.metric_name for item in series} - set(definitions.keys()))
    if missing:
        raise ValueError("metric definitions are required for toxicity reversion charts: " + ", ".join(missing))


def _is_reversion_metric(metric_name: str) -> bool:
    return metric_name.startswith(REVERSION_METRIC_PREFIX) and metric_name.endswith(REVERSION_METRIC_SUFFIX)


def _require_context_ranking(value: str) -> None:
    if value not in TOXICITY_CONTEXT_RANKINGS:
        raise ValueError("context_ranking must be one of: " + ", ".join(TOXICITY_CONTEXT_RANKINGS))


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_non_empty_sequence(values: Sequence[str], field_name: str) -> None:
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    for value in values:
        if not value.strip():
            raise ValueError(f"{field_name} must not contain empty values")


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


__all__ = [
    "DEFAULT_REVERSION_HORIZON_ORDER",
    "DEFAULT_REVERSION_VENUE_ORDER",
    "DEFAULT_TOXICITY_CONTEXT_RANKING",
    "TOXICITY_CONTEXT_RANKINGS",
    "ToxicityContextRanking",
    "ToxicityReversionPageOptions",
    "build_toxicity_reversion_page",
]
