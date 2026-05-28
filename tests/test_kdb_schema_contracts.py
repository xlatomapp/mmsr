from datetime import date

import pytest

from mmsr.kdb.schema_contracts import (
    OutputSchemaContractError,
    activity_input_schema_contract,
    effective_spread_input_schema_contracts,
    effective_spread_output_schema_contract,
    price_impact_input_schema_contracts,
    price_impact_output_schema_contract,
    activity_output_schema_contract,
    extract_result_columns,
    flow_input_schema_contract,
    flow_output_schema_contract,
    liquidity_input_schema_contract,
    liquidity_output_schema_contract,
    liquidity_ticks_input_schema_contract,
    liquidity_ticks_output_schema_contract,
    output_schema_contract_for_template,
    realized_volatility_input_schema_contract,
    realized_volatility_output_schema_contract,
    toxicity_reversion_input_schema_contracts,
    toxicity_reversion_output_schema_contract,
    validate_activity_output_schema,
    validate_effective_spread_output_schema,
    validate_price_impact_output_schema,
    validate_flow_output_schema,
    validate_liquidity_output_schema,
    validate_liquidity_ticks_output_schema,
    validate_output_schema_for_template,
    validate_realized_volatility_output_schema,
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
    }


def _liquidity_ticks_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["AMO"],
        "sector": ["Banks"],
        "quoted_spread_ticks": [1.0],
    }


def _realized_volatility_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00-09:05"],
        "sector": ["Banks"],
        "realized_volatility": [18.25],
        "return_count": [120],
        "first_mid": [1000.5],
        "last_mid": [1001.0],
    }


def _flow_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00-09:05"],
        "sector": ["Banks"],
        "signed_turnover": [250_000.0],
        "trade_imbalance": [0.25],
        "signed_volume": [500],
        "volume": [2_000],
        "trade_count": [20],
    }


def _effective_spread_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00-09:05"],
        "sector": ["Banks"],
        "effective_spread_bps": [6.25],
        "trade_count": [20],
        "notional": [25_000_000.0],
    }


def _price_impact_result() -> dict[str, list[object]]:
    return {
        "date": [date(2026, 5, 1)],
        "time_bucket": ["09:00-09:05"],
        "sector": ["Banks"],
        "price_impact_30s_bps": [4.75],
        "trade_count": [20],
        "notional": [25_000_000.0],
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

    assert contract.template_name == "liquidity.q"
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


def test_liquidity_ticks_input_contract_requires_tick_size() -> None:
    contract = liquidity_ticks_input_schema_contract(
        quotes_table="quote_l1",
        extra_required_columns=("sector", "sym"),
    )

    assert contract.template_name == "liquidity_ticks.q"
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
        "tick_size",
        "sector",
    )
    assert "tick_size" in contract.assumptions[-1]


def test_realized_volatility_input_contract_requires_symbol_for_returns() -> None:
    contract = realized_volatility_input_schema_contract(
        quotes_table="quote_l1",
        extra_required_columns=("sector", "sym"),
    )

    assert contract.template_name == "realized_volatility.q"
    assert contract.table_role == "quotes"
    assert contract.table_name == "quote_l1"
    assert contract.required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
        "sector",
    )
    assert "within each symbol" in contract.assumptions[0]


def test_flow_input_contract_requires_feed_side() -> None:
    contract = flow_input_schema_contract(
        trades_table="trade_l1",
        extra_required_columns=("sector", "sym"),
    )

    assert contract.template_name == "flow.q"
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
        "aggressorSide",
        "sector",
    )
    assert "buy=1" in contract.assumptions[0]


