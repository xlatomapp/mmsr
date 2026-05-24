import pytest

from mmsr.analysis.commentary import CommentaryFact
from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import ReportDocument
from mmsr.report.render_html import render_report
from mmsr.report.sections import ComparisonSectionOptions, build_comparison_report_page


QUOTED_SPREAD_BPS = next(
    metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps"
)
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_build_comparison_report_page_creates_cards_and_commentary() -> None:
    page = build_comparison_report_page(
        "Liquidity Summary",
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
            ),
        ],
        metric_definitions=[QUOTED_SPREAD_BPS, VOLUME],
    )

    assert page.title == "Liquidity Summary"
    assert [card.metric.name for card in page.metric_cards] == [
        "quoted_spread_bps",
        "volume",
    ]
    assert page.metric_cards[0].value_text == "42.1000 bps"
    assert page.metric_cards[0].reference_text == (
        "31.4000 bps (change +10.7000 bps +34.1%)"
    )
    assert "Formula:" in page.metric_cards[0].help_text()
    assert len(page.commentary_blocks) == 1
    assert page.commentary_blocks[0].title == "Commentary"
    assert page.commentary_blocks[0].comments[0] == (
        "Liquidity Summary headline: 1 alert, 0 watch items, "
        "0 comparison-only items, and 1 normal item across 2 comparisons "
        "in all comparisons."
    )
    assert "Quoted Spread was higher" in page.commentary_blocks[0].comments[1]


def test_build_comparison_report_page_accepts_precomputed_commentary_facts() -> None:
    page = build_comparison_report_page(
        "Activity",
        [
            MetricComparison(
                metric_name="volume",
                value=1_000,
                reference_value=900,
                change_abs=100,
                change_pct=100 / 900,
                z_score=None,
                percentile=None,
                status="comparison_only",
            )
        ],
        metric_definitions=[VOLUME],
        commentary_facts=[
            CommentaryFact(
                metric_label="Volume",
                group={"sector": "Banks"},
                value_text="1,000 shares",
                reference_text="900 shares",
                change_text="change +100 shares +11.1%",
                z_score=None,
                status="comparison_only",
                direction_word="higher",
            )
        ],
        options=ComparisonSectionOptions(
            commentary_title="Deterministic Commentary",
            max_metric_cards=1,
            max_comments=1,
        ),
    )

    assert page.commentary_blocks[0].title == "Deterministic Commentary"
    assert page.commentary_blocks[0].comments == [
        "Volume comparison for sector=Banks: current 1,000 shares versus "
        "reference 900 shares (change +100 shares +11.1%); statistical score "
        "not shown."
    ]


def test_build_comparison_report_page_requires_metric_docs_for_cards() -> None:
    with pytest.raises(ValueError, match="quoted_spread_bps"):
        build_comparison_report_page(
            "Missing docs",
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


def test_build_comparison_report_page_validates_limits() -> None:
    with pytest.raises(ValueError, match="max_metric_cards"):
        ComparisonSectionOptions(max_metric_cards=-1)

    with pytest.raises(ValueError, match="max_comments"):
        ComparisonSectionOptions(max_comments=-1)


def test_build_comparison_report_page_can_disable_section_summary() -> None:
    page = build_comparison_report_page(
        "Activity",
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
            )
        ],
        metric_definitions=[VOLUME],
        options=ComparisonSectionOptions(include_section_summary=False),
    )

    assert page.commentary_blocks[0].comments == [
        "Volume was within the normal range for the selected universe."
    ]


def test_comparison_section_options_validate_summary_scope() -> None:
    with pytest.raises(ValueError, match="section_summary_scope_label"):
        ComparisonSectionOptions(section_summary_scope_label=" ")


def test_comparison_report_page_renders_through_html_report() -> None:
    page = build_comparison_report_page(
        "Liquidity Summary",
        [
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=42.1,
                reference_value=31.4,
                change_abs=10.7,
                change_pct=10.7 / 31.4,
                z_score=2.6,
                percentile=None,
                status="alert",
            )
        ],
        metric_definitions=[QUOTED_SPREAD_BPS],
    )
    html = render_report(ReportDocument(title="MMSR Demo", pages=[page]))

    assert "Liquidity Summary" in html
    assert "Quoted Spread" in html
    assert "metric-info" in html
    assert "42.1000 bps" in html
    assert "Quoted Spread was higher" in html
