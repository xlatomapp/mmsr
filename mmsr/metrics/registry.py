"""Metric registry."""

from __future__ import annotations

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.starter_definitions import STARTER_METRICS


class MetricRegistry:
    """Registry for metric definitions."""

    def __init__(self) -> None:
        self._metrics: dict[str, MetricDefinition] = {}

    def register(self, metric: MetricDefinition) -> None:
        """Register a metric definition."""
        if metric.name in self._metrics:
            raise ValueError(f"metric already registered: {metric.name}")
        self._metrics[metric.name] = metric

    def get(self, name: str) -> MetricDefinition:
        """Return a metric definition by name."""
        return self._metrics[name]

    def names(self) -> list[str]:
        """Return registered metric names."""
        return sorted(self._metrics)

    def docs(self) -> list[MetricDefinition]:
        """Return all metric definitions for report docs/help."""
        return [self._metrics[name] for name in self.names()]


def build_default_registry() -> MetricRegistry:
    """Build the default starter metric registry."""
    registry = MetricRegistry()
    for metric in STARTER_METRICS:
        registry.register(metric)
    return registry