def test_effective_spread_input_contracts_require_trade_and_quote_symbols() -> None:
    trade_contract, quote_contract = effective_spread_input_schema_contracts(
        trades_table="trade_l1",
        quotes_table="quote_l1",
        extra_trade_required_columns=("sector", "sym"),
    )

    assert trade_contract.template_name == "effective_spread.q"
    assert trade_contract.table_role == "trades"
    assert trade_contract.table_name == "trade_l1"
    assert trade_contract.required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "tradePrice",
        "tradeSize",
        "sector",
    )
    assert quote_contract.table_role == "quotes"
    assert quote_contract.table_name == "quote_l1"
    assert quote_contract.required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
    )
    assert "same symbol" in trade_contract.assumptions[0]


def test_price_impact_input_contracts_infer_side_and_require_quotes() -> None:
    trade_contract, quote_contract = price_impact_input_schema_contracts(
        trades_table="trade_l1",
        quotes_table="quote_l1",
        extra_trade_required_columns=("sector", "sym"),
    )

    assert trade_contract.template_name == "price_impact.q"
    assert trade_contract.table_role == "trades"
    assert trade_contract.required_columns == (
        "date",
        "time",
        "sym",
        "session",
        "auction",
        "tradePrice",
        "tradeSize",
        "sector",
    )
    assert quote_contract.template_name == "price_impact.q"
    assert quote_contract.table_role == "quotes"
    assert quote_contract.required_columns == (
        "date",
        "time",
        "sym",
        "bidPrice",
        "askPrice",
    )
    assert "infers aggressorSide" in trade_contract.assumptions[0]


def test_activity_contract_lists_all_template_output_columns() -> None:
    contract = activity_output_schema_contract(
        "volume",
        group_by=("topixCapGrp",),
    )

    assert contract.template_name == "activity.q"
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


def test_liquidity_ticks_contract_lists_tick_spread_columns() -> None:
    contract = liquidity_ticks_output_schema_contract(
        "quoted_spread_ticks",
        group_by=("sector",),
    )

    assert contract.template_name == "liquidity_ticks.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "quoted_spread_ticks",
    )


def test_liquidity_ticks_contract_validates_result() -> None:
    validate_liquidity_ticks_output_schema(
        metric_name="quoted_spread_ticks",
        result=_liquidity_ticks_result(),
        group_by=("sector",),
    )

    result = _liquidity_ticks_result()
    del result["quoted_spread_ticks"]
    with pytest.raises(OutputSchemaContractError, match="quoted_spread_ticks"):
        validate_liquidity_ticks_output_schema(
            metric_name="quoted_spread_ticks",
            result=result,
            group_by=("sector",),
        )


def test_liquidity_ticks_contract_rejects_non_tick_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="quoted_spread_ticks"):
        liquidity_ticks_output_schema_contract("quoted_spread_bps")


def test_realized_volatility_contract_lists_metadata_columns() -> None:
    contract = realized_volatility_output_schema_contract(
        "realized_volatility",
        group_by=("sector",),
    )

    assert contract.template_name == "realized_volatility.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "realized_volatility",
        "return_count",
        "first_mid",
        "last_mid",
    )


def test_realized_volatility_contract_validates_result_and_rejects_missing_metadata() -> None:
    validate_realized_volatility_output_schema(
        metric_name="realized_volatility",
        result=_realized_volatility_result(),
        group_by=("sector",),
    )

    result = _realized_volatility_result()
    del result["return_count"]
    with pytest.raises(OutputSchemaContractError, match="return_count"):
        validate_realized_volatility_output_schema(
            metric_name="realized_volatility",
            result=result,
            group_by=("sector",),
        )


def test_realized_volatility_contract_rejects_non_volatility_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="realized_volatility"):
        realized_volatility_output_schema_contract("quoted_spread_bps")


def test_effective_spread_contract_lists_output_columns_and_metadata() -> None:
    contract = effective_spread_output_schema_contract(
        "effective_spread_bps",
        group_by=("sector",),
    )

    assert contract.template_name == "effective_spread.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "effective_spread_bps",
        "trade_count",
        "notional",
    )
    contract.validate_result(_effective_spread_result())


