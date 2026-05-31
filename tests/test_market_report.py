import pytest

from mmsr.examples import build_offline_sample_metrics
from mmsr.metrics.results import MetricComparison
from mmsr.report import (
    MarketReportInput,
    MarketReportOptions,
    build_market_monitor_report,
)
from mmsr.report.components import ReportDocument
from mmsr.report.render_html import render_report


def _input_from_mock_sample() -> MarketReportInput:
    sample = build_offline_sample_metrics()
    return MarketReportInput(
        metric_definitions=sample.metric_definitions,
        current_series=sample.current_series,
        comparisons=sample.comparisons,
        reference_series=sample.reference_series,
    )


def test_market_monitor_report_is_canonical_production_format() -> None:
    document = build_market_monitor_report(
        _input_from_mock_sample(),
        options=MarketReportOptions(
            title="Japanese Market Microstructure Monitor",
            brand_name="Example Securities",
            generated_at_text="2026-05-22 close",
        ),
    )

    assert isinstance(document, ReportDocument)
    assert document.title == "Japanese Market Microstructure Monitor"
    assert document.branding.brand_name == "Example Securities"
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

    assert len(summary_page.html_blocks) == 3
    assert summary_page.html_blocks[0].title == "Report Meta"
    assert 'class="report-meta-strip report-control-strip"' in summary_page.html_blocks[0].body_html
    assert summary_page.html_blocks[1].title == "Market KPI Snapshot"
    assert 'class="kpi-snapshot"' in summary_page.html_blocks[1].body_html
    assert summary_page.html_blocks[2].title == "Executive Market Overview"
    assert "Overall:</strong>" in summary_page.html_blocks[2].body_html
    assert "<strong>Market activity:</strong>" in summary_page.html_blocks[2].body_html
    assert "<strong>Displayed liquidity:</strong>" in summary_page.html_blocks[2].body_html
    assert len(summary_page.metric_cards) == 3
    assert len(summary_page.plotly_charts) == 4
    assert summary_page.plotly_charts[0].title.startswith("Primary Intraday Signal")
    assert len(summary_page.metric_tables) == 1
    assert len(summary_page.commentary_blocks) == 2
    assert summary_page.commentary_blocks[0].title == "Insight Callout"
    assert summary_page.commentary_blocks[1].comments[0].startswith("Market Summary headline:")
    assert len(activity_page.plotly_charts) == 1
    assert activity_page.plotly_charts[0].title == ("Volume cumulative intraday distribution")
    assert len(liquidity_page.plotly_charts) == 1
    assert liquidity_page.plotly_charts[0].title == "Quoted Spread intraday profile"
    assert len(trend_page.time_series_charts) == 3
    assert trend_page.time_series_charts[0].x_axis_label == "Trading day"
    assert "reference" in trend_page.time_series_charts[0].points[0].metadata_text
    assert "target" in trend_page.time_series_charts[0].points[-1].metadata_text
    assert len(drilldown_page.metric_tables[0].rows) == 6
    assert drilldown_page.metric_tables[0].help_text is not None
    assert len(detail_page.time_series_charts) == 3
    assert detail_page.time_series_charts[0].x_axis_label == "Intraday time bucket"
    assert detail_page.time_series_charts[0].points[0].x_text == "AM opening auction"
    assert len(detail_page.heatmaps) == 0


