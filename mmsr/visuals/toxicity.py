"""Toxicity visual helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import date, time
from html import escape
from typing import Any

from mmsr.analysis.commentary import CommentaryFact
from mmsr.config.models import ToxicityConfidenceConfig
from mmsr.metrics.results import MetricObservation, MetricTimeSeries

_DURATION_RE = re.compile(r"^(?P<size>[1-9][0-9]*)(?P<unit>ms|s|m|h)$")
_DURATION_MULTIPLIER_MS = {
    "ms": 1,
    "s": 1_000,
    "m": 60_000,
    "h": 3_600_000,
}


class ReversionCurveConversionError(ValueError):
    """Raised when metric results cannot be converted into curve points."""


@dataclass(frozen=True)
class ReversionCurvePoint:
    """A point in a venue reversion curve.

    ``group`` contains any non-visual grouping dimensions that were present on
    the source observation, such as ``sym``, ``sector``, or ``segment``.
    """

    venue: str
    horizon: str
    reversion_bps: float
    date: date | None = None
    time_bucket: time | str | None = None
    group: dict[str, str] = field(default_factory=dict)
    trade_count: int | None = None
    notional: float | None = None
    low_confidence: bool | None = None
    confidence_reasons: tuple[str, ...] = ()
    horizon_sort_order: int | None = None
    context_sort_order: int | None = None


def reversion_curve_points_from_timeseries(
    series: MetricTimeSeries,
    *,
    venue_order: Sequence[str] | None = None,
    horizon_order: Sequence[str] | None = None,
    confidence: ToxicityConfidenceConfig | None = None,
) -> tuple[ReversionCurvePoint, ...]:
    """Convert one metric time series into ordered reversion curve points.

    Every observation must include ``venue`` and ``horizon`` group values. The
    returned points are sorted by observation context, numeric horizon duration,
    and venue so charts render the x-axis as a true horizon progression rather
    than lexicographic text order.
    """

    ordered = _ordered_points(
        (_point_from_observation(observation) for observation in series),
        venue_order=venue_order,
        horizon_order=horizon_order,
    )
    if confidence is None:
        return ordered
    return flag_reversion_curve_confidence(ordered, confidence)


def reversion_curve_points_from_timeseries_collection(
    series_collection: Iterable[MetricTimeSeries],
    *,
    venue_order: Sequence[str] | None = None,
    horizon_order: Sequence[str] | None = None,
    confidence: ToxicityConfidenceConfig | None = None,
) -> tuple[ReversionCurvePoint, ...]:
    """Convert multiple reversion metric time series into ordered curve points."""

    points: list[ReversionCurvePoint] = []
    for series in series_collection:
        points.extend(_point_from_observation(observation) for observation in series)
    ordered = _ordered_points(
        points,
        venue_order=venue_order,
        horizon_order=horizon_order,
    )
    if confidence is None:
        return ordered
    return flag_reversion_curve_confidence(ordered, confidence)


def flag_reversion_curve_confidence(
    points: Sequence[ReversionCurvePoint],
    confidence: ToxicityConfidenceConfig,
) -> tuple[ReversionCurvePoint, ...]:
    """Apply deterministic sample-size confidence flags to curve points.

    A point is flagged as low confidence when its source sample size is below
    either configured threshold, or when a required sample-size field is absent.
    Any upstream ``low_confidence=True`` marker is preserved.
    """

    return tuple(_point_with_confidence_flag(point, confidence) for point in points)


def reversion_commentary_facts_from_curve_points(
    points: Sequence[ReversionCurvePoint],
    *,
    max_headline_points: int = 3,
    max_low_confidence_warnings: int = 3,
    watch_threshold_bps: float = 0.5,
    alert_threshold_bps: float = 2.0,
) -> tuple[CommentaryFact, ...]:
    """Build deterministic commentary facts for venue reversion curves.

    The headline facts highlight the largest positive primary-quote reversion
    points because positive values indicate future primary-mid movement in the
    aggressive trade direction under the package convention
    ``side * (future_mid - mid_at_trade) / future_mid``. Low-confidence points
    are also surfaced through caveats on headline facts and separate watch-level
    facts for non-headline rows.
    """

    if max_headline_points < 0:
        raise ValueError("max_headline_points must be non-negative")
    if max_low_confidence_warnings < 0:
        raise ValueError("max_low_confidence_warnings must be non-negative")
    if watch_threshold_bps < 0:
        raise ValueError("watch_threshold_bps must be non-negative")
    if alert_threshold_bps < watch_threshold_bps:
        raise ValueError("alert_threshold_bps must be >= watch_threshold_bps")

    headline_points = tuple(
        sorted(
            points,
            key=_headline_commentary_sort_key,
        )[:max_headline_points]
    )
    headline_ids = {_point_identity(point) for point in headline_points}
    facts = [
        _headline_commentary_fact(
            point,
            watch_threshold_bps,
            alert_threshold_bps,
        )
        for point in headline_points
    ]

    low_confidence_points = tuple(
        point
        for point in sorted(points, key=_low_confidence_commentary_sort_key)
        if point.low_confidence and _point_identity(point) not in headline_ids
    )[:max_low_confidence_warnings]
    facts.extend(_low_confidence_commentary_fact(point) for point in low_confidence_points)

    return tuple(facts)


def render_reversion_curve_placeholder(points: Sequence[ReversionCurvePoint]) -> str:
    """Render a simple HTML placeholder for venue reversion curves.

    The intended production visual has horizon progression on the x-axis and
    primary-quote reversion in bps on the y-axis, with one series per venue.
    This HTML fallback keeps tests and offline demos deterministic before a
    charting dependency is selected.
    """
    rows = "".join(_render_reversion_curve_row(point) for point in points)
    return (
        '<table class="reversion-curve">'
        "<thead><tr><th>Venue</th><th>Horizon</th>"
        "<th>Reversion (bps)</th><th>Confidence</th></tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def _render_reversion_curve_row(point: ReversionCurvePoint) -> str:
    row_class = ' class="low-confidence"' if point.low_confidence else ""
    confidence_text = _confidence_text(point)
    return (
        f"<tr{row_class}>"
        f"<td>{escape(point.venue)}</td>"
        f"<td>{escape(point.horizon)}</td>"
        f"<td>{point.reversion_bps:.4f}</td>"
        f"<td>{escape(confidence_text)}</td>"
        "</tr>"
    )


def _confidence_text(point: ReversionCurvePoint) -> str:
    if point.low_confidence:
        if point.confidence_reasons:
            return "Low confidence: " + "; ".join(point.confidence_reasons)
        return "Low confidence"
    return "OK"


def _headline_commentary_fact(
    point: ReversionCurvePoint,
    watch_threshold_bps: float,
    alert_threshold_bps: float,
) -> CommentaryFact:
    return CommentaryFact(
        metric_label=_reversion_metric_label(point.horizon),
        group=_commentary_group(point),
        value_text=f"{point.reversion_bps:+.4f} bps",
        reference_text=None,
        change_text=None,
        z_score=None,
        status=_reversion_status(
            point.reversion_bps,
            watch_threshold_bps=watch_threshold_bps,
            alert_threshold_bps=alert_threshold_bps,
        ),
        direction_word=_reversion_direction_word(point.reversion_bps),
        caveats=_confidence_caveats(point),
    )


def _low_confidence_commentary_fact(point: ReversionCurvePoint) -> CommentaryFact:
    return CommentaryFact(
        metric_label=f"{_reversion_metric_label(point.horizon)} sample size",
        group=_commentary_group(point),
        value_text="low confidence",
        reference_text=None,
        change_text=None,
        z_score=None,
        status="watch",
        direction_word="low confidence",
        caveats=_confidence_caveats(point),
    )


def _headline_commentary_sort_key(
    point: ReversionCurvePoint,
) -> tuple[float, tuple[int, int, str], tuple[int, int, str], str]:
    return (
        -point.reversion_bps,
        _horizon_sort_key(point.horizon, {}, point.horizon_sort_order),
        _ranked_text_sort_key(point.venue, {}),
        repr(sorted(point.group.items())),
    )


def _low_confidence_commentary_sort_key(
    point: ReversionCurvePoint,
) -> tuple[tuple[int, int, str], tuple[int, int, str], str]:
    return (
        _horizon_sort_key(point.horizon, {}, point.horizon_sort_order),
        _ranked_text_sort_key(point.venue, {}),
        repr(sorted(point.group.items())),
    )


def _point_identity(point: ReversionCurvePoint) -> tuple[Any, ...]:
    return (
        point.date,
        point.time_bucket,
        point.venue,
        point.horizon,
        tuple(sorted(point.group.items())),
    )


def _reversion_metric_label(horizon: str) -> str:
    if horizon.startswith("+"):
        return f"{horizon} Reversion"
    return f"+{horizon} Reversion"


def _reversion_status(
    value: float,
    *,
    watch_threshold_bps: float,
    alert_threshold_bps: float,
) -> str:
    if value >= alert_threshold_bps:
        return "alert"
    if value >= watch_threshold_bps:
        return "watch"
    return "normal"


def _reversion_direction_word(value: float) -> str:
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "flat"


def _confidence_caveats(point: ReversionCurvePoint) -> list[str]:
    if not point.low_confidence:
        return []
    if point.confidence_reasons:
        return ["Low confidence: " + "; ".join(point.confidence_reasons)]
    return ["Low confidence: sample-size thresholds were not met"]


def _commentary_group(point: ReversionCurvePoint) -> dict[str, str]:
    group: dict[str, str] = {"venue": point.venue, "horizon": point.horizon}
    if point.time_bucket is not None:
        group["time_bucket"] = str(point.time_bucket)
    for key, value in sorted(point.group.items()):
        group[key] = value
    return group


def _format_threshold_value(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)


def _point_with_confidence_flag(
    point: ReversionCurvePoint,
    confidence: ToxicityConfidenceConfig,
) -> ReversionCurvePoint:
    reasons = list(point.confidence_reasons)

    if point.trade_count is None:
        reasons.append("missing trade_count")
    elif point.trade_count < confidence.min_trade_count:
        reasons.append(f"trade_count {point.trade_count} < {confidence.min_trade_count}")

    if point.notional is None:
        reasons.append("missing notional")
    elif point.notional < confidence.min_notional:
        reasons.append(
            "notional "
            f"{_format_threshold_value(point.notional)} < "
            f"{_format_threshold_value(float(confidence.min_notional))}"
        )

    low_confidence = bool(point.low_confidence) or bool(reasons)
    return replace(
        point,
        low_confidence=low_confidence,
        confidence_reasons=tuple(dict.fromkeys(reasons)),
    )


def _point_from_observation(observation: MetricObservation) -> ReversionCurvePoint:
    venue = _required_group_value(observation, "venue")
    horizon = _required_group_value(observation, "horizon")
    if observation.value is None:
        raise ReversionCurveConversionError(f"observation for venue {venue!r} and horizon {horizon!r} has no value")

    try:
        reversion_bps = float(observation.value)
    except (TypeError, ValueError) as exc:
        raise ReversionCurveConversionError(
            f"observation for venue {venue!r} and horizon {horizon!r} has a non-numeric value"
        ) from exc

    return ReversionCurvePoint(
        venue=venue,
        horizon=horizon,
        reversion_bps=reversion_bps,
        date=observation.date,
        time_bucket=observation.time_bucket,
        group={key: value for key, value in observation.group.items() if key not in {"venue", "horizon"}},
        trade_count=_optional_int_metadata(observation.metadata, "trade_count"),
        notional=_optional_float_metadata(observation.metadata, "notional"),
        horizon_sort_order=_optional_int_metadata(
            observation.metadata,
            "horizon_sort_order",
        ),
        context_sort_order=_optional_int_metadata(
            observation.metadata,
            "context_sort_order",
        ),
        low_confidence=_optional_bool_metadata(observation.metadata, "low_confidence"),
    )


def _ordered_points(
    points: Iterable[ReversionCurvePoint],
    *,
    venue_order: Sequence[str] | None,
    horizon_order: Sequence[str] | None,
) -> tuple[ReversionCurvePoint, ...]:
    venue_rank = _rank_map(venue_order)
    horizon_rank = _rank_map(horizon_order)
    return tuple(
        sorted(
            points,
            key=lambda point: (
                _date_sort_key(point.date),
                _time_bucket_sort_key(point.time_bucket),
                tuple(sorted(point.group.items())),
                _horizon_sort_key(
                    point.horizon,
                    horizon_rank,
                    point.horizon_sort_order,
                ),
                _ranked_text_sort_key(point.venue, venue_rank),
            ),
        )
    )


def _required_group_value(observation: MetricObservation, key: str) -> str:
    value = observation.group.get(key)
    if value is None or not str(value):
        raise ReversionCurveConversionError(f"observation for {observation.metric_name!r} is missing group {key!r}")
    return str(value)


def _rank_map(values: Sequence[str] | None) -> dict[str, int]:
    if values is None:
        return {}
    return {value: index for index, value in enumerate(values)}


def _horizon_sort_key(
    horizon: str,
    horizon_rank: Mapping[str, int],
    horizon_sort_order: int | None = None,
) -> tuple[int, int, str]:
    if horizon in horizon_rank:
        return (0, horizon_rank[horizon], horizon)
    if horizon_sort_order is not None:
        return (1, horizon_sort_order, horizon)

    match = _DURATION_RE.fullmatch(horizon)
    if match is None:
        return (3, 0, horizon)

    duration_ms = int(match.group("size")) * _DURATION_MULTIPLIER_MS[match.group("unit")]
    return (2, duration_ms, horizon)


def _ranked_text_sort_key(
    value: str,
    rank_map: Mapping[str, int],
) -> tuple[int, int, str]:
    if value in rank_map:
        return (0, rank_map[value], value)
    return (1, 0, value)


def _date_sort_key(value: date | None) -> tuple[int, int]:
    if value is None:
        return (0, 0)
    return (1, value.toordinal())


def _time_bucket_sort_key(value: time | str | None) -> tuple[int, int, str]:
    if value is None:
        return (0, 0, "")
    if isinstance(value, time):
        micros_since_midnight = (
            value.hour * 3_600_000_000 + value.minute * 60_000_000 + value.second * 1_000_000 + value.microsecond
        )
        return (1, micros_since_midnight, "")
    return (2, 0, str(value))


def _optional_int_metadata(metadata: Mapping[str, Any], key: str) -> int | None:
    if key not in metadata or metadata[key] is None:
        return None
    try:
        return int(metadata[key])
    except (TypeError, ValueError) as exc:
        raise ReversionCurveConversionError(f"metadata field {key!r} must be an integer when present") from exc


def _optional_float_metadata(metadata: Mapping[str, Any], key: str) -> float | None:
    if key not in metadata or metadata[key] is None:
        return None
    try:
        return float(metadata[key])
    except (TypeError, ValueError) as exc:
        raise ReversionCurveConversionError(f"metadata field {key!r} must be numeric when present") from exc


def _optional_bool_metadata(metadata: Mapping[str, Any], key: str) -> bool | None:
    if key not in metadata or metadata[key] is None:
        return None
    value = metadata[key]
    if isinstance(value, bool):
        return value
    raise ReversionCurveConversionError(f"metadata field {key!r} must be a boolean when present")
