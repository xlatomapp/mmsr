from datetime import date, time

import pytest

from mmsr.config.models import ReportConfig, ToxicityConfig, ToxicityFiltersConfig
from mmsr.kdb.query_loader import render_calculation_function_bootstrap
from mmsr.kdb.runner import (
    KdbMetricRunner,
    KdbMetricRunnerError,
    MetricRunRequest,
    normalize_metric_result,
)
from mmsr.metrics import build_default_registry
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.periods import IntradayBucketSpec, ReportPeriod, TradingSession


class FakeKdbClient:
    def __init__(self, result: object) -> None:
        self.result = result
        self.queries: list[str] = []
        self.calls: list[tuple[object, ...]] = []

    def execute(self, query: str, *args: object) -> object:
        self.queries.append(query)
        self.calls.append((query, *args))
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


def test_calculation_function_bootstrap_contains_bucket_amend_once() -> None:
    bootstrap = render_calculation_function_bootstrap(".mmsr")
    assert "MMSR reusable q calculation library" in bootstrap
    assert "labels:@[labels;where (auction = 1) & (session = `am);:;`AMO];" in bootstrap
    assert "labels[where" not in bootstrap


def test_calculation_function_bootstrap_uses_absolute_assignments_only() -> None:
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    assert "\\d " not in bootstrap
    assert bootstrap.startswith("/ MMSR reusable q calculation library.")
    assert ".desk.mmsr.timeBucketContinuous:{[t;bucket]" in bootstrap


def test_calculation_function_bootstrap_avoids_reserved_cols_assignment() -> None:
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    assert "cols: cols facts" not in bootstrap
    assert "mmsrColumnNames: cols facts;" in bootstrap


def test_calculation_bootstrap_batches_reversion_horizons_inside_day_runner() -> None:
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    assert ".desk.mmsr.calcToxicityReversionFamily" in bootstrap
    assert "reversionMetrics: metricNames where .desk.mmsr.isToxicityReversionMetric each metricNames;" in bootstrap
    assert ".desk.mmsr.calcToxicityReversionFamily[" in bootstrap
    assert ".desk.mmsr.runRegularMetricsBatched[" in bootstrap


def test_calculation_bootstrap_prepares_reversion_common_joins_once() -> None:
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    prepare_start = bootstrap.index(".desk.mmsr.prepareToxicityReversion:{")
    family_start = bootstrap.index(".desk.mmsr.calcToxicityReversionFamily:{")
    family_body = bootstrap[family_start : bootstrap.index(".desk.mmsr.applyUniverseFilters:{")]
    assert "prepared: .desk.mmsr.prepareToxicityReversion[" in family_body
    assert family_body.count("prepareToxicityReversion[") == 1
    assert "calcToxicityReversionPrepared[" in family_body
    assert prepare_start < family_start


def test_calculation_bootstrap_partitions_sym_before_reversion_aj_inputs() -> None:
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    assert ".desk.mmsr.partedSym:{[t]" in bootstrap
    assert "sortedPtsTrades: .desk.mmsr.partedSym[`date`sym`venue`time xasc ptsTrades];" in bootstrap
    assert "sortedPtsQuotes: .desk.mmsr.partedSym[`date`sym`venue`time xasc ptsQuotes];" in bootstrap
    assert "sortedTradeWithPtsQuote: .desk.mmsr.partedSym[`date`sym`time xasc tradeWithPtsQuote];" in bootstrap
    assert "sortedPrimaryQuotes: .desk.mmsr.partedSym[`date`sym`time xasc primaryQuotes];" in bootstrap
    assert "sortedTradeForHorizon: .desk.mmsr.partedSym[`date`sym`horizonTime xasc tradeForHorizon];" in bootstrap
    assert "sortedPostQuotes: .desk.mmsr.partedSym[`date`sym`horizonTime xasc postQuotes];" in bootstrap

    reversion_start = bootstrap.index(".desk.mmsr.prepareToxicityReversion:{")
    reversion_end = bootstrap.index(".desk.mmsr.applyUniverseFilters:{")
    reversion_body = bootstrap[reversion_start:reversion_end]
    assert ".desk.mmsr.partedSym[`date`sym`venue`time xasc ptsTrades]" in reversion_body
    assert ".desk.mmsr.partedSym[`date`sym`venue`time xasc ptsQuotes]" in reversion_body
    assert "aj[\n            `date`sym`venue`time;\n            `date`sym`venue`time xasc" not in reversion_body
    assert "aj[`date`sym`horizonTime; `date`sym`horizonTime xasc" not in reversion_body


