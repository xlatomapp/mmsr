from __future__ import annotations

import json
import logging
import math
import re
import tempfile
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from mmsr.report.components import HtmlBlock, MetricCard, ReportDocument

# Suppress noisy debug/info output from image rendering libraries.
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)

_SCRIPT_RE = re.compile(
    r'<script[^>]*type="application/json"[^>]*?(?:class="(?P<class>[^"]+)"|(?P<attr>data-[^=\s>]+))[^>]*>(?P<body>.*?)</script>',
    re.DOTALL,
)
_TAG_RE = re.compile(r"<[^>]+>")
_PTS_VENUE_CARD_RE = re.compile(
    r'<section class="turnover-distribution__card pts-stats__venue-card">.*?'
    r'<div class="turnover-distribution__card-title">(?P<title>[^<]+)</div>.*?'
    r'(?P<table><table class="pts-stats__venue-table">.*?</table>)'
    r".*?</section>",
    re.DOTALL,
)
_MARKET_OVERVIEW_CARD_RE = re.compile(
    r'<article class="market-overview-card">.*?'
    r'<p class="market-overview-card__label">(?P<label>[^<]+)</p>.*?'
    r'<p class="market-overview-card__value">(?P<value>[^<]+)</p>.*?'
    r'<p class="market-overview-card__delta [^"]+">(?P<delta>[^<]+)</p>.*?'
    r"</article>",
    re.DOTALL,
)


def render_report_pdf_file(
    document: ReportDocument,
    output_path: str | Path,
) -> Path:
    resolved_output_path = Path(output_path)
    if resolved_output_path.exists() and resolved_output_path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mmsr_pdf_assets_") as tmpdir:
        renderer = _PdfRenderer(document=document, asset_dir=Path(tmpdir))
        renderer.render_to_file(resolved_output_path)
    return resolved_output_path


@dataclass(frozen=True)
class _PdfChartAsset:
    title: str
    path: Path


@dataclass(frozen=True)
class _RenderedTable:
    headers: list[str]
    rows: list[list[str]]


class _HtmlTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[_RenderedTable] = []
        self._in_table = False
        self._in_header = False
        self._in_cell = False
        self._current_cell: list[str] = []
        self._current_row: list[str] = []
        self._headers: list[str] = []
        self._rows: list[list[str]] = []

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
            self._current_row.append(_clean_html_text("".join(self._current_cell)))
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


