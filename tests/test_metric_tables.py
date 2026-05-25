from datetime import date

import pytest

from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import (
    MetricTable,
    MetricTableRow,
    ReportDocument,
    ReportPage,
)
from mmsr.report.metric_docs import (
    append_metric_definitions_appendix,
    collect_metric_definitions_from_pages,
)
from mmsr.report.render_html import render_metric_table, render_report
from mmsr.report.sections import build_comparison_metric_table


QUOTED_SPREAD_BPS = next(
    metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps"
)
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_metric_table_renders_rows_with_metric_help() -> None:
    table = MetricTable(
        title="Liquidity Table",
        rows=[
            MetricTableRow(
                metric=QUOTED_SPREAD_BPS,
                group_text="market_cap_bucket=Small",
                value_text="42.1000 bps",
                reference_text="31.4000 bps",
                change_text="change +10.7000 bps +34.1%",
                status="alert",
            )
        ],
        help_text="Current versus reference metrics.",
    )

    html = render_metric_table(table)

    assert "Liquidity Table" in html
    assert "Current versus reference metrics." in html
    assert "Quoted Spread" in html
    assert "market_cap_bucket=Small" in html
    assert "42.1000 bps" in html
    assert "31.4000 bps" in html
    assert "change +10.7000 bps +34.1%" in html
    assert "metric-table__row--alert" in html
    assert "metric-info" in html
    assert "Formula:" in html


def test_report_renders_metric_tables() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Liquidity",
                metric_tables=[
                    MetricTable(
                        title="Metric rows",
                        rows=[
                            MetricTableRow(
                                metric=VOLUME,
                                value_text="1,000",
                                status="normal",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    html = render_report(document)

    assert "Metric rows" in html
    assert "Volume" in html
    assert "metric-table__row--normal" in html
    assert "metric-info" in html


def test_build_comparison_metric_table_formats_and_orders_rows() -> None:
    table = build_comparison_metric_table(
        "Comparison rows",
        [
            MetricComparison(
                metric_name="volume",
                value=1_000,
                reference_value=900,
                change_abs=100,
                change_pct=100 / 900,
                z_score=0.2,
                percentile=None,
                status="normal",
                group={"sector": "Banks"},
            ),
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=42.1,
                reference_value=31.4,
                change_abs=10.7,
                change_pct=10.7 / 31.4,
                z_score=2.6,
                percentile=None,
                status="alert",
                group={"market_cap_bucket": "Small"},
                date=date(2026, 5, 22),
                time_bucket="09:00-09:05",
            ),
        ],
        metric_definitions=[QUOTED_SPREAD_BPS, VOLUME],
    )

    assert table.title == "Comparison rows"
    assert [row.metric.name for row in table.rows] == [
        "quoted_spread_bps",
        "volume",
    ]
    assert table.rows[0].value_text == "42.1000 bps"
    assert table.rows[0].reference_text == "31.4000 bps"
    assert table.rows[0].change_text == "change +10.7000 bps +34.1%"
    assert table.rows[0].status == "alert"
    assert table.rows[0].group_text == (
        "Date: 2026-05-22, Intraday bucket: 09:00–09:05, Market cap bucket: Small cap"
    )


def test_build_comparison_metric_table_validates_inputs() -> None:
    with pytest.raises(ValueError, match="title"):
        build_comparison_metric_table(
            " ",
            [],
            metric_definitions=[VOLUME],
        )

    with pytest.raises(ValueError, match="max_rows"):
        build_comparison_metric_table(
            "Comparison rows",
            [],
            metric_definitions=[VOLUME],
            max_rows=-1,
        )

    with pytest.raises(ValueError, match="quoted_spread_bps"):
        build_comparison_metric_table(
            "Comparison rows",
            [
                MetricComparison(
                    metric_name="quoted_spread_bps",
                    value=42.1,
                    reference_value=None,
                    change_abs=None,
                    change_pct=None,
                    z_score=None,
                    percentile=None,
                    status="normal",
                )
            ],
            metric_definitions=[VOLUME],
        )


def test_metric_table_title_validation() -> None:
    with pytest.raises(ValueError, match="title"):
        MetricTable(title=" ", rows=[])


def test_metric_definitions_appendix_collects_table_rows() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Liquidity",
                metric_tables=[
                    MetricTable(
                        title="Metric rows",
                        rows=[
                            MetricTableRow(
                                metric=QUOTED_SPREAD_BPS,
                                value_text="12.4 bps",
                            )
                        ],
                    )
                ],
            )
        ],
    )

    definitions = collect_metric_definitions_from_pages(document.pages)
    enriched = append_metric_definitions_appendix(document)

    assert [definition.name for definition in definitions] == ["quoted_spread_bps"]
    assert len(enriched.pages) == 2
    assert "Quoted Spread" in render_report(enriched)
