import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.query_loader import (
    QueryTemplateError,
    load_q_library_template,
    load_q_template,
    render_calculation_function_bootstrap,
    render_simulated_source_function_bootstrap,
    render_template,
    template_parameters,
)


def test_load_q_library_template_reads_single_calculation_library() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    assert ".calcLiquidity" in template
    assert ".callTradingCalendar" not in template


def test_load_q_library_template_reads_simulated_source_library() -> None:
    template = load_q_library_template("mmsr_simulated_sources.q.j2")

    assert ".getTradingCalendar" in template
    assert ".getRef" in template
    assert ".getTrade" in template
    assert ".getQuote" in template
    assert ".getPtsTrade" in template
    assert ".getPtsQuote" in template
    assert ".getPrimaryQuote" in template


def test_load_q_library_template_rejects_paths_and_non_q_library_names() -> None:
    with pytest.raises(ValueError, match="filename"):
        load_q_library_template("../mmsr_calculations.q.j2")

    with pytest.raises(ValueError, match="end with .q.j2"):
        load_q_library_template("mmsr_calculations.q")


def test_load_q_template_reports_removed_metric_templates() -> None:
    with pytest.raises(FileNotFoundError, match="metric q template files were removed"):
        load_q_template("missing_template.q")


def test_trading_calendar_has_no_separate_template_file() -> None:
    with pytest.raises(FileNotFoundError, match="trading_calendar.q"):
        load_q_template("trading_calendar.q")


def test_template_parameters_extracts_unique_required_parameters() -> None:
    template = "select from {{ table }} where date within {{ date_range }}, {{ table }}"

    assert template_parameters(template) == frozenset({"table", "date_range"})


def test_template_parameters_rejects_invalid_placeholder_blocks() -> None:
    with pytest.raises(QueryTemplateError, match="invalid q template placeholder"):
        template_parameters("select from {{ trades-table }}")


def test_render_template_replaces_named_placeholders_with_whitespace() -> None:
    rendered = render_template(
        "select from {{ table }} where {{date_filter}}, {{ time_filter }}",
        {
            "table": "trade",
            "date_filter": "date=2026.05.24",
            "time_filter": "time within (09:00;11:30)",
        },
    )

    assert rendered == ("select from trade where date=2026.05.24, time within (09:00;11:30)")


def test_render_template_requires_all_template_parameters() -> None:
    with pytest.raises(QueryTemplateError, match=r"missing q template parameter\(s\): filter"):
        render_template("select from {{ table }} where {{ filter }}", {"table": "quote"})


def test_render_template_rejects_unused_parameters() -> None:
    with pytest.raises(QueryTemplateError, match=r"unused q template parameter\(s\): extra"):
        render_template(
            "select from {{ table }}",
            {"table": "quote", "extra": "date=2026.05.24"},
        )


def test_render_template_rejects_invalid_parameter_names() -> None:
    with pytest.raises(QueryTemplateError, match="invalid q template parameter name"):
        render_template("select from {{ table }}", {"table": "quote", "bad-name": "x"})


def test_render_template_requires_string_parameter_values() -> None:
    with pytest.raises(TypeError, match="must be strings: table"):
        render_template("select from {{ table }}", {"table": 123})  # type: ignore[dict-item]


def test_kdb_client_can_be_instantiated_from_config_without_importing_pykx() -> None:
    config = KdbConfig(host="localhost", port=5000, username="user", password="pw")
    client = KdbClient(config)

    assert client.config == config
    assert client.config.host == "localhost"
    assert client.config.port == 5000


def test_toxicity_reversion_installed_function_uses_future_mid_denominator() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    assert "reversion_bps: aggressorSide * 10000 * (postMid - primaryMid) % postMid" in template
    assert "postMid > 0" in template
    assert "% primaryMid" not in template
    assert "`date`sym`venue`time xasc ptsQuotes" in template
    assert "aggressorSide: ?[tradePrice>ptsMid;1;?[tradePrice<ptsMid;-1;0]]" in template
    assert "horizonTime: `time$(time + params`horizon)" in template


def test_render_calculation_function_bootstrap_installs_helpers_in_namespace() -> None:
    rendered = render_calculation_function_bootstrap(".desk.mmsr")

    assert "sum tradePrice * tradeSize" in rendered
    assert "med 10000 * (askPrice - bidPrice)" in rendered
    assert ".desk.mmsr.weightedAverage" not in rendered
    assert ".desk.mmsr.sumSize" not in rendered
    assert ".desk.mmsr.rowCount" not in rendered
    assert ".desk.mmsr.callTradingCalendar" not in rendered
    assert "{{" not in rendered


