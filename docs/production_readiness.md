# Production readiness checklist

Use this checklist before adding richer sector-specific offline fixtures or
running live production validation. The deterministic offline and mock-kdb demos
prove report shape only; they do not confirm client taxonomy, live table names,
permissions, data freshness, or production schema compatibility.

## Decision gate

Do not treat a production report as ready until each item below has an owner,
an agreed source of truth, and a small bounded validation slice. The default
validation slice should be one known-good trading date and, where practical, one
liquid test symbol.

## kdb query and schema boundary

Before manually changing a q template for production, render a
`KdbMetricQueryPlanner` plan for the target metric, period, grouping, table
names, and metric parameters. Treat the plan as the source of truth for the
Python-facing kdb boundary.

| Requirement | Why it matters | Minimum evidence |
| --- | --- | --- |
| Source-table contract reviewed | Manual q edits can use client-specific table names, but required source columns must still be available before filtering, joining, or grouping. | `RenderedMetricQuery.input_contracts` reviewed against `meta table` or equivalent schema evidence. |
| Output schema preserved | The report path normalizes only after required output columns are present. | `RenderedMetricQuery.required_output_columns` match the columns returned by the final q select. |
| Optional diagnostics documented | Optional columns can improve report ranking/auditability but must not become hidden requirements. | `RenderedMetricQuery.optional_output_columns` reviewed; for reversion this currently includes `context_sort_order`. |
| Result validation run before report rendering | Schema mismatches should fail at the kdb boundary, not inside report components. | `RenderedMetricQuery.validate_result_schema(result)` or `KdbMetricRunner.run()` succeeds on a bounded slice. |
| Grouping semantics confirmed | Requested `group_by` columns become source-table requirements for starter activity/liquidity queries and output requirements for all templates. | One bounded validation slice for every production grouping used by the report. |

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

The table names can vary by deployment. The fields below are the minimum schema
contract required before live validation. Extra production columns are allowed.

### Trading calendar table

The calendar must come from a dedicated kdb+ data source. Weekday-only calendar
assumptions are not production ready.

| Required field | Purpose |
| --- | --- |
| `date` | Trading date used to select current and reference observations. |
| `is_trading_day` or equivalent | Excludes weekends, exchange holidays, and unscheduled closures. |
| Session metadata or equivalent | Confirms AM/PM sessions, lunch break, and auction boundaries used by bucket grids. |

### Trades table for `activity.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Intraday bucket assignment. |
| `sym` | Symbol-level and metadata joins. |
| `price` | Turnover and trade-value calculations. |
| `size` | Volume and turnover calculations. |

### Quotes table for `liquidity.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Intraday bucket assignment. |
| `sym` | Symbol-level and metadata joins. |
| `bid_price` | Quoted spread and top-of-book metrics. |
| `ask_price` | Quoted spread and top-of-book metrics. |
| `bid_size` | Top-of-book depth metrics. |
| `ask_size` | Top-of-book depth metrics. |

### Venue trade table for `toxicity_reversion.q`

| Required field | Purpose |
| --- | --- |
| `date` | Report-period filtering and reference comparison grouping. |
| `time` | Trade timestamp and horizon join anchor. |
| `sym` | Symbol-level and metadata joins. |
| `venue` | Cross-venue series grouping. |
| `trade_price` | Reversion denominator and execution anchor. |
| `trade_size` | Sample-size and notional diagnostics. |
| `aggressor_side` | Signed reversion direction; convention must be `buy=1`, `sell=-1`. |

### Primary quote table for `toxicity_reversion.q`

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
2. Confirm live table names and required fields with the market-data owner.
3. Run the default offline and mock-kdb test suite to confirm report shape.
4. Run environment-gated live smoke tests with one known-good trading date and
   optionally one liquid symbol.
5. Compare row counts, time buckets, group labels, and sample-size diagnostics
   against the market-data owner expectations.
6. Only then add richer production-specific offline fixtures or enable broader
   live validation.

## Not production-ready until

- The source calendar is a dedicated kdb+ calendar table.
- Trade and quote schemas have been validated against the required columns.
- Sector, segment, and market-cap taxonomy labels are confirmed and versioned.
- Symbol metadata joins are effective-dated or have an approved as-of rule.
- Live smoke tests pass on a bounded date/symbol slice.
- No credentials, client host names, or private market-data extracts are
  committed to the repository.
