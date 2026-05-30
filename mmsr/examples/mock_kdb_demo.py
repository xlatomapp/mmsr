"""Deterministic mock-kdb integration demo.

This module exercises the real kdb metric-runner boundary without requiring a
live kdb+ process or PyKX. A tiny deterministic client records rendered q queries
and returns table-shaped rows that the normal ``KdbMetricRunner`` converts into
``MetricTimeSeries`` objects. The resulting current/reference observations are
then compared and passed to the canonical market report builder.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, time
from typing import Any

from mmsr.analysis.comparison import ComparisonPolicy, compare_metric_timeseries
from mmsr.examples.offline_fixtures import SAMPLE_REFERENCE_DATES, SAMPLE_REPORT_DATE
from mmsr.kdb.runner import KdbMetricRunner, MetricRunRequest
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.registry import MetricRegistry, build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.periods.models import IntradayBucketSpec, ReportPeriod, TradingSession
from mmsr.report.components import ReportDocument
from mmsr.report.market_report import (
    MarketReportInput,
    MarketReportOptions,
    build_market_monitor_report,
)


_MOCK_KDB_METRIC_NAMES: tuple[str, ...] = (
    "quoted_spread_bps",
    "volume",
    "top_of_book_depth",
)
_MOCK_GROUP_BY: list[str] = ["market_cap_bucket"]
_MOCK_TABLE_NAMES = {
    "trades": "mock_trade",
    "quotes": "mock_quote",
}


@dataclass(frozen=True)
class MockKdbIntegrationDemoOptions:
    """Presentation options for the deterministic mock-kdb demo report."""

    title: str = "Japanese Market Microstructure Monitor — Mock kdb Integration Demo"
    brand_name: str = "mmsr mock kdb sample"
    generated_at_text: str = "deterministic mock kdb integration sample"
    summary_page_title: str = "Market Summary"
    detail_page_title: str = "Intraday Detail"
    comparison_table_title: str = "Current versus reference"
    comparison_help_text: str = (
        "Mock kdb current observations compared with deterministic historical "
        "trading-day reference observations for the same metric, bucket, and group."
    )
    detail_help_text: str = (
        "Rows on this page were produced by KdbMetricRunner from rendered q "
        "templates and a deterministic mock kdb client, then normalized into the "
        "same report-boundary schema expected from production kdb-backed runs."
    )
    daily_trend_page_title: str = "Reference and Target Daily Trends"
    daily_trend_help_text: str = (
        "Mock-kdb reference observations followed by target-period observations. "
        "The line visual keeps the trading day on the x-axis and carries bucket "
        "and market-cap context as series."
    )
    include_daily_trend_page: bool = True
    include_intraday_heatmaps: bool = False
    include_metric_definitions_appendix: bool = True
    max_metric_cards: int = 6
    max_comments: int = 5
    max_table_rows: int | None = 12
    max_chart_points: int | None = None
    max_heatmap_cells: int | None = None
    max_overview_metrics: int = 5
    include_drilldown_page: bool = True
    max_drilldown_rows: int | None = 12

    def __post_init__(self) -> None:
        _require_non_empty(self.title, "title")
        _require_non_empty(self.brand_name, "brand_name")
        _require_non_empty(self.generated_at_text, "generated_at_text")
        _require_non_empty(self.summary_page_title, "summary_page_title")
        _require_non_empty(self.detail_page_title, "detail_page_title")
        _require_non_empty(self.comparison_table_title, "comparison_table_title")
        _require_non_empty(self.comparison_help_text, "comparison_help_text")
        _require_non_empty(self.detail_help_text, "detail_help_text")
        _require_non_empty(self.daily_trend_page_title, "daily_trend_page_title")
        _require_non_empty(self.daily_trend_help_text, "daily_trend_help_text")
        _require_non_negative(self.max_metric_cards, "max_metric_cards")
        _require_non_negative(self.max_comments, "max_comments")
        _require_optional_non_negative(self.max_table_rows, "max_table_rows")
        _require_optional_non_negative(self.max_chart_points, "max_chart_points")
        _require_optional_non_negative(self.max_heatmap_cells, "max_heatmap_cells")
        _require_non_negative(self.max_overview_metrics, "max_overview_metrics")
        _require_optional_non_negative(self.max_drilldown_rows, "max_drilldown_rows")

    def to_market_report_options(self) -> MarketReportOptions:
        """Return equivalent canonical report options for the mock-kdb demo."""

        return MarketReportOptions(
            title=self.title,
            brand_name=self.brand_name,
            generated_at_text=self.generated_at_text,
            summary_page_title=self.summary_page_title,
            detail_page_title=self.detail_page_title,
            comparison_table_title=self.comparison_table_title,
            comparison_help_text=self.comparison_help_text,
            detail_help_text=self.detail_help_text,
            daily_trend_page_title=self.daily_trend_page_title,
            daily_trend_help_text=self.daily_trend_help_text,
            include_daily_trend_page=self.include_daily_trend_page,
            include_intraday_heatmaps=self.include_intraday_heatmaps,
            summary_scope_label="mock kdb integration",
            include_metric_definitions_appendix=(
                self.include_metric_definitions_appendix
            ),
            max_metric_cards=self.max_metric_cards,
            max_comments=self.max_comments,
            max_table_rows=self.max_table_rows,
            max_chart_points=self.max_chart_points,
            max_heatmap_cells=self.max_heatmap_cells,
            max_overview_metrics=self.max_overview_metrics,
            include_drilldown_page=self.include_drilldown_page,
            max_drilldown_rows=self.max_drilldown_rows,
        )


@dataclass(frozen=True)
class MockKdbIntegrationDemoResult:
    """Artifacts produced by the mock-kdb integration demo builder."""

    document: ReportDocument
    current_series: tuple[MetricTimeSeries, ...]
    reference_series: tuple[MetricTimeSeries, ...]
    comparisons: tuple[MetricComparison, ...]
    executed_queries: tuple[str, ...]


@dataclass
class DeterministicMockKdbClient:
    """Tiny client that records q and returns deterministic table-shaped results.

    It intentionally implements only the ``execute(query)`` method consumed by
    ``KdbMetricRunner``. It never imports PyKX and never opens a network socket.
    """

    queries: list[str] = field(default_factory=list)

    def execute(self, query: str, *args: Any) -> list[dict[str, Any]]:
        """Record a rendered q query and return deterministic mock rows."""

        if args:
            raise ValueError("the deterministic mock kdb client does not accept args")
        self.queries.append(query)
        if "MMSR reusable q utility library" in query:
            return []
        return _mock_rows_for_query(query)


def build_mock_kdb_integration_demo_result(
    *,
    options: MockKdbIntegrationDemoOptions | None = None,
) -> MockKdbIntegrationDemoResult:
    """Run the mock-kdb integration demo and return report plus diagnostics.

    The demo executes one rendered q template per configured metric for the
    current period and one per metric for the reference period. The resulting
    normalized series are compared and adapted into the canonical report path.
    """

    resolved_options = options or MockKdbIntegrationDemoOptions()
    registry = build_default_registry()
    definitions = _metric_definitions(registry)
    client = DeterministicMockKdbClient()
    runner = KdbMetricRunner(client)  # type: ignore[arg-type]

    current_series = _run_metric_series(
        runner,
        definitions=definitions,
        period=_current_period(),
        metadata_role="current",
    )
    reference_series = _run_metric_series(
        runner,
        definitions=definitions,
        period=_reference_period(),
        metadata_role="reference",
    )
    comparisons = _compare_series(current_series, reference_series, definitions)
    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=comparisons,
            reference_series=reference_series,
        ),
        options=resolved_options.to_market_report_options(),
    )

    return MockKdbIntegrationDemoResult(
        document=document,
        current_series=current_series,
        reference_series=reference_series,
        comparisons=comparisons,
        executed_queries=tuple(client.queries),
    )


def build_mock_kdb_integration_demo_report(
    *,
    options: MockKdbIntegrationDemoOptions | None = None,
) -> ReportDocument:
    """Build the production-format report document from mock-kdb execution."""

    return build_mock_kdb_integration_demo_result(options=options).document


def _run_metric_series(
    runner: KdbMetricRunner,
    *,
    definitions: dict[str, MetricDefinition],
    period: ReportPeriod,
    metadata_role: str,
) -> tuple[MetricTimeSeries, ...]:
    series: list[MetricTimeSeries] = []
    for metric_name in _MOCK_KDB_METRIC_NAMES:
        metric_series = runner.run(
            MetricRunRequest(
                metric=definitions[metric_name],
                period=period,
                group_by=list(_MOCK_GROUP_BY),
                table_names=dict(_MOCK_TABLE_NAMES),
            )
        )
        series.append(
            MetricTimeSeries(
                metric_name=metric_series.metric_name,
                observations=metric_series.observations,
                metadata={**metric_series.metadata, "role": metadata_role},
            )
        )
    return tuple(series)


def _compare_series(
    current_series: tuple[MetricTimeSeries, ...],
    reference_series: tuple[MetricTimeSeries, ...],
    definitions: dict[str, MetricDefinition],
) -> tuple[MetricComparison, ...]:
    directions = {
        metric_name: definition.higher_is_better
        for metric_name, definition in definitions.items()
    }
    return tuple(
        compare_metric_timeseries(
            _flatten_observations(current_series),
            _flatten_observations(reference_series),
            metric_directions=directions,
            policy=ComparisonPolicy(),
        )
    )


def _metric_definitions(registry: MetricRegistry) -> dict[str, MetricDefinition]:
    return {
        metric_name: registry.get(metric_name)
        for metric_name in _MOCK_KDB_METRIC_NAMES
    }


def _current_period() -> ReportPeriod:
    return ReportPeriod(
        start_date=SAMPLE_REPORT_DATE,
        end_date=SAMPLE_REPORT_DATE,
        sessions=_japan_cash_sessions(),
        bucket=IntradayBucketSpec("5m"),
    )


def _reference_period() -> ReportPeriod:
    return ReportPeriod(
        start_date=SAMPLE_REFERENCE_DATES[0],
        end_date=SAMPLE_REFERENCE_DATES[-1],
        sessions=_japan_cash_sessions(),
        bucket=IntradayBucketSpec("5m"),
    )


def _japan_cash_sessions() -> list[TradingSession]:
    return [
        TradingSession(time(9, 0), time(11, 30), name="AM"),
        TradingSession(time(12, 30), time(15, 0), name="PM"),
    ]


def _mock_rows_for_query(query: str) -> list[dict[str, Any]]:
    role = _query_role(query)
    if "mock_trade" in query:
        return _activity_rows(role)
    if "mock_quote" in query:
        return _liquidity_rows(role)
    raise ValueError("mock kdb client received an unsupported query")


def _query_role(query: str) -> str:
    if (
        "date within (2026.05.22;2026.05.22)" in query
        or "2026.05.22;2026.05.22" in query
    ):
        return "current"
    if (
        "date within (2026.04.06;2026.05.21)" in query
        or "2026.04.06;2026.05.21" in query
    ):
        return "reference"
    raise ValueError("mock kdb client received an unknown date range")


def _activity_rows(role: str) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "turnover": row["volume"] * 1500,
            "trade_count": round(row["volume"] / 1000),
            "mock_source": "deterministic_mock_kdb",
        }
        for row in _metric_rows(
            role,
            large_value=1_250_000,
            small_value=420_000,
            large_reference_base=1_170_000,
            small_reference_base=390_000,
            large_amplitude=55_000,
            small_amplitude=23_000,
            value_column="volume",
        )
    ]


def _liquidity_rows(role: str) -> list[dict[str, Any]]:
    spread_rows = _metric_rows(
        role,
        large_value=11.2,
        small_value=42.1,
        large_reference_base=10.4,
        small_reference_base=30.8,
        large_amplitude=0.7,
        small_amplitude=1.8,
        value_column="quoted_spread_bps",
    )
    depth_rows = _metric_rows(
        role,
        large_value=38_000,
        small_value=9_500,
        large_reference_base=40_500,
        small_reference_base=14_500,
        large_amplitude=2_300,
        small_amplitude=1_400,
        value_column="top_of_book_depth",
    )

    rows: list[dict[str, Any]] = []
    for spread_row, depth_row in zip(spread_rows, depth_rows, strict=True):
        rows.append(
            {
                "date": spread_row["date"],
                "time_bucket": spread_row["time_bucket"],
                "market_cap_bucket": spread_row["market_cap_bucket"],
                "quoted_spread_bps": spread_row["quoted_spread_bps"],
                "top_of_book_depth": depth_row["top_of_book_depth"],
                "mock_source": "deterministic_mock_kdb",
            }
        )
    return rows


def _metric_rows(
    role: str,
    *,
    large_value: float | int,
    small_value: float | int,
    large_reference_base: float,
    small_reference_base: float,
    large_amplitude: float,
    small_amplitude: float,
    value_column: str,
) -> list[dict[str, Any]]:
    if role == "current":
        return [
            _row(SAMPLE_REPORT_DATE, "AMO", "Large", value_column, large_value),
            _row(SAMPLE_REPORT_DATE, "09:00-09:05", "Small", value_column, small_value),
        ]

    rows: list[dict[str, Any]] = []
    for index, reference_date in enumerate(SAMPLE_REFERENCE_DATES):
        rows.append(
            _row(
                reference_date,
                "AMO",
                "Large",
                value_column,
                _cycle_value(large_reference_base, index, amplitude=large_amplitude),
            )
        )
        rows.append(
            _row(
                reference_date,
                "09:00-09:05",
                "Small",
                value_column,
                _cycle_value(small_reference_base, index, amplitude=small_amplitude),
            )
        )
    return rows


def _row(
    observation_date: date,
    time_bucket: str,
    market_cap_bucket: str,
    value_column: str,
    value: float | int,
) -> dict[str, Any]:
    return {
        "date": observation_date,
        "time_bucket": time_bucket,
        "market_cap_bucket": market_cap_bucket,
        value_column: value,
    }


def _cycle_value(base: float, index: int, *, amplitude: float) -> float | int:
    """Return a deterministic, bounded value around ``base``."""

    pattern = (-3, -2, -1, 0, 1, 2, 3, 2, 1, 0)
    value = base + amplitude * pattern[index % len(pattern)] / 3.0
    if float(base).is_integer() and float(amplitude).is_integer():
        return round(value)
    return value


def _flatten_observations(
    series_collection: Sequence[MetricTimeSeries],
) -> tuple[MetricObservation, ...]:
    return tuple(
        observation
        for series in series_collection
        for observation in series.observations
    )


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_non_negative(value: int, field_name: str) -> None:
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative")


def _require_optional_non_negative(value: int | None, field_name: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"{field_name} must be non-negative")


__all__ = [
    "DeterministicMockKdbClient",
    "MockKdbIntegrationDemoOptions",
    "MockKdbIntegrationDemoResult",
    "build_mock_kdb_integration_demo_report",
    "build_mock_kdb_integration_demo_result",
]