def test_calculation_bootstrap_loads_sources_once_per_chunk() -> None:
    """runReportDay must call loadReportSources exactly once per chunk, then
    share the returned rawSources dict across regular and reversion metrics."""
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    run_day_start = bootstrap.index(".desk.mmsr.runReportDay:{")
    run_day_end = bootstrap.index("\n    };\n", run_day_start) + len("\n    };\n")
    run_day_body = bootstrap[run_day_start:run_day_end]
    # Source loading: once per chunk
    assert ".desk.mmsr.loadReportSources[" in run_day_body
    assert run_day_body.count("loadReportSources[") == 1
    # Regular metrics dispatched from the same rawSources
    assert ".desk.mmsr.runRegularMetricsBatched[" in run_day_body
    # Reversion family dispatched from the same rawSources
    assert ".desk.mmsr.calcToxicityReversionFamily[" in run_day_body
    assert "rawSources`pts_trades;" in run_day_body


def test_calculation_bootstrap_has_no_noop_native_function_wrappers() -> None:
    """q calculation helpers must add real policy, not be trivial aliases
    for native q functions such as sum, count, med, avg, or wavg."""
    bootstrap = render_calculation_function_bootstrap(".desk.mmsr")
    # Reject trivial pass-through definitions like {[x] sum x} or {[x;y] avg y}
    import re

    trivial_pattern = re.compile(r"\{\s*\[[^\]]*\]\s*(sum|count|med|avg|wavg|min|max|dev)\s+\w+\s*\}")
    noop_match = trivial_pattern.search(bootstrap)
    assert not noop_match, f"no-op native function wrapper: {noop_match.group()}"


def test_kdb_metric_runner_renders_activity_query_and_normalizes_column_result() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1), date(2026, 5, 2)],
            "timeBucket": ["09:00", "09:05"],
            "market_segment": ["Prime", "Prime"],
            "turnover": [1000.0, 1250.0],
            "volume": [100, 125],
            "trade_count": [3, 4],
            "sample_size": [3, 4],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("turnover"),
            period=_period(),
            group_by=["market_segment"],
            source_functions=_default_source_functions(),
        )
    )

    assert series.metric_name == "turnover"
    assert len(series) == 2
    assert series.values == (1000.0, 1250.0)
    assert series.time_buckets == ("09:00", "09:05")
    assert series.observations[0].group == {"market_segment": "Prime"}
    assert series.observations[0].metadata == {
        "volume": 100,
        "trade_count": 3,
        "sample_size": 3,
    }

    query = client.queries[-1]
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in query
    assert (
        ".mmsr.calcActivity[2026.05.01;rawTrades;refs;(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)]"
        in query
    )
    assert "(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)" in query
    assert "labels:@[labels;where" not in query
    assert "labels[where" not in query
    assert "time within" not in query


def test_kdb_metric_runner_can_bound_starter_query_to_single_symbol() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "timeBucket": ["09:00"],
            "sym": ["7203"],
            "turnover": [1000.0],
            "volume": [100],
            "trade_count": [3],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("turnover"),
            period=_period(),
            group_by=["sym"],
            source_functions=_default_source_functions(),
            parameters={"symbol": "7203"},
        )
    )

    assert series.observations[0].group == {"sym": "7203"}
    assert 'sym = `$"7203"' in client.queries[-1]


def test_kdb_metric_runner_renders_liquidity_query_without_group_columns() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "timeBucket": ["AMO"],
            "quoted_spread_bps": [12.5],
            "top_of_book_depth": [5000],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=_period(),
            group_by=[],
            source_functions=_default_source_functions(),
        )
    )

    assert series.values == (12.5,)
    assert series.observations[0].group == {}
    query = client.queries[-1]
    assert "rawQuotes: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in query
    assert (
        ".mmsr.calcLiquidity[2026.05.01;rawQuotes;refs;(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)]"
        in query
    )
    assert "(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)" in query
    assert ".mmsr.timeBucketContinuous[time; session;" not in query
    assert ".calcLiquidity" in query


