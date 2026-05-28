/ Signed flow compatibility template.
/ Flow still requires an aggressorSide column on the enriched trade source.

{{ calculation_namespace }}.calcFlow:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    trades: {{ trades_table }} lj refs;
    select
        signed_turnover: sum aggressorSide * tradePrice * tradeSize,
        trade_imbalance: (sum aggressorSide * tradeSize) % sum tradeSize,
        signed_volume: sum aggressorSide * tradeSize,
        volume: sum tradeSize,
        trade_count: count i
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from trades
    where {{ date_filter }}{{ symbol_filter }},
          tradePrice > 0,
          tradeSize > 0,
          aggressorSide in (1 -1)
    };

{{ calculation_namespace }}.calcFlow[]
