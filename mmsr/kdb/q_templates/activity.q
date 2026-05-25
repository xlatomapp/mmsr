/ Activity metrics template.
/ Expected params:
/   `trades_table`
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.activity_output_schema_contract
/   date | time_bucket | optional group columns | requested metric column |
/   sibling aggregate columns from turnover, volume, trade_count

select
    turnover: sum trade_price * trade_size,
    volume: sum trade_size,
    trade_count: count i
by date, time_bucket: {{ bucket_expr }}{{ group_by }}
from {{ trades_table }}
where {{ date_filter }}, {{ time_filter }}{{ symbol_filter }}
