"""Command line interface for mmsr."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import typer

from mmsr.analysis.comparison import (
    ComparisonPolicy,
    ReferenceObservationSpec,
    compare_metric_timeseries,
)
from mmsr.config import load_report_config_file
from mmsr.config.models import ReportConfig
from mmsr.examples import (
    MockKdbIntegrationDemoOptions,
    OfflineDemoReportOptions,
    build_mock_kdb_integration_demo_report,
    build_offline_demo_report,
)
from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.production import (
    KdbProductionExecutor,
    KdbProductionPlanSummary,
    KdbProductionPreflight,
    KdbProductionPreflightResult,
)
from mmsr.kdb.query_loader import render_simulated_source_function_bootstrap
from mmsr.kdb.runner import KdbMetricRunner
from mmsr.logging import configure_logging
from mmsr.metrics.registry import build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.periods.calendar import KdbTradingCalendarSource
from mmsr.periods.symbols import KdbSymbolUniverseSource
from mmsr.report.market_report import (
    MarketReportInput,
    MarketReportOptions,
    build_market_monitor_report,
)
from mmsr.report.render_html import render_report_v2

CLI_HELP = "Generate Japanese market microstructure monitoring report artifacts."

app = typer.Typer(
    help=CLI_HELP,
    no_args_is_help=True,
    add_completion=False,
)

LOGGER = logging.getLogger(__name__)


def build_cli_app() -> typer.Typer:
    """Build the Typer command-line application."""

    return app


@app.command(
    "offline-demo",
    help=(
        "Render the deterministic mock-data production-format HTML report without "
        "importing PyKX, connecting to kdb+, or calling an LLM."
    ),
)
def _offline_demo_command(
    output: Path = typer.Option(
        Path("mmsr_offline_demo.html"),
        "--output",
        "-o",
        help="Output HTML path. Parent directories are created automatically.",
    ),
    template_dir: Path | None = typer.Option(
        None,
        "--template-dir",
        help="Optional directory containing report_v2.html.j2 and partial templates.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Override the mock-data report title.",
    ),
    brand_name: str | None = typer.Option(
        None,
        "--brand-name",
        help="Override the rendered report brand name.",
    ),
    generated_at_text: str | None = typer.Option(
        None,
        "--generated-at-text",
        help="Override the generated-at text shown in the rendered report.",
    ),
    no_appendix: bool = typer.Option(
        False,
        "--no-appendix",
        help="Omit the metric definitions appendix from the mock-data report.",
    ),
    max_metric_cards: int | None = typer.Option(
        None,
        "--max-metric-cards",
        help="Optional limit for summary metric cards.",
    ),
    max_comments: int | None = typer.Option(
        None,
        "--max-comments",
        help="Optional limit for deterministic commentary lines.",
    ),
    max_table_rows: int | None = typer.Option(
        None,
        "--max-table-rows",
        help="Optional limit for comparison table rows.",
    ),
    max_chart_points: int | None = typer.Option(
        None,
        "--max-chart-points",
        help="Optional limit for points per time-series chart.",
    ),
    max_heatmap_cells: int | None = typer.Option(
        None,
        "--max-heatmap-cells",
        help="Optional limit for cells per heatmap.",
    ),
    include_intraday_heatmaps: bool = typer.Option(
        False,
        "--include-intraday-heatmaps",
        help=("Opt into intraday heatmaps in addition to the default time-bucket line charts."),
    ),
    no_drilldown_page: bool = typer.Option(
        False,
        "--no-drilldown-page",
        help="Omit the sector, segment, and market-cap drilldown page.",
    ),
    max_drilldown_rows: int | None = typer.Option(
        None,
        "--max-drilldown-rows",
        help="Optional limit for drilldown table rows.",
    ),
    detailed_trends_granularity: str = typer.Option(
        "daily",
        "--detailed-trends-granularity",
        help="Detailed Metric Trends granularity: daily, weekly, monthly, quarterly, yearly.",
    ),
    include_automated_insights: bool = typer.Option(
        False,
        "--include-automated-insights",
        help="Render automated insight summaries in Detailed Metric Trends.",
    ),
) -> int:
    """Render an offline deterministic report without kdb+, PyKX, or an LLM."""

    options = _offline_demo_options_from_values(
        title=title,
        brand_name=brand_name,
        generated_at_text=generated_at_text,
        no_appendix=no_appendix,
        max_metric_cards=max_metric_cards,
        max_comments=max_comments,
        max_table_rows=max_table_rows,
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        no_drilldown_page=no_drilldown_page,
        max_drilldown_rows=max_drilldown_rows,
        detailed_trends_granularity=detailed_trends_granularity,
        include_automated_insights=include_automated_insights,
    )
    output_path = render_offline_demo_report_file(
        output,
        options=options,
        template_dir=template_dir,
    )
    typer.echo(f"Rendered mock-data production-format report: {output_path}")
    return 0


@app.command(
    "mock-kdb-demo",
    help=(
        "Execute deterministic mock kdb queries through the real q-template "
        "and KdbMetricRunner path, then render the canonical production-format "
        "HTML report without importing PyKX or connecting to production kdb+."
    ),
)
def _mock_kdb_demo_command(
    output: Path = typer.Option(
        Path("mmsr_mock_kdb_demo.html"),
        "--output",
        "-o",
        help="Output HTML path. Parent directories are created automatically.",
    ),
    template_dir: Path | None = typer.Option(
        None,
        "--template-dir",
        help="Optional directory containing report_v2.html.j2 and partial templates.",
    ),
    title: str | None = typer.Option(
        None,
        "--title",
        help="Override the mock-kdb report title.",
    ),
    brand_name: str | None = typer.Option(
        None,
        "--brand-name",
        help="Override the rendered report brand name.",
    ),
    generated_at_text: str | None = typer.Option(
        None,
        "--generated-at-text",
        help="Override the generated-at text shown in the rendered report.",
    ),
    no_appendix: bool = typer.Option(
        False,
        "--no-appendix",
        help="Omit the metric definitions appendix from the mock-kdb report.",
    ),
    max_metric_cards: int | None = typer.Option(
        None,
        "--max-metric-cards",
        help="Optional limit for summary metric cards.",
    ),
    max_comments: int | None = typer.Option(
        None,
        "--max-comments",
        help="Optional limit for deterministic commentary lines.",
    ),
    max_table_rows: int | None = typer.Option(
        None,
        "--max-table-rows",
        help="Optional limit for comparison table rows.",
    ),
    max_chart_points: int | None = typer.Option(
        None,
        "--max-chart-points",
        help="Optional limit for points per time-series chart.",
    ),
    max_heatmap_cells: int | None = typer.Option(
        None,
        "--max-heatmap-cells",
        help="Optional limit for cells per heatmap.",
    ),
    include_intraday_heatmaps: bool = typer.Option(
        False,
        "--include-intraday-heatmaps",
        help=("Opt into intraday heatmaps in addition to the default time-bucket line charts."),
    ),
    no_drilldown_page: bool = typer.Option(
        False,
        "--no-drilldown-page",
        help="Omit the sector, segment, and market-cap drilldown page.",
    ),
    max_drilldown_rows: int | None = typer.Option(
        None,
        "--max-drilldown-rows",
        help="Optional limit for drilldown table rows.",
    ),
    detailed_trends_granularity: str = typer.Option(
        "daily",
        "--detailed-trends-granularity",
        help="Detailed Metric Trends granularity: daily, weekly, monthly, quarterly, yearly.",
    ),
    include_automated_insights: bool = typer.Option(
        False,
        "--include-automated-insights",
        help="Render automated insight summaries in Detailed Metric Trends.",
    ),
) -> int:
    """Render the deterministic mock-kdb path through KdbMetricRunner."""

    options = _mock_kdb_demo_options_from_values(
        title=title,
        brand_name=brand_name,
        generated_at_text=generated_at_text,
        no_appendix=no_appendix,
        max_metric_cards=max_metric_cards,
        max_comments=max_comments,
        max_table_rows=max_table_rows,
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        no_drilldown_page=no_drilldown_page,
        max_drilldown_rows=max_drilldown_rows,
        detailed_trends_granularity=detailed_trends_granularity,
        include_automated_insights=include_automated_insights,
    )
    output_path = render_mock_kdb_demo_report_file(
        output,
        options=options,
        template_dir=template_dir,
    )
    typer.echo(f"Rendered mock-kdb integration report: {output_path}")
    return 0


@app.command(
    "plan",
    help=(
        "Summarize the production kdb-backed render plan without executing "
        "metric q. The command loads config, calls the kdb trading-calendar "
        "function, derives target/reference trading days, and prints source-function "
        "schema contracts."
    ),
)
def _plan_command(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML report config path.",
    ),
    kdb_host: str = typer.Option(
        ...,
        "--kdb-host",
        help="kdb+ host for the production plan summary.",
    ),
    kdb_port: int = typer.Option(
        ...,
        "--kdb-port",
        help="kdb+ port for the production plan summary.",
    ),
    kdb_username: str | None = typer.Option(
        None,
        "--kdb-username",
        help="Optional kdb+ username.",
    ),
    kdb_password: str | None = typer.Option(
        None,
        "--kdb-password",
        help="Optional kdb+ password.",
    ),
    symbol: list[str] | None = typer.Option(
        None,
        "--symbol",
        help=(
            "Optional symbol filter for planning. Repeat the option for "
            "multiple symbols; configured symbol_chunk_size is applied."
        ),
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose DEBUG logging for production execution diagnostics.",
    ),
    log_level: str | None = typer.Option(
        None,
        "--log-level",
        help="Explicit Python log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    ),
    inject_simulated_sources: bool = typer.Option(
        False,
        "--inject-simulated-sources",
        help=(
            "Install deterministic simulated source getter functions into the "
            "connected kdb process before planning and route calendar/reference/"
            "trade/quote source calls to that namespace."
        ),
    ),
    simulated_source_namespace: str | None = typer.Option(
        None,
        "--simulated-source-namespace",
        help=(
            "q namespace for injected simulated source getters. Defaults to the "
            "configured raw_data_functions namespace."
        ),
    ),
    simulated_symbol_count: int = typer.Option(
        240,
        "--simulated-symbol-count",
        help="Number of synthetic symbols baked into the injected simulated q source functions.",
    ),
    simulated_points_per_symbol_per_day: int = typer.Option(
        1200,
        "--simulated-points-per-symbol-per-day",
        help="Guidance points per symbol per day for simulated q sources (actual per-symbol count jitters by +/-20%).",
    ),
) -> int:
    """Print target/reference execution scope without running metric q."""

    configure_logging(verbose=verbose, log_level=log_level)
    LOGGER.info("Starting production plan command")
    summary = summarize_production_report_plan(
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
    )
    for line in summary.summary_lines():
        typer.echo(line)
    return 0


@app.command(
    "render",
    help=(
        "Render a production kdb-backed report from a YAML config. The command "
        "uses the production executor, a kdb-backed trading-calendar function, "
        "user-defined raw-data functions, and MMSR-owned calculation templates."
    ),
)
def _render_command(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML report config path.",
    ),
    output: Path = typer.Option(
        Path("mmsr_report.html"),
        "--output",
        "-o",
        help="Output HTML path. Parent directories are created automatically.",
    ),
    kdb_host: str = typer.Option(
        ...,
        "--kdb-host",
        help="kdb+ host for the production report run.",
    ),
    kdb_port: int = typer.Option(
        ...,
        "--kdb-port",
        help="kdb+ port for the production report run.",
    ),
    kdb_username: str | None = typer.Option(
        None,
        "--kdb-username",
        help="Optional kdb+ username.",
    ),
    kdb_password: str | None = typer.Option(
        None,
        "--kdb-password",
        help="Optional kdb+ password.",
    ),
    symbol: list[str] | None = typer.Option(
        None,
        "--symbol",
        help=(
            "Optional symbol filter. Repeat the option for multiple symbols; "
            "configured symbol_chunk_size is applied before kdb execution."
        ),
    ),
    template_dir: Path | None = typer.Option(
        None,
        "--template-dir",
        help="Optional directory containing report_v2.html.j2 and partial templates.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose DEBUG logging for production execution diagnostics.",
    ),
    log_level: str | None = typer.Option(
        None,
        "--log-level",
        help="Explicit Python log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    ),
    inject_simulated_sources: bool = typer.Option(
        False,
        "--inject-simulated-sources",
        help=(
            "Install deterministic simulated source getter functions into the "
            "connected kdb process before planning and route calendar/reference/"
            "trade/quote source calls to that namespace."
        ),
    ),
    simulated_source_namespace: str | None = typer.Option(
        None,
        "--simulated-source-namespace",
        help=(
            "q namespace for injected simulated source getters. Defaults to the "
            "configured raw_data_functions namespace."
        ),
    ),
    simulated_symbol_count: int = typer.Option(
        240,
        "--simulated-symbol-count",
        help="Number of synthetic symbols baked into the injected simulated q source functions.",
    ),
    simulated_points_per_symbol_per_day: int = typer.Option(
        1200,
        "--simulated-points-per-symbol-per-day",
        help="Guidance points per symbol per day for simulated q sources (actual per-symbol count jitters by +/-20%).",
    ),
    isolate_calculation_namespace_per_run: bool = typer.Option(
        True,
        "--isolate-calculation-namespace-per-run/--no-isolate-calculation-namespace-per-run",
        help=(
            "Install and execute MMSR-owned q calculations in a per-run namespace "
            "suffix (<calculation_namespace>.run_<guid>)."
        ),
    ),
    keep_isolated_calculation_namespace: bool = typer.Option(
        False,
        "--keep-isolated-calculation-namespace",
        help=(
            "When namespace isolation is enabled, keep the per-run calculation "
            "namespace after completion for kdb-side debugging."
        ),
    ),
    detailed_trends_granularity: str = typer.Option(
        "daily",
        "--detailed-trends-granularity",
        help="Detailed Metric Trends granularity: daily, weekly, monthly, quarterly, yearly.",
    ),
    include_automated_insights: bool = typer.Option(
        False,
        "--include-automated-insights",
        help="Render automated insight summaries in Detailed Metric Trends.",
    ),
) -> int:
    """Render a production report by executing configured kdb source functions."""

    configure_logging(verbose=verbose, log_level=log_level)
    LOGGER.info("Starting production render command")
    output_path = render_production_report_file(
        output,
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
        template_dir=template_dir,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
        isolate_calculation_namespace_per_run=isolate_calculation_namespace_per_run,
        keep_isolated_calculation_namespace=keep_isolated_calculation_namespace,
        detailed_trends_granularity=detailed_trends_granularity,
        include_automated_insights=include_automated_insights,
    )
    typer.echo(f"Rendered production kdb-backed report: {output_path}")
    return 0


@app.command(
    "preflight",
    help=(
        "Validate a production kdb-backed report config before a full run. "
        "The command loads the config, checks configured q names, calls the "
        "kdb trading-calendar function, plans the first bounded metric step, executes "
        "that single step, and validates the returned schema."
    ),
)
def _preflight_command(
    config: Path = typer.Option(
        ...,
        "--config",
        "-c",
        help="YAML report config path.",
    ),
    kdb_host: str = typer.Option(
        ...,
        "--kdb-host",
        help="kdb+ host for the production preflight run.",
    ),
    kdb_port: int = typer.Option(
        ...,
        "--kdb-port",
        help="kdb+ port for the production preflight run.",
    ),
    kdb_username: str | None = typer.Option(
        None,
        "--kdb-username",
        help="Optional kdb+ username.",
    ),
    kdb_password: str | None = typer.Option(
        None,
        "--kdb-password",
        help="Optional kdb+ password.",
    ),
    symbol: list[str] | None = typer.Option(
        None,
        "--symbol",
        help=("Optional symbol filter for the bounded sample step. Repeat the option for multiple symbols."),
    ),
    metric: str | None = typer.Option(
        None,
        "--metric",
        help=("Optional configured metric name to validate instead of the first configured metric."),
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose DEBUG logging for production execution diagnostics.",
    ),
    log_level: str | None = typer.Option(
        None,
        "--log-level",
        help="Explicit Python log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    ),
    inject_simulated_sources: bool = typer.Option(
        False,
        "--inject-simulated-sources",
        help=(
            "Install deterministic simulated source getter functions into the "
            "connected kdb process before planning and route calendar/reference/"
            "trade/quote source calls to that namespace."
        ),
    ),
    simulated_source_namespace: str | None = typer.Option(
        None,
        "--simulated-source-namespace",
        help=(
            "q namespace for injected simulated source getters. Defaults to the "
            "configured raw_data_functions namespace."
        ),
    ),
    simulated_symbol_count: int = typer.Option(
        240,
        "--simulated-symbol-count",
        help="Number of synthetic symbols baked into the injected simulated q source functions.",
    ),
    simulated_points_per_symbol_per_day: int = typer.Option(
        1200,
        "--simulated-points-per-symbol-per-day",
        help="Guidance points per symbol per day for simulated q sources (actual per-symbol count jitters by +/-20%).",
    ),
) -> int:
    """Run one bounded production metric step and print diagnostics."""

    configure_logging(verbose=verbose, log_level=log_level)
    LOGGER.info("Starting production preflight command")
    result = preflight_production_report(
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
        metric_name=metric,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
    )
    for line in result.summary_lines():
        typer.echo(line)
    return 0


def _kdb_calendar_source(
    client: KdbClient,
    report_config: ReportConfig,
) -> KdbTradingCalendarSource:
    """Build the configured user-function-backed kdb calendar source."""

    return KdbTradingCalendarSource(
        client=client,
        function=report_config.calendar.qualified_function(),
        date_column=report_config.calendar.date_column,
        calculation_namespace=report_config.kdb.calculation_namespace,
    )


def _kdb_symbol_source(
    client: KdbClient,
    report_config: ReportConfig,
) -> KdbSymbolUniverseSource:
    """Build the reference-data-backed kdb universe source."""

    return KdbSymbolUniverseSource(
        client=client,
        function=report_config.reference_data.qualified_function(),
        symbol_column=report_config.reference_data.symbol_column,
    )


def _simulated_source_namespace_for_config(
    report_config: ReportConfig,
    simulated_source_namespace: str | None,
) -> str:
    """Return the q namespace to install and route simulated getters through."""

    if simulated_source_namespace is not None:
        return simulated_source_namespace
    return report_config.kdb.raw_data_functions.namespace


def _report_config_with_simulated_source_functions(
    report_config: ReportConfig,
    *,
    source_namespace: str,
) -> ReportConfig:
    """Route all source-function boundaries to injected simulated q getters."""

    simulated_raw_functions = replace(
        report_config.kdb.raw_data_functions,
        namespace=source_namespace,
        trade="getTrade",
        quote="getQuote",
        pts_trade="getPtsTrade",
        pts_quote="getPtsQuote",
        primary_quote="getPrimaryQuote",
        reference_data="getRef",
        venue_trade=None,
        venue_quote=None,
    )
    simulated_kdb = replace(
        report_config.kdb,
        raw_data_functions=simulated_raw_functions,
    )
    simulated_calendar = replace(
        report_config.calendar,
        source="kdb",
        namespace=source_namespace,
        function="getTradingCalendar",
    )
    simulated_reference = replace(
        report_config.reference_data,
        source="kdb",
        namespace=source_namespace,
        function="getRef",
    )
    simulated_symbols = replace(
        report_config.symbols,
        source="kdb",
        namespace=source_namespace,
        function="getRef",
    )
    return replace(
        report_config,
        kdb=simulated_kdb,
        calendar=simulated_calendar,
        reference_data=simulated_reference,
        symbols=simulated_symbols,
    )


def _maybe_inject_simulated_source_functions(
    *,
    client: KdbClient,
    report_config: ReportConfig,
    inject_simulated_sources: bool,
    simulated_source_namespace: str | None,
    simulated_symbol_count: int,
    simulated_points_per_symbol_per_day: int,
) -> ReportConfig:
    """Optionally install simulated q getters and return the routed config.

    The kdb process can still be remote. This helper only sends a q bootstrap to
    the configured connection before normal plan/preflight/render execution; it
    does not switch to the local Python simulated client.
    """

    if not inject_simulated_sources:
        return report_config

    source_namespace = _simulated_source_namespace_for_config(
        report_config,
        simulated_source_namespace,
    )
    LOGGER.info(
        "Injecting simulated source functions into remote kdb namespace %s with symbol_count=%s points_per_symbol_per_day=%s",
        source_namespace,
        simulated_symbol_count,
        simulated_points_per_symbol_per_day,
    )
    client.execute(
        render_simulated_source_function_bootstrap(
            source_namespace,
            symbol_count=simulated_symbol_count,
            points_per_symbol_per_day=simulated_points_per_symbol_per_day,
        )
    )
    return _report_config_with_simulated_source_functions(
        report_config,
        source_namespace=source_namespace,
    )


def summarize_production_report_plan(
    *,
    config_path: str | Path,
    kdb_host: str,
    kdb_port: int,
    kdb_username: str | None = None,
    kdb_password: str | None = None,
    symbols: Sequence[str] | None = None,
    inject_simulated_sources: bool = False,
    simulated_source_namespace: str | None = None,
    simulated_symbol_count: int = 240,
    simulated_points_per_symbol_per_day: int = 1200,
) -> KdbProductionPlanSummary:
    """Return a production execution summary without executing metric q."""

    LOGGER.info("Loading production config from %s", config_path)
    report_config, period = load_report_config_file(config_path)
    LOGGER.info(
        "Loaded config title=%r period=%s..%s metrics=%s",
        report_config.title,
        period.start_date,
        period.end_date,
        ", ".join(report_config.metrics),
    )
    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
    )
    report_config = _maybe_inject_simulated_source_functions(
        client=client,
        report_config=report_config,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
    )
    calendar = _kdb_calendar_source(client, report_config)
    symbol_source = _kdb_symbol_source(client, report_config)
    runner = KdbMetricRunner(client)
    runner.install_calculation_functions(report_config.kdb.calculation_namespace)
    executor = KdbProductionExecutor(
        runner=runner,
        calendar_source=calendar,
        symbol_source=symbol_source,
    )
    return executor.build_plan_summary(
        config=report_config,
        period=period,
        symbols=symbols,
    )


def preflight_production_report(
    *,
    config_path: str | Path,
    kdb_host: str,
    kdb_port: int,
    kdb_username: str | None = None,
    kdb_password: str | None = None,
    symbols: Sequence[str] | None = None,
    metric_name: str | None = None,
    inject_simulated_sources: bool = False,
    simulated_source_namespace: str | None = None,
    simulated_symbol_count: int = 240,
    simulated_points_per_symbol_per_day: int = 1200,
) -> KdbProductionPreflightResult:
    """Run a bounded production preflight against the configured kdb endpoint."""

    LOGGER.info("Loading production config from %s", config_path)
    report_config, period = load_report_config_file(config_path)
    LOGGER.info(
        "Loaded config title=%r period=%s..%s metrics=%s",
        report_config.title,
        period.start_date,
        period.end_date,
        ", ".join(report_config.metrics),
    )
    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
    )
    report_config = _maybe_inject_simulated_source_functions(
        client=client,
        report_config=report_config,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
    )
    calendar = _kdb_calendar_source(client, report_config)
    symbol_source = _kdb_symbol_source(client, report_config)
    runner = KdbMetricRunner(client)
    runner.install_calculation_functions(report_config.kdb.calculation_namespace)
    preflight = KdbProductionPreflight(
        runner=runner,
        calendar_source=calendar,
        symbol_source=symbol_source,
    )
    return preflight.run(
        config=report_config,
        period=period,
        symbols=symbols,
        metric_name=metric_name,
    )


def render_production_report_file(
    output_path: str | Path,
    *,
    config_path: str | Path,
    kdb_host: str,
    kdb_port: int,
    kdb_username: str | None = None,
    kdb_password: str | None = None,
    symbols: Sequence[str] | None = None,
    template_dir: str | Path | None = None,
    inject_simulated_sources: bool = False,
    simulated_source_namespace: str | None = None,
    simulated_symbol_count: int = 240,
    simulated_points_per_symbol_per_day: int = 1200,
    isolate_calculation_namespace_per_run: bool = True,
    keep_isolated_calculation_namespace: bool = False,
    detailed_trends_granularity: str = "daily",
    include_automated_insights: bool = False,
) -> Path:
    """Render a production report through the production kdb executor.

    This is the live production path. It uses a PyKX-backed ``KdbClient`` unless
    tests inject lower-level fakes around ``KdbProductionExecutor`` directly.
    Raw trade/quote data remains behind the configured user source functions and
    q execution is scoped by the executor to one trading day and optional symbol
    chunk per metric request.
    """

    resolved_output_path = _validated_output_path(output_path)
    LOGGER.info("Loading production config from %s", config_path)
    report_config, period = load_report_config_file(config_path)
    LOGGER.info(
        "Loaded config title=%r period=%s..%s metrics=%s output=%s",
        report_config.title,
        period.start_date,
        period.end_date,
        ", ".join(report_config.metrics),
        resolved_output_path,
    )

    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
    )
    report_config = _maybe_inject_simulated_source_functions(
        client=client,
        report_config=report_config,
        inject_simulated_sources=inject_simulated_sources,
        simulated_source_namespace=simulated_source_namespace,
        simulated_symbol_count=simulated_symbol_count,
        simulated_points_per_symbol_per_day=simulated_points_per_symbol_per_day,
    )
    calendar = _kdb_calendar_source(client, report_config)
    symbol_source = _kdb_symbol_source(client, report_config)
    runner = KdbMetricRunner(
        client,
        isolate_calculation_namespace_per_run=isolate_calculation_namespace_per_run,
        keep_isolated_calculation_namespace=keep_isolated_calculation_namespace,
    )
    runner.install_calculation_functions(report_config.kdb.calculation_namespace)
    executor = KdbProductionExecutor(
        runner=runner,
        calendar_source=calendar,
        symbol_source=symbol_source,
    )
    LOGGER.info("Running target-period metric execution")
    current_series = executor.run(
        config=report_config,
        period=period,
        symbols=symbols,
    )
    LOGGER.info("Running reference-period metric execution")
    reference_series = executor.run_reference(
        config=report_config,
        period=period,
        symbols=symbols,
    )

    registry = build_default_registry()
    definitions = {metric_name: registry.get(metric_name) for metric_name in report_config.metrics}
    LOGGER.info("Building reference comparisons")
    comparisons = _compare_production_series(
        report_config=report_config,
        current_series=current_series,
        reference_series=reference_series,
    )
    document = build_market_monitor_report(
        MarketReportInput(
            metric_definitions=definitions,
            current_series=current_series,
            comparisons=comparisons,
            reference_series=reference_series,
        ),
        options=MarketReportOptions(
            title=report_config.title,
            brand_name=report_config.html.branding.brand_name,
            generated_at_text="production kdb-backed run",
            summary_scope_label="production kdb",
            include_metric_definitions_appendix=True,
            include_toxicity_reversion_page=report_config.toxicity.enabled,
            detailed_metric_trends_granularity=detailed_trends_granularity,
            include_automated_insights=include_automated_insights,
        ),
    )
    LOGGER.info("Rendering HTML report")
    html = render_report_v2(document, template_dir=template_dir)

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(html, encoding="utf-8")
    LOGGER.info("Wrote HTML report to %s", resolved_output_path)
    return resolved_output_path


def _compare_production_series(
    *,
    report_config: ReportConfig,
    current_series: Sequence[MetricTimeSeries],
    reference_series: Sequence[MetricTimeSeries],
) -> tuple[MetricComparison, ...]:
    registry = build_default_registry()
    policy = ComparisonPolicy(
        reference_observation=ReferenceObservationSpec(
            observation_unit=report_config.reference.observation_unit,
            comparable_keys=tuple(report_config.reference.comparable_keys),
        ),
        min_samples_for_z_score=report_config.reference.min_samples_for_z_score,
        min_samples_for_empirical_percentile=(report_config.reference.min_samples_for_empirical_percentile),
    )
    metric_directions = {
        metric_name: registry.get(metric_name).higher_is_better for metric_name in report_config.metrics
    }
    return tuple(
        compare_metric_timeseries(
            _observations_from_series(current_series),
            _observations_from_series(reference_series),
            method=_reference_comparison_method(report_config.reference.default_technical_score),
            metric_directions=metric_directions,
            policy=policy,
            reference_observation_aggregation=_reference_observation_aggregation(report_config.reference.statistic),
        )
    )


def _observations_from_series(
    series: Sequence[MetricTimeSeries],
) -> tuple[MetricObservation, ...]:
    observations: list[MetricObservation] = []
    for item in series:
        observations.extend(item.observations)
    return tuple(observations)


def _reference_comparison_method(score_name: str) -> str:
    normalized = score_name.strip().lower()
    if normalized in {"standard", "standard_z_score", "z_score"}:
        return "standard"
    return "robust"


def _reference_observation_aggregation(statistic: str) -> str:
    normalized = statistic.strip().lower()
    if normalized in {"mean", "median", "sum", "first", "last"}:
        return normalized
    return "mean"


def render_offline_demo_report_file(
    output_path: str | Path,
    *,
    options: OfflineDemoReportOptions | None = None,
    template_dir: str | Path | None = None,
) -> Path:
    """Render the deterministic mock-data report to an HTML file.

    The function is intentionally offline-only. It delegates mock data into the
    canonical production-format report builder, then uses ``render_report_v2()``,
    then writes the deterministic HTML artifact to ``output_path``.
    """

    resolved_output_path = _validated_output_path(output_path)

    document = build_offline_demo_report(options=options)
    LOGGER.info("Rendering HTML report")
    html = render_report_v2(document, template_dir=template_dir)

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(html, encoding="utf-8")
    return resolved_output_path


def render_mock_kdb_demo_report_file(
    output_path: str | Path,
    *,
    options: MockKdbIntegrationDemoOptions | None = None,
    template_dir: str | Path | None = None,
) -> Path:
    """Render the deterministic mock-kdb integration report to an HTML file.

    This command path executes rendered q through a deterministic mock client and
    the real ``KdbMetricRunner`` before delegating into the canonical report
    builder. It remains offline and does not import PyKX.
    """

    resolved_output_path = _validated_output_path(output_path)

    document = build_mock_kdb_integration_demo_report(options=options)
    LOGGER.info("Rendering HTML report")
    html = render_report_v2(document, template_dir=template_dir)

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(html, encoding="utf-8")
    return resolved_output_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Typer command-line interface and return a process exit code."""

    args = list(argv) if argv is not None else None
    try:
        result = app(args=args, prog_name="mmsr", standalone_mode=False)
    except typer.Exit as exc:
        return int(exc.exit_code or 0)
    except Exception as exc:
        if exc.__class__.__name__ == "NoArgsIsHelpError":
            return 0
        raise

    return int(result or 0)


