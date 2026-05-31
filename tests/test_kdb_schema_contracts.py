from datetime import date

import pytest

from mmsr.kdb.schema_contracts import (
    OutputSchemaContractError,
    activity_input_schema_contract,
    activity_output_schema_contract,
    extract_result_columns,
    liquidity_input_schema_contract,
    liquidity_output_schema_contract,
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
        "topixCapGrp": ["Large"],
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
        "parkinson_volatility_bps": [18.2],
    }


def test_activity_input_contract_lists_source_columns_and_extras() -> None:
    contract = activity_input_schema_contract(
        trades_table="trade_l1",
        extra_required_columns=("sector", "sym"),
    )

    assert contract.template_name == "activity"
    assert contract.table_role == "trades"
    assert contract.table_name == "trade_l1"
    assert contract.required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "tradePrice",
        "tradeSize",
        "sector",
    )


def test_liquidity_input_contract_lists_quote_columns_and_extras() -> None:
    contract = liquidity_input_schema_contract(
        quotes_table="quote_l1",
        extra_required_columns=("market_segment",),
    )

    assert contract.template_name == "liquidity"
    assert contract.table_role == "quotes"
    assert contract.table_name == "quote_l1"
    assert contract.required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
        "bidSize",
        "askSize",
        "market_segment",
    )


def test_activity_contract_lists_all_template_output_columns() -> None:
    contract = activity_output_schema_contract(
        "volume",
        group_by=("topixCapGrp",),
    )

    assert contract.template_name == "activity"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "topixCapGrp",
        "volume",
        "turnover",
        "trade_count",
    )


def test_activity_contract_validates_result_and_rejects_missing_aggregate() -> None:
    validate_activity_output_schema(
        metric_name="volume",
        result=_activity_result(),
        group_by=("topixCapGrp",),
    )

    result = _activity_result()
    del result["trade_count"]
    with pytest.raises(OutputSchemaContractError, match="trade_count"):
        validate_activity_output_schema(
            metric_name="volume",
            result=result,
            group_by=("topixCapGrp",),
        )


def test_activity_contract_rejects_non_activity_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="activity metrics"):
        activity_output_schema_contract("quoted_spread_bps")


def test_liquidity_contract_lists_all_template_output_columns() -> None:
    contract = liquidity_output_schema_contract(
        "quoted_spread_bps",
        group_by=("sector",),
    )

    assert contract.template_name == "liquidity"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "quoted_spread_bps",
        "top_of_book_depth",
        "parkinson_volatility_bps",
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
    (
        pts_contract,
        pts_quote_contract,
        primary_quote_contract,
        reference_contract,
    ) = toxicity_reversion_input_schema_contracts(
        pts_trades_table="trade_pts_l1",
        pts_quotes_table="quote_pts_l1",
        primary_quotes_table="quote_primary_l1",
        reference_table="ref_l1",
    )

    assert pts_contract.template_name == "toxicity_reversion"
    assert pts_contract.table_role == "pts_trades"
    assert pts_contract.table_name == "trade_pts_l1"
    assert pts_contract.required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "venue",
        "tradePrice",
        "tradeSize",
    )
    assert "same-PTS-venue/same-symbol prevailing quote" in pts_contract.assumptions[0]

    assert pts_quote_contract.table_role == "pts_quotes"
    assert pts_quote_contract.table_name == "quote_pts_l1"
    assert pts_quote_contract.required_columns == (
        "date",
        "time",
        "sym",
        "venue",
        "bidPrice",
        "askPrice",
    )
    assert primary_quote_contract.table_role == "primary_quotes"
    assert primary_quote_contract.table_name == "quote_primary_l1"
    assert primary_quote_contract.required_columns == (
        "date",
        "time",
        "sym",
        "venue",
        "bidPrice",
        "askPrice",
    )
    assert reference_contract.table_role == "reference_data"
    assert reference_contract.table_name == "ref_l1"
    assert "askPrice > bidPrice" in primary_quote_contract.assumptions[1]


def test_toxicity_reversion_input_contracts_validate_extra_columns() -> None:
    validate_toxicity_reversion_input_schemas(
        pts_trades_table="trade_pts_l1",
        pts_quotes_table="quote_pts_l1",
        primary_quotes_table="quote_primary_l1",
        pts_trades_columns=(
            "date",
            "time",
            "sym",
            "session",
            "auction",
            "venue",
            "tradePrice",
            "tradeSize",
            "aggressorSide",
            "exec_id",
        ),
        pts_quotes_columns=(
            "date",
            "time",
            "sym",
            "venue",
            "bidPrice",
            "askPrice",
            "bidSize",
            "askSize",
        ),
        primary_quotes_columns=(
            "date",
            "time",
            "sym",
            "venue",
            "bidPrice",
            "askPrice",
            "bidSize",
            "askSize",
        ),
    )


def test_toxicity_reversion_input_contracts_reject_missing_venue() -> None:
    with pytest.raises(OutputSchemaContractError, match="venue"):
        validate_toxicity_reversion_input_schemas(
            pts_trades_columns=(
                "date",
                "time",
                "sym",
                "session",
                "auction",
                "tradePrice",
                "tradeSize",
            ),
            pts_quotes_columns=(
                "date",
                "time",
                "sym",
                "venue",
                "bidPrice",
                "askPrice",
            ),
            primary_quotes_columns=(
                "date",
                "time",
                "sym",
                "venue",
                "bidPrice",
                "askPrice",
            ),
        )


def test_toxicity_reversion_input_contracts_reject_string_column_argument() -> None:
    venue_contract, _, _, _ = toxicity_reversion_input_schema_contracts()

    with pytest.raises(OutputSchemaContractError, match="sequence of column names"):
        venue_contract.validate_columns("date,time,sym")


def test_toxicity_reversion_contract_lists_required_report_boundary_columns() -> None:
    metric_name = "primary_quote_reversion_100ms_bps"

    contract = toxicity_reversion_output_schema_contract(
        metric_name,
        group_by=("venue", "horizon", "sym"),
    )

    assert contract.template_name == "toxicity_reversion"
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
    result = [{key: values[0] for key, values in _reversion_result().items()}]

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


def test_output_schema_validation_accepts_keyed_table_mapping_representation() -> None:
    validate_output_schema_for_template(
        template_name="liquidity",
        metric_name="quoted_spread_bps",
        group_by=("sym", "topixCapGrp"),
        result={
            "key": {
                "date": [date(2026, 5, 1)],
                "time_bucket": ["09:00"],
                "sym": ["7203"],
                "topixCapGrp": ["Large70"],
            },
            "value": {
                "quoted_spread_bps": [12.5],
                "top_of_book_depth": [5000],
                "parkinson_volatility_bps": [18.2],
                "aggregationLevel": ["symbol_bucket"],
                "groupType": ["sym"],
                "groupValue": ["7203"],
            },
        },
    )
