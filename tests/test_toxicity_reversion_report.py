from datetime import date

import pytest

from mmsr.metrics import build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.report import (
    MarketReportInput,
    MarketReportOptions,
    ToxicityReversionPageOptions,
    build_market_monitor_report,
    build_toxicity_reversion_page,
)


def _reversion_series(
    metric_name: str,
    horizon: str,
    values: dict[str, float],
    *,
    bucket: str = "09:00-09:05",
    sector: str = "Autos",
    context_sort_order: int | None = None,
) -> MetricTimeSeries:
    return MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name=metric_name,
                date=date(2026, 5, 25),
                time_bucket=bucket,
                group={"venue": venue, "horizon": horizon, "sector": sector},
                value=value,
                metadata={
                    "trade_count": 250,
                    "notional": 500_000_000.0,
                    **(
                        {}
                        if context_sort_order is None
                        else {"context_sort_order": context_sort_order}
                    ),
                },
            )
            for venue, value in values.items()
        ],
        metric_name=metric_name,
    )


def test_toxicity_reversion_page_builds_horizon_curve_by_venue() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"SBIJ": 0.45, "TSE": 0.10},
        ),
        _reversion_series(
            "primary_quote_reversion_1s_bps",
            "1s",
            {"SBIJ": 1.35, "TSE": 0.55},
        ),
    )

    page = build_toxicity_reversion_page(
        series,
        definitions,
        options=ToxicityReversionPageOptions(
            max_charts=1,
            venue_order=("TSE", "SBIJ"),
            horizon_order=("10ms", "1s"),
        ),
    )

    assert page is not None
    assert page.title == "Cross-Venue Toxicity"
    assert len(page.time_series_charts) == 1
    chart = page.time_series_charts[0]
    assert chart.x_axis_label == "Horizon"
    assert chart.resolved_y_axis_label() == "Reversion (bps)"
    assert chart.svg_legend_labels() == ("TSE", "SBIJ")
    assert [point.x_text for point in chart.points] == ["10ms", "10ms", "1s", "1s"]
    assert [point.series_text for point in chart.points] == [
        "TSE",
        "SBIJ",
        "TSE",
        "SBIJ",
    ]
    assert chart.metric.label == "Cross-Venue Reversion Curve"
    assert "kdb query has already applied" in chart.metric_help_text()
    assert page.commentary_blocks


def test_toxicity_reversion_page_adds_reversion_comparison_table() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.40},
        ),
    )
    comparisons = (
        MetricComparison(
            metric_name="primary_quote_reversion_10ms_bps",
            value=0.40,
            reference_value=0.15,
            change_abs=0.25,
            change_pct=1.6666666667,
            z_score=2.1,
            percentile=0.97,
            status="alert",
            date=date(2026, 5, 25),
            time_bucket="09:00-09:05",
            group={"venue": "TSE", "horizon": "10ms", "sector": "Autos"},
            reference_sample_size=30,
            comparison_confidence="normal",
            comparison_method="robust",
        ),
        MetricComparison(
            metric_name="turnover",
            value=1_000_000,
            reference_value=900_000,
            change_abs=100_000,
            change_pct=0.1111111111,
            z_score=None,
            percentile=None,
            status="normal",
            date=date(2026, 5, 25),
            time_bucket="09:00-09:05",
            group={},
        ),
    )

    page = build_toxicity_reversion_page(
        series,
        definitions,
        comparisons=comparisons,
        options=ToxicityReversionPageOptions(max_comparison_rows=1),
    )

    assert page is not None
    assert len(page.metric_tables) == 1
    table = page.metric_tables[0]
    assert table.title == "Reversion current versus reference"
    assert "future-mid denominator convention" in (table.help_text or "")
    assert len(table.rows) == 1
    row = table.rows[0]
    assert row.metric.name == "primary_quote_reversion_10ms_bps"
    assert row.status == "alert"
    assert row.value_text == "0.4000 bps"
    assert row.reference_text == "0.1500 bps"
    assert "change +0.2500 bps" in (row.change_text or "")
    assert "Venue: TSE" in (row.group_text or "")
    assert "Horizon: 10ms" in (row.group_text or "")


