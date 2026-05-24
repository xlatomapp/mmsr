from __future__ import annotations

import sys

import pytest

from mmsr.cli import main, render_offline_demo_report_file
from mmsr.examples import OfflineDemoReportOptions


def test_render_offline_demo_report_file_writes_deterministic_html(tmp_path) -> None:
    output_path = tmp_path / "reports" / "offline-demo.html"

    rendered_path = render_offline_demo_report_file(output_path)

    assert rendered_path == output_path
    html = output_path.read_text(encoding="utf-8")
    assert "Japanese Market Microstructure Monitor — Offline Demo" in html
    assert "Offline Market Summary" in html
    assert "Metric Definitions Appendix" in html
    assert "time-series-chart__placeholder" in html
    assert "heatmap__placeholder" in html
    assert "pykx" not in sys.modules


def test_render_offline_demo_report_file_rejects_directory_output(tmp_path) -> None:
    with pytest.raises(ValueError, match="file path"):
        render_offline_demo_report_file(tmp_path)


def test_main_offline_demo_renders_to_requested_path(tmp_path, capsys) -> None:
    output_path = tmp_path / "demo.html"

    exit_code = main(
        [
            "offline-demo",
            "--output",
            str(output_path),
            "--title",
            "Custom Offline Demo",
            "--brand-name",
            "Custom Brand",
            "--generated-at-text",
            "fixed timestamp",
            "--max-metric-cards",
            "1",
            "--max-comments",
            "1",
            "--max-table-rows",
            "2",
            "--max-chart-points",
            "1",
            "--max-heatmap-cells",
            "1",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    assert "Custom Offline Demo" in html
    assert "Custom Brand" in html
    assert "Generated: fixed timestamp" in html
    assert html.count("metric-card") >= 1
    assert "Rendered offline demo report:" in capsys.readouterr().out


def test_main_offline_demo_can_omit_metric_definitions_appendix(tmp_path) -> None:
    output_path = tmp_path / "demo-no-appendix.html"

    exit_code = main(["offline-demo", "--output", str(output_path), "--no-appendix"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Offline Market Summary" in html
    assert "Metric Definitions Appendix" not in html


def test_main_without_command_prints_help(capsys) -> None:
    assert main([]) == 0
    assert "offline-demo" in capsys.readouterr().out


def test_offline_demo_cli_surfaces_option_validation(tmp_path) -> None:
    output_path = tmp_path / "bad.html"

    with pytest.raises(ValueError, match="max_metric_cards"):
        main(["offline-demo", "--output", str(output_path), "--max-metric-cards", "-1"])


def test_render_offline_demo_report_file_accepts_options(tmp_path) -> None:
    output_path = tmp_path / "custom.html"
    options = OfflineDemoReportOptions(
        title="Programmatic Offline Demo",
        include_metric_definitions_appendix=False,
        max_metric_cards=1,
        max_comments=1,
    )

    render_offline_demo_report_file(output_path, options=options)

    html = output_path.read_text(encoding="utf-8")
    assert "Programmatic Offline Demo" in html
    assert "Metric Definitions Appendix" not in html