def _validated_output_path(output_path: str | Path) -> Path:
    resolved_output_path = Path(output_path)
    if resolved_output_path.exists() and resolved_output_path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")
    return resolved_output_path


def _offline_demo_options_from_values(
    *,
    title: str | None,
    brand_name: str | None,
    generated_at_text: str | None,
    no_appendix: bool,
    max_metric_cards: int | None,
    max_comments: int | None,
    max_table_rows: int | None,
    max_chart_points: int | None,
    max_heatmap_cells: int | None,
    include_intraday_heatmaps: bool,
    no_drilldown_page: bool,
    max_drilldown_rows: int | None,
    detailed_trends_granularity: str,
    include_automated_insights: bool,
) -> OfflineDemoReportOptions:
    defaults = OfflineDemoReportOptions()
    return OfflineDemoReportOptions(
        title=title or defaults.title,
        brand_name=brand_name or defaults.brand_name,
        generated_at_text=generated_at_text or defaults.generated_at_text,
        summary_page_title=defaults.summary_page_title,
        detail_page_title=defaults.detail_page_title,
        comparison_table_title=defaults.comparison_table_title,
        comparison_help_text=defaults.comparison_help_text,
        detail_help_text=defaults.detail_help_text,
        include_metric_definitions_appendix=not no_appendix,
        max_metric_cards=_default_when_none(
            max_metric_cards,
            defaults.max_metric_cards,
        ),
        max_comments=_default_when_none(max_comments, defaults.max_comments),
        max_table_rows=_default_when_none(
            max_table_rows,
            defaults.max_table_rows,
        ),
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        include_drilldown_page=not no_drilldown_page,
        max_drilldown_rows=_default_when_none(
            max_drilldown_rows,
            defaults.max_drilldown_rows,
        ),
        detailed_metric_trends_granularity=detailed_trends_granularity,
        include_automated_insights=include_automated_insights,
    )


