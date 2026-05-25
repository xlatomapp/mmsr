from __future__ import annotations

import argparse
from dataclasses import dataclass

import pytest

from mmsr.cli import build_parser


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
    "--no-drilldown-page",
    "--max-drilldown-rows",
)


def test_top_level_help_snapshot_lists_current_commands(capsys: pytest.CaptureFixture[str]) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--help"])

    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    assert "usage: mmsr" in help_text
    assert "offline-demo" in help_text
    assert "mock-kdb-demo" in help_text
    assert "Generate Japanese market microstructure monitoring report artifacts." in help_text


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
    parser = build_parser()

    args = parser.parse_args([command])

    snapshot = CliDefaultSnapshot(
        command=args.command,
        output=args.output,
        template_dir=args.template_dir,
        title=args.title,
        brand_name=args.brand_name,
        generated_at_text=args.generated_at_text,
        no_appendix=args.no_appendix,
        max_metric_cards=args.max_metric_cards,
        max_comments=args.max_comments,
        max_table_rows=args.max_table_rows,
        max_chart_points=args.max_chart_points,
        max_heatmap_cells=args.max_heatmap_cells,
        no_drilldown_page=args.no_drilldown_page,
        max_drilldown_rows=args.max_drilldown_rows,
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
        no_drilldown_page=False,
        max_drilldown_rows=None,
    )


@pytest.mark.parametrize("command", ("offline-demo", "mock-kdb-demo"))
def test_demo_command_override_argument_snapshot(command: str) -> None:
    parser = build_parser()

    args = parser.parse_args(
        [
            command,
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
            "--no-drilldown-page",
            "--max-drilldown-rows",
            "6",
        ]
    )

    assert args.command == command
    assert args.output == "reports/custom.html"
    assert args.template_dir == "templates"
    assert args.title == "Custom Title"
    assert args.brand_name == "Custom Brand"
    assert args.generated_at_text == "fixed timestamp"
    assert args.no_appendix is True
    assert args.max_metric_cards == 1
    assert args.max_comments == 2
    assert args.max_table_rows == 3
    assert args.max_chart_points == 4
    assert args.max_heatmap_cells == 5
    assert args.no_drilldown_page is True
    assert args.max_drilldown_rows == 6


@pytest.mark.parametrize("command", ("offline-demo", "mock-kdb-demo"))
def test_demo_command_help_option_snapshot(
    command: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args([command, "--help"])

    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    assert f"usage: mmsr {command}" in help_text
    for option in EXPECTED_DEMO_OPTIONS:
        assert option in help_text


def test_offline_demo_help_preserves_offline_safety_language(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["offline-demo", "--help"])

    assert excinfo.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "without importing PyKX, connecting to kdb+, or calling an LLM" in help_text


def test_mock_kdb_demo_help_preserves_integration_boundary_language(
    capsys: pytest.CaptureFixture[str],
) -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["mock-kdb-demo", "--help"])

    assert excinfo.value.code == 0
    help_text = " ".join(capsys.readouterr().out.split())
    assert "through the real q-template and KdbMetricRunner path" in help_text
    assert "without importing PyKX or connecting to production kdb+" in help_text


def test_parser_remains_argparse_until_typer_migration_is_explicit() -> None:
    parser = build_parser()

    assert isinstance(parser, argparse.ArgumentParser)
