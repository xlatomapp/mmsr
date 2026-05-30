from datetime import date

import pytest

from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import ReportDocument
from mmsr.report.drilldowns import (
    DEFAULT_DRILLDOWN_GROUP_KEYS,
    DrilldownReportPageOptions,
    DrilldownSelectionOptions,
    build_drilldown_report_page,
    drilldown_scope_key,
    select_drilldown_comparisons,
)
from mmsr.report.render_html import render_report


def _comparison(
    metric_name: str,
    group: dict[str, str],
    *,
    status: str = "watch",
    z_score: float | None = None,
    change_pct: float | None = None,
) -> MetricComparison:
    return MetricComparison(
        metric_name=metric_name,
        value=12.0,
        reference_value=10.0,
        change_abs=2.0,
        change_pct=change_pct,
        z_score=z_score,
        percentile=None,
        status=status,
        group=group,
        date=date(2026, 5, 25),
        time_bucket="AMO",
    )


def test_drilldown_options_default_to_sector_segment_and_market_cap_keys() -> None:
    options = DrilldownSelectionOptions()

    assert options.group_keys == DEFAULT_DRILLDOWN_GROUP_KEYS
    assert "market_cap_bucket" in options.group_keys
    assert "segment" in options.group_keys
    assert "sector" in options.group_keys
    assert not options.include_symbol_scoped


def test_select_drilldown_comparisons_filters_existing_group_facts() -> None:
    comparisons = [
        _comparison(
            "quoted_spread_bps",
            {"market_cap_bucket": "large"},
            status="watch",
            z_score=2.0,
        ),
        _comparison(
            "turnover",
            {"sector": "technology"},
            status="alert",
            z_score=4.0,
        ),
        _comparison(
            "volume",
            {"symbol": "7203", "sector": "autos"},
            status="alert",
            z_score=9.0,
        ),
        _comparison("trade_count", {"venue": "TSE"}, status="alert", z_score=8.0),
    ]

    selected = select_drilldown_comparisons(comparisons)

    assert [comparison.metric_name for comparison in selected] == [
        "turnover",
        "quoted_spread_bps",
    ]
    assert selected[0].group == {"sector": "technology"}
    assert selected[1].group == {"market_cap_bucket": "large"}


def test_select_drilldown_comparisons_can_include_symbol_scoped_rows() -> None:
    symbol_row = _comparison(
        "volume",
        {"symbol": "7203", "sector": "autos"},
        status="alert",
        z_score=9.0,
    )

    selected = select_drilldown_comparisons(
        [symbol_row],
        options=DrilldownSelectionOptions(include_symbol_scoped=True),
    )

    assert selected == (symbol_row,)


def test_select_drilldown_comparisons_supports_custom_keys_statuses_and_limits() -> None:
    comparisons = [
        _comparison(
            "quoted_spread_bps",
            {"client_segment": "retail"},
            status="normal",
            z_score=0.2,
        ),
        _comparison(
            "volume",
            {"client_segment": "institutional"},
            status="watch",
            z_score=1.5,
        ),
        _comparison(
            "turnover",
            {"sector": "technology"},
            status="alert",
            z_score=2.5,
        ),
    ]

    selected = select_drilldown_comparisons(
        comparisons,
        options=DrilldownSelectionOptions(
            group_keys=("client_segment",),
            statuses=("watch",),
            max_rows=1,
        ),
    )

    assert [comparison.metric_name for comparison in selected] == ["volume"]


def test_drilldown_scope_key_preserves_configured_dimension_order() -> None:
    comparison = _comparison(
        "turnover",
        {
            "sector": "technology",
            "market_cap_bucket": "large",
            "segment": "Prime",
        },
    )

    scope = drilldown_scope_key(
        comparison,
        group_keys=("segment", "market_cap_bucket", "sector"),
    )

    assert scope == (
        ("segment", "Prime"),
        ("market_cap_bucket", "large"),
        ("sector", "technology"),
    )


def test_drilldown_options_validate_keys_statuses_and_limits() -> None:
    with pytest.raises(ValueError, match="group_keys must not be empty"):
        DrilldownSelectionOptions(group_keys=())

    with pytest.raises(ValueError, match="group_keys must not contain"):
        DrilldownSelectionOptions(group_keys=("sector", " "))

    with pytest.raises(ValueError, match="symbol_group_keys must not be empty"):
        DrilldownSelectionOptions(symbol_group_keys=())

    with pytest.raises(ValueError, match="max_rows must be non-negative"):
        DrilldownSelectionOptions(max_rows=-1)

    with pytest.raises(ValueError, match="statuses must not be empty"):
        DrilldownSelectionOptions(statuses=())

    with pytest.raises(ValueError, match="statuses must not contain"):
        DrilldownSelectionOptions(statuses=("watch", " "))


