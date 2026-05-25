from mmsr.analysis.commentary import (
    CommentaryFact,
    TemplateCommentaryEngine,
    commentary_facts_from_comparisons,
    section_summary_fact_from_comparisons,
)


def test_template_commentary_generates_alert_text() -> None:
    engine = TemplateCommentaryEngine()
    comments = engine.generate(
        [
            CommentaryFact(
                metric_label="Quoted Spread",
                group={"market_cap_bucket": "Small"},
                value_text="42.1 bps",
                reference_text="31.4 bps",
                change_text="+34.1%",
                z_score=2.6,
                status="alert",
                direction_word="higher",
            )
        ]
    )
    assert comments
    assert "Quoted Spread" in comments[0]
    assert "z-score 2.6" in comments[0]


def test_template_commentary_includes_grounded_caveats() -> None:
    engine = TemplateCommentaryEngine()
    comments = engine.generate(
        [
            CommentaryFact(
                metric_label="+1s Reversion",
                group={"venue": "ODX"},
                value_text="+2.7500 bps",
                reference_text=None,
                change_text=None,
                z_score=None,
                status="alert",
                direction_word="positive",
                caveats=["Low confidence: trade_count 20 < 100"],
            )
        ]
    )

    assert "Caveats: Low confidence: trade_count 20 < 100" in comments[0]


from mmsr.metrics.results import MetricComparison
from mmsr.metrics.starter_definitions import STARTER_METRICS


def test_commentary_facts_from_comparisons_use_metric_docs_and_caveats() -> None:
    quoted_spread = next(m for m in STARTER_METRICS if m.name == "quoted_spread_bps")
    facts = commentary_facts_from_comparisons(
        [
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=42.1,
                reference_value=31.4,
                change_abs=10.7,
                change_pct=10.7 / 31.4,
                z_score=None,
                percentile=None,
                status="watch",
                group={"market_cap_bucket": "Small"},
                reference_sample_size=12,
                comparison_confidence="weak",
                comparison_method="robust",
                metadata={"reference_observation_unit": "trading_day"},
            )
        ],
        metric_definitions=[quoted_spread],
    )

    assert facts[0].metric_label == "Quoted Spread"
    assert facts[0].value_text == "42.1000 bps"
    assert facts[0].reference_text == "31.4000 bps"
    assert facts[0].change_text == "change +10.7000 bps +34.1%"
    assert facts[0].direction_word == "higher"
    assert facts[0].status == "watch"
    assert "Low confidence: 12 reference observations" in facts[0].caveats[0]
    assert "Reference observation unit: trading day." in facts[0].caveats


def test_template_commentary_handles_comparison_only_without_statistical_score() -> None:
    engine = TemplateCommentaryEngine()
    comments = engine.generate(
        [
            CommentaryFact(
                metric_label="Volume",
                group={"sector": "Banks"},
                value_text="1,000 shares",
                reference_text="900 shares",
                change_text="change +100 shares +11.1%",
                z_score=None,
                status="comparison_only",
                direction_word="higher",
                caveats=["One reference observation; z-score is intentionally omitted."],
            )
        ]
    )

    assert comments == [
        "Volume comparison for Sector: Banks: current 1,000 shares versus "
        "reference 900 shares (change +100 shares +11.1%); statistical score "
        "not shown. Caveats: One reference observation; z-score is intentionally "
        "omitted."
    ]


def test_section_summary_fact_counts_statuses_and_renders_headline_first() -> None:
    fact = section_summary_fact_from_comparisons(
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
        scope_label="all comparisons",
    )

    comments = TemplateCommentaryEngine().generate(
        [
            CommentaryFact(
                metric_label="Volume",
                group={},
                value_text="1,000 shares",
                reference_text="900 shares",
                change_text="change +100 shares +11.1%",
                z_score=0.2,
                status="normal",
                direction_word="higher",
            ),
            fact,
        ]
    )

    assert fact.fact_type == "section_summary"
    assert fact.status == "alert"
    assert comments[0] == (
        "Liquidity Summary headline: 1 alert, 0 watch items, "
        "0 comparison-only items, and 1 normal item across 2 comparisons "
        "in all comparisons."
    )


def test_commentary_facts_from_comparisons_can_limit_ordered_facts() -> None:
    facts = commentary_facts_from_comparisons(
        [
            MetricComparison(
                metric_name="volume",
                value=100,
                reference_value=100,
                change_abs=0,
                change_pct=0,
                z_score=0.0,
                percentile=None,
                status="normal",
            ),
            MetricComparison(
                metric_name="quoted_spread_bps",
                value=50,
                reference_value=20,
                change_abs=30,
                change_pct=1.5,
                z_score=2.7,
                percentile=None,
                status="alert",
            ),
        ],
        metric_definitions=STARTER_METRICS,
        max_facts=1,
    )

    assert len(facts) == 1
    assert facts[0].metric_label == "Quoted Spread"
