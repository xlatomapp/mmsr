from datetime import date, time

import pytest

from mmsr.config.models import (
    KdbExecutionConfig,
    KdbRawDataFunctionsConfig,
    ReferenceComparisonConfig,
    ReportConfig,
)
from mmsr.kdb.production import (
    KdbProductionExecutionError,
    KdbProductionExecutionPlanner,
    KdbProductionExecutor,
    KdbProductionPlanSummary,
    KdbProductionPreflight,
    KdbProductionReferenceWindow,
)
from mmsr.kdb.query_plan import KdbMetricQueryPlanner
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.periods import IntradayBucketSpec, ReportPeriod, TradingSession

def _period() -> ReportPeriod:
    return ReportPeriod(
        start_date=date(2026, 5, 1),
        end_date=date(2026, 5, 5),
        sessions=[
            TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
            TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
        ],
        bucket=IntradayBucketSpec("5m"),
    )

def test_production_execution_planner_builds_daily_kdb_owned_requests() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover", "quoted_spread_bps"],
        group_by=["sym"],
        kdb=KdbExecutionConfig(
            calculation_namespace=".desk.mmsrCalc",
            raw_data_functions=KdbRawDataFunctionsConfig(namespace=".sb.mmsr"),
            symbol_chunk_size=2,
        ),
    )

    plan = KdbProductionExecutionPlanner().build_plan(
        config=config,
        period=_period(),
        trading_days=[date(2026, 5, 1), date(2026, 5, 4)],
        symbols=["7203", "6758", "9984"],
    )

    assert len(plan.steps) == 4  # 2 days * 2 metrics; q owns symbol chunking
    assert plan.trading_days == (date(2026, 5, 1), date(2026, 5, 4))
    assert plan.metric_names == ("turnover", "quoted_spread_bps")

    first = plan.steps[0]
    assert first.trading_day == date(2026, 5, 1)
    assert first.symbol_chunk_id == 1
    assert first.symbol_chunk_count == 1
    assert first.symbols == ("7203", "6758", "9984")
    assert first.request.period.start_date == first.request.period.end_date
    assert first.request.period.start_date == date(2026, 5, 1)
    assert first.request.source_functions == {
        "trades": ".sb.mmsr.getTrade",
        "quotes": ".sb.mmsr.getQuote",
        "reference_data": ".sb.mmsr.getRef",
        "pts_trades": ".sb.mmsr.getTrade",
        "pts_quotes": ".sb.mmsr.getQuote",
        "primary_quotes": ".sb.mmsr.getQuote",
    }
    assert first.request.calculation_namespace == ".desk.mmsrCalc"
    assert first.request.parameters["symbols"] == ("7203", "6758", "9984")
    assert "symbol_chunk_id" not in first.request.parameters
    assert "symbol_chunk_count" not in first.request.parameters



def test_symbol_chunked_market_groups_add_per_symbol_aggregation_key() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover"],
        group_by=["topixCapGrp"],
        kdb=KdbExecutionConfig(symbol_chunk_size=2),
    )

    plan = KdbProductionExecutionPlanner().build_plan(
        config=config,
        period=_period(),
        trading_days=[date(2026, 5, 1)],
        symbols=["7203", "6758", "9984"],
    )

    request = plan.steps[0].request
    assert request.group_by == ["topixCapGrp"]

    query_plan = KdbMetricQueryPlanner().render(request)
    assert "calcActivity[rawTrades;refs;" in query_plan.query
    assert "calcActivity[rawTrades;refs;" in query_plan.query


def test_production_query_requests_are_daily_and_use_date_syms_source_args() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover"],
        kdb=KdbExecutionConfig(
            calculation_namespace=".desk.mmsrCalc",
            raw_data_functions=KdbRawDataFunctionsConfig(namespace=".sb.mmsr"),
            symbol_chunk_size=2,
        ),
    )
    plan = KdbProductionExecutionPlanner().build_plan(
        config=config,
        period=_period(),
        trading_days=[date(2026, 5, 1)],
        symbols=["7203", "6758"],
    )

    rendered = plan.steps[0].request
    query_plan = __import__(
        "mmsr.kdb.query_plan",
        fromlist=["KdbMetricQueryPlanner"],
    ).KdbMetricQueryPlanner().render(rendered)

    assert "`date`symbolChunkId`symbolChunkCount" not in query_plan.query
    assert '(`$"7203";`$"6758")' in query_plan.query
    assert "2026.05.01;1;1]" not in query_plan.query
    assert ".desk.mmsrCalc.calcActivity[rawTrades;refs;" in query_plan.query
    assert "rawRefs: select from (.sb.mmsr.getRef[2026.05.01]);" in query_plan.query
    assert 'refs: `sym xkey select from rawRefs where sym in (`$"7203";`$"6758");' in query_plan.query
    assert "rawTrades: (.sb.mmsr.getTrade[2026.05.01;0!refs]);" in query_plan.query
    assert "calcActivity[rawTrades;refs;" in query_plan.query

