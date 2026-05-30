# ROADMAP.md

This roadmap defines the implementation milestones for `mmsr`.

## Product goal

Create a Python package that generates market microstructure monitoring reports for Japanese market data using level 1 trade and quote data stored in kdb+. The package should run deterministically without an LLM and optionally support LLM-polished commentary.

## Implementation scope gate

Every future roadmap item must pass the scope guardrails in
`docs/report_scope.md` before implementation. The default product is a Japanese
market microstructure market-monitoring report, not transaction-cost analysis
(TCA), execution quality, smart-order routing, venue ranking, or a generic
validation framework / generic validation package.

Roadmap work should prioritize:

- market-wide, intraday, sector, segment, market-cap, venue, and symbol-level
  report views;
- activity, displayed liquidity, market-state volatility/quality, and
  Cross-Venue Toxicity/Reversion;
- deterministic commentary from normalized comparison facts;
- kdb q templates and report components needed by the default market report.

Do not add roadmap next steps for effective spread, implementation shortfall,
slippage, price impact, order-routing analytics, or reusable validation
frameworks unless the user explicitly changes the product scope. Existing
execution-cost-style compatibility templates may remain tested but must not be
promoted into default configs or report sections.

## Current roadmap reset: desk-first report, slimmer code, faster q

This section is the active near-term roadmap after the 2026-05-30 repo review.
It combines the product report direction with the codebase slimming and kdb
performance direction. Historical milestones below remain useful background, but
new implementation should follow this ordered sequence.

### Milestone R0: Slim and stabilize the default product surface

**Goal:** Make the default package smaller and clearly desk-monitoring-first
before adding more report features.

**Required changes:**

- Remove redundant q wrappers that only rename native q functions. Examples:
  wrappers around `sum`, `count`, `med`, or `wavg` should be deleted unless they
  add explicit null handling, validation, or report-specific policy.
- Prefer one production execution path: the installed q `runReportDay` path.
  Keep older single-metric or chunk-batch paths only where tests or explicit
  compatibility need them; otherwise mark them for removal.
- Remove symbol-level analysis from default production output. Symbol rows and
  symbol pages should be opt-in escalation tools, not the default report shape.
- Change default production aggregation levels to market and TPX cap group
  rollups first: `market`, `market_bucket`, `topix_cap_group`, and
  `topix_cap_group_bucket`. `symbol` and `symbol_bucket` should be opt-in.
- Separate demo acceptance fixtures from product defaults so synthetic
  symbol-heavy fixtures do not drive the default desk report shape.
- Clean stale docs and comments that imply removed optional metric families or
  legacy execution paths are still active roadmap priorities.

**Exit criteria:**

- Default production config does not request symbol or symbol-bucket rollups.
- Default market report options do not emit symbol anomaly/detail pages.
- q calculation helpers are only kept when they provide real policy or reuse.
- Tests assert default report pages and default aggregation levels remain
  market/group-first.

### Milestone R1: q metric calculation performance pass

**Goal:** Reduce kdb runtime and memory pressure for regular full-market
reports.

**Required changes:**

- Profile q execution by stage: reference load, raw source load, metric
  calculation, rollup, cache read/write, and result serialization.
- Keep source loading once per day/chunk and avoid repeated trade/quote loads
  across metrics in the same family.
- Ensure cross-venue reversion prepares joined trade/quote state once per
  metric family, then evaluates horizons from that prepared state.
- Avoid broad `raze` of large intermediate chunk tables where earlier q-side
  grouped rollup can reduce row counts before concatenation.
- Apply attributes such as `p#` only where they measurably help `aj` paths and
  after sort keys match the join keys.
- Return aggregated report facts to Python; raw or near-raw rows should never
  cross the Python boundary.
- Add timing logs that identify slow stages without logging sensitive source
  rows.

**Exit criteria:**

- One production day run can report per-stage q timings.
- Activity, liquidity, and reversion families load each required raw source at
  most once per day/chunk.
- Reversion horizons reuse prepared joins rather than repeating the full
  preparation per horizon.
- Tests or deterministic q-render assertions guard against reintroducing
  redundant native-function wrappers and repeated family preparation.

### Milestone R2: Market summary that tells the story

**Goal:** Make the first page useful for a trading desk review: what changed,
where it changed, when it changed, and why it matters.

**Required changes:**

- Replace the top-page emphasis on metric cards and broad comparison tables with
  a concise deterministic market narrative.
- Surface the top three to five market-level changes across activity,
  displayed liquidity, and cross-venue reversion.
- Include the leading TPX cap group, intraday bucket/session, and venue/horizon
  context when those dimensions explain the change.
- Keep metric cards and comparison tables as compact audit/detail components,
  not the primary story.
- Use deterministic wording from computed comparison facts only; LLM polishing
  remains optional and explicitly enabled.

**Exit criteria:**

- The first report page leads with narrative highlights before any broad table.
- Highlights are sourced only from normalized comparisons and metric metadata.
- Tests cover ranking, wording, and absence of symbol-level highlights in the
  default summary unless symbol mode is explicitly enabled.

### Milestone R3: Drilldowns around market questions

**Goal:** Make drilldowns explain market structure changes rather than listing
rows.

**Required changes:**

- Add a dedicated TPX cap group drilldown page before generic diagnostic tables.
- For activity metrics, show current cumulative intraday distribution versus
  reference distribution by TPX cap group.
