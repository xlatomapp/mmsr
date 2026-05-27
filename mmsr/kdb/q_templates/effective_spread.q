/ Effective-spread transaction-cost metrics template.
/ Expected params:
/   `trades_table`: table name or raw-data function expression returning canonical trades
/   `quotes_table`: table name or raw-data function expression returning canonical quotes
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `time_filter`
/   `symbol_filter`
/   `bucket_expr`
/   `group_by`
/   `max_quote_age`
/ Output schema contract (also exposed by RenderedMetricQuery):
/   mmsr.kdb.schema_contracts.effective_spread_output_schema_contract
/   date | time_bucket | optional group columns | effective_spread_bps |
/   trade_count | notional
/
/ This first transaction-cost slice uses an as-of join from trades to the
/ prevailing same-symbol quote-mid at or before the trade timestamp. It uses the
/ unsigned effective-spread formula so it does not require aggressor_side.

{{ calculation_namespace }}.calcEffectiveSpread:{
    trades:
        select
            date,
            time,
            sym,
            trade_price,
            trade_size,
            notional: trade_price * trade_size{{ group_by }}
        from {{ trades_table }}
        where {{ date_filter }},
              {{ time_filter }}{{ symbol_filter }},
              trade_price > 0,
              trade_size > 0,
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

    tradeWithMid: aj[`date`sym`time; `date`sym`time xasc trades; `date`sym`time xasc quotes];

    scored:
        update
            quote_age: time - quote_time,
            effective_spread_bps: 20000 * abs[trade_price - mid] % mid
        from tradeWithMid;

    select
        effective_spread_bps: med effective_spread_bps,
        trade_count: count i,
        notional: sum notional
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from scored
    where quote_age <= {{ max_quote_age }},
          not null mid,
          mid > 0
    };

{{ calculation_namespace }}.calcEffectiveSpread[]