def test_render_simulated_source_function_bootstrap_installs_kdb_sources() -> None:
    rendered = render_simulated_source_function_bootstrap(".dev.mmsr")

    assert ".dev.mmsr.symbolCount:240;" in rendered
    assert ".dev.mmsr.getTradingCalendar" in rendered
    assert ".dev.mmsr.getRef" in rendered
    assert ".dev.mmsr.getTrade" in rendered
    assert ".dev.mmsr.getQuote" in rendered
    assert ".dev.mmsr.getPtsTrade" in rendered
    assert ".dev.mmsr.getPtsQuote" in rendered
    assert ".dev.mmsr.getPrimaryQuote" in rendered
    assert "rows:q`row;" in rendered
    assert "0.05f * (rows mod 10)" in rendered
    assert "0.06f * (rows mod 12)" in rendered
    assert "date" in rendered
    assert "sym" in rendered
    assert "tradePrice" in rendered
    assert "tradeSize" in rendered
    assert "bidPrice" in rendered
    assert "askPrice" in rendered
    assert "bidSize" in rendered
    assert "askSize" in rendered
    assert "{{" not in rendered


def test_render_simulated_source_function_bootstrap_accepts_symbol_count() -> None:
    rendered = render_simulated_source_function_bootstrap(
        ".dev.mmsr",
        symbol_count=17,
    )

    assert ".dev.mmsr.symbolCount:17;" in rendered
    assert "{{" not in rendered


def test_render_simulated_source_function_bootstrap_validates_symbol_count() -> None:
    with pytest.raises(ValueError, match="symbol_count must be positive"):
        render_simulated_source_function_bootstrap(".dev.mmsr", symbol_count=0)


def test_q_bootstrap_renderers_validate_namespaces() -> None:
    with pytest.raises(ValueError, match="must start with"):
        render_calculation_function_bootstrap("desk.mmsr")

    with pytest.raises(ValueError, match="invalid source_namespace"):
        render_simulated_source_function_bootstrap(".bad-name")


def test_no_separate_q_template_directory_exists() -> None:
    assert not (Path(__file__).resolve().parents[1] / "mmsr" / "kdb" / "query_templates").exists()


def test_kdb_client_uses_empty_strings_for_missing_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_q_connection(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setitem(
        sys.modules,
        "pykx",
        SimpleNamespace(QConnection=fake_q_connection),
    )

    client = KdbClient(KdbConfig(host="localhost", port=5000))
    client.connect()

    assert captured["username"] == ""
    assert captured["password"] == ""


def test_q_library_uses_safe_singleton_dictionary_key_enlistment() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    assert "rawSources: enlist[`refs]!enlist refs;" in template
    assert "rawSources: `refs!(enlist refs);" not in template


def test_q_metric_functions_return_unkeyed_tables_for_python_schema_validation() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    assert "if[0=count facts; :0!facts];" in template
    assert "0!raze mmsrRollups" in template
    assert template.count("0!result") >= 3
    assert "    result\n    };" not in template


def test_q_library_excludes_removed_legacy_metric_functions() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    legacy_terms = (
        "calc" + "LiquidityTicks",
        "calc" + "RealizedVolatility",
        "calc" + "Flow",
        "quoted_spread" + "_ticks",
        "realized" + "_volatility",
        "signed" + "_turnover",
        "trade" + "_imbalance",
    )
    for term in legacy_terms:
        assert term not in template


def test_q_library_run_report_day_includes_timing_instrumentation() -> None:
    template = load_q_library_template("mmsr_calculations.q.j2")

    assert ".runReportDay:{[runDate;reportConfig]" in template
    assert ".elapsedMs:{[startTs;endTs]" in template
    assert "reportStartTs: .z.p;" in template
    assert "refLoadStartTs: .z.p;" in template
    assert "srcStart: .z.p;" in template
    assert "rollupStartTs: .z.p;" in template
    assert "report_ref_load_ms" in template
    assert "report_chunk_calc_ms" in template
    assert "report_rollup_ms" in template
    assert "report_total_ms" in template
    assert "report_chunk_count" in template
    assert "report_symbol_count" in template
    assert '-1 "MMSR runReportDay "' in template
    assert "timingResult" in template
