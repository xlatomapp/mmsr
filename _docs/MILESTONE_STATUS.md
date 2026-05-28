# Milestone Status Audit

This audit validates the implementation against `_docs/ROADMAP.md` as of 2026-05-25.

## Summary

| Milestone | Validation status | Result |
| --- | --- | --- |
| 1. Project skeleton and governance | Complete | Repository skeleton, governance docs, canonical `_docs/journal.md`, import, and pytest validation are present. |
| 2. Domain models | Complete | Period, bucket, metric definition, metric time-series, comparison, and commentary fact models are present and covered by tests. |
| 3. Metric registry and starter metric definitions | Complete | All roadmap starter metrics are registered and documented; tests cover lookup, docs/help text, and duplicate rejection. |
| 4. kdb/PyKX infrastructure | Complete | Lazy PyKX client, strict q-template loading/rendering validation, and kdb-backed calendar source are implemented and covered by offline tests. |
| 5. Metric execution interface | Complete and hardened | `KdbMetricQueryPlanner` isolates q rendering from execution, exposes input/output schema contracts through `RenderedMetricQuery`, and `KdbMetricRunner.run()` validates the planned output schema before normalizing dict/list-like results into `MetricTimeSeries`. |
| 5A. Cross-venue toxicity reversion metrics | Complete under documented assumptions | Reversion definitions, strict q template, runner integration, typed toxicity config, production report SVG venue-curve page, duplicate Intraday Detail suppression, result-to-visual conversion helpers, sample-size confidence flagging, deterministic template commentary facts, reference-comparison wiring, schema contracts, and explicit horizon sort order exist. Live production validation is deferred because credentials/endpoints are unavailable; production report behavior assumes the kdb query output schema is correct. |
| 6. Reference comparison engine | Complete | Comparison outputs preserve current/reference values, change, confidence, optional z-scores, percentiles, adverse-tail diagnostics, and direction-aware status. |
| 7. Deterministic commentary engine | Complete | Template commentary generation exists for structured metric facts and section-level summary facts; report-section assembly now prepends alert/watch/normal status headlines without LLM dependencies. |
| 8. Report components and metric help | Complete | HTML report components render metric cards, metric tables, deterministic time-series charts, deterministic heatmap visuals, trusted HTML blocks, and a deterministic metric definitions appendix with metric help/documentation. |
| 9. End-to-end mock-data demo | Complete | Deterministic synthetic metric fixtures, the `mmsr offline-demo` HTML command path, README quickstart instructions, and delegation into the canonical production-format report builder are present and tested. |
| 9A. Production-format report polish before kdb integration | Complete | The canonical production-format report builder, shared accessible metric/help controls, inline SVG time-series trend visuals, inline SVG heatmap visual encodings, human-friendly display labels, and the executive market overview section are present and tested. |
| 9B. Production kdb source-function boundary | In progress | `ReportConfig` now models a calculation namespace, user-defined calendar/symbol/reference/trade/quote functions, daily-scope enforcement, optional symbol chunk sizing, and reference lookback policy. `KdbMetricQueryPlanner` renders `.sb.mmsr.getTrade[date;syms]`, `.sb.mmsr.getQuote[date;syms]`, and `.sb.mmsr.getRef[date;syms]` style sources under a configured namespace, and source rows now carry per-tick `session`/`auction` state instead of relying on configured static session times. `KdbProductionExecutionPlanner` / `KdbProductionExecutor` build one-trading-day target/reference plans from calendar plus reference-data universe functions, summarize the bounded run scope without metric IO, and execute those plans with optional symbol chunks. `mmsr plan`, metric-selectable `mmsr preflight`, and `mmsr render` cover review, bounded validation, and current-vs-reference reporting. Live source-function validation remains pending. |
| 10. kdb integration demo | In progress | Deterministic mock-kdb integration demo executes rendered q templates through `KdbMetricRunner`, normalizes mock kdb-shaped rows, compares current/reference observations, and renders the canonical report path without PyKX. Live-kdb integration-test documentation and the first environment-gated `activity` smoke harness are in place; actual live execution remains deferred until a real kdb+ process and production-like schemas are available. |
| Later. Symbol-level anomaly pages | Complete for current phase | Deterministic symbol anomaly selection, summary-page assembly, optional per-symbol detail pages, configurable symbol keys, and offline-demo symbol fixtures work from existing `MetricComparison` and `MetricTimeSeries` facts, insert into the canonical report when symbol rows are present, and remain offline/LLM-free. |
| Later. Sector, segment, and market-cap drilldowns | Complete for current phase | `DrilldownSelectionOptions`, `select_drilldown_comparisons()`, `drilldown_scope_key()`, `DrilldownReportPageOptions`, and `build_drilldown_report_page()` select and render existing sector, segment, and market-cap `MetricComparison` facts as metric-help-backed drilldown tables. `MarketReportOptions` wires the page into the canonical report when matching group-level rows are present, and the offline/mock-kdb demo options plus CLI expose drilldown opt-out and row-limit controls. |