class _PdfRenderer:
    def __init__(self, *, document: ReportDocument, asset_dir: Path) -> None:
        self.document = document
        self.asset_dir = asset_dir
        self.asset_counter = 0
        self._pdf = self._build_pdf()

    def render_to_file(self, output_path: Path) -> None:
        self._render_cover_page()
        summary_page = self._summary_page()
        if summary_page is not None:
            self._render_market_summary(summary_page)
            self._render_summary_html_blocks(summary_page.html_blocks)
        self._pdf.output(str(output_path))

    def _build_pdf(self) -> Any:
        try:
            from fpdf import FPDF
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "PDF export requires fpdf2. Install the optional PDF dependencies in the active environment. "
                f"Underlying error: {exc!r}"
            ) from exc
        pdf = FPDF(format="A4", unit="mm")
        pdf.set_auto_page_break(auto=True, margin=12)
        pdf.set_margins(12, 12, 12)
        pdf.set_title(self.document.title)
        pdf.set_author("MMSR")
        return pdf

    def _summary_page(self):
        if not self.document.pages:
            return None
        return self.document.pages[0]

    def _render_cover_page(self) -> None:
        pdf = self._pdf
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(18, 42, 66)
        pdf.multi_cell(0, 11, _pdf_text(self.document.title))
        pdf.ln(4)
        self._render_header_meta_box()

    def _render_market_summary(self, summary_page: Any) -> None:
        has_market_overview_block = any(block.title == "Market Overview" for block in summary_page.html_blocks)
        cards = _extract_market_overview_cards(summary_page.html_blocks)
        if not cards and not has_market_overview_block:
            cards = _select_market_summary_cards(summary_page.metric_cards)
        cards = _select_market_summary_cards(cards)
        if not cards:
            return
        pdf = self._pdf
        pdf.ln(4)
        self._section_heading("Market Summary")
        top_y = pdf.get_y()
        gap = 4.0
        card_width = (self._content_width() - gap) / 2
        card_height = 34.0
        rows_per_page = max(1, int((pdf.page_break_trigger - top_y) // (card_height + gap)))
        for index, card in enumerate(cards):
            page_slot = index % (rows_per_page * 2)
            if index and page_slot == 0:
                pdf.add_page()
                self._section_heading("Market Summary")
                top_y = pdf.get_y()
            row = page_slot // 2
            column = page_slot % 2
            x = pdf.l_margin + column * (card_width + gap)
            y = top_y + row * (card_height + gap)
            self._draw_metric_card(card, x=x, y=y, width=card_width, height=card_height)
        consumed_rows = min(rows_per_page, math.ceil(min(len(cards), rows_per_page * 2) / 2))
        pdf.set_y(top_y + consumed_rows * (card_height + gap) + 6)

    def _render_header_meta_box(self) -> None:
        header = dict(self.document.header_meta or {})
        items = [
            ("PERIOD", _pdf_period_text(str(header.get("period_text") or "").strip())),
            ("UNIVERSE", str(header.get("universe") or "").strip()),
            ("REFERENCE", _pdf_period_text(str(header.get("benchmark_period_text") or "").strip())),
        ]
        if not any(value for _, value in items):
            return
        pdf = self._pdf
        x = pdf.l_margin
        y = pdf.get_y()
        width = self._content_width()
        height = 28.0
        gap = 4.0
        col_width = (width - gap * 2) / 3
        pdf.set_draw_color(214, 224, 236)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(x, y, width, height, style="DF")
        for index, (label, value) in enumerate(items):
            col_x = x + index * (col_width + gap)
            if index:
                divider_x = col_x - gap / 2
                pdf.line(divider_x, y + 4, divider_x, y + height - 4)
            pdf.set_xy(col_x + 4, y + 4)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(60, 83, 109)
            pdf.cell(col_width - 8, 5, _pdf_text(label))
            pdf.set_xy(col_x + 4, y + 11)
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(18, 42, 66)
            pdf.multi_cell(col_width - 8, 6, _pdf_text(value or "n/a"))
        pdf.set_y(y + height + 6)

    def _render_summary_html_blocks(self, blocks: list[HtmlBlock]) -> None:
        for block in blocks:
            if block.title == "Market Overview":
                continue
            if block.title == "Detailed Metric Trends":
                self._render_detailed_trends_block(block)
            elif block.title == "Intraday Turnover Distribution":
                self._render_turnover_distribution_block(block)
            elif block.title == "PTS Stats":
                self._render_pts_block(block)

    def _render_detailed_trends_block(self, block: HtmlBlock) -> None:
        spec = _extract_named_json_script(block.body_html, "data-detailed-trends-spec")
        if spec is None:
            return
        payload = json.loads(spec)
        assets: list[_PdfChartAsset] = []
        for metric_name in payload.get("ordered_metrics", []):
            metric_payload = payload["metrics"].get(metric_name, {})
            labels = metric_payload.get("labels", [])
            values = metric_payload.get("values", [])
            period_flags = metric_payload.get("period_flags", [])
            colors = ["#8AA3BF" if flag == "benchmark" else "#2D5D93" for flag in period_flags]
            shapes: list[dict[str, Any]] = []
            benchmark_mean = metric_payload.get("benchmark_mean")
            target_mean = metric_payload.get("target_mean")
            benchmark_labels = [label for label, flag in zip(labels, period_flags, strict=False) if flag == "benchmark"]
            target_labels = [label for label, flag in zip(labels, period_flags, strict=False) if flag != "benchmark"]
            if isinstance(benchmark_mean, int | float):
                shapes.append(
                    {
                        "type": "line",
                        "y0": benchmark_mean,
                        "y1": benchmark_mean,
                        "x0": benchmark_labels[0] if benchmark_labels else None,
                        "x1": benchmark_labels[-1] if benchmark_labels else None,
                        "line": {"color": "#8AA0B8", "dash": "dash", "width": 1.2},
                    }
                )
            if isinstance(target_mean, int | float):
                shapes.append(
                    {
                        "type": "line",
                        "y0": target_mean,
                        "y1": target_mean,
                        "x0": target_labels[0] if target_labels else None,
                        "x1": target_labels[-1] if target_labels else None,
                        "line": {"color": "#2D5D93", "dash": "dash", "width": 1.2},
                    }
                )
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
                    "height": 300,
                    "margin": {"l": 56, "r": 24, "t": 24, "b": 72},
                    "xaxis": {"type": "category"},
                    "yaxis": {"title": metric_payload.get("unit_text") or metric_payload.get("metric_label", metric_name)},
                    "showlegend": False,
                    "shapes": shapes,
                },
            }
            assets.append(
                _PdfChartAsset(
                    title=str(metric_payload.get("metric_label", metric_name)),
                    path=self._export_chart_image(figure, stem=_slug(f"detailed-{metric_name}")),
                )
            )

        if not assets:
            return
        self._section_heading("Detailed Metric Trends")
        for asset in assets:
            if self._pdf.get_y() + 85 > self._pdf.page_break_trigger:
                self._pdf.add_page()
                self._section_heading("Detailed Metric Trends")
            self._render_full_width_chart(asset, height=72)

    def _render_turnover_distribution_block(self, block: HtmlBlock) -> None:
        spec = _extract_named_json_script(block.body_html, "data-turnover-row-plot-spec")
        if spec is None:
            return
        payload = json.loads(spec)
        default_row = payload.get("default_row", "TSE")
        row_payload = (payload.get("rows") or {}).get(default_row, {})
        bar_figure = row_payload.get("bar_figure") or {"data": [], "layout": {}}
        line_figure = row_payload.get("line_figure") or {"data": [], "layout": {}}
        bar_asset = _PdfChartAsset(
            title=f"Session Mix — {default_row}",
            path=self._export_chart_image(bar_figure, stem=_slug(f"turnover-mix-{default_row}")),
        )
        line_asset = _PdfChartAsset(
            title=str(row_payload.get("title", "Intraday Turnover Curve")),
            path=self._export_chart_image(line_figure, stem=_slug(f"turnover-line-{default_row}")),
        )
        self._pdf.add_page()
        self._section_heading("Intraday Turnover Distribution")
        self._render_full_width_chart(bar_asset, height=72)
        self._render_full_width_chart(line_asset, height=76)
        for table in _extract_tables_from_html(block.body_html)[:1]:
            self._render_table(table.headers, table.rows, title="Supporting Table")

    def _render_pts_block(self, block: HtmlBlock) -> None:
        spec = _extract_named_json_script(block.body_html, "plotly-chart__spec")
        tables = _extract_tables_from_html(block.body_html)
        self._pdf.add_page()
        self._section_heading("PTS Stats")
        if spec is not None:
            plot_asset = _PdfChartAsset(
                title="PTS Turnover % of TSE",
                path=self._export_chart_image(json.loads(spec), stem="pts-turnover-share"),
            )
            if tables:
                summary_table = tables[0]
                self._render_table(summary_table.headers, summary_table.rows, title="Venue Summary")
                tables = tables[1:]
            self._render_plot_card(plot_asset, height=82)
        venue_tables = _extract_pts_venue_tables(block.body_html)
        if venue_tables:
            self._subsection_heading("Top 5 Stocks by Venue")
            self._render_table_grid(venue_tables, columns=2)

    def _draw_metric_card(self, card: MetricCard, *, x: float, y: float, width: float, height: float) -> None:
        pdf = self._pdf
        pdf.set_xy(x, y)
        pdf.set_draw_color(214, 224, 236)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(x, y, width, height, style="DF")
        pdf.set_xy(x + 3, y + 3)
        pdf.set_font("Helvetica", size=8)
        pdf.set_text_color(77, 92, 111)
        pdf.cell(width - 6, 5, _pdf_text(card.metric.label), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x + 3)
        pdf.set_font("Helvetica", "B", 15)
        pdf.set_text_color(17, 46, 77)
        pdf.cell(width - 6, 8, _pdf_text(card.value_text), new_x="LMARGIN", new_y="NEXT")
        pdf.set_x(x + 3)
        pdf.set_font("Helvetica", size=8)
        r, g, b = _card_delta_rgb(card.reference_text)
        pdf.set_text_color(r, g, b)
        pdf.multi_cell(width - 6, 4.5, _pdf_text(_card_delta_text(card.reference_text)))

    def _render_full_width_chart(self, asset: _PdfChartAsset, *, height: float) -> None:
        pdf = self._pdf
        x = pdf.l_margin
        y = pdf.get_y()
        width = self._content_width()
        self._draw_chart_title(asset.title, x=x, y=y, width=width)
        image_y = y + 7
        pdf.image(str(asset.path), x=x, y=image_y, w=width, h=height)
        pdf.set_y(image_y + height + 6)

    def _render_plot_card(self, asset: _PdfChartAsset, *, height: float) -> None:
        """Render a chart inside a bordered card with the title on the card."""
        pdf = self._pdf
        x = pdf.l_margin
        y = pdf.get_y()
        width = self._content_width()
        header_h = 7.0
        card_height = header_h + height
        # Card background and border
        pdf.set_draw_color(214, 224, 236)
        pdf.set_fill_color(255, 255, 255)
        pdf.rect(x, y, width, card_height, style="DF")
        # Title on the card
        pdf.set_xy(x + 3, y + 1.5)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(45, 61, 77)
        pdf.cell(width - 6, 4, _pdf_text(asset.title))
        # Separator line below title
        pdf.set_draw_color(214, 224, 236)
        pdf.line(x, y + header_h, x + width, y + header_h)
        # Chart image with no padding
        image_y = y + header_h
        pdf.image(str(asset.path), x=x, y=image_y, w=width, h=height)
        pdf.set_y(image_y + height + 6)

    def _render_table_grid(self, tables: list[Any], *, columns: int) -> None:
        pdf = self._pdf
        gap = 4.0
        card_width = (self._content_width() - gap * (columns - 1)) / columns
        start_y = pdf.get_y()
        row_max_y = start_y
        for index, table in enumerate(tables):
            column = index % columns
            if column == 0 and index:
                pdf.set_y(row_max_y + 6)
                start_y = pdf.get_y()
                row_max_y = start_y
            x = pdf.l_margin + column * (card_width + gap)
            y = start_y
            title = table.rows[0][0] if table.rows and table.rows[0] else f"Venue {index + 1}"
            self._draw_card_header(title, x=x, y=y, width=card_width)
            table_bottom_y = self._draw_compact_table(
                headers=table.headers,
                rows=table.rows,
                x=x,
                y=y + 7,
                width=card_width,
                max_rows=8,
            )
            row_max_y = max(row_max_y, table_bottom_y)
        pdf.set_y(row_max_y + 6)

    def _draw_chart_title(self, title: str, *, x: float, y: float, width: float) -> None:
        pdf = self._pdf
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(45, 61, 77)
        pdf.cell(width, 5, _pdf_text(title))

    def _draw_card_header(self, text: str, *, x: float, y: float, width: float) -> None:
        pdf = self._pdf
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(45, 61, 77)
        pdf.cell(width, 5, _pdf_text(text))

    def _render_table(self, headers: list[str], rows: list[list[str]], *, title: str) -> None:
        if not headers or not rows:
            return
        pdf = self._pdf
        self._subsection_heading(title)
        col_count = len(headers)
        widths = _table_column_widths(headers, rows, total_width=self._content_width())
        row_height = 6
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(238, 243, 248)
        pdf.set_draw_color(214, 224, 236)
        for header, width in zip(headers, widths, strict=False):
            pdf.cell(width, row_height, _pdf_text(_truncate(header)), border=1, fill=True)
        pdf.ln(row_height)
        pdf.set_font("Helvetica", size=8)
        for row_index, row in enumerate(rows):
            if pdf.get_y() > pdf.page_break_trigger - 18:
                pdf.add_page()
                self._subsection_heading(title + " (cont.)")
                pdf.set_font("Helvetica", "B", 8)
                for header, width in zip(headers, widths, strict=False):
                    pdf.cell(width, row_height, _pdf_text(_truncate(header)), border=1, fill=True)
                pdf.ln(row_height)
                pdf.set_font("Helvetica", size=8)
            fill = row_index % 2 == 0
            if fill:
                pdf.set_fill_color(250, 252, 255)
            for cell, width in zip(row[:col_count], widths, strict=False):
                text = _truncate(cell)
                if col_count >= 4 and headers and headers[-1].lower().startswith("delta") and width == widths[-1]:
                    r, g, b = _delta_text_rgb(text)
                    pdf.set_text_color(r, g, b)
                else:
                    pdf.set_text_color(38, 52, 69)
                pdf.cell(width, row_height, _pdf_text(text), border=1, fill=fill)
            pdf.ln(row_height)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

    def _draw_compact_table(
        self,
        *,
        headers: list[str],
        rows: list[list[str]],
        x: float,
        y: float,
        width: float,
        max_rows: int,
    ) -> float:
        pdf = self._pdf
        col_count = len(headers)
        widths = _table_column_widths(headers, rows[:max_rows], total_width=width)
        row_height = 5.5
        pdf.set_xy(x, y)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_fill_color(238, 243, 248)
        pdf.set_draw_color(214, 224, 236)
        for header, cell_width in zip(headers, widths, strict=False):
            pdf.cell(cell_width, row_height, _pdf_text(_truncate(header, limit=20)), border=1, fill=True)
        pdf.ln(row_height)
        pdf.set_font("Helvetica", size=7.5)
        for row in rows[:max_rows]:
            pdf.set_x(x)
            for index, (cell, cell_width) in enumerate(zip(row[:col_count], widths, strict=False)):
                text = _truncate(cell, limit=22 if index == 0 else 18)
                pdf.set_text_color(*_delta_text_rgb(text) if index == col_count - 1 and any(ch in text for ch in "+-%") else (38, 52, 69))
                pdf.cell(cell_width, row_height, _pdf_text(text), border=1)
            pdf.ln(row_height)
        pdf.set_text_color(0, 0, 0)
        return pdf.get_y()

    def _export_chart_image(self, figure: dict[str, Any], *, stem: str) -> Path:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            try:
                import seaborn as sns
                sns.set_theme(style="whitegrid")
            except Exception:
                pass
        except Exception as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "PDF export requires matplotlib/seaborn for chart rendering. "
                "Install the optional PDF dependencies in the active environment. "
                f"Underlying error: {exc!r}"
            ) from exc
        self.asset_counter += 1
        asset_path = self.asset_dir / f"{self.asset_counter:03d}_{stem}.png"
        fig = _plotly_to_matplotlib_figure(figure, plt=plt)
        try:
            fig.savefig(asset_path, dpi=180, bbox_inches="tight")
        finally:
            plt.close(fig)
        return asset_path

    def _section_heading(self, text: str) -> None:
        pdf = self._pdf
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(19, 43, 67)
        pdf.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(214, 224, 236)
        y = pdf.get_y()
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(4)

    def _subsection_heading(self, text: str) -> None:
        pdf = self._pdf
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(45, 61, 77)
        pdf.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    def _content_width(self) -> float:
        return self._pdf.w - self._pdf.l_margin - self._pdf.r_margin


