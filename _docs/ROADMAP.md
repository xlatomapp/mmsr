# ROADMAP.md

This roadmap defines the implementation milestones for `mmsr`.

## Product goal

Create a Python package that generates market microstructure monitoring reports for Japanese market data using level 1 trade and quote data stored in kdb+. The package should run deterministically without an LLM and optionally support LLM-polished commentary.

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

**Initial metrics:**

- `turnover`
- `volume`
- `trade_count`
- `quoted_spread_bps`
- `quoted_spread_ticks`
- `top_of_book_depth`
- `realized_volatility`
- `effective_spread_bps`
- `price_impact_30s_bps`
- `signed_turnover`
- `trade_imbalance`
- `primary_quote_reversion_10ms_bps`
- `primary_quote_reversion_100ms_bps`
- `primary_quote_reversion_500ms_bps`
- `primary_quote_reversion_1s_bps`
- `primary_quote_reversion_5s_bps`
- `primary_quote_reversion_10s_bps`

**Exit criteria:**

- Metrics are registered at import or through an explicit registry builder.
- Each metric has formula, interpretation, caveats, and required columns.
- Tests verify lookup, docs generation, and uniqueness.

## Milestone 4: kdb/PyKX infrastructure

**Goal:** Implement kdb client abstraction, q template loading/rendering, and kdb-backed trading calendar access.

**Exit criteria:**

- PyKX import is lazy.
- `KdbClient` can be instantiated from config.
- Query templates can be loaded from package resources.
- Query rendering validates required parameters.
- Trading calendar data is read from a dedicated kdb calendar table rather than weekday assumptions.
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
- Each rendered plan exposes required source-table contracts, required output
  columns, and supported optional output columns so production users can manually
  adjust q while preserving the Python report boundary.
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
- Formula: `side * 10000 * (primary_mid[t + horizon] - primary_mid[t-]) / primary_mid[t-]`.
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
- Time-series data should render as real charts, such as line plots for trends,
  while preserving accessible tabular backing data.
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
  placeholder-only tables.
- Heatmap/intraday diagnostics render with visual encodings rather than
  placeholder-only tables.
- Deterministic commentary uses display labels for metrics, buckets, groups,
  and observation units.
- Executive market overview section summarizes high-level market trends before
  per-bucket diagnostics.
- Metric cards, tables, charts, heatmaps, and trusted HTML blocks expose working
  accessible metric/help controls.
- Tests prove mock-data reports and production-format reports use the same
  builder/template path.

## Milestone 10: kdb integration demo

**Goal:** Run against a real or mock kdb connection using PyKX.

**Current implementation status:**

- A deterministic mock-kdb integration demo now executes rendered `activity.q`
  and `liquidity.q` queries through `KdbMetricRunner` and a tiny mock client.
- The mock-kdb result is normalized into canonical `MetricTimeSeries` objects,
  compared with deterministic reference observations, and rendered through the
  same `build_market_monitor_report()` path as production-format reports.
- Starter-template output schema contracts now cover `activity.q` and
  `liquidity.q`, and `KdbMetricRunner` validates those contracts before
  normalizing q results into report-boundary time series.
- The mock-vs-live integration-test boundary remains explicit, and live-kdb
  execution remains environment-gated: `mmsr.kdb.live_smoke` now builds bounded
  `activity.q` and `liquidity.q` smoke requests from documented `MMSR_KDB_*`
  variables, skips safely in pytest when variables are absent, and reuses the
  existing `KdbMetricRunner` output schema-contract boundary before
  normalization.

**Exit criteria:**

- Example kdb query executes.
- q templates validated against expected schema.
- Integration tests documented with deterministic mock-kdb coverage and an
  explicit opt-in live-kdb boundary.

## Later milestones

- Advanced visualizations.
- Symbol-level anomaly pages.
- Sector/segment/market-cap drilldowns.
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
- `mmsr offline-demo` now includes deterministic symbol detail series so the
  rendered report shows per-symbol trend charts and intraday heatmaps without
  live kdb+, PyKX, real market data, or LLM access.
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
- CLI behavior snapshots now preserve the current argparse command surface for
  `offline-demo` and `mock-kdb-demo`: top-level help, command defaults,
  override parsing, option presence, and offline/mock-kdb safety language.

**Remaining backlog items:**

- CLI implementation decision for this phase is to keep argparse. The existing
  command surface is small, covered by behavior snapshots, and avoids adding a
  new runtime or developer dependency solely for CLI help text.
- Revisit Typer only if additional production commands make argparse materially
  harder to maintain; if it is adopted later, migrate one command at a time while
  keeping the behavior snapshots and existing render-path tests green.
- Revisit README and MkDocs quickstart instructions after any future CLI
  implementation change.

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