## Milestone 1: Project skeleton and governance

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| ppw-style repository structure exists | Package modules, `pyproject.toml`, tests, docs, config, and CI files are present. | Met |
| `_docs/AGENTS.md` exists | Present. | Met |
| `_docs/ROADMAP.md` exists | Present. | Met |
| `_docs/journal.md` exists and records initial state | Moved from repository root to `_docs/journal.md` and retained history. | Met |
| Basic package import works | `tests/test_import.py` passes. | Met |
| Basic test command works | `python -m pytest -q` passes. | Met |

## Milestone 2: Domain models

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Models validate bucket sizes such as `1m`, `5m`, `30m` | `IntradayBucketSpec` validates size/unit strings; tests cover valid and invalid examples. | Met |
| Utility builds an intraday bucket grid with auction rows | `build_intraday_bucket_grid` returns `AMO`, `AMC`, `PMO`, and `PMC` rows; tests cover this. | Met |
| Bucket grid rows include numeric `sort_order` | `TimeBucket.sort_order` exists and is tested. | Met |
| Session breaks are represented explicitly | `ReportPeriod.sessions` accepts multiple `TradingSession` objects; tests and config use AM/PM sessions. | Met |
| Metric definitions can produce help text | `MetricDefinition.help_text()` exists and is tested. | Met |
| Tests cover model construction and validation | Period/bucket tests exist. | Met |
| Roadmap core object `MetricTimeSeries` exists | `MetricTimeSeries` exists in `mmsr/metrics/results.py`, is exported through `mmsr.metrics`, validates consistent metric names, and preserves observation order/date/time buckets/groups. | Met |

## Milestone 3: Metric registry and starter metric definitions

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Metrics are registered at import or through explicit registry builder | `build_default_registry()` registers `STARTER_METRICS`. | Met |
| Each metric has formula, interpretation, caveats, and required columns | All roadmap starter metrics define label, description, formula, interpretation, unit, aggregation, direction, required tables, and required columns. `help_text()` exposes caveats, defaulting to `None` where not specific. | Met |
| Tests verify lookup, docs generation, and uniqueness | `tests/test_metric_registry.py` covers registry contents, help text, and duplicate rejection. | Met |
| Initial metric list is complete | All 17 roadmap starter metric names are present. | Met |

## Milestone 4: kdb/PyKX infrastructure

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| PyKX import is lazy | `mmsr/kdb/client.py` imports `pykx` only in `KdbClient.connect()`. | Met |
| `KdbClient` can be instantiated from config | `KdbConfig` and `KdbClient` exist; tests instantiate the client without importing PyKX. | Met |
| Query templates can be loaded from package resources | `load_q_template()` reads packaged q templates and rejects non-q names, nested paths, and missing resources; tests cover this. | Met |
| Query rendering validates required parameters | `render_template()` extracts explicit placeholders, rejects missing/unused/invalid parameters, requires string values, and fails on malformed placeholder blocks; tests cover this behavior. | Met |
| Trading calendar data is read from a dedicated kdb calendar function | `KdbTradingCalendarSource` calls a configurable user-owned calendar function; tests assert `.sb.mmsr.getTradingCalendar`. | Met |
| Offline tests do not require live kdb | Current tests pass without PyKX or kdb. | Met |

## Milestone 5: Metric execution interface

