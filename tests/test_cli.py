from __future__ import annotations

import sys

import pytest

from mmsr.cli import (
    main,
    render_mock_kdb_demo_report_file,
    render_offline_demo_report_file,
)
from mmsr.examples import MockKdbIntegrationDemoOptions, OfflineDemoReportOptions


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
    assert "Generated: fixed timestamp" in html
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


def test_render_mock_kdb_demo_report_file_writes_deterministic_html(tmp_path) -> None:
    output_path = tmp_path / "reports" / "mock-kdb-demo.html"

    rendered_path = render_mock_kdb_demo_report_file(output_path)

    assert rendered_path == output_path
    html = output_path.read_text(encoding="utf-8")
    assert "Japanese Market Microstructure Monitor — Mock kdb Integration Demo" in html
    assert "Market Summary" in html
    assert "Executive Market Overview" in html
    assert "Metric Definitions Appendix" in html
    assert "plotly-chart__figure" in html
    assert "data-drilldown-matrix-spec" in html
    assert "Compact plot data" in html
    assert "mock kdb integration" in html
    assert "time-series-chart__placeholder" not in html
    assert "heatmap__placeholder" not in html
    assert "pykx" not in sys.modules


def test_main_mock_kdb_demo_renders_to_requested_path(tmp_path, capsys) -> None:
    output_path = tmp_path / "mock-kdb-demo.html"

    exit_code = main(
        [
            "mock-kdb-demo",
            "--output",
            str(output_path),
            "--title",
            "Custom Mock Kdb Demo",
            "--brand-name",
            "Custom Kdb Brand",
            "--generated-at-text",
            "fixed kdb timestamp",
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
    assert "Custom Mock Kdb Demo" in html
    assert "Custom Kdb Brand" in html
    assert "Generated: fixed kdb timestamp" in html
    assert html.count("metric-card") >= 1
    assert "Rendered mock-kdb integration report:" in capsys.readouterr().out


def test_main_mock_kdb_demo_can_omit_metric_definitions_appendix(tmp_path) -> None:
    output_path = tmp_path / "mock-kdb-no-appendix.html"

    exit_code = main(["mock-kdb-demo", "--output", str(output_path), "--no-appendix"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Market Summary" in html
    assert "Executive Market Overview" in html
    assert "Metric Definitions Appendix" not in html


def test_main_mock_kdb_demo_can_include_intraday_heatmaps(tmp_path) -> None:
    output_path = tmp_path / "mock-kdb-with-heatmaps.html"

    exit_code = main(["mock-kdb-demo", "--output", str(output_path), "--include-intraday-heatmaps"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Intraday Detail" in html
    assert '<section class="heatmap">' in html
    assert "bucket × market-cap view" in html


def test_main_mock_kdb_demo_can_omit_drilldown_page(tmp_path) -> None:
    output_path = tmp_path / "mock-kdb-no-drilldown.html"

    exit_code = main(["mock-kdb-demo", "--output", str(output_path), "--no-drilldown-page"])

    assert exit_code == 0
    html = output_path.read_text(encoding="utf-8")
    assert "Market Summary" in html
    assert "Sector, Segment, and Market-Cap Drilldowns" not in html


def test_main_without_command_prints_help(capsys) -> None:
    assert main([]) == 0
    help_text = capsys.readouterr().out
    assert "offline-demo" in help_text
    assert "mock-kdb-demo" in help_text
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


def test_render_mock_kdb_demo_report_file_accepts_options(tmp_path) -> None:
    output_path = tmp_path / "custom-mock-kdb.html"
    options = MockKdbIntegrationDemoOptions(
        title="Programmatic Mock Kdb Demo",
        include_metric_definitions_appendix=False,
        max_metric_cards=1,
        max_comments=1,
        include_intraday_heatmaps=True,
        include_drilldown_page=False,
    )

    render_mock_kdb_demo_report_file(output_path, options=options)

    html = output_path.read_text(encoding="utf-8")
    assert "Programmatic Mock Kdb Demo" in html
    assert "Metric Definitions Appendix" not in html
    assert "Sector, Segment, and Market-Cap Drilldowns" not in html
    assert '<section class="heatmap">' in html