- For displayed liquidity metrics, show intraday profile shifts and largest
  group deltas by TPX cap group, segment, or sector when configured.
- For reversion metrics, keep venue/horizon curves focused on adverse
  primary-quote movement and low-confidence sample flags.
- Keep symbol drilldown as an opt-in escalation from the most severe grouped
  changes.

**Exit criteria:**

- Default page order is market summary, activity distribution, displayed
  liquidity, cross-venue toxicity, TPX/group drilldowns, intraday diagnostics,
  and appendix.
- Drilldown pages use visuals first and capped tables only as supporting audit
  detail.
- Symbol pages are absent by default and appear only through explicit config or
  CLI options.

### Milestone R4: Generic q-side aggregation contract

**Goal:** Replace hard-coded group rollups with a reusable market/group/symbol
aggregation contract.

**Required changes:**

- Standardize report fact dimensions as `date`, `time_bucket`,
  `aggregationLevel`, `groupType`, and `groupValue`, plus metric columns and
  optional metadata such as `venue`, `horizon`, `trade_count`, and `notional`.
- Generalize q rollups beyond `topixCapGrp` so configured reference-data
  columns such as TPX cap group, sector, and segment use the same aggregation
  machinery.
- Treat symbol aggregation as one optional aggregation level, not a separate
  default product path.
- Keep Python report selection based on normalized fact dimensions rather than
  hard-coded source column names where practical.

**Exit criteria:**

- q can produce market, bucket, TPX cap group, sector, segment, and optional
  symbol facts through one aggregation-level mechanism.
- Output schema tests cover generic `groupType`/`groupValue` rows.
- Existing report pages consume the standardized fact contract without needing
  special cases for each taxonomy column.

### Milestone R5: stockMetrics cache as a first-class performance feature

**Goal:** Make repeated report generation fast without making MMSR own user
storage.

**Required changes:**

- Add config for user-owned q cache functions such as `loadStockMetrics` and
  `persistStockMetrics`, or an equivalent explicitly named client boundary.
- Cache aggregated metric facts, not raw trade or quote rows.
- Load one day of wide `stockMetrics` rows once for all requested metrics.
- Compute only missing metric columns and persist the newly computed wide rows
  once after q validation.
- Document the ownership split: the user owns table storage and upsert
  semantics; MMSR owns the canonical row shape and hydration/persist calls.

**Exit criteria:**

- A production run can hydrate cached metric facts before raw source loading.
- Partial cache hits compute only missing metric columns.
- A documented q example shows the expected loader/persister signatures and
  canonical row shape.
- Tests cover full hit, partial hit, miss, and persist behavior.

### Milestone R6: Real kdb production validation and report budgets

**Goal:** Validate the desk report against real production-shaped kdb data and
lock in practical runtime and HTML-size budgets.

**Required changes:**

- Run one real kdb-backed report for one target day and the configured reference
  window using activity, displayed liquidity, and reversion metrics.
- Record runtime by q stage, returned row counts by aggregation level, final HTML
  size, chart count, and report review usability notes.
- Set default caps for charts, drilldown rows, optional symbol pages, and final
  report size from observed production data.
- Add fixture-scale regression tests that preserve the chosen budgets.

**Exit criteria:**

- A real-kdb smoke report validates the q source-function boundary, cache path
  if enabled, report rendering, and compact visual defaults.
- Budget tests prevent unbounded table/chart growth in default reports.
- Remaining live-only risks are documented with concrete dates, configs, and
  observed runtime numbers.

### Milestone R7: Market-first default shape lock

**Goal:** Make the default report behavior unambiguous and regression-proof for
desk-first market monitoring.

**Required changes:**

- Add explicit tests that default report output stays market/group-first even
  when symbol-scoped comparison rows exist.
- Keep symbol anomaly/detail pages opt-in by config only.
- Verify default page ordering remains stable and market-first.
- Tighten report-option/help text to avoid wording that implies symbol-first
  default behavior.

**Exit criteria:**

- Regression tests prove symbol rows do not trigger symbol pages by default.
- Default page set/order tests are explicit and passing.
- Docs/help wording consistently describes symbol pages as optional escalation.

### Milestone R8: Visible summary storytelling polish

**Goal:** Improve first-page readability so desk users can identify key changes
quickly without table scanning.

**Required changes:**

- Add visible executive-summary hierarchy improvements (highlight container,
  spacing, status emphasis).
- Improve comparison-status readability with compact visual markers/chips.
- Add HTML-level regression checks for summary-storytelling UI elements.
- Keep data semantics unchanged; this is presentation-only.

**Exit criteria:**

- Market Summary visibly separates narrative highlights from detail sections.
- Status presentation is visually scannable in the default table.
- Rendering tests confirm expected summary UI structure/classes.

**Recommended first implementation PR:**

1. Remove no-op q wrappers around native q functions.
2. Remove `symbol` and `symbol_bucket` from default production aggregation
   levels.
3. Disable symbol anomaly/detail pages by default.
4. Add q timing instrumentation inside `runReportDay`.
5. Add tests that lock the new default report shape and aggregation defaults.


## Milestone 1: Project skeleton and governance

**Goal:** Establish ppw-style package structure, governance docs, roadmap, journal, and minimal test setup.

**Exit criteria:**

