/ Tick-normalized quoted-spread template.
/ Expected params:
/   `quotes_table`: raw-data function expression/table returning canonical quotes
/   `ref_table`: expression/table returning day reference data
/   `calculation_namespace`
/   `date_filter`
/   `ref_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`

{{ calculation_namespace }}.calcLiquidityTicks:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    quotes: {{ quotes_table }} lj refs;
    select
        quoted_spread_ticks: med (askPrice - bidPrice) % tick_size
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from quotes
    where {{ date_filter }}{{ symbol_filter }},
          bidPrice > 0,
          askPrice > bidPrice,
          tick_size > 0
    };

{{ calculation_namespace }}.calcLiquidityTicks[]
