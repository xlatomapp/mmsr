"""Report component models."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from math import isfinite

from mmsr.metrics.base import MetricDefinition


@dataclass(frozen=True)
class MetricCard:
    """A metric card with help text."""

    metric: MetricDefinition
    value_text: str
    reference_text: str | None = None
    status: str = "normal"

    def help_text(self) -> str:
        """Return the help text for this card's metric."""
        return self.metric.help_text()


@dataclass(frozen=True)
class MetricTableRow:
    """One metric row in a deterministic report table."""

    metric: MetricDefinition
    value_text: str
    reference_text: str | None = None
    change_text: str | None = None
    status: str = "normal"
    group_text: str | None = None

    def help_text(self) -> str:
        """Return the help text for this row's metric."""
        return self.metric.help_text()


@dataclass(frozen=True)
class MetricTable:
    """A metric table whose rows expose metric help text."""

    title: str
    rows: list[MetricTableRow]
    help_text: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")


@dataclass(frozen=True)
class TimeSeriesSvgMarker:
    """One marker in a deterministic inline SVG time-series plot."""

    cx: str
    cy: str
    title: str


@dataclass(frozen=True)
class TimeSeriesSvgSeries:
    """One rendered series in a deterministic inline SVG time-series plot."""

    label: str
    css_class: str
    polyline_points: str
    markers: tuple[TimeSeriesSvgMarker, ...]


@dataclass(frozen=True)
class TimeSeriesSvgTick:
    """One axis tick in a deterministic inline SVG time-series plot."""

    x: str
    y: str
    label: str


@dataclass(frozen=True)
class TimeSeriesChartPoint:
    """One deterministic point rendered by a time-series chart."""

    x_text: str
    value_text: str
    date_text: str | None = None
    time_bucket_text: str | None = None
    series_text: str | None = None
    metadata_text: str | None = None
    value: float | int | None = None

    def __post_init__(self) -> None:
        if not self.x_text.strip():
            raise ValueError("x_text must not be empty")
        if not self.value_text.strip():
            raise ValueError("value_text must not be empty")
        numeric = self.numeric_value()
        if numeric is not None and not isfinite(numeric):
            raise ValueError("value must be finite when supplied")

    def numeric_value(self) -> float | None:
        """Return the plottable numeric value for this point when available."""

        if self.value is not None:
            return float(self.value)

        # Backward-compatible fallback for hand-built report points. Builders
        # should pass ``value`` explicitly so rendering never depends on parsing
        # display text.
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", self.value_text)
        if match is None:
            return None

        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None


