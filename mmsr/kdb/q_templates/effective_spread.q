/ Effective-spread transaction-cost compatibility template.
/ Source functions receive `date` and the filtered reference table.

{{ calculation_namespace }}.calcEffectiveSpread:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    rawTrades: {{ trades_table }} lj refs;
    rawQuotes: {{ quotes_table }} lj refs;

    trades:
        select
            date,
            time,
            sym,
            tradePrice,
            tradeSize,
            notional: tradePrice * tradeSize{{ group_by }}
        from rawTrades
        where {{ date_filter }}{{ symbol_filter }},
              tradePrice > 0,
              tradeSize > 0,
              not null sym;

    quotes:
        select
            date,
            time,
            quoteTime: time,
            sym,
            mid: (bidPrice + askPrice) % 2
        from rawQuotes
        where {{ date_filter }}{{ symbol_filter }},
              bidPrice > 0,
              askPrice > bidPrice,
              not null sym;

    tradeWithMid: aj[`date`sym`time; `date`sym`time xasc trades; `date`sym`time xasc quotes];

    scored:
        update
            quoteAge: time - quoteTime,
            effective_spread_bps: 20000 * abs[tradePrice - mid] % mid
        from tradeWithMid;

    select
        effective_spread_bps: med effective_spread_bps,
        trade_count: count i,
        notional: sum notional
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from scored
    where quoteAge <= {{ max_quote_age }},
          not null mid,
          mid > 0
    };

{{ calculation_namespace }}.calcEffectiveSpread[]