- ppw-style repository structure exists.
- `_docs/AGENTS.md` exists.
- `_docs/ROADMAP.md` exists.
- `_docs/journal.md` exists and records initial state.
- Basic package import works.
- Basic test command works.

**Estimated status in this skeleton:** 70%

**Remaining after skeleton review:**

- Confirm final package name.
- Confirm preferred renderer stack.
- Confirm production kdb table schemas.

## Milestone 2: Domain models

**Goal:** Implement typed domain models that define periods, sessions, intraday buckets, metrics, and metric results.

**Core objects:**

- `ReportPeriod`
- `TradingSession`
- `IntradayBucketSpec`
- `TimeBucket`
- `AuctionBucketLabels`
- `MetricDefinition`
- `MetricTimeSeries`
- `MetricComparison`
- `CommentaryFact`

**Exit criteria:**

- Models validate bucket sizes such as `1m`, `5m`, `30m`.
- A utility can build an intraday bucket grid with auction rows such as `AMO`, `AMC`, `PMO`, `PMC`.
- Bucket grid rows include numeric `sort_order` so labels are always rendered in trading sequence.
- Session breaks are represented explicitly.
- Metric definitions can produce help text.
- Tests cover model construction and validation.

## Milestone 3: Metric registry and starter metric definitions

**Goal:** Implement central registry and first set of metric definitions.

**Default market-monitoring metrics:**

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

**Optional market-microstructure add-ons, not enabled by default:**


Transaction-cost metrics are out of scope for the market-monitoring
report. The production runner and q library should not carry transaction-cost
calculation paths unless the product scope explicitly changes.

**Exit criteria:**

- Metrics are registered at import or through an explicit registry builder.
- Each metric has formula, interpretation, caveats, and required columns.
- Tests verify lookup, docs generation, and uniqueness.

## Milestone 4: kdb/PyKX infrastructure

**Goal:** Implement kdb client abstraction, q template loading/rendering, and kdb-backed trading calendar function access.

**Exit criteria:**

- PyKX import is lazy.
- `KdbClient` can be instantiated from config.
- Query templates can be loaded from package resources.
- Query rendering validates required parameters.
- Trading calendar data is read from a dedicated user-owned kdb calendar function rather than weekday assumptions.
- Offline tests do not require live kdb.

## Milestone 5: Metric execution interface

**Goal:** Implement a kdb metric runner that executes registered metric templates over report periods and grouping dimensions.

**Exit criteria:**

- Metric runner accepts `MetricDefinition`, period, bucket spec, and group-by list.
- Runner returns a normalized time-series result schema.
- Initial q templates exist for activity and quoted spread metrics.
- Integration tests can be marked/skipped without kdb connection.

**Implemented hardening:**

- `KdbMetricQueryPlanner` now isolates q rendering from execution and returns a
  `RenderedMetricQuery` before any IO occurs.
- Each rendered plan exposes required raw-source contracts, required output
  columns, and supported optional output columns so production users can provide
  client-specific q functions while preserving the Python report boundary.
- Production plans can call user-defined raw-data functions such as
  `.sb.mmsr.getTrade[date;syms]` and `.sb.mmsr.getQuote[date;syms]` instead of
  querying physical trade/quote tables directly. Production planning can also
  call user-owned calendar, reference-data universe, and reference-data functions such as
  `.sb.mmsr.getTradingCalendar`, `.sb.mmsr.getRef[date]`, and
  `.sb.mmsr.getRef[date;syms]` so operators control trading days, the analysis
  universe, TOPIX/cap/lot-size reference data, and taxonomy outside MMSR code.
  Trade and quote source rows carry per-tick `session`/`auction` state instead
  of relying on static configured session times. The rendered q installs MMSR
  calculations into the configured namespace, for example `.desk.mmsr`, rather
  than calculating in the global namespace.
- `KdbMetricRunner.run()` uses the same query plan internally and validates the
  kdb result schema before normalizing to `MetricTimeSeries`.
- Activity, liquidity, and reversion templates share the same centralized
  output-schema dispatcher, keeping tests, manual query plans, and runner
  validation aligned.


## Milestone 5A: Cross-venue toxicity reversion metrics

**Goal:** Implement primary-quote reversion metrics for aggressive trades across venues such as TSE, SBIJ, and ODX.

**Metric family:**

- Section name: `Cross-Venue Toxicity`.
- Metric label convention: `+10ms Reversion`, `+100ms Reversion`, `+500ms Reversion`, `+1s Reversion`, `+5s Reversion`, `+10s Reversion`.
- Benchmark quote: primary exchange quote, default `TSE`.
- Formula: `side * 10000 * (primary_mid[t + horizon] - primary_mid[t-]) / primary_mid[t + horizon]`.
- Positive value: primary mid moved in the aggressive trade direction, indicating greater adverse selection/toxicity.
- Negative value: primary mid moved against the aggressive trade direction, indicating reversion.

**Required report visual:**

- Venue reversion curve.
- X-axis: horizon progression, for example `10ms`, `100ms`, `500ms`, `1s`, `5s`, `10s`.
- Y-axis: reversion in bps.
- Series: venue, for example `TSE`, `SBIJ`, `ODX`.
- Purpose: observe when impact starts, how quickly it develops, whether it reverts, and the magnitude by venue.

**Implemented production report behavior:**

- `build_toxicity_reversion_page()` consumes normalized kdb-backed
  `MetricTimeSeries` rows for `primary_quote_reversion_*_bps` metrics.
