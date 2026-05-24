# Milestone Status Audit

This audit validates the implementation against `_docs/ROADMAP.md` as of 2026-05-24.

## Summary

| Milestone | Validation status | Result |
| --- | --- | --- |
| 1. Project skeleton and governance | Complete | Repository skeleton, governance docs, canonical `_docs/journal.md`, import, and pytest validation are present. |
| 2. Domain models | Complete | Period, bucket, metric definition, metric time-series, comparison, and commentary fact models are present and covered by tests. |
| 3. Metric registry and starter metric definitions | Complete | All roadmap starter metrics are registered and documented; tests cover lookup, docs/help text, and duplicate rejection. |
| 4. kdb/PyKX infrastructure | Complete | Lazy PyKX client, strict q-template loading/rendering validation, and kdb-backed calendar source are implemented and covered by offline tests. |
| 5. Metric execution interface | Complete | `KdbMetricRunner.run()` maps initial activity/liquidity metrics to strict q templates, executes the rendered query, and normalizes dict/list-like results into `MetricTimeSeries`. |
| 5A. Cross-venue toxicity reversion metrics | Complete under documented assumptions | Reversion definitions, strict q template, runner integration, typed toxicity config, visual placeholder, result-to-visual conversion helpers, sample-size confidence flagging, deterministic template commentary facts, reference-comparison wiring, offline input/output schema contracts, and explicit horizon sort order exist. Live production validation is deferred by user direction and no longer blocks assumption-based implementation. |
| 6. Reference comparison engine | Complete | Comparison outputs preserve current/reference values, change, confidence, optional z-scores, percentiles, adverse-tail diagnostics, and direction-aware status. |
| 7. Deterministic commentary engine | Complete | Template commentary generation exists for structured metric facts and section-level summary facts; report-section assembly now prepends alert/watch/normal status headlines without LLM dependencies. |
| 8. Report components and metric help | Complete | HTML report components render metric cards, metric tables, deterministic time-series chart placeholders, deterministic heatmap placeholders, trusted HTML blocks, and a deterministic metric definitions appendix with metric help/documentation. |
| 9. End-to-end offline demo | Complete | Deterministic synthetic metric fixtures, report assembly, the `mmsr offline-demo` HTML command path, and README quickstart instructions are present and tested. |

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
| Trading calendar data is read from a dedicated kdb calendar table | `KdbTradingCalendarSource` queries a configurable calendar table; tests assert `trading_calendar` and `is_trading_day`. | Met |
| Offline tests do not require live kdb | Current tests pass without PyKX or kdb. | Met |

## Milestone 5: Metric execution interface

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Metric runner accepts `MetricDefinition`, period, bucket spec, and group-by list | `MetricRunRequest` carries `MetricDefinition`, `ReportPeriod`, and `group_by`; `period.bucket` is rendered into the q `bucket_expr`. | Met |
| Runner returns a normalized time-series result schema | `KdbMetricRunner.run()` returns `MetricTimeSeries`; `normalize_metric_result()` converts column dictionaries and row dictionaries into `MetricObservation` rows. | Met |
| Initial q templates exist for activity and quoted spread metrics | `activity.q` and `liquidity.q` group by `date`, `time_bucket`, and requested group columns. Runner maps `turnover`, `volume`, `trade_count`, `quoted_spread_bps`, and `top_of_book_depth` to those templates. | Met |
| Integration tests can be marked/skipped without kdb connection | `pyproject.toml` registers the `kdb_integration` marker and `tests/test_kdb_metric_runner.py` contains a skipped live-kdb placeholder. | Met |

## Milestone 5A: Cross-venue toxicity reversion metrics

