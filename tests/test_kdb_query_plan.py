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
        "sym",
        "session",
        "auction",
        "trade_price",
        "trade_size",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "sym",
        "topix_bucket",
        "market_cap_bucket",
        "lot_size",
        "market_segment",
    )
    assert ".mmsr.sumNotional[trade_price; trade_size]" in plan.query
    assert ".mmsr.sumSize[trade_size]" in plan.query
    assert "trades: trade_l1 lj refs" in plan.query
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
        "sym",
        "session",
        "auction",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "sym",
        "topix_bucket",
        "market_cap_bucket",
        "lot_size",
        "sector",
    )
    assert ".mmsr.medianQuotedSpreadBps[bid_price; ask_price]" in plan.query
    assert ".mmsr.medianTopOfBookDepth[bid_size; ask_size]" in plan.query




def test_query_planner_exposes_tick_spread_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("quoted_spread_ticks"),
            period=_period(),
            group_by=["sector"],
            table_names={"quotes": "quote_l1"},
            parameters={"symbol": "7203"},
        )
    )

    assert plan.template_name == "liquidity_ticks.q"
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "quoted_spread_ticks",
    )
    assert plan.input_contracts[0].table_role == "quotes"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
        "tick_size",
        "sector",
    )
    assert "calcLiquidityTicks" in plan.query
    assert "tick_size > 0" in plan.query
    assert 'sym = $"7203"' in plan.query


def test_query_planner_exposes_realized_volatility_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("realized_volatility"),
            period=_period(),
            group_by=["sector"],
            table_names={"quotes": "quote_l1"},
            parameters={"symbol": "7203"},
        )
    )

    assert plan.template_name == "realized_volatility.q"
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "realized_volatility",
        "return_count",
        "first_mid",
        "last_mid",
    )
    assert plan.input_contracts[0].table_role == "quotes"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "bid_price",
        "ask_price",
        "sector",
    )
    assert "calcRealizedVolatility" in plan.query
    assert "log_return" in plan.query
    assert 'sym = $"7203"' in plan.query


def test_query_planner_exposes_flow_trade_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("signed_turnover"),
            period=_period(),
            group_by=["sector"],
            table_names={"trades": "trade_l1"},
            parameters={"symbol": "7203"},
        )
    )

    assert plan.template_name == "flow.q"
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "signed_turnover",
        "trade_imbalance",
        "signed_volume",
        "volume",
        "trade_count",
    )
    assert plan.input_contracts[0].table_role == "trades"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "trade_price",
        "trade_size",
        "aggressor_side",
        "sector",
    )
    assert "calcFlow" in plan.query
    assert "aggressor_side in (1 -1)" in plan.query
    assert 'sym = $"7203"' in plan.query




def test_query_planner_exposes_effective_spread_trade_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("effective_spread_bps"),
            period=_period(),
            group_by=["sector"],
            table_names={"trades": "trade_l1", "quotes": "quote_l1"},
            parameters={"symbol": "7203", "max_quote_age": "500ms"},
        )
    )

    assert plan.template_name == "effective_spread.q"
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "effective_spread_bps",
        "trade_count",
        "notional",
    )
    assert plan.input_contracts[0].table_role == "trades"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "trade_price",
        "trade_size",
        "sector",
    )
    assert plan.input_contracts[1].table_role == "quotes"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "bid_price",
        "ask_price",
    )
    assert "calcEffectiveSpread" in plan.query
    assert "aj[`date`sym`time" in plan.query
    assert "quote_age <= 0D00:00:00.500" in plan.query
    assert 'sym = $"7203"' in plan.query


def test_query_planner_exposes_price_impact_trade_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("price_impact_30s_bps"),
            period=_period(),
            group_by=["sector"],
            table_names={"trades": "trade_l1", "quotes": "quote_l1"},
            parameters={
                "symbol": "7203",
                "max_quote_age": "500ms",
                "max_horizon_quote_age": "2s",
            },
        )
    )

    assert plan.template_name == "price_impact.q"
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "sector",
        "price_impact_30s_bps",
        "trade_count",
        "notional",
    )
    assert plan.input_contracts[0].table_role == "trades"
    assert plan.input_contracts[0].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "trade_price",
        "trade_size",
        "aggressor_side",
        "sector",
    )
    assert plan.input_contracts[1].table_role == "quotes"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "bid_price",
        "ask_price",
    )
    assert "calcPriceImpact" in plan.query
    assert "horizon_time: time + 0D00:00:30.000" in plan.query
    assert "quote_age <= 0D00:00:00.500" in plan.query
    assert "horizon_quote_age <= 0D00:00:02.000" in plan.query
    assert 'sym = $"7203"' in plan.query


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
        "session",
        "auction",
        "venue",
        "trade_price",
        "trade_size",
        "aggressor_side",
    )
    assert plan.input_contracts[2].table_role == "reference_data"
    assert plan.input_contracts[2].required_columns == (
        "date",
        "sym",
        "topix_bucket",
        "market_cap_bucket",
        "lot_size",
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
    assert template_for_metric("quoted_spread_ticks") == "liquidity_ticks.q"
    assert template_for_metric("realized_volatility") == "realized_volatility.q"
    assert template_for_metric("signed_turnover") == "flow.q"
    assert template_for_metric("trade_imbalance") == "flow.q"
    assert template_for_metric("effective_spread_bps") == "effective_spread.q"
    assert template_for_metric("primary_quote_reversion_10s_bps") == (
        "toxicity_reversion.q"
    )
    assert group_by_for_metric_result(
        "primary_quote_reversion_100ms_bps",
        ["venue", "horizon", "sym"],
    ) == ["venue", "horizon", "sym"]



def test_query_planner_can_call_user_defined_trade_source_function() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("turnover"),
            period=_period(),
            group_by=["market_segment"],
            source_functions={
                "trades": ".sb.mmsr.getTrade",
                "reference_data": ".sb.mmsr.getRef",
            },
            parameters={"symbol": "7203"},
            calculation_namespace=".sb.mmsrCalc",
        )
    )

    assert plan.table_names == ()
    assert plan.source_functions == (
        ("reference_data", ".sb.mmsr.getRef"),
        ("trades", ".sb.mmsr.getTrade"),
    )
    assert plan.calculation_namespace == ".sb.mmsrCalc"
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getRef"
    assert ".sb.mmsrCalc.calcActivity:{" in plan.query
    assert 'trades: (.sb.mmsr.getTrade[2026.05.01;enlist $"7203"]) lj refs' in plan.query
    assert 'refs: `sym xkey select from (.sb.mmsr.getRef[2026.05.01;enlist $"7203"])' in plan.query
    assert "`startDate`endDate`startTimes`endTimes`bucket`syms`venues" not in plan.query
    assert "`date`symbolChunkId`symbolChunkCount" not in plan.query
    assert 'enlist $"7203"' in plan.query
    assert ";2026.05.02;" not in plan.query
    assert ".mmsr.calcActivity" not in plan.query


