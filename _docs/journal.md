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


---

## 2026-05-25 — Phase 9 iteration 22: canonical production-format report builder

### Implemented

- Restarted from `mmsr_phase9_iteration21(1).zip` as the base package.
- Updated the roadmap to insert Milestone 9A before Milestone 10, reflecting user feedback that report quality must be hardened before kdb integration.
- Documented that the mock-data demo must use the exact same production-format report builder, page structure, packaged Jinja template, component partials, and metric-help behavior as production; only the data source changes.
- Added `mmsr.report.market_report.MarketReportInput`, `MarketReportOptions`, and `build_market_monitor_report()` as the canonical production-format report assembly path.
- Refactored `mmsr.examples.offline_demo.build_offline_demo_report()` into a mock-data adapter that converts fixture metrics into `MarketReportInput` and delegates to `build_market_monitor_report()`.
- Updated the default mock-data demo wording from offline-specific page names to production-format page names: `Market Summary` and `Intraday Detail`.
- Updated README and milestone status documentation to describe the demo as a production-format mock-data acceptance harness rather than a separate report layout.
- Added the requested info-icon/popover issue to Milestone 9A as an explicit requirement: title-only/inert info buttons are not sufficient, and metric/help controls must become accessible deterministic expandable/popover-style controls in a later iteration.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `mmsr/examples/offline_demo.py`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `tests/test_cli.py`
- `tests/test_docs_governance.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`

### Tests added or updated

- Added `tests/test_market_report.py` to verify the canonical production-format report builder, packaged template rendering, component limits, appendix omission, and missing metric-definition validation.
- Updated offline demo tests to assert that the mock-data demo uses production-format page names and delegates through the canonical report shape.
- Updated CLI tests for the new mock-data production-format wording.
- Updated README governance test to assert that the quickstart documents `build_market_monitor_report()` and the rule that only the data source changes.

### Validation performed

- Ran `python -m pytest tests/test_market_report.py tests/test_offline_demo.py tests/test_cli.py tests/test_docs_governance.py -q`: passed with 21 tests.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 164 tests.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 20%.

### Remaining work before milestone completion

- Replace title-only metric info buttons with accessible deterministic help controls across metric cards, tables, charts, heatmaps, and trusted HTML blocks.
- Replace time-series placeholder tables with real trend visuals while preserving accessible backing data.
- Replace heatmap placeholder tables with visual intraday/group encodings while preserving accessible backing data.
- Add human-friendly display labels for metrics, buckets, groups, and reference observation units.
- Rewrite deterministic commentary templates to avoid internal labels such as `time_bucket=AMO` and `unit=trading_day`.
- Add an executive market overview section that focuses on high-level market trend before per-bucket diagnostics.

### Best next deterministic step

- Implement shared accessible metric/help controls using deterministic template partials and `<details>/<summary>` or equivalent no-JavaScript HTML, then update the relevant rendering tests to prove the help content is visible and not only stored in a `title` attribute.

### Package phase and iteration

- Phase: 9.
- Iteration: 22.
- Delivery archive name: `mmsr_phase9_iteration22.zip`.

### Open questions

- No new open questions.


## 2026-05-25 — Phase 9 iteration 23: accessible report help controls

### Implemented

- Continued from `mmsr_phase9_iteration22.zip`.
- Implemented a shared deterministic help-control partial at `mmsr/report/templates/partials/help_control.html.j2`.
- Replaced title-only/inert info buttons with no-JavaScript `<details>/<summary>` controls across metric cards, metric tables, time-series charts, heatmaps, and trusted HTML blocks.
- Kept the existing `metric-info` CSS hook on the summary element for compatibility while removing `<button>`-based title-only help.
- Added report template CSS for expandable help popovers, compact labels, and help bodies.
- Updated milestone status documentation to mark accessible metric/help controls as met and to identify production trend visuals as the next Milestone 9A step.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/help_control.html.j2`
- `mmsr/report/templates/partials/metric_card.html.j2`
- `mmsr/report/templates/partials/metric_table.html.j2`
- `mmsr/report/templates/partials/time_series_chart.html.j2`
- `mmsr/report/templates/partials/heatmap.html.j2`
- `tests/test_metric_help_controls.py`

### Tests added or updated

- Added `tests/test_metric_help_controls.py`.
- Added coverage proving the mock-data production-format report renders expandable `<details>/<summary>` help controls for metric definitions, table help, chart help, heatmap help, and section help.
- Added coverage proving rendered help is not stored only in `title` attributes and that no `<button>` info controls remain in the default report template output.

### Validation performed

- Ran `python -m pytest tests/test_metric_help_controls.py tests/test_html_rendering.py tests/test_metric_tables.py tests/test_time_series_charts.py tests/test_heatmaps.py tests/test_offline_demo.py tests/test_market_report.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 166 tests and 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 166 tests.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_metric_help_controls.py -q`: passed.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 35%.

### Remaining work before milestone completion

- Replace time-series placeholder tables with real trend visuals while preserving accessible backing data.
- Replace heatmap placeholder tables with visual intraday/group encodings while preserving accessible backing data.
- Add human-friendly display labels for metrics, buckets, groups, and reference observation units.
- Rewrite deterministic commentary templates to avoid internal labels such as `time_bucket=AMO`, `unit=trading_day`, and `market_cap_bucket=Small`.
- Add an executive market overview section that focuses on high-level market trend before per-bucket diagnostics.

### Best next deterministic step

- Implement production-format time-series trend visuals, starting with deterministic inline SVG line charts for `TimeSeriesChart` while keeping the existing backing table for auditability and accessibility.

### Package phase and iteration

- Phase: 9.
- Iteration: 23.
- Delivery archive name: `mmsr_phase9_iteration23.zip`.

### Open questions

- No new open questions.


---

## 2026-05-25 — Phase 9 iteration 24: deterministic inline SVG time-series charts

### Implemented

- Continued from `mmsr_phase9_iteration23(1).zip`.
- Replaced the production-format `TimeSeriesChart` placeholder table with a deterministic inline SVG line chart.
- Preserved the accessible backing data table under an expanded `<details>` block so every plotted point remains auditable.
- Added typed SVG helper models for chart series, markers, and ticks.
- Preserved numeric metric values from normalized `MetricObservation` rows through `TimeSeriesChartPoint.value` so rendering does not need raw market data or external chart dependencies.
- Added a safe display-text parsing fallback for hand-built chart points that do not supply a numeric value.
- Rendered one SVG series per `series_text` value with deterministic x/y scaling, sampled x-axis ticks, y-axis ticks, marker titles, and legend labels.
- Updated the canonical report template CSS for real time-series visuals while leaving heatmap placeholders unchanged for the next step.
- Updated milestone status documentation to mark time-series trend visuals as met.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/time_series_chart.html.j2`
- `tests/test_cli.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_time_series_charts.py`

### Tests added or updated

- Updated time-series chart tests to assert inline SVG rendering, retained backing data, removal of the old placeholder class, numeric value preservation, deterministic series/tick generation, and hand-built display-text parsing.
- Updated market-report, offline-demo, and CLI tests to assert the production-format mock-data report renders SVG time-series visuals and no longer emits the old time-series placeholder class.

### Validation performed

- Ran `python -m pytest tests/test_time_series_charts.py tests/test_market_report.py tests/test_metric_help_controls.py tests/test_html_rendering.py -q`: passed.
- Ran `python -m pytest -q -ra`: initially failed because stale CLI/offline-demo tests still expected `time-series-chart__placeholder`; updated those tests to match the new SVG behavior.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 168 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 50%.

### Remaining work before milestone completion

- Replace heatmap placeholder tables with deterministic visual intraday/group encodings while preserving accessible backing data.
- Add human-friendly display labels for metrics, buckets, groups, and reference observation units.
- Rewrite deterministic commentary templates to avoid internal labels such as `time_bucket=AMO`, `unit=trading_day`, and `market_cap_bucket=Small`.
- Add an executive market overview section that focuses on high-level market trend before per-bucket diagnostics.

### Best next deterministic step

- Implement deterministic visual heatmap encodings for `Heatmap` while keeping the existing backing table for auditability and accessibility.

### Package phase and iteration

- Phase: 9.
- Iteration: 24.
- Delivery archive name: `mmsr_phase9_iteration24.zip`.

### Open questions

- No new open questions.



---

## 2026-05-25 — Phase 9 iteration 25: deterministic inline SVG heatmaps

### Implemented

- Continued from `mmsr_phase9_iteration24.zip`.
- Replaced production-format heatmap placeholder tables with deterministic inline SVG matrix visuals.
- Preserved the accessible backing data table under an expanded `<details>` block so every rendered heatmap cell remains auditable.
- Added typed SVG helper models for heatmap cells and axis labels.
- Preserved numeric metric values from normalized `MetricObservation` rows through `HeatmapCell.value` so rendering does not need raw market data or external chart dependencies.
- Added a safe display-text parsing fallback for hand-built heatmap cells that do not supply a numeric value.
- Encoded numeric heatmap magnitude through deterministic cell opacity, included missing-value cells with a deterministic missing-cell style, and retained x/y axis labels.
- Updated the canonical report template CSS for real heatmap visuals.
- Updated milestone status documentation to mark heatmap/intraday diagnostic visual encodings as met.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/report/components.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/heatmap.html.j2`
- `tests/test_cli.py`
- `tests/test_heatmaps.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`

### Tests added or updated

- Updated heatmap tests to assert inline SVG rendering, retained backing data, removal of the old placeholder class, numeric value preservation, deterministic axis labels, cell opacity, missing-cell rendering, and hand-built display-text parsing.
- Updated market-report, offline-demo, and CLI tests to assert the production-format mock-data report renders SVG heatmap visuals and no longer emits the old heatmap placeholder class.

### Validation performed

- Ran `python -m pytest tests/test_heatmaps.py tests/test_market_report.py tests/test_offline_demo.py tests/test_cli.py tests/test_metric_help_controls.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 168 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 65%.

### Remaining work before milestone completion

