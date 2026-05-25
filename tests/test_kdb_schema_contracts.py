from datetime import date

import pytest

from mmsr.kdb.schema_contracts import (
    OutputSchemaContractError,
    activity_input_schema_contract,
    activity_output_schema_contract,
    extract_result_columns,
    liquidity_input_schema_contract,
    liquidity_output_schema_contract,
    output_schema_contract_for_template,
    toxicity_reversion_input_schema_contracts,
    toxicity_reversion_output_schema_contract,
    validate_activity_output_schema,
    validate_liquidity_output_schema,
    validate_output_schema_for_template,
    validate_toxicity_reversion_input_schemas,
    validate_toxicity_reversion_output_schema,
)


def _reversion_result() -> dict[str, list[object]]:
    metric_name = "primary_quote_reversion_100ms_bps"
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00"],
        "venue": ["SBIJ"],
        "horizon": ["100ms"],
        "sym": ["7203"],
        metric_name: [0.25],
        "horizon_sort_order": [2],
        "trade_count": [150],
        "notional": [250000000.0],
        "positive_reversion_ratio": [0.54],
        "valid_primary_quote_ratio": [0.99],
    }


def _activity_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00-09:05"],
        "market_cap_bucket": ["Large"],
        "turnover": [1_500_000.0],
        "volume": [1_000],
        "trade_count": [25],
    }


def _liquidity_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["AMO"],
        "sector": ["Banks"],
        "quoted_spread_bps": [12.5],
        "top_of_book_depth": [5000],
    }


def test_activity_input_contract_lists_source_columns_and_extras() -> None:
    contract = activity_input_schema_contract(
        trades_table="trade_l1",
        extra_required_columns=("sector", "sym"),
    )

    assert contract.template_name == "activity.q"
    assert contract.table_role == "trades"
    assert contract.table_name == "trade_l1"
    assert contract.required_columns == (
        "date",
        "time",
        "trade_price",
        "trade_size",
        "sector",
        "sym",
    )


def test_liquidity_input_contract_lists_quote_columns_and_extras() -> None:
    contract = liquidity_input_schema_contract(
        quotes_table="quote_l1",
        extra_required_columns=("market_segment",),
    )

    assert contract.template_name == "liquidity.q"
    assert contract.table_role == "quotes"
    assert contract.table_name == "quote_l1"
    assert contract.required_columns == (
        "date",
        "time",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
        "market_segment",
    )


def test_activity_contract_lists_all_template_output_columns() -> None:
    contract = activity_output_schema_contract(
        "volume",
        group_by=("market_cap_bucket",),
    )

    assert contract.template_name == "activity.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "market_cap_bucket",
        "volume",
        "turnover",
        "trade_count",
    )


def test_activity_contract_validates_result_and_rejects_missing_aggregate() -> None:
    validate_activity_output_schema(
        metric_name="volume",
        result=_activity_result(),
        group_by=("market_cap_bucket",),
    )

    result = _activity_result()
    del result["trade_count"]
    with pytest.raises(OutputSchemaContractError, match="trade_count"):
        validate_activity_output_schema(
            metric_name="volume",
            result=result,
            group_by=("market_cap_bucket",),
        )


def test_activity_contract_rejects_non_activity_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="activity metrics"):
        activity_output_schema_contract("quoted_spread_bps")


def test_liquidity_contract_lists_all_template_output_columns() -> None:
    contract = liquidity_output_schema_contract(
        "quoted_spread_bps",
        group_by=("sector",),
    )

    assert contract.template_name == "liquidity.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "quoted_spread_bps",
        "top_of_book_depth",
    )


def test_liquidity_contract_validates_result_and_rejects_missing_aggregate() -> None:
    validate_liquidity_output_schema(
        metric_name="quoted_spread_bps",
        result=_liquidity_result(),
        group_by=("sector",),
    )

    result = _liquidity_result()
    del result["top_of_book_depth"]
    with pytest.raises(OutputSchemaContractError, match="top_of_book_depth"):
        validate_liquidity_output_schema(
            metric_name="quoted_spread_bps",
            result=result,
            group_by=("sector",),
        )


def test_liquidity_contract_rejects_non_liquidity_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="liquidity metrics"):
        liquidity_output_schema_contract("turnover")


def test_toxicity_reversion_input_contracts_list_required_source_columns() -> None:
    venue_contract, quote_contract = toxicity_reversion_input_schema_contracts(
        venue_trades_table="trade_venue_l1",
        primary_quotes_table="quote_primary_l1",
    )

    assert venue_contract.template_name == "toxicity_reversion.q"
    assert venue_contract.table_role == "venue_trades"
    assert venue_contract.table_name == "trade_venue_l1"
    assert venue_contract.required_columns == (
        "date",
        "time",
        "sym",
        "venue",
        "trade_price",
        "trade_size",
        "aggressor_side",
    )
    assert "buy=1" in venue_contract.assumptions[0]

    assert quote_contract.table_role == "primary_quotes"
    assert quote_contract.table_name == "quote_primary_l1"
    assert quote_contract.required_columns == (
        "date",
        "time",
        "sym",
        "venue",
        "bid_price",
        "ask_price",
    )
    assert "ask_price > bid_price" in quote_contract.assumptions[1]


