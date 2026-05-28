from pathlib import Path

from mmsr.config.loading import load_report_config_file
from mmsr.kdb.query_plan import template_for_metric


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_production_minimal_config_loads_supported_kdb_metrics() -> None:
    config, period = load_report_config_file(
        REPO_ROOT / "config" / "report.production_minimal.yaml"
    )

    assert config.title == "Japanese Market Microstructure Monitor"
    assert period.start_date.isoformat() == "2026-05-01"
    assert config.toxicity.enabled is True
    assert config.calendar.qualified_function() == ".sb.mmsr.getTradingCalendar"
    assert config.symbols.qualified_function() == ".sb.mmsr.getRef"
    assert config.metrics == [
        "turnover",
        "volume",
        "trade_count",
        "quoted_spread_bps",
        "top_of_book_depth",
        "primary_quote_reversion_10ms_bps",
        "primary_quote_reversion_100ms_bps",
        "primary_quote_reversion_500ms_bps",
        "primary_quote_reversion_1s_bps",
        "primary_quote_reversion_5s_bps",
        "primary_quote_reversion_10s_bps",
    ]
    assert {template_for_metric(metric) for metric in config.metrics} == {
        "activity.q",
        "liquidity.q",
        "toxicity_reversion.q",
    }
    assert config.kdb.raw_data_functions.to_source_functions()["pts_trades"] == (
        ".sb.mmsr.getPtsTrade"
    )
    assert config.kdb.raw_data_functions.to_source_functions()["pts_quotes"] == (
        ".sb.mmsr.getPtsQuote"
    )
    assert config.kdb.raw_data_functions.to_source_functions()["primary_quotes"] == (
        ".sb.mmsr.getQuote"
    )
    assert config.kdb.symbol_chunk_group_by == ("sym",)


def test_example_config_uses_market_monitoring_metrics() -> None:
    config, _ = load_report_config_file(REPO_ROOT / "config" / "report.example.yaml")

    assert config.metrics == [
        "turnover",
        "volume",
        "trade_count",
        "quoted_spread_bps",
        "top_of_book_depth",
        "primary_quote_reversion_10ms_bps",
        "primary_quote_reversion_100ms_bps",
        "primary_quote_reversion_500ms_bps",
        "primary_quote_reversion_1s_bps",
        "primary_quote_reversion_5s_bps",
        "primary_quote_reversion_10s_bps",
    ]
    assert "effective_spread_bps" not in config.metrics
    assert "price_impact_30s_bps" not in config.metrics
