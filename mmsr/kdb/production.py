"""Production kdb execution orchestration.

This module owns the production execution shape that sits above individual q
metric templates. It deliberately builds one-trading-day ``MetricRunRequest``
objects and, when configured, reference-universe symbol chunks. The user-owned
reference-data function chooses the analysis universe; raw trade/quote rows
remain inside kdb and are provided by user-defined source functions; MMSR q
templates perform the metric calculations under the configured namespace.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any

from mmsr.config.models import ReportConfig
from mmsr.kdb.query_plan import MetricRunRequest, RenderedMetricQuery
from mmsr.kdb.runner import KdbMetricRunner
from mmsr.kdb.schema_contracts import QTemplateInputTableSchemaContract
from mmsr.metrics.registry import MetricRegistry, build_default_registry
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.periods.calendar import TradingCalendarSource
from mmsr.periods.models import ReportPeriod
from mmsr.periods.symbols import SymbolUniverseSource


class KdbProductionExecutionError(ValueError):
    """Raised when a production kdb execution plan cannot be built safely."""


@dataclass(frozen=True)
class KdbProductionMetricContract:
    """Rendered q-template contract for one configured production metric.

    The contract is derived from ``KdbMetricRunner.plan_query()`` and therefore
    does not execute metric q. It records the user source-function/table roles
    and the result schema that a full production run will validate after kdb
    execution.
    """

    metric_name: str
    template_name: str
    source_contracts: tuple[QTemplateInputTableSchemaContract, ...]
    required_output_columns: tuple[str, ...]
    optional_output_columns: tuple[str, ...] = ()


@dataclass(frozen=True)
class KdbProductionPlanSummary:
    """Operator-facing summary of a bounded production render plan."""

    config_title: str
    target_trading_days: tuple[date, ...]
    reference_trading_days: tuple[date, ...]
    metric_names: tuple[str, ...]
    symbol_chunk_count: int
    target_step_count: int
    reference_step_count: int
    calculation_namespace: str
    source_functions: tuple[tuple[str, str], ...]
    reference_data_function: str | None
    metric_contracts: tuple[KdbProductionMetricContract, ...]

    @property
    def metric_count(self) -> int:
        """Number of configured metrics in execution order."""

        return len(self.metric_names)

    @property
    def total_step_count(self) -> int:
        """Total bounded metric q executions planned for target and reference."""

        return self.target_step_count + self.reference_step_count

    def summary_lines(self) -> tuple[str, ...]:
        """Return stable human-readable lines for CLI diagnostics."""

        lines = [
            "Production plan summary:",
            f"Report: {self.config_title}",
            (
                f"Target trading days: {len(self.target_trading_days)} "
                f"({_format_date_summary(self.target_trading_days)})"
            ),
            (
                f"Reference trading days: {len(self.reference_trading_days)} "
                f"({_format_date_summary(self.reference_trading_days)})"
            ),
            f"Metrics: {self.metric_count} ({', '.join(self.metric_names)})",
            f"Symbol chunks per trading day: {self.symbol_chunk_count}",
            f"Target metric steps: {self.target_step_count}",
            f"Reference metric steps: {self.reference_step_count}",
            f"Total metric steps: {self.total_step_count}",
            f"Calculation namespace: {self.calculation_namespace}",
            "Source functions: " + _format_source_functions(self.source_functions),
            (
                "Reference-data universe function: "
                + (self.reference_data_function or "none")
            ),
            "Source-function contracts:",
        ]
        lines.extend(
            f"- {contract.metric_name}: {contract.template_name}; "
            f"inputs: {_format_input_contracts(contract.source_contracts)}; "
            f"outputs: {', '.join(contract.required_output_columns)}"
            for contract in self.metric_contracts
        )
        return tuple(lines)


@dataclass(frozen=True)
class KdbProductionPreflightCheck:
    """One deterministic preflight validation outcome."""

    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class KdbProductionPreflightResult:
    """Summary of the bounded production preflight run."""

    config_title: str
    trading_days: tuple[date, ...]
    preflight_step: ProductionMetricRunStep
    rendered_query: RenderedMetricQuery
    result_row_count: int
    checks: tuple[KdbProductionPreflightCheck, ...]

    @property
    def ok(self) -> bool:
        """Return whether every recorded preflight check passed."""

        return all(check.status == "passed" for check in self.checks)

    def summary_lines(self) -> tuple[str, ...]:
        """Return stable human-readable summary lines for the CLI."""

        step = self.preflight_step
        return (
            f"Preflight status: {'passed' if self.ok else 'failed'}",
            f"Report: {self.config_title}",
            f"Calendar trading days: {len(self.trading_days)}",
            f"Sample metric: {step.metric_name}",
            f"Sample trading day: {step.trading_day.isoformat()}",
            f"Sample symbol chunk: {step.symbol_chunk_id}/{step.symbol_chunk_count}",
            f"Sample template: {self.rendered_query.template_name}",
            "Required output columns: "
            + ", ".join(self.rendered_query.required_output_columns),
            f"Validated sample rows: {self.result_row_count}",
        )


@dataclass(frozen=True)
class ProductionMetricRunStep:
    """One bounded kdb metric execution unit.

    A step is always scoped to one trading date. ``symbols`` contains the
    current symbol slice used to filter the reference table passed to raw source
    functions. It is empty only for direct-planner callers that deliberately do
    not use a reference-data source or explicit CLI symbols.
    """

    trading_day: date
    metric_name: str
    symbol_chunk_id: int
    symbol_chunk_count: int
    symbols: tuple[str, ...]
    request: MetricRunRequest


@dataclass(frozen=True)
class KdbProductionRunPlan:
    """Ordered production execution plan for a report period."""

    steps: tuple[ProductionMetricRunStep, ...]

    @property
    def trading_days(self) -> tuple[date, ...]:
        """Unique trading days covered by the plan in execution order."""

        return _dedupe_dates(step.trading_day for step in self.steps)

    @property
    def metric_names(self) -> tuple[str, ...]:
        """Unique metric names covered by the plan in execution order."""

        return _dedupe_strings(step.metric_name for step in self.steps)


@dataclass(frozen=True)
class KdbProductionReferenceWindow:
    """Calendar-derived reference window for bounded production execution."""

    period: ReportPeriod
    trading_days: tuple[date, ...]
    lookback_days: int
    calendar_start: date
    calendar_end: date


@dataclass(frozen=True)
class KdbProductionExecutionPlanner:
    """Build production ``MetricRunRequest`` objects from report config.

    The planner does not execute IO. It converts a report period plus a confirmed
    trading calendar into one-day metric requests using configured raw
    source-functions and the configured MMSR calculation namespace.
    """

    registry: MetricRegistry = field(default_factory=build_default_registry)

    def build_plan(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        trading_days: Sequence[date],
        symbols: Sequence[str] | None = None,
        symbols_by_day: Mapping[date, Sequence[str]] | None = None,
    ) -> KdbProductionRunPlan:
        """Return an ordered date/chunk/metric execution plan."""

        bounded_days = _validate_trading_days(period, trading_days)
        day_symbols = _symbols_by_trading_day(
            trading_days=bounded_days,
            symbols=symbols,
            symbols_by_day=symbols_by_day,
        )
        steps: list[ProductionMetricRunStep] = []
        for trading_day in bounded_days:
            daily_period = _daily_period(period, trading_day)
            symbol_chunks = _symbol_chunks(
                day_symbols[trading_day],
                config.kdb.symbol_chunk_size,
            )
            for chunk_index, chunk_symbols in enumerate(symbol_chunks, start=1):
                for metric_name in config.metrics:
                    metric = self.registry.get(metric_name)
                    parameters = dict(config.metric_parameters_for(metric_name))
                    if chunk_symbols:
                        parameters["symbols"] = chunk_symbols
                    steps.append(
                        ProductionMetricRunStep(
                            trading_day=trading_day,
                            metric_name=metric_name,
                            symbol_chunk_id=chunk_index,
                            symbol_chunk_count=len(symbol_chunks),
                            symbols=chunk_symbols,
                            request=MetricRunRequest(
                                metric=metric,
                                period=daily_period,
                                group_by=list(config.group_by),
                                parameters=parameters,
                                source_functions=config.kdb.source_functions(),
                                calculation_namespace=config.kdb.calculation_namespace,
                            ),
                        )
                    )

        return KdbProductionRunPlan(steps=tuple(steps))


class KdbProductionExecutor:
    """Execute production metric plans through ``KdbMetricRunner``.

    The executor is production-facing: it asks the configured trading calendar
    for trading days, builds date-bounded requests, executes them through the
    real runner abstraction, and returns normalized ``MetricTimeSeries`` objects.
    Offline tests can supply fake calendar/runner implementations without
    changing this production path.
    """

    def __init__(
        self,
        *,
        runner: KdbMetricRunner,
        calendar_source: TradingCalendarSource,
        symbol_source: SymbolUniverseSource | None = None,
        planner: KdbProductionExecutionPlanner | None = None,
    ) -> None:
        self.runner = runner
        self.calendar_source = calendar_source
        self.symbol_source = symbol_source
        self.planner = (
            KdbProductionExecutionPlanner() if planner is None else planner
        )

    def build_plan(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
    ) -> KdbProductionRunPlan:
        """Build the target-period execution plan using the configured calendar."""

        trading_days = self.calendar_source.trading_days(
            period.start_date,
            period.end_date,
        )
        return self.planner.build_plan(
            config=config,
            period=period,
            trading_days=trading_days,
            symbols=symbols,
            symbols_by_day=self._symbols_by_day(
                trading_days,
                explicit_symbols=symbols,
            ),
        )

    def build_reference_window(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
    ) -> KdbProductionReferenceWindow:
        """Return the previous trading-day reference window from config lookback."""

        return _reference_window_from_calendar(
            calendar_source=self.calendar_source,
            target_period=period,
            lookback_days=config.reference.lookback_days,
        )

    def build_reference_plan(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
    ) -> KdbProductionRunPlan:
        """Build a bounded reference-period plan from ``reference.lookback_days``."""

        window = self.build_reference_window(config=config, period=period)
        return self.planner.build_plan(
            config=config,
            period=window.period,
            trading_days=window.trading_days,
            symbols=symbols,
            symbols_by_day=self._symbols_by_day(
                window.trading_days,
                explicit_symbols=symbols,
            ),
        )

    def build_plan_summary(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
    ) -> KdbProductionPlanSummary:
        """Summarize target/reference production execution without metric IO."""

        target_plan = self.build_plan(
            config=config,
            period=period,
            symbols=symbols,
        )
        reference_window = self.build_reference_window(config=config, period=period)
        reference_plan = self.planner.build_plan(
            config=config,
            period=reference_window.period,
            trading_days=reference_window.trading_days,
            symbols=symbols,
            symbols_by_day=self._symbols_by_day(
                reference_window.trading_days,
                explicit_symbols=symbols,
            ),
        )
        return KdbProductionPlanSummary(
            config_title=config.title,
            target_trading_days=target_plan.trading_days,
            reference_trading_days=reference_plan.trading_days,
            metric_names=target_plan.metric_names,
            symbol_chunk_count=_symbol_chunk_count(target_plan),
            target_step_count=len(target_plan.steps),
            reference_step_count=len(reference_plan.steps),
            calculation_namespace=config.kdb.calculation_namespace,
            source_functions=tuple(sorted(config.kdb.source_functions().items())),
            reference_data_function=_symbol_source_label(self.symbol_source),
            metric_contracts=_metric_contracts_from_plan(
                runner=self.runner,
                plan=target_plan,
            ),
        )

    def run(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
    ) -> tuple[MetricTimeSeries, ...]:
        """Execute target-period metric steps and combine rows by metric name."""

        plan = self.build_plan(
            config=config,
            period=period,
            symbols=symbols,
        )
        return self._run_plan(config=config, plan=plan, execution_role="target")

    def run_reference(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
    ) -> tuple[MetricTimeSeries, ...]:
        """Execute bounded reference observations before the target period."""

        window = self.build_reference_window(config=config, period=period)
        plan = self.planner.build_plan(
            config=config,
            period=window.period,
            trading_days=window.trading_days,
            symbols=symbols,
            symbols_by_day=self._symbols_by_day(
                window.trading_days,
                explicit_symbols=symbols,
            ),
        )
        return self._run_plan(
            config=config,
            plan=plan,
            execution_role="reference",
            reference_window=window,
        )

    def _symbols_by_day(
        self,
        trading_days: Sequence[date],
        *,
        explicit_symbols: Sequence[str] | None,
    ) -> dict[date, tuple[str, ...]] | None:
        if explicit_symbols is not None:
            return None
        if self.symbol_source is None:
            return None
        return {
            trading_day: _clean_string_tuple(
                self.symbol_source.symbols_for_day(trading_day),
                f"symbols for {trading_day.isoformat()}",
            )
            for trading_day in trading_days
        }

    def _run_plan(
        self,
        *,
        config: ReportConfig,
        plan: KdbProductionRunPlan,
        execution_role: str,
        reference_window: KdbProductionReferenceWindow | None = None,
    ) -> tuple[MetricTimeSeries, ...]:
        observations_by_metric: dict[str, list[MetricObservation]] = defaultdict(list)
        child_metadata_by_metric: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for step in plan.steps:
            series = self.runner.run(step.request)
            observations_by_metric[step.metric_name].extend(series.observations)
            child_metadata_by_metric[step.metric_name].append(
                {
                    "trading_day": step.trading_day,
                    "symbol_chunk_id": step.symbol_chunk_id,
                    "symbol_chunk_count": step.symbol_chunk_count,
                    "symbols": step.symbols,
                    "calculation_namespace": step.request.calculation_namespace,
                    "source_functions": tuple(
                        sorted(step.request.source_functions.items())
                    ),
                }
            )

        base_metadata: dict[str, Any] = {
            "execution": "production_kdb",
            "execution_role": execution_role,
            "raw_scope": "trading_day",
            "trading_days": plan.trading_days,
            "source_functions": tuple(sorted(config.kdb.source_functions().items())),
            "calculation_namespace": config.kdb.calculation_namespace,
        }
        if reference_window is not None:
            base_metadata.update(
                {
                    "reference_lookback_days": reference_window.lookback_days,
                    "reference_calendar_start": reference_window.calendar_start,
                    "reference_calendar_end": reference_window.calendar_end,
                }
            )

        return tuple(
            MetricTimeSeries.from_observations(
                observations,
                metric_name=metric_name,
                metadata={
                    **base_metadata,
                    "steps": tuple(child_metadata_by_metric[metric_name]),
                },
            )
            for metric_name, observations in observations_by_metric.items()
        )


class KdbProductionPreflight:
    """Run a bounded live-kdb preflight before full production rendering.

    The preflight intentionally uses the same calendar, planner, q-template, and
    runner boundary as the full production executor, but executes only the first
    date/chunk/metric step. That validates config parsing, configured q names,
    calendar access, rendered output-schema contracts, and the result schema
    returned by the sample metric query before a full report run is attempted.
    """

    def __init__(
        self,
        *,
        runner: KdbMetricRunner,
        calendar_source: TradingCalendarSource,
        symbol_source: SymbolUniverseSource | None = None,
        planner: KdbProductionExecutionPlanner | None = None,
    ) -> None:
        self.runner = runner
        self.calendar_source = calendar_source
        self.symbol_source = symbol_source
        self.planner = (
            KdbProductionExecutionPlanner() if planner is None else planner
        )

    def run(
        self,
        *,
        config: ReportConfig,
        period: ReportPeriod,
        symbols: Sequence[str] | None = None,
        metric_name: str | None = None,
    ) -> KdbProductionPreflightResult:
        """Execute one bounded metric step and return preflight diagnostics."""

        selected_metric_names = _preflight_metric_selection(
            metric_name=metric_name,
            configured_metrics=config.metrics,
        )
        source_functions = tuple(sorted(config.kdb.source_functions().items()))
        checks = [
            KdbProductionPreflightCheck(
                name="calculation_namespace",
                status="passed",
                detail=config.kdb.calculation_namespace,
            ),
            KdbProductionPreflightCheck(
                name="source_functions",
                status="passed",
                detail=", ".join(
                    f"{role}={function_name}"
                    for role, function_name in source_functions
                ),
            ),
            KdbProductionPreflightCheck(
                name="metric_selection",
                status="passed",
                detail=_format_metric_selection(
                    selected_metric_names,
                    config.metrics,
                ),
            ),
        ]

        trading_days = tuple(
            self.calendar_source.trading_days(period.start_date, period.end_date)
        )
        checks.append(
            KdbProductionPreflightCheck(
                name="calendar_access",
                status="passed",
                detail=(
                    f"{len(trading_days)} trading day(s) between "
                    f"{period.start_date.isoformat()} and {period.end_date.isoformat()}"
                ),
            )
        )

        symbols_by_day = self._symbols_by_day(
            trading_days,
            explicit_symbols=symbols,
        )
        if symbols_by_day is not None:
            checks.append(
                KdbProductionPreflightCheck(
                    name="symbol_universe_access",
                    status="passed",
                    detail=(
                        f"{sum(len(day_symbols) for day_symbols in symbols_by_day.values())} "
                        f"symbol assignment(s) across {len(symbols_by_day)} trading day(s)"
                    ),
                )
            )

        plan = self.planner.build_plan(
            config=config,
            period=period,
            trading_days=trading_days,
            symbols=symbols,
            symbols_by_day=symbols_by_day,
        )
        if not plan.steps:
            raise KdbProductionExecutionError(
                "production preflight could not build any metric execution steps"
            )

        step = _select_preflight_step(
            plan=plan,
            metric_names=selected_metric_names,
        )
        rendered_query = self.runner.plan_query(step.request)
        checks.append(
            KdbProductionPreflightCheck(
                name="query_plan",
                status="passed",
                detail=(
                    f"{rendered_query.template_name} requires "
                    + ", ".join(rendered_query.required_output_columns)
                ),
            )
        )

        series = self.runner.run(step.request)
        checks.append(
            KdbProductionPreflightCheck(
                name="sample_result_schema",
                status="passed",
                detail=(
                    f"validated {len(series.observations)} row(s) for "
                    f"{step.metric_name}"
                ),
            )
        )

        return KdbProductionPreflightResult(
            config_title=config.title,
            trading_days=plan.trading_days,
            preflight_step=step,
            rendered_query=rendered_query,
            result_row_count=len(series.observations),
            checks=tuple(checks),
        )

    def _symbols_by_day(
        self,
        trading_days: Sequence[date],
        *,
        explicit_symbols: Sequence[str] | None,
    ) -> dict[date, tuple[str, ...]] | None:
        if explicit_symbols is not None:
            return None
        if self.symbol_source is None:
            return None
        return {
            trading_day: _clean_string_tuple(
                self.symbol_source.symbols_for_day(trading_day),
                f"symbols for {trading_day.isoformat()}",
            )
            for trading_day in trading_days
        }


def _preflight_metric_selection(
    *,
    metric_name: str | None,
    configured_metrics: Sequence[str],
) -> tuple[str, ...]:
    if metric_name is None:
        return ()

    if not isinstance(metric_name, str) or not metric_name:
        raise KdbProductionExecutionError(
            "preflight metric selection must be a non-empty metric name"
        )

    configured = tuple(configured_metrics)
    if metric_name not in configured:
        configured_label = ", ".join(configured) if configured else "none"
        raise KdbProductionExecutionError(
            f"preflight metric {metric_name!r} is not configured for this report; "
            f"configured metrics: {configured_label}"
        )

    return (metric_name,)


def _format_metric_selection(
    metric_names: Sequence[str],
    configured_metrics: Sequence[str],
) -> str:
    if metric_names:
        return ", ".join(metric_names)
    configured = tuple(configured_metrics)
    if not configured:
        return "none"
    return f"default first configured metric ({configured[0]})"


def _select_preflight_step(
    *,
    plan: KdbProductionRunPlan,
    metric_names: Sequence[str],
) -> ProductionMetricRunStep:
    if not metric_names:
        return plan.steps[0]

    selected = set(metric_names)
    for step in plan.steps:
        if step.metric_name in selected:
            return step

    raise KdbProductionExecutionError(
        "production preflight could not find a metric execution step for "
        + ", ".join(metric_names)
    )


def _metric_contracts_from_plan(
    *,
    runner: KdbMetricRunner,
    plan: KdbProductionRunPlan,
) -> tuple[KdbProductionMetricContract, ...]:
    contracts_by_metric: dict[str, KdbProductionMetricContract] = {}
    for step in plan.steps:
        if step.metric_name in contracts_by_metric:
            continue
        rendered_query = runner.plan_query(step.request)
        contracts_by_metric[step.metric_name] = KdbProductionMetricContract(
            metric_name=step.metric_name,
            template_name=rendered_query.template_name,
            source_contracts=tuple(rendered_query.input_contracts),
            required_output_columns=rendered_query.required_output_columns,
            optional_output_columns=rendered_query.optional_output_columns,
        )
    return tuple(contracts_by_metric[metric_name] for metric_name in plan.metric_names)


def _symbols_by_trading_day(
    *,
    trading_days: Sequence[date],
    symbols: Sequence[str] | None,
    symbols_by_day: Mapping[date, Sequence[str]] | None,
) -> dict[date, tuple[str, ...]]:
    if symbols is not None and symbols_by_day is not None:
        raise KdbProductionExecutionError(
            "symbols and symbols_by_day cannot both be provided"
        )
    if symbols_by_day is None:
        clean_symbols = _clean_string_tuple(symbols, "symbols")
        return {trading_day: clean_symbols for trading_day in trading_days}

    resolved: dict[date, tuple[str, ...]] = {}
    for trading_day in trading_days:
        if trading_day not in symbols_by_day:
            raise KdbProductionExecutionError(
                "reference-data universe did not return symbols for "
                f"{trading_day.isoformat()}"
            )
        clean_symbols = _clean_string_tuple(
            symbols_by_day[trading_day],
            f"symbols for {trading_day.isoformat()}",
        )
        if not clean_symbols:
            raise KdbProductionExecutionError(
                "reference-data universe returned no symbols for "
                f"{trading_day.isoformat()}"
            )
        resolved[trading_day] = clean_symbols
    return resolved


def _symbol_source_label(symbol_source: SymbolUniverseSource | None) -> str | None:
    if symbol_source is None:
        return None
    return str(getattr(symbol_source, "function", type(symbol_source).__name__))


def _symbol_chunk_count(plan: KdbProductionRunPlan) -> int:
    if not plan.steps:
        return 0
    return max(step.symbol_chunk_count for step in plan.steps)


def _format_date_summary(days: Sequence[date]) -> str:
    ordered_days = tuple(days)
    if not ordered_days:
        return "none"
    if len(ordered_days) <= 3:
        return ", ".join(day.isoformat() for day in ordered_days)
    return f"{ordered_days[0].isoformat()}..{ordered_days[-1].isoformat()}"


def _format_source_functions(source_functions: Sequence[tuple[str, str]]) -> str:
    if not source_functions:
        return "none"
    return ", ".join(
        f"{role}={function_name}" for role, function_name in source_functions
    )


def _format_input_contracts(
    contracts: Sequence[QTemplateInputTableSchemaContract],
) -> str:
    if not contracts:
        return "none"
    return "; ".join(
        (
            f"{contract.table_role} via {contract.table_name} requires "
            f"{', '.join(contract.required_columns)}"
        )
        for contract in contracts
    )


def _reference_window_from_calendar(
    *,
    calendar_source: TradingCalendarSource,
    target_period: ReportPeriod,
    lookback_days: int,
) -> KdbProductionReferenceWindow:
    if lookback_days <= 0:
        raise KdbProductionExecutionError("reference.lookback_days must be positive")

    calendar_end = target_period.start_date - timedelta(days=1)
    # Trading calendars contain non-trading dates and exchange holidays. Query a
    # deterministic buffer before the target period, then keep the last requested
    # trading days so reference execution remains daily/chunk bounded.
    calendar_start = target_period.start_date - timedelta(
        days=max((lookback_days * 3) + 14, lookback_days + 14)
    )
    if calendar_start > calendar_end:
        raise KdbProductionExecutionError(
            "could not derive a reference calendar range before the target period"
        )

    candidate_days = tuple(
        sorted(
            day
            for day in calendar_source.trading_days(calendar_start, calendar_end)
            if calendar_start <= day <= calendar_end
        )
    )
    selected_days = candidate_days[-lookback_days:]
    if not selected_days:
        raise KdbProductionExecutionError(
            "trading calendar returned no reference trading days before "
            f"{target_period.start_date.isoformat()}"
        )

    return KdbProductionReferenceWindow(
        period=_period_for_trading_days(target_period, selected_days),
        trading_days=selected_days,
        lookback_days=lookback_days,
        calendar_start=calendar_start,
        calendar_end=calendar_end,
    )


def _period_for_trading_days(
    template_period: ReportPeriod,
    trading_days: Sequence[date],
) -> ReportPeriod:
    days = tuple(trading_days)
    if not days:
        raise KdbProductionExecutionError(
            "reference period requires at least one trading day"
        )
    return ReportPeriod(
        start_date=days[0],
        end_date=days[-1],
        sessions=list(template_period.sessions),
        bucket=template_period.bucket,
        timezone=template_period.timezone,
        labels=dict(template_period.labels),
    )


def _validate_trading_days(
    period: ReportPeriod,
    trading_days: Sequence[date],
) -> tuple[date, ...]:
    days = tuple(trading_days)
    if not days:
        raise KdbProductionExecutionError(
            "trading calendar returned no trading days for the requested period"
        )

    out_of_range = [
        day for day in days if day < period.start_date or day > period.end_date
    ]
    if out_of_range:
        raise KdbProductionExecutionError(
            "trading calendar returned date(s) outside the report period: "
            + ", ".join(day.isoformat() for day in out_of_range)
        )

    return days


def _daily_period(period: ReportPeriod, trading_day: date) -> ReportPeriod:
    return ReportPeriod(
        start_date=trading_day,
        end_date=trading_day,
        sessions=list(period.sessions),
        bucket=period.bucket,
        timezone=period.timezone,
        labels=dict(period.labels),
    )


def _symbol_chunks(
    symbols: Sequence[str] | None,
    chunk_size: int | None,
) -> tuple[tuple[str, ...], ...]:
    clean_symbols = _clean_string_tuple(symbols, "symbols")
    if not clean_symbols:
        return ((),)
    if chunk_size is None:
        return (clean_symbols,)

    return tuple(
        clean_symbols[index : index + chunk_size]
        for index in range(0, len(clean_symbols), chunk_size)
    )


def _clean_string_tuple(
    values: Sequence[str] | None,
    field_name: str,
) -> tuple[str, ...]:
    if values is None:
        return ()
    if isinstance(values, (str, bytes, bytearray)):
        raise KdbProductionExecutionError(
            f"{field_name} must be a sequence of strings, not a single string"
        )
    result = tuple(value for value in values if isinstance(value, str) and value)
    if len(result) != len(values):
        raise KdbProductionExecutionError(
            f"{field_name} must contain only non-empty strings"
        )
    return result


def _dedupe_dates(values: Sequence[date] | Any) -> tuple[date, ...]:
    seen: set[date] = set()
    out: list[date] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _dedupe_strings(values: Sequence[str] | Any) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)
