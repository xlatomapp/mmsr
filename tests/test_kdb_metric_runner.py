from datetime import date, time

import pytest

from mmsr.config.models import ReportConfig, ToxicityConfig, ToxicityFiltersConfig
from mmsr.kdb.runner import (
    KdbMetricRunner,
    KdbMetricRunnerError,
    MetricRunRequest,
    normalize_metric_result,
    template_for_metric,
)
from mmsr.metrics import build_default_registry
from mmsr.metrics.base import MetricDefinition
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


def test_template_for_metric_maps_initial_activity_liquidity_and_reversion_metrics() -> None:
    assert template_for_metric("turnover") == "activity.q"
    assert template_for_metric("volume") == "activity.q"
    assert template_for_metric("trade_count") == "activity.q"
    assert template_for_metric("quoted_spread_bps") == "liquidity.q"
    assert template_for_metric("top_of_book_depth") == "liquidity.q"
    assert template_for_metric("effective_spread_bps") == "effective_spread.q"
    assert template_for_metric("price_impact_30s_bps") == "price_impact.q"
    assert template_for_metric("primary_quote_reversion_100ms_bps") == "toxicity_reversion.q"
    assert template_for_metric("primary_quote_reversion_10s_bps") == "toxicity_reversion.q"


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
            table_names={"trades": "trade"},
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
    assert "trades: trade lj refs" in query
    assert "date within (2026.05.01;2026.05.02)" in query
    assert ".mmsr.timeBucket[time; session; auction; 0D00:05:00.000]" in query
    assert "market_segment" in query
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
            table_names={"trades": "trade"},
            parameters={"symbol": "7203"},
        )
    )

    assert series.observations[0].group == {"sym": "7203"}
    assert 'sym = $"7203"' in client.queries[0]


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
            table_names={"quotes": "quote"},
        )
    )

    assert series.values == (12.5,)
    assert series.observations[0].group == {}
    assert "quotes: quote lj refs" in client.queries[0]
    assert "by date, time_bucket:" in client.queries[0]


def test_kdb_metric_runner_renders_effective_spread_query_and_preserves_metadata() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "time_bucket": ["09:00"],
            "sector": ["Banks"],
            "effective_spread_bps": [6.25],
            "trade_count": [20],
            "notional": [25_000_000.0],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("effective_spread_bps"),
            period=_period(),
            group_by=["sector"],
            table_names={"trades": "trade", "quotes": "quote"},
            parameters={"max_quote_age": "500ms"},
        )
    )

    assert series.metric_name == "effective_spread_bps"
    assert series.values == (6.25,)
    assert series.observations[0].group == {"sector": "Banks"}
    assert series.observations[0].metadata == {
        "trade_count": 20,
        "notional": 25_000_000.0,
    }
    assert series.metadata["template"] == "effective_spread.q"

    query = client.queries[0]
    assert "rawTrades: trade lj refs" in query
    assert "rawQuotes: quote lj refs" in query
    assert "aj[`date`sym`time" in query
    assert "quoteAge <= 0D00:00:00.500" in query
    assert "effective_spread_bps: med" in query


def test_kdb_metric_runner_renders_price_impact_query_and_preserves_metadata() -> None:
    registry = build_default_registry()
    client = FakeKdbClient(
        {
            "date": [date(2026, 5, 1)],
            "time_bucket": ["09:00"],
            "sector": ["Banks"],
            "price_impact_30s_bps": [4.75],
            "trade_count": [20],
            "notional": [25_000_000.0],
        }
    )
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    series = runner.run(
        MetricRunRequest(
            metric=registry.get("price_impact_30s_bps"),
            period=_period(),
            group_by=["sector"],
            table_names={"trades": "trade", "quotes": "quote"},
            parameters={"max_quote_age": "500ms", "max_horizon_quote_age": "2s"},
        )
    )

    assert series.metric_name == "price_impact_30s_bps"
    assert series.values == (4.75,)
    assert series.observations[0].group == {"sector": "Banks"}
    assert series.observations[0].metadata == {
        "trade_count": 20,
        "notional": 25_000_000.0,
    }
    assert series.metadata["template"] == "price_impact.q"

    query = client.queries[0]
    assert "rawTrades: trade lj refs" in query
    assert "rawQuotes: quote lj refs" in query
    assert "horizonTime: time + 0D00:00:30.000" in query
    assert "horizonQuoteAge <= 0D00:00:02.000" in query
    assert "price_impact_30s_bps: med" in query


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
            table_names={
                "venue_trades": "venue_trade",
                "primary_quotes": "quote",
            },
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
    assert series.metadata["template"] == "toxicity_reversion.q"
    assert series.metadata["group_by"] == ("venue", "horizon", "sym")

    query = client.queries[0]
    assert "rawVenueTrades: venue_trade lj refs" in query
    assert "rawQuotes: quote lj refs" in query
    assert "venue in `TSE`SBIJ" in query
    assert "venue = `TSE" in query
    assert "time + 0D00:00:00.100" in query
    assert "horizon: $\"100ms\"" in query
    assert "horizon_sort_order: 2" in query
    assert "primaryQuoteAge <= 0D00:00:00.500" in query
    assert "venueQuoteAge <= 0D00:00:00.500" in query
    assert "`date`sym`venue`time xasc venueQuotes" in query
    assert "inferAggressorSide[tradePrice; venueMid]" in query
    assert "primary_quote_reversion_100ms_bps: .mmsr.weightedAverage[notional; reversion_bps]" in query
    assert "by date, time_bucket:" in query
    assert ", venue, horizon:" in query
    assert ", sym" in query




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
                table_names={"trades": "trade"},
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
                table_names={"quotes": "quote"},
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
                table_names={
                    "venue_trades": "venue_trade",
                    "primary_quotes": "quote",
                },
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
                table_names={
                    "venue_trades": "venue_trade",
                    "primary_quotes": "quote",
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
                table_names={"quotes": "quote"},
            )
        )

    assert client.queries == []


def test_runner_requires_metric_source_mapping() -> None:
    registry = build_default_registry()
    client = FakeKdbClient({})
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    with pytest.raises(KdbMetricRunnerError, match="missing source_functions or table_names entry"):
        runner.run(
            MetricRunRequest(
                metric=registry.get("quoted_spread_bps"),
                period=_period(),
                group_by=[],
                table_names={"trades": "trade"},
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
                table_names={"trades": "trade"},
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
        metadata={"template": "liquidity.q"},
    )

    assert series.metric_name == "quoted_spread_bps"
    assert series.metadata == {"template": "liquidity.q"}
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
    assert ".desk.mmsr.sumNotional" in client.queries[0]
    assert ".desk.mmsr.medianTopOfBookDepth" in client.queries[0]
