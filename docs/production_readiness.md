# Production readiness checklist

Use this checklist before adding richer sector-specific offline fixtures or
running live production checks. The deterministic offline and mock-kdb demos
prove report shape only; they do not confirm client taxonomy, live raw-data
functions, permissions, data freshness, or production schema compatibility.

Validation utilities inside `mmsr` should remain small and report-specific. A
common validation framework should be designed later, above this package, after
several reports expose repeated source, calendar, entitlement, and freshness
checks.

## Decision gate

Do not treat a production report as ready until each item below has an owner,
an agreed source of truth, and a small bounded validation slice. The default
validation slice should be one known-good trading date and, where practical, one
liquid test symbol.

Before a full `mmsr render` run, prefer
`config/report.production_minimal.yaml` for the first live-kdb attempt because it
contains only the default market-monitoring metrics for this report: activity,
displayed liquidity, and cross-venue primary-quote reversion. Execute
`mmsr plan` against the same config and kdb endpoint when operators need a
no-metric-IO review of target/reference trading days, metric count, symbol chunk
count, and source-function contracts. `mmsr preflight` remains an optional
bounded sample check; do not expand it into a general validation framework inside
this report package. A full render executes both the target period and the
`reference.lookback_days` trading-day window through the same daily/chunk
executor before building current-vs-reference comparison facts. Transaction-cost
metrics such as effective spread and price impact are intentionally not part of
the default market report.

## Report scope gate

Before adding a production checklist item, q template, config metric, or report
section, review [report scope guardrails](report_scope.md) (`docs/report_scope.md`).
The default package output is a market-monitoring report. transaction-cost analysis, execution quality, implementation shortfall,
slippage, price impact, smart-order-routing, and venue-ranking features are out
of scope for default production readiness. generic validation and reusable
validation frameworks should also remain outside this package until
several reports expose repeated validation needs.


## kdb query and schema boundary

Before manually changing a q template for production, render a
`KdbMetricQueryPlanner` plan for the target metric, period, grouping, raw-data
source functions, calculation namespace, and metric parameters. Treat the plan
as the source of truth for the Python-facing kdb boundary. Production plans
should call user-owned functions with MMSR's fixed positional arguments, such as
`.sb.mmsr.getTrade[date;syms]`, `.sb.mmsr.getQuote[date;syms]`,
`.sb.mmsr.getRef[date;syms]`, `.sb.mmsr.getSymbols[date]`, and
`.sb.mmsr.getTradingCalendar[start;end]`; those functions may internally query
physical tables, cleanse rows, route between HDB/RDB, or map client taxonomy.
Production configs should not hard-code static session times. Trade and quote
rows must carry per-tick `session` and `auction` columns so MMSR can derive
continuous intraday buckets and auction buckets inside kdb.

