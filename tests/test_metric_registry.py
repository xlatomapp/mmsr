import pytest

from mmsr.metrics import MetricDefinition, MetricRegistry, build_default_registry


def test_default_registry_contains_starter_metrics() -> None:
    registry = build_default_registry()
    assert "quoted_spread_bps" in registry.names()
    assert "turnover" in registry.names()


def test_metric_help_text_contains_formula() -> None:
    registry = build_default_registry()
    metric = registry.get("quoted_spread_bps")
    assert "Formula" in metric.help_text()
    assert "ask_price" in metric.help_text()


def test_registry_rejects_duplicates() -> None:
    registry = MetricRegistry()
    metric = MetricDefinition(
        name="x",
        label="X",
        category="Test",
        description="Test metric.",
        formula="x",
        interpretation="Test.",
        unit="count",
        higher_is_better=None,
        default_aggregation="sum",
        supports_intraday=True,
        supports_symbol_level=True,
        required_tables=[],
        required_columns=[],
    )
    registry.register(metric)
    with pytest.raises(ValueError):
        registry.register(metric)