def test_kdb_metric_runner_day_query_returns_unified_metric_facts() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "turnover",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 1000.0,
                "level": "intraday",
            },
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 12.5,
                "level": "intraday",
            },
        ]
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]
    common = {
        "period": ReportPeriod(
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 1),
            sessions=[
                TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
                TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
            ],
            bucket=IntradayBucketSpec("5m"),
        ),
        "group_by": ["sym"],
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
        "parameters": {"symbols": ("7203",)},
    }

    series = runner.run_day(
        [
            MetricRunRequest(metric=registry.get("turnover"), **common),
            MetricRunRequest(metric=registry.get("quoted_spread_bps"), **common),
        ]
    )

    assert [item.metric_name for item in series] == [
        "turnover",
        "quoted_spread_bps",
    ]
    assert series[0].values == (1000.0,)
    assert series[1].values == (12.5,)
    config_query = client.queries[0]
    run_query = client.queries[-1]
    assert "`metricNames" in config_query
    assert '`$"turnover"' in config_query
    assert '`$"quoted_spread_bps"' in config_query
    assert ".mmsr.runReportDay[" in run_query


def test_day_runner_accepts_unified_metric_fact_rows() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "turnover",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 1000.0,
                "level": "intraday",
            },
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 12.5,
                "level": "intraday",
            },
        ]
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]
    common = {
        "period": ReportPeriod(
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 1),
            sessions=[
                TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
                TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
            ],
            bucket=IntradayBucketSpec("5m"),
        ),
        "group_by": ["sym"],
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
        "parameters": {"symbols": ("7203",)},
    }

    series = runner.run_day(
        [
            MetricRunRequest(metric=registry.get("turnover"), **common),
            MetricRunRequest(metric=registry.get("quoted_spread_bps"), **common),
        ]
    )

    assert [item.metric_name for item in series] == ["turnover", "quoted_spread_bps"]
    assert series[0].values == (1000.0,)
    assert series[1].values == (12.5,)


def test_day_runner_filters_unified_rows_to_requested_group_scope() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "turnover",
                "date": date(2026, 5, 1),
                "timeBucket": "DAILY",
                "metricValue": 2000.0,
                "groupType": "market",
                "groupValue": "TSE",
                "level": "daily",
            },
            {
                "metricName": "turnover",
                "date": date(2026, 5, 1),
                "timeBucket": "DAILY",
                "metricValue": 1000.0,
                "groupType": "topixCapGrp",
                "groupValue": "Large",
                "level": "daily",
            },
        ]
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]
    common = {
        "period": ReportPeriod(
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 1),
            sessions=[
                TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
                TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
            ],
            bucket=IntradayBucketSpec("5m"),
        ),
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
        "parameters": {"symbols": ("7203",)},
    }

    series = runner.run_day(
        [
            MetricRunRequest(
                metric=registry.get("turnover"),
                group_by=["topixCapGrp"],
                **common,
            ),
        ]
    )

    assert len(series) == 1
    assert series[0].values == (1000.0,)
    assert series[0].observations[0].group == {"topixCapGrp": "Large"}


def test_kdb_metric_runner_renders_reversion_query_and_normalizes_venue_horizon() -> None:
    registry = build_default_registry()
    metric_name = "primary_quote_reversion_100ms_bps"
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1), date(2026, 5, 1)],
            "timeBucket": ["09:00", "09:00"],
            "venue": ["TSE", "SBIJ"],
            "horizon": ["100ms", "100ms"],
            "sym": ["7203", "7203"],
            metric_name: [0.25, -0.75],
            "horizon_sort_order": [2, 2],
            "trade_count": [150, 120],
            "notional": [250000000.0, 175000000.0],
            "positive_reversion_ratio": [0.54, 0.42],
            "valid_primary_quote_ratio": [0.99, 0.98],
            "context_sort_order": [3, 3],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    config = ReportConfig(
        title="Daily Monitor",
        metrics=[metric_name],
        toxicity=ToxicityConfig(
            primary_venue="TSE",
            venues=["TSE", "SBIJ"],
            filters=ToxicityFiltersConfig(max_primary_quote_age="500ms"),
        ),
    )

    series = runner.run(
        MetricRunRequest(
            metric=registry.get(metric_name),
            period=_period(),
            group_by=["sym"],
            source_functions=_default_source_functions(),
            parameters=config.metric_parameters_for(metric_name),
        )
    )

    assert series.metric_name == metric_name
    assert series.values == (0.25, -0.75)
    assert series.observations[1].group == {
        "venue": "SBIJ",
        "horizon": "100ms",
        "sym": "7203",
    }
    assert series.observations[0].metadata == {
        "horizon_sort_order": 2,
        "trade_count": 150,
        "notional": 250000000.0,
        "positive_reversion_ratio": 0.54,
        "valid_primary_quote_ratio": 0.99,
        "context_sort_order": 3,
    }
    assert series.metadata["template"] == "toxicity_reversion"
    assert series.metadata["group_by"] == ("venue", "horizon", "sym")

    query = client.queries[0]
    assert "rawPtsTradeRows: (.sb.mmsr.getPtsTrade[2026.05.01;0!refs]);" in query
    assert "rawPtsQuoteRows: (.sb.mmsr.getPtsQuote[2026.05.01;0!refs]);" in query
    assert "rawPrimaryQuoteRows: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in query
    assert "`venues" in query and "`TSE`SBIJ" in query
    assert "`primary_venue" in query and "`TSE" in query
    assert "0D00:00:00.100" in query
    assert '$"100ms"' in query
    assert "`horizon_sort_order" in query and ";2;" in query
    assert "0D00:00:00.500" in query
    assert "0D00:00:00.500" in query
    assert ".mmsr.calcToxicityReversion" in query
    assert ".mmsr.calcToxicityReversion" in query
    assert '$"primary_quote_reversion_100ms_bps"' in query
    assert ".mmsr.calcToxicityReversion" in query


