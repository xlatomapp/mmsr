from datetime import time

from mmsr.presentation.labels import (
    format_comparison_scope_label,
    format_group_item_label,
    format_group_key_label,
    format_group_label,
    format_group_value_label,
    format_intraday_bucket_label,
    format_reference_observation_unit_label,
)


def test_intraday_bucket_labels_expand_auction_codes_and_time_ranges() -> None:
    assert format_intraday_bucket_label("AMO") == "AM opening auction"
    assert format_intraday_bucket_label("AMC") == "AM closing auction"
    assert format_intraday_bucket_label("PMO") == "PM opening auction"
    assert format_intraday_bucket_label("PMC") == "PM closing auction"
    assert format_intraday_bucket_label("09:00-09:05") == "09:00–09:05"
    assert format_intraday_bucket_label(time(9, 5)) == "09:05"
    assert format_intraday_bucket_label(None) is None


def test_group_labels_replace_internal_key_equals_text() -> None:
    assert format_group_key_label("market_cap_bucket") == "Market cap bucket"
    assert format_group_key_label("topixCapGrp") == "TOPIX cap group"
    assert format_group_value_label("market_cap_bucket", "Small") == "Small cap"
    assert format_group_item_label("market_cap_bucket", "Small") == "Market cap bucket: Small cap"
    assert (
        format_group_label({"market_cap_bucket": "Small", "venue": "TSE"}) == "Market cap bucket: Small cap, Venue: TSE"
    )


def test_reference_observation_unit_labels_are_human_readable() -> None:
    assert format_reference_observation_unit_label("trading_day") == "trading day"
    assert format_reference_observation_unit_label("time_bucket") == "intraday bucket"
    assert format_reference_observation_unit_label("symbol_day") == "symbol day"


def test_comparison_scope_label_orders_date_bucket_and_group() -> None:
    assert format_comparison_scope_label(
        observation_date="2026-05-22",
        time_bucket="AMO",
        group={"market_cap_bucket": "Small"},
    ) == ("Date: 2026-05-22, Intraday bucket: AM opening auction, Market cap bucket: Small cap")
