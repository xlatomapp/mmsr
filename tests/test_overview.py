from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.overview import build_executive_market_overview_block


DEFINITIONS = {
    metric.name: metric
    for metric in STARTER_METRICS
    if metric.name in {"volume", "quoted_spread_bps", "top_of_book_depth"}
}


def test_executive_overview_surfaces_activity_and_liquidity_families() -> None:
    block = build_executive_market_overview_block(
        [
            MetricComparison(
                metric_name="volume",
                value=1_200_000,
                reference_value=1_000_000,
                change_abs=200_000,
                change_pct=0.2,
                z_score=1.1,
                percentile=None,
                status="watch",
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
            ),
            MetricComparison(
                metric_name="top_of_book_depth",
                value=9_500,
                reference_value=14_500,
                change_abs=-5_000,
                change_pct=-5_000 / 14_500,
                z_score=-2.1,
                percentile=None,
                status="watch",
            ),
        ],
        DEFINITIONS,
    )

    assert (
        'aria-label="Market activity and displayed liquidity summary"'
        in block.body_html
    )
    assert "<strong>Market activity:</strong> Watch" in block.body_html
    assert "1 observed metrics (Volume)" in block.body_html
    assert (
        "Leading signal: Volume average current 1,200,000.0000 shares"
        in block.body_html
    )
    assert "<strong>Displayed liquidity:</strong> Alert" in block.body_html
    assert "2 observed metrics (Quoted Spread, Top-of-Book Depth)" in block.body_html
    assert (
        "Leading signal: Quoted Spread average current 42.1000 bps"
        in block.body_html
    )


def test_executive_overview_omits_family_summary_without_default_family_metrics() -> None:
    block = build_executive_market_overview_block(
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
        {"quoted_spread_bps": DEFINITIONS["quoted_spread_bps"]},
    )

    assert "<strong>Displayed liquidity:</strong>" in block.body_html
    assert "<strong>Market activity:</strong>" not in block.body_html