def _table_column_widths(headers: list[str], rows: list[list[str]], *, total_width: float) -> list[float]:
    sizes = [max(len(str(header)), 10) for header in headers]
    for row in rows[:12]:
        for index, cell in enumerate(row[: len(headers)]):
            sizes[index] = max(sizes[index], min(len(str(cell)), 28))
    total = sum(sizes) or 1
    widths = [total_width * size / total for size in sizes]
    minimum = 18.0
    widths = [max(width, minimum) for width in widths]
    scale = total_width / sum(widths)
    return [width * scale for width in widths]


def _truncate(value: object, *, limit: int = 28) -> str:
    text = str(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _status_rgb(status: str) -> tuple[int, int, int]:
    normalized = status.lower()
    if normalized == "alert":
        return (180, 43, 43)
    if normalized in {"watch", "comparison_only"}:
        return (177, 96, 23)
    return (27, 140, 74)


def _delta_text_rgb(text: str) -> tuple[int, int, int]:
    normalized = _normalize_delta_text(text)
    if normalized.startswith("+"):
        return (27, 140, 74)
    if normalized.startswith("-"):
        return (180, 43, 43)
    return (38, 52, 69)


def _card_delta_text(reference_text: str | None) -> str:
    if not reference_text:
        return "n/a"
    match = re.search(r"\(([^()]*)\)\s*$", reference_text)
    if match is None:
        return _normalize_delta_text(reference_text)
    return _normalize_delta_text(match.group(1).strip()) or "n/a"


def _card_delta_rgb(reference_text: str | None) -> tuple[int, int, int]:
    return _delta_text_rgb(_card_delta_text(reference_text))


def _normalize_delta_text(text: str) -> str:
    normalized = str(text).strip()
    normalized = normalized.replace("↑", "+").replace("↓", "-")
    normalized = normalized.replace("↗", "+").replace("↘", "-")
    normalized = re.sub(r"^\?\s*", "", normalized)
    return normalized


def _select_market_summary_cards(cards: list[MetricCard]) -> list[MetricCard]:
    preferred_order = (
        "turnover",
        "quoted_spread_bps",
        "top_of_book_depth",
        "parkinson_volatility_bps",
        "realized_volatility_bps",
    )
    by_name = {card.metric.name: card for card in cards}
    selected: list[MetricCard] = []
    for name in preferred_order:
        card = by_name.get(name)
        if card is not None and card.metric.name not in {"trade_count", "volume"}:
            selected.append(card)
    if selected:
        return selected[:4]
    return [card for card in cards if card.metric.name not in {"trade_count", "volume"}][:4]


def _extract_market_overview_cards(blocks: list[HtmlBlock]) -> list[MetricCard]:
    cards: list[MetricCard] = []
    for block in blocks:
        if block.title != "Market Overview":
            continue
        spec = _extract_named_json_script(block.body_html, "data-market-overview-spec")
        if spec is not None:
            payload = json.loads(spec)
            for item in payload.get("cards", []):
                if not isinstance(item, dict):
                    continue
                label = str(item.get("label") or "")
                value = str(item.get("value_text") or "")
                delta = str(item.get("delta_text") or "")
                metric = _metric_definition_for_market_overview_label(label)
                if metric is None:
                    continue
                cards.append(
                    MetricCard(
                        metric=metric,
                        value_text=value,
                        reference_text=delta,
                        status=_delta_status_from_text(delta),
                    )
                )
            return cards
        for match in _MARKET_OVERVIEW_CARD_RE.finditer(block.body_html):
            label = _clean_html_text(match.group("label"))
            value = _clean_html_text(match.group("value"))
            delta = _clean_html_text(match.group("delta"))
            metric = _metric_definition_for_market_overview_label(label)
            if metric is None:
                continue
            cards.append(
                MetricCard(
                    metric=metric,
                    value_text=value,
                    reference_text=delta,
                    status=_delta_status_from_text(delta),
                )
            )
        break
    return cards


def _metric_definition_for_market_overview_label(label: str):
    normalized = label.strip().casefold()
    mappings = {
        "traded value": ("turnover", "Daily Turnover", "JPY"),
        "daily turnover": ("turnover", "Daily Turnover", "JPY"),
        "quoted spread": ("quoted_spread_bps", "Quoted Spread", "bps"),
        "top of book depth": ("top_of_book_depth", "Top of book Depth", "lots"),
        "top-of-book depth": ("top_of_book_depth", "Top of book Depth", "lots"),
        "volatility": ("parkinson_volatility_bps", "Volatility", "bps"),
    }
    metric_info = mappings.get(normalized)
    if metric_info is None:
        return None
    from mmsr.metrics.base import MetricDefinition

    name, display_label, unit = metric_info
    return MetricDefinition(
        name=name,
        label=display_label,
        category="summary",
        description="PDF summary card extracted from page-1 market overview.",
        formula="",
        interpretation="",
        unit=unit,
        higher_is_better=None,
        default_aggregation="page_1_market_overview",
        supports_intraday=False,
        supports_symbol_level=False,
        required_tables=[],
        required_columns=[],
    )


def _delta_status_from_text(text: str) -> str:
    stripped = text.strip().lower()
    if stripped.startswith("-"):
        return "alert"
    if stripped.startswith("+"):
        return "normal"
    return "comparison_only"


def _pdf_period_text(text: str) -> str:
    if not text or len(text) <= 26 or " (" not in text:
        return text
    head, tail = text.rsplit(" (", 1)
    return f"{head}\n({tail}"


_PLOTLY_COLORS: tuple[str, ...] = ("#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3")


def _plotly_to_matplotlib_figure(figure: dict[str, Any], *, plt: Any) -> Any:
    layout = figure.get("layout") if isinstance(figure.get("layout"), dict) else {}
    traces = [trace for trace in figure.get("data", []) if isinstance(trace, dict)]
    height_px = float(layout.get("height") or 360)
    fig, ax = plt.subplots(figsize=(10.4, max(3.6, height_px / 100.0)))
    ax.set_facecolor("white")
    fig.patch.set_facecolor("white")

    title_text = _plotly_title_text(layout.get("title"))
    if title_text:
        ax.set_title(title_text, loc="left", fontsize=11, fontweight="bold", color="#23384D", pad=8)

    xaxis = layout.get("xaxis") if isinstance(layout.get("xaxis"), dict) else {}
    yaxis = layout.get("yaxis") if isinstance(layout.get("yaxis"), dict) else {}
    x_title = _plotly_title_text(xaxis.get("title"))
    y_title = _plotly_title_text(yaxis.get("title"))
    if x_title:
        ax.set_xlabel(x_title, fontsize=9, color="#42556B")
    if y_title:
        ax.set_ylabel(y_title, fontsize=9, color="#42556B")

    if traces and str(traces[0].get("type", "scatter")).lower() == "heatmap":
        _render_pdf_heatmap(ax, traces[0])
        fig.tight_layout()
        return fig

    y_values = _plotly_numeric_values(traces)
    y_min, y_max = _plotly_axis_range(y_values)
    if any(str(trace.get("type", "scatter")).lower() == "bar" for trace in traces):
        _render_pdf_bars(ax, traces, layout=layout, y_min=y_min, y_max=y_max)
    else:
        _render_pdf_lines(ax, traces)

    x_labels = _plotly_category_labels(traces)
    _render_pdf_shapes(ax, layout, y_min=y_min, y_max=y_max, x_labels=x_labels)
    tick_suffix = str(yaxis.get("ticksuffix") or "")
    if tick_suffix:
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: f"{value:.0f}{tick_suffix}" if abs(value) >= 100 else f"{value:.2f}{tick_suffix}"))

    tick_angle = _coerce_float(xaxis.get("tickangle"))
    rotation = 45 if tick_angle is None else tick_angle
    for label in ax.get_xticklabels():
        label.set_rotation(rotation)
        label.set_ha("right" if rotation else "center")

    ax.set_ylim(y_min, y_max)
    ax.grid(axis="y", color="#E6EDF5", linewidth=0.8)
    ax.grid(axis="x", visible=False)
    for spine_name in ("top", "right"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["left"].set_color("#D7DFEB")
    ax.spines["bottom"].set_color("#D7DFEB")
    ax.tick_params(axis="both", colors="#42556B", labelsize=8)

    if any(str(trace.get("name") or "").strip() for trace in traces):
        legend = layout.get("legend") if isinstance(layout.get("legend"), dict) else {}
        orientation = str(legend.get("orientation") or "").lower()
        if orientation == "h":
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=max(1, min(4, len(traces))), frameon=False, fontsize=8)
        else:
            ax.legend(loc="best", frameon=False, fontsize=8)

    fig.tight_layout()
    return fig