@dataclass(frozen=True)
class TimeSeriesChart:
    """A deterministic time-series chart with metric help text."""

    title: str
    metric: MetricDefinition
    points: list[TimeSeriesChartPoint]
    x_axis_label: str = "Report period / bucket"
    y_axis_label: str | None = None
    help_text: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.x_axis_label.strip():
            raise ValueError("x_axis_label must not be empty")
        if self.y_axis_label is not None and not self.y_axis_label.strip():
            raise ValueError("y_axis_label must not be empty when supplied")
        if self.help_text is not None and not self.help_text.strip():
            raise ValueError("help_text must not be empty when supplied")

    def metric_help_text(self) -> str:
        """Return the help text for this chart's metric."""

        return self.metric.help_text()

    def resolved_y_axis_label(self) -> str:
        """Return an explicit y-axis label or a deterministic metric fallback."""

        return self.y_axis_label or self.metric.unit or self.metric.label

    def has_svg_plot(self) -> bool:
        """Return whether the chart has at least one plottable numeric value."""

        return bool(self._numeric_points())

    def svg_view_box(self) -> str:
        """Return the fixed SVG view box used by deterministic chart rendering."""

        return "0 0 720 260"

    def svg_series(self) -> tuple[TimeSeriesSvgSeries, ...]:
        """Return deterministic SVG series while preserving report order."""

        numeric_points = self._numeric_points()
        if not numeric_points:
            return ()

        value_min, value_max = self._svg_value_range()
        x_positions = self._svg_x_positions()
        series_names = _ordered_unique(
            point.series_text or self.metric.label for _, point, _ in numeric_points
        )

        rendered_series: list[TimeSeriesSvgSeries] = []
        for series_index, series_name in enumerate(series_names):
            rendered_markers: list[TimeSeriesSvgMarker] = []
            coordinate_parts: list[str] = []
            for _, point, value in numeric_points:
                if (point.series_text or self.metric.label) != series_name:
                    continue
                x = x_positions[point.x_text]
                y = _svg_y_coordinate(value, value_min, value_max)
                coordinate_parts.append(f"{_svg_number(x)},{_svg_number(y)}")
                rendered_markers.append(
                    TimeSeriesSvgMarker(
                        cx=_svg_number(x),
                        cy=_svg_number(y),
                        title=(
                            f"{series_name}: {point.x_text} = {point.value_text}"
                        ),
                    )
                )
            rendered_series.append(
                TimeSeriesSvgSeries(
                    label=series_name,
                    css_class=f"time-series-chart__series--{series_index % 6}",
                    polyline_points=" ".join(coordinate_parts),
                    markers=tuple(rendered_markers),
                )
            )
        return tuple(rendered_series)

    def svg_x_ticks(self, *, max_ticks: int = 6) -> tuple[TimeSeriesSvgTick, ...]:
        """Return sampled x-axis ticks for deterministic SVG rendering."""

        x_positions = self._svg_x_positions()
        labels = tuple(x_positions)
        if not labels:
            return ()
        indices = _sample_axis_indices(len(labels), max_ticks)
        return tuple(
            TimeSeriesSvgTick(
                x=_svg_number(x_positions[labels[index]]),
                y=_svg_number(_SVG_HEIGHT - _SVG_BOTTOM_PADDING + 18),
                label=labels[index],
            )
            for index in indices
        )

    def svg_y_ticks(self) -> tuple[TimeSeriesSvgTick, ...]:
        """Return min/mid/max y-axis ticks for deterministic SVG rendering."""

        if not self.has_svg_plot():
            return ()
        value_min, value_max = self._svg_value_range()
        tick_values = (
            value_min,
            (value_min + value_max) / 2,
            value_max,
        )
        return tuple(
            TimeSeriesSvgTick(
                x=_svg_number(_SVG_LEFT_PADDING - 8),
                y=_svg_number(_svg_y_coordinate(value, value_min, value_max)),
                label=_format_svg_tick_label(value),
            )
            for value in tick_values
        )

    def svg_legend_labels(self) -> tuple[str, ...]:
        """Return legend labels for plottable series in display order."""

        return tuple(series.label for series in self.svg_series())

    def _numeric_points(
        self,
    ) -> tuple[tuple[int, TimeSeriesChartPoint, float], ...]:
        numeric_points: list[tuple[int, TimeSeriesChartPoint, float]] = []
        for index, point in enumerate(self.points):
            value = point.numeric_value()
            if value is None:
                continue
            numeric_points.append((index, point, value))
        return tuple(numeric_points)

    def _svg_value_range(self) -> tuple[float, float]:
        values = [value for _, _, value in self._numeric_points()]
        if not values:
            return (0.0, 1.0)

        value_min = min(values)
        value_max = max(values)
        if value_min == value_max:
            padding = abs(value_min) * 0.1 or 1.0
        else:
            padding = (value_max - value_min) * 0.05

        return (value_min - padding, value_max + padding)

    def _svg_x_positions(self) -> dict[str, float]:
        labels = _ordered_unique(point.x_text for point in self.points)
        if not labels:
            return {}

        if len(labels) == 1:
            return {
                labels[0]: _SVG_LEFT_PADDING + _SVG_PLOT_WIDTH / 2,
            }

        return {
            label: _SVG_LEFT_PADDING
            + (index / (len(labels) - 1)) * _SVG_PLOT_WIDTH
            for index, label in enumerate(labels)
        }


_SVG_WIDTH = 720.0
_SVG_HEIGHT = 260.0
_SVG_LEFT_PADDING = 58.0
_SVG_RIGHT_PADDING = 24.0
_SVG_TOP_PADDING = 20.0
_SVG_BOTTOM_PADDING = 60.0
_SVG_PLOT_WIDTH = _SVG_WIDTH - _SVG_LEFT_PADDING - _SVG_RIGHT_PADDING
_SVG_PLOT_HEIGHT = _SVG_HEIGHT - _SVG_TOP_PADDING - _SVG_BOTTOM_PADDING


def _svg_y_coordinate(value: float, value_min: float, value_max: float) -> float:
    if value_max == value_min:
        return _SVG_TOP_PADDING + _SVG_PLOT_HEIGHT / 2
    scaled = (value - value_min) / (value_max - value_min)
    return _SVG_TOP_PADDING + (1 - scaled) * _SVG_PLOT_HEIGHT


def _svg_number(value: float) -> str:
    return f"{value:.2f}"


def _format_svg_tick_label(value: float) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.4g}"


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


def _sample_axis_indices(item_count: int, max_ticks: int) -> tuple[int, ...]:
    if item_count <= 0:
        return ()
    if max_ticks <= 1:
        return (0,)
    if item_count <= max_ticks:
        return tuple(range(item_count))

    sampled = {
        round(index * (item_count - 1) / (max_ticks - 1))
        for index in range(max_ticks)
    }
    return tuple(sorted(sampled))


@dataclass(frozen=True)
class HeatmapSvgCell:
    """One rendered cell in a deterministic inline SVG heatmap."""

    x: str
    y: str
    width: str
    height: str
    label_x: str
    label_y: str
    opacity: str
    title: str
    label: str
    css_class: str