- The canonical `build_market_monitor_report()` inserts the `Cross-Venue
  Toxicity` page when those rows are present and keeps it opt-out through
  `MarketReportOptions.include_toxicity_reversion_page`.
- The visual uses the standard deterministic SVG time-series component with
  horizon on the x-axis, reversion bps on the y-axis, and one line per venue.
- Metric help, chart help, low-confidence sample-size caveats, and deterministic
  template commentary are included without report-layer metric calculation.
- Multi-context reports rank toxicity curves deterministically before applying
  chart limits. The default ranking surfaces largest positive reversion first,
  with optional absolute-move, low-confidence, upstream `context_sort_order`, and chronological ordering modes.
- When the dedicated page is present, the canonical report suppresses
  `primary_quote_reversion_*_bps` rows from the generic `Intraday Detail` page
  by default to avoid duplicate visuals. Callers can opt into both displays with
  `MarketReportOptions.include_toxicity_reversion_metrics_in_detail_page=True`.


**Exit criteria:**

- Metric definitions exist for each configured horizon.
- q template exists for primary-quote reversion calculation.
- Config supports venues, primary venue, horizons, side source, clustering, stale quote filters, and sample-size confidence thresholds.
- Production report visual renders deterministic venue reversion curves from normalized kdb-backed metric output.
- Production report visual ranks many date/bucket/group contexts deterministically before applying chart limits, including an optional upstream `context_sort_order` metadata hook.
- Dedicated toxicity visuals are not duplicated in the generic Intraday Detail page unless callers opt in.
- Tests verify metric registration and basic visual rendering.
- Terminology uses `reversion` consistently in user-facing docs, metric labels, and report output.



### Milestone 5 architecture correction — kdb-owned report-day execution

Production kdb execution must use one installed q entry point per trading day.
Python must not fetch, enumerate, or chunk the production symbol universe. Python
may pass explicit user-requested universe filters, metric names, metric
parameters, aggregation levels, source function handles, and chunk size. The
installed q library must own reference-data loading, universe filtering, symbol
discovery, symbol chunking, raw source loading, metric dispatch, and rollup.

Exit criteria for this correction:

- Runtime report rendering calls `runReportDay[runDate; reportConfig]`.
- Rendered production q does not contain Python-built chunk loops or metric
  lambdas such as `{[rawSources] ...}`.
- Rendered production q does not log or expose old q template filenames as the
  runtime execution concept; operator logs use metric family names instead.
- Full production symbol lists are never fetched from kdb into Python for
  planning or chunking.
- Tests cover q-owned symbol discovery/chunking and installed metric dispatch.


## Milestone 6: Reference comparison engine

**Goal:** Compare current metric time series against comparable reference windows without overstating statistical confidence.

**Supported methods:**

- Previous day.
- Trailing N trading days.
- Same intraday bucket trailing median.
- Same weekday trailing window.
- Configured reference observation units such as `trading_day`, `trading_week`, `session`, or `event_cluster`.

**Comparison policy:**

- Default observation unit: `trading_day`.
- Default comparable keys: `metric_name`, `time_bucket`, and report group columns.
- One reference observation: current-vs-reference change only, no z-score.
- Fewer than 30 comparable reference observations: empirical rank/range position with low-confidence flag.
- At least 30 comparable reference observations: robust z-score, standard z-score, empirical percentile, and normal-score percentile are available when dispersion is non-zero.
- Z-score-to-probability conversion must be labelled as `normal-score percentile` or `normal approximation tail probability`.

**Exit criteria:**

- Output includes value, reference value, absolute change, percentage change, reference sample size, comparison confidence, percentile/range-position fields, optional z-score, and status.
- Z-scores are calculated from comparable historical aggregated observations, such as the same metric, group, and intraday bucket over a trailing window.
- Robust z-score using median/MAD and empirical percentile rank are preferred defaults for skewed metrics such as quoted spread.
- Standard mean/std z-score remains available when appropriate.
- Tests cover edge cases: one-observation reference, short reference windows, zero reference, missing values, insufficient history, zero dispersion, direction-aware adverse tails, and robust-vs-standard behavior.

## Milestone 7: Deterministic commentary engine

**Goal:** Generate commentary from structured comparison facts without using LLMs.

**Exit criteria:**

- Rule engine detects alerts, watch items, and normal conditions.
- Template commentary is generated per page/section.
- Commentary is grounded only in computed facts.
- Tests cover severity thresholds and output text.

## Milestone 8: Report components and metric help

**Goal:** Implement report components that expose metric definitions next to values and visuals.

**Initial components:**

- Metric card.
- Metric table.
- Time-series chart placeholder.
- Heatmap placeholder.
- Commentary block.
- Metric definitions appendix.

**Exit criteria:**

- HTML renderer includes info/help icons or expandable metric docs.
- Excel/static renderers can include a metric definitions sheet or appendix placeholder.
- Tests verify metric help is included.

## Milestone 9: End-to-end mock-data demo

**Goal:** Build a demo report from synthetic/mock fixture data without live kdb.

The demo must not own a separate report format. It should use deterministic mock
data to exercise the same report builder, page order, Jinja template, component
partials, and metric-help behavior intended for production kdb-backed reports.

**Exit criteria:**