def _mock_kdb_demo_options_from_values(
    *,
    title: str | None,
    brand_name: str | None,
    generated_at_text: str | None,
    no_appendix: bool,
    max_metric_cards: int | None,
    max_comments: int | None,
    max_table_rows: int | None,
    max_chart_points: int | None,
    max_heatmap_cells: int | None,
    include_intraday_heatmaps: bool,
    no_drilldown_page: bool,
    max_drilldown_rows: int | None,
    detailed_trends_granularity: str,
    include_automated_insights: bool,
) -> MockKdbIntegrationDemoOptions:
    defaults = MockKdbIntegrationDemoOptions()
    return MockKdbIntegrationDemoOptions(
        title=title or defaults.title,
        brand_name=brand_name or defaults.brand_name,
        generated_at_text=generated_at_text or defaults.generated_at_text,
        summary_page_title=defaults.summary_page_title,
        detail_page_title=defaults.detail_page_title,
        comparison_table_title=defaults.comparison_table_title,
        comparison_help_text=defaults.comparison_help_text,
        detail_help_text=defaults.detail_help_text,
        include_metric_definitions_appendix=not no_appendix,
        max_metric_cards=_default_when_none(
            max_metric_cards,
            defaults.max_metric_cards,
        ),
        max_comments=_default_when_none(max_comments, defaults.max_comments),
        max_table_rows=_default_when_none(
            max_table_rows,
            defaults.max_table_rows,
        ),
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        max_overview_metrics=defaults.max_overview_metrics,
        include_drilldown_page=not no_drilldown_page,
        max_drilldown_rows=_default_when_none(
            max_drilldown_rows,
            defaults.max_drilldown_rows,
        ),
        detailed_metric_trends_granularity=detailed_trends_granularity,
        include_automated_insights=include_automated_insights,
    )


def _default_when_none(value: int | None, default: int | None) -> int | None:
    if value is None:
        return default
    return value


if __name__ == "__main__":
    raise SystemExit(main())