@dataclass(frozen=True)
class HeatmapSvgLabel:
    """One axis label in a deterministic inline SVG heatmap."""

    x: str
    y: str
    text: str
    css_class: str


@dataclass(frozen=True)
class HeatmapCell:
    """One deterministic cell rendered by a heatmap visual."""

    x_text: str
    y_text: str
    value_text: str
    date_text: str | None = None
    time_bucket_text: str | None = None
    group_text: str | None = None
    metadata_text: str | None = None
    value: float | int | None = None

    def __post_init__(self) -> None:
        if not self.x_text.strip():
            raise ValueError("x_text must not be empty")
        if not self.y_text.strip():
            raise ValueError("y_text must not be empty")
        if not self.value_text.strip():
            raise ValueError("value_text must not be empty")
        numeric = self.numeric_value()
        if numeric is not None and not isfinite(numeric):
            raise ValueError("value must be finite when supplied")

    def numeric_value(self) -> float | None:
        """Return the plottable numeric value for this cell when available."""

        if self.value is not None:
            return float(self.value)

        # Backward-compatible fallback for hand-built heatmap cells. Builders
        # should pass ``value`` explicitly so rendering never depends on parsing
        # display text.
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", self.value_text)
        if match is None:
            return None

        try:
            return float(match.group(0).replace(",", ""))
        except ValueError:
            return None


@dataclass(frozen=True)
class Heatmap:
    """A deterministic heatmap visual with metric help text."""

    title: str
    metric: MetricDefinition
    cells: list[HeatmapCell]
    x_axis_label: str = "Intraday bucket"
    y_axis_label: str = "Group"
    help_text: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.x_axis_label.strip():
            raise ValueError("x_axis_label must not be empty")
        if not self.y_axis_label.strip():
            raise ValueError("y_axis_label must not be empty")
        if self.help_text is not None and not self.help_text.strip():
            raise ValueError("help_text must not be empty when supplied")

    def metric_help_text(self) -> str:
        """Return the help text for this heatmap's metric."""

        return self.metric.help_text()

    def value_label(self) -> str:
        """Return the deterministic heatmap value label."""

        return self.metric.unit or self.metric.label

    def has_svg_matrix(self) -> bool:
        """Return whether the heatmap has at least one numeric cell value."""

        return bool(self._numeric_cells())

    def svg_view_box(self) -> str:
        """Return the dynamic SVG view box for deterministic heatmap rendering."""

        return (
            "0 0 "
            f"{_svg_number(self._heatmap_svg_width())} "
            f"{_svg_number(self._heatmap_svg_height())}"
        )

    def svg_cells(self) -> tuple[HeatmapSvgCell, ...]:
        """Return deterministic SVG heatmap cells in report order."""

        x_positions = self._heatmap_x_positions()
        y_positions = self._heatmap_y_positions()
        if not x_positions or not y_positions:
            return ()

        value_min, value_max = self._heatmap_value_range()
        rendered_cells: list[HeatmapSvgCell] = []
        for cell in self.cells:
            x = x_positions[cell.x_text]
            y = y_positions[cell.y_text]
            value = cell.numeric_value()
            is_missing = value is None
            css_class = "heatmap__cell"
            if is_missing:
                opacity = "1.00"
                css_class = "heatmap__cell heatmap__cell--missing"
            else:
                opacity = _svg_number(
                    _heatmap_cell_opacity(value, value_min, value_max)
                )
            rendered_cells.append(
                HeatmapSvgCell(
                    x=_svg_number(x),
                    y=_svg_number(y),
                    width=_svg_number(_HEATMAP_CELL_WIDTH),
                    height=_svg_number(_HEATMAP_CELL_HEIGHT),
                    label_x=_svg_number(x + _HEATMAP_CELL_WIDTH / 2),
                    label_y=_svg_number(y + _HEATMAP_CELL_HEIGHT / 2 + 4),
                    opacity=opacity,
                    title=(
                        f"{cell.y_text}, {cell.x_text}: {cell.value_text}"
                    ),
                    label=_heatmap_cell_label(cell.value_text),
                    css_class=css_class,
                )
            )
        return tuple(rendered_cells)

    def svg_x_labels(self) -> tuple[HeatmapSvgLabel, ...]:
        """Return deterministic x-axis labels for SVG heatmap rendering."""

        return tuple(
            HeatmapSvgLabel(
                x=_svg_number(x + _HEATMAP_CELL_WIDTH / 2),
                y=_svg_number(_HEATMAP_TOP_PADDING - 12),
                text=label,
                css_class="heatmap__axis-label heatmap__axis-label--x",
            )
            for label, x in self._heatmap_x_positions().items()
        )

    def svg_y_labels(self) -> tuple[HeatmapSvgLabel, ...]:
        """Return deterministic y-axis labels for SVG heatmap rendering."""

        return tuple(
            HeatmapSvgLabel(
                x=_svg_number(_HEATMAP_LEFT_PADDING - 8),
                y=_svg_number(y + _HEATMAP_CELL_HEIGHT / 2 + 4),
                text=label,
                css_class="heatmap__axis-label heatmap__axis-label--y",
            )
            for label, y in self._heatmap_y_positions().items()
        )

    def _numeric_cells(self) -> tuple[tuple[int, HeatmapCell, float], ...]:
        numeric_cells: list[tuple[int, HeatmapCell, float]] = []
        for index, cell in enumerate(self.cells):
            value = cell.numeric_value()
            if value is None:
                continue
            numeric_cells.append((index, cell, value))
        return tuple(numeric_cells)

    def _heatmap_value_range(self) -> tuple[float, float]:
        values = [value for _, _, value in self._numeric_cells()]
        if not values:
            return (0.0, 1.0)
        return (min(values), max(values))

    def _heatmap_x_positions(self) -> dict[str, float]:
        return {
            label: _HEATMAP_LEFT_PADDING + index * _HEATMAP_CELL_WIDTH
            for index, label in enumerate(
                _ordered_unique(cell.x_text for cell in self.cells)
            )
        }

    def _heatmap_y_positions(self) -> dict[str, float]:
        return {
            label: _HEATMAP_TOP_PADDING + index * _HEATMAP_CELL_HEIGHT
            for index, label in enumerate(
                _ordered_unique(cell.y_text for cell in self.cells)
            )
        }

    def _heatmap_svg_width(self) -> float:
        x_count = len(_ordered_unique(cell.x_text for cell in self.cells))
        return (
            _HEATMAP_LEFT_PADDING
            + max(x_count, 1) * _HEATMAP_CELL_WIDTH
            + _HEATMAP_RIGHT_PADDING
        )

    def _heatmap_svg_height(self) -> float:
        y_count = len(_ordered_unique(cell.y_text for cell in self.cells))
        return (
            _HEATMAP_TOP_PADDING
            + max(y_count, 1) * _HEATMAP_CELL_HEIGHT
            + _HEATMAP_BOTTOM_PADDING
        )