- Example config or CLI command runs locally.
- Synthetic metric results flow through comparison, commentary, and HTML report rendering.
- Demo data is adapted into the canonical production-format report input.
- README includes quickstart.

## Milestone 9A: Production-format report polish before kdb integration

**Goal:** Make the production report format readable, visual, and decision-oriented
before wiring it to a live or mock kdb connection.

**Required direction from user feedback:**

- There must be one canonical report builder and one true default HTML report
  template. Demo and production may use different data sources, but not different
  layouts.
- The mock-data demo is a format acceptance harness, not a separate example for
  arbitrary customization.
- Time-series data should render as real charts, such as daily line plots across
  reference and target periods, while preserving accessible tabular backing data.
- Dense intraday bucket grids should default to bucket-on-x-axis line charts;
  heatmaps should remain an explicit opt-in when matrix diagnostics are wanted.
- Deterministic commentary must use human-friendly labels such as "opening
  auction" and "daily observation" instead of internal labels such as
  `time_bucket=AMO` or `unit=trading_day`.
- The top report section should focus on high-level market trend and status
  across key metrics. Per-bucket alerts should remain available but move into
  diagnostic sections.
- Metric/help controls must be interactive and accessible. Inert info-icon
  buttons with title-only text are not sufficient; use deterministic
  expandable/popover-style HTML that works without JavaScript where practical.

**Exit criteria:**

- Canonical production-format report builder exists and the mock-data demo
  delegates to it.
- Roadmap/status docs state that demo and production share the same template and
  report assembly path.
- Time-series trend visuals render as real chart components rather than
  placeholder-only tables, including daily reference-to-target plots.
- Intraday diagnostics render dense time-bucket line charts by default, with
  heatmaps preserved as an explicit opt-in rather than the default view.
- Deterministic commentary uses display labels for metrics, buckets, groups,
  and observation units.
- Executive market overview section summarizes high-level market trends before
  per-bucket diagnostics.
- Metric cards, tables, charts, heatmaps, and trusted HTML blocks expose working
  accessible metric/help controls.
- Tests prove mock-data reports and production-format reports use the same
  builder/template path.

## Milestone 9B: production kdb source-function boundary

**Goal:** Make the live production data boundary function-based and bounded, so
users define raw trade/quote access while MMSR owns metric q calculations.

**Direction from user feedback:**

- Do not require direct table queries such as `trade` or `quote` for production
  report logic.
- User-defined raw functions, for example `.sb.mmsr.getTrade` and
  `.sb.mmsr.getQuote`, should provide canonical raw rows and may internally
  handle cleansing, symbol routing, HDB/RDB dispatch, and permissions.
- MMSR-owned calculation q should be pushed into kdb under a configured
  namespace and should not write intermediate calculations into the global
  namespace.
- Production orchestration must be date/chunk bounded. A full-market reference
  period must not request multi-day raw trade/quote data at once.
- After iteration 61 user feedback, stop expanding report-local validation
  utilities. Keep `mmsr plan` and `mmsr preflight` as optional operator helpers;
  future reusable validation should be designed above `mmsr` after multiple
  reports exist.
- Prioritize report implementation and runnable metric coverage over additional
  validation harnesses.

**Current implementation status:**

- `ReportConfig` exposes kdb namespace, user raw-data functions, daily-scope
  enforcement, and optional symbol chunk sizing.
- `KdbMetricQueryPlanner` renders raw source-function calls and installs MMSR
  calculation functions inside the configured q namespace.
- `KdbProductionExecutionPlanner` builds one-day `MetricRunRequest` objects from
  the trading calendar and optional symbol chunks.
- `KdbProductionExecutor` executes those bounded requests through
  `KdbMetricRunner` and combines normalized observations by metric.
- `mmsr render` is the production CLI entrypoint. It loads YAML config, connects
  through the PyKX-backed client, uses the kdb-backed trading calendar, executes
  bounded target and reference runs, builds current-vs-reference comparisons,
  and renders the canonical HTML report.
- `mmsr plan` summarizes the production render scope without metric q
  execution: target/reference trading days, metric count, symbol chunk count,
  total metric steps, calculation namespace, source functions, and q-template
  schema contracts.
- `mmsr preflight` validates the same production config and kdb endpoint before
  a full render by checking the configured q names, querying the calendar,
  planning one bounded metric step, executing that one step, and validating its
  result schema. Operators can pass `--metric` to validate one configured
  activity, liquidity, or reversion metric family at a time.
- `config/report.production_minimal.yaml` provides a first live-kdb config scoped
  to the default market-monitoring metrics only: activity, displayed liquidity,
  and cross-venue primary-quote reversion.
- Optional market-microstructure add-ons have checked-in q-template support but
  are intentionally not enabled in the minimal/default report config:
  The production q runner supports only the default activity, displayed-liquidity, and reversion families.
- Transaction-cost calculation paths are not part of the production runner or
  reusable q library. Future work should focus on market structure, liquidity,
  activity, volatility, and reversion unless the report scope explicitly expands.

**Exit criteria:**

- `ReportConfig` exposes kdb namespace and raw-data function settings.
- `MetricRunRequest` supports user-defined raw source functions for trades,
  quotes, venue trades, and primary quotes.
- `KdbMetricQueryPlanner` renders raw source-function calls and wraps MMSR
  calculations inside the configured q namespace.
- Input contracts describe the canonical columns returned by raw functions.
- Tests prove invalid namespaces/functions fail before execution and source
  functions render without direct table access.
