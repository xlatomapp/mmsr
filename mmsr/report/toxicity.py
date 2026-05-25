"""Production report builders for cross-venue toxicity/reversion visuals."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, time
from typing import Literal

from mmsr.config.models import ToxicityConfidenceConfig
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricTimeSeries
from mmsr.presentation.labels import (
    format_comparison_scope_label,
    format_group_label,
    format_intraday_bucket_label,
)
from mmsr.report.components import CommentaryBlock, ReportPage, TimeSeriesChart, TimeSeriesChartPoint
from mmsr.visuals.toxicity import (
    ReversionCurvePoint,
    reversion_commentary_facts_from_curve_points,
    reversion_curve_points_from_timeseries_collection,
)
from mmsr.analysis.commentary import TemplateCommentaryEngine


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
        "line is one execution venue. Positive values indicate adverse movement "
        "in the aggressive-trade direction."
    )
    max_charts: int | None = 6
    max_points_per_chart: int | None = None
    context_ranking: ToxicityContextRanking = DEFAULT_TOXICITY_CONTEXT_RANKING
    venue_order: tuple[str, ...] = DEFAULT_REVERSION_VENUE_ORDER
    horizon_order: tuple[str, ...] = DEFAULT_REVERSION_HORIZON_ORDER
    confidence: ToxicityConfidenceConfig | None = field(
        default_factory=ToxicityConfidenceConfig
    )
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
        _require_optional_non_negative(self.max_points_per_chart, "max_points_per_chart")
        _require_context_ranking(self.context_ranking)
        _require_non_empty_sequence(self.venue_order, "venue_order")
        _require_non_empty_sequence(self.horizon_order, "horizon_order")
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
    options: ToxicityReversionPageOptions | None = None,
) -> ReportPage | None:
    """Build the production cross-venue toxicity/reversion report page.

    The builder is presentation-only. It consumes normalized reversion
    ``MetricTimeSeries`` rows that production callers should source from
    kdb-backed metric execution, preserves venue/horizon grouping, and renders
    deterministic SVG line charts through the standard report component model.
    """

    resolved_options = options or ToxicityReversionPageOptions()
    definitions = _metric_definition_map(metric_definitions)
    reversion_series = tuple(
        series for series in current_series if _is_reversion_metric(series.metric_name)
    )
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
        _chart_from_context_points(
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

    return ReportPage(
        title=resolved_options.title.strip(),
        time_series_charts=charts,
        commentary_blocks=(
            [CommentaryBlock(title="Toxicity commentary", comments=comments)]
            if comments
            else []
        ),
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

    context_groups = tuple(
        (key, tuple(grouped[key]))
        for key in sorted(grouped, key=_context_sort_key)
    )
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
    raise ValueError(
        "context_ranking must be one of: "
        + ", ".join(TOXICITY_CONTEXT_RANKINGS)
    )


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
    orders = [
        point.context_sort_order
        for point in points
        if point.context_sort_order is not None
    ]
    if not orders:
        return (1, 0)
    return (0, min(orders))


def _time_bucket_rank(value: time | str | None) -> int:
    if value is None:
        return 0
    if isinstance(value, time):
        return (
            value.hour * 3_600_000_000
            + value.minute * 60_000_000
            + value.second * 1_000_000
            + value.microsecond
        )
    return 0


def _chart_from_context_points(
    points: Sequence[ReversionCurvePoint],
    metric_definition: MetricDefinition,
    *,
    options: ToxicityReversionPageOptions,
) -> TimeSeriesChart:
    context = _context_label(points[0])
    selected_points = (
        tuple(points)
        if options.max_points_per_chart is None
        else tuple(points)[: options.max_points_per_chart]
    )
    return TimeSeriesChart(
        title=f"{context} reversion curve",
        metric=metric_definition,
        points=[
            TimeSeriesChartPoint(
                x_text=point.horizon,
                date_text=None if point.date is None else point.date.isoformat(),
                time_bucket_text=format_intraday_bucket_label(point.time_bucket),
                series_text=point.venue,
                value_text=f"{point.reversion_bps:+.4f} bps",
                metadata_text=_point_metadata_text(point),
                value=point.reversion_bps,
            )
            for point in selected_points
        ],
        x_axis_label="Horizon",
        y_axis_label="Reversion (bps)",
        help_text=options.help_text.strip(),
    )


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
            "/ primary_mid[t-], aggregated by the upstream kdb query."
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
    missing = sorted(
        {item.metric_name for item in series}
        - set(definitions.keys())
    )
    if missing:
        raise ValueError(
            "metric definitions are required for toxicity reversion charts: "
            + ", ".join(missing)
        )


def _is_reversion_metric(metric_name: str) -> bool:
    return (
        metric_name.startswith(REVERSION_METRIC_PREFIX)
        and metric_name.endswith(REVERSION_METRIC_SUFFIX)
    )


def _require_context_ranking(value: str) -> None:
    if value not in TOXICITY_CONTEXT_RANKINGS:
        raise ValueError(
            "context_ranking must be one of: "
            + ", ".join(TOXICITY_CONTEXT_RANKINGS)
        )


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
