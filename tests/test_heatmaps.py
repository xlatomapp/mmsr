from datetime import date, time

import pytest

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import Heatmap, HeatmapCell, ReportDocument, ReportPage
from mmsr.report.metric_docs import (
    append_metric_definitions_appendix,
    collect_metric_definitions_from_pages,
)
from mmsr.report.render_html import render_heatmap, render_report
from mmsr.report.sections import build_heatmap

QUOTED_SPREAD_BPS = next(metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps")
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_heatmap_renders_metric_help_and_bucket_group_context() -> None:
    heatmap = Heatmap(
        title="Quoted Spread Heatmap",
        metric=QUOTED_SPREAD_BPS,
        x_axis_label="Intraday bucket",
        y_axis_label="Venue",
        help_text="Bucketed median quoted spread by venue.",
        cells=[
            HeatmapCell(
                x_text="AMO",
                y_text="venue=TSE",
                date_text="2026-05-22",
                time_bucket_text="AMO",
                group_text="venue=TSE",
                value_text="12.4000 bps",
                metadata_text="Sample size: 120",
            )
        ],
    )

    html = render_heatmap(heatmap)

    assert "Quoted Spread Heatmap" in html
    assert "Quoted Spread" in html
    assert "Formula:" in html
    assert "Bucketed median quoted spread by venue." in html
    assert "X-axis: Intraday bucket" in html
    assert "Y-axis: Venue" in html
    assert "Value: bps" in html
    assert "2026-05-22" in html
    assert "AMO" in html
    assert "venue=TSE" in html
    assert "12.4000 bps" in html
    assert "Sample size: 120" in html
    assert "heatmap__visual" in html
    assert "heatmap__svg" in html
    assert "heatmap__cell" in html
    assert "Backing data" in html
    assert "heatmap__placeholder" not in html


def test_build_heatmap_preserves_observation_order_bucket_and_group_context() -> None:
    series = MetricTimeSeries(
        metric_name="quoted_spread_bps",
        observations=(
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 22),
                time_bucket="AMO",
                group={"segment": "Prime", "venue": "TSE"},
                value=12.4,
                metadata={"sample_size": 120},
            ),
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 22),
                time_bucket=time(9, 5),
                group={"segment": "Prime", "venue": "ODX"},
                value=None,
            ),
        ),
    )

    heatmap = build_heatmap(
        "Quoted Spread Heatmap",
        series,
        QUOTED_SPREAD_BPS,
        group_by=["venue"],
        y_axis_label="Venue",
        max_cells=2,
    )

    assert heatmap.title == "Quoted Spread Heatmap"
    assert heatmap.metric == QUOTED_SPREAD_BPS
    assert [cell.x_text for cell in heatmap.cells] == ["AM opening auction", "09:05"]
    assert [cell.y_text for cell in heatmap.cells] == ["Venue: TSE", "Venue: ODX"]
    assert [cell.date_text for cell in heatmap.cells] == [
        "2026-05-22",
        "2026-05-22",
    ]
    assert [cell.time_bucket_text for cell in heatmap.cells] == [
        "AM opening auction",
        "09:05",
    ]
    assert [cell.group_text for cell in heatmap.cells] == ["Venue: TSE", "Venue: ODX"]
    assert heatmap.cells[0].value_text == "12.4000 bps"
    assert heatmap.cells[0].value == 12.4
    assert heatmap.cells[0].numeric_value() == 12.4
    assert heatmap.cells[1].value_text == "not available"
    assert heatmap.cells[1].value is None
    assert heatmap.cells[1].numeric_value() is None
    assert heatmap.cells[0].metadata_text == "Sample size: 120"


