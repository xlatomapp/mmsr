from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from mmsr.report.components import (
    CommentaryBlock,
    Heatmap,
    HtmlBlock,
    MetricCard,
    MetricTable,
    PlotlyChart,
    ReportDocument,
    ReportPage,
    TimeSeriesChart,
)

_SCRIPT_RE = re.compile(
    r'<script[^>]*type="application/json"[^>]*?(?:class="(?P<class>[^"]+)"|(?P<attr>data-[^=\s>]+))[^>]*>(?P<body>.*?)</script>',
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class _RenderedTable:
    headers: list[str]
    rows: list[list[str]]


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[_RenderedTable] = []
        self._in_table = False
        self._in_cell = False
        self._current_cell: list[str] = []
        self._current_row: list[str] = []
        self._headers: list[str] = []
        self._rows: list[list[str]] = []
        self._in_header = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._in_table = True
            self._headers = []
            self._rows = []
        elif self._in_table and tag == "thead":
            self._in_header = True
        elif self._in_table and tag in {"th", "td"}:
            self._in_cell = True
            self._current_cell = []
        elif self._in_table and tag == "tr":
            self._current_row = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._in_table:
            self.tables.append(_RenderedTable(headers=self._headers, rows=self._rows))
            self._in_table = False
            self._in_header = False
        elif self._in_table and tag in {"th", "td"} and self._in_cell:
            text = _clean_html_text("".join(self._current_cell))
            self._current_row.append(text)
            self._in_cell = False
        elif self._in_table and tag == "tr":
            if self._current_row:
                if self._in_header and not self._headers:
                    self._headers = self._current_row
                else:
                    self._rows.append(self._current_row)
            self._current_row = []
        elif self._in_table and tag == "thead":
            self._in_header = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)


def render_report_qmd(
    document: ReportDocument,
    *,
    asset_dir: Path,
    asset_root: str,
) -> str:
    renderer = _QuartoRenderer(document=document, asset_dir=asset_dir, asset_root=asset_root)
    return renderer.render()


def render_report_qmd_file(
    document: ReportDocument,
    output_path: str | Path,
    *,
    asset_dir_name: str | None = None,
) -> Path:
    resolved_output_path = Path(output_path)
    if resolved_output_path.exists() and resolved_output_path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_asset_dir_name = asset_dir_name or f"{resolved_output_path.stem}_assets"
    asset_dir = resolved_output_path.parent / resolved_asset_dir_name
    asset_dir.mkdir(parents=True, exist_ok=True)
    qmd = render_report_qmd(document, asset_dir=asset_dir, asset_root=resolved_asset_dir_name)
    resolved_output_path.write_text(qmd, encoding="utf-8")
    return resolved_output_path