def _render_pdf_lines(ax: Any, traces: list[dict[str, Any]]) -> None:
    for index, trace in enumerate(traces):
        x_values = [str(value) for value in (trace.get("x") or [])]
        y_values = [_coerce_float(value) for value in (trace.get("y") or [])]
        pairs = [(x, y) for x, y in zip(x_values, y_values, strict=False) if y is not None]
        if not pairs:
            continue
        mode = str(trace.get("mode") or "lines")
        draw_line = "lines" in mode
        draw_markers = "markers" in mode or not draw_line
        color = _trace_color(index, trace)
        ax.plot(
            [x for x, _ in pairs],
            [y for _, y in pairs],
            linewidth=2.0 if draw_line else 0.0,
            marker="o" if draw_markers else None,
            markersize=3.8,
            color=color,
            label=str(trace.get("name") or f"Series {index + 1}"),
        )


def _render_pdf_bars(
    ax: Any,
    traces: list[dict[str, Any]],
    *,
    layout: dict[str, Any],
    y_min: float,
    y_max: float,
) -> None:
    import numpy as np

    labels = _plotly_category_labels(traces)
    if not labels:
        return
    x_positions = np.arange(len(labels))
    bar_traces = [trace for trace in traces if str(trace.get("type", "scatter")).lower() == "bar"]
    barmode = str(layout.get("barmode") or "").lower()
    baseline = 0.0 if y_min <= 0.0 <= y_max else y_min
    if barmode == "stack":
        bottoms = [baseline] * len(labels)
        for index, trace in enumerate(bar_traces):
            values = _series_values_by_label(trace, labels)
            ax.bar(
                x_positions,
                [value - baseline for value in values],
                width=0.68,
                bottom=bottoms,
                color=_trace_color(index, trace),
                label=str(trace.get("name") or f"Series {index + 1}"),
            )
            bottoms = [bottom + (value - baseline) for bottom, value in zip(bottoms, values, strict=False)]
    else:
        width = 0.78 / max(1, len(bar_traces))
        for index, trace in enumerate(bar_traces):
            values = _series_values_by_label(trace, labels)
            ax.bar(
                x_positions + (index - (len(bar_traces) - 1) / 2) * width,
                [value - baseline for value in values],
                width=width,
                bottom=baseline,
                color=_trace_color(index, trace),
                label=str(trace.get("name") or f"Series {index + 1}"),
            )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)


