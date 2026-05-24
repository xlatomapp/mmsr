from datetime import date

import pytest

from mmsr.kdb.schema_contracts import (
    OutputSchemaContractError,
    extract_result_columns,
    toxicity_reversion_input_schema_contracts,
    toxicity_reversion_output_schema_contract,
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
