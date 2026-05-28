/ Primary-quote reversion query template.
/ Expected params:
/   `venue_trades_table`: raw-data function expression/table returning venue trades
/   `primary_quotes_table`: raw-data function expression/table returning primary quotes
/   `ref_table`: expression/table returning day reference data
/   `calculation_namespace`: namespace where MMSR installs calculation functions
/   `date_filter`
/   `ref_filter`
/   `bucket_expr`
/   `group_by`
/   `venue_filter`
/   `auction_filter`
/   `primary_venue`
/   `horizon`
/   `horizon_label`
/   `horizon_sort_order`
/   `max_primary_quote_age`
/   `max_venue_quote_age`
/   `value_column`
/
/ Reversion convention: inferred aggressorSide * (future TSE/primary mid - primary mid at trade) / future TSE/primary mid * 10000.
/ Aggressor side is inferred from each trade's own venue/symbol prevailing quote.

{{ calculation_namespace }}.weightedAverage:{[weights;values] wavg[weights; values]};
{{ calculation_namespace }}.positiveRatio:{[values] avg values > 0};
{{ calculation_namespace }}.sumNotional:{[price;size] sum price * size};
{{ calculation_namespace }}.rowCount:{[rows] count rows};
{{ calculation_namespace }}.inferAggressorSide:{[tradePrice;mid] ?[tradePrice>mid;1;?[tradePrice<mid;-1;0]]};
{{ calculation_namespace }}.timeBucket:{[t;session;auction;bucket]
    labels:`$string bucket xbar t;
    labels[where (auction = `open) & session = `am]:`AMO;
    labels[where (auction = `close) & session = `am]:`AMC;
    labels[where (auction = `open) & session = `pm]:`PMO;
    labels[where (auction = `close) & session = `pm]:`PMC;
    labels
    };

{{ calculation_namespace }}.calcToxicityReversion:{
    rawRefs: select from {{ ref_table }};
    refs: `sym xkey select from rawRefs where {{ ref_filter }};
    rawVenueTrades: {{ venue_trades_table }} lj refs;
    rawQuotes: {{ primary_quotes_table }} lj refs;

    venueTrades:
        select
            date,
            time,
            sym,
            session,
            auction,
            venue,
            tradePrice,
            tradeSize,
            notional: tradePrice * tradeSize
        from rawVenueTrades
        where {{ date_filter }},
              {{ venue_filter }},
              {{ auction_filter }},
              tradeSize > 0,
              tradePrice > 0,
              not null venue;

    venueQuotes:
        select
            date,
            time,
            venueQuoteTime: time,
            sym,
            venue,
            venueMid: (bidPrice + askPrice) % 2
        from rawQuotes
        where {{ date_filter }},
              {{ venue_filter }},
              bidPrice > 0,
              askPrice > bidPrice,
              not null venue;

    primaryQuotes:
        select
            date,
            time,
            primaryQuoteTime: time,
            sym,
            bidPrice,
            askPrice,
            primaryMid: (bidPrice + askPrice) % 2
        from rawQuotes
        where {{ date_filter }},
              venue = {{ primary_venue }},
              bidPrice > 0,
              askPrice > bidPrice;

    tradeWithVenueQuote:
        aj[
            `date`sym`venue`time;
            `date`sym`venue`time xasc venueTrades;
            `date`sym`venue`time xasc venueQuotes
        ];

    tradeWithPreMid:
        aj[
            `date`sym`time;
            `date`sym`time xasc tradeWithVenueQuote;
            `date`sym`time xasc primaryQuotes
        ];

    tradeForHorizon:
        update
            aggressorSide: {{ calculation_namespace }}.inferAggressorSide[tradePrice; venueMid],
            horizonTime: time + {{ horizon }},
            venueQuoteAge: time - venueQuoteTime,
            primaryQuoteAge: time - primaryQuoteTime
        from tradeWithPreMid;

    postQuotes:
        select
            date,
            horizonTime: time,
            postQuoteTime: time,
            sym,
            postMid: primaryMid
        from primaryQuotes;

    tradeWithPostMid: aj[`date`sym`horizonTime; `date`sym`horizonTime xasc tradeForHorizon; `date`sym`horizonTime xasc postQuotes];

    scored:
        update
            reversion_bps: aggressorSide * 10000 * (postMid - primaryMid) % postMid,
            horizon_sort_order: {{ horizon_sort_order }},
            valid_primary_quote: (primaryQuoteAge <= {{ max_primary_quote_age }}) &
                (horizonTime - postQuoteTime) <= {{ max_primary_quote_age }},
            valid_venue_quote: venueQuoteAge <= {{ max_venue_quote_age }}
        from tradeWithPostMid;

    select
        {{ value_column }}: {{ calculation_namespace }}.weightedAverage[notional; reversion_bps],
        horizon_sort_order: first horizon_sort_order,
        positive_reversion_ratio: {{ calculation_namespace }}.positiveRatio[reversion_bps],
        trade_count: {{ calculation_namespace }}.rowCount[i],
        notional: sum notional,
        valid_primary_quote_ratio: avg valid_primary_quote
    by date, time_bucket: {{ bucket_expr }}, venue, horizon: {{ horizon_label }}{{ group_by }}
    from scored
    where valid_primary_quote,
          valid_venue_quote,
          aggressorSide in (1 -1),
          not null venueMid,
          not null primaryMid,
          not null postMid,
          postMid > 0
    };

{{ calculation_namespace }}.calcToxicityReversion[]