def test_production_planner_rejects_calendar_dates_outside_period() -> None:
    config = ReportConfig(title="Daily Monitor", metrics=["turnover"])

    with pytest.raises(KdbProductionExecutionError, match="outside the report period"):
        KdbProductionExecutionPlanner().build_plan(
            config=config,
            period=_period(),
            trading_days=[date(2026, 4, 30)],
        )

class ReferenceCalendar:
    def __init__(self) -> None:
        self.requests: list[tuple[date, date]] = []

    def trading_days(self, start: date, end: date) -> list[date]:
        self.requests.append((start, end))
        if end < date(2026, 5, 1):
            return [
                date(2026, 4, 24),
                date(2026, 4, 27),
                date(2026, 4, 28),
                date(2026, 4, 30),
            ]
        return [date(2026, 5, 1), date(2026, 5, 4)]

def test_production_reference_plan_uses_previous_trading_days_and_chunks() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["volume"],
        group_by=["sym"],
        reference=ReferenceComparisonConfig(lookback_days=3),
        kdb=KdbExecutionConfig(
            raw_data_functions=KdbRawDataFunctionsConfig(namespace=".sb.mmsr"),
            symbol_chunk_size=2,
        ),
    )
    calendar = ReferenceCalendar()
    executor = KdbProductionExecutor(
        runner=FakeRunner(),  # type: ignore[arg-type]
        calendar_source=calendar,
    )

    window = executor.build_reference_window(config=config, period=_period())
    plan = executor.build_reference_plan(
        config=config,
        period=_period(),
        symbols=["7203", "6758", "9984"],
    )

    assert isinstance(window, KdbProductionReferenceWindow)
    assert window.trading_days == (
        date(2026, 4, 27),
        date(2026, 4, 28),
        date(2026, 4, 30),
    )
    assert window.period.start_date == date(2026, 4, 27)
    assert window.period.end_date == date(2026, 4, 30)
    assert len(plan.steps) == 3  # 3 reference days * 1 metric; q owns symbol chunking
    assert plan.steps[0].request.period.start_date == date(2026, 4, 27)
    assert plan.steps[-1].symbols == ("7203", "6758", "9984")

def test_production_plan_summary_reports_scope_and_contracts() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["volume", "quoted_spread_bps"],
        group_by=["sym"],
        reference=ReferenceComparisonConfig(lookback_days=2),
        kdb=KdbExecutionConfig(
            calculation_namespace=".desk.mmsrCalc",
            raw_data_functions=KdbRawDataFunctionsConfig(namespace=".sb.mmsr"),
            symbol_chunk_size=2,
        ),
    )
    runner = FakeRunner()
    executor = KdbProductionExecutor(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=ReferenceCalendar(),
    )

    summary = executor.build_plan_summary(
        config=config,
        period=_period(),
        symbols=["7203", "6758", "9984"],
    )

    assert isinstance(summary, KdbProductionPlanSummary)
    assert summary.target_trading_days == (date(2026, 5, 1), date(2026, 5, 4))
    assert summary.reference_trading_days == (date(2026, 4, 28), date(2026, 4, 30))
    assert summary.metric_names == ("volume", "quoted_spread_bps")
    assert summary.metric_count == 2
    assert summary.symbol_chunk_count == 1
    assert summary.symbol_chunk_group_by == ("sym",)
    assert summary.target_step_count == 4
    assert summary.reference_step_count == 4
    assert summary.total_step_count == 8
    assert summary.calculation_namespace == ".desk.mmsrCalc"
    assert ("trades", ".sb.mmsr.getTrade") in summary.source_functions
    assert [contract.metric_name for contract in summary.metric_contracts] == [
        "volume",
        "quoted_spread_bps",
    ]
    assert summary.metric_contracts[0].template_name == "activity"
    assert summary.metric_contracts[1].template_name == "liquidity"
    assert "sym" in summary.metric_contracts[0].source_contracts[0].required_columns
    lines = "\n".join(summary.summary_lines())
    assert "Production plan summary:" in lines
    assert "Target trading days: 2 (2026-05-01, 2026-05-04)" in lines
    assert "Reference trading days: 2 (2026-04-28, 2026-04-30)" in lines
    assert "Symbol chunks per trading day: 1" in lines
    assert "Chunk aggregation groups: sym" in lines
    assert "Reference-data universe function: none" in lines
    assert ".sb.mmsr.getTrade" in lines
    assert "outputs: date, time_bucket, sym, volume, turnover, trade_count" in lines
    assert len(runner.requests) == 0
    assert len(runner.planned_requests) == 2

