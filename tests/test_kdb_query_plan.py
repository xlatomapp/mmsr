import re
from datetime import date, time

import pytest

from mmsr.config.models import ReportConfig, ToxicityConfig
from mmsr.kdb.query_plan import (
    KdbMetricQueryPlanError,
    KdbMetricQueryPlanner,
    MetricRunRequest,
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


def _default_source_functions() -> dict[str, str]:
    return {
        "reference_data": ".sb.mmsr.getRef",
        "trades": ".sb.mmsr.getTrade",
        "quotes": ".sb.mmsr.getQuote",
        "pts_trades": ".sb.mmsr.getPtsTrade",
        "pts_quotes": ".sb.mmsr.getPtsQuote",
        "primary_quotes": ".sb.mmsr.getQuote",
    }


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
            source_functions=_default_source_functions(),
            parameters={"symbol": "7203"},
        )
    )

    assert plan.metric_name == "turnover"
    assert plan.template_name == "activity"
    assert plan.requested_group_by == ("market_segment",)
    assert plan.result_group_by == ("market_segment",)
    assert plan.required_output_columns == (
        "date",
        "time_bucket",
        "market_segment",
        "turnover",
        "volume",
        "trade_count",
    )
    assert plan.optional_output_columns == ()
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
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
    assert ".mmsr.calcActivity[rawTrades;refs;" in plan.query
    assert "calcActivity[rawTrades;refs;" in plan.query
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in plan.query
    assert ".mmsr.calcActivity[rawTrades;refs;" in plan.query
    assert 'sym = `$"7203"' in plan.query


def test_query_planner_exposes_liquidity_quote_contracts() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()

    plan = planner.render(
        MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=_period(),
            group_by=["sector"],
            source_functions=_default_source_functions(),
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
    assert ".mmsr.calcLiquidity[rawQuotes;refs;" in plan.query
    assert "calcLiquidity[rawQuotes;refs;" in plan.query


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
            source_functions=_default_source_functions(),
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
            source_functions=_default_source_functions(),
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
            source_functions=_default_source_functions(),
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

    assert plan.source_functions == (
        ("reference_data", ".sb.mmsr.getRef"),
        ("trades", ".sb.mmsr.getTrade"),
    )
    assert plan.calculation_namespace == ".sb.mmsrCalc"
    assert plan.input_contracts[0].table_name == ".sb.mmsr.getTrade"
    assert plan.input_contracts[1].table_name == ".sb.mmsr.getRef"
    assert ".sb.mmsrCalc.calcActivity[rawTrades;refs;" in plan.query
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in plan.query
    assert 'refs: `sym xkey select from rawRefs where sym = `$"7203";' in plan.query
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in plan.query
    assert "calcActivity[rawTrades;refs;" in plan.query
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
    assert ".desk.mmsr.calcLiquidity[rawQuotes;refs;" in plan.query
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in plan.query
    assert "refs: `sym xkey select from rawRefs where 1b;" in plan.query
    assert "rawQuotes: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in plan.query


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
    assert ".sb.mmsrCalc.calcToxicityReversion[rawPtsTradeRows;rawPtsQuoteRows;rawPrimaryQuoteRows;refs;" in plan.query
    assert "calcToxicityReversion[rawPtsTradeRows;rawPtsQuoteRows;rawPrimaryQuoteRows;refs;" in plan.query
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
                source_functions=_default_source_functions(),
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
    assert plan.chunk_size == 500
    assert "currentSymbolChunk" not in plan.query
    assert ".desk.mmsr.runReportDay[" in plan.query
    assert ".desk.mmsr.runMetricDay[" not in plan.query
    assert "chunkMetricResult" not in plan.query
    assert "{[rawSources]" not in plan.query
    assert "sourceFunctions" in plan.query
    assert ".sb.mmsr.getTrade" in plan.query
    assert ".sb.mmsr.getQuote" in plan.query
    assert ".sb.mmsr.getRef" in plan.query
    assert "enlist[`symbols]!" in plan.query
    assert (
        'rollupMetricResult[raze {x[$"quoted_spread_bps"]} each chunkResults;requestedAggregationLevels]'
        not in plan.query
    )
    assert 'rollupMetricResult[raze {x[$"quoted_spread_bps"]} each chunkResults;$"quoted_spread_bps";' not in plan.query
    assert "`market`market_bucket`symbol" in plan.query

    assert "`reference_data" in plan.query
    assert '`$"quoted_spread_bps"' in plan.query
    assert '`$"7203"' in plan.query
    assert re.search(r'(?<!`)\\$"reference_data"', plan.query) is None
    assert re.search(r'(?<!`)\\$"quoted_spread_bps"', plan.query) is None
    assert re.search(r'(?<!`)\\$"7203"', plan.query) is None


def test_query_planner_quote_contracts_do_not_require_tick_state() -> None:
    contract = (
        KdbMetricQueryPlanner()
        .render(
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
        )
        .input_contracts[0]
    )

    assert "session" not in contract.required_columns
    assert "auction" not in contract.required_columns
    assert "continuous-session" in " ".join(contract.assumptions)


def test_render_day_uses_canonical_q_library_blocks_not_removed_template_files() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()
    base_period = _period()
    plan = planner.render_day(
        [
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=ReportPeriod(
                    start_date=date(2026, 5, 1),
                    end_date=date(2026, 5, 1),
                    sessions=base_period.sessions,
                    bucket=base_period.bucket,
                ),
                group_by=["sym"],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "quotes": ".sb.mmsr.getQuote",
                },
                parameters={
                    "symbols": ("7203",),
                    "aggregation_levels": ("symbol",),
                },
            )
        ]
    )

    assert ".runReportDay[" in plan.query
    assert ".runMetricDay[" not in plan.query
    assert ".calcLiquidity" not in plan.query
    assert "{[rawSources]" not in plan.query
    assert "query_templates" not in plan.query
    assert "liquidity.j2" not in plan.query


def test_render_day_singleton_metric_dictionaries_enlist_keys_before_bang() -> None:
    registry = build_default_registry()
    planner = KdbMetricQueryPlanner()
    base_period = _period()
    period = ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 1),
        sessions=base_period.sessions,
        bucket=base_period.bucket,
    )

    plan = planner.render_day(
        [
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=period,
                group_by=["sym"],
                parameters={
                    "symbols": ("7203",),
                    "aggregation_levels": ("symbol",),
                },
                source_functions={
                    "quotes": ".sb.mmsr.getQuote",
                    "reference_data": ".sb.mmsr.getRef",
                },
                calculation_namespace=".desk.mmsr",
            )
        ]
    )

    assert "enlist[`quoted_spread_bps]!enlist ((`bucket;`start_date;`end_date)!" in plan.query
    assert "enlist `quoted_spread_bps!" not in plan.query
    assert 'enlist[`symbols]!enlist (enlist `$"7203")' in plan.query
    assert "enlist `symbols!" not in plan.query
    assert 'enlist `$"reference_data"!' not in plan.query
    assert re.search(r"enlist\s+`[^\[\s]+!", plan.query) is None
