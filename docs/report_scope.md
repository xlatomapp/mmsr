# Report scope guardrails

This package builds a **Japanese market microstructure market-monitoring
report**. It is not a transaction-cost analysis (TCA), execution-quality, smart order-routing, venue-ranking, or generic validation-framework package.

Use this page as the scope gate before choosing the next implementation step. Canonical path: `docs/report_scope.md`.

## Default report metric set

The default market report must stay focused on these metrics:

- `turnover`
- `volume`
- `trade_count`
- `quoted_spread_bps`
- `top_of_book_depth`
- `primary_quote_reversion_10ms_bps`
- `primary_quote_reversion_100ms_bps`
- `primary_quote_reversion_500ms_bps`
- `primary_quote_reversion_1s_bps`
- `primary_quote_reversion_5s_bps`
- `primary_quote_reversion_10s_bps`

The default report should explain market activity, displayed liquidity, and
cross-venue primary-quote reversion/toxicity across market-wide, intraday,
sector, segment, market-cap, venue, and symbol-level views.

## In-scope extensions

New work is in scope when it improves the market-monitoring report directly.
Examples include:

- better market-wide activity and liquidity summaries;
- better intraday profiles and auction-bucket handling;
- better sector, segment, market-cap, venue, and symbol drilldowns;
- clearer Cross-Venue Toxicity/Reversion visualization and commentary;
- volatility or market-quality metrics that describe market state rather than a
  specific execution outcome;
- deterministic commentary based on normalized comparison facts;
- kdb q templates needed by the default report metrics.

Optional market-microstructure add-ons may exist for future product design, but
they must not be enabled in `config/report.example.yaml` or
`config/report.production_minimal.yaml` unless the default metric set is
explicitly revised.

## Out of scope for the default report

Do not add report sections, default config entries, executive-summary language,
or roadmap next steps for:

- transaction-cost analysis;
- execution quality;
- effective spread;
- implementation shortfall;
- venue-ranking for order routing;
- fill-rate analysis;
- slippage;
- price impact as an execution-cost metric;
- broker/client order analytics;
- reusable validation frameworks that should sit above several reports.

Existing compatibility q templates for execution-cost-style metrics may remain
tested, but they are not default report features and should not drive report
design.

## Reversion convention

The Cross-Venue Toxicity section uses the `reversion` metric family. The
required reversion formula is:

```text
reversion_horizon_bps =
  aggressorSide * (future_primary_mid - primary_mid_at_trade) / future_primary_mid * 10000
```

where `aggressorSide` is `1` for buyer-initiated trades and `-1` for
seller-initiated trades. In the live kdb template, that side is inferred from the
prevailing same-venue/same-symbol quote for each trade, while the at-trade and
future mids used in the reversion value remain the configured primary venue
(TSE by default). The report should describe the sign convention explicitly near
the visual and should avoid relabeling this metric as price impact.

## Implementation gate

Before implementing a new metric, section, or utility, check these questions:

1. Does it support the default market-monitoring metric set or a clearly
   market-state-focused extension?
2. Will it appear in the market report as activity, liquidity, volatility,
   reversion/toxicity, intraday, taxonomy, venue, or symbol-level analysis?
3. Is it free of execution-cost/TCA framing unless the user has explicitly
   changed the product scope?
4. Is it report implementation rather than generic validation infrastructure?
5. Does the smallest next step improve the report itself before adding
   utilities around the report?

If any answer is no, record the ambiguity in `_docs/journal.md` and choose a
smaller market-report-focused step instead.