**Outcome:** Complete and hardened.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Metric runner accepts `MetricDefinition`, period, bucket spec, and group-by list | `MetricRunRequest` carries `MetricDefinition`, `ReportPeriod`, and `group_by`; `period.bucket` is rendered into the q `bucket_expr` by `KdbMetricQueryPlanner`. | Met |
| Querying logic is isolated from execution | `KdbMetricQueryPlanner.render()` returns a `RenderedMetricQuery` without IO, including rendered q text, source-table contracts, required output columns, supported optional output columns, and result grouping. | Met |
| Runner returns a normalized time-series result schema | `KdbMetricRunner.run()` plans the query, executes the planned q, validates `RenderedMetricQuery.output_contract`, and returns `MetricTimeSeries`; `normalize_metric_result()` converts column dictionaries and row dictionaries into `MetricObservation` rows. | Met |
| Initial q templates exist for activity and quoted spread metrics | `activity` and `liquidity` group by `date`, `time_bucket`, and requested group columns. Planner/runner maps `turnover`, `volume`, `trade_count`, `quoted_spread_bps`, and `top_of_book_depth` to those templates. | Met |
| Integration tests can be marked/skipped without kdb connection | `pyproject.toml` registers the `kdb_integration` marker and `tests/test_kdb_metric_runner.py` contains a skipped live-kdb placeholder. | Met |

## Milestone 5A: Cross-venue toxicity reversion metrics