@pytest.mark.parametrize(
    ("metric_name", "template_name", "source_role"),
    [
        ("volume", "activity", "trades"),
        ("quoted_spread_bps", "liquidity", "quotes"),
        (
            "primary_quote_reversion_10ms_bps",
            "toxicity_reversion",
            "pts_trades",
        ),
    ],
)
def test_production_preflight_can_select_configured_metric(
    metric_name: str,
    template_name: str,
    source_role: str,
) -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=[
            "volume",
            "quoted_spread_bps",
            "primary_quote_reversion_10ms_bps",
        ],
        group_by=["sym"],
        kdb=KdbExecutionConfig(
            raw_data_functions=KdbRawDataFunctionsConfig(namespace=".sb.mmsr"),
            symbol_chunk_size=2,
        ),
    )
    runner = FakeRunner()
    preflight = KdbProductionPreflight(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=FakeCalendar(),
    )

    result = preflight.run(
        config=config,
        period=_period(),
        symbols=["7203", "6758"],
        metric_name=metric_name,
    )

    assert result.ok
    assert result.preflight_step.metric_name == metric_name
    assert result.rendered_query.template_name == template_name
    assert metric_name in result.rendered_query.required_output_columns
    assert source_role in dict(result.rendered_query.metric_queries[0].source_functions)
    assert len(runner.planned_requests) == 1
    assert len(runner.requests) == 1
    assert runner.requests[0].metric.name == metric_name
    assert any(
        check.name == "metric_selection" and check.detail == metric_name
        for check in result.checks
    )

def test_production_preflight_rejects_metric_not_configured() -> None:
    config = ReportConfig(title="Daily Monitor", metrics=["volume"])
    preflight = KdbProductionPreflight(
        runner=FakeRunner(),  # type: ignore[arg-type]
        calendar_source=FakeCalendar(),
    )

    with pytest.raises(KdbProductionExecutionError, match="is not configured"):
        preflight.run(
            config=config,
            period=_period(),
            metric_name="quoted_spread_bps",
        )

class FakeCalendar:
    def trading_days(self, start: date, end: date) -> list[date]:
        assert start == date(2026, 5, 1)
        assert end == date(2026, 5, 5)
        return [date(2026, 5, 1), date(2026, 5, 4)]

class FakeSymbolUniverse:
    function = ".sb.mmsr.getRef"

    def __init__(self) -> None:
        self.requests: list[date] = []

    def symbols_for_day(self, day: date) -> list[str]:
        self.requests.append(day)
        if day == date(2026, 5, 1):
            return ["7203", "6758"]
        return ["9984"]


