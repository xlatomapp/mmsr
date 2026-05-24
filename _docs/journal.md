# Implementation Journal

This file must be updated after every implementation step.

## 2026-05-24 — Initial skeleton draft

### Implemented

- Created ppw-style project skeleton for `mmsr`.
- Added governance docs under `_docs/`.
- Added roadmap with deterministic milestones.
- Added initial package modules for config, periods, metrics, kdb, analysis, report, visuals, and optional LLM support.
- Added starter tests for package import and metric registry behavior.

### Files changed

- `_docs/AGENTS.md`
- `_docs/ROADMAP.md`
- `journal.md`
- `pyproject.toml`
- `README.md`
- `mmsr/**`
- `tests/**`
- `config/report.example.yaml`

### Validation

- Skeleton was created as a reviewable starting point.
- Tests are included but have not been run in the target project environment.

### Current milestone

- Milestone 1: Project skeleton and governance

### Estimated milestone completion

- 70%

### Remaining work before milestone completion

- Review and confirm package name.
- Generate actual repository using `ppw` if desired, then copy these project-specific files into the generated project.
- Confirm whether package should use `pandas`, `polars`, or only PyKX objects at the first report boundary.
- Run tests in the local development environment.

### Best next deterministic step

- Review `_docs/AGENTS.md` and `_docs/ROADMAP.md`, then finalize the initial domain models for `ReportPeriod`, `TradingSession`, `IntradayBucketSpec`, `MetricDefinition`, and `MetricTimeSeries`.

### Open questions

- What are the exact kdb table names and schemas for trades, quotes, and symbol metadata?
- Which visualization backend should be the default for HTML reports: Plotly, matplotlib, or static SVG/table-first HTML?
- Should the first renderer target be HTML only, or HTML plus Excel?

---

## 2026-05-24 — Skeleton revision for mmsr naming and HTML templates

### Implemented

- Renamed the repository/package target to `mmsr`.
- Moved Custom GPT instructions into `_docs/CUSTOM_GPT_INSTRUCTIONS.md`.
- Updated Python target support to 3.12 and 3.13.
- Added a stable Jinja-based HTML report template system.
- Added configurable report branding fields for brand name, logo image, header image, footer image, and footer text.

### Files changed

