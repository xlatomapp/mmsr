"""Deterministic report drilldown selection helpers.

The helpers in this module operate on already-computed ``MetricComparison``
objects. They do not calculate market microstructure metrics, query kdb+, or
call an LLM; they only select group-scoped comparison facts for sector, segment,
and market-cap report drilldowns.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from html import escape
from math import isfinite

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison
from mmsr.presentation.labels import (
    format_group_item_label,
    format_group_label,
    format_intraday_bucket_label,
)
from mmsr.report.components import Heatmap, HeatmapCell, HtmlBlock, MetricTable, MetricTableRow, ReportPage
from mmsr.report.symbols import DEFAULT_SYMBOL_GROUP_KEYS

DEFAULT_DRILLDOWN_GROUP_KEYS: tuple[str, ...] = (
    "topixCapGrp",
    "market_cap_bucket",
    "market_segment",
    "segment",
    "sector",
)


@dataclass(frozen=True)
class DrilldownSelectionOptions:
    """Configuration for deterministic group-level drilldown selection.

    ``group_keys`` defines which existing comparison group fields are considered
    drilldown dimensions. Rows with symbol identifiers are excluded by default so
    market-cap, segment, and sector drilldowns do not duplicate symbol anomaly
    pages.
    """

    group_keys: tuple[str, ...] = DEFAULT_DRILLDOWN_GROUP_KEYS
    max_rows: int | None = None
    include_symbol_scoped: bool = False
    symbol_group_keys: tuple[str, ...] = DEFAULT_SYMBOL_GROUP_KEYS
    statuses: tuple[str, ...] = ("alert", "watch", "comparison_only", "normal")

    def __post_init__(self) -> None:
        _validate_non_empty_keys(self.group_keys, "group_keys")
        _validate_non_empty_keys(self.symbol_group_keys, "symbol_group_keys")
        if self.max_rows is not None and self.max_rows < 0:
            raise ValueError("max_rows must be non-negative")
        _validate_non_empty_keys(self.statuses, "statuses")


@dataclass(frozen=True)
class DrilldownReportPageOptions:
    """Presentation options for a deterministic group drilldown page."""

    title: str = "Sector, Segment, and Market-Cap Drilldowns"
    table_title: str = "Top group-level drilldowns"
    help_text: str = (
        "Sector, segment, and market-cap drilldown rows are selected from "
        "already-computed comparison facts. The page does not calculate new "
        "metrics, query kdb+, or call an LLM."
    )
    selection: DrilldownSelectionOptions = field(default_factory=DrilldownSelectionOptions)

    def __post_init__(self) -> None:
        _validate_non_empty_text(self.title, "title")
        _validate_non_empty_text(self.table_title, "table_title")
        _validate_non_empty_text(self.help_text, "help_text")


def build_drilldown_report_page(
    comparisons: Sequence[MetricComparison],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: DrilldownReportPageOptions | None = None,
) -> ReportPage | None:
    """Build a sector/segment/market-cap drilldown page.

    The function formats selected group-scoped ``MetricComparison`` objects into
    a documented metric table. It is report-layer assembly only: all metric
    values, references, z-scores, percentiles, statuses, and confidence fields
    must already be present on the supplied comparisons.
    """

    resolved_options = options or DrilldownReportPageOptions()
    definitions = _metric_definition_map(metric_definitions)
    selected = select_drilldown_comparisons(
        comparisons,
        options=resolved_options.selection,
    )
    heatmap_selection = select_drilldown_comparisons(
        comparisons,
        options=DrilldownSelectionOptions(
            group_keys=resolved_options.selection.group_keys,
            max_rows=None,
            include_symbol_scoped=resolved_options.selection.include_symbol_scoped,
            symbol_group_keys=resolved_options.selection.symbol_group_keys,
            statuses=resolved_options.selection.statuses,
        ),
    )
    if not selected:
        return None

    _require_metric_definitions_for_comparisons(selected, definitions)
    delta_bars_block = _build_group_delta_bars_block(selected, definitions)
    matrix_explorer_block = _build_group_metric_explorer_block(heatmap_selection, definitions)
    table = MetricTable(
        title=resolved_options.table_title.strip(),
        rows=[
            _drilldown_metric_table_row_from_comparison(
                comparison,
                definitions[comparison.metric_name],
                group_keys=resolved_options.selection.group_keys,
            )
            for comparison in selected
        ],
        help_text=resolved_options.help_text.strip(),
    )
    html_blocks: list[HtmlBlock] = []
    if delta_bars_block is not None:
        html_blocks.append(delta_bars_block)
    if matrix_explorer_block is not None:
        html_blocks.append(matrix_explorer_block)
    return ReportPage(
        title=resolved_options.title.strip(),
        html_blocks=html_blocks,
        heatmaps=[],
        metric_tables=[table],
    )


_DELTA_BAR_MAX_ITEMS = 8


def _build_group_delta_bars_block(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> HtmlBlock | None:
    """Build a compact visual block ranking top group-level deltas.

    Renders horizontal CSS bars ordered by |change_pct| so the drilldown page
    leads with a scannable visual before the metric table.
    """
    if not comparisons:
        return None

    ranked = sorted(
        comparisons,
        key=lambda comp: -(abs(comp.change_pct or 0.0)),
    )[:_DELTA_BAR_MAX_ITEMS]

    if not ranked:
        return None

    max_abs_pct = max(abs(comp.change_pct or 0.0) for comp in ranked)
    if max_abs_pct == 0:
        return None

    rows_html = "\n".join(_delta_bar_row_html(comp, definitions.get(comp.metric_name), max_abs_pct) for comp in ranked)

    body_html = (
        '<div class="drilldown-delta-bars">\n'
        "  <p><strong>Top group deltas:</strong> "
        "current-versus-reference change ranked by magnitude. "
        "Bars are scaled to the largest absolute percentage change.</p>\n"
        f"{rows_html}\n"
        "</div>"
    )
    return HtmlBlock(
        title="Group Delta Overview",
        body_html=body_html,
        help_text="Deterministic group-level delta ranking from already-computed comparisons.",
    )


def _delta_bar_row_html(
    comparison: MetricComparison,
    definition: MetricDefinition | None,
    max_abs_pct: float,
) -> str:
    metric_label = definition.label if definition is not None else comparison.metric_name
    group_label = _format_drilldown_group_label(comparison)
    pct = comparison.change_pct or 0.0
    bar_width = (abs(pct) / max_abs_pct) * 100 if max_abs_pct > 0 else 0
    direction_class = "delta-bar--positive" if pct >= 0 else "delta-bar--negative"
    status_class = f"delta-bar--{comparison.status}"
    pct_text = f"{pct:+.1%}"

    return (
        f'  <div class="delta-bar {direction_class} {status_class}">\n'
        f'    <span class="delta-bar__label">{escape(metric_label)}'
        f" &mdash; {escape(group_label)}</span>\n"
        f'    <span class="delta-bar__track">'
        f'<span class="delta-bar__fill" style="width:{bar_width:.0f}%"></span>'
        f"</span>\n"
        f'    <span class="delta-bar__value">{escape(pct_text)}</span>\n'
        "  </div>"
    )


def _format_drilldown_group_label(comparison: MetricComparison) -> str:
    parts: list[str] = []
    for key in ("topixCapGrp", "market_cap_bucket", "sector", "segment", "market_segment"):
        if key in comparison.group:
            parts.append(str(comparison.group[key]))
    if not parts:
        parts.append(format_group_label(comparison.group))
    return ", ".join(parts)


_DRILLDOWN_HEATMAP_MAX_GROUPS = 10


def _build_group_metric_explorer_block(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> HtmlBlock | None:
    if not comparisons:
        return None

    pct_by_group_metric: dict[tuple[str, str], list[float]] = {}
    z_by_group_metric: dict[tuple[str, str], list[float]] = {}
    trend_by_group_metric_date: dict[str, dict[str, dict[str, list[float]]]] = {}
    metric_definitions_by_label: dict[str, MetricDefinition] = {}
    group_values: set[str] = set()
    dates: set[str] = set()
    preferred_metric_names = {
        "quoted_spread_bps",
        "top_of_book_depth",
    }

    for comp in comparisons:
        definition = definitions.get(comp.metric_name)
        if definition is None:
            continue
        if comp.metric_name not in preferred_metric_names:
            continue
        group_value = _primary_group_value(comp)
        if not group_value:
            continue
        metric_label = definition.label
        metric_definitions_by_label[metric_label] = definition
        group_values.add(group_value)
        if comp.change_pct is not None and isfinite(float(comp.change_pct)):
            pct_by_group_metric.setdefault((group_value, metric_label), []).append(float(comp.change_pct) * 100.0)
        if comp.z_score is not None and isfinite(float(comp.z_score)):
            z_by_group_metric.setdefault((group_value, metric_label), []).append(float(comp.z_score))
        if comp.value is not None:
            date_text = comp.date.isoformat() if comp.date is not None else "unknown"
            dates.add(date_text)
            metric_series = trend_by_group_metric_date.setdefault(group_value, {}).setdefault(metric_label, {})
            metric_series.setdefault(date_text, []).append(float(comp.value))

    if len(metric_definitions_by_label) < 2 or len(group_values) < 2:
        return None

    ordered_metrics = sorted(metric_definitions_by_label)
    ordered_groups = sorted(group_values)
    ordered_dates = sorted(dates)

    z_values: list[list[float | None]] = []
    text_values: list[list[str]] = []
    for group_value in ordered_groups:
        z_row: list[float | None] = []
        text_row: list[str] = []
        for metric_label in ordered_metrics:
            values = pct_by_group_metric.get((group_value, metric_label), [])
            if values:
                avg_pct = sum(values) / len(values)
                z_values_for_cell = z_by_group_metric.get((group_value, metric_label), [])
                avg_z = (sum(z_values_for_cell) / len(z_values_for_cell)) if z_values_for_cell else None
                z_row.append(avg_pct)
                if avg_z is None:
                    text_row.append(f"{avg_pct:+.1f}% (z —)")
                else:
                    text_row.append(f"{avg_pct:+.1f}% (z {avg_z:+.2f})")
            else:
                z_row.append(None)
                text_row.append("—")
        z_values.append(z_row)
        text_values.append(text_row)

    def _group_score(group_value: str) -> float:
        score = 0.0
        for metric_label in ordered_metrics:
            values = pct_by_group_metric.get((group_value, metric_label), [])
            if values:
                score += abs(sum(values) / len(values))
        return score

    default_group = max(ordered_groups, key=_group_score)

    trend_payload: dict[str, dict[str, list[float | None]]] = {}
    for group_value in ordered_groups:
        trend_payload[group_value] = {}
        for metric_label in ordered_metrics:
            values_by_date = trend_by_group_metric_date.get(group_value, {}).get(metric_label, {})
            series: list[float | None] = []
            for date_text in ordered_dates:
                entries = values_by_date.get(date_text, [])
                if entries:
                    series.append(sum(entries) / len(entries))
                else:
                    series.append(None)
            trend_payload[group_value][metric_label] = series

    payload = {
        "groups": ordered_groups,
        "metrics": ordered_metrics,
        "dates": ordered_dates,
        "z": z_values,
        "text": text_values,
        "trend_values": trend_payload,
        "default_group": default_group,
    }
    payload_json = _json_script_payload(payload)

    body_html = f"""
