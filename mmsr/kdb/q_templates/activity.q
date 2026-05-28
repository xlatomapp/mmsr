/ Activity metrics template.
/ Expected params:
/   `trades_table`: raw-data function expression/table returning canonical trades
/   `ref_table`: expression/table returning day reference data
/   `calculation_namespace`: namespace where MMSR installs calculation functions
/   `date_filter`
/   `ref_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`

{{ calculation_namespace }}.sumNotional:{[price;size] sum price * size};
{{ calculation_namespace }}.sumSize:{[size] sum size};
{{ calculation_namespace }}.rowCount:{[rows] count rows};
{{ calculation_namespace }}.timeBucket:{[t;session;auction;bucket]
    labels:`$string bucket xbar t;
    labels[where (auction = `open) & session = `am]:`AMO;
    labels[where (auction = `close) & session = `am]:`AMC;
    labels[where (auction = `open) & session = `pm]:`PMO;
    labels[where (auction = `close) & session = `pm]:`PMC;
    labels
    };

{{ calculation_namespace }}.calcActivity:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    trades: {{ trades_table }} lj refs;
    select
        turnover: {{ calculation_namespace }}.sumNotional[tradePrice; tradeSize],
        volume: {{ calculation_namespace }}.sumSize[tradeSize],
        trade_count: {{ calculation_namespace }}.rowCount[i]
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from trades
    where {{ date_filter }}{{ symbol_filter }},
          tradePrice > 0,
          tradeSize > 0
    };

{{ calculation_namespace }}.calcActivity[]