- `KdbProductionExecutionPlanner` and `KdbProductionExecutor` loop by trading
  date and optional symbol chunk before running metric queries, so production
  raw source functions are never asked for a multi-day full-market raw window.
- A production `render` command loads config/period inputs, runs bounded target
  and reference executor paths against the configured live kdb endpoint, and
  renders current-vs-reference comparisons.
- A production `plan` command prints the target/reference run scope and rendered
  source/output schema contracts without executing metric q.
- A production `preflight` command runs one bounded default or selected metric
  step against the configured endpoint and validates the result schema before
  full rendering.
- Production reference execution derives the previous
  `reference.lookback_days` trading days from the same kdb calendar, runs them
  through the daily/chunk executor, and wires comparisons plus reference-target
  trend charts into `mmsr render`.

## Milestone 10: kdb integration demo

**Goal:** Run against a real or mock kdb connection using PyKX.

**Current implementation status:**

- A deterministic mock-kdb integration demo now executes rendered `activity`
  and `liquidity` queries through `KdbMetricRunner` and a tiny mock client.
- The mock-kdb result is normalized into canonical `MetricTimeSeries` objects,
  compared with deterministic reference observations, and rendered through the
  same `build_market_monitor_report()` path as production-format reports.
- Starter-template output schema contracts now cover the default
  market-monitoring templates (`activity`, `liquidity`, and
  `toxicity_reversion`) plus optional market-microstructure add-ons
  Legacy optional template families are removed from active planning/contracts
  but are not part of the default market report.
- The mock-vs-live integration-test boundary remains explicit, and live-kdb
  execution remains environment-gated: `mmsr plan` and `mmsr preflight` now build bounded
  `activity` and `liquidity` smoke requests from documented `MMSR_KDB_*`
  variables, skips safely in pytest when variables are absent, and reuses the
  existing `KdbMetricRunner` output schema-contract boundary before
  normalization.

**Exit criteria:**

- Example kdb query executes.
- q templates validated against expected schema.
- Integration tests documented with deterministic mock-kdb coverage and an
  explicit opt-in live-kdb boundary.

## Later milestones

- Advanced visualizations that support the desk-first market story.
- Symbol-level anomaly pages as explicit opt-in escalation, not default output.
- Sector/segment/market-cap drilldowns through the generic q-side aggregation
  contract.
- Codebase slimming and q performance hardening until the default production
  path is small, fast, and easy to reason about.
- First-class stockMetrics cache integration for faster repeated generation.
- Optional LLM commentary extras.
- PDF rendering.
- Scheduling and distribution.
- Alert delivery to email/Slack/Symphony.

## Later milestone: Symbol-level anomaly pages

**Goal:** Surface symbol-scoped anomalies from already-computed comparison facts
without calculating metrics in the report layer or requiring live kdb access.

**Implemented so far:**

- `SymbolAnomalyPageOptions` defines deterministic page title, table title, help
  text, symbol group key aliases, row limits, and whether normal rows should be
  included in a watchlist.
- `select_symbol_anomalies()` filters comparison rows that contain symbol-like
  group keys, excludes normal rows by default, ranks anomalies by status,
  adverse-tail diagnostics, z-score magnitude, and percentage-change magnitude,
  and keeps the worst comparison per symbol.
- `build_symbol_anomaly_page()` formats the selected comparisons as a metric
  table with metric help and human-readable scope labels.
- The canonical `build_market_monitor_report()` path automatically inserts the
  page when symbol-scoped anomaly rows are present and can disable it through
  `MarketReportOptions.include_symbol_anomaly_page`.
- Tests cover ranking, deduplication, normal-row watchlist mode, metric-table
  rendering, no-symbol no-op behavior, and canonical report integration.
- Offline synthetic symbol-scoped comparison fixtures are generated through the
  same reference-comparison engine as the market-level demo rows, and
  `mmsr offline-demo` now visibly renders the symbol anomaly page without real
  market data.
- `SymbolDetailPageOptions` and `build_symbol_detail_pages()` build optional
  per-symbol pages from existing symbol-scoped `MetricTimeSeries` rows for the
  selected anomaly symbols.
- `MarketReportInput.symbol_series` lets production or demo callers provide
  normalized symbol-detail rows without mixing them into the market-level
  intraday detail page.
- `MarketReportOptions.symbol_group_keys` passes a configured symbol identifier
  key order through both the anomaly and detail page builders, allowing
  client-specific group keys such as `client_symbol`, `issue_code`, or
  `local_code` without report-layer code changes.
- `mmsr offline-demo` now includes deterministic reference and symbol detail
  series so the rendered report shows reference-to-target daily trend charts and
  dense-bucket intraday time-bucket line charts without live kdb+, PyKX, real
  market data, or LLM access; heatmaps remain available as an explicit opt-in.
- `build_symbol_detail_index_block()` and
  `MarketReportOptions.include_symbol_detail_index` add a compact navigation
  table on the `Symbol Anomalies` page with deterministic links to emitted
  per-symbol detail page anchors.

**Remaining backlog items:**

- None for the current symbol report-layer phase. Future production feedback may
  refine the displayed index columns, but the deterministic navigation hook is in
  place.

**Exit criteria:**

