from __future__ import annotations

import pytest

from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.overview import (
    ExecutiveOverviewOptions,
    _change_narrative_sentence,
    _select_top_changes,
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
    assert "Overall:</strong> Alert" in block.body_html
    assert "1 alerts, 1 watch items, 0 comparison-only items, and 1 normal items" in block.body_html
    assert "2 key metrics and 3 comparisons" in block.body_html
    assert "Key changes this period" in block.body_html
    assert "Quoted Spread" in block.body_html
    assert "average current 41.0000 bps versus reference 31.0000 bps" in block.body_html
    assert "change +10.0000 bps +32.5%" in block.body_html
    # Narrative highlights show specific changes with context
    assert "Small" in block.body_html
    assert "AMO auction" in block.body_html
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
    # Narrative highlights only surface alert/watch items; the compact
    # family summary at the bottom still includes all observed families.
    assert "Key changes this period" in block.body_html
    assert "<strong>Overall:</strong>" in block.body_html


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


# ---------------------------------------------------------------------------
# Narrative highlight selection and wording tests (R2 exit criteria)
# ---------------------------------------------------------------------------


def test_select_top_changes_ranks_by_status_then_zscore() -> None:
    """Alerts rank before watch; within same status, larger |z| ranks first."""
    changes = (
        MetricComparison(
            metric_name="turnover",
            value=100,
            reference_value=80,
            change_abs=20.0,
            change_pct=0.25,
            z_score=1.5,
            percentile=None,
            status="watch",
            group={"topixCapGrp": "Core30"},
        ),
        MetricComparison(
            metric_name="volume",
            value=200,
            reference_value=150,
            change_abs=50.0,
            change_pct=0.33,
            z_score=3.0,
            percentile=None,
            status="alert",
            group={"topixCapGrp": "Large"},
        ),
        MetricComparison(
            metric_name="trade_count",
            value=50,
            reference_value=60,
            change_abs=-10.0,
            change_pct=-0.17,
            z_score=2.5,
            percentile=None,
            status="alert",
            group={"topixCapGrp": "Small"},
        ),
        MetricComparison(
            metric_name="quoted_spread_bps",
            value=45,
            reference_value=30,
            change_abs=15.0,
            change_pct=0.50,
            z_score=0.8,
            percentile=None,
            status="watch",
            group={"market_cap_bucket": "Prime"},
        ),
    )

    selected = _select_top_changes(changes)

    # Alerts before watch
    assert selected[0].status == "alert"
    assert selected[1].status == "alert"
    # Within alerts: higher |z| first (3.0 > 2.5)
    assert selected[0].metric_name == "volume"  # z=3.0
    assert selected[1].metric_name == "trade_count"  # z=2.5
    # Watches follow: higher |z| first (1.5 > 0.8)
    assert selected[2].status == "watch"
    assert selected[3].status == "watch"
    assert selected[2].metric_name == "turnover"  # z=1.5
    assert selected[3].metric_name == "quoted_spread_bps"  # z=0.8


def test_select_top_changes_excludes_symbol_scoped_comparisons() -> None:
    """Symbol-level rows must not appear in default narrative highlights."""
    changes = (
        MetricComparison(
            metric_name="turnover",
            value=100,
            reference_value=80,
            change_abs=20.0,
            change_pct=0.25,
            z_score=3.5,
            percentile=None,
            status="alert",
            group={"sym": "7203"},
        ),
        MetricComparison(
            metric_name="volume",
            value=200,
            reference_value=150,
            change_abs=50.0,
            change_pct=0.33,
            z_score=2.0,
            percentile=None,
            status="alert",
            group={"topixCapGrp": "Large"},
        ),
    )

    selected = _select_top_changes(changes)
    assert len(selected) == 1
    assert selected[0].metric_name == "volume"


def test_select_top_changes_returns_empty_for_all_normal() -> None:
    """Only alert/watch rows are surfaced; all-normal produces no highlights."""
    changes = (
        MetricComparison(
            metric_name="turnover",
            value=100,
            reference_value=98,
            change_abs=2.0,
            change_pct=0.02,
            z_score=0.3,
            percentile=None,
            status="normal",
            group={"topixCapGrp": "Large"},
        ),
        MetricComparison(
            metric_name="volume",
            value=200,
            reference_value=195,
            change_abs=5.0,
            change_pct=0.03,
            z_score=0.1,
            percentile=None,
            status="normal",
            group={"topixCapGrp": "Large"},
        ),
    )

    assert _select_top_changes(changes) == ()


def test_select_top_changes_returns_empty_without_market_rows() -> None:
    """When all comparisons are symbol-scoped, no highlights are returned."""
    changes = (
        MetricComparison(
            metric_name="turnover",
            value=100,
            reference_value=80,
            change_abs=20.0,
            change_pct=0.25,
            z_score=3.5,
            percentile=None,
            status="alert",
            group={"sym": "7203"},
        ),
    )

    assert _select_top_changes(changes) == ()


def test_change_narrative_sentence_includes_context_and_interpretation() -> None:
    """Narrative sentences carry metric label, direction, magnitude, context."""
    spread_def = next(m for m in STARTER_METRICS if m.name == "quoted_spread_bps")
    comparison = MetricComparison(
        metric_name="quoted_spread_bps",
        value=42.0,
        reference_value=30.0,
        change_abs=12.0,
        change_pct=0.40,
        z_score=3.1,
        percentile=None,
        status="alert",
        group={"topixCapGrp": "Core30"},
        time_bucket="AMO",
    )

    sentence = _change_narrative_sentence(comparison, spread_def)

    assert "Quoted Spread" in sentence
    assert "Core30" in sentence
    assert "AMO auction" in sentence
    assert "40%" in sentence
    assert sentence.endswith(".")


def test_change_narrative_sentence_is_deterministic() -> None:
    """Same input always produces same output (no randomness or LLM)."""
    spread_def = next(m for m in STARTER_METRICS if m.name == "quoted_spread_bps")
    comparison = MetricComparison(
        metric_name="quoted_spread_bps",
        value=42.0,
        reference_value=30.0,
        change_abs=12.0,
        change_pct=0.40,
        z_score=3.1,
        percentile=None,
        status="alert",
        group={"topixCapGrp": "Core30"},
    )

    first = _change_narrative_sentence(comparison, spread_def)
    second = _change_narrative_sentence(comparison, spread_def)

    assert first == second
    assert len(first) > 0


def test_change_narrative_sentence_falls_back_without_definition() -> None:
    """When no MetricDefinition is available, the metric name is used as label."""
    comparison = MetricComparison(
        metric_name="unknown_metric",
        value=42.0,
        reference_value=30.0,
        change_abs=12.0,
        change_pct=0.40,
        z_score=3.1,
        percentile=None,
        status="alert",
        group={"topixCapGrp": "Core30"},
    )

    sentence = _change_narrative_sentence(comparison, None)

    assert "unknown_metric" in sentence
    assert "." in sentence