- Add human-friendly display labels for metrics, buckets, groups, and reference observation units.
- Rewrite deterministic commentary templates to avoid internal labels such as `time_bucket=AMO`, `unit=trading_day`, and `market_cap_bucket=Small`.
- Add an executive market overview section that focuses on high-level market trend before per-bucket diagnostics.

### Best next deterministic step

- Add deterministic display-label helpers for intraday buckets, group keys/values, and reference observation units, then route commentary scope and comparison text through those helpers without changing metric calculations.

### Package phase and iteration

- Phase: 9.
- Iteration: 25.
- Delivery archive name: `mmsr_phase9_iteration25.zip`.

### Open questions

- No new open questions.

---

## 2026-05-25 — Phase 9 iteration 26: roadmap backlog for ppw extras and Typer CLI

### Implemented

- Continued from `mmsr_phase9_iteration25.zip`.
- Added a later roadmap milestone for ppw packaging parity and CLI ergonomics.
- Recorded the requested future work to add explicit `dev` and `doc` optional dependency support without changing runtime dependencies in this iteration.
- Recorded the requested future work to evaluate a dedicated Typer CLI migration while preserving existing command behavior.
- Added a governance test that keeps the roadmap backlog items visible.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added `test_roadmap_tracks_packaging_and_cli_backlog` to assert that the roadmap continues to track ppw packaging parity, `dev`/`doc` optional dependency support, Typer CLI evaluation, and lean runtime installation.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 169 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 65%.

### Remaining work before milestone completion

- Add human-friendly display labels for metrics, buckets, groups, and reference observation units.
- Rewrite deterministic commentary templates to avoid internal labels such as `time_bucket=AMO`, `unit=trading_day`, and `market_cap_bucket=Small`.
- Add an executive market overview section that focuses on high-level market trend before per-bucket diagnostics.
- Later, after the production-format report path is stable, implement the newly recorded ppw packaging parity and Typer CLI backlog items as a separate milestone.

### Best next deterministic step

- Add deterministic display-label helpers for intraday buckets, group keys/values, and reference observation units, then route commentary scope and comparison text through those helpers without changing metric calculations.

### Package phase and iteration

- Phase: 9.
- Iteration: 26.
- Delivery archive name: `mmsr_phase9_iteration26.zip`.

### Open questions

- Confirm whether ppw parity should be represented as Poetry extras, Poetry dependency groups, or both for this package before implementing the dependency changes.
- Confirm whether the Typer migration should remain optional until the current argparse-style CLI has more commands, or happen immediately after Milestone 9A.


---

## 2026-05-25 — Phase 9 iteration 27: human-friendly report display labels

### Implemented

- Continued from `mmsr_phase9_iteration26.zip`.
- Added deterministic presentation label helpers for auction buckets, intraday bucket ranges, group keys, group values, comparison scopes, and reference observation units.
- Routed deterministic commentary group text and reference observation-unit caveats through the display-label helpers.
- Routed comparison table scope text, time-series chart bucket/group/metadata text, and heatmap bucket/group/metadata text through the same display-label helpers.
- Updated production-format, offline-demo, and CLI tests to assert human-facing labels and reject internal strings such as `time_bucket=`, `market_cap_bucket=`, and `reference_observation_unit` in rendered report HTML.
- Updated milestone status documentation to mark deterministic commentary display labels as complete.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/analysis/commentary.py`
- `mmsr/presentation/__init__.py`
- `mmsr/presentation/labels.py`
- `mmsr/report/sections.py`
- `tests/test_cli.py`
- `tests/test_commentary.py`
- `tests/test_display_labels.py`
- `tests/test_heatmaps.py`
- `tests/test_market_report.py`
- `tests/test_metric_tables.py`
- `tests/test_offline_demo.py`
- `tests/test_report_sections.py`
- `tests/test_time_series_charts.py`

### Tests added or updated

- Added `tests/test_display_labels.py` for auction bucket labels, group key/value labels, reference observation-unit labels, and comparison scope ordering.
- Updated commentary tests to expect human-facing group labels and `trading day` reference-unit caveats.
- Updated table, chart, and heatmap builder tests to expect display labels produced from normalized observations.
- Updated market-report, offline-demo, and CLI tests to assert the canonical rendered HTML contains display labels and does not expose selected internal key/value strings.

### Validation performed

- Ran `python -m pytest tests/test_display_labels.py tests/test_commentary.py tests/test_metric_tables.py tests/test_time_series_charts.py tests/test_heatmaps.py tests/test_report_sections.py tests/test_market_report.py tests/test_offline_demo.py tests/test_cli.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 175 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 80%.

### Remaining work before milestone completion

- Add an executive market overview section that focuses on high-level market trend and status before per-bucket diagnostics.
- Keep the newly recorded ppw packaging parity and Typer CLI backlog items for a later milestone after the production-format report path is stable.

### Best next deterministic step

- Add a deterministic executive market overview component/page section that summarizes high-level market trend and status across key metrics before the current per-bucket diagnostic cards and tables.

### Package phase and iteration

- Phase: 9.
- Iteration: 27.
- Delivery archive name: `mmsr_phase9_iteration27.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from iteration 26; no new open questions.
---

## 2026-05-25 — Phase 9 iteration 28: executive market overview

### Implemented

- Continued from `mmsr_phase9_iteration27.zip`.
- Added a deterministic executive market overview builder that summarizes already-computed comparison status across key metrics before per-bucket diagnostics.
- Added `ExecutiveOverviewOptions` with validated title, help text, and metric-summary limit fields.
- Wired the canonical market report summary page to render the executive overview before metric cards, comparison tables, and commentary.
- Rendered executive overview blocks through the existing accessible `HtmlBlock` and shared `<details>/<summary>` metric/help control path.
- Added report template styling for executive overview status cards.
- Updated milestone status documentation to mark Milestone 9A complete and identify Milestone 10 as the earliest incomplete roadmap item.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/overview.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_cli.py`
- `tests/test_executive_overview.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`

### Tests added or updated

- Added `tests/test_executive_overview.py` for deterministic overview status summaries, metric-summary limits, display-label preservation, missing-definition validation, and option validation.
- Updated market-report tests to assert the overview block is present on the summary page and renders before diagnostic components.
- Updated offline-demo and CLI tests to assert the mock-data production-format report includes the executive overview.

### Validation performed

- Ran `python -m pytest tests/test_executive_overview.py tests/test_market_report.py tests/test_offline_demo.py tests/test_cli.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 179 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 9A: Production-format report polish before kdb integration.

### Current milestone progress

- 100%.

### Remaining work before milestone completion

- None for Milestone 9A.
- Keep the ppw packaging parity and Typer CLI backlog items for a later milestone after the kdb integration demo path is started.

### Best next deterministic step

- Begin Milestone 10 by adding a deterministic mock-kdb integration demo that executes an example query through the existing lazy kdb client/template abstractions and adapts the result into the canonical market report path without requiring production data.

### Package phase and iteration

- Phase: 9.
- Iteration: 28.
- Delivery archive name: `mmsr_phase9_iteration28.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from iteration 26; no new open questions.


---

## 2026-05-25 — Phase 10 iteration 29: deterministic mock-kdb integration demo

### Implemented

- Continued from `mmsr_phase9_iteration28.zip`.
- Began Milestone 10 by adding a deterministic mock-kdb integration demo that executes rendered q templates through the existing `KdbMetricRunner` path.
- Added `DeterministicMockKdbClient`, `MockKdbIntegrationDemoOptions`, `MockKdbIntegrationDemoResult`, `build_mock_kdb_integration_demo_result()`, and `build_mock_kdb_integration_demo_report()`.
- The mock-kdb path executes starter `activity.q` and `liquidity.q` template queries for current and reference periods, normalizes table-shaped mock results into `MetricTimeSeries`, computes reference comparisons, and delegates into the canonical `build_market_monitor_report()` report path.
- Added the `mmsr mock-kdb-demo --output <path>` CLI command and programmatic `render_mock_kdb_demo_report_file()` helper.
- Documented the mock-kdb quickstart in README and updated roadmap/status docs to mark Milestone 10 as in progress.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `mmsr/examples/__init__.py`
- `mmsr/examples/mock_kdb_demo.py`
- `tests/test_cli.py`
- `tests/test_docs_governance.py`
- `tests/test_mock_kdb_demo.py`

### Tests added or updated

- Added `tests/test_mock_kdb_demo.py` for mock-kdb q execution, canonical report assembly, rendered HTML labels/visuals, option validation, and no-PyKX behavior.
- Updated CLI tests for the new `mock-kdb-demo` command, file rendering helper, appendix omission, help output, and programmatic options.
- Updated docs governance tests to keep the mock-kdb quickstart documented.

### Validation performed

- Ran `python -m pytest tests/test_mock_kdb_demo.py tests/test_cli.py -q`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_mock_kdb_demo.py tests/test_cli.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 188 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo.

### Current milestone progress

- 35%.

### Remaining work before milestone completion

- Add explicit output schema contracts for `activity.q` and `liquidity.q`.
- Validate starter-template output contracts inside `KdbMetricRunner` before normalization.
- Document how deterministic mock-kdb tests differ from live kdb integration tests.
- Keep live-kdb tests skipped unless a real kdb process and production-like schemas are explicitly available.

### Best next deterministic step

- Add explicit output schema contracts for `activity.q` and `liquidity.q`, validate those contracts in `KdbMetricRunner`, and cover missing-column failures with unit tests.

### Package phase and iteration

- Phase: 10.
- Iteration: 29.
- Delivery archive name: `mmsr_phase10_iteration29.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from iteration 26.
- Confirm whether starter activity/liquidity schema contracts should require only the requested metric value column or every aggregate column emitted by each template.



---

## 2026-05-25 — Phase 10 iteration 30: starter q-template output schema contracts

### Implemented

- Continued from `mmsr_phase10_iteration29.zip`.
- Added explicit output schema contracts for `activity.q` and `liquidity.q`.
- The starter contracts require `date`, `time_bucket`, caller-requested group
  columns, the requested metric value column, and sibling aggregate columns that
  each q template always emits.
- Routed `KdbMetricRunner` through template-specific output-schema validation
  before normalizing q results into `MetricTimeSeries`.
- Documented the new schema-contract boundary in the `activity.q` and
  `liquidity.q` template headers.
- Updated milestone status and roadmap text to reflect offline starter-template
  schema validation progress.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/kdb/q_templates/activity.q`
