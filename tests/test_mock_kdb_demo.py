from __future__ import annotations

import sys

import pytest

from mmsr.examples import (
    MockKdbIntegrationDemoOptions,
    MockKdbIntegrationDemoResult,
    build_mock_kdb_integration_demo_report,
    build_mock_kdb_integration_demo_result,
)
from mmsr.report.components import ReportDocument
from mmsr.report.render_html import render_report


def test_mock_kdb_demo_executes_q_templates_and_builds_report() -> None:
    result = build_mock_kdb_integration_demo_result()

    assert isinstance(result, MockKdbIntegrationDemoResult)
    assert isinstance(result.document, ReportDocument)
    assert result.document.title == (
        "Japanese Market Microstructure Monitor — Mock kdb Integration Demo"
    )
    assert [page.title for page in result.document.pages] == [
        "Market Summary",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
        "Metric Definitions Appendix",
    ]
    assert [series.metric_name for series in result.current_series] == [
        "quoted_spread_bps",
        "volume",
        "top_of_book_depth",
    ]
    assert [series.metric_name for series in result.reference_series] == [
        "quoted_spread_bps",
        "volume",
        "top_of_book_depth",
    ]
    assert len(result.comparisons) == 6
    assert len(result.executed_queries) == 6
    assert all("select" in query for query in result.executed_queries)
    assert all("by date, time_bucket:" in query for query in result.executed_queries)
    assert any("from mock_trade" in query for query in result.executed_queries)
    assert any("from mock_quote" in query for query in result.executed_queries)
    assert any("date within (2026.05.22;2026.05.22)" in query for query in result.executed_queries)
    assert any("date within (2026.04.06;2026.05.21)" in query for query in result.executed_queries)

    summary_page = result.document.pages[0]
    drilldown_page = result.document.pages[1]
    detail_page = result.document.pages[2]
    assert summary_page.html_blocks[0].title == "Executive Market Overview"
    assert len(summary_page.metric_tables[0].rows) == 6
    assert len(drilldown_page.metric_tables[0].rows) == 6
    assert len(detail_page.time_series_charts) == 3
    assert len(detail_page.heatmaps) == 3
    assert result.current_series[0].metadata["template"] == "liquidity.q"
    assert result.current_series[1].metadata["template"] == "activity.q"
    assert result.current_series[0].metadata["role"] == "current"
    assert "from mock_quote" in result.current_series[0].metadata["query"]


def test_mock_kdb_demo_report_renders_canonical_report_visuals_and_labels() -> None:
    html = render_report(build_mock_kdb_integration_demo_report())

    assert "Mock kdb Integration Demo" in html
    assert "mmsr mock kdb sample" in html
    assert "Executive Market Overview" in html
    assert "Sector, Segment, and Market-Cap Drilldowns" in html
    assert "Top group-level drilldowns" in html
    assert "mock kdb integration" in html
    assert "KdbMetricRunner" in html
    assert "time-series-chart__svg" in html
    assert "heatmap__svg" in html
    assert "Backing data" in html
    assert "AM opening auction" in html
    assert "Market cap bucket: Small cap" in html
    assert "Reference observation unit: trading day" in html
    assert "time-series-chart__placeholder" not in html
    assert "heatmap__placeholder" not in html
    assert "time_bucket=" not in html
    assert "market_cap_bucket=" not in html


def test_mock_kdb_demo_options_can_omit_appendix_and_limit_components() -> None:
    document = build_mock_kdb_integration_demo_report(
        options=MockKdbIntegrationDemoOptions(
            include_metric_definitions_appendix=False,
            max_metric_cards=2,
            max_comments=2,
            max_table_rows=3,
            max_chart_points=1,
            max_heatmap_cells=1,
            max_overview_metrics=2,
        )
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
    ]
    assert len(document.pages[0].metric_cards) == 2
    assert len(document.pages[0].metric_tables[0].rows) == 3
    assert len(document.pages[0].commentary_blocks[0].comments) == 2
    assert len(document.pages[1].metric_tables[0].rows) == 6
    assert all(len(chart.points) == 1 for chart in document.pages[2].time_series_charts)
    assert all(len(heatmap.cells) == 1 for heatmap in document.pages[2].heatmaps)



def test_mock_kdb_demo_options_can_disable_drilldown_page() -> None:
    document = build_mock_kdb_integration_demo_report(
        options=MockKdbIntegrationDemoOptions(
            include_metric_definitions_appendix=False,
            include_drilldown_page=False,
        )
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Intraday Detail",
    ]


def test_mock_kdb_demo_options_can_limit_drilldown_rows() -> None:
    document = build_mock_kdb_integration_demo_report(
        options=MockKdbIntegrationDemoOptions(
            include_metric_definitions_appendix=False,
            max_drilldown_rows=2,
        )
    )

    drilldown_page = next(
        page
        for page in document.pages
        if page.title == "Sector, Segment, and Market-Cap Drilldowns"
    )
    assert len(drilldown_page.metric_tables[0].rows) == 2


def test_mock_kdb_demo_options_validate_required_text_and_limits() -> None:
    with pytest.raises(ValueError, match="title"):
        MockKdbIntegrationDemoOptions(title=" ")

    with pytest.raises(ValueError, match="max_metric_cards"):
        MockKdbIntegrationDemoOptions(max_metric_cards=-1)

    with pytest.raises(ValueError, match="max_comments"):
        MockKdbIntegrationDemoOptions(max_comments=-1)

    with pytest.raises(ValueError, match="max_table_rows"):
        MockKdbIntegrationDemoOptions(max_table_rows=-1)

    with pytest.raises(ValueError, match="max_chart_points"):
        MockKdbIntegrationDemoOptions(max_chart_points=-1)

    with pytest.raises(ValueError, match="max_heatmap_cells"):
        MockKdbIntegrationDemoOptions(max_heatmap_cells=-1)

    with pytest.raises(ValueError, match="max_drilldown_rows"):
        MockKdbIntegrationDemoOptions(max_drilldown_rows=-1)


def test_mock_kdb_demo_does_not_import_pykx() -> None:
    sys.modules.pop("pykx", None)

    build_mock_kdb_integration_demo_result()

    assert "pykx" not in sys.modules
