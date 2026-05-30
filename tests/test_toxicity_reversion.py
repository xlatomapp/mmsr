from datetime import date

import pytest

from mmsr.analysis.commentary import TemplateCommentaryEngine
from mmsr.config.models import ToxicityConfidenceConfig
from mmsr.metrics import MetricTimeSeries, build_default_registry
from mmsr.metrics.results import MetricObservation
from mmsr.visuals.toxicity import (
    ReversionCurveConversionError,
    ReversionCurvePoint,
    flag_reversion_curve_confidence,
    render_reversion_curve_placeholder,
    reversion_commentary_facts_from_curve_points,
    reversion_curve_points_from_timeseries,
    reversion_curve_points_from_timeseries_collection,
)


def _reversion_observation(
    *,
    horizon: str,
    venue: str,
    value: float | None,
    sym: str = "7203",
    metric_name: str = "primary_quote_reversion_10ms_bps",
) -> MetricObservation:
    return MetricObservation(
        metric_name=metric_name,
        date=date(2026, 5, 24),
        time_bucket="09:00-09:05",
        group={"venue": venue, "horizon": horizon, "sym": sym},
        value=value,
        metadata={
            "trade_count": 120,
            "notional": 250_000_000.0,
            "horizon_sort_order": 2 if horizon == "100ms" else 1 if horizon == "10ms" else 4,
            "context_sort_order": 9,
            "low_confidence": False,
        },
    )


def test_primary_quote_reversion_metrics_are_registered() -> None:
    registry = build_default_registry()

    assert "primary_quote_reversion_10ms_bps" in registry.names()
    assert "primary_quote_reversion_10s_bps" in registry.names()

    metric = registry.get("primary_quote_reversion_10ms_bps")
    assert metric.label == "+10ms Reversion"
    assert metric.category == "Toxicity"
    assert "primary_mid" in metric.formula
    assert "/ primary_mid[t + horizon]" in metric.formula
    assert "reversion" in metric.help_text().lower()


def test_reversion_curve_placeholder_renders_venues_and_horizons() -> None:
    html = render_reversion_curve_placeholder(
        [
            ReversionCurvePoint("TSE", "10ms", 0.25),
            ReversionCurvePoint("SBIJ", "1s", 1.75),
            ReversionCurvePoint("ODX", "10s", -0.50),
        ]
    )

    assert "reversion-curve" in html
    assert "TSE" in html
    assert "SBIJ" in html
    assert "ODX" in html
    assert "10ms" in html
    assert "Reversion (bps)" in html


def test_reversion_curve_points_from_timeseries_are_ordered_by_horizon() -> None:
    series = MetricTimeSeries.from_observations(
        [
            _reversion_observation(horizon="1s", venue="SBIJ", value=1.50),
            _reversion_observation(horizon="100ms", venue="TSE", value=0.20),
            _reversion_observation(horizon="10ms", venue="TSE", value=0.10),
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    points = reversion_curve_points_from_timeseries(
        series,
        venue_order=("TSE", "SBIJ"),
    )

    assert [(point.venue, point.horizon) for point in points] == [
        ("TSE", "10ms"),
        ("TSE", "100ms"),
        ("SBIJ", "1s"),
    ]
    assert points[0].reversion_bps == 0.10
    assert points[0].date == date(2026, 5, 24)
    assert points[0].time_bucket == "09:00-09:05"
    assert points[0].group == {"sym": "7203"}
    assert points[0].trade_count == 120
    assert points[0].notional == 250_000_000.0
    assert points[0].horizon_sort_order == 1
    assert points[0].context_sort_order == 9
    assert points[0].low_confidence is False


def test_reversion_curve_points_use_output_horizon_sort_order_when_present() -> None:
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 24),
                time_bucket="09:00-09:05",
                group={"venue": "TSE", "horizon": "10s"},
                value=1.0,
                metadata={"horizon_sort_order": 1},
            ),
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 24),
                time_bucket="09:00-09:05",
                group={"venue": "TSE", "horizon": "10ms"},
                value=2.0,
                metadata={"horizon_sort_order": 2},
            ),
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    points = reversion_curve_points_from_timeseries(series)

    assert [point.horizon for point in points] == ["10s", "10ms"]
    assert [point.horizon_sort_order for point in points] == [1, 2]


def test_reversion_curve_points_reject_invalid_context_sort_order_metadata() -> None:
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 24),
                time_bucket="09:00-09:05",
                group={"venue": "TSE", "horizon": "10ms"},
                value=1.0,
                metadata={"context_sort_order": "first"},
            )
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    with pytest.raises(ReversionCurveConversionError, match="context_sort_order"):
        reversion_curve_points_from_timeseries(series)


def test_reversion_curve_points_from_series_collection_combines_horizons() -> None:
    ten_ms = MetricTimeSeries.from_observations(
        [_reversion_observation(horizon="10ms", venue="TSE", value=0.10)],
        metric_name="primary_quote_reversion_10ms_bps",
    )
    one_second = MetricTimeSeries.from_observations(
        [
            _reversion_observation(
                horizon="1s",
                venue="TSE",
                value=1.25,
                metric_name="primary_quote_reversion_1s_bps",
            )
        ],
        metric_name="primary_quote_reversion_1s_bps",
    )

    points = reversion_curve_points_from_timeseries_collection(
        [one_second, ten_ms],
        horizon_order=("10ms", "1s"),
    )

    assert [(point.horizon, point.reversion_bps) for point in points] == [
        ("10ms", 0.10),
        ("1s", 1.25),
    ]


