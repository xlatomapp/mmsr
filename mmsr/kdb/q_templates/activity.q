/ Activity metrics template.
/ Expected params:
/   `trades_table`: table name or raw-data function expression returning canonical trades
/   `ref_table`: raw-data function expression returning day/symbol reference data
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.activity_output_schema_contract
/   date | time_bucket | optional group columns | requested metric column |
/   sibling aggregate columns from turnover, volume, trade_count

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
    refs: `sym xkey select from {{ ref_table }};
    trades: {{ trades_table }} lj refs;
    select
        turnover: {{ calculation_namespace }}.sumNotional[trade_price; trade_size],
        volume: {{ calculation_namespace }}.sumSize[trade_size],
        trade_count: {{ calculation_namespace }}.rowCount[i]
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from trades
    where {{ date_filter }}{{ symbol_filter }}
    };

{{ calculation_namespace }}.calcActivity[]
