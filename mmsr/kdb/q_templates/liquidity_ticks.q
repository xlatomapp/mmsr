/ Tick-normalized quoted-spread template.
/ Expected params:
/   `quotes_table`: table name or raw-data function expression returning canonical quotes
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.liquidity_ticks_output_schema_contract
/   date | time_bucket | optional group columns | quoted_spread_ticks
/
/ The canonical quote source must already expose tick_size. Production users can
/ satisfy this by joining the exchange tick-size ladder or symbol metadata inside
/ their raw quote function before returning rows to MMSR.

{{ calculation_namespace }}.calcLiquidityTicks:{
    select
        quoted_spread_ticks: med (ask_price - bid_price) % tick_size
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from {{ quotes_table }}
    where {{ date_filter }}, {{ time_filter }}{{ symbol_filter }}, bid_price > 0, ask_price > bid_price, tick_size > 0
    };

{{ calculation_namespace }}.calcLiquidityTicks[]