class FakeRunner:
    def __init__(self) -> None:
        self.requests = []
        self.planned_requests = []
        self.batch_requests = []

    def plan_query(self, request):  # type: ignore[no-untyped-def]
        self.planned_requests.append(request)
        return KdbMetricQueryPlanner().render(request)

    def run(self, request):  # type: ignore[no-untyped-def]
        self.requests.append(request)
        return self._series_for_request(request)

    def run_batch(self, requests):  # type: ignore[no-untyped-def]
        self.batch_requests.append(tuple(requests))
        self.requests.extend(requests)
        return tuple(self._series_for_request(request) for request in requests)

    def plan_day(self, requests):  # type: ignore[no-untyped-def]
        self.planned_requests.extend(requests)
        return KdbMetricQueryPlanner().render_day(requests)

    def run_day(self, requests):  # type: ignore[no-untyped-def]
        self.batch_requests.append(tuple(requests))
        self.requests.extend(requests)
        return tuple(self._series_for_request(request) for request in requests)

    def _series_for_request(self, request):  # type: ignore[no-untyped-def]
        day = request.period.start_date
        return MetricTimeSeries.from_observations(
            [
                MetricObservation(
                    metric_name=request.metric.name,
                    date=day,
                    time_bucket="09:00",
                    group={"sym": request.parameters.get("symbols", ("ALL",))[0]},
                    value=100,
                )
            ],
            metric_name=request.metric.name,
            metadata={"child": True},
        )

def test_production_executor_uses_symbol_universe_when_symbols_not_explicit() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover"],
        group_by=["sym"],
        kdb=KdbExecutionConfig(symbol_chunk_size=1),
    )
    runner = FakeRunner()
    symbol_source = FakeSymbolUniverse()
    executor = KdbProductionExecutor(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=FakeCalendar(),
        symbol_source=symbol_source,
    )

    series = executor.run(
        config=config,
        period=_period(),
    )

    assert symbol_source.requests == []
    assert len(runner.requests) == 2  # 2 days; q owns symbol universe
    assert all("symbols" not in request.parameters for request in runner.requests)
    assert len(series[0].observations) == 2


def test_production_executor_uses_calendar_and_combines_metric_series() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover"],
        group_by=["sym"],
        kdb=KdbExecutionConfig(symbol_chunk_size=1),
    )
    runner = FakeRunner()
    executor = KdbProductionExecutor(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=FakeCalendar(),
    )

    series = executor.run(
        config=config,
        period=_period(),
        symbols=["7203", "6758"],
    )

    assert len(runner.requests) == 2  # 2 days * 1 metric; q owns chunking
    assert all(req.period.start_date == req.period.end_date for req in runner.requests)
    assert len(series) == 1
    assert series[0].metric_name == "turnover"
    assert len(series[0].observations) == 2
    assert series[0].metadata["execution"] == "production_kdb"
    assert series[0].metadata["raw_scope"] == "trading_day"
    assert series[0].metadata["trading_days"] == (
        date(2026, 5, 1),
        date(2026, 5, 4),
    )

def test_production_executor_batches_metrics_by_day_and_symbol_chunk() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover", "quoted_spread_bps"],
        group_by=["sym"],
        kdb=KdbExecutionConfig(symbol_chunk_size=1),
    )
    runner = FakeRunner()
    executor = KdbProductionExecutor(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=FakeCalendar(),
    )

    series = executor.run(
        config=config,
        period=_period(),
        symbols=["7203", "6758"],
    )

    assert [item.metric_name for item in series] == ["turnover", "quoted_spread_bps"]
    assert len(runner.batch_requests) == 2  # 2 days; q owns chunking
    assert all(len(batch) == 2 for batch in runner.batch_requests)
    assert len(runner.requests) == 4  # 2 days * 2 metrics
    assert all(
        step["batch_metric_count"] == 2
        for metric_series in series
        for step in metric_series.metadata["steps"]
    )


def test_production_executor_run_reference_marks_reference_metadata() -> None:
    config = ReportConfig(
        title="Daily Monitor",
        metrics=["turnover"],
        group_by=["sym"],
        reference=ReferenceComparisonConfig(lookback_days=2),
        kdb=KdbExecutionConfig(symbol_chunk_size=1),
    )
    runner = FakeRunner()
    executor = KdbProductionExecutor(
        runner=runner,  # type: ignore[arg-type]
        calendar_source=ReferenceCalendar(),
    )

    series = executor.run_reference(
        config=config,
        period=_period(),
        symbols=["7203"],
    )

    assert len(runner.requests) == 2  # last 2 reference days * 1 chunk * 1 metric
    assert len(series) == 1
    assert series[0].metadata["execution_role"] == "reference"
    assert series[0].metadata["reference_lookback_days"] == 2
    assert series[0].metadata["trading_days"] == (
        date(2026, 4, 28),
        date(2026, 4, 30),
    )
