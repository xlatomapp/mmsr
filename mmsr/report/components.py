"""Report component models."""

from __future__ import annotations

from dataclasses import dataclass, field

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
class TimeSeriesChartPoint:
    """One deterministic point rendered by a time-series chart placeholder."""

    x_text: str
    value_text: str
    date_text: str | None = None
    time_bucket_text: str | None = None
    series_text: str | None = None
    metadata_text: str | None = None

    def __post_init__(self) -> None:
        if not self.x_text.strip():
            raise ValueError("x_text must not be empty")
        if not self.value_text.strip():
            raise ValueError("value_text must not be empty")


@dataclass(frozen=True)
class TimeSeriesChart:
    """A deterministic time-series chart placeholder with metric help text."""

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


@dataclass(frozen=True)
class HeatmapCell:
    """One deterministic cell rendered by a heatmap placeholder."""

    x_text: str
    y_text: str
    value_text: str
    date_text: str | None = None
    time_bucket_text: str | None = None
    group_text: str | None = None
    metadata_text: str | None = None

    def __post_init__(self) -> None:
        if not self.x_text.strip():
            raise ValueError("x_text must not be empty")
        if not self.y_text.strip():
            raise ValueError("y_text must not be empty")
        if not self.value_text.strip():
            raise ValueError("value_text must not be empty")


@dataclass(frozen=True)
class Heatmap:
    """A deterministic heatmap placeholder with metric help text."""

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


@dataclass(frozen=True)
class ReportDocument:
    """Top-level HTML report document."""

    title: str
    pages: list[ReportPage]
    branding: ReportBranding = field(default_factory=ReportBranding)
    generated_at_text: str | None = None
