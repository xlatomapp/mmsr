"""Command line interface for mmsr."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import typer

from mmsr.analysis.comparison import (
    ComparisonPolicy,
    ReferenceObservationSpec,
    compare_metric_timeseries,
)
from mmsr.config import load_report_config_file
from mmsr.config.models import ReportConfig
from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.production import (
    KdbProductionExecutor,
    KdbProductionPlanSummary,
    KdbProductionPreflight,
    KdbProductionPreflightResult,
)
from mmsr.kdb.runner import KdbMetricRunner
from mmsr.metrics.registry import build_default_registry
from mmsr.metrics.results import MetricComparison, MetricObservation, MetricTimeSeries
from mmsr.periods.calendar import KdbTradingCalendarSource
from mmsr.periods.symbols import KdbSymbolUniverseSource
from mmsr.report.market_report import (
    MarketReportInput,
    MarketReportOptions,
    build_market_monitor_report,
)
from mmsr.examples import (
    MockKdbIntegrationDemoOptions,
    OfflineDemoReportOptions,
    build_mock_kdb_integration_demo_report,
    build_offline_demo_report,
)
from mmsr.report.render_html import render_report

CLI_HELP = "Generate Japanese market microstructure monitoring report artifacts."

app = typer.Typer(
    help=CLI_HELP,
    no_args_is_help=True,
    add_completion=False,
)


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
        help="Optional directory containing report.html.j2 and partial templates.",
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
        help=(
            "Opt into intraday heatmaps in addition to the default time-bucket "
            "line charts."
        ),
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
        help="Optional directory containing report.html.j2 and partial templates.",
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
        help=(
            "Opt into intraday heatmaps in addition to the default time-bucket "
            "line charts."
        ),
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
) -> int:
    """Print target/reference execution scope without running metric q."""

    summary = summarize_production_report_plan(
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
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
        help="Optional directory containing report.html.j2 and partial templates.",
    ),
) -> int:
    """Render a production report by executing configured kdb source functions."""

    output_path = render_production_report_file(
        output,
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
        template_dir=template_dir,
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
        help=(
            "Optional symbol filter for the bounded sample step. Repeat the "
            "option for multiple symbols."
        ),
    ),
    metric: str | None = typer.Option(
        None,
        "--metric",
        help=(
            "Optional configured metric name to validate instead of the first "
            "configured metric."
        ),
    ),
) -> int:
    """Run one bounded production metric step and print diagnostics."""

    result = preflight_production_report(
        config_path=config,
        kdb_host=kdb_host,
        kdb_port=kdb_port,
        kdb_username=kdb_username,
        kdb_password=kdb_password,
        symbols=symbol,
        metric_name=metric,
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


def summarize_production_report_plan(
    *,
    config_path: str | Path,
    kdb_host: str,
    kdb_port: int,
    kdb_username: str | None = None,
    kdb_password: str | None = None,
    symbols: Sequence[str] | None = None,
) -> KdbProductionPlanSummary:
    """Return a production execution summary without executing metric q."""

    report_config, period = load_report_config_file(config_path)
    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
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
) -> KdbProductionPreflightResult:
    """Run a bounded production preflight against the configured kdb endpoint."""

    report_config, period = load_report_config_file(config_path)
    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
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
) -> Path:
    """Render a production report through the production kdb executor.

    This is the live production path. It uses a PyKX-backed ``KdbClient`` unless
    tests inject lower-level fakes around ``KdbProductionExecutor`` directly.
    Raw trade/quote data remains behind the configured user source functions and
    q execution is scoped by the executor to one trading day and optional symbol
    chunk per metric request.
    """

    resolved_output_path = _validated_output_path(output_path)
    report_config, period = load_report_config_file(config_path)

    client = KdbClient(
        KdbConfig(
            host=kdb_host,
            port=kdb_port,
            username=kdb_username,
            password=kdb_password,
        )
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
    current_series = executor.run(
        config=report_config,
        period=period,
        symbols=symbols,
    )
    reference_series = executor.run_reference(
        config=report_config,
        period=period,
        symbols=symbols,
    )

    registry = build_default_registry()
    definitions = {
        metric_name: registry.get(metric_name)
        for metric_name in report_config.metrics
    }
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
        ),
    )
    html = render_report(document, template_dir=template_dir)

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(html, encoding="utf-8")
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
        min_samples_for_empirical_percentile=(
            report_config.reference.min_samples_for_empirical_percentile
        ),
    )
    metric_directions = {
        metric_name: registry.get(metric_name).higher_is_better
        for metric_name in report_config.metrics
    }
    return tuple(
        compare_metric_timeseries(
            _observations_from_series(current_series),
            _observations_from_series(reference_series),
            method=_reference_comparison_method(
                report_config.reference.default_technical_score
            ),
            metric_directions=metric_directions,
            policy=policy,
            reference_observation_aggregation=_reference_observation_aggregation(
                report_config.reference.statistic
            ),
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
    canonical production-format report builder, then uses ``render_report()``,
    then writes the deterministic HTML artifact to ``output_path``.
    """

    resolved_output_path = _validated_output_path(output_path)

    document = build_offline_demo_report(options=options)
    html = render_report(document, template_dir=template_dir)

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
    html = render_report(document, template_dir=template_dir)

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
        max_table_rows=max_table_rows,
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        include_drilldown_page=not no_drilldown_page,
        max_drilldown_rows=_default_when_none(
            max_drilldown_rows,
            defaults.max_drilldown_rows,
        ),
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
        max_table_rows=max_table_rows,
        max_chart_points=max_chart_points,
        max_heatmap_cells=max_heatmap_cells,
        include_intraday_heatmaps=include_intraday_heatmaps,
        max_overview_metrics=defaults.max_overview_metrics,
        include_drilldown_page=not no_drilldown_page,
        max_drilldown_rows=_default_when_none(
            max_drilldown_rows,
            defaults.max_drilldown_rows,
        ),
    )


def _default_when_none(value: int | None, default: int) -> int:
    if value is None:
        return default
    return value

if __name__ == "__main__":
    raise SystemExit(main())
