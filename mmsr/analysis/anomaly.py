"""Anomaly scoring placeholders."""

from __future__ import annotations


def liquidity_stress_score(
    spread_z: float,
    effective_spread_z: float,
    impact_z: float,
    volatility_z: float,
    depth_z: float,
) -> float:
    """Compute a simple liquidity stress score."""
    return spread_z + effective_spread_z + impact_z + volatility_z - depth_z