def test_toxicity_reversion_page_returns_none_without_reversion_series() -> None:
    registry = build_default_registry()
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="turnover",
                date=date(2026, 5, 25),
                time_bucket="09:00-09:05",
                group={},
                value=1_000_000,
            )
        ],
        metric_name="turnover",
    )

    assert (
        build_toxicity_reversion_page(
            (series,),
            {definition.name: definition for definition in registry.docs()},
        )
        is None
    )


def test_toxicity_reversion_page_ranks_contexts_by_positive_reversion() -> None:
    registry = build_default_registry()
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
            bucket="09:00-09:05",
        ),
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.25},
            bucket="09:05-09:10",
        ),
    )

    page = build_toxicity_reversion_page(
        series,
        {definition.name: definition for definition in registry.docs()},
        options=ToxicityReversionPageOptions(max_charts=1),
    )

    assert page is not None
    assert len(page.time_series_charts) == 1
    assert "09:05" in page.time_series_charts[0].title


def test_toxicity_reversion_page_can_rank_contexts_chronologically() -> None:
    registry = build_default_registry()
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
            bucket="09:00-09:05",
        ),
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.25},
            bucket="09:05-09:10",
        ),
    )

    page = build_toxicity_reversion_page(
        series,
        {definition.name: definition for definition in registry.docs()},
        options=ToxicityReversionPageOptions(
            max_charts=1,
            context_ranking="chronological",
        ),
    )

    assert page is not None
    assert len(page.time_series_charts) == 1
    assert "09:00" in page.time_series_charts[0].title


def test_toxicity_reversion_page_can_rank_contexts_by_upstream_sort_order() -> None:
    registry = build_default_registry()
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 1.50},
            bucket="09:00-09:05",
            context_sort_order=20,
        ),
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
            bucket="09:05-09:10",
            context_sort_order=5,
        ),
    )

    page = build_toxicity_reversion_page(
        series,
        {definition.name: definition for definition in registry.docs()},
        options=ToxicityReversionPageOptions(
            max_charts=1,
            context_ranking="context_sort_order",
        ),
    )

    assert page is not None
    assert len(page.time_series_charts) == 1
    assert "09:05" in page.time_series_charts[0].title
    assert "Context sort order: 5" in page.time_series_charts[0].points[0].metadata_text


def test_toxicity_reversion_page_can_rank_contexts_by_lowest_confidence() -> None:
    registry = build_default_registry()
    high_confidence = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 25),
                time_bucket="09:00-09:05",
                group={"venue": "TSE", "horizon": "10ms", "sector": "Autos"},
                value=0.40,
                metadata={"trade_count": 250, "notional": 500_000_000.0},
            )
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )
    low_confidence = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 25),
                time_bucket="09:05-09:10",
                group={"venue": "TSE", "horizon": "10ms", "sector": "Autos"},
                value=0.05,
                metadata={"trade_count": 10, "notional": 1_000_000.0},
            )
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    page = build_toxicity_reversion_page(
        (high_confidence, low_confidence),
        {definition.name: definition for definition in registry.docs()},
        options=ToxicityReversionPageOptions(
            max_charts=1,
            context_ranking="lowest_confidence",
        ),
    )

    assert page is not None
    assert len(page.time_series_charts) == 1
    assert "09:05" in page.time_series_charts[0].title
    assert "Low confidence" in page.time_series_charts[0].points[0].metadata_text


def test_toxicity_reversion_page_requires_metric_definitions() -> None:
    series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
        ),
    )

    with pytest.raises(ValueError, match="metric definitions"):
        build_toxicity_reversion_page(series, {})


