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
    assert document.title == "Japanese Market Microstructure Monitor — Mock Data Demo"
    assert document.branding.brand_name == "mmsr mock data sample"
    assert document.generated_at_text == "deterministic mock data sample"
    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Activity Distribution",
        "Displayed Liquidity",
        "Reference and Target Daily Trends",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
        "Metric Definitions Appendix",
    ]

    summary_page = document.pages[0]
    activity_page = document.pages[1]
    liquidity_page = document.pages[2]
    trend_page = document.pages[3]
    drilldown_page = document.pages[4]
    detail_page = document.pages[5]

    assert len(summary_page.html_blocks) == 5
    assert summary_page.html_blocks[0].title == "Report Meta"
    assert summary_page.html_blocks[1].title == "Market Overview"
    assert summary_page.html_blocks[2].title == "Detailed Metric Trends"
    assert summary_page.html_blocks[3].title == "Market KPI Snapshot"
    assert summary_page.html_blocks[4].title == "Executive Market Overview"
    assert len(summary_page.metric_cards) == 3
    assert len(summary_page.metric_tables) == 1
    assert len(summary_page.metric_tables[0].rows) == 6
    assert len(summary_page.commentary_blocks) == 2
    assert summary_page.commentary_blocks[0].title == "Insight Callout"
    assert summary_page.commentary_blocks[1].comments[0].startswith("Market Summary headline:")
    assert len(activity_page.plotly_charts) == 1
    assert activity_page.plotly_charts[0].title == ("Volume cumulative intraday distribution")
    assert len(liquidity_page.plotly_charts) == 1
    assert liquidity_page.plotly_charts[0].title == "Quoted Spread intraday profile"
    assert len(trend_page.time_series_charts) == 3
    assert trend_page.time_series_charts[0].x_axis_label == "Trading day"
    assert len(drilldown_page.metric_tables) == 1
    assert len(drilldown_page.metric_tables[0].rows) == 6
    assert len(detail_page.time_series_charts) == 3
    assert detail_page.time_series_charts[0].x_axis_label == "Intraday time bucket"
    assert len(detail_page.heatmaps) == 0

    definitions = collect_metric_definitions_from_pages(document.pages)
    assert [definition.name for definition in definitions] == [
        "volume",
        "quoted_spread_bps",
        "top_of_book_depth",
    ]


def test_offline_demo_report_renders_comparison_visuals_commentary_and_help() -> None:
    html = render_report(build_offline_demo_report())

    assert "Market Summary" in html
    assert "Executive Market Overview" in html
    assert html.index('<section class="html-block"') < html.index('<div class="metric-grid">')
    assert "Overall:</strong>" in html
    assert "Current versus reference" in html
    assert "Activity Distribution" in html
    assert "cumulative intraday distribution" in html
    assert "Displayed Liquidity" in html
    assert "intraday profile" in html
    assert "Reference and Target Daily Trends" in html
    assert "daily reference-to-target trend" in html
    assert "Symbol Anomalies" not in html
    assert "Top symbol-level anomalies" not in html
    assert "Sector, Segment, and Market-Cap Drilldowns" in html
    assert "Top group-level drilldowns" in html
    assert "Group Delta Overview" in html
    assert "data-drilldown-matrix-spec" in html
    assert "Symbol 7203 Detail" not in html
    assert "Quoted Spread intraday time-bucket trend for symbol 7203" not in html
    assert "Volume intraday time-bucket trend for symbol 8306" not in html
    assert "Top-of-Book Depth intraday time-bucket trend for symbol 6758" not in html
    assert "Symbol 7203 Detail" not in html
    assert "symbol=7203" not in html
    assert "mock data sample" in html
    assert "plotly-chart__figure" in html
    assert "Compact plot data" in html
    assert "time-series-chart__placeholder" not in html
    assert "heatmap__placeholder" not in html
    assert "AM opening auction" in html
    assert "Market cap bucket: Small cap" in html
    assert "Market Summary headline:" in html
    assert "time_bucket=" not in html
    assert "market_cap_bucket=" not in html
    assert "reference_observation_unit" not in html
    assert "Metric Definitions Appendix" in html
    assert "Quoted Spread" in html
    assert "Top-of-Book Depth" in html
    assert "Volume" in html
    assert "Formula:" in html
    assert "mmsr mock data sample" in html


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
        "Market Summary",
        "Activity Distribution",
        "Displayed Liquidity",
        "Reference and Target Daily Trends",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
    ]
    assert len(document.pages[0].metric_cards) == 2
    assert len(document.pages[0].metric_tables[0].rows) == 3
    assert len(document.pages[0].commentary_blocks[0].comments) == 1
    assert len(document.pages[0].commentary_blocks[1].comments) == 2
    assert len(document.pages[1].plotly_charts) == 1
    assert len(document.pages[2].plotly_charts) == 1
    assert all(len(chart.points) == 1 for chart in document.pages[3].time_series_charts)
    assert len(document.pages[4].metric_tables[0].rows) == 6
    assert all(len(chart.points) == 1 for chart in document.pages[5].time_series_charts)
    assert document.pages[5].heatmaps == []


