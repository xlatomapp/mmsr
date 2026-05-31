"""Tests for deterministic symbol-level anomaly report pages."""

from __future__ import annotations

from datetime import date

import pytest

from mmsr.metrics.registry import build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.report import (
    MarketReportInput,
    MarketReportOptions,
    SymbolAnomalyPageOptions,
    SymbolDetailIndexOptions,
    SymbolDetailPageOptions,
    build_market_monitor_report,
    build_symbol_anomaly_page,
    build_symbol_detail_index_block,
    build_symbol_detail_pages,
    select_symbol_anomalies,
    symbol_detail_anchor_id,
)
from mmsr.report.render_html import render_report


def test_select_symbol_anomalies_returns_worst_per_symbol_and_excludes_normal() -> None:
    comparisons = (
        _comparison(
            "quoted_spread_bps",
            "7203",
            status="normal",
            z_score=0.4,
            empirical_tail=0.62,
        ),
        _comparison(
            "top_of_book_depth",
            "7203",
            status="alert",
            z_score=-2.7,
            empirical_tail=0.01,
        ),
        _comparison(
            "quoted_spread_bps",
            "6758",
            status="watch",
            z_score=1.8,
            empirical_tail=0.08,
        ),
        _comparison(
            "quoted_spread_bps",
            "8306",
            status="normal",
            z_score=0.1,
            empirical_tail=0.55,
        ),
        _comparison(
            "quoted_spread_bps",
            None,
            status="alert",
            z_score=3.1,
            empirical_tail=0.01,
        ),
    )

    selected = select_symbol_anomalies(comparisons)

    assert [item.group["symbol"] for item in selected] == ["7203", "6758"]
    assert [item.metric_name for item in selected] == [
        "top_of_book_depth",
        "quoted_spread_bps",
    ]


def test_select_symbol_anomalies_can_include_normal_watchlist_rows() -> None:
    comparisons = (
        _comparison("quoted_spread_bps", "7203", status="normal", z_score=0.4),
        _comparison("quoted_spread_bps", "6758", status="normal", z_score=0.2),
    )

    selected = select_symbol_anomalies(
        comparisons,
        options=SymbolAnomalyPageOptions(include_normal=True, max_symbols=1),
    )

    assert len(selected) == 1
    assert selected[0].group["symbol"] == "7203"


def test_build_symbol_anomaly_page_renders_metric_table_with_scope_and_help() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison(
            "quoted_spread_bps",
            "7203",
            status="alert",
            z_score=2.9,
            empirical_tail=0.01,
            time_bucket="AMO",
        ),
    )

    page = build_symbol_anomaly_page(comparisons, definitions.docs())

    assert page is not None
    assert page.title == "Symbol Anomalies"
    assert len(page.html_blocks) == 1
    assert page.html_blocks[0].title == "Anomaly Detail Panel"
    assert "data-symbol-anomaly-explorer" in page.html_blocks[0].body_html
    assert 'role="status"' in page.html_blocks[0].body_html
    assert 'aria-live="polite"' in page.html_blocks[0].body_html
    assert 'role="region" aria-labelledby="symbol-anomaly-list-title"' in page.html_blocks[0].body_html
    assert 'id="symbol-anomaly-list-title"' in page.html_blocks[0].body_html
    assert 'id="symbol-anomaly-list-description"' in page.html_blocks[0].body_html
    assert 'role="region" aria-labelledby="symbol-anomaly-detail-title"' in page.html_blocks[0].body_html
    assert 'id="symbol-anomaly-detail-title"' in page.html_blocks[0].body_html
    assert 'id="symbol-anomaly-detail-panel"' in page.html_blocks[0].body_html
    assert 'data-symbol-anomaly-index="0"' in page.html_blocks[0].body_html
    assert 'aria-controls="symbol-anomaly-detail-panel"' in page.html_blocks[0].body_html
    assert 'aria-pressed="false"' in page.html_blocks[0].body_html
    assert 'aria-label="Select anomaly 7203 Quoted Spread status Alert"' in page.html_blocks[0].body_html
    assert 'class="symbol-anomaly-explorer__left explorer-panel"' in page.html_blocks[0].body_html
    assert "Anomaly List" in page.html_blocks[0].body_html
    assert "Selected Anomaly Detail" in page.html_blocks[0].body_html
    assert '"detail_anchor":"symbol-detail-7203-' in page.html_blocks[0].body_html
    assert "7203" in page.html_blocks[0].body_html
    assert len(page.metric_tables) == 1
    table = page.metric_tables[0]
    assert table.title == "Top symbol-level anomalies"
    assert "already-computed comparison facts" in table.help_text
    assert len(table.rows) == 1
    assert table.rows[0].metric.name == "quoted_spread_bps"
    assert table.rows[0].status == "alert"
    assert "Symbol: 7203" in table.rows[0].group_text
    assert "symbol=7203" not in table.rows[0].group_text
    assert "AM opening auction" in table.rows[0].group_text