- Symbol-level report page can be built from normalized comparison facts.
- Page ranking is deterministic and documented.
- Page components expose metric help text and human-readable symbol scope labels.
- Tests cover symbols with alert, watch, normal, missing-symbol, and duplicate
  symbol rows.

## Later milestone: Sector, segment, and market-cap drilldowns

**Goal:** Surface sector, segment, and market-cap diagnostics from
already-computed comparison facts without calculating metrics in the report
layer or requiring live kdb access.

**Implemented so far:**

- `DrilldownSelectionOptions` defines deterministic drilldown group keys,
  row limits, status filtering, and symbol-scoped row handling.
- `select_drilldown_comparisons()` filters existing `MetricComparison` facts for
  configured sector, segment, and market-cap dimensions while excluding
  symbol-scoped rows by default so drilldowns do not duplicate symbol anomaly
  pages.
- `drilldown_scope_key()` preserves configured drilldown key order for stable
  table/page grouping.
- `DrilldownReportPageOptions` and `build_drilldown_report_page()` format the
  selected rows as a metric table with registry-backed metric help and
  human-readable date, bucket, and group labels.
- `MarketReportOptions` exposes `include_drilldown_page`, page/table/help labels,
  `drilldown_group_keys`, and `max_drilldown_rows`.
- `build_market_monitor_report()` inserts the drilldown page only when matching
  group-level comparison rows are present, and the page remains opt-out through
  report options.
- `OfflineDemoReportOptions` and `MockKdbIntegrationDemoOptions` pass
  drilldown-page inclusion and row-limit controls into the canonical market
  report options.
- The bundled `offline-demo` and `mock-kdb-demo` CLI commands expose
  `--no-drilldown-page` and `--max-drilldown-rows` so sample reports can
  demonstrate default, opt-out, and compact drilldown-table behavior.
- The bundled offline demo now visibly renders the drilldown page from synthetic
  market-cap and segment comparison facts without live kdb+, PyKX, real market
  data, or LLM access.
- `docs/production_readiness.md` documents the sector taxonomy, segment labels,
  market-cap bucket rules, symbol metadata joins, required kdb+ source fields,
  and bounded live-smoke validation gates required before richer
  production-specific fixtures or live validation.
- Tests cover default dimensions, symbol exclusion and inclusion, custom keys,
  status filters, row limits, scope ordering, page rendering, metric help,
  missing definitions, market-report option wiring, no-row/disabled no-op
  behavior, and validation.

**Remaining backlog items:**

- Use the production-readiness checklist to confirm client taxonomy, metadata
  joins, and kdb+ source schemas before adding richer sector-specific offline
  fixture rows.

**Exit criteria:**

- Drilldown report pages can be built from normalized comparison facts.
- Page selection and ordering are deterministic and documented.
- Page components expose metric help text and human-readable group labels.
- Tests cover market-cap, segment, sector, custom key, missing-key, status, and
  symbol-scoped edge cases.


## Milestone 9C: compact Plotly report HTML for kdb-scale data

**Goal:** Rework the production HTML report so real kdb-backed runs stay
readable and compact by default, with Plotly visuals built from aggregated
report facts instead of large raw backing-data tables.

**Implemented so far:**

- Time-series chart components emit compact Plotly figure specifications instead
  of inline SVG-only visuals in the default full-report template.
- The default HTML template loads Plotly once and renders each chart from a
  colocated JSON specification.
- Report chart partials expose metric help text and a compact plot-data summary
  rather than dumping every backing observation into a table.
- A generic `PlotlyChart` report component supports metric-aware custom figures
  such as box/whisker distributions and stacked bars.
- The market monitor report now includes an `Activity Distribution` page when
  current and reference activity series are present.
- Turnover, volume, and trade-count activity diagnostics render current
  cumulative intraday percent as a line with circle markers, historical
  cumulative percent as per-bucket box/whisker statistics, and reference/current
  session or auction share as horizontal stacked bars.
- Activity distribution charts intentionally skip symbol-scoped series so the
  default report does not generate single-stock plots.
- The market monitor report now includes a `Displayed Liquidity` page when
  quoted-spread or top-of-book-depth current/reference series are present.
- Displayed liquidity diagnostics render historical per-bucket box/whisker
  statistics, a current-period intraday profile line with circle markers, and a
  capped horizontal bar of the largest group-level current-minus-reference
  deltas.
- Plotly activity and displayed-liquidity visuals now use current-period means
  for the current line/profile and null-filtered percentile inputs for
  historical/reference box-and-whisker statistics.
- Default comparison, symbol-anomaly, and drilldown row limits are capped so
  tables remain summary diagnostics rather than full report payload dumps.
- The Cross-Venue Toxicity/Reversion page now renders compact Plotly horizon
  progression curves with horizon on the x-axis, reversion bps on the y-axis,
  and one line per venue.
- Reversion curve visuals carry low-confidence markers and compact hover text
  built from already-aggregated kdb output rather than raw trade or quote rows.
- Reversion current-versus-reference diagnostics now default to a capped
  horizontal Plotly bar chart of current-minus-reference bps by venue/horizon
  context, with the old comparison table disabled by default and still
  available only as an explicitly capped opt-in table.

**Remaining backlog items:**

- Validate the rendered HTML size and visual usability with one real kdb-backed
  production report.
- Decide whether production deployments should use the Plotly CDN, a packaged
  local Plotly asset, or an offline self-contained bundle.