_HEATMAP_LEFT_PADDING = 118.0
_HEATMAP_TOP_PADDING = 34.0
_HEATMAP_RIGHT_PADDING = 24.0
_HEATMAP_BOTTOM_PADDING = 44.0
_HEATMAP_CELL_WIDTH = 96.0
_HEATMAP_CELL_HEIGHT = 34.0


def _heatmap_cell_opacity(
    value: float,
    value_min: float,
    value_max: float,
) -> float:
    if value_max == value_min:
        return 0.65
    scaled = (value - value_min) / (value_max - value_min)
    return 0.18 + scaled * 0.77


def _heatmap_cell_label(value_text: str) -> str:
    match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?", value_text)
    if match is None:
        return "—"
    parsed = float(match.group(0).replace(",", ""))
    return _format_svg_tick_label(parsed)



@dataclass(frozen=True)
class CommentaryBlock:
    """A block of deterministic commentary lines."""

    title: str
    comments: list[str]


@dataclass(frozen=True)
class HtmlBlock:
    """A trusted HTML block produced by the report renderer or visual layer."""

    title: str
    body_html: str
    help_text: str | None = None


@dataclass(frozen=True)
class ReportBranding:
    """Branding configuration for rendered reports."""

    brand_name: str | None = None
    logo_image_src: str | None = None
    header_image_src: str | None = None
    footer_image_src: str | None = None
    footer_text: str | None = None


@dataclass(frozen=True)
class ReportPage:
    """A logical report page or section rendered in a consistent template."""

    title: str
    metric_cards: list[MetricCard] = field(default_factory=list)
    metric_tables: list[MetricTable] = field(default_factory=list)
    time_series_charts: list[TimeSeriesChart] = field(default_factory=list)
    heatmaps: list[Heatmap] = field(default_factory=list)
    commentary_blocks: list[CommentaryBlock] = field(default_factory=list)
    html_blocks: list[HtmlBlock] = field(default_factory=list)
    anchor_id: str | None = None

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if self.anchor_id is not None:
            if not self.anchor_id.strip():
                raise ValueError("anchor_id must not be empty when supplied")
            if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", self.anchor_id):
                raise ValueError(
                    "anchor_id must start with a letter and contain only "
                    "letters, digits, underscores, or hyphens"
                )


@dataclass(frozen=True)
class ReportDocument:
    """Top-level HTML report document."""

    title: str
    pages: list[ReportPage]
    branding: ReportBranding = field(default_factory=ReportBranding)
    generated_at_text: str | None = None
