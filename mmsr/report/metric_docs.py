"""Render metric definitions for report appendices/help."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from html import escape

from mmsr.metrics.base import MetricDefinition
from mmsr.report.components import HtmlBlock, ReportDocument, ReportPage


@dataclass(frozen=True)
class MetricDefinitionsAppendixOptions:
    """Presentation options for deterministic metric definitions appendices."""

    title: str = "Metric Definitions Appendix"
    block_title: str = "Metric documentation"
    help_text: str = (
        "Definitions, formulas, units, aggregation rules, and caveats for the "
        "metrics shown in this report."
    )

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.block_title.strip():
            raise ValueError("block_title must not be empty")
        if not self.help_text.strip():
            raise ValueError("help_text must not be empty")


def metric_definitions_markdown(metrics: Iterable[MetricDefinition]) -> str:
    """Render metric definitions as deterministic markdown.

    This text-oriented representation is useful for static exports such as PDF
    appendices or spreadsheet definition sheets.
    """

    sections: list[str] = []
    for metric in _sorted_metric_definitions(metrics):
        sections.append(
            f"## {metric.label}\n\n"
            f"**Name:** `{metric.name}`\n\n"
            f"**Category:** {metric.category}\n\n"
            f"**Description:** {metric.description}\n\n"
            f"**Formula:** `{metric.formula}`\n\n"
            f"**Interpretation:** {metric.interpretation}\n\n"
            f"**Unit:** {metric.unit}\n\n"
            f"**Default aggregation:** {metric.default_aggregation}\n\n"
            f"**Direction:** {_metric_direction_text(metric)}\n\n"
            f"**Supports intraday:** {_yes_no(metric.supports_intraday)}\n\n"
            f"**Supports symbol level:** {_yes_no(metric.supports_symbol_level)}\n\n"
            f"**Required tables:** {_comma_list(metric.required_tables)}\n\n"
            f"**Required columns:** {_comma_list(metric.required_columns)}\n\n"
            f"**Caveats:** {_semicolon_list(metric.caveats)}\n"
        )
    return "\n".join(sections)


def collect_metric_definitions_from_pages(
    pages: Iterable[ReportPage],
) -> tuple[MetricDefinition, ...]:
    """Collect unique metric definitions used by report-page components.

    Definitions from metric cards, metric table rows, time-series charts,
    compact Plotly charts, and heatmaps are de-duplicated by metric name and sorted by category, label, and
    appendix is stable across repeated report runs.
    """

    definitions: dict[str, MetricDefinition] = {}
    for page in pages:
        for card in page.metric_cards:
            _register_definition(definitions, card.metric)
        for table in page.metric_tables:
            for row in table.rows:
                _register_definition(definitions, row.metric)
        for chart in page.time_series_charts:
            _register_definition(definitions, chart.metric)
        for chart in page.plotly_charts:
            _register_definition(definitions, chart.metric)
        for heatmap in page.heatmaps:
            _register_definition(definitions, heatmap.metric)
    return tuple(_sorted_metric_definitions(definitions.values()))


def build_metric_definitions_appendix_page(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
    *,
    options: MetricDefinitionsAppendixOptions | None = None,
) -> ReportPage:
    """Build a report page containing metric documentation/help text."""

    resolved_options = options or MetricDefinitionsAppendixOptions()
    definitions = _metric_definition_values(metric_definitions)
    body_html = _metric_definitions_html(definitions)

    return ReportPage(
        title=resolved_options.title.strip(),
        html_blocks=[
            HtmlBlock(
                title=resolved_options.block_title.strip(),
                body_html=body_html,
                help_text=resolved_options.help_text.strip(),
            )
        ],
    )


def append_metric_definitions_appendix(
    document: ReportDocument,
    *,
    metric_definitions: (
        Mapping[str, MetricDefinition] | Iterable[MetricDefinition] | None
    ) = None,
    options: MetricDefinitionsAppendixOptions | None = None,
) -> ReportDocument:
    """Return a copy of ``document`` with a metric definitions appendix appended.

    When ``metric_definitions`` is omitted, definitions are collected from metric
    cards already present in the document's pages. The input document is not
    mutated.
    """

    definitions = (
        collect_metric_definitions_from_pages(document.pages)
        if metric_definitions is None
        else _metric_definition_values(metric_definitions)
    )
    appendix = build_metric_definitions_appendix_page(
        definitions,
        options=options,
    )
    return ReportDocument(
        title=document.title,
        pages=[*document.pages, appendix],
        branding=document.branding,
        generated_at_text=document.generated_at_text,
    )


def _register_definition(
    definitions: dict[str, MetricDefinition],
    metric: MetricDefinition,
) -> None:
    existing = definitions.get(metric.name)
    if existing is not None and existing != metric:
        raise ValueError(
            "conflicting metric definitions for appendix metric: "
            f"{metric.name}"
        )
    definitions[metric.name] = metric


def _metric_definition_values(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition],
) -> tuple[MetricDefinition, ...]:
    if isinstance(metric_definitions, Mapping):
        return tuple(_sorted_metric_definitions(metric_definitions.values()))
    return tuple(_sorted_metric_definitions(metric_definitions))


def _sorted_metric_definitions(
    metrics: Iterable[MetricDefinition],
) -> tuple[MetricDefinition, ...]:
    return tuple(
        sorted(
            metrics,
            key=lambda metric: (
                metric.category.casefold(),
                metric.label.casefold(),
                metric.name.casefold(),
            ),
        )
    )


def _metric_definitions_html(metrics: Sequence[MetricDefinition]) -> str:
    if not metrics:
        return (
            '<p class="metric-definitions__empty">'
            "No metric definitions were supplied for this report."
            "</p>"
        )

    rows = "\n".join(_metric_definition_details(metric) for metric in metrics)
    return f'<div class="metric-definitions">\n{rows}\n</div>'


def _metric_definition_details(metric: MetricDefinition) -> str:
    caveats_html = _list_html(metric.caveats or ["None"])
    tables = _comma_list(metric.required_tables)
    columns = _comma_list(metric.required_columns)
    intraday = _definition_field(
        "Supports intraday",
        _yes_no(metric.supports_intraday),
    )
    symbol_level = _definition_field(
        "Supports symbol level",
        _yes_no(metric.supports_symbol_level),
    )
    return (
        '<details class="metric-definition" open>\n'
        f'  <summary><strong>{escape(metric.label)}</strong> '
        f'<span class="metric-definition__category">({escape(metric.category)})</span>'
        "</summary>\n"
        '  <dl class="metric-definition__fields">\n'
        f"    {_definition_field('Name', metric.name)}\n"
        f"    {_definition_field('Description', metric.description)}\n"
        f"    {_definition_field('Formula', metric.formula, code=True)}\n"
        f"    {_definition_field('Interpretation', metric.interpretation)}\n"
        f"    {_definition_field('Unit', metric.unit)}\n"
        f"    {_definition_field('Default aggregation', metric.default_aggregation)}\n"
        f"    {_definition_field('Direction', _metric_direction_text(metric))}\n"
        f"    {intraday}\n"
        f"    {symbol_level}\n"
        f"    {_definition_field('Required tables', tables)}\n"
        f"    {_definition_field('Required columns', columns)}\n"
        "    <dt>Caveats</dt>\n"
        f"    <dd>{caveats_html}</dd>\n"
        "  </dl>\n"
        "</details>"
    )


def _definition_field(label: str, value: str, *, code: bool = False) -> str:
    rendered_value = escape(value)
    if code:
        rendered_value = f"<code>{rendered_value}</code>"
    return f"<dt>{escape(label)}</dt><dd>{rendered_value}</dd>"


def _list_html(items: Sequence[str]) -> str:
    item_html = "".join(f"<li>{escape(item)}</li>" for item in items)
    return f"<ul>{item_html}</ul>"


def _metric_direction_text(metric: MetricDefinition) -> str:
    if metric.higher_is_better is True:
        return "Higher values are generally better"
    if metric.higher_is_better is False:
        return "Lower values are generally better"
    return "No directional good/bad interpretation"


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _comma_list(values: Sequence[str]) -> str:
    return ", ".join(values) if values else "None"


def _semicolon_list(values: Sequence[str]) -> str:
    return "; ".join(values) if values else "None"