def test_market_monitor_report_uses_packaged_template_for_any_data_source() -> None:
    html = render_report(
        build_market_monitor_report(
            _input_from_mock_sample(),
            options=MarketReportOptions(
                title="Production Format Acceptance Report",
                brand_name="mmsr",
                generated_at_text="mock data acceptance run",
            ),
        )
    )

    assert "Production Format Acceptance Report" in html
    assert "Market Summary" in html
    assert "Intraday Detail" in html
    assert "Activity Distribution" in html
    assert "cumulative intraday distribution" in html
    assert "Displayed Liquidity" in html
    assert "intraday profile" in html
    assert "Reference and Target Daily Trends" in html
    assert "daily reference-to-target trend" in html
    assert "Symbol Anomalies" not in html
    assert "Sector, Segment, and Market-Cap Drilldowns" in html
    assert "Top group-level drilldowns" in html
    assert "drilldown-delta-bars" in html
    assert "Group Delta Overview" in html
    assert "data-drilldown-matrix-spec" in html
    assert "data-drilldown-heatmap" in html
    assert 'aria-label="Liquidity group-metric heatmap"' in html
    assert 'aria-label="Selected group daily trend chart"' in html
    assert ".drilldown-matrix-explorer__grid {" in html
    assert "gap: 10px;" in html
    assert ".drilldown-matrix-explorer__panel h4 {" in html
    assert "font-size: 13px;" in html
    assert "line-height: 1.35;" in html
    assert ".explorer-panel__title {" in html
    assert ".explorer-panel__subtitle {" in html
    assert "Executive Market Overview" in html
    assert "Market KPI Snapshot" in html
    assert "Report Meta" in html
    assert "Universe" in html
    assert "Benchmark" in html
    assert "Export PDF" in html
    assert "report-control-strip" in html
    assert "report-export-link" in html
    assert "kpi-snapshot__mini" in html
    assert 'class="report-page__header"' in html
    assert 'class="report-page__index">1<' in html
    assert 'class="report-page__title">Market Summary<' in html
    assert "--mmsr-heading: #0b3a67;" in html
    assert ".report-page__title {" in html
    assert "font-size: 30px;" in html
    assert "Primary Intraday Signal" in html
    assert "report-page--summary" in html
    assert 'data-block-title="Report Meta"' in html
    assert 'data-block-title="Market KPI Snapshot"' in html
    assert 'data-block-title="Executive Market Overview"' in html
    assert html.index('<section class="html-block"') < html.index('<div class="metric-grid">')
    assert html.index("Report Meta") < html.index("Market KPI Snapshot")
    assert html.index("Market KPI Snapshot") < html.index("Executive Market Overview")
    assert html.index("Top market drivers") < html.index("Primary Intraday Signal")
    assert html.index("Primary Intraday Signal") < html.index("Insight Callout")
    assert html.index("Insight Callout") < html.index("Current versus reference")
    assert html.index('data-block-title="Report Meta"') < html.index('data-block-title="Market KPI Snapshot"')
    assert html.index('data-block-title="Market KPI Snapshot"') < html.index(
        'data-block-title="Executive Market Overview"'
    )
    assert html.index("Executive Market Overview") < html.index("Current versus reference")
    assert html.index("Top market drivers") < html.index("Current versus reference")
    assert html.index("Driver intensity (|z|)") < html.index("Current versus reference")
    assert html.index("cumulative intraday distribution") < html.index("Current versus reference")
    assert "Overall:</strong>" in html
    assert "Market activity:" in html
    assert "Displayed liquidity:" in html
    assert "key metrics" in html
    assert "Current versus reference" in html
    assert "plotly-chart__figure" in html
    assert "Compact plot data" in html
    assert "time-series-chart__placeholder" not in html
    assert "heatmap__placeholder" not in html
    assert "AM opening auction" in html
    assert "Market cap bucket: Small cap" in html
    assert "time_bucket=" not in html
    assert "market_cap_bucket=" not in html
    assert "Metric Definitions Appendix" in html


def test_market_monitor_report_can_omit_appendix_and_limit_components() -> None:
    document = build_market_monitor_report(
        _input_from_mock_sample(),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            max_metric_cards=2,
            max_comments=1,
            max_table_rows=3,
            max_chart_points=1,
            max_heatmap_cells=1,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Activity Distribution",
        "Displayed Liquidity",
        "Reference and Target Daily Trends",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
    ]
    assert len(document.pages[0].html_blocks) == 3
    assert len(document.pages[0].metric_cards) == 2
    assert len(document.pages[0].plotly_charts) == 4
    assert len(document.pages[0].metric_tables[0].rows) == 3
    assert len(document.pages[0].commentary_blocks[0].comments) == 1
    assert len(document.pages[0].commentary_blocks[1].comments) == 1
    assert len(document.pages[1].plotly_charts) == 1
    assert len(document.pages[2].plotly_charts) == 1
    assert all(len(chart.points) == 1 for chart in document.pages[3].time_series_charts)
    assert len(document.pages[4].metric_tables[0].rows) == 6
    assert all(len(chart.points) == 1 for chart in document.pages[5].time_series_charts)
    assert document.pages[5].heatmaps == []


