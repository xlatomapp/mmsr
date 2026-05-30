from datetime import date, time

import pytest

from mmsr.config.models import ReportConfig, ToxicityConfig, ToxicityFiltersConfig
from mmsr.kdb.cache import (
    MetricDayCacheHooks,
    MetricDayCacheKey,
    merge_stock_metrics_rows,
    metric_series_from_stock_metrics_rows,
    stock_metrics_rows_from_series,
)
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
    assert "regularMetrics!({[rawSources;metricParams;metricName]" in bootstrap


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
    assert "regularMetrics!({[rawSources;metricParams;metricName]" in run_day_body
    # Reversion family dispatched from the same rawSources
    assert ".desk.mmsr.calcToxicityReversionFamily[\n                    rawSources`pts_trades;" in run_day_body


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
            "time_bucket": ["09:00", "09:05"],
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

    query = client.queries[0]
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in query
    assert (
        ".mmsr.calcActivity[rawTrades;refs;(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)]"
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
            "time_bucket": ["09:00"],
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
    assert 'sym = `$"7203"' in client.queries[0]


def test_kdb_metric_runner_renders_liquidity_query_without_group_columns() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "time_bucket": ["AMO"],
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
    query = client.queries[0]
    assert "rawQuotes: (.sb.mmsr.getQuote[2026.05.01;0!refs]);" in query
    assert (
        ".mmsr.calcLiquidity[rawQuotes;refs;(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)]"
        in query
    )
    assert "(`bucket;`start_date;`end_date)!(0D00:05:00.000;2026.05.01;2026.05.02)" in query
    assert ".mmsr.timeBucketContinuous[time; session;" not in query
    assert ".calcLiquidity" in query


def test_kdb_metric_runner_day_query_returns_metric_tables() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "turnover": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
                "sym": ["7203"],
                "turnover": [1000.0],
                "volume": [100],
                "trade_count": [3],
            },
            "quoted_spread_bps": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
                "sym": ["7203"],
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
            },
        }
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
    query = client.queries[0]
    assert ".mmsr.runReportDay[" in query
    assert "`metricNames" in query
    assert '`$"turnover"' in query
    assert '`$"quoted_spread_bps"' in query


def test_kdb_metric_runner_renders_reversion_query_and_normalizes_venue_horizon() -> None:
    registry = build_default_registry()
    metric_name = "primary_quote_reversion_100ms_bps"
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1), date(2026, 5, 1)],
            "time_bucket": ["09:00", "09:00"],
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
            "time_bucket": ["09:00"],
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
            "time_bucket": ["09:00"],
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
            "time_bucket": ["09:00"],
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
                "time_bucket": "AMO",
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


def test_normalize_metric_result_rejects_missing_metric_value_column() -> None:
    with pytest.raises(KdbMetricRunnerError, match="missing value column"):
        normalize_metric_result(
            metric_name="turnover",
            result={"date": [date(2026, 5, 1)], "time_bucket": ["09:00"]},
            group_by=[],
        )


def test_normalize_metric_result_rejects_missing_group_column() -> None:
    with pytest.raises(KdbMetricRunnerError, match="missing group column"):
        normalize_metric_result(
            metric_name="turnover",
            result={
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
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
                "time_bucket": ["09:00"],
                "turnover": [1000.0, 2000.0, 3000.0],
            },
            group_by=[],
        )


def test_kdb_metric_runner_installs_calculation_functions() -> None:
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)

    runner.install_calculation_functions(".desk.mmsr")

    assert len(client.queries) == 1
    assert "sum tradePrice * tradeSize" in client.queries[0]
    assert "med bidSize + askSize" in client.queries[0]


