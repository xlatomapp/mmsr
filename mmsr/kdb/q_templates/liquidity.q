/ Liquidity metrics template.
/ Expected params:
/   `quotes_table`: table name or raw-data function expression returning canonical quotes
/   `ref_table`: raw-data function expression returning day/symbol reference data
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.liquidity_output_schema_contract
/   date | time_bucket | optional group columns | requested metric column |
/   sibling aggregate columns from quoted_spread_bps, top_of_book_depth

{{ calculation_namespace }}.medianQuotedSpreadBps:{[bid;ask] med 10000 * (ask - bid) % ((ask + bid) % 2)};
{{ calculation_namespace }}.medianTopOfBookDepth:{[bidSize;askSize] med bidSize + askSize};
{{ calculation_namespace }}.timeBucket:{[t;session;auction;bucket]
    labels:`$string bucket xbar t;
    labels[where (auction = `open) & session = `am]:`AMO;
    labels[where (auction = `close) & session = `am]:`AMC;
    labels[where (auction = `open) & session = `pm]:`PMO;
    labels[where (auction = `close) & session = `pm]:`PMC;
    labels
    };

{{ calculation_namespace }}.calcLiquidity:{
    refs: `sym xkey select from {{ ref_table }};
    quotes: {{ quotes_table }} lj refs;
    select
        quoted_spread_bps: {{ calculation_namespace }}.medianQuotedSpreadBps[bid_price; ask_price],
        top_of_book_depth: {{ calculation_namespace }}.medianTopOfBookDepth[bid_size; ask_size]
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from quotes
    where {{ date_filter }}{{ symbol_filter }}, bid_price > 0, ask_price > bid_price
    };

{{ calculation_namespace }}.calcLiquidity[]