def test_market_monitor_report_can_disable_drilldown_page() -> None:
    document = build_market_monitor_report(
        _input_from_mock_sample(),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_drilldown_page=False,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Activity Distribution",
        "Displayed Liquidity",
        "Reference and Target Daily Trends",
        "Intraday Detail",
    ]


def test_market_monitor_report_skips_drilldown_page_without_group_rows() -> None:
    sample = build_offline_sample_metrics()
    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=sample.metric_definitions,
            current_series=sample.current_series,
            comparisons=(),
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Intraday Detail",
    ]


def test_market_monitor_report_defaults_remain_market_first_with_symbol_rows_present() -> None:
    sample = build_offline_sample_metrics()
    symbol_comparison = MetricComparison(
        metric_name="quoted_spread_bps",
        value=25.0,
        reference_value=15.0,
        change_abs=10.0,
        change_pct=10.0 / 15.0,
        z_score=3.2,
        percentile=None,
        status="alert",
        group={"sym": "7203"},
        time_bucket="09:00-09:05",
    )
    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=sample.metric_definitions,
            current_series=sample.current_series,
            comparisons=tuple(sample.comparisons) + (symbol_comparison,),
            reference_series=sample.reference_series,
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Activity Distribution",
        "Displayed Liquidity",
        "Reference and Target Daily Trends",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
    ]
    assert "Symbol Anomalies" not in [page.title for page in document.pages]
    assert all(not page.title.startswith("Symbol ") for page in document.pages)


def test_market_summary_aggregates_bucket_level_duplicates_for_same_market_context() -> None:
    sample = build_offline_sample_metrics()
    duplicate_alerts = tuple(
        MetricComparison(
            metric_name="quoted_spread_bps",
            value=9.0 + (0.1 * idx),
            reference_value=7.0,
            change_abs=2.0 + (0.1 * idx),
            change_pct=(2.0 + (0.1 * idx)) / 7.0,
            z_score=3.5 - (0.1 * idx),
            percentile=None,
            status="alert",
            group={"topixCapGrp": "Mid"},
            time_bucket=f"09:{idx:02d}-09:{idx + 1:02d}",
        )
        for idx in range(6)
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=sample.metric_definitions,
            current_series=sample.current_series,
            comparisons=duplicate_alerts,
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )

    summary_page = document.pages[0]
    quoted_spread_cards = [card for card in summary_page.metric_cards if card.metric.name == "quoted_spread_bps"]
    assert len(quoted_spread_cards) == 1
    assert "Top market drivers" in summary_page.html_blocks[2].body_html


def test_market_monitor_report_passes_custom_drilldown_options() -> None:
    document = build_market_monitor_report(
        _input_from_mock_sample(),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            drilldown_page_title="Market-Cap Drilldowns",
            drilldown_table_title="Market-cap rows",
            drilldown_help_text="Market-cap comparison facts.",
            drilldown_group_keys=("market_cap_bucket",),
            max_drilldown_rows=2,
        ),
    )

    drilldown_page = document.pages[4]
    assert drilldown_page.title == "Market-Cap Drilldowns"
    table = drilldown_page.metric_tables[0]
    assert table.title == "Market-cap rows"
    assert table.help_text == "Market-cap comparison facts."
    assert len(table.rows) == 2
    assert all("Market cap bucket:" in row.group_text for row in table.rows)
    assert all("Market segment:" in row.group_text for row in table.rows)


def test_market_monitor_report_can_opt_into_intraday_heatmaps() -> None:
    document = build_market_monitor_report(
        _input_from_mock_sample(),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_intraday_heatmaps=True,
        ),
    )

    detail_page = next(page for page in document.pages if page.title == "Intraday Detail")
    symbol_detail_pages = [
        page for page in document.pages if page.title.startswith("Symbol ") and page.title.endswith(" Detail")
    ]
    assert len(detail_page.heatmaps) == 3
    assert symbol_detail_pages == []


def test_market_monitor_report_requires_metric_definitions_for_current_series() -> None:
    sample = build_offline_sample_metrics()
    broken_input = MarketReportInput(
        metric_definitions={key: value for key, value in sample.metric_definitions.items() if key != "volume"},
        current_series=sample.current_series,
        comparisons=sample.comparisons,
    )

    with pytest.raises(ValueError, match="volume"):
        build_market_monitor_report(broken_input)