- `mmsr/kdb/q_templates/liquidity.q`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/schema_contracts.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added activity and liquidity schema-contract tests for required output column
  order, row/result validation, invalid metric-family rejection, and missing
  sibling aggregate failures.
- Added metric-runner tests proving missing starter-template output columns fail
  after query execution but before normalization.
- Re-ran the mock-kdb demo tests to verify the canonical report path still
  satisfies the stricter contracts.

### Validation performed

- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py tests/test_mock_kdb_demo.py -q`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 197 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo.

### Current milestone progress

- 65%.

### Remaining work before milestone completion

- Document how deterministic mock-kdb tests differ from live kdb integration
  tests.
- Add explicit live-kdb integration test setup guidance, including environment
  variables, table/schema assumptions, and why live tests remain skipped by
  default.
- Keep live-kdb tests skipped unless a real kdb process and production-like
  schemas are explicitly available.

### Best next deterministic step

- Document the mock-kdb versus live-kdb integration testing boundary, including
  live environment variables, table/schema assumptions, and skip behavior for
  live tests.

### Package phase and iteration

- Phase: 10.
- Iteration: 30.
- Delivery archive name: `mmsr_phase10_iteration30.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from
  iteration 26.
- Resolved the iteration 29 starter-template schema ambiguity by requiring every
  aggregate column that `activity.q` and `liquidity.q` currently emit, not only
  the requested value column. This keeps sibling aggregates available as
  deterministic observation metadata and matches the q templates' explicit
  select lists.
---

## 2026-05-25 — Phase 10 iteration 31: live-kdb integration testing boundary documentation

### Implemented

- Continued from `mmsr_phase10_iteration30.zip`.
- Documented the deterministic mock-kdb versus opt-in live-kdb integration
  testing boundary in `docs/kdb_integration_testing.md`.
- Added the required live-kdb environment-variable contract, including
  `MMSR_KDB_HOST`, `MMSR_KDB_PORT`, starter trades/quotes table variables,
  calendar table variable, reversion table variables, and bounded smoke-test
  date/symbol variables.
- Documented starter table/schema assumptions for `activity.q`, `liquidity.q`,
  and `toxicity_reversion.q`.
- Documented why `@pytest.mark.kdb_integration` tests remain skipped by default
  and how a future live harness should opt in safely.
- Linked the integration-testing guide from README and the MkDocs navigation.
- Updated roadmap and milestone status to show integration-test documentation is
  now complete while live execution remains intentionally deferred.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/kdb_integration_testing.md`
- `mkdocs.yml`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added a docs-governance test that asserts the integration-testing guide
  contains the required environment variables, live-test marker, skip behavior,
  schema-boundary terms, and documentation links from README/MkDocs.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb placeholders.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 198 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not
  installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo.

### Current milestone progress

- 85%.

### Remaining work before milestone completion

- Live kdb execution remains intentionally deferred until a real kdb+ process,
  credentials, and production-like schemas are available.
- Add a small environment-gated live-kdb smoke-test harness that safely skips
  when required variables are missing and validates a bounded starter-template
  result through the existing schema-contract boundary.

### Best next deterministic step

- Add a small environment-gated live-kdb smoke-test harness that reads the
  documented `MMSR_KDB_*` variables, skips safely when they are absent, and
  validates one bounded `activity.q` or `liquidity.q` result through the existing
  schema-contract boundary.

### Package phase and iteration

- Phase: 10.
- Iteration: 31.
- Delivery archive name: `mmsr_phase10_iteration31.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from
  iteration 26.
- Exact production kdb table names, authentication conventions, and schema
  variants remain to be confirmed before enabling live execution.



---

## 2026-05-25 — Phase 10 iteration 32: environment-gated live activity smoke harness

### Implemented

- Continued from `mmsr_phase10_iteration31.zip`.
- Added `mmsr.kdb.live_smoke.LiveKdbActivitySmokeConfig` to parse the documented
  live-kdb smoke environment variables, including host, port, trades table,
  calendar table, bounded test date, optional credentials, and optional test
  symbol.
- Added `run_live_activity_smoke()` to execute one bounded `activity.q` turnover
  request through `KdbMetricRunner`, so live smoke validation reuses the same
  output schema-contract boundary as deterministic mock-kdb tests.
- Added an optional starter-template `symbol_filter` parameter for `activity.q`
  and `liquidity.q`, allowing live smoke runs to restrict the query to
  `MMSR_KDB_TEST_SYMBOL` without broadening the report-boundary model.
- Replaced the unconditional live metric-runner placeholder with an
  environment-gated pytest that skips safely when required `MMSR_KDB_*`
  variables are missing and imports PyKX only after the gate passes.
- Updated live integration documentation, README, roadmap, and milestone status
  to describe the implemented smoke harness and the remaining real-kdb execution
  boundary.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/kdb_integration_testing.md`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/live_smoke.py`
- `mmsr/kdb/q_templates/activity.q`
- `mmsr/kdb/q_templates/liquidity.q`
- `mmsr/kdb/runner.py`
- `tests/test_docs_governance.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_live_kdb_smoke.py`

### Tests added or updated

- Added unit tests for live-smoke environment parsing, q-date parsing,
  port validation, request construction, and dynamic skip behavior.
- Added a live `@pytest.mark.kdb_integration` activity smoke test that skips when
  required environment variables are absent.
- Added a metric-runner test for starter-template symbol filtering.
- Updated q-template parameter tests for the new `symbol_filter` placeholder.
- Updated docs-governance tests to cover the implemented harness and docs links.

### Validation performed

- Ran `python -m pytest tests/test_kdb_metric_runner.py tests/test_live_kdb_smoke.py tests/test_docs_governance.py -q`: passed with 1 skipped live-kdb smoke test.
- Ran `python -m pytest -q -ra`: passed with 2 skipped live-kdb tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 204 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not
  installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo.

### Current milestone progress

- 95%.

### Remaining work before milestone completion

- Execute the environment-gated live activity smoke test against a real kdb+
  process with confirmed production-like schemas.
- Record exact source table/schema findings from live execution.
- Decide whether to add a matching `liquidity.q` live smoke slice after the
  activity smoke has been validated against a real environment.
- Keep reversion live validation skipped until venue-trade and primary-quote
  production schemas are confirmed.

### Best next deterministic step

- Run `python -m pytest -m kdb_integration tests/test_live_kdb_smoke.py` against
  a confirmed production-like kdb+ process with the documented `MMSR_KDB_*`
  variables set, then record the observed live schema and output behavior.

### Package phase and iteration

- Phase: 10.
- Iteration: 32.
- Delivery archive name: `mmsr_phase10_iteration32.zip`.

### Open questions

- Existing ppw extras and Typer CLI timing questions remain tracked from
  iteration 26.
- Exact production kdb table names, authentication conventions, and schema
  variants remain to be confirmed before live execution can be treated as
  validated.
- The first implemented live smoke covers `activity.q`; a separate deterministic
  step should decide whether `liquidity.q` needs its own live smoke slice before
  closing Milestone 10.


---

## 2026-05-25 — Phase 10 iteration 33: environment-gated live liquidity smoke harness

### Implemented

- Continued from `mmsr_phase10_iteration32.zip`.
- Added `mmsr.kdb.live_smoke.LiveKdbLiquiditySmokeConfig` to mirror the existing
  activity smoke harness for `liquidity.q`.
- Added `REQUIRED_LIVE_LIQUIDITY_SMOKE_ENV_VARS` and `run_live_liquidity_smoke()`
  so a bounded `quoted_spread_bps` request can be executed through
  `KdbMetricRunner` against a real kdb+ process once the documented
  `MMSR_KDB_*` variables are configured.
- Kept live validation opt-in and environment-gated; the new liquidity smoke test
  skips safely when required variables are absent and imports PyKX only after the
  gate passes.
- Updated live integration documentation, README, roadmap, and milestone status
  to state that both starter templates now have environment-gated live smoke
  harnesses.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/kdb_integration_testing.md`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/live_smoke.py`
- `tests/test_docs_governance.py`
- `tests/test_live_kdb_smoke.py`

### Tests added or updated

- Added unit tests for liquidity live-smoke required environment variables,
  environment parsing, q-date parsing, port validation, and bounded
  `quoted_spread_bps` request construction.
- Added an environment-gated `@pytest.mark.kdb_integration` liquidity smoke test
  that skips safely when required variables are missing.
- Updated docs-governance tests to require documentation of
  `LiveKdbLiquiditySmokeConfig` and the liquidity live smoke test.

### Validation performed

- Ran `python -m pytest tests/test_live_kdb_smoke.py tests/test_docs_governance.py -q`: passed with 2 skipped live-kdb smoke tests.
- Ran `python -m pytest -q -ra`: passed with 3 skipped live-kdb/schema tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed collection.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo.

### Current milestone progress

- 98%.

### Remaining work before milestone completion

- Execute the environment-gated live activity and liquidity smoke tests against a
  real kdb+ process with confirmed production-like schemas.
- Record exact source table/schema findings from live execution.
- Keep reversion live validation skipped until venue-trade and primary-quote
  production schemas are confirmed.

### Best next deterministic step

- Run `python -m pytest -m kdb_integration tests/test_live_kdb_smoke.py` against
  a confirmed production-like kdb+ process with the documented `MMSR_KDB_*`
  variables set, then record observed activity and liquidity source schemas and
  output behavior.

### Package phase and iteration

