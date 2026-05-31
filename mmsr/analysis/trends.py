"""Deterministic trend classification helpers.

This module isolates STL + Kendall/Mann-Kendall + Theil-Sen logic from report
rendering concerns so report builders can stay focused on layout assembly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from statistics import median

import numpy as np
from scipy.stats import kendalltau, theilslopes
from statsmodels.tsa.seasonal import STL

_P_VALUE_SIGNIFICANCE = 0.05
_PRACTICAL_TREND_FLOOR = 0.004
_MILD_TREND_CEILING = 0.010
_MODERATE_TREND_CEILING = 0.020


@dataclass(frozen=True)
class TrendClassification:
    """Final trend classification diagnostics."""

    label: str
    tau: float
    p_value: float
    slope: float
    normalized_slope: float
    summary_text: str


def classify_trend_from_daily_values(
    dates: list[date],
    values: list[float],
) -> TrendClassification:
    """Classify trend after seasonal adjustment of daily observations."""

    rebased_values = _rebase_to_first_bucket(values)
    adjusted_values = _seasonality_adjusted_values(dates, rebased_values)
    return _classify_trend(adjusted_values)


def _classify_trend(values: list[float]) -> TrendClassification:
    if len(values) < 5:
        return TrendClassification(
            label="insufficient",
            tau=0.0,
            p_value=1.0,
            slope=0.0,
            normalized_slope=0.0,
            summary_text="Insufficient observations for robust trend classification.",
        )
    slope = _theil_sen_slope(values)
    tau, p_value = _mann_kendall_tau_pvalue(values)
    baseline = median(abs(value) for value in values)
    normalized_slope = 0.0 if baseline == 0 else slope / baseline

    abs_norm_slope = abs(normalized_slope)

    # Statistical significance alone can overstate visually tiny drifts.
    # Require a minimum practical effect size as well.
    if p_value >= _P_VALUE_SIGNIFICANCE or abs_norm_slope < _PRACTICAL_TREND_FLOOR:
        return TrendClassification(
            label="fluctuating",
            tau=tau,
            p_value=p_value,
            slope=slope,
            normalized_slope=normalized_slope,
            summary_text=(
                "Target period has no clear directional trend "
                f"(p={p_value:.3f}, normalized slope={normalized_slope * 100:.3f}% per bucket)."
            ),
        )
    direction = "up trend" if slope > 0 else "down trend"
    if abs_norm_slope < _MILD_TREND_CEILING:
        strength = "mild"
    elif abs_norm_slope < _MODERATE_TREND_CEILING:
        strength = "moderate"
    else:
        strength = "strong"
    return TrendClassification(
        label=f"{strength}_{direction.replace(' ', '_')}",
        tau=tau,
        p_value=p_value,
        slope=slope,
        normalized_slope=normalized_slope,
        summary_text=(
            f"Target period shows a {strength} {direction} "
            f"(p={p_value:.3f}, normalized slope={normalized_slope * 100:.3f}% per bucket)."
        ),
    )


def _seasonality_adjusted_values(dates: list[date], values: list[float]) -> list[float]:
    if len(values) < 10 or len(dates) != len(values):
        return values
    try:
        arr = np.asarray(values, dtype=float)
        if arr.size >= 15:
            stl = STL(arr, period=5, robust=True)
            res = stl.fit()
            return [float(item) for item in np.asarray(res.trend, dtype=float)]
    except Exception:
        pass

    by_weekday: dict[int, list[float]] = {}
    for obs_date, value in zip(dates, values):
        by_weekday.setdefault(obs_date.weekday(), []).append(value)
    weekday_mean = {weekday: (sum(items) / len(items)) for weekday, items in by_weekday.items()}
    global_mean = sum(values) / len(values)
    return [value - weekday_mean.get(obs_date.weekday(), global_mean) + global_mean for obs_date, value in zip(dates, values)]


def _rebase_to_first_bucket(values: list[float]) -> list[float]:
    """Rebase series so the first valid value equals 100."""

    if not values:
        return values
    first = values[0]
    if not isfinite(first) or first == 0:
        return values
    scale = 100.0 / first
    return [value * scale for value in values]


def _theil_sen_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    y = np.asarray(values, dtype=float)
    try:
        slope, _, _, _ = theilslopes(y, x=x)
    except Exception:
        return 0.0
    return 0.0 if not isfinite(float(slope)) else float(slope)


def _mann_kendall_tau_pvalue(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return 0.0, 1.0
    x = np.arange(len(values), dtype=float)
    y = np.asarray(values, dtype=float)
    try:
        result = kendalltau(x, y, variant="b")
    except Exception:
        return 0.0, 1.0
    tau = 0.0 if result.statistic is None else float(result.statistic)
    p_value = 1.0 if result.pvalue is None else float(result.pvalue)
    if not isfinite(tau):
        tau = 0.0
    if not isfinite(p_value):
        p_value = 1.0
    return tau, p_value