class _QuartoRenderer:
    def __init__(self, *, document: ReportDocument, asset_dir: Path, asset_root: str) -> None:
        self.document = document
        self.asset_dir = asset_dir
        self.asset_root = asset_root
        self.asset_counter = 0

    def render(self) -> str:
        lines: list[str] = []
        lines.extend(self._front_matter())
        lines.append("")
        lines.extend(self._document_header())
        for page_index, page in enumerate(self.document.pages, start=1):
            lines.append("")
            lines.append(f"# {page.title}")
            lines.append("")
            lines.extend(self._render_page(page, page_index))
        return "\n".join(lines).rstrip() + "\n"

    def _front_matter(self) -> list[str]:
        title = self.document.title.replace('"', '\\"')
        return [
            "---",
            f'title: "{title}"',
            "number-sections: false",
            "toc: false",
            "format:",
            "  html:",
            "    theme: cosmo",
            "    toc: false",
            "  pdf:",
            "    documentclass: scrartcl",
            "    papersize: a4",
            "    fontsize: 10pt",
            "    geometry:",
            "      - margin=0.7in",
            "    colorlinks: true",
            "    toc: false",
            "  revealjs: default",
            "  pptx: default",
            "execute:",
            "  enabled: false",
            "---",
        ]

    def _document_header(self) -> list[str]:
        return []

    def _render_page(self, page: ReportPage, page_index: int) -> list[str]:
        lines: list[str] = []
        if page.metric_cards:
            lines.extend(self._render_metric_cards(page.metric_cards))
        for table in page.metric_tables:
            lines.extend(self._render_metric_table(table))
        for commentary in page.commentary_blocks:
            lines.extend(self._render_commentary_block(commentary))
        for chart in page.time_series_charts:
            lines.extend(self._render_time_series_chart(chart))
        for chart in page.plotly_charts:
            lines.extend(self._render_plotly_chart(chart))
        for heatmap in page.heatmaps:
            lines.extend(self._render_heatmap(heatmap))
        for block in page.html_blocks:
            lines.extend(self._render_html_block(block, page_index))
        return lines

    def _render_metric_cards(self, cards: list[MetricCard]) -> list[str]:
        lines = ["## Market Summary", ""]
        headers = ["Metric", "Current", "Reference"]
        rows = [
            [c.metric.label, _card_current_text(c.value_text, c.reference_text), c.reference_text or "—"]
            for c in cards
        ]
        lines.extend(_markdown_table(headers, rows))
        lines.append("")
        return lines

    def _render_metric_table(self, table: MetricTable) -> list[str]:
        lines = [f"## {table.title}", ""]
        headers = ["Metric", "Current", "Reference", "Change", "Status", "Group"]
        rows = [
            [
                row.metric.label,
                row.value_text,
                row.reference_text or "—",
                row.change_text or "—",
                row.status.replace("_", " ").title(),
                row.group_text or "—",
            ]
            for row in table.rows
        ]
        lines.extend(_markdown_table(headers, rows))
        lines.append("")
        return lines

    def _render_commentary_block(self, block: CommentaryBlock) -> list[str]:
        lines = [f"## {block.title}", ""]
        lines.append("::: {.callout-note appearance=\"simple\"}")
        lines.append("")
        for comment in block.comments:
            lines.append(f"- {comment}")
        lines.append("")
        lines.append(":::")
        lines.append("")
        return lines

    def _render_time_series_chart(self, chart: TimeSeriesChart) -> list[str]:
        return self._render_plotly_like_figure(
            title=chart.title,
            help_text=chart.help_text or chart.metric_help_text(),
            figure=chart.plotly_figure(),
            fallback_summary=chart.compact_data_summary(),
        )

    def _render_plotly_chart(self, chart: PlotlyChart) -> list[str]:
        return self._render_plotly_like_figure(
            title=chart.title,
            help_text=chart.help_text or chart.metric_help_text(),
            figure=dict(chart.figure),
            fallback_summary=chart.compact_data_summary(),
        )

    def _render_heatmap(self, heatmap: Heatmap) -> list[str]:
        figure = _heatmap_to_plotly_figure(heatmap)
        return self._render_plotly_like_figure(
            title=heatmap.title,
            help_text=heatmap.help_text or heatmap.metric_help_text(),
            figure=figure,
            fallback_summary=f"{len(heatmap.cells):,} heatmap cells.",
        )

    def _render_html_block(self, block: HtmlBlock, page_index: int) -> list[str]:
        title = block.title or f"Section {page_index}"
        lines = [f"## {title}", ""]

        if block.title == "Detailed Metric Trends":
            lines.extend(self._render_detailed_trends_block(block))
            return lines
        if block.title == "Intraday Turnover Distribution":
            lines.extend(self._render_turnover_distribution_block(block))
            return lines
        if block.title == "Displayed Liquidity":
            lines.extend(self._render_liquidity_distribution_block(block))
            return lines
        if block.title == "PTS Stats":
            lines.extend(self._render_pts_block(block))
            return lines

        tables = _extract_tables_from_html(block.body_html)
        if tables:
            for idx, table in enumerate(tables, start=1):
                if idx > 1:
                    lines.append("")
                lines.append(f"### Table {idx}")
                lines.append("")
                lines.extend(_markdown_table(table.headers or [f"Column {i+1}" for i in range(len(table.rows[0]))], table.rows))
                lines.append("")
        else:
            lines.append("_Interactive HTML-only section. Use the HTML report for the full experience._")
            lines.append("")
        return lines

    def _render_detailed_trends_block(self, block: HtmlBlock) -> list[str]:
        spec = _extract_named_json_script(block.body_html, "data-detailed-trends-spec")
        if spec is None:
            return ["_Detailed trends payload unavailable._", ""]
        payload = json.loads(spec)
        lines: list[str] = []
        for metric_name in payload.get("ordered_metrics", []):
            metric_payload = payload["metrics"].get(metric_name, {})
            labels = metric_payload.get("labels", [])
            values = metric_payload.get("values", [])
            period_flags = metric_payload.get("period_flags", [])
            colors = ["#8aa3bf" if flag == "reference" else "#2d5d93" for flag in period_flags]
            figure = {
                "data": [
                    {
                        "type": "bar",
                        "x": labels,
                        "y": values,
                        "marker": {"color": colors},
                    }
                ],
                "layout": {
                    "template": "plotly_white",
                    "autosize": True,
                    "height": 320,
                    "margin": {"l": 56, "r": 24, "t": 24, "b": 72},
                    "xaxis": {"type": "category"},
                    "yaxis": {"title": metric_payload.get("unit_text") or metric_payload.get("metric_label", metric_name)},
                    "showlegend": False,
                },
            }
            lines.extend(
                self._render_plotly_like_figure(
                    title=str(metric_payload.get("metric_label", metric_name)),
                    help_text=str(metric_payload.get("aggregation_text", "")),
                    figure=figure,
                    fallback_summary=f"{len(values):,} periods.",
                    heading_level=3,
                )
            )
        return lines

    def _render_turnover_distribution_block(self, block: HtmlBlock) -> list[str]:
        spec = _extract_named_json_script(block.body_html, "data-turnover-row-plot-spec")
        if spec is None:
            return ["_Intraday turnover payload unavailable._", ""]
        payload = json.loads(spec)
        default_row = payload.get("default_row", "TSE")
        row_payload = (payload.get("rows") or {}).get(default_row, {})
        lines: list[str] = []
        lines.extend(
            self._render_plotly_like_figure(
                title=f"Session Mix — {default_row}",
                help_text="Static export of the default selected row.",
                figure=row_payload.get("bar_figure") or {"data": [], "layout": {}},
                fallback_summary="Session mix chart.",
                heading_level=3,
            )
        )
        lines.extend(
            self._render_plotly_like_figure(
                title=str(row_payload.get("title", "Intraday Curve")),
                help_text="Static export of the default selected row.",
                figure=row_payload.get("line_figure") or {"data": [], "layout": {}},
                fallback_summary="Intraday turnover curve.",
                heading_level=3,
            )
        )
        for idx, table in enumerate(_extract_tables_from_html(block.body_html), start=1):
            lines.append(f"### Table {idx}")
            lines.append("")
            lines.extend(_markdown_table(table.headers or [f"Column {i+1}" for i in range(len(table.rows[0]))], table.rows))
            lines.append("")
        return lines

    def _render_liquidity_distribution_block(self, block: HtmlBlock) -> list[str]:
        spec = _extract_named_json_script(block.body_html, "data-liquidity-plot-spec")
        if spec is None:
            return ["_Liquidity payload unavailable._", ""]
        payload = json.loads(spec)
        default_row = payload.get("default_row", "TSE")
        default_metric = payload.get("default_metric", "")
        row_payload = ((payload.get("rows") or {}).get(default_row) or {}).get(default_metric) or {}
        lines: list[str] = []
        lines.extend(
            self._render_plotly_like_figure(
                title=str(row_payload.get("line_title", row_payload.get("title", "Intraday Liquidity Curve"))),
                help_text="Static export of the default selected metric and row.",
                figure=row_payload.get("line_figure") or {"data": [], "layout": {}},
                fallback_summary="Intraday liquidity curve.",
                heading_level=3,
            )
        )
        for idx, table in enumerate(_extract_tables_from_html(block.body_html), start=1):
            lines.append(f"### Table {idx}")
            lines.append("")
            lines.extend(_markdown_table(table.headers or [f"Column {i+1}" for i in range(len(table.rows[0]))], table.rows))
            lines.append("")
        return lines

    def _render_pts_block(self, block: HtmlBlock) -> list[str]:
        spec = _extract_named_json_script(block.body_html, "plotly-chart__spec")
        lines: list[str] = []
        if spec is not None:
            lines.extend(
                self._render_plotly_like_figure(
                    title="PTS Turnover % of TSE",
                    help_text=block.help_text or "PTS venue turnover divided by total TSE turnover over the same period.",
                    figure=json.loads(spec),
                    fallback_summary="PTS share trend.",
                    heading_level=3,
                )
            )
        for idx, table in enumerate(_extract_tables_from_html(block.body_html), start=1):
            lines.append(f"### Table {idx}")
            lines.append("")
            lines.extend(_markdown_table(table.headers or [f"Column {i+1}" for i in range(len(table.rows[0]))], table.rows))
            lines.append("")
        return lines

    def _render_plotly_like_figure(
        self,
        *,
        title: str,
        help_text: str,
        figure: dict[str, Any],
        fallback_summary: str,
        heading_level: int = 2,
    ) -> list[str]:
        asset_path = self._export_matplotlib_figure(figure, stem=_slug(title))
        return self._render_asset_figure(
            title=title,
            help_text=help_text,
            asset_path=asset_path,
            fallback_summary=fallback_summary,
            heading_level=heading_level,
        )

    def _render_asset_figure(
        self,
        *,
        title: str,
        help_text: str,
        asset_path: Path,
        fallback_summary: str,
        heading_level: int = 2,
    ) -> list[str]:
        lines = [f"{'#' * heading_level} {title}", ""]
        lines.append(f"![]({self.asset_root}/{asset_path.name}){{width=100% fig-alt=\"{_escape_attr(title)}\"}}")
        lines.append("")
        return lines

    def _export_matplotlib_figure(self, figure: dict[str, Any], *, stem: str) -> Path:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            try:
                import seaborn as sns
                sns.set_theme(style="whitegrid")
            except Exception:
                pass
        except Exception as exc:  # pragma: no cover - import guard
            raise RuntimeError(
                "QMD export requires matplotlib-based static rendering support. "
                "Install the visuals extra so matplotlib and seaborn are available in the active environment. "
                f"Underlying error: {exc!r}"
            ) from exc
        self.asset_counter += 1
        asset_path = self.asset_dir / f"{self.asset_counter:03d}_{stem}.png"
        try:
            fig = _plotly_like_matplotlib_figure(figure, plt=plt)
            fig.savefig(asset_path, dpi=180, bbox_inches="tight")
            plt.close(fig)
        except Exception as exc:
            raise RuntimeError(
                "Failed to export a QMD chart figure to PNG through matplotlib/seaborn. "
                f"Underlying error: {exc!r}"
            ) from exc
        return asset_path