| Requirement | Why it matters | Minimum evidence |
| --- | --- | --- |
| Raw source-function contract reviewed | User-owned source functions can use client-specific table names internally, but required canonical columns must still be returned before MMSR filtering, joining, or grouping. The default report requires activity, displayed-liquidity, and primary-quote reversion fields. Trade and quote rows must include `session` and `auction`; reversion trades require `aggressor_side` with buy=1 and sell=-1. | `RenderedMetricQuery.input_contracts` reviewed against `meta .sb.mmsr.getTrade[date;syms]`, `meta .sb.mmsr.getQuote[date;syms]`, or equivalent schema evidence. |
| Symbol-universe function confirmed | Operators should control the report universe without editing MMSR code or raw source functions. | Configured `.sb.mmsr.getSymbols[date]` returns the intended liquid/security universe for each target and reference trading day. | 
| Reference-data function confirmed | TOPIX bucket, market-cap group, lot size, and any configured grouping taxonomy should come from a user-owned source of truth. | Configured `.sb.mmsr.getRef[date;syms]` returns `date`, `sym`, `topix_bucket`, `market_cap_bucket`, `lot_size`, and any additional configured grouping columns. |
| Daily execution scope confirmed | Full-market target and reference periods must not request multi-day raw trade/quote windows. | `KdbProductionExecutor` or `KdbProductionExecutionPlanner` shows one `MetricRunRequest` per trading day for both `run()` and `run_reference()`; each raw request is scoped to one `date` and one `syms` vector. |
| Plan summary reviewed | Operators should know live run scope before metric q calls are made. | `mmsr plan` or `KdbProductionExecutor.build_plan_summary()` reports target/reference trading days, metric count, symbol chunk count, total metric steps, calculation namespace, symbol-universe function, source functions, and schema contracts. |
| Reference lookback confirmed | Reference comparisons need a calendar-derived trading-day window, not a weekday or raw calendar-day approximation. | `KdbProductionReferenceWindow.trading_days` contains the previous `reference.lookback_days` available trading days and `MetricComparison.reference_sample_size` reflects daily reference observation units. |
| Symbol chunking policy confirmed | Some one-day full-market slices may still be too large without client-side or server-side partitioning. | Configured `kdb.symbol_chunk_size` splits the `syms` vector returned by the symbol-universe function before raw source calls. |
| Output schema preserved | The report path normalizes only after required output columns are present. | `RenderedMetricQuery.required_output_columns` match the columns returned by the final q select. |
| Optional diagnostics documented | Optional columns can improve report ranking/auditability but must not become hidden requirements. | `RenderedMetricQuery.optional_output_columns` reviewed; for reversion this currently includes `context_sort_order`. |
| Result validation run before report rendering | Schema mismatches should fail at the kdb boundary, not inside report components. | `RenderedMetricQuery.validate_result_schema(result)` or `KdbMetricRunner.run()` succeeds on a bounded slice. |
| Grouping semantics confirmed | Requested `group_by` columns become raw source-function result requirements for starter activity/liquidity queries and output requirements for all templates. | One bounded validation slice for every production grouping used by the report. |

## Sector, segment, and market-cap taxonomy

Confirm the client taxonomy before encoding richer drilldown fixtures or
production-specific defaults. The market-cap bucket rule must be explicit and
versioned.

| Requirement | Why it matters | Minimum evidence |
| --- | --- | --- |
| Canonical sector taxonomy name and version | Sector labels can differ across TOPIX, exchange, broker, and client-specific classifications. | Taxonomy owner, version/date, and allowed sector labels. |
| Segment field and allowed values | `market_segment` and `segment` are both supported normalized group keys, but production must choose the source mapping. | Confirmed field name and allowed values such as Prime, Standard, Growth, ETF, REIT, or client-specific alternatives. |
| Market-cap bucket definition | Large/mid/small labels are not meaningful without thresholds and effective dates. | Thresholds, currency, calculation date, rebalance cadence, and null/unknown handling. |
| Symbol identifier convention | Drilldowns must not collide with symbol anomaly pages or client-specific identifiers. | Confirmed primary identifier such as `sym`, `symbol`, `ticker`, `security_code`, `issue_code`, or `local_code`. |
| Effective-dated mapping behavior | Sector and market-cap mappings can change through reclassification, IPOs, delistings, and corporate actions. | Mapping table with valid-from/valid-to fields or an equivalent as-of-date rule. |
| Unknown and suspended instruments | Production reports need deterministic labels instead of dropping rows silently. | Rules for unknown sector, unknown segment, halted/suspended issues, ETFs, REITs, and preferred shares. |
| Group-key normalization | Report options are configurable, but normalized comparison facts need stable group keys. | Mapping from production field names into normalized keys such as `sector`, `segment`, and `market_cap_bucket`. |

## Required kdb+ source fields

The function names can vary by deployment. The fields below are the minimum
schema contract required before live validation. Extra production columns are allowed.

### Trading calendar function

The calendar must come from a dedicated user-owned kdb+ function. Weekday-only
calendar assumptions are not production ready.

| Required function contract | Purpose |
| --- | --- |
| `.sb.mmsr.getTradingCalendar[start;end]` or configured equivalent | Returns a date vector or table/dict with `date` rows for trading days between `start` and `end`, inclusive. |
| Session metadata or equivalent, if used upstream | Confirms AM/PM sessions, lunch break, and auction boundaries used by bucket grids. |

