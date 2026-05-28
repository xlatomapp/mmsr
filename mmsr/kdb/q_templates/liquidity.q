/ Liquidity metrics template.
/ Expected params:
/   `quotes_table`: raw-data function expression/table returning canonical quotes
/   `ref_table`: expression/table returning day reference data
/   `calculation_namespace`: namespace where MMSR installs calculation functions
/   `date_filter`
/   `ref_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`

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
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    quotes: {{ quotes_table }} lj refs;
    select
        quoted_spread_bps: {{ calculation_namespace }}.medianQuotedSpreadBps[bidPrice; askPrice],
        top_of_book_depth: {{ calculation_namespace }}.medianTopOfBookDepth[bidSize; askSize]
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from quotes
    where {{ date_filter }}{{ symbol_filter }},
          bidPrice > 0,
          askPrice > bidPrice
    };

{{ calculation_namespace }}.calcLiquidity[]