def test_build_offline_demo_report_accepts_supplied_sample_metrics() -> None:
    sample_metrics = build_offline_sample_metrics()

    document = build_offline_demo_report(sample_metrics)

    assert len(document.pages[0].metric_tables[0].rows) == 6
    assert len(document.pages[1].plotly_charts) == 1
    assert len(document.pages[2].plotly_charts) == 1
    assert len(document.pages[3].time_series_charts) == len(sample_metrics.current_series)
    assert len(document.pages[4].metric_tables[0].rows) == 6
    assert len(document.pages[5].time_series_charts) == len(sample_metrics.current_series)


def test_build_offline_demo_report_requires_definitions_for_current_series() -> None:
    sample_metrics = build_offline_sample_metrics()
    broken_sample = type(sample_metrics)(
        report_date=sample_metrics.report_date,
        metric_definitions={key: value for key, value in sample_metrics.metric_definitions.items() if key != "volume"},
        current_series=sample_metrics.current_series,
        reference_series=sample_metrics.reference_series,
        comparisons=sample_metrics.comparisons,
        symbol_current_series=sample_metrics.symbol_current_series,
    )

    with pytest.raises(ValueError, match="volume"):
        build_offline_demo_report(broken_sample)


def test_build_offline_demo_report_can_disable_drilldown_page() -> None:
    document = build_offline_demo_report(
        options=OfflineDemoReportOptions(
            include_metric_definitions_appendix=False,
            include_drilldown_page=False,
        )
    )

    assert "Sector, Segment, and Market-Cap Drilldowns" not in [page.title for page in document.pages]


def test_build_offline_demo_report_can_limit_drilldown_rows() -> None:
    document = build_offline_demo_report(
        options=OfflineDemoReportOptions(
            include_metric_definitions_appendix=False,
            max_drilldown_rows=2,
        )
    )

    drilldown_page = next(page for page in document.pages if page.title == "Sector, Segment, and Market-Cap Drilldowns")
    assert len(drilldown_page.metric_tables[0].rows) == 2


def test_offline_demo_report_options_validate_required_text_and_limits() -> None:
    with pytest.raises(ValueError, match="title"):
        OfflineDemoReportOptions(title=" ")

    with pytest.raises(ValueError, match="daily_trend_page_title"):
        OfflineDemoReportOptions(daily_trend_page_title=" ")

    with pytest.raises(ValueError, match="daily_trend_help_text"):
        OfflineDemoReportOptions(daily_trend_help_text=" ")

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

    with pytest.raises(ValueError, match="max_drilldown_rows"):
        OfflineDemoReportOptions(max_drilldown_rows=-1)
