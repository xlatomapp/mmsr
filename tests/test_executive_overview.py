from __future__ import annotations

import pytest

from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.overview import (
    ExecutiveOverviewOptions,
    build_executive_market_overview_block,
)

QUOTED_SPREAD_BPS = next(metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps")
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_executive_market_overview_summarizes_status_and_key_metrics() -> None:
    block = build_executive_market_overview_block(
        [
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=42.0,
                reference_value=30.0,
                change_abs=12.0,
                change_pct=0.4,
                z_score=3.1,
                percentile=None,
                status="alert",
                group={"market_cap_bucket": "Small"},
                time_bucket="AMO",
            ),
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=40.0,
                reference_value=32.0,
                change_abs=8.0,
                change_pct=0.25,
                z_score=2.0,
                percentile=None,
                status="watch",
                group={"market_cap_bucket": "Large"},
                time_bucket="09:00-09:05",
            ),
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
        ],
        [QUOTED_SPREAD_BPS, VOLUME],
    )

    assert block.title == "Executive Market Overview"
    assert block.help_text is not None
    assert "Overall status:</strong> Alert" in block.body_html
    assert "1 alerts, 1 watch items, 0 comparison-only items, and 1 normal items" in block.body_html
    assert "2 key metrics and 3 comparisons" in block.body_html
    assert "Quoted Spread" in block.body_html
    assert "average current 41.0000 bps versus reference 31.0000 bps" in block.body_html
    assert "change +10.0000 bps +32.5%" in block.body_html
    assert "Intraday bucket: AM opening auction" in block.body_html
    assert "Market cap bucket: Small cap" in block.body_html
    assert "time_bucket=" not in block.body_html
    assert "market_cap_bucket=" not in block.body_html


def test_executive_market_overview_limits_metric_summaries() -> None:
    block = build_executive_market_overview_block(
        [
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=42.0,
                reference_value=30.0,
                change_abs=12.0,
                change_pct=0.4,
                z_score=3.1,
                percentile=None,
                status="alert",
            ),
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
        ],
        [QUOTED_SPREAD_BPS, VOLUME],
        options=ExecutiveOverviewOptions(max_metric_summaries=1),
    )

    assert "Quoted Spread" in block.body_html
    assert "Volume" not in block.body_html
    assert "1 additional metric summaries are available" in block.body_html


def test_executive_market_overview_requires_metric_definitions() -> None:
    with pytest.raises(ValueError, match="quoted_spread_bps"):
        build_executive_market_overview_block(
            [
                MetricComparison(
                    metric_name="quoted_spread_bps",
                    value=42.0,
                    reference_value=30.0,
                    change_abs=12.0,
                    change_pct=0.4,
                    z_score=3.1,
                    percentile=None,
                    status="alert",
                )
            ],
            [VOLUME],
        )


def test_executive_overview_options_validate_text_and_limits() -> None:
    with pytest.raises(ValueError, match="title"):
        ExecutiveOverviewOptions(title=" ")

    with pytest.raises(ValueError, match="help_text"):
        ExecutiveOverviewOptions(help_text=" ")

    with pytest.raises(ValueError, match="max_metric_summaries"):
        ExecutiveOverviewOptions(max_metric_summaries=-1)
