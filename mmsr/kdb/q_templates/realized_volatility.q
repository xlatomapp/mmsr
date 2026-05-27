/ Quote-mid realized-volatility template.
/ Expected params:
/   `quotes_table`: table name or raw-data function expression returning canonical quotes
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.realized_volatility_output_schema_contract
/   date | time_bucket | optional group columns | realized_volatility |
/   return_count | first_mid | last_mid
/
/ This template uses adjacent valid quote-mid log returns by date and symbol, then
/ aggregates those returns by report bucket and requested group. The output is in
/ basis points and is not annualized.

{{ calculation_namespace }}.calcRealizedVolatility:{
    cleanQuotes:
        select from {{ quotes_table }}
        where {{ date_filter }},
              {{ time_filter }}{{ symbol_filter }},
              bid_price > 0,
              ask_price > bid_price,
              not null sym;

    quoteMids:
        update
            mid: (bid_price + ask_price) % 2
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
