import pytest

from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.query_loader import (
    QueryTemplateError,
    load_q_template,
    render_template,
    template_parameters,
)


def test_load_q_template_reads_packaged_template() -> None:
    template = load_q_template("trading_calendar.q")

    assert "select {{ date_column }}" in template
    assert "{{ table }}" in template


def test_load_q_template_rejects_paths_and_non_q_names() -> None:
    with pytest.raises(ValueError, match="filename"):
        load_q_template("../trading_calendar.q")

    with pytest.raises(ValueError, match="end with .q"):
        load_q_template("trading_calendar.txt")


def test_load_q_template_reports_missing_template() -> None:
    with pytest.raises(FileNotFoundError, match="missing_template.q"):
        load_q_template("missing_template.q")


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

    assert rendered == (
        "select from trade where date=2026.05.24, "
        "time within (09:00;11:30)"
    )


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


def test_packaged_activity_template_parameters_ignore_documentation_comments() -> None:
    template = load_q_template("activity.q")

    assert template_parameters(template) == frozenset(
        {"trades_table", "date_filter", "time_filter", "bucket_expr", "group_by"}
    )


def test_kdb_client_can_be_instantiated_from_config_without_importing_pykx() -> None:
    config = KdbConfig(host="localhost", port=5000, username="user", password="pw")
    client = KdbClient(config)

    assert client.config == config
    assert client.config.host == "localhost"
    assert client.config.port == 5000


def test_packaged_liquidity_template_parameters_include_bucket_expr() -> None:
    template = load_q_template("liquidity.q")

    assert template_parameters(template) == frozenset(
        {"quotes_table", "date_filter", "time_filter", "bucket_expr", "group_by"}
    )


def test_packaged_toxicity_reversion_template_parameters_are_strict() -> None:
    template = load_q_template("toxicity_reversion.q")

    assert template_parameters(template) == frozenset(
        {
            "venue_trades_table",
            "primary_quotes_table",
            "date_filter",
            "time_filter",
            "bucket_expr",
            "group_by",
            "venue_filter",
            "primary_venue",
            "horizon",
            "horizon_label",
            "horizon_sort_order",
            "max_primary_quote_age",
            "value_column",
        }
    )