def test_symbol_anomaly_explorer_uses_deterministic_default_selection_order() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison("quoted_spread_bps", "6758", status="watch", z_score=1.5, empirical_tail=0.08),
        _comparison("quoted_spread_bps", "7203", status="alert", z_score=2.8, empirical_tail=0.01),
    )

    page = build_symbol_anomaly_page(comparisons, definitions.docs())

    assert page is not None
    explorer_html = page.html_blocks[0].body_html
    first_idx = explorer_html.index('data-symbol-anomaly-index="0"')
    second_idx = explorer_html.index('data-symbol-anomaly-index="1"')
    first_symbol_idx = explorer_html.index("7203")
    second_symbol_idx = explorer_html.index("6758")
    assert first_idx < second_idx
    assert first_symbol_idx < second_symbol_idx


def test_build_symbol_anomaly_page_returns_none_without_symbol_rows() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison(
            "quoted_spread_bps",
            None,
            status="alert",
            z_score=2.9,
            empirical_tail=0.01,
        ),
    )

    assert build_symbol_anomaly_page(comparisons, definitions.docs()) is None


def test_market_report_skips_symbol_page_by_default() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Intraday Detail",
    ]


def test_market_report_includes_symbol_page_when_explicitly_enabled() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Symbol Anomalies",
        "Intraday Detail",
    ]


def test_market_report_symbol_page_can_be_disabled() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=False,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Intraday Detail",
    ]


def test_build_symbol_detail_pages_renders_existing_symbol_series_only() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison(
            "quoted_spread_bps",
            "7203",
            status="alert",
            z_score=2.9,
            empirical_tail=0.01,
        ),
        _comparison(
            "volume",
            "6758",
            status="alert",
            z_score=2.2,
            empirical_tail=0.02,
        ),
    )
    current_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation("quoted_spread_bps", "7203", "AMO", 17.8),
                _observation("quoted_spread_bps", "7203", "09:00-09:05", 16.9),
                _observation("quoted_spread_bps", "8306", "AMO", 10.1),
            ),
        ),
    )

    pages = build_symbol_detail_pages(
        comparisons,
        current_series,
        definitions.docs(),
    )

    assert [page.title for page in pages] == ["Symbol 7203 Detail"]
    page = pages[0]
    assert len(page.time_series_charts) == 1
    assert len(page.heatmaps) == 0
    assert page.time_series_charts[0].title == "Quoted Spread intraday time-bucket trend for symbol 7203"
    assert page.time_series_charts[0].metric.name == "quoted_spread_bps"
    assert page.time_series_charts[0].x_axis_label == "Intraday time bucket"
    assert [point.time_bucket_text for point in page.time_series_charts[0].points] == [
        "AM opening auction",
        "09:00–09:05",
    ]
    assert all("symbol 7203" in component.title for component in page.time_series_charts)


