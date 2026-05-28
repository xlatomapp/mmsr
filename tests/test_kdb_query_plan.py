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
        "tradePrice",
        "tradeSize",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "sym",
        "ric",
        "topixCapGrp",
        "lotSize",
        "market_segment",
    )
    assert ".mmsr.sumNotional[tradePrice; tradeSize]" in plan.query
    assert ".mmsr.sumSize[tradeSize]" in plan.query
    assert "rawTrades: trade_l1;" in plan.query
    assert ".mmsr.calcActivity[rawTrades;refs]" in plan.query
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
        "bidPrice",
        "askPrice",
        "bidSize",
        "askSize",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "sym",
        "ric",
        "topixCapGrp",
        "lotSize",
        "sector",
    )
    assert ".mmsr.medianQuotedSpreadBps[bidPrice; askPrice]" in plan.query
    assert ".mmsr.medianTopOfBookDepth[bidSize; askSize]" in plan.query




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
        "bidPrice",
        "askPrice",
        "bidSize",
        "askSize",
        "tick_size",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert "sector" in plan.input_contracts[1].required_columns
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
        "bidPrice",
        "askPrice",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert "sector" in plan.input_contracts[1].required_columns
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
        "tradePrice",
        "tradeSize",
        "aggressorSide",
    )
    assert plan.input_contracts[1].table_role == "reference_data"
    assert "sector" in plan.input_contracts[1].required_columns
    assert "calcFlow" in plan.query
    assert "aggressorSide in (1 -1)" in plan.query
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
        "tradePrice",
        "tradeSize",
    )
    assert plan.input_contracts[2].table_role == "reference_data"
    assert "sector" in plan.input_contracts[2].required_columns
    assert plan.input_contracts[1].table_role == "quotes"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
    )
    assert "calcEffectiveSpread" in plan.query
    assert "aj[`date`sym`time" in plan.query
    assert "quoteAge <= 0D00:00:00.500" in plan.query
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
        "tradePrice",
        "tradeSize",
    )
    assert plan.input_contracts[1].table_role == "quotes"
    assert plan.input_contracts[1].required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
    )
    assert plan.input_contracts[2].table_role == "reference_data"
    assert "sector" in plan.input_contracts[2].required_columns
    assert "calcPriceImpact" in plan.query
    assert "horizonTime: time + 0D00:00:30.000" in plan.query
    assert "quoteAge <= 0D00:00:00.500" in plan.query
    assert "horizonQuoteAge <= 0D00:00:02.000" in plan.query
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
                "pts_trades": "pts_trade_l1",
                "pts_quotes": "quote_l1",
                "primary_quotes": "primary_quote_l1",
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
        "tradePrice",
        "tradeSize",
    )
    assert plan.input_contracts[1].table_role == "pts_quotes"
    assert plan.input_contracts[2].table_role == "primary_quotes"
    assert plan.input_contracts[3].table_role == "reference_data"
    assert plan.input_contracts[3].required_columns == (
        "date",
        "sym",
        "ric",
        "topixCapGrp",
        "lotSize",
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
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in plan.query
    assert 'refs: `sym xkey select from rawRefs where sym = $"7203";' in plan.query
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in plan.query
    assert "calcActivity[rawTrades;refs]" in plan.query
    assert "`startDate`endDate`startTimes`endTimes`bucket`syms`venues" not in plan.query
    assert "`date`symbolChunkId`symbolChunkCount" not in plan.query
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
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in plan.query
    assert "refs: `sym xkey select from rawRefs where 1b;" in plan.query
    assert "rawQuotes: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in plan.query




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
    assert "from quotes" in plan.query
    assert "rawQuotes: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in plan.query


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
    assert "aggressorSide" in plan.input_contracts[0].required_columns
    assert ".desk.mmsr.calcFlow:{" in plan.query
    assert "from trades" in plan.query
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in plan.query
    assert "calcFlow[rawTrades;refs]" in plan.query




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
    assert "rawTradeRows: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in plan.query
    assert "rawQuoteRows: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in plan.query

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
                "pts_trades": ".sb.mmsr.getPtsTrade",
                "pts_quotes": ".sb.mmsr.getPtsQuote",
                "primary_quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
            },
            parameters=config.metric_parameters_for(metric_name),
            calculation_namespace=".sb.mmsrCalc",
        )
    )

    assert plan.input_contracts[0].table_name == ".sb.mmsr.getPtsTrade"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getPtsQuote"
    assert plan.input_contracts[2].table_name == ".sb.mmsr.getQuote"
    assert plan.input_contracts[3].table_name == ".sb.mmsr.getRef"
    assert ".sb.mmsrCalc.calcToxicityReversion:{" in plan.query
    assert "ptsTrades:" in plan.query
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in plan.query
    assert "rawPtsTradeRows: (.sb.mmsr.getPtsTrade[2026.05.01;0!refs]);" in plan.query
    assert "rawPtsQuoteRows: (.sb.mmsr.getPtsQuote[2026.05.01;0!refs]);" in plan.query
    assert "rawPrimaryQuoteRows: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in plan.query
    assert "refs: `sym xkey select from rawRefs where 1b;" in plan.query
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