- Phase: 10.
- Iteration: 33.
- Delivery archive name: `mmsr_phase10_iteration33.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain to be confirmed before live execution can be treated as
  validated.
- Reversion live validation remains blocked until venue-trade and primary-quote
  production schemas are confirmed.


---

## 2026-05-25 — Phase 10 iteration 34: documentation dependency group and packaging setup paths

### Implemented

- Continued from `mmsr_phase10_iteration33.zip`.
- Added a dedicated Poetry `doc` dependency group for documentation tooling while
  keeping runtime dependencies unchanged.
- Documented runtime-only, kdb-extra, contributor `dev`, and documentation `doc`
  installation profiles in README.
- Added a tox documentation environment and a GitHub Actions documentation build
  job that install only the `doc` group before running `mkdocs build --strict`.
- Updated the ppw packaging parity roadmap/status notes to record the completed
  dependency-group slice and the remaining CLI/Typer decision.

### Files changed

- `.github/workflows/ci.yml`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `pyproject.toml`
- `tests/test_packaging_metadata.py`
- `tox.ini`

### Tests added or updated

- Added `tests/test_packaging_metadata.py` covering lean runtime dependencies,
  explicit `dev` and `doc` Poetry groups, README installation profile docs, tox
  documentation build wiring, CI documentation build wiring, and roadmap
  tracking for the remaining CLI ergonomics work.
- Existing governance docs tests continue to validate the packaging backlog and
  live-kdb documentation boundary.

### Validation performed

- Ran `python -m pytest tests/test_packaging_metadata.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 215 tests.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.
- `mkdocs build --strict` was wired into tox and CI but not executed locally
  because the new `doc` dependency group is not installed in this execution
  environment.

### Current milestone

- Milestone 10: kdb integration demo remains the earliest incomplete milestone.
- Offline backlog item advanced: ppw packaging parity and CLI ergonomics.

### Current milestone progress

- Milestone 10 remains 98%.
- ppw packaging parity and CLI ergonomics is estimated at 45% after adding the
  explicit `doc` group, documenting setup paths, and wiring docs validation.

### Remaining work before milestone completion

- Milestone 10 still requires execution of the environment-gated live starter
  smoke tests against a confirmed production-like kdb+ process.
- ppw packaging parity still needs a dedicated Typer CLI migration decision and,
  if accepted, tests that preserve current `offline-demo` and `mock-kdb-demo`
  behavior.

### Best next deterministic step

- If live kdb+ remains unavailable, evaluate the Typer CLI migration as a
  dedicated offline step by first adding CLI behavior snapshots for the current
  argparse commands before changing the CLI implementation.

### Package phase and iteration

- Phase: 10.
- Iteration: 34.
- Delivery archive name: `mmsr_phase10_iteration34.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain to be confirmed before live execution can be treated as
  validated.
- Reversion live validation remains blocked until venue-trade and primary-quote
  production schemas are confirmed.
- Typer CLI migration remains undecided; the safe first step is to preserve
  current command behavior in tests before changing dependencies or CLI code.



---

## 2026-05-25 — Phase 10 iteration 35: CLI behavior snapshots before implementation decision

### Implemented

- Continued from `mmsr_phase10_iteration34.zip`.
- Honored the user direction to defer actual live-kdb work and advance later
  offline stages instead.
- Added pre-migration CLI behavior snapshots for the current argparse command
  surface before making any Typer or CLI implementation change.
- Snapshotted top-level help, `offline-demo` and `mock-kdb-demo` default
  arguments, override argument parsing, option presence in command help, and the
  offline/mock-kdb safety language that must survive a future CLI migration.
- Updated roadmap and milestone status so the CLI ergonomics backlog now records
  the completed pre-migration snapshot slice and the remaining explicit
  argparse-vs-Typer decision.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `tests/test_cli_behavior_snapshots.py`
- `tests/test_packaging_metadata.py`

### Tests added or updated

- Added `tests/test_cli_behavior_snapshots.py` with focused parser behavior
  snapshots for `offline-demo` and `mock-kdb-demo`.
- Updated `tests/test_packaging_metadata.py` so governance tests track the new
  snapshot milestone and the revised remaining CLI decision.

### Validation performed

- Ran `python -m pytest tests/test_cli_behavior_snapshots.py -q`: passed.
- Ran `python -m pytest tests/test_cli_behavior_snapshots.py tests/test_packaging_metadata.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 225 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction.
- Offline backlog item advanced: ppw packaging parity and CLI ergonomics.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- ppw packaging parity and CLI ergonomics is estimated at 65% after adding
  pre-migration CLI behavior snapshots.

### Remaining work before milestone completion

- Milestone 10 still requires execution of the environment-gated live starter
  smoke tests against a confirmed production-like kdb+ process when that work is
  resumed.
- ppw packaging parity still needs the explicit CLI implementation decision:
  keep argparse and mark the ergonomics backlog complete for now, or migrate one
  command at a time to Typer while preserving the new behavior snapshots and
  existing render-path tests.

### Best next deterministic step

- Decide whether the snapshotted CLI should remain argparse for this package
  phase or migrate one command to Typer in a dedicated step with no behavior
  changes.

### Package phase and iteration

- Phase: 10.
- Iteration: 35.
- Delivery archive name: `mmsr_phase10_iteration35.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Typer CLI migration remains undecided; behavior snapshots are now in place to
  make that decision safer.


---

## 2026-05-25 — Phase 10 iteration 36: deterministic symbol anomaly page foundation

### Implemented

- Continued from `mmsr_phase10_iteration35.zip`.
- Honored the user direction to keep actual live-kdb work deferred and advance
  later offline report stages.
- Made the CLI implementation decision for this phase: keep the existing
  argparse command surface because it is small, behavior-snapshotted, and does
  not justify adding Typer as a new dependency at this point.
- Added deterministic symbol-level anomaly page helpers:
  - `SymbolAnomalyPageOptions`.
  - `select_symbol_anomalies()`.
  - `build_symbol_anomaly_page()`.
- Implemented conservative symbol anomaly ranking from already-computed
  `MetricComparison` facts using status, adverse-tail diagnostics, z-score
  magnitude, and absolute percentage-change magnitude.
- Deduplicated symbol anomaly output to the worst comparison per symbol and
  excluded normal rows by default, while retaining an explicit normal-row
  watchlist mode.
- Wired the canonical `build_market_monitor_report()` path to automatically
  insert a symbol anomaly page when symbol-scoped anomaly rows are present, with
  an opt-out through `MarketReportOptions.include_symbol_anomaly_page`.
- Documented the symbol anomaly page behavior in README, roadmap, and milestone
  status.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/symbols.py`
- `tests/test_packaging_metadata.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added `tests/test_symbol_anomaly_pages.py` covering symbol ranking,
  deduplication, normal-row watchlist mode, metric-table rendering, no-symbol
  no-op behavior, option validation, and canonical report integration.
- Updated `tests/test_packaging_metadata.py` to record the phase decision to keep
  argparse rather than migrate to Typer now.

### Validation performed

- Ran `python -m pytest tests/test_symbol_anomaly_pages.py -q`: passed.
- Ran `python -m pytest tests/test_symbol_anomaly_pages.py tests/test_packaging_metadata.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 232 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction.
- Active offline milestone: Symbol-level anomaly pages.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- ppw packaging parity and CLI ergonomics is complete for this phase after the
  explicit keep-argparse decision.
- Symbol-level anomaly pages are estimated at 35% after adding deterministic
  selection, page assembly, canonical report integration, docs, and tests.

### Remaining work before milestone completion

- Add deterministic synthetic symbol fixtures so the offline demo visibly
  exercises the symbol anomaly page without real market data.
- Add optional per-symbol detail pages with time-series trends and intraday
  heatmap diagnostics for selected symbols.
- Add configuration-driven symbol group key preferences if production schemas use
  client-specific identifiers beyond the default aliases.

### Best next deterministic step

- Add offline synthetic symbol comparison fixtures and render-path tests so
  `mmsr offline-demo` can show the new symbol anomaly page without using real
  market data.

### Package phase and iteration

- Phase: 10.
- Iteration: 36.
- Delivery archive name: `mmsr_phase10_iteration36.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Future Typer migration remains optional and should only be reconsidered if the
  CLI grows enough to justify a new dependency.


---

## 2026-05-25 — Phase 10 iteration 37: offline symbol anomaly fixtures and render coverage

### Implemented

- Continued from `mmsr_phase10_iteration36.zip`.
- Kept live kdb work deferred per user direction and advanced the offline
  symbol-level anomaly milestone.
- Added deterministic synthetic symbol-scoped comparison fixtures for the
  offline demo:
  - `build_offline_symbol_metric_comparisons()`.
  - Symbol rows for `7203`, `6758`, and `8306`.
  - Fixture metadata that distinguishes market-level sample rows from
    `symbol_anomaly_sample` rows.
- Routed the synthetic symbol rows through the existing
  `compare_metric_timeseries()` reference-comparison engine rather than
  hand-coding report-only anomalies.
- Included the symbol comparison rows in `build_offline_metric_comparisons()` and
  `build_offline_sample_metrics()` so `mmsr offline-demo` visibly renders the
  `Symbol Anomalies` page without live kdb+, PyKX, real market data, or LLM
  access.
- Polished symbol scope formatting so rendered rows use human-readable
  `Symbol: 7203` style labels rather than raw `symbol=7203` prefixes.
- Updated README, roadmap, and milestone status to record the completed
  offline-demo fixture/render slice.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/examples/__init__.py`
- `mmsr/examples/offline_fixtures.py`
- `mmsr/report/symbols.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_offline_fixtures.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added fixture coverage for `build_offline_symbol_metric_comparisons()`,
  including sample size, confidence, alert status, deterministic symbols,
  fixture metadata, and z-score availability.
- Updated offline-demo render-path tests so the default report includes
  `Symbol Anomalies`, shows all three synthetic symbols, and avoids raw
  `symbol=` scope text.
- Updated canonical market-report tests for the now-visible symbol anomaly page
  in the offline sample input.
- Extended symbol anomaly page tests to assert human-readable symbol scope text.

### Validation performed

- Ran `python -m pytest tests/test_offline_fixtures.py tests/test_offline_demo.py tests/test_market_report.py tests/test_symbol_anomaly_pages.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 233 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction.
- Active offline milestone: Symbol-level anomaly pages.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Symbol-level anomaly pages are estimated at 60% after deterministic selection,
  summary-page assembly, canonical report integration, and visible offline-demo
  fixture coverage.

