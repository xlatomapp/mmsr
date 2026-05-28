"""Deterministic human-facing report display labels.

The helpers in this module are intentionally small and dependency-free. They
convert normalized report keys such as ``topixCapGrp`` and auction bucket
codes such as ``AMO`` into stable display text without changing the underlying
metric or comparison data.
"""

from __future__ import annotations

from datetime import time
from typing import Mapping


_AUCTION_BUCKET_LABELS: dict[str, str] = {
    "AMO": "AM opening auction",
    "AMC": "AM closing auction",
    "PMO": "PM opening auction",
    "PMC": "PM closing auction",
}

_GROUP_KEY_LABELS: dict[str, str] = {
    "date": "Date",
    "fixture": "Fixture",
    "group": "Group",
    "horizon": "Horizon",
    "market": "Market",
    "market_cap_bucket": "Market cap bucket",
    "topixCapGrp": "TOPIX cap group",
    "market_segment": "Market segment",
    "metric_name": "Metric",
    "reference_observation_aggregation": "Reference observation aggregation",
    "reference_observation_unit": "Reference observation unit",
    "sample_size": "Sample size",
    "sector": "Sector",
    "segment": "Segment",
    "source": "Source",
    "symbol": "Symbol",
    "time_bucket": "Intraday bucket",
    "venue": "Venue",
}

_REFERENCE_OBSERVATION_UNIT_LABELS: dict[str, str] = {
    "date": "date",
    "group": "group",
    "symbol": "symbol",
    "time_bucket": "intraday bucket",
    "trading_day": "trading day",
    "venue": "venue",
}

_MARKET_CAP_VALUE_LABELS: dict[str, str] = {
    "large": "Large cap",
    "mid": "Mid cap",
    "middle": "Mid cap",
    "small": "Small cap",
    "micro": "Micro cap",
}

_VALUE_LABELS_BY_KEY: dict[str, dict[str, str]] = {
    "market_cap_bucket": _MARKET_CAP_VALUE_LABELS,
}

_ACRONYMS = {
    "am",
    "bps",
    "id",
    "jpy",
    "llm",
    "odx",
    "pm",
    "q",
    "sbij",
    "tse",
}


def format_intraday_bucket_label(bucket: object | None) -> str | None:
    """Return a deterministic display label for an intraday or auction bucket."""

    if bucket is None:
        return None
    if isinstance(bucket, time):
        return bucket.strftime("%H:%M")

    raw = str(bucket).strip()
    if not raw:
        return None

    upper = raw.upper()
    if upper in _AUCTION_BUCKET_LABELS:
        return _AUCTION_BUCKET_LABELS[upper]

    if "-" in raw:
        start, separator, end = raw.partition("-")
        if separator and start.strip() and end.strip():
            return f"{start.strip()}–{end.strip()}"

    return raw


def format_group_key_label(key: object) -> str:
    """Return a deterministic display label for a normalized group key."""

    raw = str(key).strip()
    if not raw:
        return "Group"

    known = _GROUP_KEY_LABELS.get(raw)
    if known is not None:
        return known

    return " ".join(_format_key_word(part) for part in raw.split("_") if part)


def format_reference_observation_unit_label(unit: object | None) -> str | None:
    """Return a readable label for a comparison reference observation unit."""

    if unit is None:
        return None
    raw = str(unit).strip()
    if not raw:
        return None

    known = _REFERENCE_OBSERVATION_UNIT_LABELS.get(raw)
    if known is not None:
        return known
    return format_group_key_label(raw).lower()


def format_group_value_label(key: object, value: object) -> str:
    """Return a deterministic display value for a group key/value pair."""

    raw_key = str(key).strip()
    raw_value = str(value).strip()
    if raw_key == "time_bucket":
        label = format_intraday_bucket_label(raw_value)
        return "" if label is None else label
    if raw_key == "reference_observation_unit":
        label = format_reference_observation_unit_label(raw_value)
        return "" if label is None else label

    value_lookup = _VALUE_LABELS_BY_KEY.get(raw_key, {})
    known = value_lookup.get(raw_value.lower())
    if known is not None:
        return known

    return raw_value


def format_group_item_label(key: object, value: object) -> str:
    """Return one human-facing group item such as ``Venue: TSE``."""

    return f"{format_group_key_label(key)}: {format_group_value_label(key, value)}"


def format_group_label(
    group: Mapping[str, object],
    *,
    group_by: tuple[str, ...] | list[str] | None = None,
) -> str | None:
    """Return a stable display label for a normalized group mapping."""

    if not group:
        return None

    keys = tuple(sorted(group)) if group_by is None else tuple(group_by)
    parts = [
        format_group_item_label(key, group[key])
        for key in keys
        if key in group
    ]
    return ", ".join(parts) if parts else None


def format_comparison_scope_label(
    *,
    observation_date: object | None = None,
    time_bucket: object | None = None,
    group: Mapping[str, object] | None = None,
) -> str | None:
    """Return a human-facing comparison scope label.

    The order is deterministic and mirrors report reading order: report date,
    intraday bucket, then any supplied grouping dimensions.
    """

    parts: list[str] = []
    if observation_date is not None:
        parts.append(format_group_item_label("date", observation_date))
    if time_bucket is not None:
        bucket_label = format_intraday_bucket_label(time_bucket)
        if bucket_label is not None:
            parts.append(format_group_item_label("time_bucket", bucket_label))
    if group:
        group_label = format_group_label(group)
        if group_label is not None:
            parts.append(group_label)

    return ", ".join(parts) if parts else None


def _format_key_word(word: str) -> str:
    lower = word.lower()
    if lower in _ACRONYMS:
        return lower.upper()
    return lower.capitalize()


__all__ = [
    "format_comparison_scope_label",
    "format_group_item_label",
    "format_group_key_label",
    "format_group_label",
    "format_group_value_label",
    "format_intraday_bucket_label",
    "format_reference_observation_unit_label",
]
