/ Quote-mid realized-volatility template.
/ Expected params:
/   `quotes_table`: raw-data function expression/table returning canonical quotes
/   `ref_table`: expression/table returning day reference data
/   `calculation_namespace`
/   `date_filter`
/   `ref_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`

{{ calculation_namespace }}.calcRealizedVolatility:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    quotes: {{ quotes_table }} lj refs;

    cleanQuotes:
        select from quotes
        where {{ date_filter }}{{ symbol_filter }},
              bidPrice > 0,
              askPrice > bidPrice,
              not null sym;

    quoteMids:
        update
            mid: (bidPrice + askPrice) % 2
        from cleanQuotes;

    quoteReturns:
        update
            log_return: log_mid - prev log_mid
        by date, sym
        from `date`sym`time xasc update log_mid: log mid from quoteMids;

    select
        realized_volatility: 10000 * sqrt avg log_return * log_return,
        return_count: count i,
        first_mid: first mid,
        last_mid: last mid
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from quoteReturns
    where not null log_return
    };

{{ calculation_namespace }}.calcRealizedVolatility[]