def test_toxicity_reversion_input_contracts_validate_extra_columns() -> None:
    validate_toxicity_reversion_input_schemas(
        venue_trades_table="trade_venue_l1",
        primary_quotes_table="quote_primary_l1",
        venue_trades_columns=(
            "date",
            "time",
            "sym",
            "venue",
            "trade_price",
            "trade_size",
            "aggressor_side",
            "exec_id",
        ),
        primary_quotes_columns=(
            "date",
            "time",
            "sym",
            "venue",
            "bid_price",
            "ask_price",
            "bid_size",
            "ask_size",
        ),
    )


def test_toxicity_reversion_input_contracts_reject_missing_trade_side() -> None:
    with pytest.raises(OutputSchemaContractError, match="aggressor_side"):
        validate_toxicity_reversion_input_schemas(
            venue_trades_columns=(
                "date",
                "time",
                "sym",
                "venue",
                "trade_price",
                "trade_size",
            ),
            primary_quotes_columns=(
                "date",
                "time",
                "sym",
                "venue",
                "bid_price",
                "ask_price",
            ),
        )


def test_toxicity_reversion_input_contracts_reject_string_column_argument() -> None:
    venue_contract, _ = toxicity_reversion_input_schema_contracts()

    with pytest.raises(OutputSchemaContractError, match="sequence of column names"):
        venue_contract.validate_columns("date,time,sym")


def test_toxicity_reversion_contract_lists_required_report_boundary_columns() -> None:
    metric_name = "primary_quote_reversion_100ms_bps"

    contract = toxicity_reversion_output_schema_contract(
        metric_name,
        group_by=("venue", "horizon", "sym"),
    )

    assert contract.template_name == "toxicity_reversion.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "venue",
        "horizon",
        "sym",
        metric_name,
        "horizon_sort_order",
        "trade_count",
        "notional",
        "positive_reversion_ratio",
        "valid_primary_quote_ratio",
    )
    assert contract.optional_columns == ("context_sort_order",)
    assert contract.documented_columns[-1] == "context_sort_order"


def test_toxicity_reversion_contract_validates_column_mapping_result() -> None:
    validate_toxicity_reversion_output_schema(
        metric_name="primary_quote_reversion_100ms_bps",
        result=_reversion_result(),
        group_by=("venue", "horizon", "sym"),
    )


def test_toxicity_reversion_contract_validates_row_dict_result() -> None:
    result = [
        {
            key: values[0]
            for key, values in _reversion_result().items()
        }
    ]

    assert extract_result_columns(result) == tuple(_reversion_result())

    validate_toxicity_reversion_output_schema(
        metric_name="primary_quote_reversion_100ms_bps",
        result=result,
        group_by=("venue", "horizon", "sym"),
    )


def test_toxicity_reversion_contract_rejects_missing_metadata_column() -> None:
    result = _reversion_result()
    del result["valid_primary_quote_ratio"]

    with pytest.raises(OutputSchemaContractError, match="valid_primary_quote_ratio"):
        validate_toxicity_reversion_output_schema(
            metric_name="primary_quote_reversion_100ms_bps",
            result=result,
            group_by=("venue", "horizon", "sym"),
        )


def test_toxicity_reversion_contract_rejects_missing_requested_group_column() -> None:
    result = _reversion_result()
    del result["sym"]

    with pytest.raises(OutputSchemaContractError, match="sym"):
        validate_toxicity_reversion_output_schema(
            metric_name="primary_quote_reversion_100ms_bps",
            result=result,
            group_by=("venue", "horizon", "sym"),
        )


def test_toxicity_reversion_contract_rejects_empty_row_list() -> None:
    with pytest.raises(OutputSchemaContractError, match="empty row list"):
        validate_toxicity_reversion_output_schema(
            metric_name="primary_quote_reversion_100ms_bps",
            result=[],
            group_by=("venue", "horizon"),
        )


def test_toxicity_reversion_contract_rejects_non_reversion_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="primary_quote_reversion"):
        toxicity_reversion_output_schema_contract("quoted_spread_bps")


def test_output_schema_contract_dispatch_validates_template_results() -> None:
    contract = output_schema_contract_for_template(
        template_name="activity.q",
        metric_name="volume",
        group_by=("market_cap_bucket",),
    )

    assert contract.required_columns == (
        "date",
        "time_bucket",
        "market_cap_bucket",
        "volume",
        "turnover",
        "trade_count",
    )

    validate_output_schema_for_template(
        template_name="liquidity.q",
        metric_name="quoted_spread_bps",
        result=_liquidity_result(),
        group_by=("sector",),
    )

    with pytest.raises(OutputSchemaContractError, match="not_registered.q"):
        output_schema_contract_for_template(
            template_name="not_registered.q",
            metric_name="volume",
        )


@pytest.mark.kdb_integration
@pytest.mark.skip(
    reason="requires live kdb+ and confirmed production reversion schemas"
)
def test_live_toxicity_reversion_query_matches_output_schema_contract() -> None:
    """Placeholder for production validation of ``toxicity_reversion.q``.

    A live implementation should run one small date/symbol slice against the
    configured venue trade and primary quote tables, then call
    ``validate_toxicity_reversion_output_schema`` before normalizing results.
    """
    raise AssertionError(
        "configure live kdb schema validation for toxicity_reversion.q"
    )