<div class="drilldown-matrix-explorer" data-drilldown-matrix>
  <div class="drilldown-matrix-explorer__grid">
    <div class="drilldown-matrix-explorer__panel">
      <h4>Group-Metric Heatmap</h4>
      <p>Rows are groups, columns are liquidity metrics.
      Cells show mean % change, with mean z-score in parentheses for reference.</p>
      <div class="drilldown-matrix-explorer__chart" data-drilldown-heatmap></div>
      <p class="drilldown-matrix-explorer__legend">
        Cell format: mean % change (z-score reference).
      </p>
    </div>
    <div class="drilldown-matrix-explorer__panel">
      <h4>Selected Group Daily Trend</h4>
      <p data-drilldown-selected-group></p>
      <div class="drilldown-matrix-explorer__chart" data-drilldown-trend></div>
    </div>
  </div>
  <script type="application/json" data-drilldown-matrix-spec>{payload_json}</script>
</div>
"""
    return HtmlBlock(
        title="Metric Explorer & Group Analysis",
        body_html=body_html.strip(),
        help_text=(
            "Unified group-versus-metric heatmap with click-linked daily trend rendered from existing comparison facts."
        ),
    )


def _json_script_payload(payload: object) -> str:
    """Serialize JSON for script-tag payloads without HTML entity escaping."""
    return json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")


def _build_drilldown_heatmaps(
    comparisons: tuple[MetricComparison, ...],
    definitions: Mapping[str, MetricDefinition],
) -> list[Heatmap]:
    """Build per-metric Heatmap components showing change_pct across groups.

    Each heatmap renders as an inline SVG with groups on the x-axis and a
    single metric row on the y-axis. Cell color intensity reflects |change_pct|.
    """
    if not comparisons:
        return []

    grouped: dict[str, list[MetricComparison]] = {}
    for comp in comparisons:
        gv = _primary_group_value(comp)
        if not gv:
            continue
        grouped.setdefault(comp.metric_name, []).append(comp)

    heatmaps: list[Heatmap] = []
    for metric_name, comps in grouped.items():
        definition = definitions.get(metric_name)
        if definition is None:
            continue
        best_by_group: dict[str, MetricComparison] = {}
        for comp in comps:
            gv = _primary_group_value(comp)
            if not gv:
                continue
            existing = best_by_group.get(gv)
            if existing is None or abs(comp.change_pct or 0.0) > abs(existing.change_pct or 0.0):
                best_by_group[gv] = comp

        sorted_groups = sorted(best_by_group, key=lambda gv: -abs(best_by_group[gv].change_pct or 0.0))[
            :_DRILLDOWN_HEATMAP_MAX_GROUPS
        ]
        if len(sorted_groups) < 2:
            continue

        cells = [
            HeatmapCell(
                x_text=gv,
                y_text=definition.label,
                value_text=(
                    f"{best_by_group[gv].change_pct:+.1%}" if best_by_group[gv].change_pct is not None else "—"
                ),
                value=best_by_group[gv].change_pct,
                group_text=f"{definition.label} — {gv}",
            )
            for gv in sorted_groups
        ]
        heatmaps.append(
            Heatmap(
                title=f"{definition.label} change by group",
                metric=definition,
                cells=cells,
                x_axis_label="Group",
                y_axis_label="Metric",
                help_text=f"Percentage change in {definition.label} versus reference across drilldown groups.",
            )
        )

    return heatmaps


def _primary_group_value(comparison: MetricComparison) -> str:
    """Return the most meaningful drilldown group value for heatmap columns."""
    for key in ("market_cap_bucket", "sector", "segment", "topixCapGrp", "market_segment"):
        if key in comparison.group:
            return str(comparison.group[key])
    for key, value in comparison.group.items():
        if key not in ("sym", "ric", "isin", "ticker", "venue", "horizon"):
            return str(value)
    return ""


def select_drilldown_comparisons(
    comparisons: Sequence[MetricComparison],
    *,
    options: DrilldownSelectionOptions | None = None,
) -> tuple[MetricComparison, ...]:
    """Return deterministic group-level comparisons for drilldown pages.

    A comparison is selected when its group contains at least one configured
    drilldown key with a non-empty value. Symbol-scoped rows are excluded unless
    ``include_symbol_scoped`` is enabled. The result is sorted severity-first and
    then by configured drilldown dimension/value, metric, date, bucket, and full
    group mapping for stable report rendering.
    """

    resolved_options = options or DrilldownSelectionOptions()
    selected = tuple(
        comparison
        for comparison in comparisons
        if _has_any_group_value(comparison, resolved_options.group_keys)
        and comparison.status in resolved_options.statuses
        and (
            resolved_options.include_symbol_scoped
            or not _has_any_group_value(comparison, resolved_options.symbol_group_keys)
        )
    )
    ordered = tuple(
        sorted(
            selected,
            key=lambda comparison: _drilldown_sort_key(comparison, resolved_options),
        )
    )
    if resolved_options.max_rows is None:
        return ordered
    return ordered[: resolved_options.max_rows]


def drilldown_scope_key(
    comparison: MetricComparison,
    *,
    group_keys: tuple[str, ...] = DEFAULT_DRILLDOWN_GROUP_KEYS,
) -> tuple[tuple[str, str], ...]:
    """Return the configured drilldown key/value pairs present on a comparison."""

    _validate_non_empty_keys(group_keys, "group_keys")
    return tuple(
        (key, comparison.group[key].strip())
        for key in group_keys
        if key in comparison.group and comparison.group[key].strip()
    )


def _drilldown_metric_table_row_from_comparison(
    comparison: MetricComparison,
    definition: MetricDefinition,
    *,
    group_keys: tuple[str, ...],
) -> MetricTableRow:
    unit = definition.unit
    reference_text = (
        None if comparison.reference_value is None else _format_metric_value(comparison.reference_value, unit)
    )
    return MetricTableRow(
        metric=definition,
        value_text=_format_metric_value(comparison.value, unit),
        reference_text=reference_text,
        change_text=_format_change(comparison, unit),
        status=comparison.status,
        group_text=_format_drilldown_scope(comparison, group_keys),
    )


def _format_drilldown_scope(
    comparison: MetricComparison,
    group_keys: tuple[str, ...],
) -> str:
    parts: list[str] = []
    if comparison.date is not None:
        parts.append(format_group_item_label("date", comparison.date))
    if comparison.time_bucket is not None:
        bucket_label = format_intraday_bucket_label(comparison.time_bucket)
        if bucket_label is not None:
            parts.append(format_group_item_label("time_bucket", bucket_label))

    scope_group = _ordered_drilldown_group(comparison.group, group_keys)
    group_text = format_group_label(
        scope_group,
        group_by=tuple(scope_group),
    )
    if group_text is not None:
        parts.append(group_text)

    if parts:
        return ", ".join(parts)
    return format_group_label(comparison.group) or "report scope"


def _ordered_drilldown_group(
    group: Mapping[str, str],
    group_keys: tuple[str, ...],
) -> dict[str, str]:
    ordered: dict[str, str] = {}
    for key in group_keys:
        value = group.get(key)
        if value is not None and value.strip():
            ordered[key] = value.strip()
    for key in sorted(group):
        if key in ordered:
            continue
        value = group[key]
        if value.strip():
            ordered[key] = value.strip()
    return ordered


def _metric_definition_map(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
) -> dict[str, MetricDefinition]:
    if isinstance(metric_definitions, Mapping):
        return dict(metric_definitions)
    return {definition.name: definition for definition in metric_definitions}


def _require_metric_definitions_for_comparisons(
    comparisons: Sequence[MetricComparison],
    definitions: Mapping[str, MetricDefinition],
) -> None:
    missing = sorted({comparison.metric_name for comparison in comparisons} - set(definitions.keys()))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"metric definitions are required for drilldown report components: {missing_text}")


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


def _drilldown_sort_key(
    comparison: MetricComparison,
    options: DrilldownSelectionOptions,
) -> tuple[int, float, int, str, str, str, str, str]:
    priority = {"alert": 0, "watch": 1, "comparison_only": 2, "normal": 3}
    scope = drilldown_scope_key(comparison, group_keys=options.group_keys)
    first_scope_key, first_scope_value = scope[0] if scope else ("", "")
    dimension_index = (
        options.group_keys.index(first_scope_key) if first_scope_key in options.group_keys else len(options.group_keys)
    )
    date_key = "" if comparison.date is None else comparison.date.isoformat()
    bucket_key = "" if comparison.time_bucket is None else str(comparison.time_bucket)
    severity_magnitude = _severity_magnitude(comparison)
    return (
        priority.get(comparison.status, 99),
        -severity_magnitude,
        dimension_index,
        first_scope_value,
        comparison.metric_name,
        date_key,
        bucket_key,
        repr(sorted(comparison.group.items())),
    )


def _severity_magnitude(comparison: MetricComparison) -> float:
    candidates = (
        comparison.z_score,
        comparison.change_pct,
        comparison.change_abs,
    )
    finite_values = [abs(float(value)) for value in candidates if value is not None and isfinite(float(value))]
    if not finite_values:
        return 0.0
    return max(finite_values)


def _has_any_group_value(
    comparison: MetricComparison,
    keys: tuple[str, ...],
) -> bool:
    return any(key in comparison.group and comparison.group[key].strip() for key in keys)


def _validate_non_empty_text(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _validate_non_empty_keys(keys: tuple[str, ...], field_name: str) -> None:
    if not keys:
        raise ValueError(f"{field_name} must not be empty")
    for key in keys:
        if not key.strip():
            raise ValueError(f"{field_name} must not contain empty values")


__all__ = [
    "DEFAULT_DRILLDOWN_GROUP_KEYS",
    "DrilldownReportPageOptions",
    "DrilldownSelectionOptions",
    "build_drilldown_report_page",
    "drilldown_scope_key",
    "select_drilldown_comparisons",
]
