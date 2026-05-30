"""Template-driven HTML rendering helpers."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, PackageLoader, select_autoescape

from mmsr.report.components import (
    CommentaryBlock,
    Heatmap,
    MetricCard,
    MetricTable,
    PlotlyChart,
    ReportDocument,
    TimeSeriesChart,
)


def build_template_environment(template_dir: str | Path | None = None) -> Environment:
    """Build the Jinja environment used for HTML reports.

    Parameters
    ----------
    template_dir:
        Optional override directory. When omitted, the packaged templates under
        ``mmsr/report/templates`` are used.
    """
    if template_dir is None:
        loader = PackageLoader("mmsr.report", "templates")
    else:
        loader = FileSystemLoader(str(template_dir))

    return Environment(
        loader=loader,
        autoescape=select_autoescape(("html", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_metric_card(card: MetricCard) -> str:
    """Render a metric card using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/metric_card.html.j2")
    return template.render(card=card)


def render_metric_table(table: MetricTable) -> str:
    """Render a metric table using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/metric_table.html.j2")
    return template.render(table=table)


def render_time_series_chart(chart: TimeSeriesChart) -> str:
    """Render a time-series chart using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/time_series_chart.html.j2")
    return template.render(chart=chart)




def render_plotly_chart(chart: PlotlyChart) -> str:
    """Render a compact Plotly chart using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/plotly_chart.html.j2")
    return template.render(chart=chart)


def render_heatmap(heatmap: Heatmap) -> str:
    """Render a heatmap visual using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/heatmap.html.j2")
    return template.render(heatmap=heatmap)


def render_commentary(block: CommentaryBlock) -> str:
    """Render commentary block using the shared partial template."""
    env = build_template_environment()
    template = env.get_template("partials/commentary_block.html.j2")
    return template.render(block=block)


def render_report(
    document: ReportDocument,
    template_dir: str | Path | None = None,
) -> str:
    """Render a full HTML report document.

    The default report template is intentionally stable so repeated report runs
    have a consistent layout. Project-specific/client-specific branding can be
    supplied through ``ReportBranding`` or by passing a custom template directory.
    """
    env = build_template_environment(template_dir)
    template = env.get_template("report.html.j2")
    return template.render(document=document)
