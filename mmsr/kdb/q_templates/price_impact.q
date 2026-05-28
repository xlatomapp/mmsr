/ Price-impact transaction-cost compatibility template.
/ MMSR infers aggressorSide from the prevailing quote midpoint.

{{ calculation_namespace }}.inferAggressorSide:{[tradePrice;mid] ?[tradePrice>mid;1;?[tradePrice<mid;-1;0]]};

{{ calculation_namespace }}.calcPriceImpact:{
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

    tradesWithBefore:
        aj[`date`sym`time; `date`sym`time xasc trades; `date`sym`time xasc quotes];

    horizonRequests:
        update
            aggressorSide: {{ calculation_namespace }}.inferAggressorSide[tradePrice; mid],
            horizonTime: time + {{ horizon }},
            quoteAge: time - quoteTime
        from tradesWithBefore;

    horizonQuotes:
        select
            date,
            sym,
            horizonTime: time,
            horizonQuoteTime: time,
            horizonMid: mid
        from quotes;

    scored:
        update
            horizonQuoteAge: horizonTime - horizonQuoteTime,
            price_impact_30s_bps: aggressorSide * 10000 * (horizonMid - mid) % mid
        from aj[
            `date`sym`horizonTime;
            `date`sym`horizonTime xasc horizonRequests;
            `date`sym`horizonTime xasc horizonQuotes
        ];

    select
        price_impact_30s_bps: med price_impact_30s_bps,
        trade_count: count i,
        notional: sum notional
    by date, time_bucket: {{ bucket_expr }}{{ group_by }}
    from scored
    where quoteAge <= {{ max_quote_age }},
          horizonQuoteAge <= {{ max_horizon_quote_age }},
          aggressorSide in (1 -1),
          not null mid,
          not null horizonMid,
          mid > 0
    };

{{ calculation_namespace }}.calcPriceImpact[]