def test_build_symbol_detail_pages_can_opt_into_heatmaps() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison(
            "quoted_spread_bps",
            "7203",
            status="alert",
            z_score=2.9,
            empirical_tail=0.01,
        ),
    )
    current_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation("quoted_spread_bps", "7203", "AMO", 17.8),
                _observation("quoted_spread_bps", "7203", "09:00-09:05", 16.9),
            ),
        ),
    )

    pages = build_symbol_detail_pages(
        comparisons,
        current_series,
        definitions.docs(),
        options=SymbolDetailPageOptions(include_heatmaps=True),
    )

    assert [page.title for page in pages] == ["Symbol 7203 Detail"]
    assert len(pages[0].time_series_charts) == 1
    assert len(pages[0].heatmaps) == 1
    assert all("symbol 7203" in component.title for component in (*pages[0].time_series_charts, *pages[0].heatmaps))


def test_build_symbol_detail_pages_can_limit_and_disable_rows() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),
        _comparison("volume", "6758", status="alert", z_score=2.2),
    )
    current_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation("quoted_spread_bps", "7203", "AMO", 17.8),
                _observation("quoted_spread_bps", "6758", "AMO", 11.1),
            ),
        ),
    )

    disabled = build_symbol_detail_pages(
        comparisons,
        current_series,
        definitions.docs(),
        options=SymbolDetailPageOptions(max_symbols=0),
    )
    limited = build_symbol_detail_pages(
        comparisons,
        current_series,
        definitions.docs(),
        options=SymbolDetailPageOptions(max_symbols=1, max_chart_points=1),
    )

    assert disabled == ()
    assert [page.title for page in limited] == ["Symbol 7203 Detail"]
    assert len(limited[0].time_series_charts[0].points) == 1


def test_build_symbol_detail_pages_assign_stable_page_anchors() -> None:
    definitions = build_default_registry()
    pages = build_symbol_detail_pages(
        (_comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),),
        (
            _series(
                "quoted_spread_bps",
                (_observation("quoted_spread_bps", "7203", "AMO", 17.8),),
            ),
        ),
        definitions.docs(),
    )

    assert pages[0].anchor_id == symbol_detail_anchor_id("7203")
    assert pages[0].anchor_id.startswith("symbol-detail-7203-")


def test_build_symbol_detail_index_block_links_only_emitted_detail_pages() -> None:
    definitions = build_default_registry()
    comparisons = (
        _comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),
        _comparison("volume", "6758", status="alert", z_score=2.2),
    )
    detail_pages = build_symbol_detail_pages(
        comparisons,
        (
            _series(
                "quoted_spread_bps",
                (_observation("quoted_spread_bps", "7203", "AMO", 17.8),),
            ),
        ),
        definitions.docs(),
    )

    block = build_symbol_detail_index_block(
        comparisons,
        detail_pages,
        definitions.docs(),
    )

    assert block is not None
    assert block.title == "Symbol Detail Index"
    assert "1 symbol detail page selected from the anomaly ranking." in block.body_html
    assert f'href="#{symbol_detail_anchor_id("7203")}"' in block.body_html
    assert "Symbol 7203 Detail" in block.body_html
    assert "Quoted Spread" in block.body_html
    assert "6758" not in block.body_html


def test_build_symbol_detail_index_block_can_be_disabled_by_row_limit() -> None:
    definitions = build_default_registry()
    detail_pages = build_symbol_detail_pages(
        (_comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),),
        (
            _series(
                "quoted_spread_bps",
                (_observation("quoted_spread_bps", "7203", "AMO", 17.8),),
            ),
        ),
        definitions.docs(),
    )

    block = build_symbol_detail_index_block(
        (_comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),),
        detail_pages,
        definitions.docs(),
        options=SymbolDetailIndexOptions(max_symbols=0),
    )

    assert block is None


def test_build_symbol_detail_pages_returns_empty_without_symbol_series() -> None:
    definitions = build_default_registry()
    comparisons = (_comparison("quoted_spread_bps", "7203", status="alert", z_score=2.9),)

    pages = build_symbol_detail_pages(
        comparisons,
        current_series=(),
        metric_definitions=definitions.docs(),
    )

    assert pages == ()


