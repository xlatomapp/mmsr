from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mmsr.cli import (
    _resolve_pdf_browser_executable,
    export_report_html_to_pdf,
    main,
    render_offline_demo_report_file,
)
from mmsr.examples import OfflineDemoReportOptions


def test_render_offline_demo_report_file_writes_deterministic_html(tmp_path) -> None:
    output_path = tmp_path / "reports" / "offline-demo.html"

    rendered_path = render_offline_demo_report_file(output_path)

    assert rendered_path == output_path
    html = output_path.read_text(encoding="utf-8")
    assert "Japanese Market Microstructure Monitor — Mock Data Demo" in html
    assert "Market Summary" in html
    assert "Executive Market Overview" in html
    assert "Metric Definitions Appendix" in html
    assert "plotly-chart__figure" in html
    assert "Compact plot data" in html
    assert "time-series-chart__placeholder" not in html
    assert "data-drilldown-matrix-spec" in html
    assert "heatmap__placeholder" not in html
    assert "AM opening auction" in html
    assert "Market cap bucket: Small cap" in html
    assert "time_bucket=" not in html
    assert "market_cap_bucket=" not in html
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
            "--max-drilldown-rows",
            "1",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    html = output_path.read_text(encoding="utf-8")
    assert "Custom Offline Demo" in html
    assert "Custom Brand" in html
    assert html.count("metric-card") >= 1
    assert "Rendered mock-data production-format report:" in capsys.readouterr().out


def test_main_offline_demo_can_omit_metric_definitions_appendix(tmp_path) -> None:
    output_path = tmp_path / "demo-no-appendix.html"

    exit_code = main(["offline-demo", "--output", str(output_path), "--no-appendix"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Market Summary" in html
    assert "Executive Market Overview" in html
    assert "Metric Definitions Appendix" not in html


def test_main_offline_demo_can_include_intraday_heatmaps(tmp_path) -> None:
    output_path = tmp_path / "demo-with-heatmaps.html"

    exit_code = main(["offline-demo", "--output", str(output_path), "--include-intraday-heatmaps"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Intraday Detail" in html
    assert "data-drilldown-matrix-spec" in html
    assert "bucket × market-cap view" in html


def test_main_offline_demo_can_omit_drilldown_page(tmp_path) -> None:
    output_path = tmp_path / "demo-no-drilldown.html"

    exit_code = main(["offline-demo", "--output", str(output_path), "--no-drilldown-page"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Market Summary" in html
    assert "Sector, Segment, and Market-Cap Drilldowns" not in html


def test_main_without_command_prints_help(capsys) -> None:
    assert main([]) == 0
    help_text = capsys.readouterr().out
    assert "offline-demo" in help_text
    assert "simulated-source-q" not in help_text
    assert "simulated-source-demo" not in help_text


def test_offline_demo_cli_surfaces_option_validation(tmp_path) -> None:
    output_path = tmp_path / "bad.html"

    with pytest.raises(ValueError, match="max_metric_cards"):
        main(["offline-demo", "--output", str(output_path), "--max-metric-cards", "-1"])


def test_offline_demo_cli_surfaces_drilldown_option_validation(tmp_path) -> None:
    output_path = tmp_path / "bad-drilldown.html"

    with pytest.raises(ValueError, match="max_drilldown_rows"):
        main(["offline-demo", "--output", str(output_path), "--max-drilldown-rows", "-1"])


def test_render_offline_demo_report_file_accepts_options(tmp_path) -> None:
    output_path = tmp_path / "custom.html"
    options = OfflineDemoReportOptions(
        title="Programmatic Offline Demo",
        include_metric_definitions_appendix=False,
        max_metric_cards=1,
        max_comments=1,
        include_intraday_heatmaps=True,
        include_drilldown_page=False,
    )

    render_offline_demo_report_file(output_path, options=options)

    html = output_path.read_text(encoding="utf-8")
    assert "Programmatic Offline Demo" in html
    assert "Metric Definitions Appendix" not in html
    assert "Sector, Segment, and Market-Cap Drilldowns" not in html
    assert '<section class="heatmap">' in html


def test_resolve_pdf_browser_executable_prefers_explicit_path(tmp_path) -> None:
    browser = tmp_path / "chrome"
    browser.write_text("", encoding="utf-8")

    assert _resolve_pdf_browser_executable(browser) == str(browser)


def test_resolve_pdf_browser_executable_rejects_missing_explicit_path(tmp_path) -> None:
    with pytest.raises(ValueError, match="browser_path"):
        _resolve_pdf_browser_executable(tmp_path / "missing-browser")


def test_export_report_html_to_pdf_uses_detected_browser(monkeypatch, tmp_path) -> None:
    input_path = tmp_path / "report.html"
    output_path = tmp_path / "report.pdf"
    input_path.write_text("<html><body>report</body></html>", encoding="utf-8")

    called: dict[str, object] = {}

    def fake_run(command: list[str], *, check: bool, capture_output: bool, text: bool):
        called["command"] = command
        output_path.write_bytes(b"%PDF-1.4\n")

        class Result:
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr("mmsr.cli.shutil.which", lambda name: "/usr/bin/chromium" if name == "chromium" else None)
    monkeypatch.setattr("mmsr.cli.subprocess.run", fake_run)

    rendered_path = export_report_html_to_pdf(input_path, output_path)

    assert rendered_path == output_path
    command = called["command"]
    assert command[0] == "/usr/bin/chromium"
    assert any(str(output_path.resolve()) in part for part in command)
    assert command[-1] == input_path.resolve().as_uri()


def test_export_report_html_to_pdf_errors_when_browser_is_missing(tmp_path) -> None:
    input_path = tmp_path / "report.html"
    input_path.write_text("<html><body>report</body></html>", encoding="utf-8")

    with pytest.raises(RuntimeError, match="no Chromium-family browser"):
        export_report_html_to_pdf(input_path, tmp_path / "report.pdf")


def test_main_export_pdf_invokes_helper(monkeypatch, tmp_path, capsys) -> None:
    input_path = tmp_path / "report.html"
    output_path = tmp_path / "report.pdf"
    input_path.write_text("<html><body>report</body></html>", encoding="utf-8")

    def fake_export(input_arg: str | Path, output_arg: str | Path, *, browser_path: str | Path | None = None) -> Path:
        assert Path(input_arg) == input_path
        assert Path(output_arg) == output_path
        assert browser_path is None
        output_path.write_bytes(b"%PDF-1.4\n")
        return output_path

    monkeypatch.setattr("mmsr.cli.export_report_html_to_pdf", fake_export)

    exit_code = main(["export-pdf", "--input", str(input_path), "--output", str(output_path)])

    assert exit_code == 0
    assert "Exported report PDF:" in capsys.readouterr().out