def _render_pdf_heatmap(ax: Any, trace: dict[str, Any]) -> None:
    z_values = trace.get("z") or []
    x_labels = [str(value) for value in (trace.get("x") or [])]
    y_labels = [str(value) for value in (trace.get("y") or [])]
    text_values = trace.get("text") or []
    image = ax.imshow(z_values, aspect="auto", cmap="RdBu")
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    for row_index, row in enumerate(text_values):
        for col_index, text in enumerate(row):
            ax.text(col_index, row_index, str(text), ha="center", va="center", fontsize=7, color="#13283F")
    ax.figure.colorbar(image, ax=ax, fraction=0.045, pad=0.03)


def _render_pdf_shapes(ax: Any, layout: dict[str, Any], *, y_min: float, y_max: float, x_labels: list[str]) -> None:
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
        if y0 < y_min or y0 > y_max:
            continue
        line = shape.get("line") if isinstance(shape.get("line"), dict) else {}
        color = str(line.get("color") or "#9AA7B8")
        dash = str(line.get("dash") or "")
        linestyle = "--" if "dash" in dash else "-"
        width = _coerce_float(line.get("width")) or 1.1
        x0 = shape.get("x0")
        x1 = shape.get("x1")
        if x_labels and x0 is not None and x1 is not None:
            try:
                start_index = x_labels.index(str(x0))
                end_index = x_labels.index(str(x1))
            except ValueError:
                start_index = 0
                end_index = len(x_labels) - 1
            xmin = start_index - 0.45
            xmax = end_index + 0.45
            ax.hlines(y0, xmin=xmin, xmax=xmax, color=color, linestyle=linestyle, linewidth=width, zorder=0)
        else:
            ax.axhline(y0, color=color, linestyle=linestyle, linewidth=width, zorder=0)


