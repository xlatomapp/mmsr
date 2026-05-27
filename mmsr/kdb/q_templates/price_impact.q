/ Price-impact transaction-cost metrics template.
/ Expected params:
/   `trades_table`: table name or raw-data function expression returning canonical trades
/   `quotes_table`: table name or raw-data function expression returning canonical quotes
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/   `horizon`
/   `max_quote_age`
/   `max_horizon_quote_age`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.price_impact_output_schema_contract
/   date | time_bucket | optional group columns | price_impact_30s_bps |
/   trade_count | notional
/
/ This first price-impact slice uses feed-provided aggressor_side with buy=1 and
/ sell=-1. It as-of joins each trade to the prevailing same-symbol quote mid
/ before the trade and to the prevailing same-symbol quote mid at trade time plus
/ the fixed 30s horizon.

{{ calculation_namespace }}.calcPriceImpact:{
    trades:
        select
            date,
            time,
            sym,
            trade_price,
            trade_size,
            aggressor_side,
            notional: trade_price * trade_size{{ group_by }}
        from {{ trades_table }}
        where {{ date_filter }},
              {{ time_filter }}{{ symbol_filter }},
              trade_price > 0,
              trade_size > 0,
              aggressor_side in (1 -1),
              not null sym;

    quotes:
        select
            date,
            time,
            quote_time: time,
            sym,
            mid: (bid_price + ask_price) % 2
        from {{ quotes_table }}
        where {{ date_filter }},
              {{ time_filter }}{{ symbol_filter }},
              bid_price > 0,
              ask_price > bid_price,
              not null sym;

    tradesWithBefore:
        aj[`date`sym`time; `date`sym`time xasc trades; `date`sym`time xasc quotes];

    horizonRequests:
        update horizon_time: time + {{ horizon }}
        from tradesWithBefore;

    horizonQuotes:
        select
            date,
            sym,
            horizon_time: time,
            horizon_quote_time: time,
            horizon_mid: mid
        from quotes;

    scored:
        update
            quote_age: time - quote_time,
            horizon_quote_age: horizon_time - horizon_quote_time,
            price_impact_30s_bps: aggressor_side * 10000 * (horizon_mid - mid) % mid
        from aj[
            `date`sym`horizon_time;
            `date`sym`horizon_time xasc horizonRequests;
            `date`sym`horizon_time xasc horizonQuotes
        ];

    select
        price_impact_30s_bps: med price_impact_30s_bps,
        trade_count: count i,
        notional: sum notional
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from scored
    where quote_age <= {{ max_quote_age }},
          horizon_quote_age <= {{ max_horizon_quote_age }},
          not null mid,
          not null horizon_mid,
          mid > 0
    };

{{ calculation_namespace }}.calcPriceImpact[]