QUOTED_SPREAD_BPS = next(metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps")
TURNOVER = next(metric for metric in STARTER_METRICS if metric.name == "turnover")
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")
TOP_OF_BOOK_DEPTH = next(metric for metric in STARTER_METRICS if metric.name == "top_of_book_depth")


def test_build_drilldown_report_page_formats_rows_with_metric_help() -> None:
    comparisons = [
        _comparison(
            "quoted_spread_bps",
            {"market_cap_bucket": "large", "sector": "technology"},
            status="watch",
            z_score=1.8,
            change_pct=0.12,
        ),
        _comparison(
            "turnover",
            {"segment": "Prime", "sector": "autos"},
            status="alert",
            z_score=3.1,
            change_pct=0.25,
        ),
        _comparison(
            "top_of_book_depth",
            {"segment": "Prime", "sector": "autos"},
            status="watch",
            z_score=1.9,
            change_pct=-0.10,
        ),
        _comparison(
            "volume",
            {"symbol": "7203", "sector": "autos"},
            status="alert",
            z_score=8.0,
        ),
    ]

    page = build_drilldown_report_page(
        comparisons,
        [QUOTED_SPREAD_BPS, TURNOVER, TOP_OF_BOOK_DEPTH, VOLUME],
    )

    assert page is not None
    assert page.title == "Sector, Segment, and Market-Cap Drilldowns"
    assert len(page.html_blocks) == 2
    assert page.html_blocks[0].title == "Group Delta Overview"
    assert "drilldown-delta-bars" in page.html_blocks[0].body_html
    assert page.html_blocks[1].title == "Metric Explorer & Group Analysis"
    assert "data-drilldown-matrix-spec" in page.html_blocks[1].body_html
    assert "data-drilldown-heatmap" in page.html_blocks[1].body_html
    assert 'aria-label="Liquidity group-metric heatmap"' in page.html_blocks[1].body_html
    assert "data-drilldown-trend" in page.html_blocks[1].body_html
    assert 'aria-label="Selected group daily trend chart"' in page.html_blocks[1].body_html
    assert "Cells show mean % change" in page.html_blocks[1].body_html
    assert "Cell format: mean % change (z-score reference)." in page.html_blocks[1].body_html
    # Heatmaps require at least 2 groups per metric — sparse test data
    # may produce 0 heatmaps. Integration tests cover the populated case.
    assert isinstance(page.heatmaps, list)
    assert len(page.metric_tables) == 1

    table = page.metric_tables[0]
    assert table.title == "Top group-level drilldowns"
    assert table.help_text is not None
    assert "already-computed comparison facts" in table.help_text
    assert [row.metric.name for row in table.rows] == [
        "turnover",
        "quoted_spread_bps",
        "top_of_book_depth",
    ]
    assert table.rows[0].value_text == "12 JPY"
    assert table.rows[0].reference_text == "10 JPY"
    assert table.rows[0].change_text == "change +2 JPY +25.0%"
    assert table.rows[0].group_text == (
        "Date: 2026-05-25, Intraday bucket: AM opening auction, Segment: Prime, Sector: autos"
    )
    assert table.rows[1].group_text == (
        "Date: 2026-05-25, Intraday bucket: AM opening auction, Market cap bucket: Large cap, Sector: technology"
    )
    assert "Formula:" in table.rows[0].help_text()


def test_drilldown_heatmaps_use_uncapped_selection_even_when_table_is_limited() -> None:
    comparisons = [
        _comparison(
            "quoted_spread_bps",
            {"topixCapGrp": "Large"},
            status="alert",
            z_score=4.0,
            change_pct=0.20,
        ),
        _comparison(
            "quoted_spread_bps",
            {"topixCapGrp": "Mid"},
            status="watch",
            z_score=1.8,
            change_pct=0.08,
        ),
        _comparison(
            "quoted_spread_bps",
            {"topixCapGrp": "Small"},
            status="watch",
            z_score=1.6,
            change_pct=-0.06,
        ),
    ]

    page = build_drilldown_report_page(
        comparisons,
        [QUOTED_SPREAD_BPS],
        options=DrilldownReportPageOptions(
            selection=DrilldownSelectionOptions(max_rows=1),
        ),
    )

    assert page is not None
    assert len(page.metric_tables[0].rows) == 1
    assert len(page.heatmaps) == 0
    assert len(page.html_blocks) == 1


def test_drilldown_matrix_uses_liquidity_metrics_and_change_pct_fallback() -> None:
    comparisons = [
        _comparison(
            "quoted_spread_bps",
            {"topixCapGrp": "Large"},
            status="watch",
            z_score=None,
            change_pct=0.05,
        ),
        _comparison(
            "quoted_spread_bps",
            {"topixCapGrp": "Mid"},
            status="watch",
            z_score=None,
            change_pct=-0.03,
        ),
        _comparison(
            "top_of_book_depth",
            {"topixCapGrp": "Large"},
            status="watch",
            z_score=None,
            change_pct=0.04,
        ),
        _comparison(
            "top_of_book_depth",
            {"topixCapGrp": "Mid"},
            status="watch",
            z_score=None,
            change_pct=-0.02,
        ),
        _comparison(
            "turnover",
            {"topixCapGrp": "Large"},
            status="watch",
            z_score=1.5,
            change_pct=0.10,
        ),
    ]

    page = build_drilldown_report_page(
        comparisons,
        [QUOTED_SPREAD_BPS, TOP_OF_BOOK_DEPTH, TURNOVER],
    )

    assert page is not None
    explorer_html = page.html_blocks[1].body_html
    assert "liquidity metrics" in explorer_html
    assert "z-score in parentheses for reference" in explorer_html
    assert "Quoted Spread" in explorer_html
    assert "Top-of-Book Depth" in explorer_html
    assert "Turnover" not in explorer_html


def test_drilldown_report_page_renders_as_html_metric_table() -> None:
    page = build_drilldown_report_page(
        [
            _comparison(
                "quoted_spread_bps",
                {"market_cap_bucket": "small"},
                status="alert",
                z_score=2.4,
            )
        ],
        [QUOTED_SPREAD_BPS],
    )

    assert page is not None
    html = render_report(
        ReportDocument(
            title="MMSR",
            pages=[page],
        )
    )

    assert "Sector, Segment, and Market-Cap Drilldowns" in html
    assert "Top group-level drilldowns" in html
    assert "Market cap bucket: Small cap" in html
    assert "metric-info" in html
    assert "Formula:" in html


def test_build_drilldown_report_page_supports_custom_selection_options() -> None:
    page = build_drilldown_report_page(
        [
            _comparison(
                "volume",
                {"client_segment": "retail", "sector": "technology"},
                status="normal",
                z_score=0.1,
            ),
            _comparison(
                "turnover",
                {"sector": "technology"},
                status="alert",
                z_score=4.0,
            ),
        ],
        [VOLUME, TURNOVER],
        options=DrilldownReportPageOptions(
            title="Client Segment Drilldowns",
            table_title="Client rows",
            help_text="Client-defined group diagnostics.",
            selection=DrilldownSelectionOptions(
                group_keys=("client_segment",),
                statuses=("normal",),
                max_rows=1,
            ),
        ),
    )

    assert page is not None
    assert page.title == "Client Segment Drilldowns"
    table = page.metric_tables[0]
    assert table.title == "Client rows"
    assert table.help_text == "Client-defined group diagnostics."
    assert [row.metric.name for row in table.rows] == ["volume"]
    assert table.rows[0].group_text == (
        "Date: 2026-05-25, Intraday bucket: AM opening auction, Client Segment: retail, Sector: technology"
    )


def test_build_drilldown_report_page_returns_none_without_selected_rows() -> None:
    page = build_drilldown_report_page(
        [_comparison("volume", {"venue": "TSE"}, status="alert")],
        [VOLUME],
    )

    assert page is None


def test_build_drilldown_report_page_requires_metric_definitions() -> None:
    with pytest.raises(ValueError, match="quoted_spread_bps"):
        build_drilldown_report_page(
            [
                _comparison(
                    "quoted_spread_bps",
                    {"market_cap_bucket": "small"},
                    status="alert",
                )
            ],
            [VOLUME],
        )


def test_drilldown_report_page_options_validate_text() -> None:
    with pytest.raises(ValueError, match="title"):
        DrilldownReportPageOptions(title=" ")

    with pytest.raises(ValueError, match="table_title"):
        DrilldownReportPageOptions(table_title=" ")

    with pytest.raises(ValueError, match="help_text"):
        DrilldownReportPageOptions(help_text=" ")