def _extract_named_json_script(html: str, token: str) -> str | None:
    for match in _SCRIPT_RE.finditer(html):
        marker = match.group("class") or match.group("attr") or ""
        if token in marker:
            return unescape(match.group("body").strip())
    return None


def _extract_tables_from_html(html: str) -> list[_RenderedTable]:
    parser = _HtmlTableParser()
    parser.feed(html)
    return [table for table in parser.tables if table.rows or table.headers]


def _markdown_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    safe_headers = [_escape_pipe(cell) for cell in headers]
    lines = ["| " + " | ".join(safe_headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        padded = row + [""] * max(0, len(headers) - len(row))
        lines.append("| " + " | ".join(_escape_pipe(cell) for cell in padded[: len(headers)]) + " |")
    return lines


def _clean_html_text(html: str) -> str:
    text = unescape(_TAG_RE.sub(" ", html))
    return re.sub(r"\s+", " ", text).strip()


def _escape_pipe(value: object) -> str:
    return str(value).replace("|", "\\|")


def _slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip()).strip("-").lower()
    return slug or "figure"


def _escape_attr(text: str) -> str:
    return text.replace('"', "'")


def _heatmap_to_plotly_figure(heatmap: Heatmap) -> dict[str, Any]:
    x_labels: list[str] = []
    y_labels: list[str] = []
    values: dict[tuple[str, str], float | None] = {}
    texts: dict[tuple[str, str], str] = {}
    for cell in heatmap.cells:
        if cell.x_text not in x_labels:
            x_labels.append(cell.x_text)
        if cell.y_text not in y_labels:
            y_labels.append(cell.y_text)
        values[(cell.y_text, cell.x_text)] = cell.numeric_value()
        texts[(cell.y_text, cell.x_text)] = cell.value_text
    z = [[values.get((y, x)) for x in x_labels] for y in y_labels]
    text = [[texts.get((y, x), "") for x in x_labels] for y in y_labels]
    return {
        "data": [
            {
                "type": "heatmap",
                "x": x_labels,
                "y": y_labels,
                "z": z,
                "text": text,
                "texttemplate": "%{text}",
                "colorscale": "RdBu",
                "zmid": 0,
            }
        ],
        "layout": {
            "template": "plotly_white",
            "autosize": True,
            "height": 420,
            "margin": {"l": 96, "r": 24, "t": 24, "b": 72},
            "xaxis": {"title": heatmap.x_axis_label, "type": "category"},
            "yaxis": {"title": heatmap.y_axis_label, "type": "category"},
        },
    }


def _plotly_like_matplotlib_figure(figure: dict[str, Any], *, plt: Any) -> Any:
    layout = figure.get("layout") or {}
    traces = [trace for trace in figure.get("data", []) if isinstance(trace, dict)]
    height_px = float(layout.get("height") or 360)
    fig, ax = plt.subplots(figsize=(10, max(3.5, height_px / 100.0)))
    title = layout.get("title")
    if isinstance(title, dict):
        title = title.get("text")
    if title:
        ax.set_title(str(title))
    x_title = ((layout.get("xaxis") or {}).get("title")) if isinstance(layout.get("xaxis"), dict) else None
    if isinstance(x_title, dict):
        x_title = x_title.get("text")
    y_title = ((layout.get("yaxis") or {}).get("title")) if isinstance(layout.get("yaxis"), dict) else None
    if isinstance(y_title, dict):
        y_title = y_title.get("text")
    if x_title:
        ax.set_xlabel(str(x_title))
    if y_title:
        ax.set_ylabel(str(y_title))

    y_values = _ordered_plotly_y_values(traces)
    y_min, y_max = _plotly_value_range(y_values)

    if traces and str(traces[0].get("type", "scatter")) == "heatmap":
        _render_matplotlib_heatmap(ax, traces[0])
        fig.tight_layout()
        return fig

    if any(str(trace.get("type", "scatter")) == "bar" for trace in traces):
        _render_matplotlib_bars(ax, traces, y_min=y_min, y_max=y_max, layout=layout)
    else:
        _render_matplotlib_lines(ax, traces)

    _render_matplotlib_reference_lines(ax, layout)
    ax.set_ylim(y_min, y_max)
    if any(trace.get("name") for trace in traces):
        ax.legend(loc="best")
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


def _render_matplotlib_lines(ax: Any, traces: list[dict[str, Any]]) -> None:
    for idx, trace in enumerate(traces):
        xs = [str(x) for x in (trace.get("x", []) or [])]
        ys = [_coerce_float(y) for y in (trace.get("y", []) or [])]
        pairs = [(x, y) for x, y in zip(xs, ys, strict=False) if y is not None]
        if not pairs:
            continue
        color = _trace_color(idx, trace)
        ax.plot(
            [x for x, _ in pairs],
            [y for _, y in pairs],
            marker="o",
            linewidth=2.0,
            markersize=4.0,
            label=str(trace.get("name") or f"Series {idx + 1}"),
            color=color,
        )


def _render_matplotlib_bars(
    ax: Any,
    traces: list[dict[str, Any]],
    *,
    y_min: float,
    y_max: float,
    layout: dict[str, Any],
) -> None:
    labels = _ordered_plotly_x_labels(traces)
    if not labels:
        return
    import numpy as np
    x = np.arange(len(labels))
    bar_traces = [trace for trace in traces if str(trace.get("type", "scatter")) == "bar"]
    baseline = 0.0 if y_min <= 0.0 <= y_max else y_min
    barmode = str(layout.get("barmode") or "").lower()
    if barmode == "stack":
        bottoms = [baseline] * len(labels)
        for idx, trace in enumerate(bar_traces):
            ys_by_label = {str(k): _coerce_float(v) for k, v in zip(trace.get("x", []) or [], trace.get("y", []) or [], strict=False)}
            ys = [ys_by_label.get(label, 0.0) or 0.0 for label in labels]
            color = _trace_color(idx, trace)
            ax.bar(
                x,
                [value - baseline for value in ys],
                width=0.7,
                bottom=bottoms,
                label=str(trace.get("name") or f"Series {idx + 1}"),
                color=color,
            )
            bottoms = [bottom + (value - baseline) for bottom, value in zip(bottoms, ys, strict=False)]
    else:
        width = 0.8 / max(1, len(bar_traces))
        for idx, trace in enumerate(bar_traces):
            ys_by_label = {str(k): _coerce_float(v) for k, v in zip(trace.get("x", []) or [], trace.get("y", []) or [], strict=False)}
            ys = [ys_by_label.get(label, 0.0) or 0.0 for label in labels]
            color = _trace_color(idx, trace)
            ax.bar(
                x + (idx - (len(bar_traces) - 1) / 2) * width,
                [value - baseline for value in ys],
                width=width,
                bottom=baseline,
                label=str(trace.get("name") or f"Series {idx + 1}"),
                color=color,
            )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")


def _render_matplotlib_heatmap(ax: Any, trace: dict[str, Any]) -> None:
    z = trace.get("z") or []
    x_labels = [str(x) for x in (trace.get("x") or [])]
    y_labels = [str(y) for y in (trace.get("y") or [])]
    text = trace.get("text") or []
    im = ax.imshow(z, aspect="auto", cmap="RdBu")
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    for row_index, row in enumerate(text):
        for col_index, cell_text in enumerate(row):
            ax.text(col_index, row_index, str(cell_text), ha="center", va="center", fontsize=8)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


_SVG_SERIES_COLORS = ("#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3")


def _render_matplotlib_reference_lines(ax: Any, layout: dict[str, Any]) -> None:
    shapes = layout.get("shapes")
    if not isinstance(shapes, list):
        return
    for shape in shapes:
        if not isinstance(shape, dict):
            continue
        if str(shape.get("type") or "").lower() != "line":
            continue
        y0 = _coerce_float(shape.get("y0"))
        y1 = _coerce_float(shape.get("y1"))
        if y0 is None or y1 is None or abs(y0 - y1) > 1e-9:
            continue
        line = shape.get("line") if isinstance(shape.get("line"), dict) else {}
        color = str(line.get("color") or "#9aa7b8")
        dash = str(line.get("dash") or "dash")
        linestyle = "--" if "dash" in dash else "-"
        width = _coerce_float(line.get("width")) or 1.2
        ax.axhline(y0, color=color, linestyle=linestyle, linewidth=width, zorder=0)


def _time_series_chart_svg(chart: TimeSeriesChart) -> str:
    title_id = f"{_slug(chart.title)}-title"
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{chart.svg_view_box()}" role="img" aria-labelledby="{title_id}">',
        "<style>",
        ".axis{stroke:#d7dfeb;stroke-width:1;fill:none;}",
        ".grid{stroke:#e9eef5;stroke-width:1;fill:none;}",
        ".tick{font:12px sans-serif;fill:#42556b;}",
        ".legend{font:12px sans-serif;fill:#23384d;}",
        ".title{font:14px sans-serif;font-weight:700;fill:#1e3144;}",
        "</style>",
        f'<title id="{title_id}">{escape(chart.title)}</title>',
        '<rect x="0" y="0" width="720" height="260" fill="white"/>',
    ]
    for tick in chart.svg_y_ticks():
        lines.append(f'<line class="grid" x1="58" y1="{tick.y}" x2="696" y2="{tick.y}"/>')
        lines.append(f'<text class="tick" x="{tick.x}" y="{tick.y}" text-anchor="end" dominant-baseline="middle">{escape(tick.label)}</text>')
    lines.append('<line class="axis" x1="58" y1="200" x2="696" y2="200"/>')
    lines.append('<line class="axis" x1="58" y1="20" x2="58" y2="200"/>')
    for tick in chart.svg_x_ticks(max_ticks=8):
        lines.append(f'<text class="tick" x="{tick.x}" y="{tick.y}" text-anchor="middle">{escape(tick.label)}</text>')
    for index, series in enumerate(chart.svg_series()):
        color = _SVG_SERIES_COLORS[index % len(_SVG_SERIES_COLORS)]
        lines.append(
            f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{series.polyline_points}"/>'
        )
        for marker in series.markers:
            lines.append(
                f'<circle cx="{marker.cx}" cy="{marker.cy}" r="3.5" fill="{color}"><title>{escape(marker.title)}</title></circle>'
            )
    legend_y = 238
    legend_x = 86
    for index, label in enumerate(chart.svg_legend_labels()):
        color = _SVG_SERIES_COLORS[index % len(_SVG_SERIES_COLORS)]
        x = legend_x + index * 108
        lines.append(f'<line x1="{x}" y1="{legend_y}" x2="{x + 24}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        lines.append(f'<text class="legend" x="{x + 30}" y="{legend_y + 4}">{escape(label)}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def _heatmap_svg(heatmap: Heatmap) -> str:
    title_id = f"{_slug(heatmap.title)}-title"
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{heatmap.svg_view_box()}" role="img" aria-labelledby="{title_id}">',
        "<style>",
        ".axis{font:12px sans-serif;fill:#42556b;}",
        ".cell-label{font:11px sans-serif;fill:#13283f;text-anchor:middle;dominant-baseline:middle;}",
        ".missing{fill:#f1f4f8;stroke:#d7dfeb;stroke-width:1;}",
        "</style>",
        f'<title id="{title_id}">{escape(heatmap.title)}</title>',
    ]
    for cell in heatmap.svg_cells():
        cls = "missing" if "missing" in cell.css_class else ""
        fill = "#2d5d93"
        opacity = cell.opacity if cls == "" else "1.0"
        lines.append(
            f'<rect x="{cell.x}" y="{cell.y}" width="{cell.width}" height="{cell.height}" fill="{fill}" fill-opacity="{opacity}" class="{cls}"><title>{escape(cell.title)}</title></rect>'
        )
        lines.append(f'<text class="cell-label" x="{cell.label_x}" y="{cell.label_y}">{escape(cell.label)}</text>')
    for label in heatmap.svg_x_labels():
        lines.append(f'<text class="axis" x="{label.x}" y="{label.y}" text-anchor="middle">{escape(label.text)}</text>')
    for label in heatmap.svg_y_labels():
        lines.append(f'<text class="axis" x="{label.x}" y="{label.y}" text-anchor="end" dominant-baseline="middle">{escape(label.text)}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def _plotly_like_svg(figure: dict[str, Any]) -> str:
    width = 900.0
    height = float((((figure.get("layout") or {}).get("height")) or 360))
    left = 64.0
    right = 24.0
    top = 24.0
    bottom = 72.0
    plot_width = width - left - right
    plot_height = height - top - bottom
    traces = [trace for trace in figure.get("data", []) if isinstance(trace, dict)]
    x_labels = _ordered_plotly_x_labels(traces)
    y_values = _ordered_plotly_y_values(traces)
    y_min, y_max = _plotly_value_range(y_values)
    title_id = f"{_slug(str(((figure.get('layout') or {}).get('title')) or 'figure'))}-title"
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" role="img" aria-labelledby="{title_id}">',
        "<style>",
        ".axis{stroke:#d7dfeb;stroke-width:1;fill:none;}",
        ".grid{stroke:#e9eef5;stroke-width:1;fill:none;}",
        ".tick{font:12px sans-serif;fill:#42556b;}",
        ".legend{font:12px sans-serif;fill:#23384d;}",
        "</style>",
        f'<title id="{title_id}">{escape(str(((figure.get("layout") or {}).get("title")) or "figure"))}</title>',
        f'<rect x="0" y="0" width="{width:.0f}" height="{height:.0f}" fill="white"/>',
    ]
    tick_values = _plotly_tick_values(y_min, y_max)
    for tick_value in tick_values:
        y = _plotly_y_coord(tick_value, y_min, y_max, top, plot_height)
        lines.append(f'<line class="grid" x1="{left:.2f}" y1="{y:.2f}" x2="{left + plot_width:.2f}" y2="{y:.2f}"/>')
        lines.append(f'<text class="tick" x="{left - 8:.2f}" y="{y:.2f}" text-anchor="end" dominant-baseline="middle">{escape(_format_plotly_tick(tick_value))}</text>')
    lines.append(f'<line class="axis" x1="{left:.2f}" y1="{top + plot_height:.2f}" x2="{left + plot_width:.2f}" y2="{top + plot_height:.2f}"/>')
    lines.append(f'<line class="axis" x1="{left:.2f}" y1="{top:.2f}" x2="{left:.2f}" y2="{top + plot_height:.2f}"/>')
    x_positions = _plotly_x_positions(x_labels, left, plot_width)
    for label, x in x_positions.items():
        lines.append(f'<text class="tick" x="{x:.2f}" y="{top + plot_height + 22:.2f}" text-anchor="middle">{escape(label)}</text>')
    bar_traces = [trace for trace in traces if str(trace.get("type", "scatter")) == "bar"]
    scatter_traces = [trace for trace in traces if str(trace.get("type", "scatter")) != "bar"]
    if bar_traces:
        lines.extend(_plotly_bar_svg(bar_traces, x_positions, y_min, y_max, top, plot_height))
    if scatter_traces:
        lines.extend(_plotly_scatter_svg(scatter_traces, x_positions, y_min, y_max, top, plot_height))
    legend_y = height - 28
    legend_x = left
    for index, trace in enumerate(traces):
        label = str(trace.get("name") or f"Series {index + 1}")
        color = _trace_color(index, trace)
        x = legend_x + index * 120
        if str(trace.get("type", "scatter")) == "bar":
            lines.append(f'<rect x="{x:.2f}" y="{legend_y - 10:.2f}" width="18" height="10" fill="{color}"/>')
        else:
            lines.append(f'<line x1="{x:.2f}" y1="{legend_y - 5:.2f}" x2="{x + 24:.2f}" y2="{legend_y - 5:.2f}" stroke="{color}" stroke-width="3"/>')
            lines.append(f'<circle cx="{x + 12:.2f}" cy="{legend_y - 5:.2f}" r="3" fill="{color}"/>')
        lines.append(f'<text class="legend" x="{x + 30:.2f}" y="{legend_y - 1:.2f}">{escape(label)}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def _ordered_plotly_x_labels(traces: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for trace in traces:
        for raw in trace.get("x", []) or []:
            label = str(raw)
            if label not in seen:
                seen.add(label)
                labels.append(label)
    return labels or ["Value"]


def _ordered_plotly_y_values(traces: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for trace in traces:
        for raw in trace.get("y", []) or []:
            try:
                values.append(float(raw))
            except (TypeError, ValueError):
                continue
    return values or [0.0, 1.0]


def _plotly_value_range(values: list[float]) -> tuple[float, float]:
    value_min = min(values)
    value_max = max(values)
    if value_min == value_max:
        padding = abs(value_min) * 0.08 or 1.0
    else:
        padding = (value_max - value_min) * 0.08
    return value_min - padding, value_max + padding


def _plotly_tick_values(value_min: float, value_max: float) -> list[float]:
    if value_max == value_min:
        return [value_min]
    return [value_min + (value_max - value_min) * step / 4 for step in range(5)]


def _plotly_y_coord(value: float, value_min: float, value_max: float, top: float, plot_height: float) -> float:
    if value_max == value_min:
        return top + plot_height / 2
    scaled = (value - value_min) / (value_max - value_min)
    return top + (1 - scaled) * plot_height


def _plotly_x_positions(labels: list[str], left: float, plot_width: float) -> dict[str, float]:
    if len(labels) == 1:
        return {labels[0]: left + plot_width / 2}
    return {
        label: left + index * (plot_width / (len(labels) - 1))
        for index, label in enumerate(labels)
    }


def _plotly_bar_svg(
    traces: list[dict[str, Any]],
    x_positions: dict[str, float],
    y_min: float,
    y_max: float,
    top: float,
    plot_height: float,
) -> list[str]:
    lines: list[str] = []
    labels = list(x_positions)
    group_width = 48.0
    bar_width = max(10.0, group_width / max(1, len(traces)))
    baseline_y = _plotly_y_coord(0.0, y_min, y_max, top, plot_height)
    for trace_index, trace in enumerate(traces):
        xs = [str(x) for x in (trace.get("x", []) or [])]
        ys = trace.get("y", []) or []
        color = _trace_color(trace_index, trace)
        for point_index, (label, raw_y) in enumerate(zip(xs, ys, strict=False)):
            if label not in x_positions:
                continue
            try:
                value = float(raw_y)
            except (TypeError, ValueError):
                continue
            center_x = x_positions[label]
            x = center_x - group_width / 2 + trace_index * bar_width
            y = _plotly_y_coord(max(value, 0.0), y_min, y_max, top, plot_height)
            height = abs(baseline_y - _plotly_y_coord(value, y_min, y_max, top, plot_height))
            lines.append(
                f'<rect x="{x:.2f}" y="{min(y, baseline_y):.2f}" width="{bar_width - 2:.2f}" height="{height:.2f}" fill="{color}"><title>{escape(f"{label}: {value:.2f}")}</title></rect>'
            )
    return lines


def _plotly_scatter_svg(
    traces: list[dict[str, Any]],
    x_positions: dict[str, float],
    y_min: float,
    y_max: float,
    top: float,
    plot_height: float,
) -> list[str]:
    lines: list[str] = []
    for trace_index, trace in enumerate(traces):
        xs = [str(x) for x in (trace.get("x", []) or [])]
        ys = trace.get("y", []) or []
        color = _trace_color(trace_index, trace)
        points: list[str] = []
        markers: list[tuple[float, float, str]] = []
        for label, raw_y in zip(xs, ys, strict=False):
            if label not in x_positions:
                continue
            try:
                value = float(raw_y)
            except (TypeError, ValueError):
                continue
            x = x_positions[label]
            y = _plotly_y_coord(value, y_min, y_max, top, plot_height)
            points.append(f"{x:.2f},{y:.2f}")
            markers.append((x, y, f"{label}: {value:.2f}"))
        if points:
            lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="2.5" points="{" ".join(points)}"/>')
        for x, y, title in markers:
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.5" fill="{color}"><title>{escape(title)}</title></circle>')
    return lines


def _trace_color(index: int, trace: dict[str, Any]) -> str:
    marker = trace.get("marker")
    if isinstance(marker, dict):
        color = marker.get("color")
        if isinstance(color, str):
            return color
        if isinstance(color, list) and color:
            first = color[0]
            if isinstance(first, str):
                return first
    line = trace.get("line")
    if isinstance(line, dict):
        color = line.get("color")
        if isinstance(color, str):
            return color
    return _SVG_SERIES_COLORS[index % len(_SVG_SERIES_COLORS)]


def _format_plotly_tick(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def _summary_sentence(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return ""
    for sep in (". ", "; ", "\n"):
        if sep in cleaned:
            return cleaned.split(sep, 1)[0].rstrip(".") + "."
    return cleaned


def _card_current_text(value_text: str, reference_text: str | None) -> str:
    if reference_text is None:
        return value_text
    current_value = _parse_display_number(value_text)
    reference_value = _parse_display_number(reference_text)
    if current_value is None or reference_value is None or reference_value == 0:
        return value_text
    change_pct = ((current_value - reference_value) / reference_value) * 100.0
    return f"{value_text} ({change_pct:+.2f}%)"


def _parse_display_number(text: str) -> float | None:
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", text)
    if match is None:
        return None
    numeric = float(match.group(0).replace(",", ""))
    suffix_match = re.search(r"(?i)([kmbt])\b", text)
    if suffix_match is None:
        return numeric
    scale = {
        "k": 1e3,
        "m": 1e6,
        "b": 1e9,
        "t": 1e12,
    }[suffix_match.group(1).lower()]
    return numeric * scale