def test_activity_runner_validates_output_schema_before_normalization() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "timeBucket": ["09:00"],
            "volume": [100],
            "turnover": [1000.0],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="trade_count"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("volume"),
                period=_period(),
                group_by=[],
                source_functions=_default_source_functions(),
            )
        )

    assert len(client.queries) == 1


def test_liquidity_runner_validates_output_schema_before_normalization() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "timeBucket": ["09:00"],
            "quoted_spread_bps": [12.5],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="top_of_book_depth"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=_period(),
                group_by=[],
                source_functions=_default_source_functions(),
            )
        )

    assert len(client.queries) == 1


def test_reversion_runner_validates_output_schema_before_normalization() -> None:
    registry = build_default_registry()
    metric_name = "primary_quote_reversion_100ms_bps"
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "timeBucket": ["09:00"],
            "venue": ["SBIJ"],
            "horizon": ["100ms"],
            metric_name: [0.25],
            "horizon_sort_order": [2],
            "trade_count": [150],
            "notional": [250000000.0],
            "positive_reversion_ratio": [0.54],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    config = ReportConfig(
        title="Daily Monitor",
        metrics=[metric_name],
        toxicity=ToxicityConfig(primary_venue="TSE", venues=["TSE", "SBIJ"]),
    )

    with pytest.raises(ValueError, match="valid_primary_quote_ratio"):
        runner.run(
            MetricRunRequest(
                metric=registry.get(metric_name),
                period=_period(),
                group_by=[],
                source_functions=_default_source_functions(),
                parameters=config.metric_parameters_for(metric_name),
            )
        )


def test_reversion_runner_requires_venue_parameters_before_execution() -> None:
    registry = build_default_registry()
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(KdbMetricRunnerError, match="missing parameter 'primary_venue'"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("primary_quote_reversion_10ms_bps"),
                period=_period(),
                group_by=[],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "pts_trades": ".sb.mmsr.getPtsTrade",
                    "pts_quotes": ".sb.mmsr.getPtsQuote",
                    "primary_quotes": ".sb.mmsr.getQuote",
                },
            )
        )

    assert client.queries == []


def test_runner_rejects_unsupported_metrics_before_query_execution() -> None:
    metric = MetricDefinition(
        name="registered_without_q_template",
        label="Registered Without Q Template",
        category="Test",
        description="Synthetic registered metric without a q template.",
        formula="n/a",
        interpretation="n/a",
        unit="count",
        higher_is_better=None,
        default_aggregation="sum",
        supports_intraday=True,
        supports_symbol_level=False,
        required_tables=[],
        required_columns=[],
    )
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(NotImplementedError, match="not yet supported"):
        runner.run(
            MetricRunRequest(
                metric=metric,
                period=_period(),
                group_by=[],
            )
        )

    assert client.queries == []


def test_runner_requires_metric_source_mapping() -> None:
    registry = build_default_registry()
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(KdbMetricRunnerError, match="missing source_functions entry"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=_period(),
                group_by=[],
            )
        )