def test_reversion_curve_points_require_venue_and_horizon_groups() -> None:
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="primary_quote_reversion_10ms_bps",
                date=date(2026, 5, 24),
                time_bucket=None,
                group={"venue": "TSE"},
                value=0.10,
            )
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    with pytest.raises(ReversionCurveConversionError, match="horizon"):
        reversion_curve_points_from_timeseries(series)


def test_reversion_curve_points_reject_missing_values() -> None:
    series = MetricTimeSeries.from_observations(
        [_reversion_observation(horizon="10ms", venue="TSE", value=None)],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    with pytest.raises(ReversionCurveConversionError, match="no value"):
        reversion_curve_points_from_timeseries(series)


def test_reversion_curve_points_apply_confidence_thresholds() -> None:
    series = MetricTimeSeries.from_observations(
        [
            _reversion_observation(
                horizon="10ms",
                venue="SBIJ",
                value=0.25,
            ),
            _reversion_observation(
                horizon="100ms",
                venue="ODX",
                value=0.40,
            ),
        ],
        metric_name="primary_quote_reversion_10ms_bps",
    )

    points = reversion_curve_points_from_timeseries(
        series,
        confidence=ToxicityConfidenceConfig(
            min_trade_count=150,
            min_notional=300_000_000,
        ),
    )

    assert all(point.low_confidence for point in points)
    assert points[0].confidence_reasons == (
        "trade_count 120 < 150",
        "notional 250000000 < 300000000",
    )


def test_reversion_curve_confidence_flags_missing_sample_metadata() -> None:
    point = ReversionCurvePoint("TSE", "10ms", 0.10)

    (flagged,) = flag_reversion_curve_confidence(
        [point],
        ToxicityConfidenceConfig(min_trade_count=100, min_notional=1),
    )

    assert flagged.low_confidence is True
    assert flagged.confidence_reasons == ("missing trade_count", "missing notional")


def test_reversion_curve_confidence_preserves_upstream_low_confidence_flag() -> None:
    point = ReversionCurvePoint(
        "TSE",
        "10ms",
        0.10,
        trade_count=500,
        notional=500_000_000,
        low_confidence=True,
    )

    (flagged,) = flag_reversion_curve_confidence(
        [point],
        ToxicityConfidenceConfig(min_trade_count=100, min_notional=1),
    )

    assert flagged.low_confidence is True
    assert flagged.confidence_reasons == ()


def test_reversion_curve_placeholder_surfaces_low_confidence_rows() -> None:
    html = render_reversion_curve_placeholder(
        [
            ReversionCurvePoint(
                "SBIJ",
                "10ms",
                0.25,
                low_confidence=True,
                confidence_reasons=("trade_count 50 < 100",),
            )
        ]
    )

    assert "low-confidence" in html
    assert "Low confidence: trade_count 50 &lt; 100" in html
    assert "Confidence" in html


def test_reversion_commentary_facts_highlight_positive_reversion() -> None:
    facts = reversion_commentary_facts_from_curve_points(
        [
            ReversionCurvePoint("TSE", "10ms", 0.25),
            ReversionCurvePoint("ODX", "1s", 2.75, time_bucket="09:00-09:05"),
            ReversionCurvePoint("SBIJ", "100ms", -0.50),
        ],
        max_headline_points=2,
    )

    assert [fact.metric_label for fact in facts] == [
        "+1s Reversion",
        "+10ms Reversion",
    ]
    assert facts[0].status == "alert"
    assert facts[0].direction_word == "positive"
    assert facts[0].value_text == "+2.7500 bps"
    assert facts[0].group == {
        "venue": "ODX",
        "horizon": "1s",
        "time_bucket": "09:00-09:05",
    }


def test_reversion_commentary_facts_surface_low_confidence_caveats() -> None:
    facts = reversion_commentary_facts_from_curve_points(
        [
            ReversionCurvePoint(
                "ODX",
                "1s",
                2.75,
                low_confidence=True,
                confidence_reasons=("trade_count 20 < 100",),
            ),
            ReversionCurvePoint(
                "SBIJ",
                "10ms",
                0.10,
                low_confidence=True,
                confidence_reasons=("missing notional",),
            ),
        ],
        max_headline_points=1,
    )

    comments = TemplateCommentaryEngine().generate(list(facts), max_comments=5)

    assert facts[0].caveats == ["Low confidence: trade_count 20 < 100"]
    assert any("Caveats: Low confidence: trade_count 20 < 100" in line for line in comments)
    assert any("+10ms Reversion sample size" in line for line in comments)
    assert any("missing notional" in line for line in comments)


def test_reversion_commentary_facts_validate_thresholds() -> None:
    with pytest.raises(ValueError, match="alert_threshold_bps"):
        reversion_commentary_facts_from_curve_points(
            [ReversionCurvePoint("TSE", "10ms", 0.10)],
            watch_threshold_bps=2.0,
            alert_threshold_bps=1.0,
        )
