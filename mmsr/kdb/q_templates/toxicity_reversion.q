/ Primary-quote reversion query template.
/ Expected params:
/   `venue_trades_table`
/   `primary_quotes_table`
/   `date_filter`
/   `time_filter`
/   `bucket_expr`
/   `group_by`
/   `venue_filter`
/   `primary_venue`
/   `horizon`
/   `horizon_label`
/   `horizon_sort_order`
/   `max_primary_quote_age`
/   `value_column`
/
/ Input and output schema contracts:
/   Required source-table columns are mirrored by
/   mmsr.kdb.schema_contracts.toxicity_reversion_input_schema_contracts.
/   Required output columns are mirrored by
/   mmsr.kdb.schema_contracts.toxicity_reversion_output_schema_contract.
/   date | time_bucket | venue | horizon | optional group columns |
/   value column | horizon_sort_order | trade_count | notional | positive_reversion_ratio |
/   valid_primary_quote_ratio
/
/ This template is schema-explicit enough for offline runner integration while
/ still documenting assumptions that must be confirmed before live production
/ use. It expects venue trades with date, time, sym, venue, trade_price,
/ trade_size, and aggressor_side where buy is 1 and sell is -1. It expects
/ primary quotes with date, time, sym, venue, bid_price, and ask_price.

venueTrades:
    select
        date,
        time,
        sym,
        venue,
        trade_price,
        trade_size,
        notional: trade_price * trade_size,
        aggressor_side
    from {{ venue_trades_table }}
    where {{ date_filter }},
          {{ time_filter }},
          {{ venue_filter }},
          trade_size > 0,
          not null aggressor_side;

primaryQuotes:
    select
        date,
        time,
        quote_time: time,
        sym,
        bid_price,
        ask_price,
        primary_mid: (bid_price + ask_price) % 2
    from {{ primary_quotes_table }}
    where {{ date_filter }},
          venue = {{ primary_venue }},
          bid_price > 0,
          ask_price > bid_price;

tradeWithPreMid: aj[`date`sym`time; venueTrades; primaryQuotes];

tradeForHorizon:
    update
        horizon_time: time + {{ horizon }},
        primary_quote_age: time - quote_time
    from tradeWithPreMid;

postQuotes:
    select
        date,
        horizon_time: time,
        post_quote_time: time,
        sym,
        post_mid: primary_mid
    from primaryQuotes;

tradeWithPostMid: aj[`date`sym`horizon_time; tradeForHorizon; postQuotes];

scored:
    update
        reversion_bps: aggressor_side * 10000 * (post_mid - primary_mid) % primary_mid,
        horizon_sort_order: {{ horizon_sort_order }},
        valid_primary_quote: (primary_quote_age <= {{ max_primary_quote_age }}) &
            (horizon_time - post_quote_time) <= {{ max_primary_quote_age }}
    from tradeWithPostMid;

select
    {{ value_column }}: wavg[notional; reversion_bps],
    horizon_sort_order: first horizon_sort_order,
    positive_reversion_ratio: avg reversion_bps > 0,
    trade_count: count i,
    notional: sum notional,
    valid_primary_quote_ratio: avg valid_primary_quote
by date, time_bucket: {{ bucket_expr }}, venue, horizon: {{ horizon_label }}{{ group_by }}
from scored
where valid_primary_quote,
      not null primary_mid,
      not null post_mid,
      primary_mid > 0
