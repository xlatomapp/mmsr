/ Feed-signed flow metrics template.
/ Expected params:
/   `trades_table`: table name or raw-data function expression returning canonical trades
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.flow_output_schema_contract
/   date | time_bucket | optional group columns | requested metric column |
/   sibling aggregate columns from signed_turnover, trade_imbalance |
/   signed_volume | volume | trade_count
/
/ This first flow slice intentionally uses feed-provided aggressor_side with
/ buy=1 and sell=-1. Quote-based side inference can be added later as a separate
/ production metric enhancement.

{{ calculation_namespace }}.calcFlow:{
    select
        signed_turnover: sum aggressor_side * trade_price * trade_size,
        trade_imbalance: (sum aggressor_side * trade_size) % sum trade_size,
        signed_volume: sum aggressor_side * trade_size,
        volume: sum trade_size,
        trade_count: count i
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from {{ trades_table }}
    where {{ date_filter }},
          {{ time_filter }}{{ symbol_filter }},
          trade_price > 0,
          trade_size > 0,
          aggressor_side in (1 -1)
    };

{{ calculation_namespace }}.calcFlow[]