**Outcome:** Complete under documented assumptions.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Metric definitions exist for each configured horizon | Six reversion metrics are registered. | Met |
| q template exists for primary-quote reversion calculation | `toxicity_reversion` is now a strict renderable template with placeholders for PTS trades, PTS quotes, date/time filters, optional venue filters, horizon, horizon sort order, max primary and matched-PTS quote age, bucket expression, value column, and group columns. `toxicity_reversion_input_schema_contracts()` defines required PTS trade, PTS quote, and primary quote source columns; `toxicity_reversion_output_schema_contract()` defines the required report-boundary output columns offline. | Met under documented source/output schema assumptions. |
| Runner maps reversion metrics to the q template | `KdbMetricRunner` maps `primary_quote_reversion_*_bps` to `toxicity_reversion`, renders horizon, optional venue, primary-venue, and quote-age parameters, validates the reversion output schema contract, and normalizes `venue`/`horizon` dimensions into `MetricTimeSeries`. | Met |
| Config supports optional venues, primary venue, horizons, side source, clustering, stale quote filters, and confidence thresholds | `ToxicityConfig` and nested typed config models expose an optional venue filter, primary venue, horizons, side source, clustering, stale-quote filters, and confidence thresholds. When no venue filter is configured, the q template discovers venues from source rows. `ReportConfig.metric_parameters_for()` translates reversion settings into `MetricRunRequest.parameters`. | Met |
| Production visual supports venue reversion curves, context ranking, and duplicate detail suppression | `build_toxicity_reversion_page()` renders deterministic SVG venue reversion curves from normalized kdb-backed `MetricTimeSeries` rows. Horizon progression uses configured horizon order or q-output `horizon_sort_order`; low-confidence sample metadata is surfaced; context ranking options select largest positive reversion, largest absolute reversion, lowest confidence, upstream `context_sort_order`, or chronological order before chart limits. The q convention is `aggressorSide * (future_primary_mid - primary_mid_at_trade) / future_primary_mid * 10000`, with side inferred from each trade's own PTS quote. `MarketReportOptions.include_toxicity_reversion_metrics_in_detail_page` defaults to `False`, so the dedicated page suppresses duplicate reversion series from generic `Intraday Detail` unless callers opt in. | Met |
| Tests verify metric registration and basic visual rendering | `tests/test_toxicity_reversion.py` covers registration, placeholder rendering, point conversion, and confidence flagging; `tests/test_kdb_metric_runner.py` covers runner integration. | Met |
| Terminology uses `reversion` consistently | User-facing labels use `+... Reversion`; visual uses `Reversion (bps)`. | Met |
| Deterministic commentary supports reversion results | `reversion_commentary_facts_from_curve_points()` converts curve points into grounded `CommentaryFact` objects for headline positive reversion and low-confidence warnings without LLM dependencies. | Met |
| Reference comparison supports reversion results | `compare_reversion_metric_timeseries()` delegates to `compare_metric_timeseries`, compares venue/horizon/report-group histories with one observation per trading day by default, and forces `higher_is_better=False` for the reversion metric family. | Met |
| Offline output-schema contract documents reversion template outputs | `mmsr.kdb.schema_contracts` defines the required `toxicity_reversion` output columns: `date`, `time_bucket`, `venue`, `horizon`, the dynamic metric value column, `horizon_sort_order`, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`, plus requested report groups. | Met |
| Offline input-schema contract documents production source-table assumptions | `toxicity_reversion_input_schema_contracts()` defines required venue-trade columns (`date`, `time`, `sym`, `venue`, `tradePrice`, `tradeSize`) and quote-source columns (`date`, `time`, `sym`, `venue`, `bidPrice`, `askPrice`), including assumptions for same-venue side inference and quote price conventions. | Met |
| Horizon progression sort order is explicit | The reversion q template emits `horizon_sort_order`, the runner renders deterministic horizon order for the six supported horizons, and visual conversion preserves the value for chart ordering. | Met |
| Live-kdb validation boundary is explicit | `tests/test_kdb_schema_contracts.py` includes a skipped `kdb_integration` placeholder for validating the template against confirmed production venue-trade and primary-quote schemas. User direction on 2026-05-24 is to skip live validation and build from the documented assumptions first. | Deferred to Milestone 10. |

## Milestone 7: Deterministic commentary engine

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Rule engine detects alerts, watch items, and normal conditions | `TemplateCommentaryEngine` orders section summaries before metric facts, then orders alert, watch, comparison-only, and normal facts deterministically. `section_summary_fact_from_comparisons()` counts already-computed alert/watch/comparison-only/normal statuses and assigns the headline severity from those counts. | Met |
| Template commentary is generated per page/section | `build_comparison_report_page()` converts comparisons and commentary facts into `ReportPage` metric cards and a deterministic `CommentaryBlock`, prepending a section headline when deriving commentary from comparisons. | Met |
| Commentary is grounded only in computed facts | Generic comparison commentary facts and section summary facts are built only from `MetricComparison` fields and optional metric definitions; the report-section builder does not calculate new analytics or call an LLM. | Met |
| Tests cover severity thresholds and output text | Tests cover alert output, caveats, comparison-only text, status ordering, section summary counts, headline output text, and page-level report-section assembly/rendering. | Met |

## Milestone 8: Report components and metric help

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| HTML renderer includes info/help icons or expandable metric docs | Metric cards, metric tables, time-series charts, heatmaps, trusted HTML blocks, and metric definitions appendix blocks render `metric-info` controls or inline expandable definitions backed by metric/help text. | Met |
| Excel/static renderers can include a metric definitions sheet or appendix placeholder | `metric_definitions_markdown()` renders complete deterministic definition text, and `build_metric_definitions_appendix_page()` / `append_metric_definitions_appendix()` add an HTML/static appendix page from the metric definitions used by report-page cards, metric-table rows, time-series charts, and heatmaps. | Met |
| Tests verify metric help is included | HTML rendering, report-section, metric-table, time-series chart, heatmap, and metric-doc tests assert that metric help/info controls and appendix definition fields are included. | Met |
| Initial report component set exists | Metric card, metric table, deterministic time-series chart, deterministic heatmap visual, commentary block, trusted HTML block, and metric definitions appendix exist. | Met |

## Milestone 9: End-to-end mock-data demo

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Example config or command runs locally | The `mmsr offline-demo --output <path>` command renders deterministic synthetic HTML through `build_offline_demo_report()`, which adapts mock metrics into `MarketReportInput` and delegates to `build_market_monitor_report()` before `render_report()`; tests cover file output, custom text, appendix omission, and validation. | Met |
| Synthetic metric results flow through comparison, commentary, and HTML report rendering | `mmsr.examples.offline_fixtures` builds deterministic synthetic current/reference `MetricTimeSeries` objects and precomputed `MetricComparison` rows; `mmsr.examples.offline_demo.build_offline_demo_report()` adapts them into the canonical `MarketReportInput`; `mmsr.report.market_report.build_market_monitor_report()` assembles the shared production-format `ReportDocument` with metric cards, comparison table, deterministic commentary, time-series/heatmap visuals, and a metric definitions appendix; tests render the document to HTML. | Met |
| README includes quickstart | README documents `poetry run mmsr offline-demo --output reports/offline_demo.html`, describes the synthetic normalized metrics, states that the demo routes through `build_market_monitor_report()`, and states that the demo does not query kdb+, import PyKX, call an LLM, or use real market data; tests cover the quickstart text. | Met |

## Milestone 9A: Production-format report polish before kdb integration

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Canonical production-format report builder exists and mock-data demo delegates to it | `mmsr.report.market_report.build_market_monitor_report()` owns the shared report document shape; `mmsr.examples.offline_demo.build_offline_demo_report()` adapts mock fixtures into `MarketReportInput` and delegates to it. | Met |
| Roadmap/status docs state that demo and production share the same template and report assembly path | `_docs/ROADMAP.md`, `_docs/MILESTONE_STATUS.md`, and README describe the mock-data demo as a format acceptance harness. | Met |
| Time-series trend visuals render as real chart components | `TimeSeriesChart` renders deterministic inline SVG line charts with one series per group and keeps an expandable backing data table for auditability; tests cover direct rendering, reference-to-target daily trends, dense intraday time-bucket line charts, and production-format reports. | Met |
| Heatmap/intraday diagnostics render with visual encodings | `Heatmap` renders deterministic inline SVG matrix visuals, encodes magnitude through cell intensity, includes missing-value cells, and keeps an expandable backing data table for auditability; report detail pages now use dense intraday time-bucket line charts by default, preserve heatmaps as an explicit opt-in, and the demo CLI exposes `--include-intraday-heatmaps` for sample artifacts that need both views. | Met |
| Deterministic commentary uses display labels | `mmsr.presentation.labels` formats auction buckets, group keys/values, comparison scopes, and reference observation units; commentary, comparison tables, charts, heatmaps, offline demo HTML, and CLI output tests assert human-facing labels and reject internal key/value strings. | Met |
| Executive market overview summarizes high-level trends before per-bucket diagnostics | `build_executive_market_overview_block()` renders a deterministic high-level status summary before metric cards, comparison tables, and per-bucket diagnostic visuals; market-report and offline-demo tests assert it appears before the diagnostic components. | Met |
| Metric/help controls are working accessible controls | Shared `partials/help_control.html.j2` renders deterministic `<details>/<summary>` controls across metric cards, tables, charts, heatmaps, and trusted HTML blocks; tests assert there are no title-only info buttons. | Met |
| Tests prove mock-data and production-format reports use the same builder/template path | `tests/test_market_report.py` and offline-demo tests cover canonical builder delegation and packaged template rendering. | Met |

## Milestone 9B: Production kdb source-function boundary

**Outcome:** In progress.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Config exposes namespace and raw data functions | `KdbExecutionConfig` and `KdbRawDataFunctionsConfig` are available from `ReportConfig.kdb`; `enforce_daily_raw_scope` and `symbol_chunk_size` document the production scaling contract. | Met |
| Metric plans call user-defined raw functions | `MetricRunRequest.source_functions` and `KdbMetricQueryPlanner` render raw-source function calls. | Met |
| MMSR calculations are namespace scoped | `activity`, `liquidity`, and `toxicity_reversion` install calculation functions under the configured `calculation_namespace`. | Met |
| Raw function result schemas are validated | Existing input contracts now apply to canonical rows returned by source functions; output contracts validate metric tables before normalization; `mmsr preflight` executes one bounded production metric step and can target a configured metric with `--metric` before full rendering. | Met offline; live preflight available |
| Production orchestration loops by date/chunk | `KdbProductionExecutionPlanner` builds one-day metric requests from a trading calendar and optional symbol chunks; `KdbProductionExecutor.build_plan_summary()` reports target/reference scope and contracts without metric IO; `KdbProductionExecutor` executes plans through `KdbMetricRunner` and combines normalized observations by metric; `mmsr preflight` validates the first planned step or a selected configured metric before a full run. | Met offline; live validation gated |

## Milestone 10: kdb integration demo

**Outcome:** In progress; live execution is now environment-gated.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Example kdb query executes | `mmsr.examples.mock_kdb_demo` executes rendered `activity` and `liquidity` queries through `KdbMetricRunner` and `DeterministicMockKdbClient`; the CLI exposes `mmsr mock-kdb-demo --output <path>`. `mmsr plan` and `mmsr preflight` provide bounded config-driven live-kdb checks before rendering. | Met offline; live path available but not executed here |
| q templates validated against expected schema | `mmsr.kdb.schema_contracts` defines output schema contracts for `activity`, `liquidity`, and `toxicity_reversion`; `KdbMetricRunner` validates the matching contract before normalization; unit tests cover missing-column failures. The live activity and liquidity smoke tests execute through the same runner and schema-contract boundary after their environment gates pass. | Met offline; live validation gated |
| Integration tests documented | Unit tests cover the deterministic mock-kdb demo path. `docs/kdb_integration_testing.md` documents the mock-vs-live boundary, required `MMSR_KDB_*` environment variables, starter table/schema assumptions, `LiveKdbActivitySmokeConfig`, `LiveKdbLiquiditySmokeConfig`, and why `@pytest.mark.kdb_integration` tests remain skipped unless explicitly configured. | Met |

## Later milestone: Symbol-level anomaly pages

**Outcome:** Complete for the current package phase.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Symbol-level report pages can be built from normalized facts | `mmsr.report.symbols.build_symbol_anomaly_page()` accepts already-computed `MetricComparison` rows and metric definitions, `build_symbol_detail_pages()` accepts existing symbol-scoped `MetricTimeSeries` rows for selected symbols, and `build_symbol_detail_index_block()` links emitted detail pages from the anomaly page without calculating new metrics. | Met for summary, detail, and index blocks |
| Page ranking is deterministic and documented | `select_symbol_anomalies()` ranks by status, adverse-tail diagnostics, z-score magnitude, and absolute percentage-change magnitude, then keeps the worst comparison per symbol. `_docs/ROADMAP.md` and README describe the behavior. | Met |
| Page components expose metric help text and human-readable symbol scope labels | The page uses `MetricTable`/`MetricTableRow` objects with metric definitions and `format_comparison_scope_label()` output such as `Symbol: 7203` and auction display labels. | Met |
| Canonical report builder can include the pages | `build_market_monitor_report()` inserts the anomaly page when symbol-scoped alert/watch rows are present, inserts optional per-symbol detail pages when `MarketReportInput.symbol_series` or symbol-scoped current series rows are supplied, adds a compact `Symbol Detail Index` when detail pages are emitted, supports `MarketReportOptions.include_symbol_anomaly_page=False`, `include_symbol_detail_pages=False`, and `include_symbol_detail_index=False`, and passes `MarketReportOptions.symbol_group_keys` through summary/detail/index builders for client-specific identifier keys. | Met |
| Offline demo visibly exercises symbol anomalies without real data | `mmsr.examples.offline_fixtures.build_offline_symbol_metric_comparisons()` creates deterministic symbol-scoped comparison facts through the comparison engine, `build_offline_symbol_metric_time_series()` creates matching symbol detail rows, and `mmsr offline-demo` renders both the `Symbol Anomalies` page and per-symbol detail pages. | Met |
| Tests cover symbols with alert, watch, normal, missing-symbol, duplicate symbol rows, detail rows, and detail-index links | `tests/test_symbol_anomaly_pages.py` covers ranking, deduplication, normal-row watchlist mode, no-symbol no-op behavior, summary/detail/index option validation, symbol-series filtering, stable detail-page anchors, rendered index links, and canonical report integration. `tests/test_offline_fixtures.py` and `tests/test_offline_demo.py` cover synthetic fixture generation and render-path visibility. | Met |

**Remaining work:** Symbol-level anomaly pages, detail pages, and compact
detail-index navigation are complete for this package phase. Future production
feedback may refine index columns or styling, but no deterministic symbol
report-layer backlog remains.

## Later milestone: Sector, segment, and market-cap drilldowns

**Outcome:** Complete for the current package phase.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Drilldown report pages can be built from normalized comparison facts | `build_drilldown_report_page()` selects existing `MetricComparison` rows using `DrilldownSelectionOptions` and renders a `ReportPage` with a metric table. | Met |
| Page selection and ordering are deterministic and documented | `DrilldownSelectionOptions` validates configured keys, status filters, row limits, and symbol-scoped handling; selection is sorted by status, severity magnitude, configured dimension order, metric, date, bucket, and full group mapping. `_docs/ROADMAP.md` documents the behavior. | Met |
| Page components expose metric help text and human-readable group labels | `DrilldownReportPageOptions` and `build_drilldown_report_page()` render metric-table rows backed by registry metric definitions and scope labels with readable date, intraday bucket, market-cap, segment, sector, and custom group-key text. | Met |
| Tests cover market-cap, segment, sector, custom key, missing-key, status, and symbol-scoped edge cases | `tests/test_drilldowns.py`, `tests/test_market_report.py`, `tests/test_offline_demo.py`, `tests/test_mock_kdb_demo.py`, `tests/test_cli.py`, and `tests/test_cli_behavior_snapshots.py` cover default dimensions, symbol exclusion and inclusion, custom group keys, status filtering, row limits, configured scope ordering, page rendering, metric help, missing definitions, canonical-report wiring, disabled/no-row no-op behavior, demo/CLI passthroughs, and validation. | Met |
| Production readiness requirements are documented before richer sector fixtures or live validation | `docs/production_readiness.md` documents sector taxonomy ownership/versioning, segment labels, market-cap bucket thresholds, symbol metadata joins, required kdb+ source fields, and bounded live-smoke validation gates. | Met |

**Remaining work:** Use the production-readiness checklist to confirm client
taxonomy, metadata joins, and kdb+ source schemas before adding richer
sector-specific offline fixture rows. Live production validation remains deferred
until kdb+ schemas and credentials are available.

## Later milestone: ppw packaging parity and CLI ergonomics

**Outcome:** Complete for the current package phase.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| `dev` and `doc` setup paths are documented and validated in CI or local tests | `pyproject.toml` declares the existing `dev` group and a dedicated `doc` group for MkDocs tooling; README documents `poetry install --with dev` and `poetry install --with doc`; `docs/index.md` mirrors the README demo quickstart, including `--max-drilldown-rows` and `--no-drilldown-page`; tox and CI include a docs build path; tests validate the metadata and docs text. | Met for dependency groups |
| Runtime install remains lean and does not pull documentation or development tooling unless explicitly requested | Runtime dependencies remain separate from `pytest`, formatter/type-check tooling, `mkdocs`, `mkdocs-material`, and `mkdocstrings`. | Met |
| CLI tests cover the existing `offline-demo` and `mock-kdb-demo` command behavior before and after any Typer migration | Existing render-path tests cover both demo commands; `tests/test_cli_behavior_snapshots.py` now snapshots the Typer command surface, demo command defaults, override parsing, option presence, offline/mock-kdb safety language, and the explicit `--include-intraday-heatmaps` opt-in. | Met |
| The roadmap and journal explain any new dependency added | Roadmap and journal document why the documentation dependencies live in the `doc` group, and why Typer is now a runtime dependency for the requested CLI ergonomics. | Met |

## Earliest incomplete roadmap item

The earliest incomplete milestone remains **Milestone 10**, but additional
live validation harnesses are intentionally deferred and the existing
live-kdb integration-test guidance remains the opt-in boundary. After user feedback in
iteration 62, report-local validation utilities are frozen at the current
`mmsr plan` and `mmsr preflight` scope. After iteration 67, the default
production config and example config are scoped back to the market-monitoring
report: activity, displayed liquidity, and cross-venue primary-quote reversion.
Legacy optional q-template families have been removed from active planning and schema contracts; only production default metric families remain enabled by
default. Transaction-cost templates remain outside the default market-report
scope. Iteration 69 adds `docs/report_scope.md` as the explicit scope gate for
future roadmap and implementation choices so default work stays on market
monitoring rather than transaction-cost analysis, TCA, execution quality,
price impact, venue routing, or generic validation frameworks.

## Recommended next deterministic step

Focus future iterations on report implementation rather than more validation
utilities. The next deterministic implementation step should improve the actual
market-monitoring report surface, especially the Cross-Venue Toxicity/Reversion
page and market-wide activity/liquidity summaries, using the narrowed default
metric set and the `docs/report_scope.md` gate rather than adding
transaction-cost sections.