**Outcome:** Complete under documented assumptions.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Metric definitions exist for each configured horizon | Six reversion metrics are registered. | Met |
| q template exists for primary-quote reversion calculation | `toxicity_reversion.q` is now a strict renderable template with placeholders for venue trades, primary quotes, date/time filters, venue filters, horizon, horizon sort order, max primary quote age, bucket expression, value column, and group columns. `toxicity_reversion_input_schema_contracts()` defines required venue-trade and primary-quote source columns; `toxicity_reversion_output_schema_contract()` defines the required report-boundary output columns offline. | Met under documented source/output schema assumptions. |
| Runner maps reversion metrics to the q template | `KdbMetricRunner` maps `primary_quote_reversion_*_bps` to `toxicity_reversion.q`, renders horizon/venue/primary-venue parameters, validates the reversion output schema contract, and normalizes `venue`/`horizon` dimensions into `MetricTimeSeries`. | Met |
| Config supports venues, primary venue, horizons, side source, clustering, stale quote filters, and confidence thresholds | `ToxicityConfig` and nested typed config models expose venues, primary venue, horizons, side source, clustering, stale-quote filters, and confidence thresholds. `ReportConfig.metric_parameters_for()` translates reversion settings into `MetricRunRequest.parameters`. | Met |
| Visual placeholder or production visual supports venue reversion curves | `render_reversion_curve_placeholder()` and deterministic `MetricTimeSeries`-to-`ReversionCurvePoint` conversion helpers exist and are tested. Low-confidence rows are surfaced in the placeholder table, and horizon progression can use the explicit q-output `horizon_sort_order`. | Met |
| Tests verify metric registration and basic visual rendering | `tests/test_toxicity_reversion.py` covers registration, placeholder rendering, point conversion, and confidence flagging; `tests/test_kdb_metric_runner.py` covers runner integration. | Met |
| Terminology uses `reversion` consistently | User-facing labels use `+... Reversion`; visual uses `Reversion (bps)`. | Met |
| Deterministic commentary supports reversion results | `reversion_commentary_facts_from_curve_points()` converts curve points into grounded `CommentaryFact` objects for headline positive reversion and low-confidence warnings without LLM dependencies. | Met |
| Reference comparison supports reversion results | `compare_reversion_metric_timeseries()` delegates to `compare_metric_timeseries`, compares venue/horizon/report-group histories with one observation per trading day by default, and forces `higher_is_better=False` for the reversion metric family. | Met |
| Offline output-schema contract documents reversion template outputs | `mmsr.kdb.schema_contracts` defines the required `toxicity_reversion.q` output columns: `date`, `time_bucket`, `venue`, `horizon`, the dynamic metric value column, `horizon_sort_order`, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`, plus requested report groups. | Met |
| Offline input-schema contract documents production source-table assumptions | `toxicity_reversion_input_schema_contracts()` defines required venue-trade columns (`date`, `time`, `sym`, `venue`, `trade_price`, `trade_size`, `aggressor_side`) and primary-quote columns (`date`, `time`, `sym`, `venue`, `bid_price`, `ask_price`), including assumptions for side and quote price conventions. | Met |
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
| HTML renderer includes info/help icons or expandable metric docs | Metric cards, metric tables, time-series chart placeholders, heatmap placeholders, trusted HTML blocks, and metric definitions appendix blocks render `metric-info` controls or inline expandable definitions backed by metric/help text. | Met |
| Excel/static renderers can include a metric definitions sheet or appendix placeholder | `metric_definitions_markdown()` renders complete deterministic definition text, and `build_metric_definitions_appendix_page()` / `append_metric_definitions_appendix()` add an HTML/static appendix page from the metric definitions used by report-page cards, metric-table rows, time-series charts, and heatmaps. | Met |
| Tests verify metric help is included | HTML rendering, report-section, metric-table, time-series chart, heatmap, and metric-doc tests assert that metric help/info controls and appendix definition fields are included. | Met |
| Initial report component set exists | Metric card, metric table, deterministic time-series chart placeholder, deterministic heatmap placeholder, commentary block, trusted HTML block, and metric definitions appendix exist. | Met |

## Milestone 9: End-to-end offline demo

**Outcome:** Complete.

| Exit criterion | Evidence | Status |
| --- | --- | --- |
| Example config or command runs locally | The `mmsr offline-demo --output <path>` command renders deterministic synthetic HTML through `build_offline_demo_report()` and `render_report()` without kdb/PyKX or LLM calls; tests cover file output, custom text, appendix omission, and validation. | Met |
| Synthetic metric results flow through comparison, commentary, and HTML report rendering | `mmsr.examples.offline_fixtures` builds deterministic synthetic current/reference `MetricTimeSeries` objects and precomputed `MetricComparison` rows; `mmsr.examples.offline_demo.build_offline_demo_report()` assembles them into a `ReportDocument` with metric cards, comparison table, deterministic commentary, time-series/heatmap placeholders, and a metric definitions appendix; tests render the document to HTML. | Met |
| README includes quickstart | README documents `poetry run mmsr offline-demo --output reports/offline_demo.html`, describes the synthetic normalized metrics, and states that the demo does not query kdb+, import PyKX, call an LLM, or use real market data; tests cover the quickstart text. | Met |

## Earliest incomplete roadmap item

The earliest incomplete milestone is **Milestone 10** because the offline demo is complete, while a real or mock kdb integration demo and documented integration validation remain incomplete.

## Recommended next deterministic step

Add a deterministic mock-kdb integration example that exercises an existing q template through `KdbMetricRunner`, validates the normalized result, and documents the live-kdb boundary.