def test_runner_rejects_invalid_group_by_identifier() -> None:
    registry = build_default_registry()
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(KdbMetricRunnerError, match="invalid group_by column"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("turnover"),
                period=_period(),
                group_by=["bad-column"],
                source_functions=_default_source_functions(),
            )
        )


def test_normalize_metric_result_accepts_list_of_row_dicts_and_preserves_metadata() -> None:
    series = normalize_metric_result(
        metric_name="quoted_spread_bps",
        result=[
            {
                "date": "2026.05.01",
                "timeBucket": "AMO",
                "market_segment": "Prime",
                "quoted_spread_bps": 10.5,
                "reference_rows": 20,
            }
        ],
        group_by=["market_segment"],
        metadata={"template": "liquidity"},
    )

    assert series.metric_name == "quoted_spread_bps"
    assert series.metadata == {"template": "liquidity"}
    assert series.dates == (date(2026, 5, 1),)
    assert series.observations[0].metadata == {"reference_rows": 20}


def test_normalize_metric_result_accepts_long_value_rows() -> None:
    series = normalize_metric_result(
        metric_name="quoted_spread_bps",
        result=[
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 12.5,
                "level": "intraday",
                "reportTotalMs": 42,
            }
        ],
        group_by=["sym"],
        metadata={"shape": "long"},
    )

    assert series.metric_name == "quoted_spread_bps"
    assert series.values == (12.5,)
    assert series.metadata == {"shape": "long"}
    assert series.observations[0].metadata == {"level": "intraday", "reportTotalMs": 42}


def test_normalize_metric_result_uses_group_type_and_group_value_for_unified_rows() -> None:
    series = normalize_metric_result(
        metric_name="turnover",
        result=[
            {
                "metricName": "turnover",
                "date": date(2026, 5, 1),
                "timeBucket": "DAILY",
                "metricValue": 1000.0,
                "groupType": "topixCapGrp",
                "groupValue": "Large70",
                "level": "daily",
            }
        ],
        group_by=["topixCapGrp"],
    )

    assert series.metric_name == "turnover"
    assert series.values == (1000.0,)
    assert series.observations[0].group == {"topixCapGrp": "Large70"}


def test_normalize_metric_result_rejects_missing_metric_value_column() -> None:
    with pytest.raises(KdbMetricRunnerError, match="missing value column"):
        normalize_metric_result(
            metric_name="turnover",
            result={"date": [date(2026, 5, 1)], "timeBucket": ["09:00"]},
            group_by=[],
        )


def test_normalize_metric_result_rejects_missing_group_column() -> None:
    with pytest.raises(KdbMetricRunnerError, match="missing group column"):
        normalize_metric_result(
            metric_name="turnover",
            result={
                "date": [date(2026, 5, 1)],
                "timeBucket": ["09:00"],
                "turnover": [1000.0],
            },
            group_by=["market_segment"],
        )


def test_normalize_metric_result_rejects_mismatched_column_lengths() -> None:
    with pytest.raises(KdbMetricRunnerError, match="column lengths"):
        normalize_metric_result(
            metric_name="turnover",
            result={
                "date": [date(2026, 5, 1), date(2026, 5, 2)],
                "timeBucket": ["09:00"],
                "turnover": [1000.0, 2000.0, 3000.0],
            },
            group_by=[],
        )


def test_kdb_metric_runner_installs_calculation_functions() -> None:
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)

    runner.install_calculation_functions(".desk.mmsr")

    assert len(client.queries) > 1
    assert any("sum tradePrice * tradeSize" in query for query in client.queries)
    assert any("top_of_book_depth: med depth_lots" in query for query in client.queries)


def test_day_runner_normalizes_keyed_table_mapping_metric_result() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "sym": "7203",
                "metricValue": 12.5,
                "top_of_book_depth": 5000,
                "aggregationLevel": "symbol_bucket",
                "groupType": "sym",
                "groupValue": "7203",
                "level": "intraday",
            }
        ]
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run_day(
        [
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=ReportPeriod(
                    start_date=date(2026, 5, 1),
                    end_date=date(2026, 5, 1),
                    sessions=_period().sessions,
                    bucket=_period().bucket,
                ),
                group_by=["sym"],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "quotes": ".sb.mmsr.getQuote",
                },
            )
        ]
    )

    assert series[0].values == (12.5,)
    assert series[0].observations[0].group == {"sym": "7203"}
    assert series[0].observations[0].metadata["top_of_book_depth"] == 5000


