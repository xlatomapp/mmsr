"""Symbol-level anomaly report helpers.

These builders operate on already-computed ``MetricComparison`` and
``MetricTimeSeries`` objects. They do not calculate market microstructure
metrics, query kdb+, or call an LLM; they select and format symbol-scoped
facts into deterministic report components.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha1
from html import escape
from math import isfinite

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.presentation.labels import format_comparison_scope_label
from mmsr.report.components import HtmlBlock, MetricTable, MetricTableRow, ReportPage
from mmsr.report.sections import build_heatmap, build_intraday_time_bucket_chart

DEFAULT_SYMBOL_GROUP_KEYS: tuple[str, ...] = (
    "symbol",
    "ticker",
    "security_code",
    "sym",
)


@dataclass(frozen=True)
class SymbolAnomalyPageOptions:
    """Presentation options for a deterministic symbol-level anomaly page."""

    title: str = "Symbol Anomalies"
    table_title: str = "Top symbol-level anomalies"
    help_text: str = (
        "Symbol-level anomaly rows are selected from already-computed "
        "comparison facts. The default page shows the worst comparison per "
        "symbol using status, adverse-tail diagnostics, z-score magnitude, and "
        "absolute percentage change as deterministic ranking inputs."
    )
    max_symbols: int = 20
    symbol_group_keys: tuple[str, ...] = DEFAULT_SYMBOL_GROUP_KEYS
    include_normal: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.table_title.strip():
            raise ValueError("table_title must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")
        if self.max_symbols < 0:
            raise ValueError("max_symbols must be non-negative")
        _validate_symbol_group_keys(self.symbol_group_keys)


@dataclass(frozen=True)
class SymbolDetailPageOptions:
    """Presentation options for optional per-symbol detail pages."""

    title_template: str = "Symbol {symbol} Detail"
    help_text: str = (
        "Per-symbol detail pages render existing symbol-scoped metric time "
        "series for selected anomaly symbols. They are report-layer diagnostics "
        "only: no new metrics are calculated, no kdb queries are run, and no LLM "
        "commentary is generated."
    )
    max_symbols: int = 5
    symbol_group_keys: tuple[str, ...] = DEFAULT_SYMBOL_GROUP_KEYS
    include_normal: bool = False
    chart_group_by: tuple[str, ...] = ("market_cap_bucket",)
    heatmap_group_by: tuple[str, ...] = ("market_cap_bucket",)
    max_chart_points: int | None = None
    max_heatmap_cells: int | None = None
    include_heatmaps: bool = False

    def __post_init__(self) -> None:
        if not self.title_template.strip():
            raise ValueError("title_template must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")
        if self.max_symbols < 0:
            raise ValueError("max_symbols must be non-negative")
        _validate_symbol_group_keys(self.symbol_group_keys)
        _validate_group_by(self.chart_group_by, "chart_group_by")
        _validate_group_by(self.heatmap_group_by, "heatmap_group_by")
        if self.max_chart_points is not None and self.max_chart_points < 0:
            raise ValueError("max_chart_points must be non-negative")
        if self.max_heatmap_cells is not None and self.max_heatmap_cells < 0:
            raise ValueError("max_heatmap_cells must be non-negative")
        _format_symbol_title(self.title_template, "SAMPLE")


@dataclass(frozen=True)
class SymbolDetailIndexOptions:
    """Presentation options for a compact symbol-detail navigation block."""

    title: str = "Symbol Detail Index"
    help_text: str = (
        "Compact navigation for per-symbol detail pages. Rows are selected from "
        "the same already-computed symbol comparison facts that drive the "
        "symbol anomaly page; no additional metrics are calculated."
    )
    symbol_group_keys: tuple[str, ...] = DEFAULT_SYMBOL_GROUP_KEYS
    max_symbols: int = 5
    include_normal: bool = False

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")
        if self.max_symbols < 0:
            raise ValueError("max_symbols must be non-negative")
        _validate_symbol_group_keys(self.symbol_group_keys)


def select_symbol_anomalies(
    comparisons: Sequence[MetricComparison],
    *,
    options: SymbolAnomalyPageOptions | None = None,
) -> tuple[MetricComparison, ...]:
    """Return one deterministic worst comparison per symbol.

    The selection is intentionally conservative for report pages: by default it
    excludes ``normal`` rows, deduplicates to the highest-priority comparison per
    symbol, and then applies ``max_symbols``. Set ``include_normal=True`` in the
    options when a full symbol watchlist is desired.
    """

    resolved_options = options or SymbolAnomalyPageOptions()
    if resolved_options.max_symbols == 0:
        return ()

    symbol_scoped = [
        comparison
        for comparison in comparisons
        if _symbol_from_group(
            comparison.group,
            symbol_group_keys=resolved_options.symbol_group_keys,
        )
        is not None
        and (resolved_options.include_normal or comparison.status != "normal")
    ]
    ordered = sorted(symbol_scoped, key=_symbol_anomaly_sort_key)

    selected_by_symbol: dict[str, MetricComparison] = {}
    for comparison in ordered:
        symbol = _symbol_from_group(
            comparison.group,
            symbol_group_keys=resolved_options.symbol_group_keys,
        )
        if symbol is None or symbol in selected_by_symbol:
            continue
        selected_by_symbol[symbol] = comparison
        if len(selected_by_symbol) >= resolved_options.max_symbols:
            break

    return tuple(selected_by_symbol.values())


def build_symbol_anomaly_page(
    comparisons: Sequence[MetricComparison],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: SymbolAnomalyPageOptions | None = None,
) -> ReportPage | None:
    """Build a symbol-level anomaly page when symbol-scoped rows are available."""

    resolved_options = options or SymbolAnomalyPageOptions()
    definitions = _metric_definition_map(metric_definitions)
    selected = select_symbol_anomalies(comparisons, options=resolved_options)
    if not selected:
        return None

    _require_metric_definitions_for_comparisons(selected, definitions)
    table = MetricTable(
        title=resolved_options.table_title.strip(),
        rows=[
            _symbol_metric_table_row_from_comparison(
                comparison,
                definitions[comparison.metric_name],
                symbol_group_keys=resolved_options.symbol_group_keys,
            )
            for comparison in selected
        ],
        help_text=resolved_options.help_text.strip(),
    )
    return ReportPage(
        title=resolved_options.title.strip(),
        metric_tables=[table],
    )


def build_symbol_detail_pages(
    comparisons: Sequence[MetricComparison],
    current_series: Sequence[MetricTimeSeries],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: SymbolDetailPageOptions | None = None,
) -> tuple[ReportPage, ...]:
    """Build optional per-symbol detail pages from existing symbol time series.

    Selected symbols come from ``select_symbol_anomalies()`` so detail pages
    follow the same deterministic ordering as the anomaly summary page. A page is
    only emitted when at least one supplied ``MetricTimeSeries`` contains
    observations whose group includes the selected symbol. The function does not
    calculate metrics or fetch additional data.
    """

    resolved_options = options or SymbolDetailPageOptions()
    if resolved_options.max_symbols == 0:
        return ()

    selected = select_symbol_anomalies(
        comparisons,
        options=SymbolAnomalyPageOptions(
            max_symbols=resolved_options.max_symbols,
            symbol_group_keys=resolved_options.symbol_group_keys,
            include_normal=resolved_options.include_normal,
        ),
    )
    if not selected:
        return ()

    definitions = _metric_definition_map(metric_definitions)
    pages: list[ReportPage] = []
    for comparison in selected:
        symbol = _symbol_from_group(
            comparison.group,
            symbol_group_keys=resolved_options.symbol_group_keys,
        )
        if symbol is None:
            continue
        symbol_series = _filter_series_for_symbol(
            current_series,
            symbol,
            symbol_group_keys=resolved_options.symbol_group_keys,
        )
        if not symbol_series:
            continue
        _require_metric_definitions_for_series(symbol_series, definitions)

        charts = []
        heatmaps = []
        for series in symbol_series:
            definition = definitions[series.metric_name]
            charts.append(
                build_intraday_time_bucket_chart(
                    f"{definition.label} intraday time-bucket trend for symbol {symbol}",
                    series,
                    definition,
                    group_by=resolved_options.chart_group_by,
                    y_axis_label=_metric_axis_label(definition),
                    help_text=resolved_options.help_text,
                    max_points=resolved_options.max_chart_points,
                )
            )
            if resolved_options.include_heatmaps:
                heatmaps.append(
                    build_heatmap(
                        f"{definition.label} intraday diagnostics for symbol {symbol}",
                        series,
                        definition,
                        group_by=resolved_options.heatmap_group_by,
                        y_axis_label="Group",
                        help_text=resolved_options.help_text,
                        max_cells=resolved_options.max_heatmap_cells,
                    )
                )

        pages.append(
            ReportPage(
                title=_format_symbol_title(
                    resolved_options.title_template,
                    symbol,
                ),
                time_series_charts=charts,
                heatmaps=heatmaps,
                anchor_id=symbol_detail_anchor_id(symbol),
            )
        )

    return tuple(pages)


def build_symbol_detail_index_block(
    comparisons: Sequence[MetricComparison],
    detail_pages: Sequence[ReportPage],
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: SymbolDetailIndexOptions | None = None,
) -> HtmlBlock | None:
    """Build a compact navigation block for emitted symbol detail pages.

    The block is intended to sit near the symbol-anomaly table so production
    reports with multiple per-symbol sections expose an auditable path from the
    selected anomaly row to the matching detail page.
    """

    resolved_options = options or SymbolDetailIndexOptions()
    if resolved_options.max_symbols == 0 or not detail_pages:
        return None

    selected = select_symbol_anomalies(
        comparisons,
        options=SymbolAnomalyPageOptions(
            max_symbols=resolved_options.max_symbols,
            symbol_group_keys=resolved_options.symbol_group_keys,
            include_normal=resolved_options.include_normal,
        ),
    )
    if not selected:
        return None

    definitions = _metric_definition_map(metric_definitions)
    _require_metric_definitions_for_comparisons(selected, definitions)

    page_by_anchor = {
        page.anchor_id: page for page in detail_pages if page.anchor_id is not None and page.anchor_id.strip()
    }
    rows: list[str] = []
    for comparison in selected:
        symbol = _symbol_from_group(
            comparison.group,
            symbol_group_keys=resolved_options.symbol_group_keys,
        )
        if symbol is None:
            continue
        anchor_id = symbol_detail_anchor_id(symbol)
        page = page_by_anchor.get(anchor_id)
        if page is None:
            continue
        definition = definitions[comparison.metric_name]
        rows.append(
            "<tr>"
            f"<td>{escape(symbol)}</td>"
            f'<td><a href="#{escape(anchor_id, quote=True)}">'
            f"{escape(page.title)}</a></td>"
            f"<td>{escape(comparison.status.replace('_', ' ').title())}</td>"
            f"<td>{escape(definition.label)}</td>"
            f"<td>{escape(_format_symbol_scope(comparison, resolved_options.symbol_group_keys))}</td>"
            "</tr>"
        )

    if not rows:
        return None

    body_html = (
        f"<p>{len(rows)} symbol detail page"
        f"{'' if len(rows) == 1 else 's'} selected from the anomaly ranking.</p>"
        '<table class="symbol-detail-index">'
        "<thead><tr>"
        "<th>Symbol</th>"
        "<th>Detail page</th>"
        "<th>Status</th>"
        "<th>Driving metric</th>"
        "<th>Scope</th>"
        "</tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    )
    return HtmlBlock(
        title=resolved_options.title.strip(),
        body_html=body_html,
        help_text=resolved_options.help_text.strip(),
    )


def symbol_detail_anchor_id(symbol: str) -> str:
    """Return a stable HTML anchor id for a symbol-detail report page."""

    symbol_text = symbol.strip()
    if not symbol_text:
        raise ValueError("symbol must not be empty")
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", symbol_text).strip("-").lower()
    digest = sha1(symbol_text.encode("utf-8")).hexdigest()[:8]
    if slug:
        return f"symbol-detail-{slug}-{digest}"
    return f"symbol-detail-{digest}"


def _symbol_metric_table_row_from_comparison(
    comparison: MetricComparison,
    definition: MetricDefinition,
    *,
    symbol_group_keys: tuple[str, ...],
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
        group_text=_format_symbol_scope(comparison, symbol_group_keys),
    )


def _format_symbol_scope(
    comparison: MetricComparison,
    symbol_group_keys: tuple[str, ...],
) -> str:
    symbol = _symbol_from_group(
        comparison.group,
        symbol_group_keys=symbol_group_keys,
    )
    scope_text = format_comparison_scope_label(
        observation_date=comparison.date,
        time_bucket=comparison.time_bucket,
        group=comparison.group,
    )
    if scope_text is None:
        return f"Symbol: {symbol}"
    return scope_text


def _filter_series_for_symbol(
    series_collection: Sequence[MetricTimeSeries],
    symbol: str,
    *,
    symbol_group_keys: tuple[str, ...],
) -> tuple[MetricTimeSeries, ...]:
    filtered_series: list[MetricTimeSeries] = []
    for series in series_collection:
        observations = tuple(
            observation
            for observation in series.observations
            if _observation_symbol(
                observation,
                symbol_group_keys=symbol_group_keys,
            )
            == symbol
        )
        if not observations:
            continue
        metadata = {
            **series.metadata,
            "filtered_symbol": symbol,
            "source_metric_series": series.metric_name,
        }
        filtered_series.append(
            MetricTimeSeries.from_observations(
                observations,
                metric_name=series.metric_name,
                metadata=metadata,
            )
        )
    return tuple(filtered_series)


def _observation_symbol(
    observation: MetricObservation,
    *,
    symbol_group_keys: tuple[str, ...],
) -> str | None:
    return _symbol_from_group(observation.group, symbol_group_keys=symbol_group_keys)


def _symbol_from_group(
    group: Mapping[str, str],
    *,
    symbol_group_keys: tuple[str, ...],
) -> str | None:
    for key in symbol_group_keys:
        value = group.get(key)
        if value is not None and value.strip():
            return value.strip()
    return None


def _symbol_anomaly_sort_key(
    comparison: MetricComparison,
) -> tuple[int, float, float, float, str, str, str]:
    priority = {"alert": 0, "watch": 1, "comparison_only": 2, "normal": 3}
    adverse_tail = _adverse_tail_score(comparison)
    z_magnitude = _finite_abs(comparison.z_score)
    pct_magnitude = _finite_abs(comparison.change_pct)
    date_key = "" if comparison.date is None else comparison.date.isoformat()
    bucket_key = "" if comparison.time_bucket is None else str(comparison.time_bucket)
    return (
        priority.get(comparison.status, 99),
        adverse_tail,
        -z_magnitude,
        -pct_magnitude,
        comparison.metric_name,
        date_key,
        bucket_key,
    )


def _adverse_tail_score(comparison: MetricComparison) -> float:
    candidates = (
        comparison.normal_score_adverse_tail_probability,
        comparison.empirical_adverse_tail_probability,
    )
    finite_candidates = [float(value) for value in candidates if value is not None and isfinite(float(value))]
    if not finite_candidates:
        return 1.0
    return min(finite_candidates)


def _finite_abs(value: float | None) -> float:
    if value is None or not isfinite(float(value)):
        return 0.0
    return abs(float(value))


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
        raise ValueError(f"metric definitions are required for symbol anomaly report components: {missing_text}")


def _require_metric_definitions_for_series(
    series_collection: Sequence[MetricTimeSeries],
    definitions: Mapping[str, MetricDefinition],
) -> None:
    missing = sorted({series.metric_name for series in series_collection} - set(definitions.keys()))
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"metric definitions are required for symbol detail report components: {missing_text}")


def _metric_axis_label(definition: MetricDefinition) -> str:
    if definition.unit:
        return f"{definition.label} ({definition.unit})"
    return definition.label


def _format_symbol_title(title_template: str, symbol: str) -> str:
    try:
        title = title_template.format(symbol=symbol)
    except (KeyError, IndexError) as exc:
        raise ValueError("title_template may only use the named {symbol} placeholder") from exc
    if not title.strip():
        raise ValueError("title_template must render a non-empty title")
    return title.strip()


def _validate_symbol_group_keys(symbol_group_keys: tuple[str, ...]) -> None:
    if not symbol_group_keys:
        raise ValueError("symbol_group_keys must not be empty")
    for key in symbol_group_keys:
        if not key.strip():
            raise ValueError("symbol_group_keys must not contain empty values")


def _validate_group_by(group_by: tuple[str, ...], field_name: str) -> None:
    for key in group_by:
        if not key.strip():
            raise ValueError(f"{field_name} must not contain empty values")


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


__all__ = [
    "DEFAULT_SYMBOL_GROUP_KEYS",
    "SymbolAnomalyPageOptions",
    "SymbolDetailIndexOptions",
    "SymbolDetailPageOptions",
    "build_symbol_anomaly_page",
    "build_symbol_detail_index_block",
    "build_symbol_detail_pages",
    "select_symbol_anomalies",
    "symbol_detail_anchor_id",
]