- Add compact production smoke evidence for a real kdb-backed report that
  includes activity, displayed-liquidity, and reversion pages together.

**Exit criteria:**

- Default market reports do not include full raw observation tables under chart
  components.
- Activity metrics have compact current-vs-reference intraday distribution
  visuals.
- Displayed liquidity metrics have compact current-vs-reference intraday profile
  visuals with capped group deltas.
- Cross-Venue Toxicity/Reversion has compact Plotly horizon curves and capped
  venue/horizon comparison diagnostics, with no default full comparison table.
- Report options can disable or cap the activity and displayed-liquidity pages.
- Tests cover compact figure construction, current-period mean semantics,
  null-filtered reference percentile statistics, reversion Plotly horizon
  curves, capped reversion diagnostic bars, report wiring, template rendering,
  capped table defaults, and no-symbol activity/liquidity chart behavior.

## Milestone 9D: simulated kdb source functions for dev/debug

**Goal:** Let developers and report reviewers run normal remote-kdb
plan/preflight/render commands without production market-data tables by
injecting deterministic q source getters into the connected kdb process for that
run.

**Implemented so far:**

- Added a packaged q library template `mmsr_simulated_sources.q.j2` that defines
  deterministic dev/debug source functions under a configurable namespace:
  `getTradingCalendar`, `getRef`, `getTrade`, `getQuote`, `getPtsTrade`,
  `getPtsQuote`, and `getPrimaryQuote`.
- Added `render_simulated_source_function_bootstrap()` so the production CLI can
  render and inject the q source-function library with a chosen namespace and
  synthetic symbol count.
- The normal remote-kdb production commands `plan`, `preflight`, and `render`
  support `--inject-simulated-sources`, `--simulated-source-namespace`, and
  `--simulated-symbol-count`. When enabled, MMSR sends the simulated source q
  bootstrap over the existing kdb connection and routes calendar, reference,
  trade, quote, PTS, and primary quote source-function calls to the injected
  namespace for that run.
- Removed the earlier standalone local/offline simulated-source CLI and Python
  client path so there is one supported simulated-source mechanism: injection
  into the same kdb process used by normal production commands.

**Remaining backlog items:**

- Validate the injected simulated q source functions in a real remote kdb+
  process once q is available in the development environment.
- Add optional knobs beyond symbol count only if developers need to vary venues,
  bucket grids, or trading-day depth for stress testing.

**Exit criteria:**

- The simulated q functions match the canonical source-function signatures used
  by the production runner.
- Existing production commands can inject and use the simulated source getters
  against a remote kdb process without requiring a separate render/preflight CLI
  command path.
- Tests prevent regressions in q bootstrap rendering, namespace validation,
  source-function routing, and injected-command wiring.
- CLI helpers let developers choose the simulated universe size for one normal
  production command invocation without editing q by hand.

## Later milestone: ppw packaging parity and CLI ergonomics

**Goal:** Align project packaging and command-line ergonomics with the ppw-style
foundation after the production-format report path is stable, including explicit
`dev` and `doc` optional dependency support without changing lean runtime
installs.

**Implemented so far:**

- The runtime dependency path remains limited to the package's production
  dependencies and optional runtime extras.
- The existing `dev` Poetry group contains contributor tooling for tests,
  formatters, type checks, tox, and pre-commit hooks.
- A dedicated `doc` Poetry group now contains MkDocs tooling required by
  `mkdocs.yml`: `mkdocs`, `mkdocs-material`, and `mkdocstrings[python]`.
- README documents the runtime, kdb extra, `dev`, and `doc` setup paths.
- `docs/index.md` provides a MkDocs quickstart that mirrors the README demo
  commands, including offline/mock-kdb drilldown examples with
  `--max-drilldown-rows` and `--no-drilldown-page`.
- Tox and CI include a documentation build path using `poetry install --with doc`
  and `mkdocs build --strict`.
- CLI behavior snapshots preserve the Typer command surface for
  `offline-demo` and `mock-kdb-demo`: top-level help, command defaults,
  override parsing, option presence, and offline/mock-kdb safety language.
- Both demo commands expose `--include-intraday-heatmaps` as an explicit opt-in
  while keeping dense time-bucket line charts as the default intraday view.
- The CLI now uses Typer as an explicit runtime dependency because the project
  owner requested Typer ergonomics for the installed `mmsr` command.

**Remaining backlog items:**

- Revisit README and MkDocs quickstart instructions whenever additional
  production commands are added.
- Consider relocating synthetic demo entry points out of the installed package
  after production report construction and kdb schema-contract tests fully cover
  the same deterministic paths.

**Exit criteria:**

- `dev` and `doc` setup paths are documented and validated in CI or local tests.
- Runtime install remains lean and does not pull documentation or development
  tooling unless explicitly requested.
- CLI tests cover the existing `offline-demo` and `mock-kdb-demo` command
  behavior before and after any Typer migration.
- The roadmap and journal explain any new dependency added.


## HTML template and branding milestone details

The HTML report layer must provide:

- A default Jinja report template committed under `mmsr/report/templates/`.
- Partial templates for repeated blocks such as metric cards and commentary.
- A renderer that accepts packaged templates by default and an override template directory for client-specific customization.
- Branding options for `brand_name`, `logo_image_src`, `header_image_src`, `footer_image_src`, and `footer_text`.
- Tests that verify default rendering and custom branding values.
