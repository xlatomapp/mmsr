"""Deterministic executive market overview builder."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from html import escape
from math import isfinite

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison
from mmsr.presentation.labels import format_comparison_scope_label
from mmsr.report.components import HtmlBlock

_STATUS_PRIORITY: dict[str, int] = {
    "alert": 0,
    "watch": 1,
    "comparison_only": 2,
    "normal": 3,
}

_STATUS_LABELS: dict[str, str] = {
    "alert": "Alert",
    "watch": "Watch",
    "comparison_only": "Comparison only",
    "normal": "Normal",
}

_MARKET_SUMMARY_FAMILIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Market activity", ("turnover", "volume", "trade_count")),
    ("Displayed liquidity", ("quoted_spread_bps", "top_of_book_depth")),
    (
        "Cross-venue reversion",
        tuple(f"primary_quote_reversion_{horizon}_bps" for horizon in ("10ms", "100ms", "500ms", "1s", "5s", "10s")),
    ),
)

_NARRATIVE_MAX_CHANGES = 5


@dataclass(frozen=True)
class ExecutiveOverviewOptions:
    """Presentation options for the deterministic executive overview."""

    title: str = "Executive Market Overview"
    help_text: str = (
        "High-level deterministic summary of already-computed comparison "
        "results across key metrics. This section does not calculate new market "
        "metrics, query kdb+, or use an LLM."
    )
    max_metric_summaries: int = 5

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")
        if self.max_metric_summaries < 0:
            raise ValueError("max_metric_summaries must be non-negative")


@dataclass(frozen=True)
class _MetricOverview:
    metric_name: str
    metric_label: str
    status: str
    comparison_count: int
    alert_count: int
    watch_count: int
    normal_count: int
    comparison_only_count: int
    average_value: float | None
    average_reference_value: float | None
    average_change_abs: float | None
    average_change_pct: float | None
    most_severe_scope: str | None
    unit: str


@dataclass(frozen=True)
class _MetricFamilyOverview:
    family_label: str
    status: str
    comparison_count: int
    observed_metric_labels: tuple[str, ...]
    alert_count: int
    watch_count: int
    normal_count: int
    comparison_only_count: int
    leading_metric: _MetricOverview


def build_executive_market_overview_block(
    comparisons: Sequence[MetricComparison],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: ExecutiveOverviewOptions | None = None,
) -> HtmlBlock:
    """Build a deterministic high-level market overview HTML block.

    The block summarizes already-computed comparison status and average current
    versus reference values by metric. It is presentation-only glue: it does not
    calculate new metrics, query kdb+, or call an LLM.
    """

    resolved_options = options or ExecutiveOverviewOptions()
    definitions = _metric_definition_map(metric_definitions)
    _require_metric_definitions(comparisons, definitions)

    body_html = _overview_html(
        tuple(comparisons),
        definitions,
        max_metric_summaries=resolved_options.max_metric_summaries,
    )
    return HtmlBlock(
        title=resolved_options.title.strip(),
        body_html=body_html,
        help_text=resolved_options.help_text.strip(),
    )


def _overview_html(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
    *,
    max_metric_summaries: int,
) -> str:
    if not comparisons:
        return (
            '<section class="executive-overview executive-overview--empty">'
            '<p class="executive-overview__status">'
            "<strong>Overall status:</strong> No comparison observations were "
            "supplied for this report."
            "</p>"
            "</section>"
        )

    status_counts = Counter(comparison.status for comparison in comparisons)
    overall_status = _overall_status(status_counts)

    # Narrative highlights: top 3-5 specific changes with context
    highlights_html = _narrative_highlights_html(comparisons, definitions)

    # Compact status summary below the narrative
    status_text = _status_count_sentence(status_counts)
    family_html = _metric_family_overview_html(
        comparisons, tuple(_metric_overviews(comparisons, definitions)[:max_metric_summaries])
    )

    return (
        f'<section class="executive-overview executive-overview--{escape(overall_status)}">\n'
        f"{highlights_html}"
        '  <p class="executive-overview__status">'
        f"<strong>Overall:</strong> {_status_label(overall_status)} — "
        f"{escape(status_text)} across {len(_unique_metric_names(comparisons))} "
        f"key metrics and {len(comparisons)} comparisons."
        "</p>\n"
        f"{family_html}"
        "</section>"
    )


def _narrative_highlights_html(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> str:
    """Return HTML for the top 3-5 specific market-level changes."""
    top_changes = _select_top_changes(comparisons)
    if not top_changes:
        return ""

    sentences = [_change_narrative_sentence(change, definitions.get(change.metric_name)) for change in top_changes]
    items = "\n".join(
        f'    <li class="executive-overview__highlight">{escape(sentence)}</li>' for sentence in sentences if sentence
    )
    if not items.strip():
        return ""

    return (
        '  <div class="executive-overview__highlights">\n'
        "    <p><strong>Key changes this period:</strong></p>\n"
        "    <ul>\n"
        f"{items}\n"
        "    </ul>\n"
        "  </div>\n"
    )


def _select_top_changes(
    comparisons: tuple[MetricComparison, ...],
) -> tuple[MetricComparison, ...]:
    """Return the top N comparison rows ranked by severity and magnitude."""
    # Only consider market-level rows (not symbol-level)
    market_comparisons = tuple(comp for comp in comparisons if "sym" not in comp.group)
    if not market_comparisons:
        return ()

    ranked = sorted(
        market_comparisons,
        key=lambda comp: (
            _STATUS_PRIORITY.get(comp.status, 99),
            -(abs(comp.z_score or 0.0)),
            -(abs(comp.change_pct or 0.0)),
        ),
    )
    # Return top N, but only those with meaningful deviation
    return tuple(comp for comp in ranked[:_NARRATIVE_MAX_CHANGES] if comp.status in ("alert", "watch"))


def _change_narrative_sentence(
    comparison: MetricComparison,
    definition: MetricDefinition | None,
) -> str:
    """Build a deterministic sentence for one comparison change."""
    label = definition.label if definition else comparison.metric_name
    direction = _change_direction_word(comparison, definition)
    magnitude = _format_change_magnitude(comparison)
    context = _format_change_context(comparison)

    sentence = f"{label} {direction}{magnitude}"
    if context:
        sentence += f" in {context}"
    sentence += "."

    if definition and definition.interpretation:
        sentence += f" {definition.interpretation}"

    return sentence


def _change_direction_word(
    comparison: MetricComparison,
    definition: MetricDefinition | None,
) -> str:
    """Return a human-readable direction word for the change."""
    pct = comparison.change_pct
    if pct is None or not isfinite(float(pct)):
        return "changed"
    higher_is_better = definition.higher_is_better if definition else True
    abs_pct = abs(pct)
    if abs_pct < 0.01:
        return "was flat"
    if pct > 0:
        return "increased" if higher_is_better else "rose"
    return "decreased" if higher_is_better else "declined"


def _format_change_magnitude(comparison: MetricComparison) -> str:
    """Return a formatted magnitude suffix for the change, e.g. ' 40%'."""
    if comparison.change_pct is not None and isfinite(float(comparison.change_pct)):
        return f" {abs(comparison.change_pct):.0%}"
    if comparison.change_abs is not None and isfinite(float(comparison.change_abs)):
        return f" {comparison.change_abs:+,.0f}"
    return ""


def _format_change_context(comparison: MetricComparison) -> str:
    """Build context string from group, bucket, venue, and horizon metadata."""
    parts: list[str] = []
    group = comparison.group
    # Include meaningful classification keys; skip identifiers and raw codes
    _context_keys = ("topixCapGrp", "market_cap_bucket", "sector", "segment")
    for key in _context_keys:
        if key in group:
            parts.append(str(group[key]))
    # Venue and horizon context for reversion metrics
    if "venue" in group:
        parts.append(str(group["venue"]))
    if "horizon" in group:
        parts.append(str(group["horizon"]))
    # Auction bucket context
    if comparison.time_bucket is not None:
        bucket_str = str(comparison.time_bucket)
        if bucket_str in ("AMO", "AMC", "PMO", "PMC"):
            parts.append(f"{bucket_str} auction")
    if not parts:
        return ""
    return ", ".join(parts)


def _metric_overviews(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> tuple[_MetricOverview, ...]:
    grouped: dict[str, list[MetricComparison]] = {}
    for comparison in comparisons:
        grouped.setdefault(comparison.metric_name, []).append(comparison)

    overviews = [
        _metric_overview(metric_name, metric_comparisons, definitions[metric_name])
        for metric_name, metric_comparisons in grouped.items()
    ]
    return tuple(
        sorted(
            overviews,
            key=lambda summary: (
                _STATUS_PRIORITY.get(summary.status, 99),
                -(summary.alert_count + summary.watch_count),
                summary.metric_label.casefold(),
                summary.metric_name,
            ),
        )
    )


def _metric_overview(
    metric_name: str,
    comparisons: Sequence[MetricComparison],
    definition: MetricDefinition,
) -> _MetricOverview:
    status_counts = Counter(comparison.status for comparison in comparisons)
    most_severe = min(
        comparisons,
        key=lambda comparison: (
            _STATUS_PRIORITY.get(comparison.status, 99),
            -abs(comparison.z_score or 0.0),
            "" if comparison.date is None else comparison.date.isoformat(),
            "" if comparison.time_bucket is None else str(comparison.time_bucket),
            repr(sorted(comparison.group.items())),
        ),
    )

    return _MetricOverview(
        metric_name=metric_name,
        metric_label=definition.label,
        status=_overall_status(status_counts),
        comparison_count=len(comparisons),
        alert_count=status_counts.get("alert", 0),
        watch_count=status_counts.get("watch", 0),
        normal_count=status_counts.get("normal", 0),
        comparison_only_count=status_counts.get("comparison_only", 0),
        average_value=_average_numeric(comparison.value for comparison in comparisons),
        average_reference_value=_average_numeric(comparison.reference_value for comparison in comparisons),
        average_change_abs=_average_numeric(comparison.change_abs for comparison in comparisons),
        average_change_pct=_average_numeric(comparison.change_pct for comparison in comparisons),
        most_severe_scope=_format_scope(most_severe),
        unit=definition.unit,
    )


def _metric_family_overview_html(
    comparisons: tuple[MetricComparison, ...],
    metric_summaries: tuple[_MetricOverview, ...],
) -> str:
    family_summaries = _metric_family_overviews(comparisons, metric_summaries)
    if not family_summaries:
        return ""

    items = "\n".join(_metric_family_overview_item(summary) for summary in family_summaries)
    return (
        '  <div class="executive-overview__families" '
        'aria-label="Market activity and displayed liquidity summary">\n'
        f"{items}\n"
        "  </div>\n"
    )


def _metric_family_overviews(
    comparisons: tuple[MetricComparison, ...],
    metric_summaries: tuple[_MetricOverview, ...],
) -> tuple[_MetricFamilyOverview, ...]:
    metric_summary_by_name = {summary.metric_name: summary for summary in metric_summaries}
    selected_metric_names = set(metric_summary_by_name)
    family_overviews: list[_MetricFamilyOverview] = []
    for family_label, metric_names in _MARKET_SUMMARY_FAMILIES:
        family_comparisons = tuple(
            comparison
            for comparison in comparisons
            if comparison.metric_name in metric_names and comparison.metric_name in selected_metric_names
        )
        if not family_comparisons:
            continue

        status_counts = Counter(comparison.status for comparison in family_comparisons)
        observed_summaries = tuple(
            metric_summary_by_name[metric_name] for metric_name in metric_names if metric_name in metric_summary_by_name
        )
        leading_metric = min(
            observed_summaries,
            key=lambda summary: (
                _STATUS_PRIORITY.get(summary.status, 99),
                -(summary.alert_count + summary.watch_count),
                summary.metric_label.casefold(),
                summary.metric_name,
            ),
        )
        family_overviews.append(
            _MetricFamilyOverview(
                family_label=family_label,
                status=_overall_status(status_counts),
                comparison_count=len(family_comparisons),
                observed_metric_labels=tuple(summary.metric_label for summary in observed_summaries),
                alert_count=status_counts.get("alert", 0),
                watch_count=status_counts.get("watch", 0),
                normal_count=status_counts.get("normal", 0),
                comparison_only_count=status_counts.get("comparison_only", 0),
                leading_metric=leading_metric,
            )
        )
    return tuple(family_overviews)


def _metric_family_overview_item(summary: _MetricFamilyOverview) -> str:
    observed_metrics = ", ".join(summary.observed_metric_labels)
    leading = summary.leading_metric
    leading_current = _format_metric_value(leading.average_value, leading.unit)
    leading_reference = _format_metric_value(
        leading.average_reference_value,
        leading.unit,
    )
    leading_change = _format_change(
        leading.average_change_abs,
        leading.average_change_pct,
        leading.unit,
    )
    status_counts = Counter(
        {
            "alert": summary.alert_count,
            "watch": summary.watch_count,
            "comparison_only": summary.comparison_only_count,
            "normal": summary.normal_count,
        }
    )

    return (
        '    <p class="executive-overview__family">'
        f"<strong>{escape(summary.family_label)}:</strong> "
        f"{_status_label(summary.status)} — "
        f"{escape(_status_count_sentence(status_counts))} across "
        f"{summary.comparison_count} comparison rows from "
        f"{len(summary.observed_metric_labels)} observed metrics "
        f"({escape(observed_metrics)}). Leading signal: "
        f"{escape(leading.metric_label)} average current "
        f"{escape(leading_current)} versus reference "
        f"{escape(leading_reference)}{escape(leading_change)}."
        "</p>"
    )


def _metric_overview_item(summary: _MetricOverview) -> str:
    abnormal_count = summary.alert_count + summary.watch_count
    current_text = _format_metric_value(summary.average_value, summary.unit)
    reference_text = _format_metric_value(summary.average_reference_value, summary.unit)
    change_text = _format_change(
        summary.average_change_abs,
        summary.average_change_pct,
        summary.unit,
    )
    scope_text = summary.most_severe_scope or "selected universe"
    abnormal_text = f"{abnormal_count} alert/watch observations" if abnormal_count != 1 else "1 alert/watch observation"

    return (
        "    <li>"
        f"<strong>{escape(summary.metric_label)}</strong>: "
        f"{_status_label(summary.status).lower()} status across "
        f"{summary.comparison_count} comparisons; {abnormal_text}; "
        f"average current {escape(current_text)} versus reference "
        f"{escape(reference_text)}{escape(change_text)}; leading scope "
        f"{escape(scope_text)}."
        "</li>"
    )


def _overall_status(status_counts: Counter[str]) -> str:
    for status in ("alert", "watch", "comparison_only", "normal"):
        if status_counts.get(status, 0):
            return status
    return "normal"


def _status_count_sentence(status_counts: Counter[str]) -> str:
    return (
        f"{status_counts.get('alert', 0)} alerts, "
        f"{status_counts.get('watch', 0)} watch items, "
        f"{status_counts.get('comparison_only', 0)} comparison-only items, and "
        f"{status_counts.get('normal', 0)} normal items"
    )


def _format_change(
    change_abs: float | None,
    change_pct: float | None,
    unit: str,
) -> str:
    parts: list[str] = []
    if change_abs is not None:
        parts.append(f"change {_format_signed_metric_value(change_abs, unit)}")
    if change_pct is not None:
        parts.append(f"{change_pct:+.1%}")
    if not parts:
        return ""
    return " (" + " ".join(parts) + ")"


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


def _average_numeric(values: Iterable[float | int | None]) -> float | None:
    numeric_values = [float(value) for value in values if value is not None and isfinite(float(value))]
    if not numeric_values:
        return None
    return sum(numeric_values) / len(numeric_values)


def _format_scope(comparison: MetricComparison) -> str | None:
    return format_comparison_scope_label(
        observation_date=comparison.date,
        time_bucket=comparison.time_bucket,
        group=comparison.group,
    )


def _status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status.replace("_", " ").title())


def _unique_metric_names(comparisons: Iterable[MetricComparison]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for comparison in comparisons:
        if comparison.metric_name in seen:
            continue
        seen.add(comparison.metric_name)
        ordered.append(comparison.metric_name)
    return tuple(ordered)


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
    missing = sorted({comparison.metric_name for comparison in comparisons} - set(definitions.keys()))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"metric definitions are required for executive overview metrics: {missing_text}")


__all__ = [
    "ExecutiveOverviewOptions",
    "build_executive_market_overview_block",
]
