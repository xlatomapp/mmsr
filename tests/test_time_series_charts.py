from datetime import date, time

import pytest

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import (
    ReportDocument,
    ReportPage,
    TimeSeriesChart,
    TimeSeriesChartPoint,
)
from mmsr.report.metric_docs import (
    append_metric_definitions_appendix,
    collect_metric_definitions_from_pages,
)
from mmsr.report.render_html import render_report, render_time_series_chart
from mmsr.report.sections import build_time_series_chart


QUOTED_SPREAD_BPS = next(
    metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps"
)
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_time_series_chart_renders_metric_help_and_period_context() -> None:
    chart = TimeSeriesChart(
        title="Quoted Spread Trend",
        metric=QUOTED_SPREAD_BPS,
        y_axis_label="Quoted spread (bps)",
        help_text="Bucketed median quoted spread.",
        points=[
            TimeSeriesChartPoint(
                x_text="2026-05-22 AMO",
                date_text="2026-05-22",
                time_bucket_text="AMO",
                series_text="venue=TSE",
                value_text="12.4000 bps",
                metadata_text="sample_size=120",
            )
        ],
    )

    html = render_time_series_chart(chart)

    assert "Quoted Spread Trend" in html
    assert "Quoted Spread" in html
    assert "Formula:" in html
    assert "Bucketed median quoted spread." in html
    assert "X-axis: Report period / bucket" in html
    assert "Y-axis: Quoted spread (bps)" in html
    assert "2026-05-22" in html
    assert "AMO" in html
    assert "venue=TSE" in html
    assert "12.4000 bps" in html
    assert "sample_size=120" in html
    assert "time-series-chart__placeholder" in html


def test_build_time_series_chart_preserves_observation_order_and_bucket_context() -> None:
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

    chart = build_time_series_chart(
        "Quoted Spread Trend",
        series,
        QUOTED_SPREAD_BPS,
        group_by=["venue"],
        y_axis_label="Quoted spread (bps)",
        max_points=2,
    )

    assert chart.title == "Quoted Spread Trend"
    assert chart.metric == QUOTED_SPREAD_BPS
    assert [point.x_text for point in chart.points] == [
        "2026-05-22 AMO",
        "2026-05-22 09:05",
    ]
    assert [point.date_text for point in chart.points] == [
        "2026-05-22",
        "2026-05-22",
    ]
    assert [point.time_bucket_text for point in chart.points] == ["AMO", "09:05"]
    assert [point.series_text for point in chart.points] == ["venue=TSE", "venue=ODX"]
    assert chart.points[0].value_text == "12.4000 bps"
    assert chart.points[1].value_text == "not available"
    assert chart.points[0].metadata_text == "sample_size=120"


def test_report_renders_time_series_charts_and_appendix_collects_definition() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Liquidity",
                time_series_charts=[
                    TimeSeriesChart(
                        title="Volume Trend",
                        metric=VOLUME,
                        points=[
                            TimeSeriesChartPoint(
                                x_text="2026-05-22",
                                date_text="2026-05-22",
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

    assert "Volume Trend" in html
    assert "time-series-chart" in html
    assert [definition.name for definition in definitions] == ["volume"]
    assert "Volume" in render_report(enriched)


def test_build_time_series_chart_validates_inputs() -> None:
    series = MetricTimeSeries.from_observations([], metric_name="quoted_spread_bps")

    with pytest.raises(ValueError, match="title"):
        build_time_series_chart(" ", series, QUOTED_SPREAD_BPS)

    with pytest.raises(ValueError, match="must match"):
        build_time_series_chart("Trend", series, VOLUME)

    with pytest.raises(ValueError, match="max_points"):
        build_time_series_chart("Trend", series, QUOTED_SPREAD_BPS, max_points=-1)

    with pytest.raises(ValueError, match="x_axis_label"):
        build_time_series_chart(
            "Trend",
            series,
            QUOTED_SPREAD_BPS,
            x_axis_label=" ",
        )

    with pytest.raises(ValueError, match="y_axis_label"):
        build_time_series_chart(
            "Trend",
            series,
            QUOTED_SPREAD_BPS,
            y_axis_label=" ",
        )

    with pytest.raises(ValueError, match="help_text"):
        build_time_series_chart("Trend", series, QUOTED_SPREAD_BPS, help_text=" ")


def test_time_series_chart_models_validate_required_text() -> None:
    with pytest.raises(ValueError, match="x_text"):
        TimeSeriesChartPoint(x_text=" ", value_text="1")

    with pytest.raises(ValueError, match="value_text"):
        TimeSeriesChartPoint(x_text="2026-05-22", value_text=" ")

    with pytest.raises(ValueError, match="title"):
        TimeSeriesChart(title=" ", metric=VOLUME, points=[])


def test_build_time_series_chart_requires_matching_definition() -> None:
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
        build_time_series_chart("Trend", series, changed_metric)