### Remaining work before milestone completion

- Add optional per-symbol detail pages with time-series trends and intraday
  heatmap diagnostics for selected symbols.
- Add configuration-driven symbol group key preferences if production schemas use
  client-specific identifiers beyond the default aliases.

### Best next deterministic step

- Add a deterministic per-symbol detail page builder for selected symbol
  anomalies using existing `MetricTimeSeries` rows where symbol-scoped series are
  available, without querying kdb or adding new dependencies.

### Package phase and iteration

- Phase: 10.
- Iteration: 37.
- Delivery archive name: `mmsr_phase10_iteration37.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production symbol identifier preferences beyond `symbol`, `ticker`,
  `security_code`, and `sym` remain to be confirmed.

---

## 2026-05-25 — Phase 10 iteration 38: per-symbol detail pages from normalized series

### Implemented

- Continued from `mmsr_phase10_iteration37.zip`.
- Kept live kdb work deferred per user direction and advanced the offline
  symbol-level anomaly milestone.
- Added deterministic optional per-symbol detail page support:
  - `SymbolDetailPageOptions`.
  - `build_symbol_detail_pages()`.
  - Existing symbol anomaly ranking is reused so detail pages follow the same
    selected-symbol order as the summary anomaly page.
- Added `MarketReportInput.symbol_series` so callers can provide normalized
  symbol-scoped `MetricTimeSeries` rows without mixing them into the market-level
  intraday detail page.
- Added `MarketReportOptions.include_symbol_detail_pages`,
  `symbol_detail_page_title_template`, `symbol_detail_help_text`, and
  `max_symbol_detail_pages`.
- Wired `build_market_monitor_report()` to insert per-symbol detail pages only
  when selected anomaly symbols also have symbol-scoped time-series rows.
- Added deterministic offline symbol detail fixtures via
  `build_offline_symbol_metric_time_series()` and routed `mmsr offline-demo`
  through them so the mock report visibly renders per-symbol trend charts and
  intraday heatmaps without live kdb+, PyKX, real market data, or LLM access.
- Updated README, roadmap, milestone status, and this journal.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/examples/__init__.py`
- `mmsr/examples/offline_demo.py`
- `mmsr/examples/offline_fixtures.py`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/symbols.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_offline_fixtures.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added symbol-detail page tests for existing-series filtering, max-symbol
  limiting, no-series no-op behavior, option validation, canonical report
  integration, and disabling detail pages.
- Added offline fixture tests for deterministic symbol detail time series.
- Updated offline-demo render-path tests so the generated mock report includes
  `Symbol 7203 Detail`, `Symbol 6758 Detail`, and `Symbol 8306 Detail` pages.
- Updated market report option validation tests for the new symbol-detail fields.

### Validation performed

- Ran `python -m pytest tests/test_symbol_anomaly_pages.py tests/test_offline_fixtures.py tests/test_offline_demo.py tests/test_market_report.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: collected 244 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction.
- Active offline milestone: Symbol-level anomaly pages.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Symbol-level anomaly pages are estimated at 80% after deterministic selection,
  summary-page assembly, per-symbol detail pages, canonical report integration,
  and visible offline-demo fixture coverage.

### Remaining work before milestone completion

- Add configuration-driven symbol group key preferences if production schemas use
  client-specific identifiers beyond the default aliases.
- Consider a compact symbol-detail navigation/index section if production reports
  routinely include many selected symbols.

### Best next deterministic step

- Add `MarketReportOptions.symbol_group_keys` and pass it through the anomaly and
  detail page builders so client-specific symbol identifiers can be configured
  without changing report-layer code.

### Package phase and iteration

- Phase: 10.
- Iteration: 38.
- Delivery archive name: `mmsr_phase10_iteration38.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production symbol identifier preferences beyond `symbol`, `ticker`,
  `security_code`, and `sym` remain to be confirmed.

---

## 2026-05-25 — Phase 10 iteration 39: configurable symbol identifier keys

### Implemented

- Continued from `mmsr_phase10_iteration38.zip`.
- Kept live kdb work deferred per user direction and completed the offline
  symbol-level anomaly milestone for this package phase.
- Added `MarketReportOptions.symbol_group_keys` with the same default aliases as
  the lower-level symbol page builders: `symbol`, `ticker`, `security_code`, and
  `sym`.
- Passed the configured symbol key order through both `SymbolAnomalyPageOptions`
  and `SymbolDetailPageOptions`, so client-specific identifiers such as
  `client_symbol`, `issue_code`, or `local_code` can drive anomaly selection and
  per-symbol detail pages without report-layer code changes.
- Exported `DEFAULT_SYMBOL_GROUP_KEYS` from `mmsr.report`.
- Documented the configured symbol-key behavior in README.
- Updated roadmap and milestone status.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `tests/test_market_report.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added a canonical report-builder test proving custom `symbol_group_keys`
  enable both the symbol anomaly page and matching per-symbol detail page for a
  non-default group key.
- Added `MarketReportOptions.symbol_group_keys` validation coverage for empty
  key lists and blank key aliases.

### Validation performed

- Ran `python -m pytest tests/test_symbol_anomaly_pages.py tests/test_market_report.py -q`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_symbol_anomaly_pages.py tests/test_market_report.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed; `python -m pytest --collect-only`
  reported 240 tests collected.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction.
- Active offline milestone: Symbol-level anomaly pages.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Symbol-level anomaly pages are 100% complete for this package phase after
  deterministic selection, summary-page assembly, per-symbol detail pages,
  offline-demo fixture coverage, and configurable symbol identifier keys.

### Remaining work before milestone completion

- No required symbol-level anomaly work remains for this package phase.
- A compact symbol-detail navigation/index section can be revisited later if
  production reports routinely include many selected symbols.

### Best next deterministic step

- Start the sector, segment, and market-cap drilldown milestone by adding a small
  typed drilldown configuration model and deterministic comparison filtering
  helper for existing normalized facts.

### Package phase and iteration

- Phase: 10.
- Iteration: 39.
- Delivery archive name: `mmsr_phase10_iteration39.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production symbol-detail page count and navigation preferences remain
  client-specific and can be revisited if reports include many selected symbols.



---

## 2026-05-25 — Phase 10 iteration 40: drilldown comparison selector

### Implemented

- Continued from `mmsr_phase10_iteration39.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Started the sector, segment, and market-cap drilldown milestone with a small
  typed selection layer for existing normalized comparison facts.
- Added `DrilldownSelectionOptions` with configurable drilldown group keys,
  row limits, status filters, symbol group aliases, and symbol-scoped row
  handling.
- Added `select_drilldown_comparisons()` to select comparisons containing
  configured group dimensions such as `market_cap_bucket`, `market_segment`,
  `segment`, and `sector`, excluding symbol-scoped rows by default so the future
  drilldown page will not duplicate symbol anomaly pages.
- Added `drilldown_scope_key()` to preserve configured key order for future
  deterministic page/table grouping.
- Exported the drilldown selector helpers from `mmsr.report`.
- Documented the drilldown selector in README, roadmap, and milestone status.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/drilldowns.py`
- `tests/test_drilldowns.py`

### Tests added or updated

- Added `tests/test_drilldowns.py` with coverage for default sector/segment/
  market-cap dimensions, symbol-scoped exclusion, optional symbol-scoped
  inclusion, custom keys, status filters, row limits, configured scope ordering,
  and validation of empty keys/statuses and negative limits.

### Validation performed

- Ran `python -m pytest tests/test_drilldowns.py -q`: passed.
- Ran `python -m pytest tests/test_drilldowns.py tests/test_import.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 246 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, and market-cap drilldowns are estimated at 25% after adding
  the typed selector/options layer, deterministic comparison filtering, exports,
  documentation, and focused tests.

### Remaining work before milestone completion

- Build a deterministic drilldown report page with metric help controls.
- Wire the drilldown page into `build_market_monitor_report()` behind report
  options.
- Add offline-demo fixture coverage so sector, segment, and market-cap drilldown
  pages are visibly rendered without live kdb+, PyKX, real market data, or LLM
  access.

### Best next deterministic step

- Add `build_drilldown_report_page()` that formats selected drilldown
  comparisons as a metric table with metric help and human-readable group labels,
  without calculating new metrics or querying kdb+.

### Package phase and iteration

- Phase: 10.
- Iteration: 40.
- Delivery archive name: `mmsr_phase10_iteration40.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector/segment/market-cap group key preferences beyond
  `market_cap_bucket`, `market_segment`, `segment`, and `sector` remain
  client-specific and can be configured through the selector options for now.



---

## 2026-05-25 — Phase 10 iteration 41: drilldown report page builder

### Implemented

- Continued from `mmsr_phase10_iteration40.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Added `DrilldownReportPageOptions` for deterministic sector/segment/market-cap
  drilldown page presentation.
- Added `build_drilldown_report_page()` to select existing normalized
  `MetricComparison` facts and render them as a `ReportPage` with a documented
  `MetricTable`.
- Preserved registry-backed metric help for every drilldown table row.
- Added human-readable drilldown scope labels for report date, auction/intraday
  bucket, market-cap bucket, segment, sector, and custom group keys while
  preserving configured drilldown key order.
- Exported the drilldown page builder and options from `mmsr.report`.
- Documented the page builder in README, roadmap, and milestone status.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/drilldowns.py`
- `tests/test_drilldowns.py`

### Tests added or updated

- Added drilldown page-builder coverage for metric-help-backed table rendering,
  human-readable group labels, HTML rendering, custom selection options, no-row
  no-op behavior, missing metric definitions, and page-option validation.
- Updated drilldown tests to cover the exported report-page builder in addition
  to the selector.

### Validation performed

