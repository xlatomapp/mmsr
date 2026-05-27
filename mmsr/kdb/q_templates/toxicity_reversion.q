/ Primary-quote reversion query template.
/ Expected params:
/   `venue_trades_table`: table name or raw-data function expression returning canonical venue trades
/   `primary_quotes_table`: table name or raw-data function expression returning canonical primary quotes
/   `ref_table`: raw-data function expression returning day/symbol reference data
/   `calculation_namespace`: namespace where MMSR installs the calculation function
/   `date_filter`
/   `bucket_expr`
/   `group_by`
/   `venue_filter`
/   `auction_filter`
/   `primary_venue`
/   `horizon`
/   `horizon_label`
/   `horizon_sort_order`
/   `max_primary_quote_age`
/   `value_column`
/
/ Input and output schema contracts:
/   Required source columns are mirrored by
/   mmsr.kdb.schema_contracts.toxicity_reversion_input_schema_contracts.
/   Required output columns are mirrored by
/   mmsr.kdb.schema_contracts.toxicity_reversion_output_schema_contract.
/   date | time_bucket | venue | horizon | optional group columns |
/   value column | horizon_sort_order | trade_count | notional | positive_reversion_ratio |
/   valid_primary_quote_ratio
/   optional: context_sort_order
/
/ This template is schema-explicit enough for offline runner integration while
/ still documenting assumptions that must be confirmed before live production
/ use. It expects venue trades with date, time, sym, venue, trade_price,
/ trade_size, and aggressor_side where buy is 1 and sell is -1. It expects
/ primary quotes with date, time, sym, venue, bid_price, and ask_price.
/ Reversion convention: aggressor_side * (future_mid - mid_at_trade) / future_mid * 10000.

{{ calculation_namespace }}.weightedAverage:{[weights;values] wavg[weights; values]};
{{ calculation_namespace }}.positiveRatio:{[values] avg values > 0};
{{ calculation_namespace }}.sumNotional:{[price;size] sum price * size};
{{ calculation_namespace }}.rowCount:{[rows] count rows};
{{ calculation_namespace }}.timeBucket:{[t;session;auction;bucket]
    labels:`$string bucket xbar t;
    labels[where (auction = `open) & session = `am]:`AMO;
    labels[where (auction = `close) & session = `am]:`AMC;
    labels[where (auction = `open) & session = `pm]:`PMO;
    labels[where (auction = `close) & session = `pm]:`PMC;
    labels
    };

{{ calculation_namespace }}.calcToxicityReversion:{
    refs: `sym xkey select from {{ ref_table }};
    rawVenueTrades: {{ venue_trades_table }} lj refs;
    rawPrimaryQuotes: {{ primary_quotes_table }} lj refs;

    venueTrades:
        select
            date,
            time,
            sym,
            session,
            auction,
            venue,
            trade_price,
            trade_size,
            notional: trade_price * trade_size,
            aggressor_side
        from rawVenueTrades
        where {{ date_filter }},
              {{ venue_filter }},
              {{ auction_filter }},
              trade_size > 0,
              not null aggressor_side;

    primaryQuotes:
        select
            date,
            time,
            quote_time: time,
            sym,
            bid_price,
            ask_price,
            primary_mid: (bid_price + ask_price) % 2
        from rawPrimaryQuotes
        where {{ date_filter }},
              venue = {{ primary_venue }},
              bid_price > 0,
              ask_price > bid_price;

    tradeWithPreMid: aj[`date`sym`time; venueTrades; primaryQuotes];

    tradeForHorizon:
        update
            horizon_time: time + {{ horizon }},
            primary_quote_age: time - quote_time
        from tradeWithPreMid;

    postQuotes:
        select
            date,
            horizon_time: time,
            post_quote_time: time,
            sym,
            post_mid: primary_mid
        from primaryQuotes;

    tradeWithPostMid: aj[`date`sym`horizon_time; tradeForHorizon; postQuotes];

    scored:
        update
            reversion_bps: aggressor_side * 10000 * (post_mid - primary_mid) % post_mid,
            horizon_sort_order: {{ horizon_sort_order }},
            valid_primary_quote: (primary_quote_age <= {{ max_primary_quote_age }}) &
                (horizon_time - post_quote_time) <= {{ max_primary_quote_age }}
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
          not null primary_mid,
          not null post_mid,
          post_mid > 0
    };

{{ calculation_namespace }}.calcToxicityReversion[]