def test_day_runner_normalizes_keyed_table_mapping_metric_result() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "quoted_spread_bps": {
                "key": {
                    "date": [date(2026, 5, 1)],
                    "time_bucket": ["09:00"],
                    "sym": ["7203"],
                    "topixCapGrp": ["Large70"],
                },
                "value": {
                    "quoted_spread_bps": [12.5],
                    "top_of_book_depth": [5000],
                    "aggregationLevel": ["symbol_bucket"],
                    "groupType": ["sym"],
                    "groupValue": ["7203"],
                },
            }
        }
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
                group_by=["sym", "topixCapGrp"],
                source_functions={
                    "reference_data": ".sb.mmsr.getRef",
                    "quotes": ".sb.mmsr.getQuote",
                },
            )
        ]
    )

    assert series[0].values == (12.5,)
    assert series[0].observations[0].group == {
        "sym": "7203",
        "topixCapGrp": "Large70",
    }
    assert series[0].observations[0].metadata["top_of_book_depth"] == 5000


def _single_day_period() -> ReportPeriod:
    return ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 1),
        sessions=_period().sessions,
        bucket=_period().bucket,
    )


def test_day_runner_uses_cached_metric_day_result_without_kdb_execution() -> None:
    registry = build_default_registry()
    cached_series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 1),
                time_bucket="09:00",
                group={"sym": "7203"},
                value=12.5,
                metadata={"top_of_book_depth": 5000},
            )
        ],
        metadata={"storage": "user-cache"},
    )
    load_calls: list[MetricDayCacheKey] = []

    def load_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        load_calls.append(key)
        assert request.metric.name == "quoted_spread_bps"
        return cached_series

    client = FakeKdbClient({})
    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(load=load_cached),
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

    assert series == (
        cached_series.__class__(
            metric_name="quoted_spread_bps",
            observations=cached_series.observations,
            metadata={"storage": "user-cache", "cache_status": "hit"},
        ),
    )
    assert client.queries == []
    assert load_calls[0].trading_day == date(2026, 5, 1)
    assert load_calls[0].metric_name == "quoted_spread_bps"
    assert load_calls[0].group_by == ("sym",)
    assert load_calls[0].bucket == "5m"


def test_day_runner_persists_metric_day_cache_misses_after_execution() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "quoted_spread_bps": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
                "sym": ["7203"],
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
            }
        }
    )
    load_calls: list[MetricDayCacheKey] = []
    persisted: list[tuple[MetricDayCacheKey, MetricTimeSeries]] = []

    def load_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        load_calls.append(key)
        return None

    def persist_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
        series: MetricTimeSeries,
    ) -> None:
        persisted.append((key, series))

    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(load=load_cached, persist=persist_cached),
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

    assert len(client.queries) == 1
    assert len(load_calls) == 1
    assert len(persisted) == 1
    persisted_key, persisted_series = persisted[0]
    assert persisted_key.metric_name == "quoted_spread_bps"
    assert persisted_key.trading_day == date(2026, 5, 1)
    assert persisted_series is series[0]
    assert series[0].metadata["cache_status"] == "miss"
    assert series[0].values == (12.5,)