- Ran `python -m pytest tests/test_drilldowns.py -q`: passed.
- Ran `python -m pytest tests/test_drilldowns.py tests/test_import.py -q`: passed.
- Ran `python -m pytest tests/test_drilldowns.py tests/test_import.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 252 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, and market-cap drilldowns are estimated at 55% after adding
  typed selection, deterministic comparison filtering, report-page table
  rendering, metric help, human-readable group labels, exports, documentation,
  and focused tests.

### Remaining work before milestone completion

- Wire the drilldown page into `build_market_monitor_report()` behind report
  options.
- Add offline-demo fixture coverage so sector, segment, and market-cap drilldown
  pages are visibly rendered without live kdb+, PyKX, real market data, or LLM
  access.

### Best next deterministic step

- Add `MarketReportOptions.include_drilldown_page`, drilldown page labels/limits,
  and `drilldown_group_keys`, then insert `build_drilldown_report_page()` into
  the canonical market report only when matching group-level comparison rows are
  present.

### Package phase and iteration

- Phase: 10.
- Iteration: 41.
- Delivery archive name: `mmsr_phase10_iteration41.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector/segment/market-cap group key preferences beyond
  `market_cap_bucket`, `market_segment`, `segment`, and `sector` remain
  client-specific and can be configured through the drilldown options for now.


---

## 2026-05-25 — Phase 10 iteration 42: canonical drilldown report wiring

### Implemented

- Continued from `mmsr_phase10_iteration41.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Added canonical market-report options for sector/segment/market-cap drilldown
  pages:
  - `include_drilldown_page`
  - `drilldown_page_title`
  - `drilldown_table_title`
  - `drilldown_help_text`
  - `max_drilldown_rows`
  - `drilldown_group_keys`
- Wired `build_drilldown_report_page()` into `build_market_monitor_report()`.
  The page is inserted only when matching group-level comparison rows are
  present and remains opt-out through `include_drilldown_page=False`.
- Reused the existing symbol key configuration when excluding symbol-scoped rows
  from drilldowns, so custom symbol identifiers do not duplicate symbol anomaly
  pages.
- Updated canonical market-report, offline-demo, mock-kdb-demo, and custom symbol
  key tests for the new deterministic page order.
- Documented canonical drilldown page wiring in README, roadmap, and milestone
  status.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/market_report.py`
- `tests/test_market_report.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_offline_demo.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added market-report coverage for:
  - default drilldown page insertion when group-level rows exist;
  - disabling the page through `include_drilldown_page=False`;
  - no-op behavior when no group-level rows are present;
  - custom drilldown title/table/help text, group keys, and row limits;
  - validation for drilldown labels, row limits, and group keys.
- Updated offline-demo and mock-kdb-demo render/path tests so the drilldown page
  is visible from existing synthetic group-level comparison facts.
- Updated custom symbol-key coverage so custom symbol rows are excluded from
  drilldowns when `symbol_group_keys` is configured.

### Validation performed

- Ran `python -m pytest tests/test_market_report.py -q`: passed.
- Ran `python -m pytest tests/test_market_report.py tests/test_offline_demo.py -q`:
  passed.
- Ran `python -m pytest tests/test_drilldowns.py tests/test_market_report.py tests/test_offline_demo.py -q`:
  passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 255 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, and market-cap drilldowns are complete for the current phase
  after adding typed selection, deterministic comparison filtering, report-page
  table rendering, metric help, human-readable group labels, canonical report
  wiring, offline/mock-kdb demo visibility, documentation, and tests.

### Remaining work before milestone completion

- Add richer sector-specific offline fixture rows once production sector naming
  conventions are confirmed.
- Live production validation remains deferred until kdb+ schemas and credentials
  are available.

### Best next deterministic step

- Add optional offline-demo and mock-kdb-demo option/CLI passthroughs for
  drilldown page inclusion and row limits so sample reports can demonstrate both
  the default drilldown page and opt-out behavior from the command line.

### Package phase and iteration

- Phase: 10.
- Iteration: 42.
- Delivery archive name: `mmsr_phase10_iteration42.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector naming and any client-specific sector taxonomy remain
  unconfirmed; current drilldown keys stay configurable through
  `drilldown_group_keys`.


---

## 2026-05-25 — Phase 10 iteration 43: drilldown demo CLI passthroughs

### Implemented

- Continued from `mmsr_phase10_iteration42.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Added drilldown presentation passthroughs to `OfflineDemoReportOptions`:
  - `include_drilldown_page`
  - `max_drilldown_rows`
- Added the same passthroughs to `MockKdbIntegrationDemoOptions`.
- Passed both option sets into canonical `MarketReportOptions` so the demos still
  use the single production-format report builder.
- Added `--no-drilldown-page` and `--max-drilldown-rows` to both
  `mmsr offline-demo` and `mmsr mock-kdb-demo`.
- Updated CLI behavior snapshots, demo render-path tests, README, roadmap, and
  milestone status for the new deterministic controls.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `mmsr/examples/mock_kdb_demo.py`
- `mmsr/examples/offline_demo.py`
- `tests/test_cli.py`
- `tests/test_cli_behavior_snapshots.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_offline_demo.py`

### Tests added or updated

- Added offline-demo option tests for disabling the drilldown page, limiting
  drilldown rows, and validating negative row limits.
- Added mock-kdb-demo option tests for disabling the drilldown page, limiting
  drilldown rows, and validating negative row limits.
- Added CLI render-path tests for `--no-drilldown-page`.
- Updated CLI behavior snapshots to cover the new `--no-drilldown-page` and
  `--max-drilldown-rows` arguments.
- Updated programmatic render-file option tests to prove drilldown opt-out flows
  through the public file-rendering helpers.

### Validation performed

- Ran `python -m pytest tests/test_offline_demo.py tests/test_mock_kdb_demo.py tests/test_cli.py tests/test_cli_behavior_snapshots.py -q`: passed.
- Ran `python -m pytest tests/test_offline_demo.py tests/test_mock_kdb_demo.py tests/test_cli.py tests/test_cli_behavior_snapshots.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 262 tests.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, and market-cap drilldowns are complete for the current phase
  after adding typed selection, deterministic comparison filtering, report-page
  table rendering, metric help, human-readable group labels, canonical report
  wiring, demo/CLI passthroughs, documentation, and tests.

### Remaining work before milestone completion

- Add richer sector-specific offline fixture rows once production sector naming
  conventions are confirmed.
- Live production validation remains deferred until kdb+ schemas and credentials
  are available.

### Best next deterministic step

- Add MkDocs quickstart coverage for the demo drilldown CLI options so the docs
  site and README stay aligned before adding any more report behavior.

### Package phase and iteration

- Phase: 10.
- Iteration: 43.
- Delivery archive name: `mmsr_phase10_iteration43.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector naming and any client-specific sector taxonomy remain
  unconfirmed; current drilldown keys stay configurable through
  `drilldown_group_keys`.


---

## 2026-05-25 — Phase 10 iteration 44: MkDocs drilldown quickstart alignment

### Implemented

- Continued from `mmsr_phase10_iteration43.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Expanded `docs/index.md` from a placeholder landing page into a concise
  MkDocs quickstart covering installation, deterministic tests, documentation
  builds, offline-demo rendering, mock-kdb-demo rendering, and live-kdb testing
  boundaries.
- Added MkDocs demo examples for sector, segment, and market-cap drilldown
  controls using `--max-drilldown-rows` and `--no-drilldown-page` for both
  `offline-demo` and `mock-kdb-demo`.
- Updated the README demo quickstart so it shows the same drilldown opt-out and
  compact-table command examples as the MkDocs site.
- Updated roadmap and milestone-status evidence for documentation/CLI alignment.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/index.md`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added `test_mkdocs_quickstart_documents_drilldown_demo_options()` to ensure
  the MkDocs quickstart and README both document offline/mock-kdb demo commands,
  `--max-drilldown-rows`, `--no-drilldown-page`, and the offline/mock-kdb safety
  boundaries.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py -q`: passed after fixing
  the MkDocs quickstart wording to include the exact offline safety phrase.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_cli_behavior_snapshots.py tests/test_cli.py -q`:
  passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 263 tests.
- Ran `python -m mkdocs build --strict`: could not run because `mkdocs` is not
  installed in this environment.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns plus
  documentation/CLI alignment.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, market-cap drilldowns, demo CLI passthroughs, and MkDocs/README
  quickstart alignment are complete for the current package phase.

### Remaining work before milestone completion

- Add richer sector-specific offline fixture rows once production sector naming
  conventions are confirmed.
- Live production validation remains deferred until kdb+ schemas and credentials
  are available.

### Best next deterministic step

- Add a production-readiness checklist documenting the sector taxonomy and kdb
  schema fields required before implementing richer production-specific drilldown
  fixtures or live validation.

### Package phase and iteration

- Phase: 10.
- Iteration: 44.
- Delivery archive name: `mmsr_phase10_iteration44.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector naming and any client-specific sector taxonomy remain
  unconfirmed; current drilldown keys stay configurable through
  `drilldown_group_keys`.

---

## 2026-05-25 — Phase 10 iteration 45: Production readiness checklist

### Implemented

- Continued from `mmsr_phase10_iteration44.zip`.
- Kept live kdb work deferred because no real kdb+ process, credentials, or
  production-like schemas are available.
- Added `docs/production_readiness.md` as the checklist required before richer
  sector-specific offline fixtures or broader live validation.
- Documented sector taxonomy ownership/versioning, segment label confirmation,
  market-cap bucket thresholds, symbol identifier conventions, effective-dated
  metadata joins, unknown/suspended instrument handling, and normalized
  group-key mapping.
- Documented required kdb+ source fields for the trading calendar, `activity.q`
  trades table, `liquidity.q` quotes table, `toxicity_reversion.q` venue-trade
  and primary-quote tables, and symbol metadata/taxonomy joins.
- Added the checklist to MkDocs navigation and linked it from the MkDocs
  quickstart and README.
