from datetime import date, time

import pytest

from mmsr.config.models import ReportConfig, ToxicityConfig
from mmsr.kdb.query_plan import (
    KdbMetricQueryPlanError,
    KdbMetricQueryPlanner,
    MetricRunRequest,
    group_by_for_metric_result,
    template_for_metric,
)
from mmsr.kdb.runner import KdbMetricRunner
from mmsr.metrics import build_default_registry
from mmsr.periods import IntradayBucketSpec, ReportPeriod, TradingSession


class FakeKdbClient:
    def __init__(self, result: object) -> None:
        self.result = result
        self.queries: list[str] = []

    def execute(self, query: str) -> object:
        self.queries.append(query)
        return self.result


def _period() -> ReportPeriod:
    return ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 2),
        sessions=[
            TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
            TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
        ],
        bucket=IntradayBucketSpec("5m"),
    )


def test_query_planner_exposes_activity_input_and_output_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("turnover"),
            period=_period(),
            group_by=["market_segment"],
            table_names={"trades": "trade_l1"},
            parameters={"symbol": "7203"},
        )
    )

    assert plan.metric_name == "turnover"
    assert plan.template_name == "activity.q"
    assert plan.requested_group_by == ("market_segment",)
    assert plan.result_group_by == ("market_segment",)
    assert plan.table_names == (("trades", "trade_l1"),)
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "market_segment",
        "turnover",
        "volume",
        "trade_count",
    )
    assert plan.optional_output_columns == ()
    assert plan.input_contracts[0].table_name == "trade_l1"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "trade_price",
        "trade_size",
        "market_segment",
        "sym",
    )
    assert "from trade_l1" in plan.query
    assert 'sym = $"7203"' in plan.query


def test_query_planner_exposes_liquidity_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=_period(),
            group_by=["sector"],
            table_names={"quotes": "quote_l1"},
        )
    )

    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "quoted_spread_bps",
        "top_of_book_depth",
    )
    assert plan.input_contracts[0].table_role == "quotes"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
        "sector",
    )


def test_query_planner_exposes_reversion_optional_metadata_contract() -> None:
    registry = build_default_registry()
    metric_name = "primary_quote_reversion_100ms_bps"
    config = ReportConfig(
        title="Daily Monitor",
        metrics=[metric_name],
        toxicity=ToxicityConfig(primary_venue="TSE", venues=["TSE", "SBIJ"]),
    )

    plan = KdbMetricQueryPlanner().render(
        MetricRunRequest(
            metric=registry.get(metric_name),
            period=_period(),
            group_by=["sym"],
            table_names={
                "venue_trades": "venue_trade_l1",
                "primary_quotes": "quote_l1",
            },
            parameters=config.metric_parameters_for(metric_name),
        )
    )

    assert plan.result_group_by == ("venue", "horizon", "sym")
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "venue",
        "horizon",
        "sym",
        metric_name,
        "horizon_sort_order",
        "trade_count",
        "notional",
        "positive_reversion_ratio",
        "valid_primary_quote_ratio",
    )
    assert plan.optional_output_columns == ("context_sort_order",)
    assert plan.documented_output_columns[-1] == "context_sort_order"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "venue",
        "trade_price",
        "trade_size",
        "aggressor_side",
    )


def test_rendered_query_plan_validates_result_schema_before_normalization() -> None:
    registry = build_default_registry()
    plan = KdbMetricQueryPlanner().render(
        MetricRunRequest(
            metric=registry.get("volume"),
            period=_period(),
            group_by=[],
            table_names={"trades": "trade_l1"},
        )
    )

    valid_result = {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00"],
        "turnover": [1000.0],
        "volume": [100],
        "trade_count": [3],
    }
    plan.validate_result_schema(valid_result)

    invalid_result = dict(valid_result)
    del invalid_result["trade_count"]
    with pytest.raises(ValueError, match="trade_count"):
        plan.validate_result_schema(invalid_result)


def test_runner_uses_query_plan_metadata_in_normalized_series() -> None:
    registry = build_default_registry()
    result = {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00"],
        "turnover": [1000.0],
        "volume": [100],
        "trade_count": [3],
    }
    client = FakeKdbClient(result)
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("volume"),
            period=_period(),
            group_by=[],
            table_names={"trades": "trade_l1"},
        )
    )

    assert series.metadata["required_output_columns"] == (
        "date",
        "time_bucket",
        "volume",
        "turnover",
        "trade_count",
    )
    assert series.metadata["optional_output_columns"] == ()
    assert client.queries == [series.metadata["query"]]


def test_template_for_metric_and_result_grouping_remain_public() -> None:
    assert template_for_metric("turnover") == "activity.q"
    assert template_for_metric("primary_quote_reversion_10s_bps") == (
        "toxicity_reversion.q"
    )
    assert group_by_for_metric_result(
        "primary_quote_reversion_100ms_bps",
        ["venue", "horizon", "sym"],
    ) == ["venue", "horizon", "sym"]


def test_query_planner_rejects_invalid_group_identifier_before_execution() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    with pytest.raises(KdbMetricQueryPlanError, match="invalid group_by column"):
        planner.render(
            MetricRunRequest(
                metric=registry.get("turnover"),
                period=_period(),
                group_by=["bad-column"],
                table_names={"trades": "trade_l1"},
            )
        )