def _plotly_title_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text") or "")
    if value is None:
        return ""
    return str(value)


def _plotly_category_labels(traces: list[dict[str, Any]]) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for trace in traces:
        for raw in trace.get("x", []) or []:
            text = str(raw)
            if text not in seen:
                seen.add(text)
                labels.append(text)
    return labels


def _plotly_numeric_values(traces: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for trace in traces:
        for raw in trace.get("y", []) or []:
            numeric = _coerce_float(raw)
            if numeric is not None and math.isfinite(numeric):
                values.append(numeric)
    return values or [0.0, 1.0]


def _plotly_axis_range(values: list[float]) -> tuple[float, float]:
    value_min = min(values)
    value_max = max(values)
    if value_min == value_max:
        padding = abs(value_min) * 0.08 or 1.0
    else:
        padding = (value_max - value_min) * 0.08
    return value_min - padding, value_max + padding


def _series_values_by_label(trace: dict[str, Any], labels: list[str]) -> list[float]:
    mapping = {
        str(x): _coerce_float(y) or 0.0
        for x, y in zip(trace.get("x", []) or [], trace.get("y", []) or [], strict=False)
    }
    return [mapping.get(label, 0.0) for label in labels]


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
    return _PLOTLY_COLORS[index % len(_PLOTLY_COLORS)]


def _coerce_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pdf_text(value: object) -> str:
    text = str(value)
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2026": "...",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text.encode("latin-1", "replace").decode("latin-1")


def _extract_named_json_script(html: str, token: str) -> str | None:
    for match in _SCRIPT_RE.finditer(html):
        marker = match.group("class") or match.group("attr") or ""
        if token in marker:
            return unescape(match.group("body").strip())
    return None


def _extract_tables_from_html(html: str) -> list[_RenderedTable]:
    parser = _HtmlTableParser()
    parser.feed(html)
    return [table for table in parser.tables if table.headers or table.rows]


def _extract_pts_venue_tables(html: str) -> list[_RenderedTable]:
    tables: list[_RenderedTable] = []
    for match in _PTS_VENUE_CARD_RE.finditer(html):
        title = _clean_html_text(match.group("title"))
        parsed = _extract_tables_from_html(match.group("table"))
        if not parsed:
            continue
        table = parsed[0]
        rows = [[title, *row] for row in table.rows]
        tables.append(_RenderedTable(headers=["Venue", *table.headers], rows=rows))
    return tables


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


def _slug(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.strip()).strip("-").lower()
    return slug or "figure"


def _clean_html_text(html: str) -> str:
    text = unescape(_TAG_RE.sub(" ", html))
    return re.sub(r"\s+", " ", text).strip()