- Updated roadmap and milestone-status evidence so the checklist becomes the
  documented prerequisite for richer production-specific drilldown fixtures.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/index.md`
- `docs/production_readiness.md`
- `mkdocs.yml`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added `test_docs_document_production_readiness_checklist()` to verify the
  checklist is present, linked from README/MkDocs, listed in MkDocs navigation,
  and referenced by roadmap/status evidence.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_cli_behavior_snapshots.py tests/test_cli.py -q`:
  passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected skips for live-kdb/schema
  tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 264 tests.
- Ran `python -m mkdocs build --strict`: could not run because `mkdocs` is not
  installed in this environment.
- Ran `python -m mypy mmsr tests`: could not run because `mypy` is not installed
  in this environment.
- Ran `python -m black --check mmsr tests`: could not run because `black` is not
  installed in this environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Milestone 10: kdb integration demo remains deferred by user direction and
  unavailable live kdb+ infrastructure.
- Active offline milestone: Sector, segment, and market-cap drilldowns plus
  production-readiness documentation.

### Current milestone progress

- Milestone 10 remains 98% because no live kdb+ endpoint is available and the
  user requested skipping actual kdb-related work for now.
- Sector, segment, market-cap drilldowns, demo CLI passthroughs, MkDocs/README
  quickstart alignment, and production-readiness documentation are complete for
  the current package phase.

### Remaining work before milestone completion

- Use the production-readiness checklist to confirm client taxonomy, metadata
  joins, and kdb+ source schemas before adding richer sector-specific offline
  fixture rows.
- Live production validation remains deferred until kdb+ schemas and credentials
  are available.

### Best next deterministic step

- Add a metadata-ready offline fixture sample that exercises sector drilldowns
  only after the checklist's taxonomy and schema assumptions are either
  confirmed or explicitly documented as synthetic.

### Package phase and iteration

- Phase: 10.
- Iteration: 45.
- Delivery archive name: `mmsr_phase10_iteration45.zip`.

### Open questions

- Exact production kdb table names, authentication conventions, and schema
  variants remain deferred with live-kdb work.
- Reversion live validation remains deferred until venue-trade and primary-quote
  production schemas are confirmed.
- Production sector naming and any client-specific sector taxonomy remain
  unconfirmed; current drilldown keys stay configurable through
  `drilldown_group_keys`.



## 2026-05-25 — Phase 10 iteration 46: Production toxicity reversion report page

### Implemented

- Continued from `mmsr_phase10_iteration45.zip`.
- Corrected direction away from offline/demo-first work after user feedback and
  refocused on production report behavior assuming the kdb reversion query output
  is correct.
- Added `mmsr.report.toxicity` with `ToxicityReversionPageOptions` and
  `build_toxicity_reversion_page()`.
- The new production report page consumes normalized
  `primary_quote_reversion_*_bps` `MetricTimeSeries` rows, groups them by
  report date, intraday bucket, and remaining production group keys, and renders
  deterministic SVG reversion curves.
- The required visual semantics are now implemented in the canonical report path:
  horizon progression on the x-axis, reversion in bps on the y-axis, and one
  line per venue.
- Added low-confidence sample-size metadata display and deterministic toxicity
  commentary from existing reversion curve facts.
- Wired the page into `build_market_monitor_report()` with opt-out and limit
  controls on `MarketReportOptions`.
- Exported the new production report builder from `mmsr.report`.
- Updated README, roadmap, and milestone status to describe the production
  report feature rather than treating the curve as an offline/demo placeholder.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/toxicity.py`
- `tests/test_toxicity_reversion_report.py`

### Tests added or updated

- Added `tests/test_toxicity_reversion_report.py`.
- Tests cover direct toxicity page construction from normalized kdb-style metric
  rows, no-op behavior without reversion rows, context chart limits, missing
  metric definitions, canonical market-report insertion, and report-level opt-out.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion_report.py -q`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion_report.py tests/test_toxicity_reversion.py -q`:
  passed.
- Ran `python -m pytest tests/test_market_report.py tests/test_html_rendering.py tests/test_import.py -q`:
  passed.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m pytest --collect-only -q`: passed and collected 270 tests.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Cross-venue toxicity reversion production report features.
- Milestone 10 live kdb validation remains unavailable, but production feature
  work now assumes the kdb query output schema is correct as requested.

### Current milestone progress

- Cross-venue toxicity/reversion production report page: 85% complete.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- Add production report controls for selecting which toxicity contexts should be
  rendered first when there are many date/bucket/group combinations.
- Optionally exclude reversion metric series from the generic intraday detail
  page once the dedicated toxicity page is confirmed as the canonical display for
  that metric family.
- Live production validation remains blocked by missing kdb+ endpoint and
  credentials, not by report-layer implementation.

### Best next deterministic step

- Add deterministic context-ranking options for the Cross-Venue Toxicity page so
  production reports with many venue/horizon groups show the most important
  curves first.

### Package phase and iteration

- Phase: 10.
- Iteration: 46.
- Delivery archive name: `mmsr_phase10_iteration46.zip`.

### Open questions

- Should reversion metrics be excluded from the generic `Intraday Detail` page
  now that the production `Cross-Venue Toxicity` page renders the canonical
  venue/horizon curve?
- Which production grouping dimension should rank toxicity contexts first when
  many sector/symbol/bucket combinations are present: largest positive
  reversion, lowest confidence, turnover/notional, or explicit upstream sort
  metadata?

---


## 2026-05-25 — Phase 10 iteration 47: Toxicity context ranking controls

### Implemented

- Continued from `mmsr_phase10_iteration46.zip`.
- Refocused on production report behavior, not offline demo expansion.
- Added deterministic context-ranking controls to the production
  `Cross-Venue Toxicity` page.
- Added `ToxicityContextRanking`, `TOXICITY_CONTEXT_RANKINGS`, and
  `DEFAULT_TOXICITY_CONTEXT_RANKING`.
- Added `ToxicityReversionPageOptions.context_ranking` with supported modes:
  `max_positive_reversion`, `max_absolute_reversion`, `lowest_confidence`, and
  `chronological`.
- Made the default context ranking surface the largest positive reversion first,
  because positive reversion means primary-quote movement in the aggressive
  trade direction and is the most direct toxicity signal.
- Added `MarketReportOptions.toxicity_reversion_context_ranking` and passed it
  into the toxicity page builder.
- Exported the context-ranking constants and type alias from `mmsr.report`.
- Updated README, roadmap, and milestone status to describe context ranking as a
  production report feature.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/toxicity.py`
- `tests/test_toxicity_reversion_report.py`

### Tests added or updated

- Updated `tests/test_toxicity_reversion_report.py`.
- Added coverage for default largest-positive context ranking.
- Added coverage for chronological ranking.
- Added coverage for low-confidence context ranking.
- Added validation coverage for unknown ranking names.
- Added canonical market-report coverage proving
  `MarketReportOptions.toxicity_reversion_context_ranking` is passed through to
  `build_toxicity_reversion_page()`.

### Validation performed

- Ran `python -m compileall -q mmsr/report/toxicity.py mmsr/report/market_report.py tests/test_toxicity_reversion_report.py`:
  passed.
- Ran `python -m pytest tests/test_toxicity_reversion_report.py -q`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion_report.py tests/test_market_report.py tests/test_import.py -q`:
  passed.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 273 tests.
- The environment emitted the unrelated spreadsheet runtime warmup warning before
  Python validation commands, but the commands returned success.

### Current milestone

- Active milestone: Cross-venue toxicity reversion production report features.

### Current milestone progress

- Cross-venue toxicity/reversion production report page: 95% complete.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- Decide whether to exclude `primary_quote_reversion_*_bps` series from the
  generic `Intraday Detail` page when the dedicated production
  `Cross-Venue Toxicity` page is present, to avoid duplicate visuals.
- Live production validation remains blocked by missing kdb+ endpoint and
  credentials, not by report-layer implementation.

### Best next deterministic step

- Add a `MarketReportOptions` control that excludes the reversion metric family
  from the generic `Intraday Detail` page whenever the dedicated
  `Cross-Venue Toxicity` page is present.

### Package phase and iteration

- Phase: 10.
- Iteration: 47.
- Delivery archive name: `mmsr_phase10_iteration47.zip`.

### Open questions

- Should duplicate reversion visuals be suppressed from `Intraday Detail` by
  default, or only through an explicit opt-in option?
- Should production context ranking eventually support an upstream
  `context_sort_order` metadata field from kdb when callers want business-owned
  prioritization?


---

## 2026-05-25 — Phase 10 iteration 48: Suppress duplicate reversion detail visuals

### Implemented

- Continued from `mmsr_phase10_iteration47.zip`.
- Added `MarketReportOptions.include_toxicity_reversion_metrics_in_detail_page`, defaulting to `False`.
- Updated the canonical `build_market_monitor_report()` flow so it first determines whether the dedicated `Cross-Venue Toxicity` page is present, then filters `primary_quote_reversion_*_bps` series out of the generic `Intraday Detail` page by default.
- Kept a deterministic opt-in path for production callers that explicitly want both the dedicated toxicity curves and the generic detail charts/heatmaps.
- Preserved generic Intraday Detail rendering for reversion series when the dedicated toxicity page is disabled or absent, so supplied data remains visible.
- Updated README, roadmap, and milestone status documentation to describe the duplicate-suppression behavior and the opt-in option.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/market_report.py`
- `tests/test_toxicity_reversion_report.py`

### Tests added or updated

- Updated `tests/test_toxicity_reversion_report.py`.
- Added coverage proving the dedicated `Cross-Venue Toxicity` page suppresses duplicate generic Intraday Detail reversion charts by default.
- Added coverage for `include_toxicity_reversion_metrics_in_detail_page=True` to retain both displays.
- Added coverage proving disabled toxicity pages still leave supplied reversion series visible in Intraday Detail.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion_report.py -q`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion_report.py tests/test_market_report.py tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 274 tests.
- Ran `python -m pytest tests/test_docs_governance.py -q` after updating `_docs/journal.md`: passed.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the unrelated spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Cross-venue toxicity reversion production report features.