def test_market_report_options_validate_text_and_limits() -> None:
    with pytest.raises(ValueError, match="title"):
        MarketReportOptions(title=" ")

    with pytest.raises(ValueError, match="brand_name"):
        MarketReportOptions(brand_name=" ")

    with pytest.raises(ValueError, match="generated_at_text"):
        MarketReportOptions(generated_at_text=" ")

    with pytest.raises(ValueError, match="daily_trend_page_title"):
        MarketReportOptions(daily_trend_page_title=" ")

    with pytest.raises(ValueError, match="daily_trend_help_text"):
        MarketReportOptions(daily_trend_help_text=" ")

    with pytest.raises(ValueError, match="summary_scope_label"):
        MarketReportOptions(summary_scope_label=" ")

    with pytest.raises(ValueError, match="displayed_liquidity_page_title"):
        MarketReportOptions(displayed_liquidity_page_title=" ")

    with pytest.raises(ValueError, match="displayed_liquidity_help_text"):
        MarketReportOptions(displayed_liquidity_help_text=" ")

    with pytest.raises(ValueError, match="displayed_liquidity_metric_names"):
        MarketReportOptions(displayed_liquidity_metric_names=("quoted_spread_bps", " "))

    with pytest.raises(ValueError, match="max_displayed_liquidity_charts"):
        MarketReportOptions(max_displayed_liquidity_charts=-1)

    with pytest.raises(ValueError, match="max_displayed_liquidity_groups"):
        MarketReportOptions(max_displayed_liquidity_groups=-1)

    with pytest.raises(ValueError, match="executive_overview_title"):
        MarketReportOptions(executive_overview_title=" ")

    with pytest.raises(ValueError, match="executive_overview_help_text"):
        MarketReportOptions(executive_overview_help_text=" ")

    with pytest.raises(ValueError, match="max_metric_cards"):
        MarketReportOptions(max_metric_cards=-1)

    with pytest.raises(ValueError, match="max_summary_story_charts"):
        MarketReportOptions(max_summary_story_charts=-1)

    with pytest.raises(ValueError, match="overview_top_change_diversification"):
        MarketReportOptions(overview_top_change_diversification="invalid")

    with pytest.raises(ValueError, match="primary_intraday_signal_metric_name"):
        MarketReportOptions(primary_intraday_signal_metric_name=" ")

    with pytest.raises(ValueError, match="max_comments"):
        MarketReportOptions(max_comments=-1)

    with pytest.raises(ValueError, match="max_table_rows"):
        MarketReportOptions(max_table_rows=-1)

    with pytest.raises(ValueError, match="max_overview_metrics"):
        MarketReportOptions(max_overview_metrics=-1)

    with pytest.raises(ValueError, match="symbol_detail_page_title_template"):
        MarketReportOptions(symbol_detail_page_title_template=" ")

    with pytest.raises(ValueError, match="symbol_detail_help_text"):
        MarketReportOptions(symbol_detail_help_text=" ")

    with pytest.raises(ValueError, match="max_symbol_detail_pages"):
        MarketReportOptions(max_symbol_detail_pages=-1)

    with pytest.raises(ValueError, match="drilldown_page_title"):
        MarketReportOptions(drilldown_page_title=" ")

    with pytest.raises(ValueError, match="drilldown_table_title"):
        MarketReportOptions(drilldown_table_title=" ")

    with pytest.raises(ValueError, match="drilldown_help_text"):
        MarketReportOptions(drilldown_help_text=" ")

    with pytest.raises(ValueError, match="max_drilldown_rows"):
        MarketReportOptions(max_drilldown_rows=-1)

    with pytest.raises(ValueError, match="drilldown_group_keys must not be empty"):
        MarketReportOptions(drilldown_group_keys=())

    with pytest.raises(ValueError, match="drilldown_group_keys must not contain"):
        MarketReportOptions(drilldown_group_keys=("sector", " "))

    with pytest.raises(ValueError, match="symbol_group_keys must not be empty"):
        MarketReportOptions(symbol_group_keys=())

    with pytest.raises(ValueError, match="symbol_group_keys must not contain"):
        MarketReportOptions(symbol_group_keys=("symbol", " "))