def test_market_report_includes_symbol_detail_pages_when_symbol_series_exist() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )
    symbol_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation("quoted_spread_bps", "7203", "AMO", 17.8),
                _observation("quoted_spread_bps", "7203", "09:00-09:05", 16.9),
            ),
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Intraday Detail",
    ]

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
            include_symbol_detail_pages=True,
            include_symbol_detail_index=True,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Symbol Anomalies",
        "Symbol 7203 Detail",
        "Intraday Detail",
    ]


def test_market_report_adds_symbol_detail_index_when_detail_pages_exist() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )
    symbol_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation("quoted_spread_bps", "7203", "AMO", 17.8),
                _observation("quoted_spread_bps", "7203", "09:00-09:05", 16.9),
            ),
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
            include_symbol_detail_pages=True,
            include_symbol_detail_index=True,
        ),
    )
    symbol_page = document.pages[1]
    detail_page = document.pages[2]
    html = render_report(document)

    assert symbol_page.title == "Symbol Anomalies"
    assert [block.title for block in symbol_page.html_blocks] == [
        "Anomaly Detail Panel",
        "Symbol Detail Index",
    ]
    assert detail_page.anchor_id == symbol_detail_anchor_id("7203")
    assert f'id="{detail_page.anchor_id}"' in html
    assert f'href="#{detail_page.anchor_id}"' in html
    assert "data-symbol-anomaly-explorer" in html
    assert "data-symbol-anomaly-detail" in html
    assert "data-symbol-anomaly-spec" in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-controls="symbol-anomaly-detail-panel"' in html
    assert 'aria-pressed="false"' in html
    assert 'id="symbol-anomaly-detail-panel"' in html
    assert 'role="region" aria-labelledby="symbol-anomaly-list-title"' in html
    assert 'role="region" aria-labelledby="symbol-anomaly-detail-title"' in html
    assert 'button.setAttribute("aria-pressed", buttonIndex === index ? "true" : "false");' in html
    assert 'aria-label="Select anomaly 7203 Quoted Spread status Alert"' in html
    assert ".symbol-anomaly-explorer__row:focus-visible" in html
    assert ".symbol-anomaly-explorer__rows {" in html
    assert ".symbol-anomaly-explorer__detail-item {" in html
    assert "padding-bottom: 6px;" in html
    assert ".explorer-panel {" in html
    assert "box-shadow: 0 3px 10px rgba(16, 39, 66, 0.06);" in html
    assert ".explorer-panel__subtitle {" in html
    assert "font-size: 12px;" in html
    assert ".symbol-anomaly-explorer__detail-value {" in html
    assert "font-size: 12px;" in html
    assert "Open detail page" in html


def test_market_report_symbol_detail_index_can_be_disabled() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
    )
    symbol_series = (
        _series(
            "quoted_spread_bps",
            (_observation("quoted_spread_bps", "7203", "AMO", 17.8),),
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
            include_symbol_detail_pages=True,
            include_symbol_detail_index=False,
        ),
    )

    assert document.pages[1].title == "Symbol Anomalies"
    assert [block.title for block in document.pages[1].html_blocks] == ["Anomaly Detail Panel"]


def test_market_report_symbol_detail_pages_can_be_disabled() -> None:
    definitions = build_default_registry()
    comparison = _comparison(
        "quoted_spread_bps",
        "7203",
        status="alert",
        z_score=2.9,
    )
    symbol_series = (
        _series(
            "quoted_spread_bps",
            (_observation("quoted_spread_bps", "7203", "AMO", 17.8),),
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
            include_symbol_detail_pages=False,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Symbol Anomalies",
        "Intraday Detail",
    ]


def test_market_report_uses_custom_symbol_group_keys_for_summary_and_details() -> None:
    definitions = build_default_registry()
    comparison = _comparison_with_group(
        "quoted_spread_bps",
        {"market_segment": "Prime", "client_symbol": "ABC123"},
        status="alert",
        z_score=2.9,
        empirical_tail=0.01,
    )
    symbol_series = (
        _series(
            "quoted_spread_bps",
            (
                _observation_with_group(
                    "quoted_spread_bps",
                    {"market_segment": "Prime", "client_symbol": "ABC123"},
                    "AMO",
                    17.8,
                ),
            ),
        ),
    )

    without_custom_keys = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(include_metric_definitions_appendix=False),
    )
    with_custom_keys = build_market_monitor_report(
        MarketReportInput(
            metric_definitions={
                "quoted_spread_bps": definitions.get("quoted_spread_bps"),
            },
            current_series=(),
            comparisons=(comparison,),
            symbol_series=symbol_series,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=True,
            include_symbol_detail_pages=True,
            symbol_group_keys=("client_symbol",),
        ),
    )

    assert [page.title for page in without_custom_keys.pages] == [
        "Market Summary",
        "Sector, Segment, and Market-Cap Drilldowns",
        "Intraday Detail",
    ]
    assert [page.title for page in with_custom_keys.pages] == [
        "Market Summary",
        "Symbol Anomalies",
        "Symbol ABC123 Detail",
        "Intraday Detail",
    ]
    assert "Client Symbol: ABC123" in (with_custom_keys.pages[1].metric_tables[0].rows[0].group_text)