def test_day_runner_runs_only_uncached_metrics_and_preserves_request_order() -> None:
    registry = build_default_registry()
    cached_turnover = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="turnover",
                date=date(2026, 5, 1),
                time_bucket="09:00",
                group={"sym": "7203"},
                value=1000.0,
            )
        ]
    )
    client = FakeKdbClient(
        {
            "quoted_spread_bps": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
                "sym": ["7203"],
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
            }
        }
    )
    persisted: list[str] = []

    def load_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        if key.metric_name == "turnover":
            return cached_turnover
        return None

    def persist_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
        series: MetricTimeSeries,
    ) -> None:
        persisted.append(key.metric_name)

    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(load=load_cached, persist=persist_cached),
    )
    common = {
        "period": _single_day_period(),
        "group_by": ["sym"],
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
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
    assert series[0].metadata["cache_status"] == "hit"
    assert series[1].metadata["cache_status"] == "miss"
    assert persisted == ["quoted_spread_bps"]
    assert len(client.queries) == 1
    assert '`$"turnover"' not in client.queries[0]
    assert '`$"quoted_spread_bps"' in client.queries[0]


def test_day_runner_loads_stock_metrics_once_and_computes_only_missing_metrics() -> None:
    registry = build_default_registry()
    stock_load_calls: list[tuple[date, tuple[str, ...]]] = []
    per_metric_load_calls: list[str] = []
    persisted: list[str] = []
    client = FakeKdbClient(
        {
            "quoted_spread_bps": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00-09:05"],
                "sym": ["7203"],
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
            }
        }
    )

    def load_stock_metrics(
        trading_day: date,
        requests: tuple[MetricRunRequest, ...],
        keys: tuple[MetricDayCacheKey, ...],
        metric_names: tuple[str, ...],
    ) -> tuple[dict[str, object], ...]:
        stock_load_calls.append((trading_day, tuple(metric_names)))
        assert [key.trading_day for key in keys] == [trading_day, trading_day]
        assert [request.metric.name for request in requests] == list(metric_names)
        return (
            {
                "date": trading_day,
                "timeBucket": "09:00-09:05",
                "bucketSize": "5m",
                "sym": "7203",
                "groupType": "symbol",
                "groupValue": "7203",
                "turnover": 1000.0,
            },
        )

    def load_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        per_metric_load_calls.append(key.metric_name)
        return None

    def persist_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
        series: MetricTimeSeries,
    ) -> None:
        persisted.append(key.metric_name)

    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(
            load=load_cached,
            persist=persist_cached,
            load_stock_metrics=load_stock_metrics,
        ),
    )
    common = {
        "period": _single_day_period(),
        "group_by": ["sym"],
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
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
    assert series[0].metadata == {"storage": "stockMetrics", "cache_status": "hit"}
    assert series[0].values == (1000.0,)
    assert series[1].metadata["cache_status"] == "miss"
    assert stock_load_calls == [(date(2026, 5, 1), ("turnover", "quoted_spread_bps"))]
    assert per_metric_load_calls == ["quoted_spread_bps"]
    assert persisted == ["quoted_spread_bps"]
    assert len(client.queries) == 1
    assert '`$"turnover"' not in client.queries[0]
    assert '`$"quoted_spread_bps"' in client.queries[0]


def test_day_runner_persists_computed_misses_as_one_stock_metrics_batch() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "turnover": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00-09:05"],
                "sym": ["7203"],
                "turnover": [1000.0],
                "volume": [100],
                "trade_count": [3],
            },
            "quoted_spread_bps": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00-09:05"],
                "sym": ["7203"],
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
            },
        }
    )
    persisted_batches: list[tuple[date, tuple[str, ...], tuple[dict[str, object], ...]]] = []
    per_metric_persist_calls: list[str] = []

    def persist_stock_metrics(
        trading_day: date,
        requests: tuple[MetricRunRequest, ...],
        keys: tuple[MetricDayCacheKey, ...],
        rows: tuple[dict[str, object], ...],
    ) -> None:
        persisted_batches.append(
            (
                trading_day,
                tuple(key.metric_name for key in keys),
                rows,
            )
        )
        assert [request.metric.name for request in requests] == [
            "turnover",
            "quoted_spread_bps",
        ]

    def persist_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
        series: MetricTimeSeries,
    ) -> None:
        per_metric_persist_calls.append(key.metric_name)

    runner = KdbMetricRunner(
        client,  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(
            persist=persist_cached,
            persist_stock_metrics=persist_stock_metrics,
        ),
    )
    common = {
        "period": _single_day_period(),
        "group_by": ["sym"],
        "source_functions": {
            "reference_data": ".sb.mmsr.getRef",
            "trades": ".sb.mmsr.getTrade",
            "quotes": ".sb.mmsr.getQuote",
        },
    }

    series = runner.run_day(
        [
            MetricRunRequest(metric=registry.get("turnover"), **common),
            MetricRunRequest(metric=registry.get("quoted_spread_bps"), **common),
        ]
    )

    assert [item.metadata["cache_status"] for item in series] == ["miss", "miss"]
    assert per_metric_persist_calls == []
    assert len(persisted_batches) == 1
    trading_day, metric_names, rows = persisted_batches[0]
    assert trading_day == date(2026, 5, 1)
    assert metric_names == ("turnover", "quoted_spread_bps")
    assert rows == (
        {
            "date": date(2026, 5, 1),
            "timeBucket": "09:00-09:05",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "turnover": 1000.0,
            "quoted_spread_bps": 12.5,
        },
    )


