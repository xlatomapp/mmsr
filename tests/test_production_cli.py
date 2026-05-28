from __future__ import annotations

from datetime import date
from pathlib import Path

from mmsr.cli import (
    main,
    preflight_production_report,
    render_production_report_file,
    summarize_production_report_plan,
)

CONFIG_YAML = """
report:
  title: "Production Preflight Report"
  branding:
    brand_name: "Prod Brand"

data:
  source: kdb
  kdb:
    calculation_namespace: ".desk.mmsr"
    enforce_daily_raw_scope: true
    symbol_chunk_size: 2
    raw_data_functions:
      namespace: ".sb.mmsr"
      trade: "getTrade"
      quote: "getQuote"

calendar:
  source: kdb
  namespace: ".sb.mmsr"
  function: "getTradingCalendar"
  date_column: date

period:
  start_date: "2026-05-01"
  end_date: "2026-05-02"

intraday:
  bucket_size: "5m"

groups:
  - topixCapGrp

reference:
  method: same_intraday_bucket
  lookback_days: 2
  statistic: median
  observation_unit: trading_day
  comparable_keys:
    - metric_name
    - time_bucket
    - group
  min_samples_for_z_score: 30
  min_samples_for_empirical_percentile: 2
  default_technical_score: robust_z_score

metrics:
  - volume
"""

MULTI_METRIC_CONFIG_YAML = CONFIG_YAML.replace(
    "metrics:\n  - volume\n",
    "metrics:\n  - volume\n  - quoted_spread_bps\n",
)

class FakeProductionKdbClient:
    queries: list[str] = []

    def __init__(self, config) -> None:
        self.config = config

    def execute(self, query: str, *args):
        self.queries.append(query)
        if "getTradingCalendar" in query:
            start, end = args
            if end < date(2026, 5, 1):
                return {"date": [date(2026, 4, 29), date(2026, 4, 30)]}
            return {"date": [date(2026, 5, 1)]}
        if "getRef" in query and args:
            return {
                "date": [args[0], args[0], args[0]],
                "sym": ["7203", "6758", "9984"],
                "ric": ["7203.T", "6758.T", "9984.T"],
                "topixCapGrp": ["Large", "Large", "Large"],
                "lotSize": [100, 100, 100],
            }

        row_date = date(2026, 5, 1)
        volume = 12345
        if "2026.04.29" in query:
            row_date = date(2026, 4, 29)
            volume = 10000
        elif "2026.04.30" in query:
            row_date = date(2026, 4, 30)
            volume = 11000

        if "calcLiquidity" in query:
            return [
                {
                    "date": row_date,
                    "time_bucket": "09:00-09:05",
                    "topixCapGrp": "Large",
                    "quoted_spread_bps": 3.5,
                    "top_of_book_depth": 2500,
                }
            ]

        return [
            {
                "date": row_date,
                "time_bucket": "09:00-09:05",
                "topixCapGrp": "Large",
                "volume": volume,
                "turnover": 987654321,
                "trade_count": 42,
            }
        ]