### Current milestone progress

- Cross-venue toxicity/reversion production report page: 100% complete under the documented assumption that the kdb reversion output schema is correct.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Live production validation remains blocked by missing kdb+ endpoint and credentials, not by report-layer implementation.
- Optional future production polish may add an upstream `context_sort_order` metadata hook if callers need business-owned toxicity context ordering beyond the deterministic ranking modes already implemented.

### Best next deterministic step

- Keep live-kdb work deferred until schemas and credentials are available; otherwise, add the upstream `context_sort_order` metadata hook only if production callers confirm that the existing context-ranking modes are insufficient.

### Package phase and iteration

- Phase: 10.
- Iteration: 48.
- Delivery archive name: `mmsr_phase10_iteration48.zip`.

### Open questions

- Should production context ranking eventually support an upstream `context_sort_order` metadata field from kdb when callers want business-owned prioritization?

---

## 2026-05-25 — Phase 10 iteration 49: Upstream toxicity context sort-order hook

### Implemented

- Continued from `mmsr_phase10_iteration48.zip`.
- Added optional `context_sort_order` metadata support to toxicity reversion curve points.
- Added `context_sort_order` as a supported `ToxicityContextRanking` mode.
- The new ranking mode sorts toxicity contexts by the smallest supplied upstream numeric `context_sort_order`, then uses positive reversion, absolute reversion, and chronological keys as deterministic tie-breakers.
- Surfaced supplied context sort order in chart point metadata for auditability.
- Preserved the default largest-positive-reversion ranking so existing production reports do not change unless callers opt in.
- Verified that kdb-runner normalization preserves optional `context_sort_order` output columns as observation metadata without making the field mandatory in the q output schema.
- Updated README, roadmap, and milestone status documentation to describe the optional upstream ordering hook.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/toxicity.py`
- `mmsr/visuals/toxicity.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_toxicity_reversion.py`
- `tests/test_toxicity_reversion_report.py`

### Tests added or updated

- Updated `tests/test_toxicity_reversion.py` to preserve `context_sort_order` metadata and reject non-integer values.
- Updated `tests/test_toxicity_reversion_report.py` to cover direct toxicity-page ranking by upstream `context_sort_order` and canonical market-report option pass-through.
- Updated `tests/test_kdb_metric_runner.py` to prove optional `context_sort_order` kdb output columns are preserved as normalized observation metadata.

### Validation performed

- Ran `python -m compileall -q mmsr/report/toxicity.py mmsr/visuals/toxicity.py tests/test_toxicity_reversion.py tests/test_toxicity_reversion_report.py`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion.py tests/test_toxicity_reversion_report.py -q`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion.py tests/test_toxicity_reversion_report.py tests/test_kdb_metric_runner.py -q`: passed.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 278 tests.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Cross-venue toxicity reversion production report features.

### Current milestone progress

- Cross-venue toxicity/reversion production report page and controls: 100% complete under the documented assumption that the kdb reversion output schema is correct.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Live production validation remains blocked by missing kdb+ endpoint and credentials, not by report-layer implementation.
- No further deterministic toxicity report-layer backlog remains under the currently documented assumptions.

### Best next deterministic step

- Run the environment-gated live kdb+ smoke validation once production-like schemas, endpoint, and credentials are available.

### Package phase and iteration

- Phase: 10.
- Iteration: 49.
- Delivery archive name: `mmsr_phase10_iteration49.zip`.

### Open questions

- None for this implementation step.

---

## 2026-05-25 — Phase 10 iteration 50: Symbol detail index navigation

### Implemented

- Continued from `mmsr_phase10_iteration49.zip`.
- Accepted user direction to prioritize an actual production-report feature over
  another live-smoke validation step.
- Added stable optional `ReportPage.anchor_id` support and rendered anchors in
  the packaged HTML template.
- Added `symbol_detail_anchor_id()` for deterministic per-symbol detail anchors.
- Added `SymbolDetailIndexOptions` and `build_symbol_detail_index_block()` to
  build a compact trusted-HTML navigation table from already-computed
  symbol-scoped comparison facts and emitted symbol detail pages.
- Updated the canonical `build_market_monitor_report()` flow so the
  `Symbol Anomalies` page includes a `Symbol Detail Index` by default whenever
  per-symbol detail pages are emitted.
- Added `MarketReportOptions.include_symbol_detail_index`,
  `symbol_detail_index_title`, and `symbol_detail_index_help_text` so production
  callers can keep detail pages while omitting or relabeling the index.
- Added basic table styling for trusted HTML blocks so the index renders
  consistently with other report tables.
- Updated README, roadmap, and milestone status documentation to describe the
  compact symbol-detail navigation behavior.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/report/__init__.py`
- `mmsr/report/components.py`
- `mmsr/report/market_report.py`
- `mmsr/report/symbols.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Updated `tests/test_symbol_anomaly_pages.py`.
- Added coverage for stable symbol-detail page anchors.
- Added coverage for direct `build_symbol_detail_index_block()` output and
  filtering to only emitted detail pages.
- Added coverage for disabling the detail index via index options.
- Added canonical market-report coverage proving the `Symbol Anomalies` page
  receives the index when detail pages are emitted.
- Added rendered HTML coverage proving the index links target detail-page
  anchors.
- Added canonical market-report coverage for
  `MarketReportOptions.include_symbol_detail_index=False`.

### Validation performed

- Ran `python -m compileall -q mmsr/report/components.py mmsr/report/symbols.py mmsr/report/market_report.py`:
  passed.
- Ran `python -m pytest tests/test_symbol_anomaly_pages.py -q`: passed.
- Ran `python -m pytest tests/test_market_report.py tests/test_html_rendering.py tests/test_symbol_anomaly_pages.py -q`:
  passed.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 283 tests.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Symbol-level anomaly and detail production report pages.

### Current milestone progress

- Symbol anomaly summary, detail pages, and compact detail-index navigation: 100%
  complete for the current report-layer phase.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- No deterministic symbol report-layer backlog remains under the current
  assumptions.
- Live production validation remains blocked by missing kdb+ endpoint and
  credentials, not by the report-layer implementation.
- Future production feedback may refine the index columns, add a separate
  detail-page table of contents, or introduce richer alert-delivery formatting.

### Best next deterministic step

- Keep live-kdb execution deferred until schemas and credentials are available.
  For local feature work, choose the next narrow production-report refinement
  backed by user feedback, such as drilldown summary navigation or alert delivery
  formatting.

### Package phase and iteration

- Phase: 10.
- Iteration: 50.
- Delivery archive name: `mmsr_phase10_iteration50.zip`.

### Open questions

- None for this implementation step.


---

## 2026-05-25 — Phase 10 iteration 51: kdb query-plan and schema-boundary hardening

### Implemented

- Continued from `mmsr_phase10_iteration50.zip`.
- Accepted user direction to harden the expected kdb table schema and isolate
  query rendering so production q can be manually edited toward a stable Python
  result contract.
- Added `mmsr.kdb.query_plan` with `KdbMetricQueryPlanner`,
  `RenderedMetricQuery`, and the public `MetricRunRequest` boundary.
- `KdbMetricQueryPlanner.render()` now returns rendered q text, requested and
  normalized grouping columns, source input-table contracts, required output
  columns, supported optional output columns, and a reusable output contract
  before any client IO occurs.
- Refactored `KdbMetricRunner` so `run()` plans first, executes the planned q,
  validates the planned output schema, then normalizes to `MetricTimeSeries`.
- Preserved `KdbMetricRunner.render_query()` for compatibility while adding
  `KdbMetricRunner.plan_query()` for callers that need schema details before
  execution.
- Added activity and liquidity source-table contracts, including extra required
  source columns for configured `group_by` fields and optional symbol-bounded
  starter queries.
- Centralized output schema contract dispatch with
  `output_schema_contract_for_template()` and
  `validate_output_schema_for_template()`.
- Documented supported optional kdb output columns through
  `QTemplateOutputSchemaContract.optional_columns`; reversion now documents
  optional `context_sort_order` without making it mandatory.
- Updated README, roadmap, milestone status, q-template comments, and the
  production-readiness checklist to describe the query-plan/schema-boundary
  workflow for manual q edits.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `docs/production_readiness.md`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/q_templates/activity.q`
- `mmsr/kdb/q_templates/liquidity.q`
- `mmsr/kdb/q_templates/toxicity_reversion.q`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added `tests/test_kdb_query_plan.py` covering plan rendering for activity,
  liquidity, and reversion metrics; input contracts; required/optional output
  columns; plan-level result validation; runner metadata; public grouping
  helpers; and pre-execution identifier validation.
- Updated `tests/test_kdb_schema_contracts.py` to cover activity/liquidity input
  contracts, optional reversion output columns, and centralized template output
  schema dispatch.
- Existing kdb metric-runner tests now exercise the refactored plan-first runner
  path through the same public `MetricRunRequest` compatibility import.

### Validation performed

- Ran `python -m pytest tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_kdb_schema_contracts.py -q`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m pytest --collect-only -q`: passed and collected 290 tests.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: kdb query/schema boundary hardening for production q edits.

### Current milestone progress

- Query rendering is isolated from execution and the expected Python-facing kdb
  result schema is explicit for activity, liquidity, and reversion templates:
  100% complete for this hardening slice.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- No further deterministic work remains for this schema-boundary hardening slice.
- Live schema validation against production tables remains blocked by missing
  kdb+ endpoint, credentials, and confirmed production schemas.
- Future production feedback may add stricter type contracts or source-table
  metadata probes, but the column-shape contract is now explicit and reusable.

### Best next deterministic step

- Add the first quote-quality metric family on top of the hardened query-plan
  boundary, such as locked/crossed quote rate, stale quote rate, or
  spread-time-at-wide, using explicit schema contracts and offline tests.

### Package phase and iteration

- Phase: 10.
- Iteration: 51.
- Delivery archive name: `mmsr_phase10_iteration51.zip`.

### Open questions

- Should future production validation include q type checks in addition to column
  presence checks once live schema metadata is available?
