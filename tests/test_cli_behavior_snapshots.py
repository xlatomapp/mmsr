from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import typer
import typer.main
from typer.testing import CliRunner

from mmsr.cli import CLI_HELP, build_cli_app


@dataclass(frozen=True)
class CliDefaultSnapshot:
    command: str
    output: str
    template_dir: str | None
    title: str | None
    brand_name: str | None
    generated_at_text: str | None
    no_appendix: bool
    max_metric_cards: int | None
    max_comments: int | None
    max_table_rows: int | None
    max_chart_points: int | None
    max_heatmap_cells: int | None
    include_intraday_heatmaps: bool
    no_drilldown_page: bool
    max_drilldown_rows: int | None


EXPECTED_DEMO_OPTIONS = (
    "--output",
    "--template-dir",
    "--title",
    "--brand-name",
    "--generated-at-text",
    "--no-appendix",
    "--max-metric-cards",
    "--max-comments",
    "--max-table-rows",
    "--max-chart-points",
    "--max-heatmap-cells",
    "--include-intraday-heatmaps",
    "--no-drilldown-page",
    "--max-drilldown-rows",
)


def _click_root():
    return typer.main.get_command(build_cli_app())


def _click_command(command: str):
    return _click_root().commands[command]


def _command_params(command: str, args: list[str] | None = None) -> dict:
    ctx = _click_command(command).make_context(
        f"mmsr {command}",
        args or [],
        resilient_parsing=False,
    )
    return ctx.params


def _command_options(command: str) -> set[str]:
    option_names: set[str] = set()
    for param in _click_command(command).params:
        option_names.update(param.opts)
        option_names.update(param.secondary_opts)
    return option_names


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_top_level_help_snapshot_lists_current_commands() -> None:
    result = CliRunner().invoke(build_cli_app(), ["--help"], prog_name="mmsr")

    assert result.exit_code == 0
    help_text = _strip_ansi(result.output)
    assert "Usage:" in help_text
    assert "mmsr" in help_text
    assert "offline-demo" in help_text
    assert "mock-kdb-demo" in help_text
    assert CLI_HELP in help_text


@pytest.mark.parametrize(
    ("command", "expected_output"),
    (
        ("offline-demo", "mmsr_offline_demo.html"),
        ("mock-kdb-demo", "mmsr_mock_kdb_demo.html"),
    ),
)
def test_demo_command_default_argument_snapshots(
    command: str,
    expected_output: str,
) -> None:
    args = _command_params(command)

    snapshot = CliDefaultSnapshot(
        command=command,
        output=str(Path(args["output"])),
        template_dir=args["template_dir"],
        title=args["title"],
        brand_name=args["brand_name"],
        generated_at_text=args["generated_at_text"],
        no_appendix=args["no_appendix"],
        max_metric_cards=args["max_metric_cards"],
        max_comments=args["max_comments"],
        max_table_rows=args["max_table_rows"],
        max_chart_points=args["max_chart_points"],
        max_heatmap_cells=args["max_heatmap_cells"],
        include_intraday_heatmaps=args["include_intraday_heatmaps"],
        no_drilldown_page=args["no_drilldown_page"],
        max_drilldown_rows=args["max_drilldown_rows"],
    )
    assert snapshot == CliDefaultSnapshot(
        command=command,
        output=expected_output,
        template_dir=None,
        title=None,
        brand_name=None,
        generated_at_text=None,
        no_appendix=False,
        max_metric_cards=None,
        max_comments=None,
        max_table_rows=None,
        max_chart_points=None,
        max_heatmap_cells=None,
        include_intraday_heatmaps=False,
        no_drilldown_page=False,
        max_drilldown_rows=None,
    )


@pytest.mark.parametrize("command", ("offline-demo", "mock-kdb-demo"))
def test_demo_command_override_argument_snapshot(command: str) -> None:
    args = _command_params(
        command,
        [
            "--output",
            "reports/custom.html",
            "--template-dir",
            "templates",
            "--title",
            "Custom Title",
            "--brand-name",
            "Custom Brand",
            "--generated-at-text",
            "fixed timestamp",
            "--no-appendix",
            "--max-metric-cards",
            "1",
            "--max-comments",
            "2",
            "--max-table-rows",
            "3",
            "--max-chart-points",
            "4",
            "--max-heatmap-cells",
            "5",
            "--include-intraday-heatmaps",
            "--no-drilldown-page",
            "--max-drilldown-rows",
            "6",
        ],
    )

    assert args["output"] == "reports/custom.html"
    assert args["template_dir"] == "templates"
    assert args["title"] == "Custom Title"
    assert args["brand_name"] == "Custom Brand"
    assert args["generated_at_text"] == "fixed timestamp"
    assert args["no_appendix"] is True
    assert args["max_metric_cards"] == 1
    assert args["max_comments"] == 2
    assert args["max_table_rows"] == 3
    assert args["max_chart_points"] == 4
    assert args["max_heatmap_cells"] == 5
    assert args["include_intraday_heatmaps"] is True
    assert args["no_drilldown_page"] is True
    assert args["max_drilldown_rows"] == 6


@pytest.mark.parametrize("command", ("offline-demo", "mock-kdb-demo"))
def test_demo_command_option_surface_snapshot(command: str) -> None:
    option_names = _command_options(command)

    for option in EXPECTED_DEMO_OPTIONS:
        assert option in option_names


def test_offline_demo_help_preserves_offline_safety_language() -> None:
    result = CliRunner().invoke(build_cli_app(), ["offline-demo", "--help"], prog_name="mmsr")

    assert result.exit_code == 0
    help_text = " ".join(_strip_ansi(result.output).split())
    assert "importing PyKX, connecting to kdb+, or calling an LLM" in help_text


def test_mock_kdb_demo_help_preserves_integration_boundary_language() -> None:
    result = CliRunner().invoke(
        build_cli_app(),
        ["mock-kdb-demo", "--help"],
        prog_name="mmsr",
    )

    assert result.exit_code == 0
    help_text = " ".join(_strip_ansi(result.output).split())
    assert "real q-template and KdbMetricRunner path" in help_text


def test_cli_application_uses_typer() -> None:
    app = build_cli_app()

    assert isinstance(app, typer.Typer)