def test_toxicity_reversion_page_rejects_unknown_context_ranking() -> None:
    with pytest.raises(ValueError, match="context_ranking"):
        ToxicityReversionPageOptions(
            context_ranking="not-a-ranking"  # type: ignore[arg-type]
        )


def test_market_report_inserts_toxicity_reversion_page_from_current_series() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    current_series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10, "SBIJ": 0.20},
        ),
    )
    comparisons = (
        MetricComparison(
            metric_name="primary_quote_reversion_10ms_bps",
            value=0.10,
            reference_value=0.05,
            change_abs=0.05,
            change_pct=1.0,
            z_score=None,
            percentile=None,
            status="normal",
            date=date(2026, 5, 25),
            time_bucket="09:00-09:05",
            group={},
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=comparisons,
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=False,
            include_symbol_detail_pages=False,
            include_drilldown_page=False,
        ),
    )

    assert [page.title for page in document.pages] == [
        "Market Summary",
        "Cross-Venue Toxicity",
        "Intraday Detail",
    ]
    assert document.pages[1].time_series_charts[0].x_axis_label == "Horizon"
    assert len(document.pages[1].metric_tables) == 1
    assert document.pages[1].metric_tables[0].rows[0].metric.name == (
        "primary_quote_reversion_10ms_bps"
    )
    assert document.pages[2].time_series_charts == []
    assert document.pages[2].heatmaps == []


def test_market_report_can_keep_toxicity_reversion_metrics_in_detail_page() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    current_series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10, "SBIJ": 0.20},
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=(),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=False,
            include_symbol_detail_pages=False,
            include_drilldown_page=False,
            include_toxicity_reversion_metrics_in_detail_page=True,
        ),
    )

    assert document.pages[1].title == "Cross-Venue Toxicity"
    assert document.pages[2].title == "Intraday Detail"
    assert len(document.pages[2].time_series_charts) == 1
    assert (
        document.pages[2].time_series_charts[0].metric.name
        == "primary_quote_reversion_10ms_bps"
    )


def test_market_report_passes_toxicity_context_ranking_option() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    current_series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
            bucket="09:00-09:05",
        ),
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.35},
            bucket="09:05-09:10",
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=(),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=False,
            include_symbol_detail_pages=False,
            include_drilldown_page=False,
            toxicity_reversion_context_ranking="chronological",
            max_toxicity_reversion_charts=1,
        ),
    )

    assert document.pages[1].title == "Cross-Venue Toxicity"
    assert "09:00" in document.pages[1].time_series_charts[0].title


def test_market_report_passes_toxicity_context_sort_order_ranking_option() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    current_series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.35},
            bucket="09:00-09:05",
            context_sort_order=10,
        ),
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
            bucket="09:05-09:10",
            context_sort_order=1,
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=(),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_symbol_anomaly_page=False,
            include_symbol_detail_pages=False,
            include_drilldown_page=False,
            toxicity_reversion_context_ranking="context_sort_order",
            max_toxicity_reversion_charts=1,
        ),
    )

    assert document.pages[1].title == "Cross-Venue Toxicity"
    assert "09:05" in document.pages[1].time_series_charts[0].title


def test_market_report_toxicity_reversion_page_can_be_disabled() -> None:
    registry = build_default_registry()
    definitions = {definition.name: definition for definition in registry.docs()}
    current_series = (
        _reversion_series(
            "primary_quote_reversion_10ms_bps",
            "10ms",
            {"TSE": 0.10},
        ),
    )

    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=(),
        ),
        options=MarketReportOptions(
            include_metric_definitions_appendix=False,
            include_toxicity_reversion_page=False,
        ),
    )

    assert "Cross-Venue Toxicity" not in [page.title for page in document.pages]
    assert len(document.pages[-1].time_series_charts) == 1
    assert (
        document.pages[-1].time_series_charts[0].metric.name
        == "primary_quote_reversion_10ms_bps"
    )
