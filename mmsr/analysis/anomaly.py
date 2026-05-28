"""Anomaly scoring placeholders."""

from __future__ import annotations


def liquidity_stress_score(
    spread_z: float,
    volatility_z: float,
    depth_z: float,
) -> float:
    """Compute a simple displayed-liquidity market stress score."""
    return spread_z + volatility_z - depth_z