- `pyproject.toml`
- `tox.ini`
- `mypy.ini`
- `README.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/AGENTS.md`
- `_docs/ROADMAP.md`
- `config/report.example.yaml`
- `mmsr/config/models.py`
- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/templates/**`
- `tests/test_config_models.py`
- `tests/test_html_rendering.py`

### Validation

- Ran `python -m pytest` successfully after generating this revision.

### Milestone progress

- Milestone 1: 85% complete.

### Remaining before milestone complete

- Review the governance docs and confirm naming, milestone wording, and package boundaries.

### Best next deterministic step

- Finalize `_docs/AGENTS.md` and `_docs/ROADMAP.md`, then start Milestone 2 by hardening domain models and tests.

---

## 2026-05-24 — Replace dashboard performance terminology with metric terminology

### Implemented

- Reviewed the project scaffold for legacy dashboard performance terminology.
- Replaced the remaining dashboard performance wording with generic metric terminology.
- Updated the report component docstring to describe a metric card.
- Updated the roadmap to list a metric card as the initial report component.

### Files changed

- `_docs/ROADMAP.md`
- `mmsr/report/components.py`
- `journal.md`

### Validation

- Confirmed there are no remaining occurrences of the legacy dashboard performance wording in the scaffold.
- Ran `python -m pytest` successfully.

### Milestone progress

- Milestone 1: 88% complete.

### Remaining before milestone complete

- Review and finalize governance language in `_docs/AGENTS.md` and `_docs/ROADMAP.md`.
- Confirm exact kdb table names and field conventions for trades, quotes, and symbol metadata.

### Best next deterministic step

- Finalize the milestone wording in `_docs/ROADMAP.md`, then begin Milestone 2 by hardening the period, bucket, metric definition, and metric result domain models.

### Open questions

- Should the user-facing report consistently use the word `metric`, or should some higher-level dashboard summaries use `indicator`?

## 2026-05-24 - Add cross-venue toxicity reversion roadmap and CI

### Implemented

- Added cross-venue toxicity reversion metric definitions using the requested `reversion` terminology.
- Added horizon-specific metric labels: `+10ms Reversion`, `+100ms Reversion`, `+500ms Reversion`, `+1s Reversion`, `+5s Reversion`, and `+10s Reversion`.
- Added a pseudo-q template for primary-quote reversion calculation against the primary exchange quote.
- Added a deterministic HTML placeholder for the venue reversion curve visual: x-axis horizon progression, y-axis reversion in bps, series by venue.
- Added toxicity/reversion configuration to the example report config.
- Added a GitHub Actions CI workflow that runs tests on Python 3.12 and 3.13 without PyPI publishing.
- Added `.gitignore` for Python caches, build outputs, virtual environments, and local report outputs.
- Updated agent instructions so every implementation step must end with a git commit after validation and journal update.

### Files changed

- `.github/workflows/ci.yml`
- `.gitignore`
- `_docs/AGENTS.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/ROADMAP.md`
- `README.md`
- `config/report.example.yaml`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `mmsr/metrics/starter_definitions.py`
- `mmsr/visuals/toxicity.py`
- `tests/test_toxicity_reversion.py`
- `journal.md`

### Tests added or updated

- Added tests for primary-quote reversion metric registration.
- Added tests for the venue reversion curve HTML placeholder.

### Validation

- `python -m pytest -q` passed with 14 tests.

### Current milestone

Milestone 3: Metric registry and starter metric definitions, plus new Milestone 5A: Cross-venue toxicity reversion metrics.

### Estimated milestone progress

- Milestone 3: 85% complete.
- Milestone 5A: 30% complete.

### Remaining work

- Implement concrete q logic for `toxicity_reversion.q` after production schemas are confirmed.
- Add normalized result models for venue/horizon reversion series.
- Add production chart renderer for the venue reversion curve.
- Add reference comparison and template commentary for reversion results.

### Best next deterministic step

Define the normalized result schema for toxicity reversion outputs, including `venue`, `horizon`, `reversion_bps`, `trade_count`, `notional`, and confidence flags.

### Open questions

- Confirm exact venue trade schema and whether aggressor side is provided by the feed or inferred.
- Confirm primary quote table naming and whether TSE quote is represented as a venue field or a separate table.

---

## 2026-05-24 - Add auction-aware bucket grid, kdb calendar source, and comparison guidance

### Implemented

- Added `TimeBucket` and `AuctionBucketLabels` domain models.
- Added `build_intraday_bucket_grid` to create deterministic intraday bucket grids with explicit auction rows such as `AMO`, `AMC`, `PMO`, and `PMC`.
- Added numeric `sort_order` to every bucket row so reports can render buckets in true trading order instead of lexicographic order.
- Added `KdbTradingCalendarSource` so production trading days come from a dedicated kdb calendar table.
- Kept `weekdays_between` only as an offline fixture/helper with documentation that production code should not rely on weekday assumptions.
- Added comparison utilities for standard and robust z-scores over comparable historical aggregated observations.
- Documented that z-scores are anomaly scores, not a theoretical claim that metrics such as quoted spread are normally distributed.
- Updated example config to include kdb calendar settings and auction bucket settings.

### Files changed

- `_docs/AGENTS.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/ROADMAP.md`
- `README.md`
- `config/report.example.yaml`
- `journal.md`
- `mmsr/analysis/comparison.py`
- `mmsr/config/models.py`
- `mmsr/kdb/q_templates/trading_calendar.q`
- `mmsr/periods/__init__.py`
- `mmsr/periods/buckets.py`
- `mmsr/periods/calendar.py`
- `mmsr/periods/models.py`
- `tests/test_calendar.py`
- `tests/test_comparison.py`
- `tests/test_config_models.py`
- `tests/test_periods.py`

### Tests added or updated

- Added tests for auction-aware bucket grid labels and sort order.
- Added tests for kdb-backed trading calendar query construction using a fake client.
- Added tests for standard z-score, robust median/MAD z-score, and reference distribution comparison.
- Updated config tests for calendar and auction bucket defaults.

### Validation

- `python -m pytest -q` passed with 22 tests.
- `python -m compileall -q mmsr tests` passed.
- `grep -RIn "KPI\|key performance" .` returned no matches.
- `python -m black --check .` could not be run in this environment because Black is not installed.

### Current milestone

Milestone 2: Domain models, Milestone 4: kdb/PyKX infrastructure, and Milestone 6: Reference comparison engine.

### Estimated milestone progress

- Milestone 2: 65% complete.
- Milestone 4: 45% complete.
- Milestone 6: 35% complete.

### Remaining work

- Add serialization helpers for bucket grids if required by kdb query templates.
- Confirm production kdb calendar table schema and date types.
- Implement reference comparison over full metric time-series tables, not just scalar helper functions.
- Add percentile-rank calculation once the canonical result table shape is finalized.

### Best next deterministic step

Define the normalized `MetricTimeSeries` table schema and implement a comparison function that groups by metric, date, time bucket, venue, horizon, and report group columns before calculating reference statistics.

### Git commit

- Local scaffold commit created with message: `Update bucket grid calendar and comparison guidance`.

### Open questions

- Confirm whether auction bucket labels should always be `AMO`, `AMC`, `PMO`, `PMC`, or whether they should be configurable per exchange/venue.
- Confirm production calendar table name and whether half-day or special-session metadata is available.

---

## 2026-05-24 - Add reference observation-unit policy and small-sample comparison behavior

### Implemented

- Added explicit reference observation-unit modeling for comparison policy.
- Clarified that the default reference observation unit is `trading_day`, so raw quote/trade observations should be aggregated to one comparable value per date and key set before statistical scoring.
- Added `ComparisonPolicy` and `ReferenceObservationSpec` to control minimum sample sizes, comparable keys, and fallback behavior.
- Updated comparison utilities so z-scores are not produced by default when the reference distribution has fewer than 30 comparable observations.
- Added one-observation behavior: current-vs-reference change only, with no z-score.
- Added weak-history behavior for fewer than 30 observations: empirical percentile, adverse-tail estimate, range position, and low-confidence message where possible.
- Added normal-score percentile and normal approximation adverse-tail probability for cases where a z-score is available.
- Made adverse-tail probability direction-aware using the metric's `higher_is_better` semantics.
- Extended `MetricComparison` with optional fields for sample size, comparison confidence, comparison method, normal-score percentile, empirical percentile, adverse-tail probabilities, and range-position score.
- Updated config models and example config with reference comparison policy settings.
- Updated docs to explain that z-score-to-probability conversion should be labelled as normal-score percentile or normal approximation tail probability, not a literal probability.

### Files changed

- `_docs/AGENTS.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/ROADMAP.md`
- `README.md`
- `config/report.example.yaml`
- `journal.md`
- `mmsr/analysis/comparison.py`
- `mmsr/config/models.py`
- `mmsr/metrics/results.py`
- `mmsr/periods/__init__.py`
- `mmsr/periods/reference.py`
- `tests/test_comparison.py`
- `tests/test_config_models.py`

### Tests added or updated

- Added tests for one-reference-observation behavior.
- Added tests for short reference windows that produce empirical rank but no headline z-score.
- Added tests for normal-score percentile and adverse-tail probability when the sample threshold is met.
- Added tests for direction-aware adverse-tail calculation.
- Added tests for reference observation spec and comparison policy validation.
- Added config tests for reference comparison defaults and validation.

### Validation

- `python -m pytest -q` passed with 29 tests.
- `python -m compileall -q mmsr tests` passed.

### Current milestone

Milestone 6: Reference comparison engine.

### Estimated milestone progress

Milestone 6 is approximately 55% complete.

### Remaining work

- Implement comparison over normalized metric time-series tables rather than scalar helper functions only.
- Wire metric definitions' `higher_is_better` field into comparison calls automatically.
- Add rendering logic that chooses user-facing fields based on `comparison_confidence`.
- Add technical appendix output for z-score, normal-score percentile, and sample-size diagnostics.
- Add kdb-side aggregation templates that produce one row per configured reference observation unit.

### Best next deterministic step

Implement a `compare_metric_timeseries` function that groups normalized metric observations by comparable keys, builds one reference distribution per current observation, and applies `ComparisonPolicy` consistently.

### Git commit

- Local scaffold commit to be created with message: `Add reference comparison policy`.

### Open questions

- Confirm whether 30 comparable observations should remain the default threshold for all metrics or whether some metrics should override it.
- Confirm whether the main report should prefer empirical percentile, normal-score percentile, or range-position score as the default displayed indicator.

---

## 2026-05-24 - Add normalized metric time-series comparison

### Implemented

- Reviewed `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `journal.md` before changing code.
- Added `compare_metric_timeseries` for normalized current and reference metric observations.
- Matched current observations to comparable history using `ComparisonPolicy.reference_observation.comparable_keys`, defaulting to `metric_name`, `time_bucket`, and the full group key.
- Collapsed reference rows to one value per configured reference observation unit, defaulting to one `trading_day`, before calculating comparison statistics.
- Preserved current observation `date`, `time_bucket`, group, and comparison metadata in `MetricComparison`.
- Allowed auction bucket labels such as `AMO` to be carried in `MetricObservation.time_bucket`.

### Files changed

- `mmsr/analysis/comparison.py`
- `mmsr/metrics/results.py`
- `tests/test_comparison.py`
- `journal.md`

### Tests added or updated

- Added tests for time-series comparison by metric, bucket, and group.
- Added tests that keep venue and horizon histories separate for reversion-style outputs.
- Added tests that duplicate rows within one trading day count as one reference observation after deterministic aggregation.

### Validation

- `python -m pytest -q` passed with 32 tests.
- `python -m compileall -q mmsr tests` passed.
- `python -m mypy mmsr tests` could not be run because `mypy` is not installed in this environment.
- The Python startup emitted an unrelated spreadsheet runtime warmup warning from the environment, but the pytest and compileall commands returned success.

### Current milestone

Milestone 6: Reference comparison engine.

### Estimated milestone progress

Milestone 6 is approximately 65% complete.

### Remaining work

- Wire registered metric definitions' `higher_is_better` field into time-series comparison automatically.
- Add rendering logic that chooses user-facing comparison fields based on `comparison_confidence`.
- Add technical appendix output for z-score, normal-score percentile, empirical percentile, and sample-size diagnostics.
- Add kdb-side aggregation templates that produce one row per configured reference observation unit.

### Best next deterministic step

Wire `MetricDefinition.higher_is_better` into `compare_metric_timeseries` through a small helper that accepts metric definitions or a registry and derives the direction mapping automatically.

### Git commit

- Local scaffold commit to be created with message: `Add metric timeseries comparison`.

### Open questions

- Confirm whether duplicate normalized reference rows within one trading day should default to `mean`, `median`, or metric-specific aggregation once kdb metric outputs are finalized.
---

## 2026-05-24 — Move journal under docs and audit roadmap status

### Implemented

- Moved the canonical implementation journal from `journal.md` to `_docs/journal.md`.
- Updated governance docs, the local custom GPT instructions copy, README, and roadmap references to use `_docs/journal.md`.
- Added `_docs/MILESTONE_STATUS.md` with a milestone-by-milestone validation audit for Milestones 1 through 5A.
- Added governance tests to ensure the journal remains under `_docs` and documented references point to the canonical path.

### Files changed

- `_docs/journal.md`
- `_docs/AGENTS.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `README.md`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added `tests/test_docs_governance.py`.

### Validation performed

- Ran `python -m pytest -q`: passed with 34 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m zipfile -t /mnt/data/mmsr_phase5_iteration12.zip`: passed after packaging.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning before the validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 2: Domain models.

### Current milestone progress

- 85%.

### Validation outcome for previous milestones

- Milestone 1 is complete against the current roadmap exit criteria.
- Milestone 2 is partial because `MetricTimeSeries` is missing as a first-class domain model.
- Milestone 3 is complete against the current roadmap exit criteria.
- Milestone 4 is partial because q-template rendering does not yet validate required parameters and direct template-loader tests are missing.
- Milestone 5 is not complete because `KdbMetricRunner.run()` is still a placeholder and no normalized runner result is returned.
- Milestone 5A is partial because reversion definitions and visual placeholder exist, but the q template is still pseudo-q and not wired into the runner.

### Remaining work before milestone completion

- Implement the first-class `MetricTimeSeries` domain model.
- Expose it through the metrics package public API.
- Add tests for consistent metric names, date/time bucket preservation, group key preservation, and observation ordering.

### Best next deterministic step

- Implement `MetricTimeSeries` in `mmsr/metrics/results.py` and add tests for its validation behavior.

### Open questions

- Should `MetricTimeSeries` store observations as a Python tuple of `MetricObservation` objects only, or should it also provide dataframe adapters later for PyKX/pandas/polars boundaries?

---

## 2026-05-24 — Add MetricTimeSeries domain model

### Implemented

- Added `MetricTimeSeries` as a first-class domain model for ordered normalized metric observations.
- Added validation that all observations in a series share the same `metric_name`.
- Added `MetricTimeSeries.from_observations()` for deterministic construction and metric-name inference.
- Added convenience accessors for observation dates, time buckets, and values in stored order.
- Exposed `MetricObservation`, `MetricComparison`, and `MetricTimeSeries` through the `mmsr.metrics` public API.
- Updated `_docs/MILESTONE_STATUS.md` to mark Milestone 2 complete and identify Milestone 4 as the earliest incomplete roadmap item.

### Files changed

- `mmsr/metrics/results.py`
- `mmsr/metrics/__init__.py`
- `tests/test_metric_timeseries.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added `tests/test_metric_timeseries.py` covering construction, metric-name inference, inconsistent metric-name rejection, empty-series handling, date/time bucket preservation, group preservation, and observation-order preservation.

### Validation performed

- Ran `python -m pytest -q`: passed with 39 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning before the validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 2: Domain models.

### Current milestone progress

- 100%.

### Milestone completion assessment

- Milestone 2 is complete against the current roadmap exit criteria.
- The earliest incomplete roadmap item is now Milestone 4: kdb/PyKX infrastructure.

### Remaining work before milestone completion

- None for Milestone 2 under the current roadmap exit criteria.

### Best next deterministic step

- Implement strict q-template rendering validation in `mmsr/kdb/query_loader.py` and add offline tests for template loading plus missing/unused parameter behavior.

### Package phase and iteration

- Phase: 2.
- Iteration: 1.
- Delivery archive name: `mmsr_phase2_iteration1.zip`.

### Open questions

- Should `MetricTimeSeries` later provide dataframe/PyKX table adapters at the report boundary, or should adapters live in separate boundary modules?


---

## 2026-05-24 — Phase 4 iteration 1: strict q-template validation

### Implemented

- Completed the Milestone 4 q-template infrastructure step.
- Added strict `QueryTemplateError` handling for deterministic q template rendering.
- Added `template_parameters()` to extract and validate explicit `{{ name }}` placeholders.
- Hardened `load_q_template()` so only simple `.q` filenames can be loaded from package resources.
- Updated q-template comments to avoid documentation-only mustache placeholders being treated as required render parameters.
- Added offline tests for q-template loading, missing template handling, placeholder extraction, malformed placeholders, missing parameters, unused parameters, invalid parameter names, non-string values, packaged activity template parameters, and KdbClient construction without PyKX.

### Files changed

- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/q_templates/activity.q`
- `mmsr/kdb/q_templates/liquidity.q`
- `mmsr/kdb/q_templates/trading_calendar.q`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `tests/test_kdb_query_loader.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added `tests/test_kdb_query_loader.py`.

### Validation

- `python -m pytest -q` passed with 50 tests.
- `python -m compileall -q mmsr tests` passed.
- `python -m mypy mmsr tests` could not be run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 4: kdb/PyKX infrastructure.

### Estimated milestone completion

- 100%.

### Remaining work before milestone completion

- None for the current roadmap exit criteria.

### Best next deterministic step

- Start Milestone 5 by replacing the `KdbMetricRunner.run()` placeholder with a deterministic request-to-template mapping for the initial activity and liquidity metrics that renders validated q and normalizes dict/list-like kdb results into `MetricTimeSeries`.

### Package phase and iteration

- Phase: 4.
- Iteration: 1.
- Delivery archive name: `mmsr_phase4_iteration1.zip`.

### Open questions

- What are the exact production kdb table names and schemas for trades, quotes, and symbol metadata?
- Should the first runner implementation return only metric values from q templates, or should q templates already emit all normalization fields (`metric_name`, `date`, `time_bucket`, and group columns)?


---

## 2026-05-24 — Phase 5 iteration 1: kdb metric runner normalization

### Implemented

- Started and completed the Milestone 5 metric execution interface step.
- Replaced the `KdbMetricRunner.run()` placeholder with deterministic request-to-template execution for initial activity and liquidity metrics.
- Added `template_for_metric()` mapping for `turnover`, `volume`, `trade_count`, `quoted_spread_bps`, and `top_of_book_depth`.
- Added strict query rendering through packaged q templates, including date filters, session time filters, intraday bucket expressions, and requested group-by suffixes.
- Updated `activity.q` and `liquidity.q` to emit time-series rows grouped by `date`, `time_bucket`, and requested group columns.
- Added `normalize_metric_result()` to convert dict/list-like kdb results, including PyKX-like objects with `.py()`, into `MetricTimeSeries`.
- Added runner errors for unsupported metrics, missing table mappings, invalid group columns, missing value/date/group fields, non-numeric metric values, and mismatched column lengths.
- Added a registered `kdb_integration` pytest marker and a skipped live-kdb placeholder test so integration tests can remain outside the offline suite.
- Updated `_docs/MILESTONE_STATUS.md` to mark Milestone 5 complete and identify Milestone 5A as the earliest incomplete roadmap item.

### Files changed

- `mmsr/kdb/runner.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/q_templates/activity.q`
- `mmsr/kdb/q_templates/liquidity.q`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_import.py`
- `pyproject.toml`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added `tests/test_kdb_metric_runner.py`.
- Updated `tests/test_kdb_query_loader.py` for the new `bucket_expr` template parameter.
- Added tests for public kdb runner API exports, metric-to-template mapping, activity query rendering, liquidity query rendering, normalized column-dictionary results, normalized row-dictionary results, metadata preservation, unsupported metrics, missing table mappings, invalid group identifiers, missing metric/group fields, mismatched column lengths, and the skipped live-kdb integration marker.

### Validation performed

- Ran `python -m pytest -q`: passed with 63 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 64 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 5: Metric execution interface.

### Current milestone progress

- 100%.

### Milestone completion assessment

- Milestone 5 is complete against the current roadmap exit criteria.
- The earliest incomplete roadmap item is now Milestone 5A: Cross-venue toxicity reversion metrics.

### Remaining work before milestone completion

- None for Milestone 5 under the current roadmap exit criteria.

### Best next deterministic step

- Start Milestone 5A runner integration by mapping the `primary_quote_reversion_*_bps` metric family to `toxicity_reversion.q`, rendering horizon/venue/primary-venue parameters, and normalizing venue/horizon result rows into `MetricTimeSeries`.

### Package phase and iteration

- Phase: 5.
- Iteration: 1.
- Delivery archive name: `mmsr_phase5_iteration1.zip`.

### Open questions

- What are the exact production kdb table names and schemas for trades, quotes, and symbol metadata?
- Should q templates emit `time_bucket` as a q temporal value, an auction/continuous label string, or both a label and numeric `sort_order` for downstream rendering?
- Should `quoted_spread_ticks` be supported by the initial liquidity template once the symbol/tick-size join convention is confirmed?


---

## 2026-05-24 — Phase 5 iteration 2: reversion runner integration

### Implemented

- Continued Milestone 5A by wiring the cross-venue primary-quote reversion metric family into `KdbMetricRunner`.
- Added deterministic mapping from all `primary_quote_reversion_*_bps` metrics to `toxicity_reversion.q`.
- Extended `MetricRunRequest` with optional metric-family parameters for `primary_venue`, `venues`, and `max_primary_quote_age`.
- Rendered reversion-specific q parameters for metric value column, primary venue, venue filter, parsed horizon duration, horizon label, and stale-primary-quote age.
- Normalized reversion result rows with `venue` and `horizon` as required group dimensions, preserving requested group columns such as `sym`.
- Replaced the previous pseudo-q outline with a strict renderable `toxicity_reversion.q` template that uses placeholders validated by the q template renderer.
- Updated milestone audit status to reflect that runner integration is complete while typed toxicity configuration and live q validation remain open.

### Files changed

- `mmsr/kdb/runner.py`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Updated metric-to-template tests to include reversion metrics.
- Added a fake-kdb runner test that renders a reversion query, checks venue/primary-venue/horizon parameters, and verifies normalized `venue`/`horizon`/`sym` grouping.
- Added a test that reversion metrics require venue parameters before query execution.
- Added a q-template parameter test for `toxicity_reversion.q`.

### Validation performed

- Ran `python -m pytest -q`: passed with 66 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 67 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 60%.

### Remaining work before milestone completion

- Add first-class typed `ToxicityConfig` models and tests.
- Add a deterministic request-builder path from report configuration to `MetricRunRequest.parameters`.
- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add result-to-visual conversion helpers for venue reversion curves if the report layer should consume `MetricTimeSeries` directly.
- Add reference comparison and template commentary for reversion results.

### Best next deterministic step

- Add typed `ToxicityConfig` models to `mmsr.config.models` for primary venue, venues, horizons, side source, event clustering, stale quote filters, and confidence thresholds, then test how those settings populate `MetricRunRequest.parameters`.

### Package phase and iteration

- Phase: 5.
- Iteration: 2.
- Delivery archive name: `mmsr_phase5_iteration2.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering?


---

## 2026-05-24 — Phase 5 iteration 3: typed toxicity configuration

### Implemented

- Continued Milestone 5A by adding first-class typed configuration for the cross-venue toxicity/reversion section.
- Added `ToxicityConfig` with default section title, primary venue, venues, reversion horizons, side source, default visual, event clustering, stale-primary-quote filters, and confidence thresholds.
- Added nested typed models for the reversion curve visual, event clustering, filters, and confidence thresholds.
- Added duration, side-source, primary-venue, venue-list, horizon-list, and confidence-threshold validation.
- Added `ToxicityConfig.to_metric_run_parameters()` so report configuration can deterministically populate `MetricRunRequest.parameters`.
- Added `ReportConfig.metric_parameters_for()` so reversion metrics receive toxicity parameters while unrelated metrics receive an empty parameter map.
- Updated the reversion runner test to use parameters generated from `ReportConfig`.
- Exported the config model API from `mmsr.config`.
- Updated `_docs/MILESTONE_STATUS.md` to mark typed toxicity configuration complete and identify result-to-visual conversion as the next deterministic step.

### Files changed

- `mmsr/config/models.py`
- `mmsr/config/__init__.py`
- `tests/test_config_models.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for default toxicity configuration values.
- Added validation tests for invalid horizons, side sources, primary venue membership, stale quote age, clustering windows, and confidence thresholds.
- Added a test that converts toxicity settings into `MetricRunRequest.parameters`.
- Updated the reversion runner test to render `toxicity_reversion.q` using config-generated parameters.
- Added a public config API import test.

### Validation performed

- Ran `python -m pytest -q`: passed with 71 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 72 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 75%.

### Remaining work before milestone completion

- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add deterministic result-to-visual conversion from `MetricTimeSeries` rows to ordered venue reversion curve points.
- Add reference comparison and template commentary for reversion results.
- Decide whether the q template should emit numeric horizon sort order in addition to the horizon label.

### Best next deterministic step

- Add a deterministic result-to-visual conversion helper that converts `MetricTimeSeries` rows with `venue` and `horizon` groups into ordered `ReversionCurvePoint` values for the cross-venue toxicity visual.

### Package phase and iteration

- Phase: 5.
- Iteration: 3.
- Delivery archive name: `mmsr_phase5_iteration3.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering?

## 2026-05-24 — Phase 5 iteration 4: reversion curve point conversion

### Implemented

- Continued Milestone 5A by adding deterministic conversion from normalized reversion `MetricTimeSeries` observations into `ReversionCurvePoint` values.
- Extended `ReversionCurvePoint` compatibly with optional observation context: date, time bucket, non-visual groups, trade count, notional, and low-confidence metadata.
- Added strict validation that every converted observation includes `venue` and `horizon` group dimensions and a numeric reversion value.
- Added natural duration sorting for horizons such as `10ms`, `100ms`, and `1s`, with optional explicit venue and horizon order overrides.
- Added a collection helper so separate horizon-specific metric series can be combined into one ordered venue reversion curve.
- Updated the deterministic HTML placeholder to accept any sequence of curve points and escape text values.
- Exported the toxicity visual helper API through `mmsr.visuals`.
- Updated `_docs/MILESTONE_STATUS.md` to mark result-to-visual conversion complete.

### Files changed

- `mmsr/visuals/toxicity.py`
- `mmsr/visuals/__init__.py`
- `tests/test_toxicity_reversion.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for converting unordered `MetricTimeSeries` observations into horizon-ordered `ReversionCurvePoint` values.
- Added tests for combining horizon-specific metric series into one ordered point collection.
- Added validation tests for missing `horizon`/`venue` groups and missing metric values.
- Updated existing reversion visual tests to cover the expanded point model.
- Added a public visual API import test.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion.py -q`: passed with 6 tests.
- Ran `python -m pytest -q`: passed with 77 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 78 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 85%.

### Remaining work before milestone completion

- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add deterministic sample-size confidence flagging for reversion curve points using configured trade-count and notional thresholds.
- Add reference comparison and template commentary for reversion results.
- Decide whether the q template should emit both `horizon` label and numeric horizon sort order for downstream rendering, or whether Python-side duration sorting is sufficient.

### Best next deterministic step

- Add deterministic sample-size confidence flagging for reversion curve points using `ToxicityConfidenceConfig` thresholds, then surface low-confidence rows in the placeholder visual.

### Package phase and iteration

- Phase: 5.
- Iteration: 4.
- Delivery archive name: `mmsr_phase5_iteration4.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?


---

## 2026-05-24 — Phase 5 iteration 5: reversion confidence flagging

### Implemented

- Continued Milestone 5A by adding deterministic sample-size confidence flagging for reversion curve points.
- Added `flag_reversion_curve_confidence()` to apply configured `ToxicityConfidenceConfig` thresholds to existing points.
- Extended `ReversionCurvePoint` with `confidence_reasons` so low-confidence decisions can be surfaced without recalculating policy in the renderer.
- Added optional confidence threshold application to both single-series and collection-based `MetricTimeSeries` conversion helpers.
- Updated the deterministic HTML placeholder to include a confidence column and mark low-confidence rows with a stable `low-confidence` CSS class.
- Exported the confidence flagging helper through `mmsr.visuals`.
- Updated `_docs/MILESTONE_STATUS.md` to record confidence flagging progress and the next deterministic step.

### Files changed

- `mmsr/visuals/toxicity.py`
- `mmsr/visuals/__init__.py`
- `tests/test_toxicity_reversion.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests that apply `ToxicityConfidenceConfig` thresholds during reversion point conversion.
- Added tests that missing sample-size metadata is flagged as low confidence.
- Added a test that upstream low-confidence markers are preserved even when configured thresholds pass.
- Added a placeholder-rendering test for low-confidence row classes and escaped confidence text.
- Updated the public visual API import test for the exported confidence helper.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion.py -q`: passed with 10 tests.
- Ran `python -m pytest -q`: passed with 80 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 81 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted an unrelated spreadsheet runtime warmup warning during Python startup, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 90%.

### Remaining work before milestone completion

- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add deterministic template commentary for reversion curve headlines and low-confidence warnings.
- Add reference comparison support for reversion results when the comparison engine is connected to report sections.

### Best next deterministic step

- Add deterministic reversion commentary facts for headline venue/horizon movements and low-confidence warnings, using the existing template commentary path without LLM dependencies.

### Package phase and iteration

- Phase: 5.
- Iteration: 5.
- Delivery archive name: `mmsr_phase5_iteration5.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?

---

## 2026-05-24 — Phase 5 iteration 6: reversion template commentary facts

### Implemented

- Continued Milestone 5A by adding deterministic template-commentary facts for cross-venue primary-quote reversion curves.
- Added `reversion_commentary_facts_from_curve_points()` to generate grounded `CommentaryFact` objects for headline positive reversion by venue/horizon and low-confidence sample-size warnings.
- Preserved the existing non-LLM `TemplateCommentaryEngine` path and extended it to include grounded caveats, such as low-confidence reasons, in rendered comments.
- Exported the analysis commentary API and the reversion commentary helper through package public APIs.
- Updated `_docs/MILESTONE_STATUS.md` to record deterministic reversion commentary progress and identify reference-comparison wiring as the next deterministic step.

### Files changed

- `mmsr/analysis/__init__.py`
- `mmsr/analysis/commentary.py`
- `mmsr/visuals/__init__.py`
- `mmsr/visuals/toxicity.py`
- `tests/test_commentary.py`
- `tests/test_import.py`
- `tests/test_toxicity_reversion.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for reversion commentary headline selection, status assignment, value formatting, and group preservation.
- Added tests for low-confidence caveats and non-headline low-confidence warning facts.
- Added tests for commentary threshold validation.
- Added tests that the template commentary engine includes grounded caveats.
- Updated public API import tests for analysis and visual commentary helpers.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion.py tests/test_commentary.py tests/test_import.py -q`: passed.
- Ran `python -m pytest -q`: passed; `python -m pytest --collect-only -q` reported 86 collected tests, including the existing skipped live-kdb placeholder.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 95%.

### Remaining work before milestone completion

- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add deterministic reference-comparison wiring for reversion results using the existing time-series comparison engine.
- Decide whether the q template should emit both `horizon` label and numeric horizon sort order, or whether Python-side natural-duration sorting is sufficient.

### Best next deterministic step

- Add deterministic reversion reference-comparison wiring that uses `compare_metric_timeseries` for venue/horizon groups and applies `higher_is_better=False` for reversion metrics.

### Package phase and iteration

- Phase: 5.
- Iteration: 6.
- Delivery archive name: `mmsr_phase5_iteration6.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?
---

## 2026-05-24 — Phase 5 iteration 7: reversion reference comparison wiring

### Implemented

- Continued Milestone 5A by adding deterministic reference-comparison wiring for cross-venue primary-quote reversion results.
- Added `compare_reversion_metric_timeseries()` as a narrow wrapper around `compare_metric_timeseries()`.
- Set the default reversion comparison policy to preserve `metric_name`, `time_bucket`, `venue`, `horizon`, and the full report `group` when matching current observations to reference histories.
- Forced `higher_is_better=False` for every `primary_quote_reversion_*` metric so positive reversion is treated as the adverse direction in empirical and normal-score tail diagnostics.
- Added validation that reversion comparison inputs use the `primary_quote_reversion_` metric family and include `venue` and `horizon` group dimensions.
- Exported the reversion comparison helper through the public `mmsr.analysis` API.
- Updated `_docs/MILESTONE_STATUS.md` to mark reversion reference-comparison wiring complete and to keep live production q/schema validation as the remaining Milestone 5A gap.

### Files changed

- `mmsr/analysis/comparison.py`
- `mmsr/analysis/__init__.py`
- `tests/test_comparison.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added a test that reversion comparisons keep venue, horizon, intraday bucket, and additional report group dimensions separate.
- Added a test that the helper accepts collections of `MetricTimeSeries` objects.
- Added validation coverage for rejecting non-reversion metrics.
- Updated public API import tests for the new analysis helper.

### Validation performed

- Ran `python -m pytest tests/test_comparison.py tests/test_import.py -q`: passed with 19 tests.
- Ran `python -m pytest -q`: passed with 88 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest --collect-only -q`: collected 89 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 98%.

### Remaining work before milestone completion

- Validate `toxicity_reversion.q` against confirmed production kdb schemas.
- Add an explicit offline output-schema contract for `toxicity_reversion.q` so the live production validation target is deterministic.
- Decide whether the q template should emit both `horizon` label and numeric horizon sort order, or whether Python-side natural-duration sorting is sufficient.

### Best next deterministic step

- Add an explicit offline schema contract and live-kdb validation placeholder for `toxicity_reversion.q`, including required output columns such as `date`, `time_bucket`, `venue`, `horizon`, the metric value, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`.

### Package phase and iteration

- Phase: 5.
- Iteration: 7.
- Delivery archive name: `mmsr_phase5_iteration7.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?


---

## 2026-05-24 — Phase 5 iteration 8: reversion output-schema contract

### Implemented

- Continued Milestone 5A by adding an explicit offline output-schema contract for `toxicity_reversion.q`.
- Added `mmsr.kdb.schema_contracts` with `QTemplateOutputSchemaContract`, `OutputSchemaContractError`, and validation helpers for extracting and checking result columns from dict/list/PyKX-like objects.
- Defined required reversion report-boundary output columns: `date`, `time_bucket`, `venue`, `horizon`, the dynamic metric value column, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`, plus requested report group columns.
- Wired `KdbMetricRunner.run()` to validate reversion result schemas before normalizing them into `MetricTimeSeries`.
- Added a skipped live-kdb validation placeholder for checking `toxicity_reversion.q` against confirmed production schemas.
- Updated the q-template comments and milestone audit to point to the schema contract.

### Files changed

- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added offline schema-contract tests for required reversion output columns, dict/list result validation, missing metadata columns, missing requested report groups, empty row lists, and non-reversion metric rejection.
- Added a runner test confirming reversion output-schema validation happens before normalization.
- Added a skipped `kdb_integration` placeholder for live validation of the toxicity reversion template against production schemas.
- Updated public API import coverage for the schema contract helper.

### Validation performed

- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py tests/test_import.py -q`: passed with 25 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest -q`: passed with 96 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 98 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 99%.

### Remaining work before milestone completion

- Run the live-kdb schema validation against confirmed production venue-trade and primary-quote tables.
- Confirm exact production kdb table names, side conventions, and whether output tables expose stable column metadata for zero-row validation.

### Best next deterministic step

- Execute the live-kdb `toxicity_reversion.q` schema validation once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 8.
- Delivery archive name: `mmsr_phase5_iteration8.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?
- Does the production PyKX conversion preserve column metadata for zero-row result tables, or should live schema validation force a minimum one-row sample slice?
---

## 2026-05-24 — Phase 5 iteration 9: explicit reversion horizon sort order

### Implemented

- Continued Milestone 5A by making the reversion horizon progression explicit at the q-template output boundary.
- Added deterministic `horizon_sort_order` rendering for the six supported primary-quote reversion horizons: `10ms`, `100ms`, `500ms`, `1s`, `5s`, and `10s`.
- Updated `toxicity_reversion.q` to emit `horizon_sort_order` alongside the rendered horizon label so downstream visuals can preserve horizon progression without relying only on text parsing.
- Extended the offline `toxicity_reversion.q` output-schema contract to require `horizon_sort_order`.
- Preserved `horizon_sort_order` in normalized observation metadata and in `ReversionCurvePoint` objects.
- Updated visual sorting to use caller-provided `horizon_order` first, then q-provided `horizon_sort_order`, then natural duration parsing as a deterministic fallback.
- Updated the milestone audit to reflect the explicit horizon sort-order contract.

### Files changed

- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/visuals/toxicity.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_toxicity_reversion.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added schema-contract expectations for required `horizon_sort_order`.
- Added runner coverage that rendered reversion queries include the numeric horizon sort order and normalized metadata preserves it.
- Added visual conversion coverage showing q-provided `horizon_sort_order` can control horizon progression.
- Updated strict q-template parameter coverage for the new parameter.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion.py tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py tests/test_kdb_query_loader.py -q`: passed with 48 passed and 2 skipped live-kdb placeholders.
- Ran `python -m pytest -q`: passed with 98 passed and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 100 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 99%.

### Remaining work before milestone completion

- Run the live-kdb schema validation against confirmed production venue-trade and primary-quote tables.
- Confirm exact production kdb table names, side conventions, and whether output tables expose stable column metadata for zero-row validation.

### Best next deterministic step

- Execute the live-kdb `toxicity_reversion.q` schema validation once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 9.
- Delivery archive name: `mmsr_phase5_iteration9.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Does the production PyKX conversion preserve column metadata for zero-row result tables, or should live schema validation force a minimum one-row sample slice?

---

## 2026-05-24 — Phase 5 iteration 10: reversion input schema contracts

### Implemented

- Continued Milestone 5A with an offline production input-schema contract for `toxicity_reversion.q`.
- Added `QTemplateInputTableSchemaContract` to make required source-table columns explicit for the venue-trade and primary-quote table roles.
- Added `toxicity_reversion_input_schema_contracts()` and `validate_toxicity_reversion_input_schemas()` so live-kdb validation can check source-table schemas before running the q template.
- Documented feed assumptions for `aggressor_side` and primary quote price conventions in the contract.
- Updated the reversion q-template comments, public kdb API exports, and milestone audit.

### Files changed

- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added input-schema contract tests for required venue-trade columns.
- Added input-schema contract tests for required primary-quote columns.
- Added validation coverage for extra source columns and missing `aggressor_side`.
- Updated public API import coverage for the new input-schema helpers.

### Validation performed

- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_import.py -q`: passed with 16 tests and 1 skipped live-kdb placeholder.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_kdb_schema_contracts.py tests/test_import.py -q`: passed with 18 tests and 1 skipped live-kdb placeholder after updating the journal.
- Ran `python -m pytest -q`: passed with 101 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 103 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 5A: Cross-venue toxicity reversion metrics.

### Current milestone progress

- 99%.

### Remaining work before milestone completion

- Run live-kdb validation against confirmed production venue-trade and primary-quote tables.
- Confirm exact production table names and whether `aggressor_side` is numeric with buy as `1` and sell as `-1`, or requires feed-specific mapping before the q template.
- Confirm whether production PyKX conversion preserves column metadata for zero-row result tables, or whether live validation should force a minimum one-row sample slice.

### Best next deterministic step

- Execute live-kdb source-schema and output-schema validation for `toxicity_reversion.q` once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 10.
- Delivery archive name: `mmsr_phase5_iteration10.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressor_side` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Does the production PyKX conversion preserve column metadata for zero-row result tables, or should live schema validation force a minimum one-row sample slice?


---

## 2026-05-24 — Phase 5 iteration 11: assumption-based comparison commentary facts

### Implemented

- Accepted the explicit direction to skip live-kdb validation for now and proceed under the documented offline input/output schema assumptions.
- Marked live-kdb source/output schema validation as deferred to Milestone 10 rather than a blocker for assumption-based implementation.
- Continued Milestone 7 by adding `commentary_facts_from_comparisons()` to convert computed `MetricComparison` objects into grounded `CommentaryFact` rows.
- Extended `TemplateCommentaryEngine` to handle `comparison_only` facts with deterministic wording that clearly states statistical scores are not shown.
- Added deterministic formatting for metric labels, units, reference values, absolute/percentage changes, reference observation units, and low-confidence sample-size caveats.
- Exported the new commentary helper through the public `mmsr.analysis` API.
- Updated the milestone status audit so Milestone 5A is complete under documented assumptions and Milestone 7 is now the earliest incomplete roadmap item.

### Files changed

- `mmsr/analysis/commentary.py`
- `mmsr/analysis/__init__.py`
- `tests/test_commentary.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for converting `MetricComparison` into commentary facts using metric definitions and units.
- Added tests for low-confidence and reference-observation-unit caveats.
- Added tests for deterministic `comparison_only` commentary text.
- Added tests for ordered/limited commentary facts and public analysis API exports.

### Validation performed

- Ran `python -m pytest tests/test_commentary.py tests/test_import.py -q`: passed with 10 tests.
- Ran `python -m pytest -q`: passed with 104 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest`: passed with 104 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 106 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 7: Deterministic commentary engine.

### Current milestone progress

- 65%.

### Remaining work before milestone completion

- Add a section-level rule/builder that assembles comparison-derived facts into `CommentaryBlock` objects for specific report pages.
- Add more explicit severity-threshold tests for section-level alert/watch/normal summaries.
- Keep live-kdb reversion validation deferred to Milestone 10 unless production access and conventions are provided earlier.

### Best next deterministic step

- Add a deterministic report-section builder that converts metric definitions, current comparisons, and commentary facts into `ReportPage` components for the offline demo path.

### Package phase and iteration

- Phase: 5.
- Iteration: 11.
- Delivery archive name: `mmsr_phase5_iteration11.zip`.

### Open questions

- When live validation is re-enabled, are production `aggressor_side` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
- Should page-level commentary group by metric category first, by report dimension first, or by severity first?


---

## 2026-05-24 — Phase 5 iteration 12: deterministic comparison report-section builder

### Implemented

- Continued under the documented assumption-based path with live-kdb validation deferred to Milestone 10.
- Added `mmsr.report.sections` with `ComparisonSectionOptions` and `build_comparison_report_page()`.
- Built deterministic report-page assembly from current `MetricComparison` rows, required `MetricDefinition` help text, and supplied or derived `CommentaryFact` rows.
- Added metric card formatting for current values, reference values, absolute changes, percentage changes, and comparison statuses.
- Preserved deterministic commentary generation without LLM usage through `TemplateCommentaryEngine`.
- Exported the section builder through `mmsr.report`.
- Updated the milestone status audit to show page-level commentary generation is now met while section summary thresholds remain.

### Files changed

- `mmsr/report/sections.py`
- `mmsr/report/__init__.py`
- `tests/test_report_sections.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for building report pages with ordered metric cards and deterministic commentary.
- Added tests for precomputed commentary facts, custom commentary titles, and presentation limits.
- Added tests requiring metric definitions before rendering metric cards so help text remains available.
- Added tests for HTML rendering of a built comparison report page.
- Added public API import coverage for the new report section builder.

### Validation performed

- Ran `python -m pytest tests/test_report_sections.py tests/test_html_rendering.py tests/test_commentary.py tests/test_import.py -q`: passed with 18 tests.
- Ran `python -m pytest -q`: passed with 110 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 112 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_report_sections.py tests/test_import.py -q`: passed with 13 tests after updating governance docs.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed with 2 tests after the final journal validation note.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 7: Deterministic commentary engine.

### Current milestone progress

- 80%.

### Remaining work before milestone completion

- Add deterministic section summary facts that count alert/watch/normal comparison statuses per report page.
- Add explicit section-level severity-threshold tests and headline output text coverage.
- Keep live-kdb reversion validation deferred to Milestone 10 unless production access and conventions are provided earlier.

### Best next deterministic step

- Add deterministic section summary facts that count alert/watch/normal comparison statuses per report page and render a concise headline before metric-level commentary.

### Package phase and iteration

- Phase: 5.
- Iteration: 12.
- Delivery archive name: `mmsr_phase5_iteration12.zip`.

### Open questions

- When live validation is re-enabled, are production `aggressor_side` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
- Should section summary thresholds count every comparison row, only displayed metric cards, or a configured subset of headline metrics?


---

## 2026-05-24 — Phase 5 iteration 13: deterministic section summary commentary

### Implemented

- Continued under the documented assumption-based path with live-kdb validation deferred to Milestone 10.
- Added `section_summary_fact_from_comparisons()` to count already-computed comparison statuses at report-section level.
- Extended `CommentaryFact` with a deterministic `fact_type` field so section summary facts can render before metric-level facts.
- Updated `TemplateCommentaryEngine` to render concise section headlines such as alert/watch/comparison-only/normal counts without using LLMs.
- Updated `build_comparison_report_page()` to prepend a section summary headline when commentary facts are derived from comparisons.
- Added `ComparisonSectionOptions.include_section_summary` and `section_summary_scope_label` controls.
- Exported the new summary helper through `mmsr.analysis`.
- Updated the milestone status audit to mark Milestone 7 complete and identify Milestone 8 as the next incomplete roadmap item.

### Files changed

- `mmsr/analysis/commentary.py`
- `mmsr/analysis/__init__.py`
- `mmsr/report/sections.py`
- `tests/test_commentary.py`
- `tests/test_report_sections.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for section summary status counting and headline output ordering.
- Updated report-section tests to assert summary headlines appear before metric-level commentary.
- Added tests for disabling section summary generation and validating summary scope labels.
- Updated public API import coverage for `section_summary_fact_from_comparisons()`.

### Validation performed

- Ran `python -m pytest tests/test_commentary.py tests/test_report_sections.py tests/test_import.py -q`: passed with 20 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_commentary.py tests/test_report_sections.py tests/test_import.py -q`: passed with 22 tests.
- Ran `python -m pytest -q`: passed with 113 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest -q -ra`: passed and confirmed the same 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 115 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 7: Deterministic commentary engine.

### Current milestone progress

- 100%.

### Remaining work before milestone completion

- Milestone 7 is complete for the deterministic, non-LLM path.
- Keep live-kdb reversion validation deferred to Milestone 10 unless production access and conventions are provided earlier.

### Best next deterministic step

- Add a deterministic metric definitions appendix builder that converts the metric definitions used in a report page into an appendix `ReportPage` with help/documentation content.

### Package phase and iteration

- Phase: 5.
- Iteration: 13.
- Delivery archive name: `mmsr_phase5_iteration13.zip`.

### Open questions

- When live validation is re-enabled, are production `aggressor_side` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
- Should the metric definitions appendix be embedded as a final HTML report page by default, or exposed as an opt-in builder for callers to append explicitly?

---

## 2026-05-24 — Phase 5 iteration 14: metric definitions appendix builder

### Implemented

- Continued Milestone 8 by adding a deterministic metric definitions appendix path for static/report exports.
- Added `MetricDefinitionsAppendixOptions` to configure appendix page title, block title, and help text.
- Added `collect_metric_definitions_from_pages()` to gather unique metric definitions from report-page metric cards with deterministic category/label/name ordering.
- Added `build_metric_definitions_appendix_page()` to render complete metric documentation as an appendix `ReportPage` with a trusted HTML definition block.
- Added `append_metric_definitions_appendix()` to return a copied `ReportDocument` with an appendix appended without mutating the original document.
- Expanded `metric_definitions_markdown()` so static exports include name, category, description, formula, interpretation, unit, aggregation, direction, intraday/symbol support, required tables, required columns, and caveats.
- Added HTML styling for expandable metric definition blocks in the default report template.
- Exported the appendix helpers through the public `mmsr.report` API.
- Updated the milestone status audit to reflect that the definitions appendix path is now implemented while metric table and chart/heatmap placeholders remain.

### Files changed

- `mmsr/report/metric_docs.py`
- `mmsr/report/__init__.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_metric_docs.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for collecting metric definitions from report pages, including de-duplication and deterministic ordering.
- Added tests for detecting conflicting duplicate metric definitions.
- Added tests for appendix HTML content, complete definition fields, HTML escaping, and report rendering.
- Added tests for non-mutating document appendix append behavior.
- Added tests for expanded markdown output and appendix option validation.
- Updated public API import coverage for the new appendix helpers.

### Validation performed

- Ran `python -m pytest tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py -q`: passed with 15 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py -q`: passed with 17 tests after updating the journal and milestone status audit.
- Ran `python -m pytest -q -ra`: passed and confirmed the same 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 122 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 8: Report components and metric help.

### Current milestone progress

- 60%.

### Remaining work before milestone completion

- Add a deterministic metric table component with metric help text exposed per metric row.
- Add time-series chart and heatmap placeholder components that can expose metric definitions/help.
- Consider whether appendices should be appended automatically by a higher-level report builder or remain opt-in utilities for callers.

### Best next deterministic step

- Add a deterministic metric table component that renders metric rows with values, statuses, and metric help text from `MetricDefinition` objects.

### Package phase and iteration

- Phase: 5.
- Iteration: 14.
- Delivery archive name: `mmsr_phase5_iteration14.zip`.

### Open questions

- Should metric definitions appendices be appended automatically by a higher-level report builder, or remain opt-in utilities for callers to add explicitly?


---

## 2026-05-24 — Phase 5 iteration 15: deterministic metric table component

### Implemented

- Continued Milestone 8 by adding a deterministic metric table component for report pages.
- Added `MetricTableRow` and `MetricTable` report component models with per-row metric help text sourced from `MetricDefinition.help_text()`.
- Added a shared Jinja metric-table partial and default HTML styling for rows, status classes, group labels, values, references, changes, and help icons.
- Added `render_metric_table()` for focused table rendering and report-template support for `ReportPage.metric_tables`.
- Added `build_comparison_metric_table()` to format already-computed `MetricComparison` rows into deterministic severity-first metric tables without calculating new analytics or using LLMs.
- Included date and time-bucket keys in comparison row ordering so equal-severity table/card rows remain stable for time-series report periods.
- Extended metric definition collection so appendix builders include definitions used by both metric cards and metric table rows.
- Exported the new metric table models and comparison-table builder through the public `mmsr.report` API.
- Updated the milestone status audit to reflect that metric tables are implemented and time-series/heatmap placeholders remain.

### Files changed

- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/metric_docs.py`
- `mmsr/report/__init__.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/metric_table.html.j2`
- `tests/test_metric_tables.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for metric table rendering with row-level metric help, table-level help, values, references, changes, group labels, and status classes.
- Added tests for full-report rendering of metric tables.
- Added tests for deterministic comparison-to-table formatting and severity-first ordering.
- Added validation tests for blank table titles, invalid row limits, and missing metric definitions.
- Added tests proving metric definitions appendices collect definitions from metric table rows.
- Updated public API import coverage for `MetricTable`, `MetricTableRow`, and `build_comparison_metric_table()`.

### Validation performed

- Ran `python -m pytest tests/test_metric_tables.py tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py -q`: passed with 21 tests.
- Ran `python -m pytest -q -ra`: passed with 128 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 128 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_metric_tables.py tests/test_import.py -q`: passed with 14 tests after updating docs and journal.
- Ran `python -m pytest tests/test_metric_tables.py tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py tests/test_docs_governance.py -q`: passed with 23 tests after final formatting cleanup.
- Ran `python -m pytest tests/test_metric_tables.py tests/test_report_sections.py tests/test_import.py -q`: passed with 19 tests after final comparison sort-key cleanup.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 8: Report components and metric help.

### Current milestone progress

- 75%.

### Remaining work before milestone completion

- Add deterministic time-series chart placeholder components that can expose metric definitions/help.
- Add deterministic heatmap placeholder components that can expose metric definitions/help.
- Consider whether appendices or metric tables should be wired into a higher-level report builder automatically or remain opt-in utilities for callers.

### Best next deterministic step

- Add a deterministic time-series chart placeholder component that can expose metric definitions/help while preserving report-period and bucket context.

### Package phase and iteration

- Phase: 5.
- Iteration: 15.
- Delivery archive name: `mmsr_phase5_iteration15.zip`.

### Open questions

- No new open questions.

---

## 2026-05-24 — Phase 8 iteration 16: deterministic time-series chart placeholder

### Implemented

- Continued Milestone 8 by adding a deterministic time-series chart placeholder component for report pages.
- Added `TimeSeriesChartPoint` and `TimeSeriesChart` report component models with metric help text sourced from `MetricDefinition.help_text()`.
- Added a shared Jinja time-series chart partial and default HTML styling for chart metadata, placeholder table rows, axis labels, report-period labels, time-bucket labels, series labels, values, and context metadata.
- Added `render_time_series_chart()` for focused chart rendering and report-template support for `ReportPage.time_series_charts`.
- Added `build_time_series_chart()` to format already-normalized `MetricTimeSeries` observations into deterministic chart points without calculating new analytics or using LLMs.
- Preserved observation order, report date, intraday/auction bucket label, selected group/series labels, and metadata context in the rendered placeholder.
- Extended metric definition collection so appendix builders include definitions used by time-series charts.
- Exported the new time-series chart models and builder through the public `mmsr.report` API.
- Updated the milestone status audit to reflect that time-series chart placeholders are implemented and heatmap placeholders remain.
- Corrected the delivery archive naming scheme for this output so the package phase now matches the active roadmap milestone: `mmsr_phase8_iteration16.zip`.

### Files changed

- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/metric_docs.py`
- `mmsr/report/__init__.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/time_series_chart.html.j2`
- `tests/test_time_series_charts.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for rendering time-series chart placeholders with metric help, axis labels, period context, time-bucket context, series labels, values, and metadata.
- Added tests for building chart points from `MetricTimeSeries` while preserving observation order and bucket context.
- Added tests for full-report rendering of time-series charts and metric definitions appendix collection from chart components.
- Added validation tests for blank chart/point labels, invalid point limits, blank axis/help text, and mismatched metric definitions.
- Updated public API import coverage for `TimeSeriesChart`, `TimeSeriesChartPoint`, and `build_time_series_chart()`.

### Validation performed

- Ran `python -m pytest tests/test_time_series_charts.py tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py -q`: passed with 22 tests.
- Ran `python -m pytest -q -ra`: passed with 134 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 134 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_time_series_charts.py tests/test_import.py -q`: passed with 14 tests after updating docs and journal.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 8: Report components and metric help.

### Current milestone progress

- 85%.

### Remaining work before milestone completion

- Add deterministic heatmap placeholder components that can expose metric definitions/help while preserving intraday bucket and grouping context.
- Consider whether appendices, metric tables, and chart placeholders should be wired into a higher-level report builder automatically or remain opt-in utilities for callers.

### Best next deterministic step

- Add a deterministic heatmap placeholder component that can expose metric definitions/help while preserving intraday bucket and grouping context.

### Package phase and iteration

- Phase: 8.
- Iteration: 16.
- Delivery archive name: `mmsr_phase8_iteration16.zip`.

### Open questions

- No new open questions.

---

## 2026-05-24 — Phase 8 iteration 17: deterministic heatmap placeholder component

### Implemented

- Completed Milestone 8 by adding a deterministic heatmap placeholder component for report pages.
- Added `HeatmapCell` and `Heatmap` report component models with metric help text sourced from `MetricDefinition.help_text()`.
- Added a shared Jinja heatmap partial and default HTML styling for heatmap metadata, placeholder table cells, intraday bucket labels, group labels, report dates, values, and context metadata.
- Added `render_heatmap()` for focused heatmap rendering and report-template support for `ReportPage.heatmaps`.
- Added `build_heatmap()` to format already-normalized `MetricTimeSeries` observations into deterministic heatmap cells without calculating new analytics or using LLMs.
- Preserved observation order, report date, intraday/auction bucket label, grouping context, values, and metadata context in the rendered placeholder.
- Extended metric definition collection so appendix builders include definitions used by heatmaps.
- Exported the new heatmap models and builder through the public `mmsr.report` API.
- Updated the milestone status audit to mark Milestone 8 complete and identify Milestone 9 as the earliest incomplete roadmap item.
- Kept the corrected phase-based delivery naming scheme: `mmsr_phase8_iteration17.zip`.

### Files changed

- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/metric_docs.py`
- `mmsr/report/__init__.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/heatmap.html.j2`
- `tests/test_heatmaps.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests for rendering heatmap placeholders with metric help, axis labels, value labels, report date, intraday/auction bucket context, group context, values, and metadata.
- Added tests for building heatmap cells from `MetricTimeSeries` while preserving observation order and bucket/group context.
- Added tests for full-report rendering of heatmaps and metric definitions appendix collection from heatmap components.
- Added validation tests for blank heatmap/cell labels, invalid cell limits, blank axis/help text, and mismatched metric definitions.
- Updated public API import coverage for `Heatmap`, `HeatmapCell`, and `build_heatmap()`.

### Validation performed

- Ran `python -m pytest tests/test_heatmaps.py tests/test_metric_docs.py tests/test_html_rendering.py tests/test_import.py -q`: passed with 22 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 140 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 140 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_heatmaps.py tests/test_import.py -q`: passed with 14 tests after updating docs and journal.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 8: Report components and metric help.

### Current milestone progress

- 100%.

### Remaining work before milestone completion

- No remaining Milestone 8 exit criteria are incomplete under the current roadmap.

### Best next deterministic step

- Start Milestone 9 by adding an offline sample fixture module that builds representative `MetricTimeSeries` and `MetricComparison` objects for report examples without a live kdb connection.

### Package phase and iteration

- Phase: 8.
- Iteration: 17.
- Delivery archive name: `mmsr_phase8_iteration17.zip`.

### Open questions

- No new open questions.
---

## 2026-05-24 — Phase 9 iteration 18: offline sample metric fixtures

### Implemented

- Started Milestone 9 by adding deterministic offline fixture helpers for report examples.
- Added `mmsr.examples.offline_fixtures` with explicit synthetic reference trading-day dates, current `MetricTimeSeries` builders, historical reference `MetricTimeSeries` builders, precomputed `MetricComparison` builder, and an `OfflineSampleMetrics` bundle.
- Included representative activity and liquidity metrics: `quoted_spread_bps`, `volume`, and `top_of_book_depth`.
- Kept the fixtures offline-only: they build already-normalized observations and comparisons without importing PyKX, connecting to kdb, calculating from raw trade/quote data, or using LLM calls.
- Exported the offline fixture helpers through the public `mmsr.examples` API.
- Updated the milestone status audit to mark Milestone 9 as in progress and to identify offline demo report assembly as the next deterministic step.
- Kept phase-based delivery naming: `mmsr_phase9_iteration18.zip`.

### Files changed

- `mmsr/examples/__init__.py`
- `mmsr/examples/offline_fixtures.py`
- `tests/test_offline_fixtures.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests that verify offline current/reference fixture series are deterministic, typed as `MetricTimeSeries`, preserve report date, bucket, group, and synthetic metadata context, and use explicit historical observation-unit dates.
- Added tests that verify precomputed offline comparisons have six rows, 30 reference observations, normal comparison confidence, available z-scores, and `trading_day` reference-observation metadata.
- Added tests that verify the bundled `OfflineSampleMetrics` object contains metric definitions, current series, reference series, and comparisons.
- Updated public API import tests for `mmsr.examples`.

### Validation performed

- Ran `python -m pytest tests/test_offline_fixtures.py tests/test_import.py -q`: passed with 11 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_offline_fixtures.py tests/test_import.py -q`: passed with 13 tests after updating docs and journal.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 144 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 144 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9: End-to-end offline demo.

### Current milestone progress

- 25%.

### Remaining work before milestone completion

- Add a deterministic offline demo report builder that assembles the sample metrics into a `ReportDocument` with comparison tables, time-series/heatmap placeholders, commentary, and a metric definitions appendix.
- Add an offline example config or command path that runs locally without live kdb.
- Add README quickstart instructions for the offline demo.

### Best next deterministic step

- Add a deterministic offline demo report builder that uses `build_offline_sample_metrics()` to assemble comparison tables, chart/heatmap placeholders, commentary, and a metric definitions appendix into a `ReportDocument` without a live kdb connection.

### Package phase and iteration

- Phase: 9.
- Iteration: 18.
- Delivery archive name: `mmsr_phase9_iteration18.zip`.

### Open questions

- No new open questions.

---

## 2026-05-24 — Phase 9 iteration 19: offline demo report builder

### Implemented

- Added a deterministic offline demo report builder for Milestone 9.
- Added `mmsr.examples.offline_demo` with `OfflineDemoReportOptions` and `build_offline_demo_report()`.
- Assembled the synthetic offline fixture bundle into a `ReportDocument` with:
  - comparison metric cards,
  - a severity-sorted current-versus-reference metric table,
  - deterministic template commentary with a section headline,
  - time-series chart placeholders,
  - heatmap placeholders,
  - branding/generation text, and
  - an optional metric definitions appendix.
- Kept the builder offline-only: it consumes already-normalized synthetic `MetricTimeSeries` and precomputed `MetricComparison` objects, does not import PyKX, does not connect to kdb, does not write files, and does not call an LLM.
- Exported the offline demo report builder through the public `mmsr.examples` API.
- Updated the milestone status audit to mark the synthetic report-rendering flow as met and to identify offline config/command wiring as the next deterministic step.
- Kept phase-based delivery naming: `mmsr_phase9_iteration19.zip`.

### Files changed

- `mmsr/examples/offline_demo.py`
- `mmsr/examples/__init__.py`
- `tests/test_offline_demo.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added tests that verify the offline demo builder assembles summary, detail, and metric definitions appendix pages.
- Added tests that verify rendered HTML includes comparison tables, deterministic commentary, time-series chart placeholders, heatmap placeholders, metric help/formula text, and offline branding.
- Added tests for appendix omission and row/point/cell/comment limits.
- Added tests that verify caller-supplied offline sample bundles are accepted.
- Added tests that verify missing metric definitions are rejected deterministically.
- Added validation tests for offline demo report option text fields and numeric limits.
- Updated public API import coverage for `OfflineDemoReportOptions` and `build_offline_demo_report()`.

### Validation performed

- Ran `python -m pytest tests/test_offline_demo.py tests/test_import.py -q`: passed with 13 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_offline_demo.py tests/test_offline_fixtures.py tests/test_import.py -q`: passed with 19 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 151 tests and 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 151 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9: End-to-end offline demo.

### Current milestone progress

- 55%.

### Remaining work before milestone completion

- Add an offline example configuration or command path that renders the demo report locally without a live kdb connection.
- Add README quickstart instructions for the offline demo.

### Best next deterministic step

- Add an offline example configuration or command path that invokes `build_offline_demo_report()` and `render_report()` to produce a local HTML demo without a live kdb connection.

### Package phase and iteration

- Phase: 9.
- Iteration: 19.
- Delivery archive name: `mmsr_phase9_iteration19.zip`.

### Open questions

- No new open questions.


---

## 2026-05-24 — Phase 9 iteration 20: offline demo CLI render path

### Implemented

- Added a deterministic `mmsr offline-demo` command path for Milestone 9.
- Replaced the CLI placeholder with an argparse-based command that renders the synthetic offline HTML report to a caller-specified file.
- Added `render_offline_demo_report_file()` so tests and programmatic callers can render the offline demo without invoking a subprocess.
- Supported deterministic command options for report title, brand name, generated-at text, appendix omission, metric card/comment/table/chart/heatmap limits, output path, and optional template directory.
- Kept the command path offline-only: it delegates to `build_offline_demo_report()` and `render_report()`, writes HTML only, does not import PyKX, does not connect to kdb, and does not call an LLM.
- Updated the milestone status audit to mark the local offline command path as met and identify README quickstart documentation as the remaining Milestone 9 item.
- Kept phase-based delivery naming: `mmsr_phase9_iteration20.zip`.

### Files changed

- `mmsr/cli.py`
- `tests/test_cli.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added CLI tests for rendering the offline demo HTML to a requested path.
- Added tests for parent-directory creation, custom title/brand/generated-at options, appendix omission, option validation, directory-output rejection, programmatic helper usage, and help output.
- Added an offline guard assertion that the render path does not import `pykx`.

### Validation performed

- Ran `python -m pytest tests/test_cli.py tests/test_import.py -q`: passed with 14 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_cli.py tests/test_offline_demo.py tests/test_offline_fixtures.py tests/test_import.py -q`: passed with 26 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 158 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9: End-to-end offline demo.

### Current milestone progress

- 80%.

### Remaining work before milestone completion

- Add README quickstart instructions for rendering the deterministic offline demo HTML report locally.

### Best next deterministic step

- Add README quickstart instructions that show `mmsr offline-demo --output <path>` and describe that the demo uses synthetic normalized metrics without kdb/PyKX or LLM calls.

### Package phase and iteration

- Phase: 9.
- Iteration: 20.
- Delivery archive name: `mmsr_phase9_iteration20.zip`.

### Open questions

- No new open questions.

---

## 2026-05-24 — Phase 9 iteration 21: README offline demo quickstart

### Implemented

- Added README quickstart instructions for rendering the deterministic offline demo HTML report locally.
- Documented `poetry run mmsr offline-demo --output reports/offline_demo.html`.
- Documented that the offline demo uses synthetic normalized metrics and precomputed comparisons, does not query kdb+, does not import PyKX, does not call an LLM, and does not use real market data.
- Added a governance test to keep the README offline demo quickstart from regressing.
- Updated the milestone status audit to mark Milestone 9 complete and identify Milestone 10 as the earliest incomplete roadmap item.
- Kept phase-based delivery naming: `mmsr_phase9_iteration21.zip`.

### Files changed

- `README.md`
- `tests/test_docs_governance.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added `test_readme_documents_offline_demo_quickstart()` to verify the README includes the offline demo command and offline/no-LLM/no-kdb boundaries.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py tests/test_cli.py tests/test_import.py -q`: passed with 18 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m pytest --collect-only -q`: collected 159 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9: End-to-end offline demo.

### Current milestone progress

- 100%.

### Remaining work before milestone completion

- None. Milestone 9 is complete under the offline-demo scope.

### Best next deterministic step

- Start Milestone 10 by adding a deterministic mock-kdb integration example that exercises an existing q template through `KdbMetricRunner`, validates the normalized result, and documents the live-kdb boundary.

### Package phase and iteration

- Phase: 9.
- Iteration: 21.
- Delivery archive name: `mmsr_phase9_iteration21.zip`.

### Open questions

- No new open questions.