def test_query_planner_can_call_user_defined_quote_source_function() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=_period(),
            group_by=[],
            source_functions={
                "quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
            },
            calculation_namespace=".desk.mmsr",
        )
    )

    assert plan.source_functions == (
        ("quotes", ".sb.mmsr.getQuote"),
        ("reference_data", ".sb.mmsr.getRef"),
    )
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getQuote"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getRef"
    assert ".desk.mmsr.calcLiquidity:{" in plan.query
    assert "quotes: (.sb.mmsr.getQuote[2026.05.01;0#`]) lj refs" in plan.query
    assert "refs: `sym xkey select from (.sb.mmsr.getRef[2026.05.01;0#`])" in plan.query




def test_query_planner_can_call_user_defined_quote_source_function_for_ticks() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("quoted_spread_ticks"),
            period=_period(),
            group_by=[],
            source_functions={"quotes": ".sb.mmsr.getQuote"},
            calculation_namespace=".desk.mmsr",
        )
    )

    assert plan.source_functions == (("quotes", ".sb.mmsr.getQuote"),)
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getQuote"
    assert "tick_size" in plan.input_contracts[0].required_columns
    assert ".desk.mmsr.calcLiquidityTicks:{" in plan.query
    assert "from (.sb.mmsr.getQuote[2026.05.01;0#`])" in plan.query


def test_query_planner_can_call_user_defined_trade_source_function_for_flow() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("trade_imbalance"),
            period=_period(),
            group_by=[],
            source_functions={"trades": ".sb.mmsr.getTrade"},
            calculation_namespace=".desk.mmsr",
        )
    )

    assert plan.source_functions == (("trades", ".sb.mmsr.getTrade"),)
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
    assert "aggressor_side" in plan.input_contracts[0].required_columns
    assert ".desk.mmsr.calcFlow:{" in plan.query
    assert "from (.sb.mmsr.getTrade[2026.05.01;0#`])" in plan.query




def test_query_planner_can_call_user_defined_trade_and_quote_functions_for_effective_spread() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("effective_spread_bps"),
            period=_period(),
            group_by=[],
            source_functions={
                "trades": ".sb.mmsr.getTrade",
                "quotes": ".sb.mmsr.getQuote",
            },
            calculation_namespace=".desk.mmsr",
        )
    )

    assert plan.source_functions == (
        ("quotes", ".sb.mmsr.getQuote"),
        ("trades", ".sb.mmsr.getTrade"),
    )
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getQuote"
    assert ".desk.mmsr.calcEffectiveSpread:{" in plan.query
    assert "from (.sb.mmsr.getTrade[2026.05.01;0#`])" in plan.query
    assert "from (.sb.mmsr.getQuote[2026.05.01;0#`])" in plan.query

def test_reversion_planner_uses_user_defined_trade_and_quote_source_functions() -> None:
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
            group_by=[],
            source_functions={
                "venue_trades": ".sb.mmsr.getTrade",
                "primary_quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
            },
            parameters=config.metric_parameters_for(metric_name),
            calculation_namespace=".sb.mmsrCalc",
        )
    )

    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getQuote"
    assert plan.input_contracts[2].table_name == ".sb.mmsr.getRef"
    assert ".sb.mmsrCalc.calcToxicityReversion:{" in plan.query
    assert "venueTrades:" in plan.query
    assert "rawVenueTrades: (.sb.mmsr.getTrade[2026.05.01;0#`]) lj refs" in plan.query
    assert "rawPrimaryQuotes: (.sb.mmsr.getQuote[2026.05.01;0#`]) lj refs" in plan.query
    assert "refs: `sym xkey select from (.sb.mmsr.getRef[2026.05.01;0#`])" in plan.query
    assert "`TSE`SBIJ" in plan.query


def test_query_planner_rejects_invalid_source_function_and_namespace() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    with pytest.raises(KdbMetricQueryPlanError, match="source_functions"):
        planner.render(
            MetricRunRequest(
                metric=registry.get("turnover"),
                period=_period(),
                group_by=[],
                source_functions={"trades": ".sb.bad-name"},
            )
        )

    with pytest.raises(KdbMetricQueryPlanError, match="calculation_namespace"):
        planner.render(
            MetricRunRequest(
                metric=registry.get("turnover"),
                period=_period(),
                group_by=[],
                source_functions={"trades": ".sb.mmsr.getTrade"},
                calculation_namespace="global",
            )
        )

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