def test_report_renders_heatmaps_and_appendix_collects_definition() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Liquidity",
                heatmaps=[
                    Heatmap(
                        title="Volume Heatmap",
                        metric=VOLUME,
                        cells=[
                            HeatmapCell(
                                x_text="AMO",
                                y_text="segment=Prime",
                                date_text="2026-05-22",
                                time_bucket_text="AMO",
                                group_text="segment=Prime",
                                value_text="1,000",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    html = render_report(document)
    definitions = collect_metric_definitions_from_pages(document.pages)
    enriched = append_metric_definitions_appendix(document)

    assert "Volume Heatmap" in html
    assert "heatmap" in html
    assert [definition.name for definition in definitions] == ["volume"]
    assert "Volume" in render_report(enriched)


def test_build_heatmap_validates_inputs() -> None:
    series = MetricTimeSeries.from_observations([], metric_name="quoted_spread_bps")

    with pytest.raises(ValueError, match="title"):
        build_heatmap(" ", series, QUOTED_SPREAD_BPS)

    with pytest.raises(ValueError, match="must match"):
        build_heatmap("Heatmap", series, VOLUME)

    with pytest.raises(ValueError, match="max_cells"):
        build_heatmap("Heatmap", series, QUOTED_SPREAD_BPS, max_cells=-1)

    with pytest.raises(ValueError, match="x_axis_label"):
        build_heatmap("Heatmap", series, QUOTED_SPREAD_BPS, x_axis_label=" ")

    with pytest.raises(ValueError, match="y_axis_label"):
        build_heatmap("Heatmap", series, QUOTED_SPREAD_BPS, y_axis_label=" ")

    with pytest.raises(ValueError, match="help_text"):
        build_heatmap("Heatmap", series, QUOTED_SPREAD_BPS, help_text=" ")


def test_heatmap_renders_deterministic_svg_matrix_and_backing_data() -> None:
    heatmap = Heatmap(
        title="Volume Heatmap",
        metric=VOLUME,
        x_axis_label="Intraday bucket",
        y_axis_label="Segment",
        cells=[
            HeatmapCell(
                x_text="AMO",
                y_text="segment=Prime",
                value_text="1,000",
                value=1000,
            ),
            HeatmapCell(
                x_text="09:05",
                y_text="segment=Prime",
                value_text="2,000",
                value=2000,
            ),
            HeatmapCell(
                x_text="AMO",
                y_text="segment=Standard",
                value_text="not available",
            ),
        ],
    )

    html = render_heatmap(heatmap)

    assert heatmap.has_svg_matrix()
    assert heatmap.svg_view_box() == "0 0 334.00 146.00"
    assert [label.text for label in heatmap.svg_x_labels()] == ["AMO", "09:05"]
    assert [label.text for label in heatmap.svg_y_labels()] == [
        "segment=Prime",
        "segment=Standard",
    ]
    svg_cells = heatmap.svg_cells()
    assert len(svg_cells) == 3
    assert svg_cells[0].opacity == "0.18"
    assert svg_cells[1].opacity == "0.95"
    assert svg_cells[2].css_class == "heatmap__cell heatmap__cell--missing"
    assert "Volume Heatmap heatmap" in html
    assert "Deterministic inline SVG heatmap" in html
    assert "segment=Prime, AMO: 1,000" in html
    assert "segment=Prime, 09:05: 2,000" in html
    assert "segment=Standard, AMO: not available" in html
    assert "heatmap__visual" in html
    assert "heatmap__data" in html
    assert "Backing data" in html
    assert "heatmap__placeholder" not in html


def test_heatmap_numeric_value_falls_back_to_display_text() -> None:
    heatmap = Heatmap(
        title="Hand-built Heatmap",
        metric=QUOTED_SPREAD_BPS,
        cells=[
            HeatmapCell(
                x_text="AMO",
                y_text="venue=TSE",
                value_text="12.4000 bps",
            )
        ],
    )

    assert heatmap.cells[0].numeric_value() == 12.4
    assert heatmap.has_svg_matrix()
    assert heatmap.svg_cells()[0].label == "12.4"


def test_heatmap_models_validate_required_text() -> None:
    with pytest.raises(ValueError, match="x_text"):
        HeatmapCell(x_text=" ", y_text="venue=TSE", value_text="1")

    with pytest.raises(ValueError, match="y_text"):
        HeatmapCell(x_text="AMO", y_text=" ", value_text="1")

    with pytest.raises(ValueError, match="value_text"):
        HeatmapCell(x_text="AMO", y_text="venue=TSE", value_text=" ")

    with pytest.raises(ValueError, match="title"):
        Heatmap(title=" ", metric=VOLUME, cells=[])

    with pytest.raises(ValueError, match="x_axis_label"):
        Heatmap(title="Heatmap", metric=VOLUME, cells=[], x_axis_label=" ")

    with pytest.raises(ValueError, match="y_axis_label"):
        Heatmap(title="Heatmap", metric=VOLUME, cells=[], y_axis_label=" ")

    with pytest.raises(ValueError, match="help_text"):
        Heatmap(title="Heatmap", metric=VOLUME, cells=[], help_text=" ")


def test_build_heatmap_requires_matching_definition() -> None:
    changed_metric = MetricDefinition(
        name="changed_volume",
        label=VOLUME.label,
        category=VOLUME.category,
        description=VOLUME.description,
        formula=VOLUME.formula,
        interpretation=VOLUME.interpretation,
        unit=VOLUME.unit,
        higher_is_better=VOLUME.higher_is_better,
        default_aggregation=VOLUME.default_aggregation,
        supports_intraday=VOLUME.supports_intraday,
        supports_symbol_level=VOLUME.supports_symbol_level,
        required_tables=VOLUME.required_tables,
        required_columns=VOLUME.required_columns,
    )

    series = MetricTimeSeries.from_observations([], metric_name="volume")

    with pytest.raises(ValueError, match="must match"):
        build_heatmap("Heatmap", series, changed_metric)