### Trade raw-data function for `activity.q` and optional `flow.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Intraday bucket assignment. |
| `sym` | Symbol-level and metadata joins. |
| `trade_price` | Turnover and optional signed-turnover calculations. |
| `trade_size` | Volume, turnover, and optional imbalance calculations. |
| `aggressor_side` | Required only for `signed_turnover` and `trade_imbalance` / `flow.q`; convention must be `buy=1`, `sell=-1`. |

### Quote raw-data function for `liquidity.q` and optional liquidity/volatility add-ons

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Intraday bucket assignment and quote-return ordering. |
| `sym` | Symbol-level and metadata joins; required for optional `realized_volatility.q` so adjacent mid-price returns are calculated within each symbol. |
| `bid_price` | Quoted spread, top-of-book, primary-mid reversion, and optional quote-mid realized-volatility metrics. |
| `ask_price` | Quoted spread, top-of-book, primary-mid reversion, and optional quote-mid realized-volatility metrics. |
| `bid_size` | Top-of-book depth metrics. |
| `ask_size` | Top-of-book depth metrics. |
| `tick_size` | Required only for `quoted_spread_ticks` / `liquidity_ticks.q`; may be supplied by a symbol-metadata or tick-ladder join inside the user quote function. |

### Venue trade raw-data function for `toxicity_reversion.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Trade timestamp and horizon join anchor. |
| `sym` | Symbol-level and metadata joins. |
| `venue` | Cross-venue series grouping. |
| `trade_price` | Reversion denominator and execution anchor. |
| `trade_size` | Sample-size and notional diagnostics. |
| `aggressor_side` | Signed reversion direction; convention must be `buy=1`, `sell=-1`; reversion uses `aggressor_side * (future_mid - mid_at_trade) / future_mid * 10000`. |

### Primary quote raw-data function for `toxicity_reversion.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Quote timestamp used before and after the trade horizon. |
| `sym` | Symbol-level and metadata joins. |
| `venue` | Primary-quote venue confirmation, normally TSE unless configured otherwise. |
| `bid_price` | Primary mid-price calculation. |
| `ask_price` | Primary mid-price calculation; rows should satisfy `ask_price > bid_price`. |

### Symbol metadata / taxonomy table

The richer sector drilldowns require an effective-dated metadata source that can
be joined to normalized metric rows before comparison facts are built.

| Required field | Purpose |
| --- | --- |
| Symbol identifier | Must map to the configured production identifier such as `sym` or `security_code`. |
| Effective date or validity range | Supports as-of joins for historical comparisons. |
| Sector | Populates normalized `sector` group keys. |
| Segment | Populates normalized `segment` or `market_segment` group keys. |
| Market-cap bucket or source market cap | Populates `market_cap_bucket` after the agreed threshold rule. |
| Optional display name | Improves human-readable report labels without changing metric keys. |

## Validation sequence

1. Confirm taxonomy ownership, labels, effective-date behavior, and null handling.
2. Confirm live function names, positional arguments, and required fields with the market-data owner.
3. Run the default offline and mock-kdb test suite to confirm report shape.
4. Run `mmsr plan` and, when useful, one bounded `mmsr preflight --metric`
   check with one known-good trading date and optionally one liquid symbol.
5. Compare row counts, time buckets, group labels, and sample-size diagnostics
   against the market-data owner expectations.
6. Only then add richer production-specific offline fixtures or move repeated
   validation requirements into a shared framework above report packages.

## Not production-ready until

- The source calendar is a dedicated user-owned kdb+ calendar function.
- Trade and quote schemas have been validated against the required columns.
- Sector, segment, and market-cap taxonomy labels are confirmed and versioned.
- Symbol metadata joins are effective-dated or have an approved as-of rule.
- The minimal production config has been reviewed against the configured raw
  source functions for activity, displayed liquidity, and cross-venue
  primary-quote reversion. Optional add-ons such as tick-normalized spread,
  quote-mid realized volatility, or feed-signed order-flow imbalance should be
  enabled only after the required extra source fields are confirmed.
- No credentials, client host names, or private market-data extracts are
  committed to the repository.