def test_day_runner_rejects_cached_series_for_wrong_metric_or_day() -> None:
    registry = build_default_registry()
    wrong_series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="turnover",
                date=date(2026, 5, 2),
                time_bucket="09:00",
                group={},
                value=1000.0,
            )
        ]
    )

    def load_cached(
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        return wrong_series

    runner = KdbMetricRunner(
        FakeKdbClient({}),  # type: ignore[arg-type]
        cache_hooks=MetricDayCacheHooks(load=load_cached),
    )

    with pytest.raises(KdbMetricRunnerError, match="quoted_spread_bps"):
        runner.run_day(
            [
                MetricRunRequest(
                    metric=registry.get("quoted_spread_bps"),
                    period=_single_day_period(),
                    group_by=[],
                    source_functions={
                        "reference_data": ".sb.mmsr.getRef",
                        "quotes": ".sb.mmsr.getQuote",
                    },
                )
            ]
        )


def test_stock_metrics_rows_use_time_bucket_and_bucket_size_only() -> None:
    key = MetricDayCacheKey.from_request(
        MetricRunRequest(
            metric=build_default_registry().get("quoted_spread_bps"),
            period=_single_day_period(),
            group_by=["sym"],
        )
    )
    series = MetricTimeSeries.from_observations(
        [
            MetricObservation(
                metric_name="quoted_spread_bps",
                date=date(2026, 5, 1),
                time_bucket="AMO",
                group={"sym": "7203"},
                value=12.5,
                metadata={"top_of_book_depth": 5000},
            )
        ]
    )

    rows = stock_metrics_rows_from_series(key, series)

    assert rows == (
        {
            "date": date(2026, 5, 1),
            "timeBucket": "AMO",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "quoted_spread_bps": 12.5,
        },
    )
    assert "timeSegmentType" not in rows[0]
    assert "timeSegmentSort" not in rows[0]
    assert "bucketSort" not in rows[0]


def test_stock_metrics_rows_can_round_trip_metric_series() -> None:
    rows = [
        {
            "date": date(2026, 5, 1),
            "timeBucket": "09:00-09:05",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "quoted_spread_bps": 12.5,
            "top_of_book_depth": 5000,
        },
        {
            "date": "2026.05.01",
            "timeBucket": "AMO",
            "bucketSize": "5m",
            "sym": "ALL",
            "groupType": "market",
            "groupValue": "ALL",
            "quoted_spread_bps": 10.0,
        },
    ]

    series = metric_series_from_stock_metrics_rows(
        "quoted_spread_bps",
        rows,
        metadata={"cache_status": "hit"},
    )

    assert series is not None
    assert series.metadata == {"cache_status": "hit"}
    assert series.time_buckets == ("09:00-09:05", "AMO")
    assert series.values == (12.5, 10.0)
    assert series.observations[0].group == {"sym": "7203"}
    assert series.observations[0].metadata == {"top_of_book_depth": 5000}
    assert series.observations[1].group == {}


def test_merge_stock_metrics_rows_widens_rows_by_canonical_dimensions() -> None:
    spread_rows = [
        {
            "date": date(2026, 5, 1),
            "timeBucket": "09:00-09:05",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "quoted_spread_bps": 12.5,
        }
    ]
    depth_rows = [
        {
            "date": date(2026, 5, 1),
            "timeBucket": "09:00-09:05",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "top_of_book_depth": 5000,
        }
    ]

    assert merge_stock_metrics_rows([spread_rows, depth_rows]) == (
        {
            "date": date(2026, 5, 1),
            "timeBucket": "09:00-09:05",
            "bucketSize": "5m",
            "sym": "7203",
            "groupType": "symbol",
            "groupValue": "7203",
            "quoted_spread_bps": 12.5,
            "top_of_book_depth": 5000,
        },
    )