def test_effective_spread_contract_validates_result_and_rejects_missing_metadata() -> None:
    validate_effective_spread_output_schema(
        metric_name="effective_spread_bps",
        result=_effective_spread_result(),
        group_by=("sector",),
    )

    result = _effective_spread_result()
    del result["notional"]
    with pytest.raises(OutputSchemaContractError, match="notional"):
        validate_effective_spread_output_schema(
            metric_name="effective_spread_bps",
            result=result,
            group_by=("sector",),
        )


def test_effective_spread_contract_rejects_non_effective_spread_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="effective_spread_bps"):
        effective_spread_output_schema_contract("quoted_spread_bps")


def test_price_impact_contract_lists_output_columns_and_metadata() -> None:
    contract = price_impact_output_schema_contract(
        "price_impact_30s_bps",
        group_by=("sector",),
    )

    assert contract.template_name == "price_impact.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "price_impact_30s_bps",
        "trade_count",
        "notional",
    )
    contract.validate_result(_price_impact_result())


def test_price_impact_contract_validates_result_and_rejects_missing_metadata() -> None:
    validate_price_impact_output_schema(
        metric_name="price_impact_30s_bps",
        result=_price_impact_result(),
        group_by=("sector",),
    )

    result = _price_impact_result()
    del result["notional"]
    with pytest.raises(OutputSchemaContractError, match="notional"):
        validate_price_impact_output_schema(
            metric_name="price_impact_30s_bps",
            result=result,
            group_by=("sector",),
        )


def test_price_impact_contract_rejects_non_price_impact_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="price_impact_30s_bps"):
        price_impact_output_schema_contract("effective_spread_bps")


def test_flow_contract_lists_all_template_output_columns() -> None:
    contract = flow_output_schema_contract(
        "signed_turnover",
        group_by=("sector",),
    )

    assert contract.template_name == "flow.q"
    assert contract.required_columns == (
        "date",
        "time_bucket",
        "sector",
        "signed_turnover",
        "trade_imbalance",
        "signed_volume",
        "volume",
        "trade_count",
    )


def test_flow_contract_validates_result_and_rejects_missing_metadata() -> None:
    validate_flow_output_schema(
        metric_name="trade_imbalance",
        result=_flow_result(),
        group_by=("sector",),
    )

    result = _flow_result()
    del result["signed_volume"]
    with pytest.raises(OutputSchemaContractError, match="signed_volume"):
        validate_flow_output_schema(
            metric_name="trade_imbalance",
            result=result,
            group_by=("sector",),
        )


def test_flow_contract_rejects_non_flow_metric() -> None:
    with pytest.raises(OutputSchemaContractError, match="flow metrics"):
        flow_output_schema_contract("turnover")


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

    assert pts_contract.template_name == "toxicity_reversion.q"
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
        group_by=("topixCapGrp",),
    )

    assert contract.required_columns == (
        "date",
        "time_bucket",
        "topixCapGrp",
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
    validate_output_schema_for_template(
        template_name="liquidity_ticks.q",
        metric_name="quoted_spread_ticks",
        result=_liquidity_ticks_result(),
        group_by=("sector",),
    )
    validate_output_schema_for_template(
        template_name="realized_volatility.q",
        metric_name="realized_volatility",
        result=_realized_volatility_result(),
        group_by=("sector",),
    )
    validate_output_schema_for_template(
        template_name="effective_spread.q",
        metric_name="effective_spread_bps",
        result=_effective_spread_result(),
        group_by=("sector",),
    )
    validate_output_schema_for_template(
        template_name="price_impact.q",
        metric_name="price_impact_30s_bps",
        result=_price_impact_result(),
        group_by=("sector",),
    )
    validate_output_schema_for_template(
        template_name="flow.q",
        metric_name="signed_turnover",
        result=_flow_result(),
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



def test_output_schema_validation_accepts_keyed_table_mapping_representation() -> None:
    validate_output_schema_for_template(
        template_name="liquidity.q",
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
                "aggregationLevel": ["symbol_bucket"],
                "groupType": ["sym"],
                "groupValue": ["7203"],
            },
        },
    )