def test_query_planner_renders_day_query_with_explicit_syms_and_q_rollup() -> None:
    registry = build_default_registry()
    period = ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 1),
        bucket=IntradayBucketSpec("5m"),
    )
    planner = KdbMetricQueryPlanner()
    requests = [
        MetricRunRequest(
            metric=registry.get("turnover"),
            period=period,
            group_by=["topixCapGrp", "sym"],
            parameters={
                "symbols": ("7203", "6758"),
                "aggregation_levels": ("market", "market_bucket", "symbol"),
            },
            source_functions={
                "trades": ".sb.mmsr.getTrade",
                "quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
                "pts_trades": ".sb.mmsr.getPtsTrade",
                "pts_quotes": ".sb.mmsr.getPtsQuote",
                "primary_quotes": ".sb.mmsr.getQuote",
            },
            calculation_namespace=".desk.mmsr",
        ),
        MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=period,
            group_by=["topixCapGrp", "sym"],
            parameters={
                "symbols": ("7203", "6758"),
                "aggregation_levels": ("market", "market_bucket", "symbol"),
            },
            source_functions={
                "trades": ".sb.mmsr.getTrade",
                "quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
                "pts_trades": ".sb.mmsr.getPtsTrade",
                "pts_quotes": ".sb.mmsr.getPtsQuote",
                "primary_quotes": ".sb.mmsr.getQuote",
            },
            calculation_namespace=".desk.mmsr",
        ),
    ]

    plan = planner.render_day(requests)

    assert plan.metric_names == ("turnover", "quoted_spread_bps")
    assert plan.all_symbols == ("7203", "6758")
    assert plan.chunk_size == 2
    assert "currentSymbolChunk" not in plan.query
    assert "{[runDate;allSyms;chunkSize;requestedAggregationLevels]" in plan.query
    assert '($\"7203\";$\"6758\")' in plan.query
    assert "chunks: $[0=count allSyms; enlist 0#`; chunkSize cut allSyms];" in plan.query
    assert ".sb.mmsr.getTrade[runDate;0!refs]" in plan.query
    assert ".sb.mmsr.getQuote[runDate;0!refs]" in plan.query
    assert "rollupMetricResult[raze" in plan.query
    assert "`market`market_bucket`symbol" in plan.query


def test_query_planner_quote_contracts_do_not_require_tick_state() -> None:
    contract = KdbMetricQueryPlanner().render(
        MetricRunRequest(
            metric=build_default_registry().get("quoted_spread_bps"),
            period=ReportPeriod(
                start_date=date(2026, 5, 1),
                end_date=date(2026, 5, 1),
                bucket=IntradayBucketSpec("5m"),
            ),
            group_by=["topixCapGrp"],
            source_functions={
                "quotes": ".sb.mmsr.getQuote",
                "reference_data": ".sb.mmsr.getRef",
            },
        )
    ).input_contracts[0]

    assert "session" not in contract.required_columns
    assert "auction" not in contract.required_columns
    assert "continuous-session" in " ".join(contract.assumptions)