def test_day_runner_keeps_present_but_empty_metric_results() -> None:
    registry = build_default_registry()
    metric_name = "primary_quote_reversion_10ms_bps"
    client = FakeKdbClient(
        {
            "metricName": [],
            "date": [],
            "timeBucket": [],
            "venue": [],
            "horizon": [],
            "sym": [],
            "metricValue": [],
            "level": [],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run_day(
        [
            MetricRunRequest(
                metric=registry.get(metric_name),
                period=ReportPeriod(
                    start_date=date(2026, 5, 1),
                    end_date=date(2026, 5, 1),
                    sessions=_period().sessions,
                    bucket=_period().bucket,
                ),
                group_by=["sym"],
                source_functions=_default_source_functions(),
                parameters=ReportConfig(
                    title="Daily Monitor",
                    metrics=[metric_name],
                    toxicity=ToxicityConfig(primary_venue="TSE", venues=["TSE", "SBIJ"]),
                ).metric_parameters_for(metric_name),
            )
        ]
    )

    assert len(series) == 1
    assert series[0].metric_name == metric_name
    assert series[0].observations == ()


def _single_day_period() -> ReportPeriod:
    return ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 1),
        sessions=_period().sessions,
        bucket=_period().bucket,
    )


def test_day_runner_can_load_unified_rows_from_configured_q_cache_function() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "groupType": "sym",
                "groupValue": "7203",
                "metricValue": 12.5,
                "level": "intraday",
            }
        ]
    )
    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        q_day_cache_functions={
            "use_load": True,
            "load": ".cache.mmsr.loadUnifiedMetricFacts",
            "use_persist": False,
            "persist_mode": "upsert",
        },
    )

    series = runner.run_day(
        [
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=_single_day_period(),
                group_by=["sym"],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "quotes": ".sb.mmsr.getQuote",
                },
            )
        ]
    )

    assert client.queries == ["{[tradingDay] .cache.mmsr.loadUnifiedMetricFacts[tradingDay]}"]
    assert client.calls[0][1:] == (date(2026, 5, 1),)
    assert series[0].metadata["cache_status"] == "hit"
    assert series[0].values == (12.5,)


def test_day_runner_calls_configured_q_persist_function_with_day_table_and_mode() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        [
            {
                "metricName": "quoted_spread_bps",
                "date": date(2026, 5, 1),
                "timeBucket": "09:00",
                "groupType": "sym",
                "groupValue": "7203",
                "metricValue": 12.5,
                "level": "intraday",
            }
        ]
    )
    client.result = [
        {
            "metricName": "quoted_spread_bps",
            "date": date(2026, 5, 1),
            "timeBucket": "09:00",
            "groupType": "sym",
            "groupValue": "7203",
            "metricValue": 12.5,
            "level": "intraday",
        }
    ]

    class SequencedFakeKdbClient(FakeKdbClient):
        def __init__(self, results: list[object]) -> None:
            super().__init__(results[0])
            self._results = list(results)

        def execute(self, query: str, *args: object) -> object:
            self.queries.append(query)
            self.calls.append((query, *args))
            return self._results.pop(0)

    client = SequencedFakeKdbClient(
        [
            None,
            [
                {
                    "metricName": "quoted_spread_bps",
                    "date": date(2026, 5, 1),
                    "timeBucket": "09:00",
                    "groupType": "sym",
                    "groupValue": "7203",
                    "metricValue": 12.5,
                    "level": "intraday",
                }
            ],
            True,
        ]
    )
    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        q_day_cache_functions={
            "use_load": False,
            "use_persist": True,
            "persist": ".cache.mmsr.persistUnifiedMetricFacts",
            "persist_mode": "overwrite",
        },
    )

    series = runner.run_day(
        [
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=_single_day_period(),
                group_by=["sym"],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "quotes": ".sb.mmsr.getQuote",
                },
            )
        ]
    )

    persist_call = client.calls[-1]
    assert persist_call[0] == "{[tradingDay;rows;persistMode] .cache.mmsr.persistUnifiedMetricFacts[tradingDay;rows;persistMode]}"
    assert persist_call[1] == date(2026, 5, 1)
    assert persist_call[3] == "overwrite"
    assert series[0].metadata["cache_status"] == "miss"