def test_symbol_anomaly_options_validate_inputs() -> None:
    with pytest.raises(ValueError, match="max_symbols must be non-negative"):
        SymbolAnomalyPageOptions(max_symbols=-1)

    with pytest.raises(ValueError, match="symbol_group_keys must not contain"):
        SymbolAnomalyPageOptions(symbol_group_keys=("symbol", " "))

    with pytest.raises(ValueError, match="max_symbols must be non-negative"):
        SymbolDetailPageOptions(max_symbols=-1)

    with pytest.raises(ValueError, match="title_template may only use"):
        SymbolDetailPageOptions(title_template="Symbol {ticker} Detail")

    with pytest.raises(ValueError, match="max_chart_points must be non-negative"):
        SymbolDetailPageOptions(max_chart_points=-1)


def _observation(
    metric_name: str,
    symbol: str,
    time_bucket: str,
    value: float | int,
) -> MetricObservation:
    return _observation_with_group(
        metric_name,
        {
            "market_segment": "Prime",
            "market_cap_bucket": "Large",
            "symbol": symbol,
        },
        time_bucket,
        value,
    )


def _observation_with_group(
    metric_name: str,
    group: dict[str, str],
    time_bucket: str,
    value: float | int,
) -> MetricObservation:
    return MetricObservation(
        metric_name=metric_name,
        date=date(2026, 5, 21),
        time_bucket=time_bucket,
        group=group,
        value=value,
        metadata={"fixture": "symbol_detail_test"},
    )


def _series(
    metric_name: str,
    observations: tuple[MetricObservation, ...],
) -> MetricTimeSeries:
    return MetricTimeSeries.from_observations(
        observations,
        metric_name=metric_name,
        metadata={"role": "current"},
    )


def _comparison(
    metric_name: str,
    symbol: str | None,
    *,
    status: str,
    value: float = 12.0,
    reference_value: float = 10.0,
    z_score: float | None = None,
    empirical_tail: float | None = None,
    time_bucket: str = "09:00-09:05",
) -> MetricComparison:
    group = {"market_segment": "Prime"}
    if symbol is not None:
        group["symbol"] = symbol
    return _comparison_with_group(
        metric_name,
        group,
        status=status,
        value=value,
        reference_value=reference_value,
        z_score=z_score,
        empirical_tail=empirical_tail,
        time_bucket=time_bucket,
    )


def _comparison_with_group(
    metric_name: str,
    group: dict[str, str],
    *,
    status: str,
    value: float = 12.0,
    reference_value: float = 10.0,
    z_score: float | None = None,
    empirical_tail: float | None = None,
    time_bucket: str = "09:00-09:05",
) -> MetricComparison:
    return MetricComparison(
        metric_name=metric_name,
        value=value,
        reference_value=reference_value,
        change_abs=value - reference_value,
        change_pct=(value - reference_value) / reference_value,
        z_score=z_score,
        percentile=None,
        status=status,
        group=group,
        date=date(2026, 5, 21),
        time_bucket=time_bucket,
        reference_sample_size=30,
        comparison_confidence="normal",
        comparison_method="robust",
        empirical_adverse_tail_probability=empirical_tail,
    )
