import pytest

from mmsr.examples import (
    OfflineDemoReportOptions,
    build_offline_demo_report,
    build_offline_sample_metrics,
)
from mmsr.report.components import ReportDocument
from mmsr.report.metric_docs import collect_metric_definitions_from_pages
from mmsr.report.render_html import render_report


def test_build_offline_demo_report_assembles_document_with_appendix() -> None:
    document = build_offline_demo_report()

    assert isinstance(document, ReportDocument)
    assert document.title == "Japanese Market Microstructure Monitor — Offline Demo"
    assert document.branding.brand_name == "mmsr offline sample"
    assert document.generated_at_text == "deterministic offline sample"
    assert [page.title for page in document.pages] == [
        "Offline Market Summary",
        "Offline Intraday Detail",
        "Metric Definitions Appendix",
    ]

    summary_page = document.pages[0]
    detail_page = document.pages[1]

    assert len(summary_page.metric_cards) == 6
    assert len(summary_page.metric_tables) == 1
    assert len(summary_page.metric_tables[0].rows) == 6
    assert len(summary_page.commentary_blocks) == 1
    assert summary_page.commentary_blocks[0].comments[0].startswith(
        "Offline Market Summary headline:"
    )
    assert len(detail_page.time_series_charts) == 3
    assert len(detail_page.heatmaps) == 3

    definitions = collect_metric_definitions_from_pages(document.pages)
    assert [definition.name for definition in definitions] == [
        "volume",
        "quoted_spread_bps",
        "top_of_book_depth",
    ]


def test_offline_demo_report_renders_comparison_visuals_commentary_and_help() -> None:
    html = render_report(build_offline_demo_report())

    assert "Offline Market Summary" in html
    assert "Current versus synthetic reference" in html
    assert "offline synthetic sample" in html
    assert "time-series-chart__placeholder" in html
    assert "heatmap__placeholder" in html
    assert "Metric Definitions Appendix" in html
    assert "Quoted Spread" in html
    assert "Top-of-Book Depth" in html
    assert "Volume" in html
    assert "Formula:" in html
    assert "mmsr offline sample" in html


def test_build_offline_demo_report_can_omit_appendix_and_limit_rows() -> None:
    options = OfflineDemoReportOptions(
        include_metric_definitions_appendix=False,
        max_metric_cards=2,
        max_comments=2,
        max_table_rows=3,
        max_chart_points=1,
        max_heatmap_cells=1,
    )

    document = build_offline_demo_report(options=options)

    assert [page.title for page in document.pages] == [
        "Offline Market Summary",
        "Offline Intraday Detail",
    ]
    assert len(document.pages[0].metric_cards) == 2
    assert len(document.pages[0].metric_tables[0].rows) == 3
    assert len(document.pages[0].commentary_blocks[0].comments) == 2
    assert all(len(chart.points) == 1 for chart in document.pages[1].time_series_charts)
    assert all(len(heatmap.cells) == 1 for heatmap in document.pages[1].heatmaps)


def test_build_offline_demo_report_accepts_supplied_sample_metrics() -> None:
    sample_metrics = build_offline_sample_metrics()

    document = build_offline_demo_report(sample_metrics)

    assert len(document.pages[0].metric_tables[0].rows) == len(
        sample_metrics.comparisons
    )
    assert len(document.pages[1].time_series_charts) == len(
        sample_metrics.current_series
    )


def test_build_offline_demo_report_requires_definitions_for_current_series() -> None:
    sample_metrics = build_offline_sample_metrics()
    broken_sample = type(sample_metrics)(
        report_date=sample_metrics.report_date,
        metric_definitions={
            key: value
            for key, value in sample_metrics.metric_definitions.items()
            if key != "volume"
        },
        current_series=sample_metrics.current_series,
        reference_series=sample_metrics.reference_series,
        comparisons=sample_metrics.comparisons,
    )

    with pytest.raises(ValueError, match="volume"):
        build_offline_demo_report(broken_sample)


def test_offline_demo_report_options_validate_required_text_and_limits() -> None:
    with pytest.raises(ValueError, match="title"):
        OfflineDemoReportOptions(title=" ")

    with pytest.raises(ValueError, match="max_metric_cards"):
        OfflineDemoReportOptions(max_metric_cards=-1)

    with pytest.raises(ValueError, match="max_comments"):
        OfflineDemoReportOptions(max_comments=-1)

    with pytest.raises(ValueError, match="max_table_rows"):
        OfflineDemoReportOptions(max_table_rows=-1)

    with pytest.raises(ValueError, match="max_chart_points"):
        OfflineDemoReportOptions(max_chart_points=-1)

    with pytest.raises(ValueError, match="max_heatmap_cells"):
        OfflineDemoReportOptions(max_heatmap_cells=-1)