def test_render_production_report_file_uses_live_execution_path(
    tmp_path, monkeypatch
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    output_path = tmp_path / "production.html"
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    rendered_path = render_production_report_file(
        output_path,
        config_path=config_path,
        kdb_host="localhost",
        kdb_port=5001,
        symbols=["7203", "6758", "9984"],
    )

    assert rendered_path == output_path
    html = output_path.read_text(encoding="utf-8")
    assert "Production Preflight Report" in html
    assert "Prod Brand" in html
    assert "Volume" in html
    assert "TOPIX cap group" in html
    assert "Large" in html
    assert "Current versus reference" in html
    assert "Reference and Target Daily Trends" in html
    assert "Reference observation unit: trading day" in html
    assert any("getTradingCalendar" in query for query in FakeProductionKdbClient.queries)
    metric_queries = [
        query
        for query in FakeProductionKdbClient.queries
        if "calcActivity" in query or "calcLiquidity" in query
    ]
    assert len(metric_queries) == 6  # 2 target chunks + 2 reference days * 2 chunks
    assert ".sb.mmsr.getTrade" in "\n".join(FakeProductionKdbClient.queries)
    assert "(.sb.mmsr.getTrade[2026.04.29;" in "\n".join(metric_queries)
    assert "(.sb.mmsr.getTrade[2026.04.30;" in "\n".join(metric_queries)

def test_summarize_production_report_plan_queries_calendar_not_metrics(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    summary = summarize_production_report_plan(
        config_path=config_path,
        kdb_host="localhost",
        kdb_port=5001,
        symbols=["7203", "6758", "9984"],
    )

    assert summary.config_title == "Production Preflight Report"
    assert summary.target_trading_days == (date(2026, 5, 1),)
    assert summary.reference_trading_days == (
        date(2026, 4, 29),
        date(2026, 4, 30),
    )
    assert summary.metric_names == ("volume",)
    assert summary.symbol_chunk_count == 2
    assert summary.target_step_count == 2
    assert summary.reference_step_count == 4
    assert summary.metric_contracts[0].template_name == "activity.q"
    assert len(FakeProductionKdbClient.queries) == 2
    assert all("getTradingCalendar" in query for query in FakeProductionKdbClient.queries)
    assert "Reference-data universe function: .sb.mmsr.getRef" in "\n".join(summary.summary_lines())
    assert ".sb.mmsr.getTrade" in "\n".join(summary.summary_lines())

def test_summarize_production_report_plan_uses_symbol_function_without_cli_symbols(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    summary = summarize_production_report_plan(
        config_path=config_path,
        kdb_host="localhost",
        kdb_port=5001,
    )

    assert summary.symbol_chunk_count == 2
    assert summary.target_step_count == 2
    assert summary.reference_step_count == 4
    assert any("getRef" in query for query in FakeProductionKdbClient.queries)


def test_preflight_production_report_executes_one_bounded_metric_step(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    result = preflight_production_report(
        config_path=config_path,
        kdb_host="localhost",
        kdb_port=5001,
        symbols=["7203", "6758", "9984"],
    )

    assert result.ok
    assert result.config_title == "Production Preflight Report"
    assert result.trading_days == (date(2026, 5, 1),)
    assert result.preflight_step.metric_name == "volume"
    assert result.preflight_step.symbols == ("7203", "6758")
    assert result.rendered_query.template_name == "activity.q"
    assert "topixCapGrp" in result.rendered_query.required_output_columns
    assert result.result_row_count == 1
    assert len(FakeProductionKdbClient.queries) == 2
    assert "getTradingCalendar" in FakeProductionKdbClient.queries[0]
    assert ".sb.mmsr.getTrade" in FakeProductionKdbClient.queries[1]

def test_preflight_production_report_can_select_metric(
    tmp_path,
    monkeypatch,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(MULTI_METRIC_CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    result = preflight_production_report(
        config_path=config_path,
        kdb_host="localhost",
        kdb_port=5001,
        symbols=["7203", "6758", "9984"],
        metric_name="quoted_spread_bps",
    )

    assert result.ok
    assert result.preflight_step.metric_name == "quoted_spread_bps"
    assert result.rendered_query.template_name == "liquidity.q"
    assert "quoted_spread_bps" in result.rendered_query.required_output_columns
    assert ".sb.mmsr.getQuote" in FakeProductionKdbClient.queries[1]
    assert "calcLiquidity" in FakeProductionKdbClient.queries[1]

def test_main_render_command_writes_report(tmp_path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    output_path = tmp_path / "production-cli.html"
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    exit_code = main(
        [
            "render",
            "--config",
            str(config_path),
            "--output",
            str(output_path),
            "--kdb-host",
            "localhost",
            "--kdb-port",
            "5001",
            "--symbol",
            "7203",
            "--symbol",
            "6758",
        ]
    )

    assert exit_code == 0
    assert output_path.exists()
    assert "Rendered production kdb-backed report:" in capsys.readouterr().out

def test_main_preflight_command_prints_diagnostics(tmp_path, monkeypatch, capsys) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    exit_code = main(
        [
            "preflight",
            "--config",
            str(config_path),
            "--kdb-host",
            "localhost",
            "--kdb-port",
            "5001",
            "--symbol",
            "7203",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Preflight status: passed" in output
    assert "Sample metric: volume" in output
    assert "Required output columns:" in output

def test_main_preflight_command_accepts_metric_selection(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(MULTI_METRIC_CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    exit_code = main(
        [
            "preflight",
            "--config",
            str(config_path),
            "--kdb-host",
            "localhost",
            "--kdb-port",
            "5001",
            "--symbol",
            "7203",
            "--metric",
            "quoted_spread_bps",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Sample metric: quoted_spread_bps" in output
    assert "Sample template: liquidity.q" in output
    assert "calcLiquidity" in FakeProductionKdbClient.queries[1]

def test_main_plan_command_prints_summary_without_metric_execution(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    config_path = tmp_path / "report.yaml"
    config_path.write_text(CONFIG_YAML, encoding="utf-8")
    FakeProductionKdbClient.queries = []

    monkeypatch.setattr("mmsr.cli.KdbClient", FakeProductionKdbClient)

    exit_code = main(
        [
            "plan",
            "--config",
            str(config_path),
            "--kdb-host",
            "localhost",
            "--kdb-port",
            "5001",
            "--symbol",
            "7203",
            "--symbol",
            "6758",
            "--symbol",
            "9984",
        ]
    )

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "Production plan summary:" in output
    assert "Target trading days: 1 (2026-05-01)" in output
    assert "Reference trading days: 2 (2026-04-29, 2026-04-30)" in output
    assert "Symbol chunks per trading day: 2" in output
    assert "Total metric steps: 6" in output
    assert ".sb.mmsr.getTrade" in output
    assert all("getTradingCalendar" in query for query in FakeProductionKdbClient.queries)

def test_main_help_lists_production_render_command(capsys) -> None:
    assert main([]) == 0
    help_text = capsys.readouterr().out
    assert "render" in help_text
    assert "preflight" in help_text
    assert "plan" in help_text
    assert "offline-demo" in help_text
    assert "mock-kdb-demo" in help_text
