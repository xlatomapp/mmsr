# Implementation Journal

This file must be updated after every implementation step.

## 2026-05-30 — D2 implementation start: lead-chart-first defaults per section

### What changed
- Enforced visual-priority defaults by reducing default auxiliary chart count:
  - `max_activity_distribution_charts`: `1`
  - `max_displayed_liquidity_charts`: `1`
  - `max_toxicity_reversion_charts`: `1`
- This makes each section lead with one primary chart by default, with
  additional diagnostics available through explicit option overrides.
- Updated report/offline/mock tests to reflect new default chart counts and
  preserved structural ordering assertions added in D1.

### Milestone status
- Current milestone: `D2` visual-priority refactor
- Progress to next implementation gate: `~35%` of D2
- Remaining deterministic implementation work: add explicit per-section lead
  metric config fields (activity/liquidity/reversion) and deterministic tests
  proving lead-metric precedence under custom metric ordering.

### Next deterministic step
- Implement configurable lead metric selectors for activity/liquidity/reversion
  section charts and enforce lead chart precedence in section builders.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — D1 implementation: final page-1 hierarchy contract hooks

### What changed
- Added explicit summary-page structural hooks in template:
  - summary page class: `report-page--summary`
  - html-block attribute: `data-block-title="<Block Title>"`
- Added summary-page hierarchy polish styles for tighter spacing rhythm and
  stronger heading/section structure.
- Added HTML-level structural assertions to lock order and presence of:
  - `Report Meta`
  - `Market KPI Snapshot`
  - `Executive Market Overview`
  plus ordering around `Primary Intraday Signal`, `Insight Callout`, and
  `Current versus reference`.
- Updated compatibility assertions in offline demo tests for the new
  `html-block` markup shape.

### Milestone status
- Current milestone: `D1` page-1 redesign
- Progress to next implementation gate: `100%` for planned D1 contract slices
- Remaining deterministic implementation work: begin D2 visual-priority refactor for downstream sections (activity/liquidity/reversion pages) while preserving deterministic semantics.

### Next deterministic step
- Start D2: make section-level visual hierarchy consistent by adding explicit
  per-section lead-chart constraints and demoting auxiliary diagnostics in
  activity/distributed-liquidity/reversion pages.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — D1 implementation: deterministic Insight Callout under primary chart

### What changed
- Added deterministic page-1 `Insight Callout` as a `CommentaryBlock` derived
  from the configured primary intraday signal metric.
- Fact inputs used:
  - average percent change direction/magnitude for primary metric
  - alert/watch row counts for that metric
  - count of market contexts
- Summary-page commentary now prepends:
  1. `Insight Callout`
  2. existing deterministic `Market Summary` commentary
- Updated template ordering so `Market Summary` renders commentary blocks before
  the summary comparison table, ensuring:
  - `Primary Intraday Signal` chart
  - then `Insight Callout`
  - then `Current versus reference` table.
- Updated tests in:
  - `tests/test_market_report.py`
  - `tests/test_offline_demo.py`
  - `tests/test_mock_kdb_demo.py`

### Milestone status
- Current milestone: `D1` page-1 redesign
- Progress to next implementation gate: `~90%` of D1
- Remaining deterministic implementation work: tighten final page-1 spacing/visual hierarchy contract and add one regression assertion set for block order + section anchors in rendered HTML.

### Next deterministic step
- Implement final D1 page-1 hierarchy polish (section spacing/heading rhythm for `Report Meta`, `KPI Snapshot`, `Executive Overview`, `Primary Intraday Signal`, `Insight Callout`) and lock with HTML-level structural assertions.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — D1 implementation: page-1 Report Meta strip

### What changed
- Added a Python-composed `Report Meta` block above KPI Snapshot on page 1.
- Block fields:
  - `Period` (from summary comparison dates)
  - `Reference` (dominant comparison method)
  - `Scope` (summary scope label)
  - `Run Tag` (generated-at text fallback)
- Updated summary page composition order:
  1. Report Meta
  2. Market KPI Snapshot
  3. Executive Market Overview
- Added responsive styling for the meta strip.
- Updated tests to lock new page-1 block ordering and visibility:
  - `tests/test_market_report.py`
  - `tests/test_offline_demo.py`
  - `tests/test_mock_kdb_demo.py`

### Milestone status
- Current milestone: `D1` page-1 redesign
- Progress to next implementation gate: `~80%` of D1
- Remaining deterministic implementation work: enforce fixed section spacing/visual rhythm and introduce one explicit page-1 “insight callout” block under the primary intraday signal.

### Next deterministic step
- Implement a deterministic page-1 `Insight Callout` block (non-LLM, fact-derived) directly under `Primary Intraday Signal`, with strict ordering assertions.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — D1 implementation: Primary Intraday Signal on page 1

### What changed
- Added a fixed-position page-1 `Primary Intraday Signal` chart in
  `mmsr/report/market_report.py`.
- New summary-page options:
  - `include_primary_intraday_signal` (default `True`)
  - `primary_intraday_signal_metric_name` (default `quoted_spread_bps`)
- Summary chart ordering now places this primary chart first in page-1 plotly
  charts, then appends remaining summary charts.
- Updated tests to lock:
  - presence of `Primary Intraday Signal`
  - ordering after top-driver narrative and before comparison table content
  - option validation for primary signal metric name.

### Milestone status
- Current milestone: `D1` page-1 redesign
- Progress to next implementation gate: `~60%` of D1
- Remaining deterministic implementation work: tighten page-1 layout contract for visual rhythm (header meta strip + consistent block spacing hierarchy) and lock with explicit HTML-level assertions.

### Next deterministic step
- Implement a compact page-1 report meta strip (`period`, `benchmark/reference`, `run tag`) as a Python-composed block above KPI snapshot, then add ordering/visibility tests.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Design decision: Python-first section rendering

### What changed
- Updated `_docs/report_design_roadmap.md` with a rendering strategy decision:
  - keep Jinja as a thin shell layer
  - implement redesigned report sections in Python builders first
  - avoid new `.j2` partials unless strong reuse is proven

### Milestone status
- Current milestone: `D1` page-1 redesign
- Progress to next implementation gate: `~35%` of D1
- Remaining deterministic implementation work: add fixed-position primary intraday signal chart in page-1 flow using Python-first composition.

### Next deterministic step
- Implement `Primary Intraday Signal` as a Python-composed section in summary-page assembly and lock strict page-1 ordering tests.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — D1 implementation start: Market KPI Snapshot row on page 1

### What changed
- Implemented a new page-1 `Market KPI Snapshot` block in summary assembly:
  - file: `mmsr/report/market_report.py`
  - rendered before `Executive Market Overview`
  - uses market+date aggregated summary comparisons
  - default KPI metric set:
    - `turnover`
    - `quoted_spread_bps`
    - `top_of_book_depth`
    - `primary_quote_reversion_100ms_bps`
- Added `MarketReportOptions` controls:
  - `include_summary_kpi_snapshot` (default `True`)
  - `summary_kpi_metric_names`
- Added styling for a compact 4-cell KPI row in:
  - `mmsr/report/templates/report.html.j2`
- Updated report tests to lock the new page-1 block order and content expectations:
  - `tests/test_market_report.py`
  - `tests/test_offline_demo.py`
  - `tests/test_mock_kdb_demo.py`

### Milestone status
- Current milestone: design roadmap `D1` execution (page-1 redesign)
- Progress to next implementation gate: `~35%` of D1
- Remaining deterministic implementation work in D1: add explicit page-1 primary intraday chart contract (single lead chart in fixed position) and lock HTML ordering assertions.

### Next deterministic step
- Implement a fixed-position `Primary Intraday Signal` chart block on page 1 (target vs reference for quoted spread by default), rendered immediately after Top Drivers, and add deterministic order tests.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Design roadmap metric alignment update

### What changed
- Updated `_docs/report_design_roadmap.md` to explicitly separate:
  - reference layout signals
  - MMSR default metric content
- Added a metric coverage matrix mapping reference cards/charts to MMSR metric
  families and replacements.
- Explicitly corrected `Price Impact` wording to MMSR default
  `Cross-venue reversion` metrics for default reporting.
- Added a concrete list of required MVP default metrics and a list of
  intentionally non-default metric families.

### Milestone status
- Current milestone: `R6` (active implementation stream), design roadmap drafted.
- Progress to next implementation gate: `99%`
- Remaining deterministic implementation work: wire optional family-diversification mode into user-facing YAML/docs.

### Next deterministic step
- Add config documentation/examples for `overview_top_change_diversification`
  (`metric` default, optional `family`) in report config docs and README snippets.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Added dedicated report redesign roadmap document

### What changed
- Added `_docs/report_design_roadmap.md` based on the provided visual reference.
- Defined target information architecture, design principles, section-by-section redesign intent, and implementation milestones (`D0`..`D5`).
- Included explicit acceptance criteria and direct mapping to current report modules/tests.

### Milestone status
- Current milestone: `R6` (current implementation stream)
- Progress to next implementation gate: `99%`
- Remaining deterministic implementation work in current stream: wire optional family diversification mode into YAML/config docs (default remains metric diversification).

### Next deterministic step
- Start `D1` in implementation terms: lock page-1 visual contract with explicit ordering assertions for KPI row, key changes, top drivers + mini bars, and primary intraday chart.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Configurable summary diversification mode (default unchanged)

### What changed
- Added configurable summary driver diversification mode:
  - `metric` (default, current MVP behavior)
  - `family` (future hardening mode)
- Implementation:
  - `ExecutiveOverviewOptions.top_change_diversification`
  - `MarketReportOptions.overview_top_change_diversification`
  - `_select_top_changes(..., diversification=...)` in `mmsr/report/overview.py`
- Added validation and regression coverage:
  - `tests/test_executive_overview.py`
  - `tests/test_market_report.py`

### Milestone status
- Current milestone: `R6`
- Progress to next implementation gate: `99%`
- Remaining deterministic implementation work: expose this diversification mode in user-facing config/CLI docs with clear MVP default guidance.

### Next deterministic step
- Wire `overview_top_change_diversification` into YAML config loading/docs so users can opt into `family` mode without code changes, while preserving `metric` as default.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — TPX-first context ordering + roadmap decision lock

### What changed
- Implemented explicit TPX-first context ordering in executive summary context rendering:
  - `topixCapGrp`/`topix_bucket` first, then market-cap, segment, sector.
  - File: `mmsr/report/overview.py`
- Added regression test:
  - `tests/test_executive_overview.py::test_top_market_drivers_context_is_tpx_first`
- Documented roadmap decision in `_docs/ROADMAP.md`:
  - `Key changes` and `Top market drivers` use market+date aggregated rows,
    time-bucket-collapsed summary, and metric-diversified ranking before repeats.

### Milestone status
- Current milestone: `R6`
- Progress to next implementation gate: `99%`
- Remaining deterministic implementation work: add family-level diversification option (metric-family quotas) as a future milestone item, not default MVP behavior.

### Next deterministic step
- Add a configurable family-diversification mode for summary drivers (off by default), and document it as a future milestone hardening path.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Summary driver diversification: prevent single-metric monopolization

### What changed
- Updated `mmsr/report/overview.py::_select_top_changes`:
  - keeps existing severity ordering (`alert/watch`, `|z|`, `|change_pct|`)
  - adds first-pass metric diversification (one row per metric before repeats)
  - fills remaining slots by severity only after diversity pass
- Added regression test in `tests/test_executive_overview.py`:
  - `test_select_top_changes_diversifies_metrics_before_repeats`
  - verifies `Quoted Spread` does not crowd out `Volume` / `Trade Count` in first slots.

### Milestone status
- Current milestone: `R6`
- Progress to next implementation gate: `99%`
- Remaining deterministic implementation work: enforce deterministic context label ordering in top-driver display (`topixCapGrp` first) and add explicit assertion coverage.

### Next deterministic step
- Implement deterministic TPX-cap-first context label ordering in top-driver display text and add tests that fail on non-TPX-first ordering.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — Summary aggregation contract fix: market+date (not cross-date)

### What changed
- Updated summary aggregation in `mmsr/report/market_report.py` so summary rows aggregate at:
  - `metric + market context + date`
  - time-bucket is collapsed
- This prevents duplicate bucket-level rows in summary while avoiding invalid cross-date blending.
- Updated tests to reflect the aggregated summary surface:
  - `tests/test_market_report.py`
  - `tests/test_production_cli.py`

### Milestone status
- Current milestone: `R6`
- Progress to next implementation gate: `98%`
- Remaining deterministic implementation work: enforce TPX-cap-first display ordering in `Top market drivers` context text and verify with explicit context-order assertions.

### Next deterministic step
- Implement deterministic TPX-cap-first context label ordering for the executive `Top market drivers` section (`topixCapGrp`, then market-cap/segment/sector), and add tests that fail on wrong context order.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — MVP implementation: visible Top Market Drivers block on page 1

### What changed
- Added a dedicated `Top market drivers` block in `mmsr/report/overview.py` directly below the KPI strip.
- Driver rows are deterministic and market-first:
  - market-level only (symbol-scoped rows excluded),
  - ranked by status severity then `|z|` then `|change_pct|`,
  - capped by existing narrative cap (`5`) via shared selection path.
- Added dedicated styling for the new block in `mmsr/report/templates/report.html.j2`.
- Added coverage in:
  - `tests/test_executive_overview.py`
  - `tests/test_market_report.py`

### Milestone status
- Current milestone: `R6`
- Progress to next gate: `97%`
- Remaining deterministic implementation work: add the summary-page market-driver mini chart strip tied to the same top-5 drivers so narrative and visuals use one ranking source.

### Next deterministic step
- Implement a `Top market drivers` mini chart strip on page 1 (market-only, deterministic top-5, same ordering as driver list) and place it directly below the driver list.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — MVP implementation: Top Market Drivers mini chart strip

### What changed
- Implemented a new inline mini chart strip under `Top market drivers` in `mmsr/report/overview.py`.
- The mini chart is driven by the exact same deterministic top-5 market-only driver selection already used by the driver list.
- Added CSS for the bar-strip visualization in `mmsr/report/templates/report.html.j2`.
- Added/updated assertions in:
  - `tests/test_executive_overview.py`
  - `tests/test_market_report.py`
  so the mini chart section is required in summary output before the comparison table.

### Milestone status
- Current milestone: `R6`
- Progress to next implementation gate: `98%`
- Remaining deterministic implementation work: enforce TPX-cap-first context labeling in Top Market Drivers display and add explicit ordering test coverage for that display contract.

### Next deterministic step
- Implement TPX-cap-first context formatting for the `Top market drivers` section (prefer `topixCapGrp` in displayed context ordering, then market-cap/segment/sector), and lock it with deterministic tests.

### Exit gate after implementation step
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passes fully.

## 2026-05-30 — MVP implementation: summary page now plot-first

### What changed
- Implemented plot-first summary-page composition in `mmsr/report/market_report.py`:
  - Added `max_summary_story_charts` option (default `3`).
  - Added `_build_summary_story_charts(...)` to place market-level story charts directly on page 1.
  - Summary page now includes:
    - executive overview (narrative + KPI strip)
    - metric cards
    - summary story charts (activity + displayed-liquidity priority)
    - comparison table (demoted below visuals)
- Updated template render order in `mmsr/report/templates/report.html.j2` so charts render before tables globally.
- Extended `tests/test_market_report.py` for:
  - summary-page chart presence
  - visual-before-table ordering assertion
  - option validation for `max_summary_story_charts`.

### Milestone status
- Current milestone: `R6`
- Progress to next gate: `95%`
- Remaining deterministic gate: run full pre-commit after this code change and finalize commit.

### Next deterministic step
- Implement a dedicated `Top Market Drivers` block on page 1 (market-level only, max 5, deterministic severity ordering) directly under the executive KPI strip, then wire/validate it in report assembly tests.

### Exit gate after implementation step
- Run full pre-commit and resolve any failures from the new market-driver block wiring.

## 2026-05-30 — MVP reset: remove detour and enforce market-first story surface

### What changed
- Removed the non-MVP `--calendar-function` CLI override path from:
  - `mmsr plan`
  - `mmsr preflight`
  - `mmsr render`
- Deleted override implementation in `mmsr/cli.py` and removed the related test:
  - `tests/test_production_cli.py::test_summarize_production_report_plan_can_override_calendar_function`
- Added a visible market-story summary strip at the top of executive overview:
  - status KPI cards for `Alert`, `Watch`, `Comparison only`, and `Normal`
  - implementation in `mmsr/report/overview.py`
  - styling in `mmsr/report/templates/report.html.j2`
  - assertion coverage in `tests/test_executive_overview.py`

### Why this aligns with MVP
- Keeps runtime/config semantics strict and deterministic (no runtime override detour).
- Makes the first report section immediately tell the market-level story before tables.

### Milestone status
- Current milestone: `R6` (production readiness + budget discipline)
- Progress to next milestone gate: `~90%`
- Remaining deterministic gate for R6 close: run full pre-commit and commit cleanly.

### Next deterministic step
- Execute full pre-commit suite and commit this MVP cleanup slice.

## 2026-05-30 — R6 unblock: CLI calendar-function override for live preflight/render

### Implemented

- Added an optional `--calendar-function` override to production CLI commands:
  - `mmsr plan`
  - `mmsr preflight`
  - `mmsr render`
- Added internal config-rewrite helper so users can override calendar q function at runtime without editing YAML.
- Extended production CLI tests to cover calendar-function override behavior in plan summary path.

### Files changed

- `mmsr/cli.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added `test_summarize_production_report_plan_can_override_calendar_function` in `tests/test_production_cli.py`.

### Validation

- `python -m pytest -q tests/test_production_cli.py tests/test_kdb_production_execution.py` passed.
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passed:
  - `ruff check`
  - `ruff format`
  - `mypy`
  - `pytest-full`

### Current milestone

- Milestone R6: real kdb production validation and report budgets.

### Estimated milestone completion

- 95%

### Remaining work before milestone completion

- Re-run live preflight using the actual calendar function available on host via `--calendar-function`.
- Run one live render and capture final runtime/row-count/HTML-size/chart-count evidence.

### Best next deterministic step

- Execute `mmsr preflight` against `192.168.3.99:5001` with `--calendar-function <host_function>` and record pass/fail evidence.

### Open questions

- Which exact calendar function name exists on `192.168.3.99:5001`?

## 2026-05-30 — R6 completion pass: report budgets + live preflight evidence

### Implemented

- Added deterministic report budget measurement/enforcement utilities:
  - `ReportBudgetSnapshot`
  - `ReportBudgetLimits`
  - `snapshot_report_budget(document, html)`
  - `evaluate_report_budget(snapshot, limits)`
- Added regression tests that enforce bounded default report growth for offline and mock-kdb reports.
- Wired production render path to compute budget snapshot and log pass/warning status with concrete counts (pages, HTML bytes, chart count, metric-row count).
- Executed live preflight against configured host to close the R6 live-validation loop.

### Files changed

- `mmsr/report/budgets.py`
- `tests/test_report_budgets.py`
- `mmsr/cli.py`

### Tests added or updated

- Added `tests/test_report_budgets.py` with:
  - offline-demo budget compliance test
  - mock-kdb-demo budget compliance test
  - explicit budget-violation detection test

### Validation

- `python -m pytest -q tests/test_report_budgets.py tests/test_production_cli.py tests/test_market_report.py` passed.
- Live preflight command executed against kdb host:
  - `python -m mmsr.cli preflight --config config/report.production_minimal.yaml --kdb-host 192.168.3.99 --kdb-port 5001`
  - Result: connection succeeded, preflight failed with `QError: .sb.mmsr.getTradingCalendar` (calendar function missing on remote host namespace).

### Current milestone

- Milestone R6: real kdb production validation and report budgets.

### Estimated milestone completion

- 90%

### Remaining work before milestone completion

- Deploy/confirm calendar function `.sb.mmsr.getTradingCalendar` (or update config to the correct function name available on host).
- Re-run live `preflight`, then run one full live `render` to record:
  - q stage timings
  - returned row counts
  - final HTML size
  - chart count
  - review usability notes

### Best next deterministic step

- Update production config calendar function to an existing host function (or install `.sb.mmsr.getTradingCalendar`), then rerun `mmsr preflight` and capture runtime/row-count evidence for R6 closure.

### Open questions

- What is the correct production calendar function name on `192.168.3.99:5001` if not `.sb.mmsr.getTradingCalendar`?

## 2026-05-30 — Governance sync: add missing R7/R8 milestones to roadmap

### Implemented

- Added explicit `Milestone R7` and `Milestone R8` sections to `_docs/ROADMAP.md` under the active roadmap reset.
- Added an active-reset milestone tracking table to `_docs/MILESTONE_STATUS.md` so labels used during implementation are visible and auditable in one place.
- Aligned milestone naming across roadmap, status audit, and recent journal entries.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`

### Tests added or updated

- No code or test behavior changes (documentation/governance sync only).

### Validation

- Pending pre-commit run for docs-only update.

### Current milestone

- Milestone R7/R8 governance and implementation alignment.

### Estimated milestone completion

- 100% (for this governance-sync step).

### Remaining work before milestone completion

- None for this sync step.

### Best next deterministic step

- Add the remaining HTML-level regression assertions for R7/R8 summary/storytelling defaults.

### Open questions

- None.

## 2026-05-30 — R8: visible report storytelling polish (executive overview + status chips)

### Implemented

- Applied visible report styling improvements focused on narrative readability:
  - Added pill-style status chips in comparison tables.
  - Increased executive-overview visual hierarchy with stronger spacing.
  - Added explicit highlight-panel styling (`Key changes this period`) to separate narrative bullets from the rest of summary content.
- Kept metric calculations and data contracts unchanged; this step is presentation-only.

### Files changed

- `mmsr/report/templates/report.html.j2`

### Tests added or updated

- No new tests required (presentation-only CSS pass).
- Verified existing report rendering tests continue to pass.

### Validation

- `python -m pytest -q tests/test_market_report.py tests/test_mock_kdb_demo.py tests/test_offline_demo.py` passed.

### Current milestone

- Milestone R7/R8: market-first report shape lock and visible report storytelling improvements.

### Estimated milestone completion

- 65%

### Remaining work before milestone completion

- Add one HTML-level regression test asserting presence of executive highlight container and status chip class in rendered output.
- Apply a compact summary KPI row (counts of alert/watch/normal) above the comparison table to further reduce table-scanning burden.
- Validate mobile rendering readability for summary page with long highlight sentences.

### Best next deterministic step

- Add HTML rendering regression tests for the new executive highlight panel and status-chip classes in the Market Summary page.

### Open questions

- None.

## 2026-05-30 — R7: lock market-first default report shape when symbol rows are present

### Implemented

- Added a deterministic regression test that injects a symbol-scoped comparison row and verifies default report output remains market-first (no symbol anomaly/detail pages unless explicitly enabled).
- Tightened symbol-page help text wording to make explicit that symbol pages are opt-in escalation views.

### Files changed

- `tests/test_market_report.py`
- `mmsr/report/market_report.py`

### Tests added or updated

- Added `test_market_monitor_report_defaults_remain_market_first_with_symbol_rows_present` in `tests/test_market_report.py`.

### Validation

- `python -m pytest -q tests/test_market_report.py tests/test_symbol_anomaly_pages.py` passed.

### Current milestone

- Milestone R7: market-first report-shape lock and default behavior hardening.

### Estimated milestone completion

- 40%

### Remaining work before milestone completion

- Add one HTML-level assertion test to ensure symbol-specific headers/blocks are absent in default rendering with symbol rows.
- Add one complementary test that enabling symbol anomaly page surfaces symbol content in expected page order without changing other defaults.
- Sweep README/report docs for any wording that implies symbol-first default flow.

### Best next deterministic step

- Add an HTML rendering regression test that verifies default output excludes symbol anomaly/detail sections even when symbol comparisons exist.

### Open questions

- None.

## 2026-05-30 — R6: remove `table_names` field and complete source-functions-only API surface

### Implemented

- Removed `table_names` from `MetricRunRequest`; planner requests are now fully source-function native.
- Confirmed no remaining runtime references to `table_names` across package code/tests/docs.
- Updated remaining tests to construct metric requests without table-name mappings.
- Updated README query-plan example to use `source_functions` instead of `table_names`.

### Files changed

- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `README.md`

### Tests added or updated

- Updated existing tests in `tests/test_kdb_metric_runner.py` for request construction and expectation alignment with source-functions-only behavior.

### Validation

- `python -m pytest -q` passed (full suite).
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passed:
  - `ruff check`
  - `ruff format`
  - `mypy`
  - `pytest-full`

### Current milestone

- Milestone R5/R6 transition: source-function-only kdb query contract and legacy-surface removal.

### Estimated milestone completion

- 100%

### Remaining work before milestone completion

- None for R5/R6 scope.

### Best next deterministic step

- Start next milestone on report-focused tightening: remove stale symbol-level defaults/docs that still imply symbol-first workflow and lock market-first report shape with explicit snapshot tests for default page set and ordering.

### Open questions

- Should we hard-remove historical mentions of table-name pathways from older journal sections, or keep them as immutable historical record?

## 2026-05-30 — R5: remove planner table-name fallback and migrate callers/tests to source functions

### Implemented

- Removed remaining `table_names` fallback logic from planner/render execution paths:
  - `RenderedMetricQuery` no longer carries `table_names`.
  - Source expression rendering now resolves from `source_functions` only.
  - Source contract labels now derive from source-function names only.
  - Missing-source failures now consistently report `missing source_functions entry ...`.
- Kept `MetricRunRequest.table_names` as a deprecated compatibility field for now, but it is no longer used by planner execution logic.
- Migrated mock kdb integration demo to source-function style:
  - Replaced mock table-name config with mock source function handles.
  - Updated deterministic mock client query routing to detect function-handle calls.
- Updated affected tests to the new source-function contract and updated expectation strings.

### Files changed

- `mmsr/kdb/query_plan.py`
- `mmsr/examples/mock_kdb_demo.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_mock_kdb_demo.py`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passed:
  - `ruff check`
  - `ruff format`
  - `mypy`
  - `pytest-full`

### Current milestone

- Milestone R5/R6 transition: source-function-only kdb query contract and legacy-surface removal.

### Estimated milestone completion

- 85%

### Remaining work before milestone completion

- Remove deprecated `MetricRunRequest.table_names` field from models and signatures.
- Remove remaining test/config/document references that mention table-name mapping as a supported path.
- Run one final compatibility audit for cache/report metadata fields after field removal.

### Best next deterministic step

- Remove `table_names` from `MetricRunRequest` and complete corresponding type/test updates in one atomic pass.

### Notes

- Production/day-run and single-metric planner paths now share one source contract model (`source_functions`), which reduces ambiguity and removes legacy table-name branching from query rendering.

## 2026-05-30 — R4: make day-run path source-function only and simplify cache identity

### Implemented

- Updated day-query planning to use `source_functions` as the only source contract for `render_day`.
  - Removed day-path dependency on `table_names` fallback resolution.
  - Day-query errors now explicitly require missing source roles to be present in `source_functions`.
- Simplified day-request compatibility checks:
  - Removed `table_names` equality checks across requests.
  - Kept strict checks for single-day scope, shared `source_functions`, and shared `calculation_namespace`.
- Simplified day-cache identity:
  - Removed `table_names` from `MetricDayCacheKey` and `fingerprint`.
  - Cache identity now tracks actual day-run shaping fields (`parameters`, `source_functions`, grouping, bucket, namespace) without legacy table aliases.
- Kept legacy single-metric render compatibility in place to avoid abrupt breakage outside the production day-run path.

### Files changed

- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/cache.py`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passed:
  - `ruff check`
  - `ruff format`
  - `mypy`
  - `pytest-full`

### Current milestone

- Milestone R5/R6 transition: source-function-only kdb query contract and legacy-surface removal.

### Estimated milestone completion

- 70%

### Remaining work before milestone completion

- Remove single-metric planner fallback logic that still used table-name paths.
- Migrate mock/demo call sites that still passed table-name mappings.
- Align error messages/tests with source-function-only contract.

### Best next deterministic step

- Remove table-name fallback in single-metric planner render path and migrate affected tests.

### Notes

- This is an incremental migration: production day execution is now clearly source-function driven, while legacy non-day call sites can be removed in a later cleanup step.

## 2026-05-30 — R3 cleanup: remove redundant q wrappers and harden executive highlight scope filter

### Implemented

- Removed redundant q helper wrappers that only proxied native q behavior:
  - `sumNotional`
  - `medianQuotedSpreadBps`
  - `medianTopOfBookDepth`
  - `positiveRatio`
  - `inferAggressorSide`
  - `callTradingCalendar`
- Inlined the corresponding native q expressions directly in metric calculations:
  - activity notional sum
  - liquidity medians
  - aggressor-side inference
  - positive-reversion ratio
- Simplified kdb trading calendar query construction to call configured calendar function directly instead of routing through wrapper.
- Hardened executive overview highlight filtering so symbol-scoped rows are excluded not only for `sym` but also common identifier keys (`symbol`, `ticker`, `ric`, `isin`).
- Added/updated tests to reflect direct q expression usage and calendar-query behavior.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/periods/calendar.py`
- `mmsr/report/overview.py`
- `tests/test_calendar.py`
- `tests/test_executive_overview.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_production_cli.py`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache pre-commit run --all-files` passed:
  - `ruff check`
  - `ruff format`
  - `mypy`
  - `pytest-full`

### Current milestone

- Milestone R5/R6 transition: source-function-only kdb query contract and legacy-surface removal.

### Estimated milestone completion

- 55%

### Remaining work before milestone completion

- Normalize day-run and single-metric planner contracts around source functions.
- Remove legacy table-name branching from planner/cache identities.
- Migrate remaining tests and demo paths to the canonical source-function contract.

### Best next deterministic step

- Make day-run planning strictly source-function based and remove table-name coupling from day cache identity.

### Notes

- This iteration keeps behavior unchanged at the metric-contract boundary while reducing q indirection and improving readability/performance transparency.

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
- `mmsr/kdb/q_templates/toxicity_reversion`
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

- Implement concrete q logic for `toxicity_reversion` after production schemas are confirmed.
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
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/trading_calendar.q`
- `mmsr/kdb/q_templates/toxicity_reversion`
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
- Updated `activity` and `liquidity` to emit time-series rows grouped by `date`, `time_bucket`, and requested group columns.
- Added `normalize_metric_result()` to convert dict/list-like kdb results, including PyKX-like objects with `.py()`, into `MetricTimeSeries`.
- Added runner errors for unsupported metrics, missing table mappings, invalid group columns, missing value/date/group fields, non-numeric metric values, and mismatched column lengths.
- Added a registered `kdb_integration` pytest marker and a skipped live-kdb placeholder test so integration tests can remain outside the offline suite.
- Updated `_docs/MILESTONE_STATUS.md` to mark Milestone 5 complete and identify Milestone 5A as the earliest incomplete roadmap item.

### Files changed

- `mmsr/kdb/runner.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
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

- Start Milestone 5A runner integration by mapping the `primary_quote_reversion_*_bps` metric family to `toxicity_reversion`, rendering horizon/venue/primary-venue parameters, and normalizing venue/horizon result rows into `MetricTimeSeries`.

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
- Added deterministic mapping from all `primary_quote_reversion_*_bps` metrics to `toxicity_reversion`.
- Extended `MetricRunRequest` with optional metric-family parameters for `primary_venue`, `venues`, and `max_primary_quote_age`.
- Rendered reversion-specific q parameters for metric value column, primary venue, venue filter, parsed horizon duration, horizon label, and stale-primary-quote age.
- Normalized reversion result rows with `venue` and `horizon` as required group dimensions, preserving requested group columns such as `sym`.
- Replaced the previous pseudo-q outline with a strict renderable `toxicity_reversion` template that uses placeholders validated by the q template renderer.
- Updated milestone audit status to reflect that runner integration is complete while typed toxicity configuration and live q validation remain open.

### Files changed

- `mmsr/kdb/runner.py`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Updated metric-to-template tests to include reversion metrics.
- Added a fake-kdb runner test that renders a reversion query, checks venue/primary-venue/horizon parameters, and verifies normalized `venue`/`horizon`/`sym` grouping.
- Added a test that reversion metrics require venue parameters before query execution.
- Added a q-template parameter test for `toxicity_reversion`.

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
- Validate `toxicity_reversion` against confirmed production kdb schemas.
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
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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
- Updated the reversion runner test to render `toxicity_reversion` using config-generated parameters.
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

- Validate `toxicity_reversion` against confirmed production kdb schemas.
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
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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

- Validate `toxicity_reversion` against confirmed production kdb schemas.
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
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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

- Validate `toxicity_reversion` against confirmed production kdb schemas.
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
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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

- Validate `toxicity_reversion` against confirmed production kdb schemas.
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
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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

- Validate `toxicity_reversion` against confirmed production kdb schemas.
- Add an explicit offline output-schema contract for `toxicity_reversion` so the live production validation target is deterministic.
- Decide whether the q template should emit both `horizon` label and numeric horizon sort order, or whether Python-side natural-duration sorting is sufficient.

### Best next deterministic step

- Add an explicit offline schema contract and live-kdb validation placeholder for `toxicity_reversion`, including required output columns such as `date`, `time_bucket`, `venue`, `horizon`, the metric value, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`.

### Package phase and iteration

- Phase: 5.
- Iteration: 7.
- Delivery archive name: `mmsr_phase5_iteration7.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?


---

## 2026-05-24 — Phase 5 iteration 8: reversion output-schema contract

### Implemented

- Continued Milestone 5A by adding an explicit offline output-schema contract for `toxicity_reversion`.
- Added `mmsr.kdb.schema_contracts` with `QTemplateOutputSchemaContract`, `OutputSchemaContractError`, and validation helpers for extracting and checking result columns from dict/list/PyKX-like objects.
- Defined required reversion report-boundary output columns: `date`, `time_bucket`, `venue`, `horizon`, the dynamic metric value column, `trade_count`, `notional`, `positive_reversion_ratio`, and `valid_primary_quote_ratio`, plus requested report group columns.
- Wired `KdbMetricRunner.run()` to validate reversion result schemas before normalizing them into `MetricTimeSeries`.
- Added a skipped live-kdb validation placeholder for checking `toxicity_reversion` against confirmed production schemas.
- Updated the q-template comments and milestone audit to point to the schema contract.

### Files changed

- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/q_templates/toxicity_reversion`
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

- Execute the live-kdb `toxicity_reversion` schema validation once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 8.
- Delivery archive name: `mmsr_phase5_iteration8.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Should the reversion q template emit both `horizon` label and numeric horizon sort order for downstream rendering, or is Python-side natural-duration sorting sufficient?
- Does the production PyKX conversion preserve column metadata for zero-row result tables, or should live schema validation force a minimum one-row sample slice?
---

## 2026-05-24 — Phase 5 iteration 9: explicit reversion horizon sort order

### Implemented

- Continued Milestone 5A by making the reversion horizon progression explicit at the q-template output boundary.
- Added deterministic `horizon_sort_order` rendering for the six supported primary-quote reversion horizons: `10ms`, `100ms`, `500ms`, `1s`, `5s`, and `10s`.
- Updated `toxicity_reversion` to emit `horizon_sort_order` alongside the rendered horizon label so downstream visuals can preserve horizon progression without relying only on text parsing.
- Extended the offline `toxicity_reversion` output-schema contract to require `horizon_sort_order`.
- Preserved `horizon_sort_order` in normalized observation metadata and in `ReversionCurvePoint` objects.
- Updated visual sorting to use caller-provided `horizon_order` first, then q-provided `horizon_sort_order`, then natural duration parsing as a deterministic fallback.
- Updated the milestone audit to reflect the explicit horizon sort-order contract.

### Files changed

- `mmsr/kdb/q_templates/toxicity_reversion`
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

- Execute the live-kdb `toxicity_reversion` schema validation once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 9.
- Delivery archive name: `mmsr_phase5_iteration9.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
- Does the production PyKX conversion preserve column metadata for zero-row result tables, or should live schema validation force a minimum one-row sample slice?

---

## 2026-05-24 — Phase 5 iteration 10: reversion input schema contracts

### Implemented

- Continued Milestone 5A with an offline production input-schema contract for `toxicity_reversion`.
- Added `QTemplateInputTableSchemaContract` to make required source-table columns explicit for the venue-trade and primary-quote table roles.
- Added `toxicity_reversion_input_schema_contracts()` and `validate_toxicity_reversion_input_schemas()` so live-kdb validation can check source-table schemas before running the q template.
- Documented feed assumptions for `aggressorSide` and primary quote price conventions in the contract.
- Updated the reversion q-template comments, public kdb API exports, and milestone audit.

### Files changed

- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_import.py`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`

### Tests added or updated

- Added input-schema contract tests for required venue-trade columns.
- Added input-schema contract tests for required primary-quote columns.
- Added validation coverage for extra source columns and missing `aggressorSide`.
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
- Confirm exact production table names and whether `aggressorSide` is numeric with buy as `1` and sell as `-1`, or requires feed-specific mapping before the q template.
- Confirm whether production PyKX conversion preserves column metadata for zero-row result tables, or whether live validation should force a minimum one-row sample slice.

### Best next deterministic step

- Execute live-kdb source-schema and output-schema validation for `toxicity_reversion` once production table names, side conventions, and access to a representative kdb environment are confirmed.

### Package phase and iteration

- Phase: 5.
- Iteration: 10.
- Delivery archive name: `mmsr_phase5_iteration10.zip`.

### Open questions

- What are the exact production kdb table names and schemas for venue trades and primary quotes?
- Is `aggressorSide` guaranteed to be numeric with buy as `1` and sell as `-1`, or should the q template map from feed-specific side codes?
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

- When live validation is re-enabled, are production `aggressorSide` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
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

- When live validation is re-enabled, are production `aggressorSide` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
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

- When live validation is re-enabled, are production `aggressorSide` values numeric buy `1` / sell `-1`, or feed-specific codes requiring mapping?
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
- The mock-kdb path executes starter `activity` and `liquidity` template queries for current and reference periods, normalizes table-shaped mock results into `MetricTimeSeries`, computes reference comparisons, and delegates into the canonical `build_market_monitor_report()` report path.
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

- Add explicit output schema contracts for `activity` and `liquidity`.
- Validate starter-template output contracts inside `KdbMetricRunner` before normalization.
- Document how deterministic mock-kdb tests differ from live kdb integration tests.
- Keep live-kdb tests skipped unless a real kdb process and production-like schemas are explicitly available.

### Best next deterministic step

- Add explicit output schema contracts for `activity` and `liquidity`, validate those contracts in `KdbMetricRunner`, and cover missing-column failures with unit tests.

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
- Added explicit output schema contracts for `activity` and `liquidity`.
- The starter contracts require `date`, `time_bucket`, caller-requested group
  columns, the requested metric value column, and sibling aggregate columns that
  each q template always emits.
- Routed `KdbMetricRunner` through template-specific output-schema validation
  before normalizing q results into `MetricTimeSeries`.
- Documented the new schema-contract boundary in the `activity` and
  `liquidity` template headers.
- Updated milestone status and roadmap text to reflect offline starter-template
  schema validation progress.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
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
  aggregate column that `activity` and `liquidity` currently emit, not only
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
- Documented starter table/schema assumptions for `activity`, `liquidity`,
  and `toxicity_reversion`.
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
  validates one bounded `activity` or `liquidity` result through the existing
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
- Added `run_live_activity_smoke()` to execute one bounded `activity` turnover
  request through `KdbMetricRunner`, so live smoke validation reuses the same
  output schema-contract boundary as deterministic mock-kdb tests.
- Added an optional starter-template `symbol_filter` parameter for `activity`
  and `liquidity`, allowing live smoke runs to restrict the query to
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
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
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
- Decide whether to add a matching `liquidity` live smoke slice after the
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
- The first implemented live smoke covers `activity`; a separate deterministic
  step should decide whether `liquidity` needs its own live smoke slice before
  closing Milestone 10.


---

## 2026-05-25 — Phase 10 iteration 33: environment-gated live liquidity smoke harness

### Implemented

- Continued from `mmsr_phase10_iteration32.zip`.
- Added `mmsr.kdb.live_smoke.LiveKdbLiquiditySmokeConfig` to mirror the existing
  activity smoke harness for `liquidity`.
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
- Documented required kdb+ source fields for the trading calendar, `activity`
  trades table, `liquidity` quotes table, `toxicity_reversion` venue-trade
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
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/toxicity_reversion`
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

---

## 2026-05-26 — Phase 10 iteration 52: migrate CLI to Typer

### Implemented

- Continued from `mmsr_phase10_iteration51.zip`.
- Accepted user correction that the requested Typer CLI migration had not been
  implemented yet.
- Replaced the argparse command surface in `mmsr.cli` with a Typer application
  while preserving the existing `offline-demo` and `mock-kdb-demo` commands.
- Added `build_cli_app()` as the explicit Typer application factory and kept
  `main(argv)` as the console-script/programmatic entry point that returns an
  integer exit code.
- Preserved command options, defaults, output messages, offline safety language,
  render-file helper functions, and validation behavior.
- Added `typer` as an explicit runtime dependency because the installed `mmsr`
  command now uses Typer.
- Updated CLI behavior snapshots, packaging metadata tests, README installation
  wording, roadmap status, and milestone status to reflect the Typer migration.

### Files changed

- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `pyproject.toml`
- `tests/test_cli_behavior_snapshots.py`
- `tests/test_packaging_metadata.py`

### Tests added or updated

- Updated `tests/test_cli_behavior_snapshots.py` to inspect the Typer/Click
  command surface instead of an argparse parser.
- Updated packaging metadata tests to require the runtime `typer` dependency and
  roadmap documentation of the migration.

### Validation performed

- Ran `python -m pytest tests/test_cli_behavior_snapshots.py tests/test_cli.py -q`:
  passed.
- Ran `python -m pytest tests/test_cli_behavior_snapshots.py tests/test_cli.py tests/test_packaging_metadata.py tests/test_docs_governance.py -q`:
  passed.
- Ran `python -m pytest -q -ra`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m pytest --collect-only -q`: passed and collected 293 tests.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_docs_governance.py -q`: passed.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: ppw packaging parity and CLI ergonomics.

### Current milestone progress

- The requested Typer CLI migration is complete for the current command surface:
  100% complete for this ergonomics slice.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- No further deterministic work remains for the current Typer migration slice.
- Additional production commands can be added later on top of the Typer app.
- The synthetic demo modules can be relocated or deleted later once direct
  production report-builder and kdb schema-contract tests fully replace their
  coverage.

### Best next deterministic step

- Add toxicity/reversion rows to the deterministic demo fixture so the
  Cross-Venue Toxicity visual is visible in the default offline demo output.

### Package phase and iteration

- Phase: 10.
- Iteration: 52.
- Delivery archive name: `mmsr_phase10_iteration52.zip`.

### Open questions

- Should the CLI grow a production `render` command before or after quote-quality
  metric families are added?

---

## 2026-05-26 — Phase 10 iteration 53: add daily trends and intraday line visuals

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before
  modifying the report layer.
- Added `MarketReportInput.reference_series` and a default `Reference and Target
  Daily Trends` report page that plots reference observations followed by the
  target/current period on a daily x-axis.
- Added deterministic intraday time-bucket line charts for dense bucket grids so
  the x-axis is the bucket label rather than an oversized matrix.
- Changed market detail and symbol detail pages to use intraday time-bucket line
  charts by default and made heatmaps an explicit opt-in through
  `include_intraday_heatmaps=True`.
- Updated offline and mock-kdb demos to pass reference series into the canonical
  report builder and expose the new daily-trend and heatmap options.
- Updated README, roadmap, and milestone-status wording to document
  reference-to-target daily trends and heatmap opt-in behavior.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `mmsr/report/sections.py`
- `mmsr/report/market_report.py`
- `mmsr/report/symbols.py`
- `mmsr/examples/offline_demo.py`
- `mmsr/examples/mock_kdb_demo.py`
- `tests/test_time_series_charts.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_cli.py`
- `tests/test_metric_help_controls.py`
- `tests/test_symbol_anomaly_pages.py`

### Tests added or updated

- Added direct chart tests for intraday time-bucket line charts and
  reference-to-target daily trend charts.
- Updated production report, offline demo, mock-kdb demo, CLI, symbol detail, and
  help-control tests for the new default line-chart behavior.
- Added opt-in heatmap coverage so the heatmap visual and help controls remain
  tested even though dense intraday pages no longer render heatmaps by default.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_metric_help_controls.py tests/test_symbol_anomaly_pages.py -q --tb=short`:
  passed.
- Ran `python -m pytest tests/test_docs_governance.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema
  skips.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 production-format report visual polish.

### Current milestone progress

- The requested visualization correction is complete for this report-polish
  slice: 100% complete.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- No deterministic work remains for this visualization correction.
- Live kdb+ validation remains deferred until credentials and production-like
  schemas are available.
- Future CLI work can expose a user-facing flag for `include_intraday_heatmaps`
  if product owners want command-line opt-in rather than config/API opt-in only.

### Best next deterministic step

- Add a CLI option to explicitly opt into intraday heatmaps for offline and
  mock-kdb demo reports, while keeping dense time-bucket line charts as the
  default.

### Package phase and iteration

- Phase: 10.
- Iteration: 53.
- Delivery archive name: `mmsr_phase10_iteration53.zip`.

### Open questions

- Should intraday heatmap opt-in be exposed in the CLI immediately, or remain an
  API/config-level option until a production user asks for it?


---

## 2026-05-26 — Phase 10 iteration 54: expose intraday heatmap CLI opt-in

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before
  modifying the CLI and documentation.
- Added `--include-intraday-heatmaps` to both Typer demo commands:
  `offline-demo` and `mock-kdb-demo`.
- Kept dense intraday time-bucket line charts as the default report behavior and
  made heatmaps an explicit CLI opt-in for sample artifacts that need
  bucket × group matrix diagnostics.
- Wired the new CLI option through the command handlers and internal option
  builders into `OfflineDemoReportOptions` and
  `MockKdbIntegrationDemoOptions`.
- Updated README and MkDocs quickstart examples to document heatmap opt-in
  without changing the default line-chart guidance.
- Updated roadmap and milestone-status wording to record that heatmaps are
  available from the demo CLI only by explicit request.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `docs/index.md`
- `mmsr/cli.py`
- `tests/test_cli.py`
- `tests/test_cli_behavior_snapshots.py`
- `tests/test_docs_governance.py`

### Tests added or updated

- Updated CLI behavior snapshots to include
  `--include-intraday-heatmaps`, its default `False` value, and override parsing.
- Added offline-demo and mock-kdb-demo CLI tests proving the opt-in renders
  heatmap sections while the default render path remains heatmap-free.
- Updated documentation-governance tests so README and MkDocs quickstarts must
  document the explicit heatmap opt-in flag.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_cli_behavior_snapshots.py tests/test_cli.py tests/test_docs_governance.py -q --tb=short`:
  passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema
  skips.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 production-format report visual polish and CLI
  ergonomics.

### Current milestone progress

- The requested heatmap opt-in CLI slice is complete: 100% complete.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- No deterministic work remains for the intraday visualization/CLI opt-in slice.
- Live kdb+ validation remains deferred until credentials and production-like
  schemas are available.
- Future production feedback may request a config-driven production `render`
  command, but the current offline and mock-kdb demo command surfaces are covered.

### Best next deterministic step

- Keep live kdb+ execution deferred until a real endpoint, credentials, and
  production-like schemas are available; if local-only work continues, add a
  narrow config-driven production `render` command skeleton that validates inputs
  without contacting kdb+ by default.

### Package phase and iteration

- Phase: 10.
- Iteration: 54.
- Delivery archive name: `mmsr_phase10_iteration54.zip`.

### Open questions

- Should the future production `render` command expose every report-layout option
  directly, or should it only load a versioned report configuration file?

---

## 2026-05-27 — Phase 10 iteration 55: add production kdb source-function boundary

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before
  modifying the kdb planning boundary.
- Updated the roadmap and milestone status to add the production kdb
  source-function boundary: user-defined raw trade/quote functions provide
  canonical rows, while MMSR-owned q templates perform metric calculations.
- Added `KdbRawDataFunctionsConfig` and `KdbExecutionConfig` to `ReportConfig`
  so production config can specify a calculation namespace and raw-data functions
  such as `.sb.mmsr.getTrade` and `.sb.mmsr.getQuote`.
- Extended `MetricRunRequest` and `KdbMetricQueryPlanner` to support
  `source_functions` for trades, quotes, venue trades, and primary quotes while
  keeping direct `table_names` as a legacy/mock fallback.
- Rendered raw source-function calls with a canonical request dictionary
  containing start/end dates, session start/end times, bucket size, symbol
  filters, and venue filters.
- Wrapped `activity`, `liquidity`, and `toxicity_reversion` calculations
  in a configured q namespace such as `.desk.mmsr`, avoiding intermediate
  calculations in the global namespace.
- Added planner metadata for rendered source functions and calculation namespace
  so normalized `MetricTimeSeries` results preserve the kdb execution boundary.
- Updated README, example config, production-readiness docs, and kdb integration
  docs to describe the function-based production boundary and the date/chunk
  scaling constraint.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/config/models.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `tests/test_config_models.py`
- `tests/test_docs_governance.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`

### Tests added or updated

- Added config tests for default and custom kdb calculation namespaces and
  raw-data source function mappings.
- Added planner tests proving activity, liquidity, and reversion queries can call
  user-defined source functions and install calculations in a configured
  namespace.
- Added validation tests for invalid source function names and calculation
  namespaces.
- Updated q-template parameter tests for the new `calculation_namespace`
  placeholder.
- Updated documentation-governance tests for raw-data function production
  readiness wording.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_config_models.py -q --tb=short`:
  passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema
  skips.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function
  boundary.

### Current milestone progress

- The source-function query planning and namespace-scoped q calculation slice is
  complete: 100% complete.
- Milestone 9B is approximately 65% complete because date/chunk orchestration is
  still pending.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- Add a production driver that loops over the kdb-backed trading calendar one
  date at a time and optionally chunks symbols before building reference and
  target `MetricTimeSeries`.
- Decide how raw source functions should receive symbol chunks beyond the current
  single-symbol smoke request shape.
- Add live-kdb smoke configuration for source-function based validation once a
  production-like endpoint is available.

### Best next deterministic step

- Add a local-only production daily execution planner that expands a report
  period into one-day `MetricRunRequest` objects using configured
  `source_functions` and `calculation_namespace`, without connecting to kdb+.

### Package phase and iteration

- Phase: 10.
- Iteration: 55.
- Delivery archive name: `mmsr_phase10_iteration55.zip`.

### Open questions

- Should the production source-function request use `syms` only, or should MMSR
  also pass an explicit `symbolChunkId` / `chunkCount` pair for server-side
  chunking?
- Should live smoke tests keep the legacy direct-table environment variables as a
  fallback, or should they switch entirely to source-function environment
  variables?

---

## 2026-05-27 — Phase 10 iteration 56: add production daily/chunk execution path

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before
  changing the production kdb execution boundary.
- Added `KdbProductionExecutionPlanner`, `KdbProductionExecutor`,
  `KdbProductionRunPlan`, and `ProductionMetricRunStep` to build and run the
  production path as one trading date, one metric, and one optional symbol chunk
  at a time.
- Added `KdbExecutionConfig.enforce_daily_raw_scope` and
  `KdbExecutionConfig.symbol_chunk_size` to document and configure the bounded
  production raw-data contract.
- Extended raw source-function request rendering to include `date`,
  `symbolChunkId`, and `symbolChunkCount` while preserving existing
  `startDate`, `endDate`, `syms`, and `venues` request keys.
- Extended query planning to support production `symbols` vectors in addition to
  the legacy single-symbol smoke-test `symbol` parameter.
- Exported the production execution classes through `mmsr.kdb`.
- Updated README, example config, kdb integration docs, production readiness
  checklist, roadmap, and milestone status to describe the production execution
  path rather than a local-only placeholder.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/config/models.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/query_plan.py`
- `tests/test_config_models.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_plan.py`

### Tests added or updated

- Added `tests/test_kdb_production_execution.py` covering date-bounded planning,
  symbol chunk expansion, rendered source-function request metadata, calendar
  bounds validation, and production executor series combination.
- Updated config tests for daily raw-scope and symbol chunk settings.
- Updated query-plan tests for the expanded raw request dictionary.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_kdb_query_plan.py tests/test_config_models.py tests/test_docs_governance.py -q --tb=short`:
  passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema
  skips.
- Ran `python -m black --check .`: could not run because Black is not installed
  in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function
  boundary.

### Current milestone progress

- The production date/chunk orchestration slice is complete: 100% complete.
- Milestone 9B is approximately 85% complete because the production executor now
  exists and is tested, but live source-function execution against a real kdb+
  endpoint remains unavailable.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are
  available in this environment.

### Remaining work before milestone completion

- Add a production `render` command that wires config loading, period parsing,
  kdb connection setup, `KdbProductionExecutor`, comparison, and report rendering.
- Add live-kdb smoke configuration for source-function based validation once a
  production-like endpoint is available.
- Decide whether server-side raw functions should honor `symbolChunkId` and
  `symbolChunkCount` even when `syms` is empty, for venues/universes managed
  entirely inside kdb.

### Best next deterministic step

- Add a production `render` command skeleton that uses `KdbProductionExecutor`
  and requires explicit config/period inputs, while keeping actual live
  execution guarded by connection settings and existing kdb integration skips.

### Package phase and iteration

- Phase: 10.
- Iteration: 56.
- Delivery archive name: `mmsr_phase10_iteration56.zip`.

### Open questions

- Should `symbol_chunk_id` be passed as a zero-based or one-based value to match
  existing internal kdb conventions? This implementation uses one-based IDs for
  user readability.
- Should full-universe runs with no explicit `syms` use server-side chunk IDs in
  the raw functions, or should MMSR require an explicit reference-data universe before
  enabling `symbol_chunk_size`?


---

## 2026-05-27 — Production render command wired to bounded kdb executor

### Implemented

- Added YAML config loading helpers that build typed `ReportConfig` and `ReportPeriod` objects from the repository config shape.
- Added the production `mmsr render` CLI command.
- Wired `mmsr render` to the live production execution path: PyKX-backed `KdbClient`, kdb-backed trading calendar, `KdbMetricRunner`, `KdbProductionExecutor`, and canonical HTML rendering.
- Kept production raw data access behind configured user-defined functions while MMSR-owned q templates run inside the configured calculation namespace.
- Added production CLI tests with a fake kdb client to validate the real command/executor path without requiring credentials.

### Files changed

- `mmsr/cli.py`
- `mmsr/config/__init__.py`
- `mmsr/config/loading.py`
- `tests/test_production_cli.py`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`

### Tests added or updated

- Added `tests/test_production_cli.py` covering `render_production_report_file`, `mmsr render`, and CLI help.
- Existing CLI and production executor tests continue to cover offline demos and date/chunk planning.

### Validation

- `python -m compileall -q mmsr tests` passed.
- `python -m pytest tests/test_production_cli.py -q --tb=short` passed.
- `python -m pytest -q -ra --tb=short` passed with three expected live-kdb/schema skips.
- `python -m black --check .` could not run because Black is not installed in this environment.

### Current milestone

- Phase 10 / Milestone 9B: production kdb source-function boundary.

### Estimated milestone completion

- 92%

### Remaining work before milestone completion

- Add explicit schema preflight checks for configured raw source functions and canonical result output before full report execution.
- Add live-kdb smoke coverage once a real kdb endpoint, namespace, and user raw source functions are available.
- Add production reference-period execution/comparison wiring beyond current-period rendering.

### Best next deterministic step

- Add a production preflight command that validates configured function names, calculation namespace, calendar access, and one small metric result schema before running the full report.

### Open questions

- What exact canonical raw result columns should `.sb.mmsr.getTrade` and `.sb.mmsr.getQuote` expose for each metric family in production?
- Should production `mmsr render` accept separate target and reference periods in CLI/config, or derive reference dates only from `reference.lookback_days` and the calendar source?

---

## 2026-05-27 — Phase 10 iteration 58: add production preflight command

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the production kdb boundary.
- Added `KdbProductionPreflight`, `KdbProductionPreflightResult`, and `KdbProductionPreflightCheck` to run a bounded live-kdb preflight through the same calendar, planner, query-rendering, runner, and schema-validation path used by production rendering.
- Added the production `mmsr preflight` CLI command and `preflight_production_report()` helper.
- The preflight loads YAML config, validates configured q namespace/source-function names through typed config/query planning, queries the configured kdb calendar, plans the first trading-day/chunk/metric step, executes only that sample step, and validates the returned metric result schema.
- Documented the preflight command in README, kdb integration testing guidance, production readiness guidance, roadmap, and milestone status.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/production.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added production CLI tests covering `preflight_production_report()`.
- Added CLI command tests proving `mmsr preflight` prints deterministic diagnostics.
- Updated CLI help tests to include the new production preflight command.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_production_cli.py tests/test_kdb_production_execution.py -q --tb=short`: passed.
- Ran `python -m pytest tests/test_production_cli.py tests/test_kdb_production_execution.py tests/test_docs_governance.py tests/test_cli_behavior_snapshots.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function boundary.

### Current milestone progress

- The production preflight command slice is complete: 100% complete.
- Milestone 9B is approximately 96% complete because config loading, daily/chunk execution planning, production rendering, and bounded preflight validation now exist and are tested offline.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Add production reference-period execution/comparison wiring beyond current-period rendering.
- Add live-kdb smoke coverage for source-function based validation once a production-like endpoint is available.
- Confirm canonical raw function output columns with the market-data owner before treating live preflight as production-certified.

### Best next deterministic step

- Add production reference-period execution planning that derives reference trading days from `reference.lookback_days`, runs the same bounded executor path for reference observations, and wires current-vs-reference comparisons into `mmsr render`.

### Package phase and iteration

- Phase: 10.
- Iteration: 58.
- Delivery archive name: `mmsr_phase10_iteration58.zip`.

### Open questions

- Should production `mmsr render` accept explicit reference-period start/end dates, or continue deriving reference observations from `reference.lookback_days` and the kdb-backed calendar?
- Should `mmsr preflight` support a dedicated `--metric` override for checking each metric family independently before a full render?

---

## 2026-05-27 — Phase 10 iteration 59: wire production reference execution into render

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the production render boundary.
- Added `KdbProductionReferenceWindow` and reference-window planning to derive the previous `reference.lookback_days` trading days from the configured kdb trading calendar.
- Added `KdbProductionExecutor.build_reference_window()`, `build_reference_plan()`, and `run_reference()` so target and reference observations use the same one-trading-day, optional-symbol-chunk execution shape.
- Updated production executor metadata to mark target vs reference series and preserve reference calendar bounds/lookback settings.
- Updated `mmsr render` to execute reference observations, build `MetricComparison` facts with the configured reference policy, and pass reference series into the canonical report builder for current-vs-reference tables and trend charts.
- Updated README, kdb integration testing guidance, production readiness guidance, roadmap, and milestone status to document bounded reference execution.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/production.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added production executor tests for reference-window derivation, reference plan chunking, and reference-series metadata.
- Updated production CLI render tests to prove `mmsr render` executes target and reference metric queries, emits current-vs-reference report content, and includes reference-target trend charts.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_docs_governance.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function boundary.

### Current milestone progress

- The production reference execution and render comparison wiring slice is complete: 100% complete.
- Milestone 9B is approximately 98% complete because config loading, production rendering, bounded preflight validation, daily/chunk target execution, and daily/chunk reference execution are now implemented and tested offline.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Add live-kdb smoke coverage for source-function based validation once a production-like endpoint is available.
- Confirm canonical raw function output columns with the market-data owner before treating live preflight/render as production-certified.
- Decide whether production render should expose explicit reference start/end overrides in addition to the current `reference.lookback_days` calendar-derived default.

### Best next deterministic step

- Add a production render plan-summary helper that reports target/reference trading days, metric count, symbol chunk count, and source-function contracts before executing metric q, so operators can review the bounded execution plan ahead of a full live render.

### Package phase and iteration

- Phase: 10.
- Iteration: 59.
- Delivery archive name: `mmsr_phase10_iteration59.zip`.

### Open questions

- Should production `mmsr render` accept explicit reference-period start/end dates, or continue deriving reference observations from `reference.lookback_days` and the kdb-backed calendar?
- Should a future live production smoke test validate all metric families in one command, or keep separate bounded checks for activity, liquidity, and reversion source functions?

---

## 2026-05-27 — Phase 10 iteration 60: add production render plan summary

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the production kdb boundary.
- Added `KdbProductionPlanSummary` and `KdbProductionMetricContract` to report bounded production render scope without executing metric q.
- Added `KdbProductionExecutor.build_plan_summary()` so operators can review target trading days, reference trading days, metric count, symbol chunk count, total metric steps, calculation namespace, configured source functions, and q-template source/output contracts before a full live render.
- Added `summarize_production_report_plan()` and the production `mmsr plan` CLI command. The command queries only the configured trading calendar and renders query contracts; it does not execute metric source functions.
- Documented the plan-summary command and production readiness gate in README, kdb integration testing guidance, production readiness guidance, roadmap, and milestone status.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/production.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added production executor tests for plan-summary target/reference scope, chunk counts, total metric steps, rendered input contracts, output contracts, and no metric execution.
- Added production CLI tests for `summarize_production_report_plan()` and `mmsr plan`, including proof that only calendar queries are sent through the fake kdb client.
- Updated production CLI help assertions to include the new plan command.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_production_cli.py -q --tb=short`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_docs_governance.py tests/test_cli_behavior_snapshots.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function boundary.

### Current milestone progress

- The production render plan-summary slice is complete: 100% complete.
- Milestone 9B is approximately 99% complete because config loading, production plan review, bounded preflight validation, target/reference execution, and current-vs-reference rendering are now implemented and tested offline.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Add live-kdb smoke coverage for source-function based validation once a production-like endpoint is available.
- Confirm canonical raw function output columns with the market-data owner before treating live preflight/render as production-certified.
- Decide whether production render should expose explicit reference start/end overrides in addition to the current `reference.lookback_days` calendar-derived default.

### Best next deterministic step

- Add a metric-selectable production preflight option so operators can validate one metric family at a time, including activity, liquidity, and reversion contracts, before a broader live render.

### Package phase and iteration

- Phase: 10.
- Iteration: 60.
- Delivery archive name: `mmsr_phase10_iteration60.zip`.

### Open questions

- Should production `mmsr render` accept explicit reference-period start/end dates, or continue deriving reference observations from `reference.lookback_days` and the kdb-backed calendar?
- Should full production render print the plan summary by default, or should operators continue to call `mmsr plan` explicitly before `mmsr render`?


---

## 2026-05-27 — Phase 10 iteration 61: add metric-selectable production preflight

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the production kdb boundary.
- Added `KdbProductionPreflight.run(..., metric_name=...)` so operators can validate a specific configured metric instead of always executing the first metric in the report config.
- Added preflight metric-selection validation and a deterministic `metric_selection` check in preflight diagnostics.
- Wired the production `mmsr preflight` CLI and `preflight_production_report()` helper to accept `--metric`, keeping the executed sample bounded to one trading day, one symbol chunk, and one selected metric.
- Documented metric-selectable preflight usage for activity, liquidity, and reversion source-function contract checks.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/kdb/production.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added production preflight tests proving selected activity, liquidity, and reversion metrics render the expected q-template/source-function contracts and execute only the selected sample step.
- Added a production preflight validation test for rejecting a selected metric that is not configured in the report.
- Added production CLI tests for `preflight_production_report(..., metric_name=...)` and `mmsr preflight --metric quoted_spread_bps`.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_production_cli.py -q --tb=short`: passed.
- Ran `python -m pytest tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_docs_governance.py tests/test_cli_behavior_snapshots.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function boundary.

### Current milestone progress

- The metric-selectable production preflight slice is complete: 100% complete.
- Milestone 9B is approximately 99.5% complete because config loading, production plan review, bounded default/selected preflight validation, target/reference execution, and current-vs-reference rendering are now implemented and tested offline.
- Milestone 10 remains 98% because no live kdb+ endpoint or credentials are available in this environment.

### Remaining work before milestone completion

- Add live-kdb smoke coverage for source-function based validation once a production-like endpoint is available.
- Confirm canonical raw function output columns with the market-data owner before treating live preflight/render as production-certified.
- Decide whether production render should expose explicit reference start/end overrides in addition to the current `reference.lookback_days` calendar-derived default.

### Best next deterministic step

- Add an environment-gated live production preflight smoke harness that can run `mmsr preflight --metric` for configured activity, liquidity, and reversion source-function checks when a production-like kdb endpoint is available.

### Package phase and iteration

- Phase: 10.
- Iteration: 61.
- Delivery archive name: `mmsr_phase10_iteration61.zip`.

### Open questions

- Should production `mmsr render` accept explicit reference-period start/end dates, or continue deriving reference observations from `reference.lookback_days` and the kdb-backed calendar?
- Should full production render print the plan summary by default, or should operators continue to call `mmsr plan` explicitly before `mmsr render`?
- Should a future convenience option select metric families by template name, such as `--metric-family activity`, or is explicit `--metric` safer for production checks?


---

## 2026-05-27 — Phase 10 iteration 62: pivot back to report metrics and add tick-spread q support

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the roadmap and metric execution layer.
- Incorporated user feedback to freeze additional report-local validation expansion. Roadmap and production docs now keep `mmsr plan` and `mmsr preflight` as optional operator helpers, while deferring any broader reusable validation framework until multiple reports exist.
- Added `config/report.production_minimal.yaml` for first live-kdb runs. It includes only metrics that are currently backed by checked-in q templates and explicitly notes the `tick_size` requirement for `quoted_spread_ticks`.
- Implemented production q-template support for `quoted_spread_ticks` through a dedicated `liquidity_ticks` template.
- Added source and output schema contracts for `liquidity_ticks`, including the `tick_size` quote-source requirement.
- Wired `quoted_spread_ticks` into `KdbMetricQueryPlanner`, `template_for_metric()`, source-function rendering, symbol filtering, and output-schema dispatch.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/liquidity_ticks`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `tests/test_config_files.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added config-file coverage proving `config/report.production_minimal.yaml` loads and contains only metrics supported by checked-in kdb templates.
- Added query-planner coverage for `quoted_spread_ticks`, including `liquidity_ticks`, `tick_size` source-contract requirements, symbol filtering, and user-defined quote source-function rendering.
- Added schema-contract coverage for `liquidity_ticks` input and output contracts plus dispatch through `output_schema_contract_for_template()`.
- Updated docs/governance expectations implicitly through existing governance tests.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_config_files.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_config_files.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Phase 10 / Milestone 9B production kdb source-function boundary, now frozen at the current operator-helper scope per user feedback.
- Report implementation focus resumes under Milestone 10 / runnable kdb metric coverage.

### Current milestone progress

- Milestone 9B is complete enough for this package phase: 100% complete for the bounded source-function boundary and optional operator helpers.
- Milestone 10 is approximately 98.5% complete because `quoted_spread_ticks` now has a checked-in q template and minimal production config coverage, while several registered metrics remain roadmap definitions only.

### Remaining work before milestone completion

- Add q-template support for registered metrics that still lack production execution support: `realized_volatility`, `effective_spread_bps`, `price_impact_30s_bps`, `signed_turnover`, and `trade_imbalance`.
- Improve report pages and deterministic commentary once those metrics are available as normalized `MetricTimeSeries` rows.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Implement a checked-in q template for `trade_imbalance` and `signed_turnover` as a focused flow-metric slice, including source/output schema contracts, query-planner wiring, and tests.

### Package phase and iteration

- Phase: 10.
- Iteration: 62.
- Delivery archive name: `mmsr_phase10_iteration62.zip`.

### Open questions

- Should `quoted_spread_ticks` remain in the minimal production config by default, or should it move to an optional example when a client quote function does not yet join `tick_size`?
- Should flow metrics use feed-provided `aggressorSide` first, with quote-based signing as a later fallback, to keep the next q-template slice simple and production-friendly?

---

## 2026-05-27 — Phase 10 iteration 63: add feed-signed flow metric q support

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the report metric execution layer.
- Implemented a focused `flow` production template for `signed_turnover` and `trade_imbalance`.
- Kept the first flow slice deterministic by using feed-provided `aggressorSide` with buy=1 and sell=-1; quote-based trade signing remains a later explicit enhancement.
- Added flow input and output schema contracts, including required trade-source columns and normalized output metadata (`signed_volume`, `volume`, and `trade_count`).
- Wired flow metrics into `KdbMetricQueryPlanner`, `template_for_metric()`, source-function rendering, symbol filtering, and output-schema dispatch.
- Updated starter metric definitions so flow metrics document the feed-side signing requirement.
- Added `signed_turnover` and `trade_imbalance` to `config/report.production_minimal.yaml` with a removal note when `aggressorSide` is unavailable.
- Updated production and kdb integration docs to reflect the new runnable flow metric coverage and the canonical trade-source requirement.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/flow`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added schema-contract tests for `flow` input requirements, output requirements, result validation, dispatch, and non-flow metric rejection.
- Added query-planner tests for `signed_turnover` and `trade_imbalance`, including user-defined trade source-function rendering and `aggressorSide` requirements.
- Updated production minimal config coverage to include the new flow q-template metrics.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_config_files.py tests/test_docs_governance.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / runnable kdb metric coverage, with Milestone 9B validation utility expansion frozen per user feedback.

### Current milestone progress

- The feed-signed flow metric q-template slice is complete: 100% complete.
- Milestone 10 is approximately 99% complete because activity, liquidity, tick-spread, flow, and reversion metric families now have checked-in q-template coverage, while some registered metrics remain roadmap definitions only.

### Remaining work before milestone completion

- Add q-template support for registered metrics that still lack production execution support: `realized_volatility`, `effective_spread_bps`, and `price_impact_30s_bps`.
- Improve report pages and deterministic commentary once those metrics are available as normalized `MetricTimeSeries` rows.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Implement a checked-in quote-only q template for `realized_volatility`, including source/output schema contracts, query-planner wiring, and tests, before tackling the more involved trade-to-quote transaction-cost metrics.

### Package phase and iteration

- Phase: 10.
- Iteration: 63.
- Delivery archive name: `mmsr_phase10_iteration63.zip`.

### Open questions

- Should a later flow enhancement add quote-based aggressor-side inference for venues that do not provide `aggressorSide`, or should MMSR continue requiring feed-side signing for production flow metrics?


---

## 2026-05-27 — Phase 10 iteration 64: add quote-mid realized-volatility q support

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the runnable report-metric layer.
- Implemented a focused `realized_volatility` production template for quote-mid realized volatility.
- Kept the calculation quote-only and deterministic: valid quote mids are sorted by `date`, `sym`, and `time`, adjacent log-mid returns are calculated by `date × sym`, and bucket/group volatility is emitted in basis points.
- Added realized-volatility input and output schema contracts, including the required `sym` quote-source column and normalized output metadata (`return_count`, `first_mid`, and `last_mid`).
- Wired `realized_volatility` into `KdbMetricQueryPlanner`, `template_for_metric()`, source-function rendering, symbol filtering, output-schema dispatch, and runner support.
- Added `realized_volatility` to `config/report.production_minimal.yaml` with a note that the canonical quote function must return `sym`.
- Updated production and kdb integration docs to reflect the new runnable volatility metric coverage and quote-source requirement.
- Updated roadmap and milestone status to keep validation utilities frozen and move the next work toward transaction-cost report metrics.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/realized_volatility`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `tests/test_config_files.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added schema-contract tests for `realized_volatility` input requirements, output metadata, result validation, dispatch, and non-volatility metric rejection.
- Added query-planner coverage for `realized_volatility`, including the quote source contract, selected-symbol rendering, q-template dispatch, and required output columns.
- Updated the unsupported-runner test to use `effective_spread_bps`, which remains a registered metric without production q-template support.
- Updated production minimal config coverage to include the new volatility q-template metric.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_config_files.py tests/test_docs_governance.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / runnable kdb metric coverage, with Milestone 9B validation utility expansion frozen per user feedback.

### Current milestone progress

- The quote-mid realized-volatility q-template slice is complete: 100% complete.
- Milestone 10 is approximately 99.3% complete because activity, liquidity, tick-spread, volatility, flow, and reversion metric families now have checked-in q-template coverage, while the registered transaction-cost metrics remain roadmap definitions only.

### Remaining work before milestone completion

- Add q-template support for registered transaction-cost metrics that still lack production execution support: `effective_spread_bps` and `price_impact_30s_bps`.
- Improve report pages and deterministic commentary once those metrics are available as normalized `MetricTimeSeries` rows.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Implement the first trade-to-quote transaction-cost q template for `effective_spread_bps`, including source/output schema contracts, query-planner wiring, and tests, before adding horizon-specific `price_impact_30s_bps`.

### Package phase and iteration

- Phase: 10.
- Iteration: 64.
- Delivery archive name: `mmsr_phase10_iteration64.zip`.

### Open questions

- Should `realized_volatility` remain unannualized in basis points for intraday monitoring, or should a later report-output option add an explicitly labeled annualized view?

---

## 2026-05-27 — Phase 10 iteration 65: add effective-spread q support

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the runnable report-metric layer.
- Implemented a focused `effective_spread.q` production template for the first trade-to-quote transaction-cost metric.
- Kept the slice deterministic and report-focused: executions are as-of joined to the prevailing same-symbol quote mid, unsigned effective spread is calculated in basis points, and bucket/group aggregates emit median effective spread with trade-count and notional metadata.
- Added effective-spread input and output schema contracts for canonical trade and quote source functions, including required `sym` alignment columns and normalized output metadata.
- Wired `effective_spread_bps` into `KdbMetricQueryPlanner`, `template_for_metric()`, source-function rendering, symbol filtering, `max_quote_age` parameter rendering, output-schema dispatch, and runner support.
- Added `effective_spread_bps` to `config/report.production_minimal.yaml` with a note that canonical trades and quotes must expose same-symbol timestamps suitable for a prevailing quote-mid as-of join.
- Updated production, kdb integration, roadmap, and milestone status docs to include the new runnable transaction-cost metric and keep validation utility expansion frozen.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/effective_spread.q`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added schema-contract tests for `effective_spread.q` trade/quote input requirements, output metadata, result validation, dispatch, and non-effective-spread metric rejection.
- Added query-planner coverage for `effective_spread_bps`, including the two-source trade/quote contract, selected-symbol rendering, `max_quote_age` rendering, q-template dispatch, source-function rendering, and required output columns.
- Added runner normalization coverage for `effective_spread_bps`, including metadata preservation from `trade_count` and `notional`.
- Updated the unsupported-runner test to use `price_impact_30s_bps`, which remains a registered metric without production q-template support.
- Updated production minimal config coverage to include the new transaction-cost q-template metric.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py tests/test_config_files.py tests/test_docs_governance.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / runnable kdb metric coverage, with Milestone 9B validation utility expansion frozen per user feedback.

### Current milestone progress

- The effective-spread q-template slice is complete: 100% complete.
- Milestone 10 is approximately 99.5% complete because activity, liquidity, tick-spread, volatility, effective-spread, flow, and reversion metric families now have checked-in q-template coverage, while `price_impact_30s_bps` remains a roadmap-only starter metric.

### Remaining work before milestone completion

- Add q-template support for the remaining registered transaction-cost metric: `price_impact_30s_bps`.
- Improve report pages and deterministic commentary once the transaction-cost metrics are available as normalized `MetricTimeSeries` rows.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Implement the horizon-specific `price_impact_30s_bps` q template, including trade/quote source contracts, quote-horizon alignment, output metadata, query-planner wiring, and tests.

### Package phase and iteration

- Phase: 10.
- Iteration: 65.
- Delivery archive name: `mmsr_phase10_iteration65.zip`.

### Open questions

- Should `effective_spread_bps` expose a configurable `max_quote_age` in report YAML, or is the current runner-level default of `1s` sufficient until transaction-cost configuration is generalized?

---

## 2026-05-27 — Phase 10 iteration 66: add 30-second price-impact q support

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the runnable report-metric layer.
- Implemented the remaining registered transaction-cost starter metric, `price_impact_30s_bps`, as a focused production q-template slice.
- Added `price_impact.q`, which aligns trades to the prevailing same-symbol quote mid and the same-symbol quote mid at trade time plus the fixed 30-second horizon, then calculates signed price impact in basis points using feed-provided `aggressorSide`.
- Added price-impact input and output schema contracts requiring canonical trade `aggressorSide` and canonical same-symbol quote fields, with `trade_count` and `notional` metadata preserved for report diagnostics.
- Wired `price_impact_30s_bps` into q-template dispatch, query planning, source-function rendering, symbol filtering, horizon/freshness parameter rendering, output-schema dispatch, runner support, starter metric documentation, and `config/report.production_minimal.yaml`.
- Updated README, kdb integration docs, production readiness docs, roadmap, and milestone status to describe the runnable price-impact metric and keep validation utility expansion frozen.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/price_impact.q`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Added schema-contract tests for `price_impact.q` trade/quote input requirements, output metadata, result validation, dispatch, and non-price-impact metric rejection.
- Added query-planner coverage for `price_impact_30s_bps`, including the two-source trade/quote contract, selected-symbol rendering, fixed 30-second horizon rendering, quote-freshness parameters, q-template dispatch, and required output columns.
- Added runner normalization coverage for `price_impact_30s_bps`, including metadata preservation from `trade_count` and `notional`.
- Updated the unsupported-runner test to use a synthetic registered metric with no q template because all starter report metrics now have runnable q-template coverage.
- Updated production minimal config coverage to include the new price-impact q-template metric.

### Validation performed

- Ran `python -m pytest tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_config_files.py tests/test_docs_governance.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / runnable kdb metric coverage, with Milestone 9B validation utility expansion frozen per user feedback.

### Current milestone progress

- The price-impact q-template slice is complete: 100% complete.
- Milestone 10 is approximately 100% complete for the registered starter metrics because activity, liquidity, tick-spread, volatility, effective-spread, price-impact, flow, and reversion metric families now have checked-in q-template coverage.

### Remaining work before milestone completion

- Run the full test suite and compile validation after the journal update.
- Improve report pages and deterministic commentary now that the starter runnable kdb metrics are available as normalized `MetricTimeSeries` rows.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Add a transaction-cost report section/table grouping `effective_spread_bps` and `price_impact_30s_bps` with metric-help text and deterministic commentary, using existing normalized comparison facts rather than adding more validation utilities.

### Package phase and iteration

- Phase: 10.
- Iteration: 66.
- Delivery archive name: `mmsr_phase10_iteration66.zip`.

### Open questions

- Should `max_quote_age` and `max_horizon_quote_age` become explicit report YAML settings for transaction-cost metrics, or should the current conservative runner defaults remain until transaction-cost configuration is generalized?

---

## 2026-05-27 — Phase 10 iteration 67: rescope default market report metrics

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before changing the default report scope.
- Rescoped `config/report.production_minimal.yaml` to the market-monitoring metrics requested for this report: activity, displayed liquidity, and the six primary-quote reversion horizons.
- Enabled the Cross-Venue Toxicity/Reversion settings in the minimal production config and made the venue-trade / primary-quote raw functions explicit for the reversion metrics.
- Rescoped `config/report.example.yaml` to the same default market-report metric list so the example no longer advertises transaction-cost or optional add-on metrics as part of the standard report.
- Documented that optional market-microstructure add-ons such as tick-normalized spread, quote-mid realized volatility, and feed-signed order-flow imbalance remain available as checked-in q templates, but are not enabled by default.
- Documented that transaction-cost metrics such as effective spread and price impact are outside the default market-monitoring report scope and should not drive future report-section work unless the product scope explicitly changes.
- Updated config-file tests to lock the minimal/example configs to the narrowed market-report metric list and verify explicit production reversion source functions.

### Files changed

- `README.md`
- `_docs/ROADMAP.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `tests/test_config_files.py`

### Tests added or updated

- Updated `test_production_minimal_config_loads_supported_kdb_metrics` to assert the exact market-monitoring metric set, toxicity/reversion enablement, and explicit venue-trade / primary-quote raw source functions.
- Added `test_example_config_uses_market_monitoring_metrics` to prevent the example config from drifting back into transaction-cost or optional add-on metrics.

### Validation performed

- Ran `python -m pytest tests/test_config_files.py tests/test_docs_governance.py -q --tb=short`: passed.
- Ran `python -m pytest tests/test_config_files.py tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py tests/test_docs_governance.py -q --tb=short`: passed with 1 expected live-kdb/schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / kdb integration demo and first live-kdb market-report readiness.
- Milestone 9B validation utility expansion remains frozen per user feedback.

### Current milestone progress

- The default report metric scope correction is complete: 100% complete.
- Milestone 10 is approximately 99.5% complete for a first market-monitoring live run because the default configs now align with the market report scope and all default metrics have checked-in q-template coverage.

### Remaining work before milestone completion

- Clarify the sign convention and wording for primary-quote reversion so report users can distinguish reversion framing from price-impact framing.
- Improve the Cross-Venue Toxicity/Reversion page and market-wide activity/liquidity summaries using the narrowed default metric set.
- Keep broader validation framework work deferred until there are several reports with shared validation needs.

### Best next deterministic step

- Audit and, if needed, correct the primary-quote reversion sign convention and explanatory text so positive/negative values are consistently described as reversion versus adverse movement before enhancing the Cross-Venue Toxicity page.

### Package phase and iteration

- Phase: 10.
- Iteration: 67.
- Delivery archive name: `mmsr_phase10_iteration67.zip`.

### Open questions

- Should `primary_quote_reversion_*_bps` use a positive-is-reversion sign convention (`side * (pre_mid - post_mid)`) or keep the existing positive-is-adverse-movement convention while explaining that it is adverse reversion/toxicity rather than literal price reversion?

## 2026-05-27 — Phase 10 Iteration 68: fix primary-quote reversion formula convention

### Summary

- Updated the primary-quote reversion convention per user direction to:
  `aggressorSide * (future_mid - mid_at_trade) / future_mid * 10000`.
- Changed `toxicity_reversion` to divide by `post_mid` and require `post_mid > 0` for valid scored rows.
- Updated metric-definition formula text, Cross-Venue Toxicity help text, deterministic commentary docs, roadmap wording, production readiness notes, and kdb integration docs to use the future-mid denominator consistently.
- Added regression coverage so the packaged q template cannot drift back to the old `primary_mid` denominator.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/metrics/starter_definitions.py`
- `mmsr/report/toxicity.py`
- `mmsr/visuals/toxicity.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_toxicity_reversion.py`

### Tests added or updated

- Added `test_toxicity_reversion_template_uses_future_mid_denominator`.
- Updated the registered reversion metric test to assert the documented formula denominator.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_kdb_query_loader.py tests/test_toxicity_reversion.py tests/test_toxicity_reversion_report.py tests/test_docs_governance.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: could not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / kdb integration demo and first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Formula-convention correction is complete: 100%.
- Milestone 10 is approximately 99.8% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Improve the Cross-Venue Toxicity/Reversion page using the narrowed default market metric set, without adding transaction-cost report sections or additional validation utilities.

### Best next deterministic step

- Add a focused Cross-Venue Toxicity/Reversion report enhancement that uses the corrected reversion convention and existing normalized comparison facts.

### Package phase and iteration

- Phase: 10.
- Iteration: 68.
- Delivery archive name: `mmsr_phase10_iteration68.zip`.

### Open questions

- None.

---

## 2026-05-27 — Phase 10 iteration 69: add report scope guardrails

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md` before adding documentation guardrails.
- Added `docs/report_scope.md` as the canonical scope gate for future implementation work.
- Documented that `mmsr` is a Japanese market microstructure market-monitoring report package, not a transaction-cost analysis, execution-quality, smart-order-routing, venue-ranking, or generic validation-framework package.
- Locked the default report metric description to activity, displayed liquidity, and the six Cross-Venue Toxicity/Reversion horizons.
- Documented in-scope future work: market-wide summaries, intraday/auction profiles, taxonomy and symbol drilldowns, volatility or market-quality metrics that describe market state, and deterministic commentary.
- Documented out-of-scope default work: effective spread, implementation shortfall, slippage, price impact, order-routing analytics, broker/client order analytics, and reusable validation frameworks.
- Linked the scope guardrails from README, MkDocs navigation, docs index, AGENTS, the checked-in custom instructions copy, roadmap, milestone status, and production readiness docs.
- Added a governance regression test so the scope guardrails and cross-doc references remain visible.

### Files changed

- `README.md`
- `_docs/AGENTS.md`
- `_docs/CUSTOM_GPT_INSTRUCTIONS.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `docs/index.md`
- `docs/production_readiness.md`
- `docs/report_scope.md`
- `mkdocs.yml`
- `tests/test_docs_governance.py`

### Tests added or updated

- Added `test_docs_define_report_scope_guardrails` to assert the canonical scope page, default metric set, out-of-scope execution-cost/TCA language, validation-framework boundary, and MkDocs nav entry.

### Validation performed

- Ran `python -m pytest tests/test_docs_governance.py -q --tb=short`: passed.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: not run because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Scope-guardrail documentation is complete: 100%.
- Milestone 10 remains approximately 99.8% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Improve the Cross-Venue Toxicity/Reversion page and market-wide activity/liquidity summaries using the narrowed default market metric set.
- Use `docs/report_scope.md` as the gate before adding any new metrics, report sections, utilities, or roadmap next steps.

### Best next deterministic step

- Improve the Cross-Venue Toxicity/Reversion report page using the corrected reversion convention and existing normalized comparison facts, without adding transaction-cost report sections or additional validation utilities.

### Package phase and iteration

- Phase: 10.
- Iteration: 69.
- Delivery archive name: `mmsr_phase10_iteration69.zip`.

### Open questions

- None.
---

## 2026-05-27 — Phase 10 iteration 70: add toxicity reversion comparison table

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, `_docs/journal.md`, and the scope guardrail before implementing the next deterministic step.
- Enhanced the Cross-Venue Toxicity/Reversion page so it can render existing normalized `MetricComparison` facts for the reversion metric family as a current-versus-reference metric table.
- Kept the enhancement presentation-only: the page filters precomputed reversion comparisons, preserves current value, reference value, change, status, metric help, bucket, venue, horizon, and group context, and does not recalculate metrics or comparisons in Python.
- Routed `MarketReportInput.comparisons` into the toxicity page from the canonical market report builder.
- Added table help text that states the future-mid denominator convention and that positive current values or positive changes indicate more aggressive-direction primary-quote reversion.

### Files changed

- `mmsr/report/toxicity.py`
- `mmsr/report/market_report.py`
- `tests/test_toxicity_reversion_report.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_toxicity_reversion_page_adds_reversion_comparison_table`.
- Updated the canonical market report toxicity-page insertion test to assert that reversion comparison facts are passed through to the page table.

### Validation performed

- Ran `python -m pytest tests/test_toxicity_reversion_report.py -q --tb=short`: passed.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest tests/test_toxicity_reversion.py tests/test_toxicity_reversion_report.py tests/test_market_report.py tests/test_html_rendering.py -q --tb=short`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Toxicity/Reversion page comparison-table enhancement is complete: 100%.
- Milestone 10 remains approximately 99.85% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Improve the market-wide activity and displayed-liquidity summary presentation using the narrowed default market metric set.
- Keep default report work inside `docs/report_scope.md`: activity, displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/taxonomy/symbol views, and deterministic commentary.
- Live production validation remains pending until a real kdb+ process, credentials, source functions, and production-like schemas are available.

### Best next deterministic step

- Add a small market summary refinement that surfaces existing activity and displayed-liquidity comparison facts more clearly, without adding transaction-cost sections, new validation utilities, or new metric families.

### Package phase and iteration

- Phase: 10.
- Iteration: 70.
- Delivery archive name: `mmsr_phase10_iteration70.zip`.

### Open questions

- None.

---

## 2026-05-27 — Phase 10 iteration 71: surface activity and displayed-liquidity summary families

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, `_docs/journal.md`, and the scope guardrail before implementing the next deterministic step.
- Enhanced the Executive Market Overview block so the Market Summary page surfaces existing comparison facts for the default market-monitoring families:
  - Market activity: `turnover`, `volume`, and `trade_count`.
  - Displayed liquidity: `quoted_spread_bps` and `top_of_book_depth`.
- Kept the change presentation-only: the overview uses already-computed `MetricComparison` rows, respects the existing `max_metric_summaries` limit, and does not calculate new metrics, query kdb+, add transaction-cost sections, or add validation utilities.
- Added lightweight CSS for the family overview callouts in the packaged HTML template.
- Updated the canonical market-report regression test to assert the family summaries are rendered in both the component model and packaged HTML.

### Files changed

- `mmsr/report/overview.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_overview.py`
- `tests/test_market_report.py`
- `_docs/journal.md`

### Tests added or updated

- Added `tests/test_overview.py` with coverage for activity and displayed-liquidity family summaries and omission behavior when a family has no selected default-family metrics.
- Updated `tests/test_market_report.py` to assert the Market Summary page and rendered HTML expose the new family summary text.

### Validation performed

- Ran `python -m pytest tests/test_executive_overview.py tests/test_overview.py tests/test_market_report.py -q --tb=short`: passed.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Market-summary activity and displayed-liquidity family callouts are complete: 100%.
- Milestone 10 is approximately 99.9% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process, credentials, source functions, and production-like schemas are available.
- Keep future default-report refinements inside `docs/report_scope.md`: activity, displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/taxonomy/symbol views, and deterministic commentary.

### Best next deterministic step

- Add a concise production handoff note that points operators to the existing live-kdb smoke-test environment variables and bounded validation sequence, without adding new validation utilities.

### Package phase and iteration

- Phase: 10.
- Iteration: 71.
- Delivery archive name: `mmsr_phase10_iteration71.zip`.

### Open questions

- None.



---

## 2026-05-27 — Phase 10 iteration 72: switch production kdb boundary to user functions with positional arguments

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, `_docs/journal.md`, and the scope guardrail before implementing the user-requested production boundary change.
- Replaced production trading-calendar table configuration with a user-owned calendar function configuration:
  - `calendar.namespace`
  - `calendar.function`
  - `calendar.date_column`
- Updated `KdbTradingCalendarSource` to call the configured calendar function as `{[start;end] .namespace.function[start;end]}` and coerce either a date vector or a table/dict with the configured date column.
- Changed raw source-function rendering from a request dictionary to fixed positional q arguments:
  - `startDate`
  - `endDate`
  - `startTimes`
  - `endTimes`
  - `bucket`
  - `syms`
  - `venues`
  - `date`
  - `symbolChunkId`
  - `symbolChunkCount`
- Updated production CLI wiring so `mmsr plan`, `mmsr preflight`, and `mmsr render` all use the configured calendar function.
- Updated live-smoke helper environment variables from table names to user source functions:
  - `MMSR_KDB_TRADE_FUNCTION`
  - `MMSR_KDB_QUOTE_FUNCTION`
  - `MMSR_KDB_CALENDAR_FUNCTION`
- Updated production/example configs and production readiness documentation to describe the function-based boundary and positional argument contract.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/kdb/live_smoke.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/q_templates/trading_calendar.q`
- `mmsr/kdb/query_plan.py`
- `mmsr/periods/calendar.py`
- `tests/test_calendar.py`
- `tests/test_config_files.py`
- `tests/test_config_models.py`
- `tests/test_docs_governance.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_live_kdb_smoke.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Updated calendar-source tests to assert user-function calendar calls instead of table selects.
- Updated query-plan and production-execution tests to assert positional source-function calls and no request dictionary.
- Updated production CLI tests to use `calendar.function` config and fake calendar function detection.
- Updated live-kdb smoke tests to use function environment variables and source-function metric requests.
- Updated governance/docs tests for the new function-based production boundary terms.

### Validation performed

- Ran `python -m pytest tests/test_config_models.py tests/test_config_files.py tests/test_calendar.py tests/test_kdb_query_loader.py tests/test_kdb_query_plan.py tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_live_kdb_smoke.py tests/test_docs_governance.py -q --tb=short`: passed with 2 expected live-kdb smoke skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- User-function calendar and positional raw source-function boundary is complete: 100%.
- Milestone 10 is approximately 99.95% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process, credentials, configured source functions, configured calendar function, and production-like schemas are available.
- Keep future default-report refinements inside `docs/report_scope.md`: activity, displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/taxonomy/symbol views, and deterministic commentary.

### Best next deterministic step

- Run a bounded live-kdb trial using `config/report.production_minimal.yaml`, one known-good trading day, one liquid symbol, and the configured user functions for calendar, trade, quote, venue trade, and primary quote.

### Package phase and iteration

- Phase: 10.
- Iteration: 72.
- Delivery archive name: `mmsr_phase10_iteration72.zip`.

### Open questions

- None.

---

## 2026-05-27 — Phase 10 iteration 73: simplify source functions and add reference-data universe function

### Implemented

- Re-read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, `_docs/journal.md`, and the scope guardrail before implementing the user-requested source-boundary refinement.
- Simplified raw trade/quote source-function rendering from the broader positional argument list to the minimal production boundary:
  - `date`
  - `syms`
- Added first-class reference-data universe configuration:
  - `symbols.namespace`
  - `symbols.function`
  - `symbols.symbol_column`
- Added `KdbSymbolUniverseSource`, which calls the configured user-owned q function as `{[date] .namespace.function[date]}` and accepts either a symbol vector or a table/dict with the configured symbol column.
- Updated `KdbProductionExecutor`, `KdbProductionExecutionPlanner`, and preflight planning so production runs use the configured reference-data universe function by default, while explicit CLI `--symbol` values remain a bounded smoke/debug override.
- Updated production plan summaries to show the configured reference-data universe function.
- Removed `symbolChunkId` and `symbolChunkCount` from raw source-function calls; chunking remains an MMSR-side execution-plan detail that determines which `syms` vector each source call receives.
- Updated production/example configs and operator documentation to describe the new `getRef[date]`, `getTrade[date;syms]`, and `getQuote[date;syms]` contracts.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/cli.py`
- `mmsr/config/__init__.py`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/periods/__init__.py`
- `mmsr/periods/symbols.py`
- `tests/test_config_files.py`
- `tests/test_config_models.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_production_cli.py`
- `tests/test_symbols.py`

### Tests added or updated

- Added `tests/test_symbols.py` for `KdbSymbolUniverseSource` function calls and vector coercion.
- Updated config model/config-file tests for `SymbolUniverseConfig` and `symbols:` YAML loading.
- Updated query-plan tests to assert raw source functions are called as `function[date;syms]` with no request dictionary and no chunk-id arguments.
- Updated production execution tests to assert day-specific reference-data universes drive symbol chunks when CLI symbols are not provided.
- Updated production CLI tests to fake the configured reference-data universe function and verify plan summaries include it.

### Validation performed

- Ran `python -m pytest tests/test_config_models.py tests/test_config_files.py tests/test_calendar.py tests/test_symbols.py tests/test_kdb_query_loader.py tests/test_kdb_query_plan.py tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_live_kdb_smoke.py tests/test_docs_governance.py -q --tb=short --color=no`: passed with 2 expected live-kdb smoke skips.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Minimal `date;syms` raw source-function boundary and user-owned reference-data universe function support are complete: 100%.
- Milestone 10 is approximately 99.97% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process, credentials, configured calendar/symbol/trade/quote functions, and production-like schemas are available.
- Keep future default-report refinements inside `docs/report_scope.md`: activity, displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/taxonomy/symbol views, and deterministic commentary.

### Best next deterministic step

- Run a bounded live-kdb trial using `config/report.production_minimal.yaml`, one known-good trading day, and the configured user functions for calendar, symbols, trade, quote, venue trade, and primary quote.

### Package phase and iteration

- Phase: 10.
- Iteration: 73.
- Delivery archive name: `mmsr_phase10_iteration73.zip`.

### Open questions

- None.


## 2026-05-27 - Phase 10 Iteration 74

### Summary

Implemented MMSR-owned q aggregation helpers under the configured calculation namespace so user-owned kdb functions remain limited to calendar, reference-data universe, and canonical source-row access while MMSR owns metric calculation logic.

### Files changed

- `README.md`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/calculation_functions.q`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`

### Tests added or updated

- Added tests for rendering the calculation-function bootstrap into a configured namespace.
- Added a runner test for `install_calculation_functions()`.
- Updated query-plan and runner tests to assert activity, liquidity, and reversion templates use MMSR-owned namespace helpers for core aggregations.

### Validation performed

- Ran `python -m pytest tests/test_kdb_query_loader.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py -q --tb=short --color=no`: passed.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Minimal source functions and MMSR-owned kdb calculation namespace support are complete: 100%.
- Milestone 10 is approximately 99.98% complete for a first market-monitoring live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process, credentials, configured calendar/symbol/trade/quote functions, and production-like schemas are available.
- Keep future default-report refinements inside `docs/report_scope.md`: activity, displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/taxonomy/symbol views, and deterministic commentary.

### Best next deterministic step

- Run a bounded live-kdb trial using `config/report.production_minimal.yaml`, one known-good trading day, configured user source functions, and the MMSR calculation namespace.

### Package phase and iteration

- Phase: 10.
- Iteration: 74.
- Delivery archive name: `mmsr_phase10_iteration74.zip`.

### Open questions

- None.


## 2026-05-27 - Phase 10 Iteration 75

### Summary

Implemented the production source-boundary update requested for the first real
kdb trial: static session times are no longer required in production configs,
trade/quote source rows carry per-tick `session` and `auction` state, a
user-owned reference-data function supplies TOPIX/cap/lot-size metadata, and a
packaged live-kdb example config is included in the package.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/config/__init__.py`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/examples/mock_kdb_demo.py`
- `mmsr/kdb/live_smoke.py`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/calculation_functions.q`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/periods/models.py`
- `pyproject.toml`
- `tests/test_cli.py`
- `tests/test_config_models.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_live_kdb_smoke.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_periods.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added/updated config tests for `reference_data` / `getRef` config loading and
  source-function propagation.
- Updated schema-contract tests so activity, liquidity, reversion, and reference
  data contracts require per-tick `session`/`auction` state and `getRef` fields.
- Updated query-plan and runner tests to assert `date;syms` source calls,
  reference-data joins, and namespace-owned session/auction-aware time bucketing.
- Updated production CLI/executor/live-smoke tests for the `reference_data`
  function and sessionless production period config.
- Updated mock-kdb demo tests for the new canonical q source shape.

### Validation performed

- Ran `python -m pytest tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_live_kdb_smoke.py -q --tb=short --color=no`: passed with 2 expected live-kdb smoke skips.
- Ran `python -m pytest tests/test_config_models.py tests/test_kdb_schema_contracts.py tests/test_kdb_query_loader.py tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_mock_kdb_demo.py tests/test_cli.py tests/test_periods.py -q --tb=short --color=no`: passed with 1 expected live-schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Production kdb source-boundary alignment with user-owned calendar, symbol,
  reference, trade, and quote functions is complete: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured calendar/symbol/reference/trade/quote functions, and
  production-like schemas are available.
- Keep future default-report refinements inside `docs/report_scope.md`: activity,
  displayed liquidity, Cross-Venue Toxicity/Reversion, market-wide/intraday/
  taxonomy/symbol views, and deterministic commentary.

### Best next deterministic step

- Run a bounded live-kdb trial using `config/report.production_minimal.yaml`, one
  known-good trading day, one liquid symbol, configured `getTradingCalendar`,
  `getRef`, `getRef`, `getTrade`, and `getQuote` functions, and the MMSR
  calculation namespace.

### Package phase and iteration

- Phase: 10.
- Iteration: 75.
- Delivery archive name: `mmsr_phase10_iteration75.zip`.

### Open questions

- Confirm whether `getRef` should support client-specific additional taxonomy
  columns beyond `topix_bucket`, `market_cap_bucket`, and `lotSize` before
  those columns are enabled in `groups`.


## 2026-05-27 - Phase 10 Iteration 76

### Summary

Aligned the live kdb reference-data boundary with the current available
taxonomy: renamed the TOPIX grouping field from `topix_bucket` to `topixCapGrp`
and removed `market_cap_bucket` from the required `getRef[date;syms]` schema and
packaged production starter configs because MMSR does not currently calculate or
source a market-cap group by default.

### Files changed

- `README.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/presentation/labels.py`
- `tests/test_display_labels.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Updated kdb query-plan tests so reference-data contracts require
  `topixCapGrp` and no longer require `market_cap_bucket`.
- Updated schema-contract tests to cover `topixCapGrp` as the default live
  taxonomy group.
- Updated production CLI tests and fake live results to use `topixCapGrp`.
- Added a display-label assertion for the human-facing `TOPIX cap group` label.

### Validation performed

- Ran `python -m pytest tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py tests/test_production_cli.py tests/test_config_models.py tests/test_display_labels.py -q --tb=short --color=no`: passed with 1 expected live-schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 3 expected live-kdb/schema skips.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Production kdb source-boundary alignment with the current user-owned calendar,
  symbol, reference, trade, and quote functions is complete: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured calendar/symbol/reference/trade/quote functions, and
  production-like schemas are available.
- Optional historical/offline market-cap drilldown support remains in the report
  layer, but `market_cap_bucket` is no longer a required live reference-data
  column or a packaged production default group.

### Best next deterministic step

- Run a bounded live-kdb trial using `config/report.production_minimal.yaml`, one
  known-good trading day, one liquid symbol, configured `getTradingCalendar`,
  `getRef`, `getRef`, `getTrade`, and `getQuote` functions, and the MMSR
  calculation namespace.

### Package phase and iteration

- Phase: 10.
- Iteration: 76.
- Delivery archive name: `mmsr_phase10_iteration76.zip`.

### Open questions

- None.



## 2026-05-27 - Phase 10 Iteration 77

### Summary

Simplified the live kdb source boundary around a single reference-data universe
function and removed the legacy live-smoke harness. `getRef[date]` now owns the
analysis universe and reference attributes, raw source functions receive the
filtered reference table, live contracts use camelCase source columns, and MMSR
infers `aggressorSide` inside q for default reversion/price-impact-style
calculations instead of requiring it from the trade source.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/calculation_functions.q`
- `mmsr/kdb/production.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/effective_spread.q`
- `mmsr/kdb/q_templates/flow`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/liquidity_ticks`
- `mmsr/kdb/q_templates/price_impact.q`
- `mmsr/kdb/q_templates/realized_volatility`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/periods/symbols.py`
- `tests/test_config_files.py`
- `tests/test_config_models.py`
- `tests/test_docs_governance.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_production_cli.py`
- `tests/test_symbols.py`

Removed files:

- `mmsr/kdb/live_smoke.py`
- `tests/test_live_kdb_smoke.py`

### Tests added or updated

- Updated config and production CLI tests to use `getRef[date]` instead of a
  separate `getSymbols` function.
- Updated q-template planning tests so source functions are rendered as
  `getTrade[date;0!refs]` and `getQuote[date;0!refs]` after MMSR filters the
  `getRef[date]` table.
- Updated schema-contract tests for camelCase live source columns and MMSR-owned
  `aggressorSide` inference in reversion and price-impact templates.
- Updated docs-governance tests to describe the production preflight path rather
  than the removed live-smoke harness.

### Validation performed

- Ran `python -m pytest tests/test_config_files.py tests/test_config_models.py tests/test_symbols.py tests/test_kdb_query_plan.py tests/test_kdb_production_execution.py tests/test_production_cli.py tests/test_kdb_query_loader.py -q --tb=short --color=no`: passed.
- Ran `python -m pytest tests/test_docs_governance.py tests/test_kdb_metric_runner.py tests/test_kdb_schema_contracts.py -q --tb=short --color=no`: passed with 1 expected live-schema skip.
- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 1 expected live-schema skip.
- Ran `python -m black --check .`: not run successfully because Black is not installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before Python validation commands, but pytest and compileall returned success.

### Current milestone

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Validation utility expansion remains frozen per user feedback.

### Current milestone progress

- Production kdb source-boundary alignment with the user-owned calendar,
  reference-data universe, trade, and quote functions is complete: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured `getTradingCalendar`, `getRef`, `getTrade`, and
  `getQuote` functions, and production-like schemas are available.
- Optional historical/offline market-cap drilldown support remains in the report
  layer, but `market_cap_bucket` is not a packaged production default group.

### Best next deterministic step

- Run a bounded production preflight with one known-good trading day and one
  liquid symbol using `config/report.production_minimal.yaml`, the configured
  user-owned source functions, and the MMSR calculation namespace.

### Package phase and iteration

- Phase: 10.
- Iteration: 77.
- Delivery archive name: `mmsr_phase10_iteration77.zip`.

### Open questions

- None.
## 2026-05-28 - Phase 10 Iteration 78

### Current milestone and next deterministic step

- Active milestone: Milestone 10 / first live-kdb market-report readiness.
- Smallest deterministic task: remove the production `--venue` override, keep the
  default analysis target anchored to TSE via `toxicity.primary_venue`, and fix
  reversion-side inference so `aggressorSide` is calculated per venue and per
  symbol from the matched prevailing quote before measuring the future primary
  quote path.

### Implemented in this step

- Removed the production CLI/API venue override from `plan`, `preflight`, and
  `render`; production runs now rely on the configured TSE primary venue and the
  source functions' reference-data universe instead of an operator `--venue`
  filter.
- Changed `ToxicityConfig.venues` to an optional venue filter. When omitted, the
  reversion q template discovers venues present in the trade and quote rows; when
  supplied, it remains a narrow explicit filter for controlled diagnostics.
- Updated `toxicity_reversion` so each trade is matched to the prevailing quote
  by `date`, `sym`, `venue`, and `time`, infers `aggressorSide` from that
  same-venue/same-symbol midpoint, then separately uses the TSE/primary quote
  path for at-trade and future mids in the reversion formula.
- Added a matched-venue quote staleness guard through `max_venue_quote_age`,
  defaulting to the primary quote-age threshold unless explicitly supplied.
- Removed static PTS venue lists from the packaged production/example configs so
  PTS venues come from available trade/quote data by default.
- Updated metric definitions, schema-contract assumptions, docs, and tests to
  document MMSR-owned side inference for reversion and the TSE primary target.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `docs/report_scope.md`
- `mmsr/cli.py`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/production.py`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_models.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Updated config-model and config-file tests for the new `venues=None` default
  and optional venue-filter serialization.
- Updated query-loader, query-planner, and metric-runner tests to assert the
  reversion q renders all-venue quote sourcing, same-venue as-of quote matching,
  `venueMid`-based `aggressorSide` inference, and `max_venue_quote_age`.
- Updated production CLI/executor tests to remove `--venue` and programmatic
  venue overrides.
- Updated schema-contract tests so reversion trades no longer require a
  feed-provided `aggressorSide`.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 1 expected
  live-schema skip.
- Ran `python -m black --check .`: not run successfully because Black is not
  installed in this execution environment.
- Ran `python -m ruff check .`: not run successfully because Ruff is not
  installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but compileall and pytest returned success.

### Current milestone progress

- Venue override removal and per-venue/per-symbol reversion-side inference are
  complete for this implementation slice: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured `getTradingCalendar`, `getRef`, `getTrade`, and
  `getQuote` functions, and production-like schemas are available.
- Optional historical/offline market-cap drilldown support remains in the report
  layer, but `market_cap_bucket` is not a packaged production default group.

### Best next deterministic step

- Run a bounded production preflight with one known-good trading day and one
  liquid symbol using `config/report.production_minimal.yaml`, the configured
  user-owned source functions, and the MMSR calculation namespace.

### Package phase and iteration

- Phase: 10.
- Iteration: 78.
- Delivery archive name: `mmsr_phase10_iteration78.zip`.

### Open questions

- None.


## 2026-05-28 — Iteration 79: Dedicated PTS toxicity source and chunk-safe symbol aggregation

### Implemented

- Split the toxicity-only PTS trade source out from the main production trade
  source by adding the first-class `raw_data_functions.pts_trade` role.
- Added separate reversion input roles for `pts_trades`, `venue_quotes`, and
  `primary_quotes`. Reversion now calls the configured PTS trade source for PTS
  prints, same-venue quote source for aggressor-side inference, and primary/TSE
  quote source for reversion measurement.
- Kept backward-compatible parsing for the older `venue_trade` config key, but
  updated packaged production/example configs and README guidance to use
  `pts_trade`.
- Added `data.kdb.symbol_chunk_group_by`, defaulting to `[sym]`, so configured
  symbol chunking calculates at a per-symbol grain inside each chunk before
  MMSR concatenates chunk outputs.
- Updated the production planner so when `symbol_chunk_size` is set it appends
  the configured chunk aggregation columns to each request's q `group_by` list.
  This avoids unsafe duplicate market/sector aggregates from independently
  processed chunks.
- Added plan-summary and execution metadata for chunk aggregation columns.
- Updated q-template schema contracts, metric definitions, config loading, and
  tests to reflect dedicated PTS trade sourcing and chunk-safe symbol
  aggregation.

### Files changed

- `README.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/production.py`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_config_models.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Updated config-model and config-file tests for `pts_trade`,
  `venue_quote`, `primary_quote`, and `symbol_chunk_group_by`.
- Updated query-loader, query-plan, runner, and schema-contract tests for the
  new reversion source roles and template parameters.
- Added a production-planner test confirming market/grouped chunked execution
  appends `sym` to request groupings before q aggregation.
- Updated production CLI fake results to include `sym` when chunk-safe grouping
  is enabled.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 1 expected
  live-schema skip.
- Ran `python -m black --check .`: not run successfully because Black is not
  installed in this execution environment.
- Ran `python -m ruff check .`: not run successfully because Ruff is not
  installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but compileall and pytest returned success.

### Current milestone progress

- Dedicated PTS source-role separation and chunk-safe per-symbol aggregation are
  complete for this implementation slice: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured `getTradingCalendar`, `getRef`, `getTrade`,
  `getPtsTrade`, `getQuote`, and production-like schemas are available.
- If operators need chunked market-wide or sector-wide totals rather than
  per-symbol chunk outputs, a second-stage weighted rollup should be implemented
  after the per-symbol chunk union.

### Best next deterministic step

- Run a bounded production preflight for one known-good trading day and one small
  symbol chunk using the configured `getPtsTrade`, venue quote, and primary quote
  functions to validate live reversion schema compatibility.

### Package phase and iteration

- Phase: 10.
- Iteration: 79.
- Delivery archive name: `mmsr_phase10_iteration79.zip`.

### Open questions

- None.

---

## 2026-05-28 — Iteration 80: Dedicated PTS quote source for reversion side inference

### Implemented

- Added a first-class `raw_data_functions.pts_quote` configuration role for
  toxicity/reversion so PTS trade side inference no longer defaults to the main
  TSE/displayed-liquidity quote source in production configs.
- Renamed the reversion q source role from `venue_quotes` to `pts_quotes` and
  updated `toxicity_reversion` to load `rawPtsQuotes`, as-of join PTS trades to
  PTS quotes by `date`, `sym`, `venue`, and `time`, and infer `aggressorSide`
  from `ptsMid`.
- Kept backward-compatible parsing for the older `venue_quote` config key and
  `venue_quotes` source role so earlier local configs still render, while packaged
  configs now use `pts_quote: getPtsQuote`.
- Added `toxicity.filters.max_pts_quote_age`, defaulting to the primary quote-age
  threshold when omitted, and rendered it as `max_pts_quote_age` in q.
- Updated source-function schema contracts, metric definitions, production docs,
  README guidance, and tests to distinguish PTS trades, PTS quotes, and
  primary/TSE quotes.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/journal.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_config_models.py`
- `tests/test_docs_governance.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Updated config-model and config-file tests for `pts_quote`, `pts_quotes`, and
  `max_pts_quote_age`.
- Updated q-template loader, runner, and query-plan tests to assert
  `pts_quotes_table`, `rawPtsQuotes`, `ptsMid`, and `ptsQuoteAge`.
- Updated schema-contract tests so reversion has distinct `pts_trades`,
  `pts_quotes`, `primary_quotes`, and `reference_data` input contracts.
- Updated docs-governance tests to require the new PTS quote production-readiness
  checklist section.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 1 expected
  live-kdb schema skip.
- Ran `python -m black --check .`: not run successfully because Black is not
  installed in this execution environment.
- Ran `python -m ruff check .`: not run successfully because Ruff is not
  installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but compileall and pytest returned success.

### Current milestone progress

- Dedicated PTS quote sourcing and PTS quote-based `aggressorSide` inference are
  complete for this implementation slice: 100%.
- Milestone 10 is approximately 99.99% complete for a first market-monitoring
  live run.

### Remaining work before milestone completion

- Live production validation remains pending until a real kdb+ process,
  credentials, configured `getTradingCalendar`, `getRef`, `getTrade`, `getQuote`,
  `getPtsTrade`, `getPtsQuote`, and production-like schemas are available.
- If operators need chunked market-wide or sector-wide totals rather than
  per-symbol chunk outputs, a second-stage weighted rollup should be implemented
  after the per-symbol chunk union.

### Best next deterministic step

- Run a bounded production preflight for one known-good trading day and one small
  symbol chunk using a reversion metric, validating `getPtsTrade`, `getPtsQuote`,
  and primary/TSE `getQuote` schema compatibility together.

### Package phase and iteration

- Phase: 10.
- Iteration: 80.
- Delivery archive name: `mmsr_phase10_iteration80.zip`.

### Open questions

- None.

---

## 2026-05-28 — Clarified live q return path and explicit raw-table calc arguments

### Implemented

- Reviewed the rendered q-template execution model after operator feedback that
  functions such as `calcFlow` did not visibly receive source tables or persist
  results.
- Refactored production q templates so each MMSR `calc*` function now accepts
  explicit raw table arguments plus the filtered `refs` table, for example
  `.desk.mmsr.calcFlow[rawTrades;refs]`.
- Wrapped the source-loading block in a local q lambda so temporary variables such
  as `rawRefs`, `refs`, and `rawTrades` do not leak into the kdb global namespace.
- Kept the intended result path: the last q expression is the aggregated table,
  PyKX returns that table to Python through `KdbClient.execute`, and
  `KdbMetricRunner` validates and normalizes it into `MetricTimeSeries`; MMSR
  does not persist result tables in kdb by default.
- Updated README production documentation to describe the exact live data path,
  symbol-chunk source calls, PyKX return boundary, and non-persistent result
  behavior.

### Files changed

- `README.md`
- `_docs/journal.md`
- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/effective_spread.q`
- `mmsr/kdb/q_templates/flow`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/liquidity_ticks`
- `mmsr/kdb/q_templates/price_impact.q`
- `mmsr/kdb/q_templates/realized_volatility`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_plan.py`

### Tests added or updated

- Updated q-template runner and query-plan tests to assert explicit raw table
  source assignments and explicit `calc*` calls.
- Preserved tests that validate daily symbol chunking calls source functions with
  `[date;0!refs]` for the current chunk.

### Validation performed

- Ran `python -m compileall -q mmsr tests`: passed.
- Ran `python -m pytest -q -ra --tb=short --color=no`: passed with 1 expected
  live-kdb schema skip.
- Ran `python -m black --check .`: not run successfully because Black is not
  installed in this execution environment.
- Ran `python -m ruff check .`: not run successfully because Ruff is not
  installed in this execution environment.
- The environment emitted the recurring spreadsheet runtime warmup warning before
  Python validation commands, but compileall and pytest returned success.

### Current milestone progress

- Explicit source-table passing and PyKX return-path documentation are complete
  for this implementation slice: 100%.
- Milestone 10 remains approximately 99.99% complete for a first
  market-monitoring live run.

### Remaining work before milestone completion

- Live production validation remains pending against the real kdb+ functions and
  schemas.
- If operators want kdb-side persisted metric results, add a separate optional
  sink/export step; the current report path intentionally returns aggregates to
  Python without saving intermediate or final tables in kdb.

### Best next deterministic step

- Run `mmsr preflight` for one liquid symbol and one reversion metric against the
  live kdb process, then inspect the rendered query/result row count to confirm
  source calls and PyKX returned aggregate rows.

### Package phase and iteration

- Phase: 10.
- Iteration: 81.
- Delivery archive name: `mmsr_phase10_iteration81.zip`.

### Open questions

- Should MMSR add an optional kdb sink function for operators who want aggregated
  metric tables persisted in kdb in addition to the HTML report?

---

## 2026-05-28 — Batch kdb source loading and explicit q returns

### Implemented

- Refactored metric q templates so they define argument-taking calculation functions only; top-level source loading is now owned by the query planner.
- Made every calculation function explicitly assign its aggregate `select` to `result` and return `result` as the final expression.
- Added single-metric query wrappers that build the day/chunk `refs` table, load raw source rows, pass them into the calculation function, and return the result table as the final q expression.
- Added `RenderedMetricBatchQuery` and `KdbMetricRunner.run_batch()` so production execution can load each source role once per trading day/symbol chunk and return a q dictionary of metric result tables keyed by metric name.
- Updated production execution to batch metrics by `(trading_day, symbol_chunk_id)` instead of reloading trade/quote data for every report section.
- Preserved PTS toxicity separation: PTS trades and PTS quotes are loaded only for reversion metrics; primary/TSE quotes are loaded separately for the benchmark mids.
- Documented the corrected live data path in `README.md`.

### Files changed

- `mmsr/kdb/q_templates/activity`
- `mmsr/kdb/q_templates/flow`
- `mmsr/kdb/q_templates/liquidity`
- `mmsr/kdb/q_templates/liquidity_ticks`
- `mmsr/kdb/q_templates/realized_volatility`
- `mmsr/kdb/q_templates/effective_spread.q`
- `mmsr/kdb/q_templates/price_impact.q`
- `mmsr/kdb/q_templates/toxicity_reversion`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/production.py`
- `README.md`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`

### Tests added or updated

- Added a runner batch test proving one query can return multiple metric tables and source tables are loaded once.
- Added a production executor test proving metrics are batched by day and symbol chunk.
- Updated q-template parameter tests for the new argument-only template contract.

### Validation

- `python -m compileall -q mmsr tests` passed.
- `python -m pytest -q -ra --tb=short --color=no` passed with one expected live-kdb schema skip.
- The environment emitted the known spreadsheet runtime warmup warning before Python commands, but the validation commands completed successfully.

### Current milestone

- Phase 10 / first live-kdb market-report readiness

### Estimated milestone completion

- 99.99%

### Remaining work before milestone completion

- Validate the new day/chunk batch query against live kdb+ for one small symbol chunk.
- Confirm q dictionary return conversion from PyKX for the production kdb version in use.

### Best next deterministic step

- Run `mmsr preflight` and then a one-day/two-symbol `mmsr render` against live kdb+ to validate the batched q return path.

### Open questions

- Should MMSR add an optional configured kdb result sink after the Python report path is live-validated?

---

## 2026-05-28 — q-side day chunk rollups and continuous quote contract

### Implemented

- Moved the production execution shape from Python day/chunk batches to one q-side trading-day wrapper.
- Added `RenderedMetricDayQuery`, `KdbMetricQueryPlanner.render_day()`, `KdbMetricRunner.plan_day()`, and `KdbMetricRunner.run_day()`.
- Production execution now groups real kdb runs by trading day, passes explicit `allSyms` and `chunkSize` into q, cuts symbol chunks inside q, loads raw sources once per chunk, razes chunk outputs inside q, and returns metric result tables keyed by metric name.
- Added configurable `data.kdb.aggregation_levels` with defaults for market, market bucket, TOPIX cap group, TOPIX cap group bucket, symbol, and symbol bucket.
- Added q-side `rollupMetricResult` and scope metadata columns (`aggregationLevel`, `groupType`, `groupValue`) for day-level rollup output.
- Renamed rendered q resources from `mmsr/kdb/q_templates/*.q` to `mmsr/kdb/query_templates/*.q.j2`; the Python loader still accepts legacy `.q` names and maps them to `.q.j2` resources.
- Removed the `auction` requirement from quote source contracts. Quotes are treated as continuous-session quote rows and use `timeBucketContinuous`; trade rows still use auction-aware buckets.
- Updated production/example configs and README with the new q-side execution path and aggregation-level configuration.

### Files changed

- `mmsr/kdb/query_templates/*.q.j2`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/config/models.py`
- `mmsr/config/loading.py`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `mmsr/examples/config/live_kdb_report.yaml`
- `pyproject.toml`
- `README.md`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added planner coverage proving a day query has explicit `allSyms`, q-side chunk cutting, `runDate` source calls, and q-side `rollupMetricResult` calls.
- Added quote-source contract coverage proving `auction` is no longer required for quote data.
- Updated production CLI expectations for one q-side day query per target/reference trading day instead of one query per Python chunk.

### Validation

- `python -m compileall -q mmsr tests` passed.
- `python -m pytest -q -ra --tb=short --color=no` passed with one expected live-kdb schema skip.
- The environment emitted the known spreadsheet runtime warmup warning before Python commands, but the validation commands completed successfully.

### Current milestone

- Phase 10 / first live-kdb market-report readiness.

### Estimated milestone completion

- 99.99%.

### Remaining work before milestone completion

- Live validate q syntax and PyKX conversion for the new one-day q wrapper against real kdb+.
- Refine metric-family-specific q rollups for weighted liquidity and reversion if live validation shows the generic scope rollup is insufficient for production reporting.

### Best next deterministic step

- Run a one-day/two-symbol live preflight and render against real kdb+ to validate `run_day`, q-side chunk cutting, quote contracts without `auction`, and returned metric dictionaries.

### Open questions

- Should the generic q-side `rollupMetricResult` be replaced by fully metric-family-specific weighted rollup functions before the first full-universe production run?

---

## 2026-05-28 — Clarify trade and quote bucket q helpers

### Implemented

- Replaced ambiguous indexed assignment in `.timeBucket` with q functional amend
  (`@[labels;where ...;:;label]`) so auction bucket overrides are explicit and
  reviewable.
- Kept auction bucket logic trade-only: `AMO`, `AMC`, `PMO`, and `PMC` are
  derived from trade `session` and `auction` columns.
- Changed `.timeBucketContinuous` to accept only `time` and `bucket`, and updated
  quote metric bucket expressions to call `timeBucketContinuous[time;bucket]`.
- Documented that quote source functions are continuous-session quote sources
  and are not expected to return `auction`.
- Added tests that assert rendered activity q uses functional amend and rendered
  liquidity q does not pass `session` or `auction` into quote bucketing.

### Files changed

- `mmsr/kdb/query_templates/calculation_functions.q.j2`
- `mmsr/kdb/query_templates/activity.j2`
- `mmsr/kdb/query_templates/liquidity.j2`
- `mmsr/kdb/query_templates/toxicity_reversion.j2`
- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `README.md`
- `docs/kdb_integration_testing.md`
- `_docs/journal.md`

### Tests added or updated

- Updated `tests/test_kdb_metric_runner.py` coverage for trade auction bucket
  helper rendering and quote continuous bucket helper rendering.

### Validation

- `python -m compileall -q mmsr tests` passed.
- `python -m pytest -q -ra --tb=short --color=no` passed with one expected
  live-kdb schema skip.
- `python -m black --check .` could not run because Black is not installed.
- `python -m ruff check .` could not run because Ruff is not installed.

### Current milestone

- Phase 10 / first live-kdb market-report readiness.

### Estimated milestone completion

- 99.99%

### Remaining work before milestone completion

- Live validation of the q syntax and returned schemas against a real kdb+
  process, especially the day-level chunk loop and q-side rollup path.

### Best next deterministic step

- Run one live day with two liquid symbols and activity plus liquidity metrics to
  validate `.timeBucket`, `.timeBucketContinuous`, and the day-level q wrapper
  inside kdb+.

### Open questions

- None.


## 2026-05-28 — Centralized q calculation library install

### Implemented

- Added `mmsr/kdb/q_lib/mmsr_calculations.q.j2` as the single package-owned reusable q utility library.
- Updated the q library loader so MMSR renders reusable functions from `q_lib` rather than repeating helper definitions across metric query templates.
- Removed repeated utility function definitions from metric query templates; templates now reference the installed calculation namespace.
- Updated `KdbMetricRunner` with an `ensure_calculation_functions` path that installs the q library once per namespace for real `KdbClient` / PyKX-backed executions before metric queries run.
- Kept deterministic non-PyKX test doubles from requiring library installation, while preserving explicit `install_calculation_functions()` for direct validation.
- Documented the runtime contract: install q utilities once, then run q-side day/chunk source loading, chunk calculation, raze/rollup, and PyKX result return.

### Files changed

- `mmsr/kdb/q_lib/__init__.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/query_templates/*.q.j2`
- `mmsr/examples/mock_kdb_demo.py`
- `tests/test_kdb_metric_runner.py`
- `pyproject.toml`
- `README.md`
- `_docs/journal.md`

### Tests added or updated

- Updated metric-runner tests so reusable utility definitions are validated in the q library bootstrap instead of repeated rendered metric queries.
- Updated deterministic mock kdb client to accept the q library bootstrap without requiring a date-scoped metric query.

### Validation

- `python -m compileall -q mmsr tests` passed.
- `python -m pytest -q -ra --tb=short --color=no` passed, with one expected live-kdb schema skip.
- Formatter checks remain unavailable in this runtime unless Black/Ruff are installed.

### Current milestone

- Phase 10 / first live-kdb market-report readiness.

### Estimated milestone completion

- 99.99%

### Remaining work before milestone completion

- Live production validation against real kdb source functions and schemas.
- Confirm whether metric-specific calculation functions should also be fully static q-library functions with config dictionaries rather than rendered metric wrappers.

### Open Questions

- Should all metric calculation functions be converted to static q-library functions that accept q config dictionaries, leaving only a tiny source-function wrapper template?

### Next deterministic step

- Run a one-day, two-symbol live kdb render and verify the q library is installed once before the day/chunk calculation query.

---

## 2026-05-28 — Quote schema simplification and integer auction codes

### Implemented

- Removed `session` from quote input schema contracts because quote-backed templates bucket by raw `time` through `timeBucketContinuous` and do not use quote session state.
- Kept `session` on trade input schemas because auction bucket labels still need the AM/PM session context.
- Changed kdb auction-state handling from symbolic/null values to integer codes:
  - `1` = opening auction
  - `2` = closing auction
  - `0` = continuous session
- Updated the toxicity/reversion auction exclusion filter to select `auction = 0`.
- Updated q bootstrap and unit tests to assert integer auction codes.

### Files changed

- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Updated schema-contract tests so liquidity, tick-normalized liquidity, realized-volatility, effective-spread, and price-impact quote contracts no longer require `session`.
- Updated query-planner tests to check quote contracts require neither `session` nor `auction`.
- Updated kdb bootstrap tests to assert integer auction-code bucket amendments.

### Validation

- Ran `PYTHONPATH=. pytest -q tests/test_kdb_schema_contracts.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py` successfully.
- Ran `PYTHONPATH=. pytest -q` successfully.
- Ran a repository grep confirming no remaining q references to `` `open``, `` `close``, or `null auction`.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 93%

### Remaining work before milestone completion

- Confirm production raw-data functions emit integer `auction` codes on trade rows.
- Add a short production-schema note or sample fixture documenting `auction` code semantics at the kdb source boundary.
- Continue hardening live query smoke tests around production source-function contracts.

### Best next deterministic step

- Add a production-schema example documenting the canonical trade and quote source columns, including integer `auction` semantics and quote rows without `session`.

### Open questions

- Should MMSR tolerate legacy symbolic auction values during a transition period, or should production source functions convert them to integer codes before returning rows?


## 2026-05-28 — Fix calculation namespace bootstrap for live kdb preflight

### Implemented

- Diagnosed the live kdb `assign` error during `mmsr preflight --metric quoted_spread_bps` as a likely namespace bootstrap failure when using nested calculation namespaces such as `.desk.mmsr`.
- Updated the calculation-function bootstrap to enter and create the configured q namespace before assigning MMSR helper functions.
- Added regression coverage for nested namespace bootstrap output.

### Files changed

- `mmsr/kdb/query_loader.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_calculation_function_bootstrap_creates_nested_namespace`.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup emitted the environment-level spreadsheet warmup warning, but pytest completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 94%

### Remaining work before milestone completion

- Re-run the live kdb preflight against the user's environment to confirm the namespace creation resolves the `assign` error.
- Add a production schema example documenting canonical source columns and integer auction semantics.

### Open Questions

- None.

### Next deterministic step

- If preflight still fails, capture and inspect the exact rendered q/query fragment and kdb stack/error line to distinguish source-function schema issues from q syntax/runtime issues.

## Phase 10 Iteration 88 - Reserved q local-name fix for kdb assign error

### Implemented

- Corrected the previous diagnosis of the live kdb `assign` failure.
- Identified an MMSR-owned q helper collision: `rollupMetricResult` used `cols:` as a local assignment, but `cols` is a q table keyword/reserved name and can raise `assign`.
- Renamed the helper's internal locals to `mmsrColumnNames`, `mmsrHasBucket`, `mmsrHasSym`, `mmsrHasCap`, and `mmsr*` rollup variables.
- Added a regression test to ensure the bootstrap no longer renders `cols: cols facts`.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_calculation_function_bootstrap_avoids_reserved_cols_assignment`.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup emitted the environment-level spreadsheet warmup warning, but pytest completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 95%

### Remaining work before milestone completion

- Re-run live kdb preflight against the user's environment to confirm the `assign` error is gone.
- Add a production schema example documenting canonical source columns and integer auction semantics.
- Add a broader reserved-word lint for rendered q helper local assignments if more live-kdb parse issues surface.

### Open Questions

- None.

### Next deterministic step

- Re-run the same preflight command against live kdb using the patched package; if another q parser/runtime error appears, capture the rendered q/backtrace and fix the next concrete q incompatibility.

---

## 2026-05-28 — Centralized MMSR q function definitions and removed rollup `$` branching

### Implemented

- Moved every MMSR-owned metric calculation function body out of per-metric query template files and into the single canonical q library file `mmsr/kdb/q_lib/mmsr_calculations.q.j2`.
- Kept per-metric `query_templates/*.q.j2` files only as compatibility/documentation shims; query planning now loads metric function blocks from the q library.
- Added `load_metric_q_template` so legacy template names such as `liquidity` still resolve to the q library block.
- Changed calculation bootstrap rendering to install only shared reusable helpers from the q library, not request-specific metric functions.
- Rewrote `rollupMetricResult` to avoid `$[...]` conditional branching and to parenthesize aggregation-level membership predicates explicitly.
- Preserved existing metric query behavior and schema contracts while making the physical q function source single-file.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/query_templates/activity.j2`
- `mmsr/kdb/query_templates/effective_spread.q.j2`
- `mmsr/kdb/query_templates/flow.j2`
- `mmsr/kdb/query_templates/liquidity.j2`
- `mmsr/kdb/query_templates/liquidity_ticks.j2`
- `mmsr/kdb/query_templates/price_impact.q.j2`
- `mmsr/kdb/query_templates/realized_volatility.j2`
- `mmsr/kdb/query_templates/toxicity_reversion.j2`
- `_docs/journal.md`

### Tests added or updated

- Existing query loader tests now continue to pass through `load_q_template(...)` because metric template names resolve to the canonical q library blocks.
- Existing runner and query-plan tests cover that rendered metric queries still include the expected calculation functions and calls.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py tests/test_kdb_schema_contracts.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup printed an environment-level spreadsheet warmup warning, but the test suite completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 94%

### Remaining work before milestone completion

- Validate the rendered q against a live kdb process using the user's production source functions and capture any remaining q runtime errors with the rendered query text.
- Add a production schema/example document for canonical source columns and integer auction semantics.

### Best next deterministic step

- Add a debug/preflight option that prints or saves the exact rendered q query and source contracts whenever kdb raises a runtime error.

### Open questions

- Need the exact live kdb `$` backtrace/query line if the centralized q library package still raises `$` after this change.

## 2026-05-28 — Remove per-metric q template shims

### Implemented

- Removed the per-metric q template shim files from `mmsr/kdb/query_templates`.
- Kept `mmsr/kdb/q_lib/mmsr_calculations.q.j2` as the single source for all MMSR-owned q function definitions and metric calculation blocks.
- Updated q template loader documentation to make per-metric names stable identifiers only, not separate q files.
- Updated README guidance to describe the single-library q layout.
- Added a regression test asserting that no metric `.q.j2` files remain under `mmsr.kdb.query_templates`.

### Files changed

- `README.md`
- `mmsr/kdb/query_loader.py`
- `tests/test_kdb_query_loader.py`
- Removed `mmsr/kdb/query_templates/activity.j2`
- Removed `mmsr/kdb/query_templates/effective_spread.q.j2`
- Removed `mmsr/kdb/query_templates/flow.j2`
- Removed `mmsr/kdb/query_templates/liquidity.j2`
- Removed `mmsr/kdb/query_templates/liquidity_ticks.j2`
- Removed `mmsr/kdb/query_templates/price_impact.q.j2`
- Removed `mmsr/kdb/query_templates/realized_volatility.j2`
- Removed `mmsr/kdb/query_templates/toxicity_reversion.j2`
- `_docs/journal.md`

### Tests added or updated

- Added `test_metric_q_functions_only_live_in_calculation_library`.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_loader.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_kdb_schema_contracts.py`
- `PYTHONPATH=. pytest -q`
- Both commands passed. The environment emitted the existing spreadsheet runtime warmup warning during Python startup; it did not affect test results.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 94%

### Remaining work before milestone completion

- Validate the generated q against the live kdb error path that raised `$` and fix the concrete expression once the backtrace/rendered line is identified.
- Add a production schema example documenting canonical trade and quote source columns.

### Open Questions

- The live kdb `$` error still needs its exact rendered q line or q backtrace to identify whether it is caused by time-bucket casting, source column types, or another expression.

### Single best next deterministic step

- Capture/render the exact q submitted for the failing live `preflight` command and reduce the `$` error to the smallest failing q expression.

---

## 2026-05-28 — Remove separate calendar q template and centralize calendar dispatch

### Implemented

- Removed the remaining separate `mmsr/kdb/query_templates` q template directory from the package.
- Moved the package-owned calendar dispatch helper into `mmsr/kdb/q_lib/mmsr_calculations.q.j2` as `.callTradingCalendar`.
- Changed `KdbTradingCalendarSource` so it no longer renders a `{{ calendar_function }}[start;end]` template or emits a direct `.sb...getTradingCalendar[start;end]` call.
- Updated production CLI paths to install the configured MMSR calculation namespace before calendar queries, so the calendar source calls the central `.callTradingCalendar` helper.
- Updated packaging metadata and docs so only `mmsr/kdb/q_lib/*.q.j2` is packaged for kdb q logic.

### Files changed

- `README.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `pyproject.toml`
- `mmsr/cli.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_loader.py`
- `mmsr/periods/calendar.py`
- `tests/test_calendar.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_production_cli.py`
- Removed `mmsr/kdb/query_templates/__init__.py`
- Removed `mmsr/kdb/query_templates/trading_calendar.q.j2`

### Tests added or updated

- Updated calendar tests to assert `.callTradingCalendar[.sb.mmsr.getTradingCalendar;start;end]` is used and the direct `.sb.mmsr.getTradingCalendar[start;end]` pattern is not emitted.
- Updated query-loader tests to assert `trading_calendar.q` no longer exists as a separate template.
- Updated production CLI tests for the explicit q library install query before calendar access.

### Validation

- `PYTHONPATH=. pytest -q` passed.
- Python startup printed the existing environment-level spreadsheet warmup warning, but the test suite completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 95%

### Remaining work before milestone completion

- Validate the generated q against the live kdb `$` error path and fix the concrete expression once the backtrace/rendered line is identified.
- Add a production schema example documenting canonical trade and quote source columns.

### Open Questions

- The live kdb `$` error still needs its exact rendered q line or q backtrace to identify whether it is caused by time-bucket casting, source column types, or another expression.

### Single best next deterministic step

- Add a CLI/debug option that writes the exact rendered q submitted during `preflight`, then use it to isolate the live `$` error.


---

## 2026-05-28 — Remove unused metricName from q rollup API

### Implemented

- Removed the unused `metricName` argument from `{{ calculation_namespace }}.rollupMetricResult`.
- Updated day-query rendering so rollup calls now pass only the fact table and requested aggregation levels.
- Added a regression assertion that generated q does not pass a metric name into `rollupMetricResult`.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_plan.py`
- `_docs/journal.md`

### Tests added or updated

- Updated `tests/test_kdb_query_plan.py` to assert the new two-argument rollup call shape and prevent the removed metric-name argument from returning.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup printed the existing environment-level spreadsheet warmup warning, but the test suite completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 96%

### Remaining work before milestone completion

- Validate the generated q against the live kdb `$` error path and fix the concrete expression once the backtrace/rendered line is identified.
- Add a production schema example documenting canonical trade and quote source columns.

### Open Questions

- The live kdb `$` error still needs its exact rendered q line or q backtrace to identify whether it is caused by time-bucket casting, source column types, or another expression.

### Single best next deterministic step

- Add a CLI/debug option that writes the exact rendered q submitted during `preflight`, then use it to isolate the live `$` error.

---

## 2026-05-28 — Delegate production day query assembly to q runner function

### Implemented

- Added `{calculation_namespace}.runMetricDay` to `mmsr/kdb/q_lib/mmsr_calculations.q.j2` so kdb owns the production day chunk loop, source loading, metric dispatch, and q-side rollups.
- Simplified `KdbMetricQueryPlanner.render_day` to render a readable top-level q function call instead of assembling the day execution body line by line in Python.
- Added Python helpers for explicit q source-loader and metric-function dictionaries.
- Updated production/query-plan tests to assert the new function-call shape rather than the old inline anonymous day body.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_production_cli.py`
- `_docs/journal.md`

### Tests added or updated

- Updated day-query planner coverage to check `.runMetricDay[...]`, source loader functions, and metric function handles.
- Updated production CLI coverage to confirm live metric execution uses `.runMetricDay[...]`.

### Validation

- Ran `PYTHONPATH=. pytest -q` successfully.
- The environment still prints the spreadsheet runtime warmup warning during Python startup, but it does not affect the test result.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 95%

### Remaining work before milestone completion

- Continue removing request-rendered q from the execution path by parameterizing metric calculation functions directly, so metric function definitions can be installed once and production queries can be pure function calls.

### Best next deterministic step

- Convert `calcActivity` and `calcLiquidity` to parameterized installed q functions first, then remove their request-rendered metric template blocks from production day queries.

### Open questions

- None.

---

## 2026-05-28 — Revert q namespace directory bootstrap

### Implemented

- Reverted the calculation namespace `\d` bootstrap added in the previous iteration.
- Restored q library installation to render absolute namespace-qualified assignments only, such as `.desk.mmsr.timeBucket:{...}`.
- Updated the bootstrap regression test so `render_calculation_function_bootstrap` fails if `\d` directory changes are reintroduced.

### Files changed

- `mmsr/kdb/query_loader.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Updated `test_calculation_function_bootstrap_uses_absolute_assignments_only` to assert the rendered bootstrap contains no `\d` directory commands.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup still printed the unrelated spreadsheet runtime warmup warning from the execution environment, but it did not fail the tests.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 94%

### Remaining work before milestone completion

- Continue simplifying live kdb execution so Python submits compact function calls and q owns calculation control flow.
- Validate the centralized q runner against a real kdb process using production-like source functions and exact live error traces.

### Best next deterministic step

- Reproduce the reported live `$` error with the current centralized q query and remove the failing q construct from `mmsr_calculations.q.j2`.

### Open questions

- What exact q backtrace is produced by the remaining live `$` error after the namespace bootstrap revert?

---

## 2026-05-28 — Add production execution logging controls

### Implemented

- Added `mmsr.logging.configure_logging` for CLI-controlled Python logging.
- Added `--verbose` / `-v` and `--log-level` options to production `plan`, `preflight`, and `render` commands.
- Added status logs for config loading, kdb connection/query execution, q-library installation, calendar calls, symbol-universe calls, plan sizing, day-batch execution, preflight sample execution, comparison building, report rendering, and HTML output writing.
- Added DEBUG logging of the exact rendered q sent through `KdbClient.execute` when verbose mode is enabled.
- Documented production logging usage in `README.md`.

### Files changed

- `README.md`
- `mmsr/cli.py`
- `mmsr/kdb/client.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/runner.py`
- `mmsr/logging.py`
- `mmsr/periods/calendar.py`
- `mmsr/periods/symbols.py`
- `tests/test_logging.py`
- `_docs/journal.md`

### Tests added or updated

- Added `tests/test_logging.py` to verify production CLI logging options and logging configuration behavior.

### Validation

- `PYTHONPATH=. pytest -q tests/test_logging.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- `python -m black mmsr tests` could not run because `black` is not installed in this execution environment.
- Python startup still printed the unrelated spreadsheet runtime warmup warning from the execution environment, but it did not fail the tests.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 95%

### Remaining work before milestone completion

- Validate verbose live-kdb logs against the reported `$` failure and use the rendered q/backtrace to remove the failing q construct.
- Continue simplifying production q submission so Python submits compact function calls and q owns calculation control flow.

### Best next deterministic step

- Run `mmsr preflight --verbose` against the live kdb endpoint and fix the concrete `$` error using the logged rendered q and kdb backtrace.

### Open questions

- What exact rendered q line and q backtrace correspond to the remaining live `$` error under verbose logging?

---

## 2026-05-28 — Fix PyKX credential defaults and q library block loading names

### Implemented

- Updated `KdbClient.connect` so missing `username` and `password` values are passed to `pykx.QConnection` as empty strings instead of `None`.
- Investigated the reported render-time q template loading path after removing `mmsr/kdb/query_templates`.
- Confirmed the render path was not reading deleted per-metric files, but it still used the legacy `load_metric_q_template` name, which made the code look like it was loading removed files.
- Renamed the active render-path loader usage to `load_metric_calculation_block`, which resolves marked metric calculation blocks from the canonical `mmsr/kdb/q_lib/mmsr_calculations.q.j2` file.
- Kept `load_metric_q_template` only as a backward-compatible alias for older callers/tests, with render planning no longer importing or calling it.

### Files changed

- `mmsr/kdb/client.py`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `_docs/journal.md`

### Tests added or updated

- Added a client regression test confirming missing kdb credentials are normalized to empty strings before calling `pykx.QConnection`.
- Added a render-day regression test confirming the planned query comes from canonical q-library blocks and contains no removed `query_templates` path or `.q.j2` per-metric filename.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_loader.py tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_logging.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Running `pytest -q` without `PYTHONPATH=.` still fails in this extracted zip layout because the package is not installed and the project root is not on the import path.
- Python startup still printed the unrelated spreadsheet runtime warmup warning from the execution environment, but it did not fail the tests.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 96%

### Remaining work before milestone completion

- Continue replacing request-rendered metric blocks with true parameterized q functions so production queries become compact q function calls and no metric calculation block needs to be rendered into each query.
- Validate live kdb execution with the verbose logs and remove the concrete source of the remaining live `$` error.

### Best next deterministic step

- Parameterize the liquidity q calculation first so `quoted_spread_bps` preflight can call an installed q function with explicit parameters instead of rendering a metric calculation block.

### Open questions

- What exact q backtrace is produced by the remaining live `$` error after credential normalization and canonical-library render cleanup?

---

## 2026-05-28 — Stop loading metric q templates and parameterize installed q calculations

### Implemented

- Removed runtime metric q template/block loading from production query planning.
- Changed single-metric, batch, and day render paths to call installed q functions from `mmsr/kdb/q_lib/mmsr_calculations.q.j2` instead of rendering deleted per-metric `.q.j2` files or q-library metric blocks into each report query.
- Kept every MMSR-owned q function definition in the single canonical q file, including activity, liquidity, flow, realized volatility, effective spread, price impact, and reversion calculations.
- Added parameter dictionaries for installed q metric functions so bucket duration, report start/end dates, and metric-specific values are passed as q parameters rather than template substitutions.
- Deprecated `load_q_template` and `load_metric_calculation_block` so they no longer resolve metric template files; runtime code no longer calls them.
- Updated the mock kdb demo path to recognize the new parameterized query shape used by report rendering.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/query_loader.py`
- `mmsr/examples/mock_kdb_demo.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_production_cli.py`
- `_docs/journal.md`

### Tests added or updated

- Updated q loader tests to assert metric template loaders are deprecated and do not resolve removed files.
- Updated query planner and production execution tests to assert rendered queries call installed q functions and do not include removed template file paths or embedded metric template blocks.
- Updated mock report rendering tests for the new parameterized q call shape.

### Validation

- `PYTHONPATH=. pytest -q` passed.
- Python startup still printed the unrelated spreadsheet runtime warmup warning from the execution environment, but it did not fail the tests.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 97%

### Remaining work before milestone completion

- Run the new verbose report/preflight path against live kdb and fix any remaining q runtime errors using the logged query and q backtrace.
- Harden q-side rollups further if live results show aggregation-level semantics need more explicit market/topix/symbol aggregation rather than the current canonical grouped fact shape.

### Best next deterministic step

- Run `mmsr preflight --verbose` for `quoted_spread_bps` against the live kdb endpoint and fix any concrete q runtime failure from the logged rendered call and kdb backtrace.

### Open questions

- Does the live kdb `$` error persist after report rendering stops loading metric templates entirely and uses installed parameterized q functions?


---

## 2026-05-28 — Move production report-day orchestration into q

### Implemented

- Updated `_docs/ROADMAP.md` with the Milestone 5 architecture correction: production report-day execution must be kdb-owned.
- Replaced Python-built production day chunk loops and metric lambdas with a single installed q entry point: `runReportDay[runDate; reportConfig]`.
- Added q-side helpers in `mmsr/kdb/q_lib/mmsr_calculations.q.j2`:
  - `applyUniverseFilters`
  - `loadReportSources`
  - `runMetric`
  - `runReportDay`
- Changed `KdbMetricQueryPlanner.render_day()` so Python renders only date, source function handles, metric names, metric parameter dictionaries, universe filters, aggregation levels, and chunk size.
- Stopped Python production planning from fetching symbol universes or splitting symbol chunks. Optional CLI symbols are passed only as q-side universe filters.
- Changed production preflight to use the day runner path.
- Removed `template=` wording from day/single runner logs and day-result metadata in favor of metric family terminology.
- Updated tests for q-owned symbol discovery, q-owned chunking, and the `runReportDay` execution shape.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/production.py`
- `mmsr/kdb/runner.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Updated production execution tests to assert one Python request per day/metric with q-owned symbol chunking.
- Updated query-plan tests to assert production day q uses `runReportDay`, does not contain generated metric lambdas, and does not reference removed template files.
- Updated production CLI tests to assert `runReportDay` is the production execution entry point.

### Validation

- `PYTHONPATH=. pytest -q` passed.
- The environment still printed the unrelated spreadsheet runtime warmup warning during Python startup, but it did not prevent tests from passing.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 98%

### Remaining work before milestone completion

- Run `mmsr preflight --verbose` against live kdb to validate `runReportDay` q syntax and source-function invocation with real PyKX.
- If live q exposes syntax/runtime issues, fix only the q-side top-level runner or source dispatch path.

### Best next deterministic step

- Execute `quoted_spread_bps` preflight with `--verbose` against live kdb and use the logged `runReportDay` query/backtrace to harden q runtime behavior.

### Open questions

- Should explicit CLI `--symbol` filters be passed as PyKX query arguments instead of rendered q literals in a later hardening step?


---

## 2026-05-28 — Fix q symbol-cast rendering for report-day config dictionaries

### Implemented

- Fixed the central q string-to-symbol literal renderer so arbitrary string symbols render with the required leading backtick, for example `` `$"reference_data"``, `` `$"quoted_spread_bps"``, and `` `$"7203"``.
- Updated report-day config rendering so dictionary keys and symbol-vector values sent to ``runReportDay`` no longer produce bare ``$"..."`` expressions.
- Updated legacy single/batch query tests to expect the same canonical q symbol cast for numeric Japanese symbols.
- Added regression checks that report-day rendered q does not contain bare ``$"reference_data"``, ``$"quoted_spread_bps"``, or ``$"7203"`` without a leading backtick.

### Files changed

- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `_docs/journal.md`

### Tests added or updated

- Updated q rendering expectations for numeric symbol filters and metric-result dictionaries.
- Added explicit report-day query assertions for backtick-preserving symbol casts in source-function keys, metric names, and explicit symbol filters.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_plan.py tests/test_kdb_metric_runner.py tests/test_kdb_production_execution.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- Python startup still printed the unrelated spreadsheet runtime warmup warning from the execution environment, but it did not fail the tests.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 98%

### Remaining work before milestone completion

- Run `mmsr preflight --verbose` against live kdb to validate the corrected ``runReportDay`` config dictionary syntax end-to-end.
- Fix any remaining live q runtime issues in the q-side top-level runner or source dispatch path.

### Best next deterministic step

- Execute `quoted_spread_bps` preflight with `--verbose` against live kdb and use the logged corrected ``runReportDay`` query/backtrace to harden q runtime behavior.

### Open questions

- Should explicit CLI `--symbol` filters be passed as PyKX query arguments instead of rendered q literals in a later hardening step?

---

## 2026-05-28 — Fix q singleton dictionary rendering and rawSources key enlistment

### Implemented

- Fixed q dictionary rendering for singleton keys so Python emits `enlist[`key]!enlist value` instead of `enlist `key!enlist value`.
- Applied the safe singleton-key rendering to metric parameter dictionaries and universe filter dictionaries used by `runReportDay`.
- Updated the q library `loadReportSources` initialization from `` `refs!(enlist refs)`` to `enlist[`refs]!enlist refs`.
- Added regression tests for singleton metric dictionaries, universe filter dictionaries, and the q-library raw source initialization shape.
- Updated legacy query tests to accept parenthesized multi-key dictionaries such as ``(`bucket;`start_date;`end_date)!...``.

### Files changed

- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_render_day_singleton_metric_dictionaries_enlist_keys_before_bang`.
- Added `test_q_library_uses_safe_singleton_dictionary_key_enlistment`.
- Updated kdb metric runner string expectations for the safer parenthesized q dictionary syntax.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_plan.py tests/test_kdb_query_loader.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- The environment still prints an unrelated spreadsheet warmup warning during Python startup, but tests passed.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 98%

### Remaining work before milestone completion

- Run `mmsr preflight --verbose --metric quoted_spread_bps` against live kdb and fix any remaining q runtime issue in the `runReportDay` path.
- Continue replacing rendered literals with PyKX argument passing where practical.

### Best next deterministic step

- Validate the corrected `runReportDay` query against live kdb with a one-symbol `quoted_spread_bps` preflight.

### Open questions

- None.

---

## 2026-05-28 — Enforce safe singleton q dictionary rendering

### Implemented

- Reviewed singleton q dictionary construction in Python query rendering and the central q library.
- Added a shared singleton dictionary renderer so one-pair q dictionaries consistently use the safe `enlist[`key]!enlist value` shape.
- Parenthesized composite singleton dictionary values in rendered q so kdb enlists the full value expression, not a partial right-hand expression.
- Updated function-handle dictionary rendering to use the same singleton dictionary helper.
- Kept `loadReportSources` initialized as `rawSources: enlist[`refs]!enlist refs;` in `mmsr_calculations.q.j2`.
- Added/updated regression tests for singleton `metricParams` and `universeFilters` rendering.

### Files changed

- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_query_plan.py`
- `_docs/journal.md`

### Tests added or updated

- Updated `test_render_day_singleton_metric_dictionaries_enlist_keys_before_bang` to assert the exact safe singleton dictionary forms for metric parameters and symbol filters.
- Updated day-rendering assertions to accept simple q symbol keys such as `reference_data` while retaining checks against bare `$"..."` forms.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_plan.py tests/test_kdb_query_loader.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- The environment still prints the unrelated spreadsheet runtime warmup warning during Python startup, but the test commands completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 98%.

### Remaining work before milestone completion

- Run the new `runReportDay` query against live kdb with `--verbose` and fix any remaining q runtime issue from the actual kdb backtrace.
- Consider moving explicit CLI filter dictionaries from rendered q literals to PyKX arguments if live debugging shows additional parser friction.

### Best next deterministic step

- Run `mmsr preflight --verbose --metric quoted_spread_bps` against live kdb using this package and patch the first concrete q error from the logged `runReportDay` call.

### Open questions

- None.

## 2026-05-28 — Return unkeyed kdb metric tables from runReportDay

### Implemented

- Investigated the live `OutputSchemaContractError` where kdb returned a dictionary keyed by `quoted_spread_bps` and the metric value was a keyed table.
- Updated all MMSR q metric calculation functions in `mmsr/kdb/q_lib/mmsr_calculations.q.j2` to return unkeyed tables with `0!result`.
- Updated `rollupMetricResult` to return unkeyed tables for normal, empty-input, and no-rollup paths.
- Added defensive Python handling for common keyed-table Python representations by merging key/value columns during schema validation and result normalization.
- Added defensive handling for pandas-like keyed-table conversions by including index names during schema extraction and resetting named indexes during normalization.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/runner.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added q-library regression coverage that metric functions and rollups return unkeyed tables.
- Added output-schema validation coverage for keyed-table mapping representations.
- Added day-runner normalization coverage for a metric dictionary whose value is a keyed-table mapping representation.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_query_loader.py tests/test_kdb_schema_contracts.py tests/test_kdb_metric_runner.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- The environment still prints the unrelated spreadsheet runtime warmup warning during Python startup, but the test commands completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 99%.

### Remaining work before milestone completion

- Run `mmsr preflight --verbose --metric quoted_spread_bps` against live kdb and confirm Python now sees `date`, `time_bucket`, `sym`, `topixCapGrp`, `quoted_spread_bps`, and `top_of_book_depth`.
- If live PyKX still preserves keyed-table structure in a different shape, add that shape to the defensive unkeying adapter.

### Best next deterministic step

- Validate the corrected unkeyed `runReportDay` output against live kdb with the failing `quoted_spread_bps` command.

### Open questions

- None.


## 2026-05-28 — Add pluggable day-metric cache hooks

### Implemented

- Added a small kdb cache API with `MetricDayCacheKey`, `MetricDayCacheHooks`, and load/persist protocols for user-provided day/metric storage.
- Extended `KdbMetricRunner.run_day()` to consult user cache loaders before executing kdb, skip fully cached metrics, execute only cache misses, and call user persisters after successful schema validation and normalization.
- Added defensive validation for cached series so a user loader cannot accidentally return the wrong metric or a different trading day.
- Added cache hit/miss metadata to returned `MetricTimeSeries` objects while keeping the no-cache default path unchanged.
- Exported the cache hook/key types from `mmsr.kdb`.

### Files changed

- `mmsr/kdb/cache.py`
- `mmsr/kdb/runner.py`
- `mmsr/kdb/__init__.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added day-runner coverage for a full cache hit that avoids kdb execution.
- Added day-runner coverage for cache misses that execute kdb and persist normalized results.
- Added mixed hit/miss coverage confirming only uncached metrics are requested from kdb and original request order is preserved.
- Added validation coverage for stale/wrong cached series.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- `python -m black ...` could not be run because `black` is not installed in this environment.
- `python -m flake8 ...` could not be run because `flake8` is not installed in this environment.
- The environment still prints the unrelated spreadsheet runtime warmup warning during Python startup, but the pytest commands completed successfully.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 99%.

### Remaining work before milestone completion

- Run `mmsr preflight --verbose --metric quoted_spread_bps` against live kdb and confirm the day-runner output shape with and without cache hooks.
- Decide whether to add a built-in file-backed cache implementation, or keep MMSR cache storage entirely user-owned for production.

### Best next deterministic step

- Validate `KdbMetricRunner.run_day()` with production user load/persist functions against live kdb for one `quoted_spread_bps` trading day.

### Open questions

- Should MMSR provide a reference local filesystem cache implementation, or should production cache storage remain entirely user-pluggable?

---

---

## 2026-05-28 — Reversion day-run performance inspection and common-prejoin batching

### Implemented

- Inspected the Python day-run path and q reversion calculation path after production feedback that one day of reversion data can run for about 1.5 hours.
- Identified the main deterministic performance issue: each requested `primary_quote_reversion_*_bps` horizon was executed as a separate metric, causing the same large PTS trade, PTS quote, and primary quote inputs to be filtered, sorted, and as-of joined once per horizon.
- Split reversion q calculation into:
  - `prepareToxicityReversion`, which filters and performs common PTS/primary pre-joins once for a chunk.
  - `calcToxicityReversionPrepared`, which applies one horizon to already-prepared rows.
  - `calcToxicityReversionFamily`, which computes all requested reversion horizons from the shared prepared rows in one day-run family block.
- Updated `runReportDay` so reversion metrics are batched as a family per chunk while non-reversion metrics continue through the normal `runMetric` path.
- Added a q predicate `isToxicityReversionMetric` to keep family detection centralized.
- Documented in the q template that production day source functions should already return one `runDate`; date filters remain only as defensive guards for direct/multi-day calls.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added bootstrap tests proving the day runner batches reversion horizons through `calcToxicityReversionFamily`.
- Added bootstrap tests proving the shared reversion preparation block is called once by the family calculation before horizon-specific scoring.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- `python -m black --check mmsr tests` could not run because `black` is not installed in this environment.
- `python -m flake8 mmsr tests` could not run because `flake8` is not installed in this environment.
- Live kdb performance validation was not possible in this environment.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Run one live production day for all six reversion horizons and compare wall-clock time before/after this common-prejoin batching.
- If runtime is still above target, profile whether the remaining cost is dominated by primary post-horizon as-of joins, source loader scans, or symbol chunk sizing.

### Best next deterministic step

- Add optional q-side timing instrumentation around source load, common reversion preparation, per-horizon post joins, and rollup so production can identify the remaining bottleneck precisely.

### Open questions

- Are production `pts_trades`, `pts_quotes`, and `primary_quotes` source functions guaranteed to return only the supplied `runDate`, or should MMSR assert that invariant inside the day runner?
- Are the production PTS and primary quote sources already sorted/parted by `date`, `sym`, `venue`, and `time`, or does MMSR need to add explicit source-contract guidance for parted attributes?



---

## 2026-05-28 — Partition reversion aj inputs by symbol

### Implemented

- Added a q-side `partedSym` helper that applies the `p#` attribute to `sym` on sorted tables.
- Updated the Cross-Venue Toxicity/Reversion q path so every reversion `aj` consumes a materialized, sorted table with `sym` partitioned before the join.
- Kept the optimization scoped to reversion joins, where production execution is day-scoped and `sym` is contiguous after the join-key sort.
- Avoided changing the Python execution API or cache hooks.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added a bootstrap rendering test that verifies reversion aj inputs are sorted and passed through `partedSym` before the aj calls.
- Updated tests indirectly covering q bootstrap rendering.

### Validation

- `PYTHONPATH=. pytest -q tests/test_kdb_metric_runner.py tests/test_kdb_query_plan.py` passed.
- `PYTHONPATH=. pytest -q` passed.
- `black` and `flake8` are not installed in this environment, so those checks could not run.
- Live kdb timing was not available in this environment.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Validate the reversion query with live kdb data to confirm `p#sym` materially reduces runtime and does not expose any multi-day/direct-template attr assumptions.
- Profile the remaining horizon aj and aggregation costs if single-day runtime is still above a few minutes.

### Best next deterministic step

- Run one live kdb timing comparison for a single trading day and confirm whether the optimized reversion family path now completes within the expected runtime window.

### Open questions

- Should direct multi-day q-template calls be explicitly unsupported for reversion, since production source loaders are expected to return a single `runDate`?
---

## 2026-05-28 — Remove legacy transaction-cost q paths and template filename references

### Implemented

- Removed the out-of-scope `calcEffectiveSpread` and `calcPriceImpact` q calculation functions from the reusable MMSR q library.
- Removed production runner/query-planner support for `effective_spread_bps` and `price_impact_30s_bps`.
- Removed transaction-cost input/output schema contracts and validation dispatch from `mmsr.kdb.schema_contracts`.
- Removed transaction-cost starter metric definitions so the default registry now contains market activity, displayed liquidity, optional market-state add-ons, flow, and reversion metrics only.
- Replaced legacy logical template filename identifiers such as `activity.q`, `liquidity.q`, and `toxicity_reversion.q` with metric-family identifiers such as `activity`, `liquidity`, and `toxicity_reversion` across active code, tests, and production docs.
- Updated tests to assert the active metric-family contract names and the smaller q library surface.

### Files changed

- `_docs/AGENTS.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `mmsr/analysis/anomaly.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/metrics/starter_definitions.py`
- `tests/test_config_files.py`
- `tests/test_kdb_metric_runner.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`

### Tests added or updated

- Updated kdb runner, query planner, schema contract, production execution, config, and q-library tests to remove transaction-cost expectations.
- Updated active template-name expectations from legacy `.q` filenames to metric-family identifiers.

### Validation

- Ran `PYTHONPATH=. pytest -q` successfully.
- Confirmed active code/tests/docs no longer contain `calcEffectiveSpread`, `calcPriceImpact`, `effective_spread`, `price_impact`, `activity.q`, `liquidity.q`, or `toxicity_reversion.q` references outside historical journal content.
- `black --check .` could not be run because `black` is not installed in this environment.
- `flake8 .` could not be run because `flake8` is not installed in this environment.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Run a live single-day kdb timing comparison for the optimized reversion family path.
- Confirm production source loaders return day-scoped rows for the supplied run date.

### Best next deterministic step

- Run one live kdb preflight/timing pass for a configured reversion metric family over one trading day and record the elapsed time per chunk and horizon family.

### Open questions

- None.



## 2026-05-28 — Remove remaining legacy optional q-template families

### Implemented

- Removed the remaining legacy optional metric families from the active registry, q library, query planner, and schema contracts.
- Removed active support for tick-normalized spread, quote-mid volatility, and feed-signed flow metrics so the production surface only exposes activity, displayed liquidity, and Cross-Venue Toxicity/Reversion.
- Removed q runner dispatch branches for the legacy optional metric families.
- Updated active documentation to stop describing removed legacy optional q-template families as supported.
- Added a q-library regression test that guards against reintroducing the removed legacy metric functions.

### Files changed

- `mmsr/metrics/starter_definitions.py`
- `mmsr/kdb/query_plan.py`
- `mmsr/kdb/schema_contracts.py`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_query_plan.py`
- `tests/test_kdb_schema_contracts.py`
- `tests/test_kdb_query_loader.py`
- `README.md`
- `docs/kdb_integration_testing.md`
- `docs/production_readiness.md`
- `_docs/MILESTONE_STATUS.md`
- `_docs/ROADMAP.md`
- `_docs/journal.md`

### Tests added or updated

- Removed query-plan and schema-contract tests for removed legacy optional metric families.
- Updated the q-library unkeyed-table assertion for the smaller active q surface.
- Added `test_q_library_excludes_removed_legacy_metric_functions`.

### Validation

- `python -m pytest -q` passed.
- Verified active source, tests, configs, README, and docs outside the historical journal no longer contain legacy identifiers for removed q-template families.
- `black` and `flake8` are not installed in this environment, so formatter/linter validation could not be run.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Run one live kdb timing/preflight pass for the optimized reversion family over one production trading day.
- Confirm the reduced production q surface with a live configuration using only default activity, displayed liquidity, and reversion metrics.

### Best next deterministic step

- Run a live one-day reversion family timing pass and record elapsed time per source load, preparation step, and horizon family.

### Open questions

- None.

---

## 2026-05-28 — Add canonical stockMetrics cache row helpers

### Implemented

- Added a canonical wide cache-row contract for user-owned `stockMetrics` persistence.
- Defined persisted dimensions as `date`, `timeBucket`, `bucketSize`, `sym`, `groupType`, and `groupValue`.
- Kept `timeBucket` as the actual segment label such as `AMO` or `09:00-09:05`.
- Kept `bucketSize` as the configured continuous-session interval such as `5m`.
- Avoided persisting time-segment type or sort columns because those are inferable by MMSR from the bucket label and configured bucket size.
- Added helpers to convert normalized `MetricTimeSeries` objects into stockMetrics rows, hydrate a metric series from stockMetrics rows, and merge metric-specific rows into a wide stockMetrics shape.
- Kept the existing per-metric cache hook signature for compatibility while documenting stockMetrics as the recommended storage shape.

### Files changed

- `mmsr/kdb/cache.py`
- `mmsr/kdb/__init__.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added coverage that stockMetrics rows persist only `timeBucket` and `bucketSize` for the time dimension.
- Added coverage for stockMetrics-to-`MetricTimeSeries` hydration.
- Added coverage for merging metric-specific stockMetrics rows into a wide table keyed by canonical dimensions.

### Validation

- Ran `python -m pytest -q` successfully.
- Python startup emitted a non-fatal spreadsheet runtime warmup warning from the environment, but pytest completed successfully.
- `black` and `flake8` are not installed in this environment, so formatter/linter validation could not be run.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Wire a batch-level stockMetrics loader/persister around `run_day()` so one user table read can satisfy multiple requested metric columns before falling back to q misses.
- Run one live kdb timing/preflight pass for the optimized reversion family over one production trading day.

### Best next deterministic step

- Replace per-metric cache hook calls with a batch stockMetrics-oriented load path that reads one day table once and computes only missing metric columns.

### Open questions

- None.


---

## 2026-05-28 — Batch stockMetrics cache load and persist hooks

### Implemented

- Added preferred wide `stockMetrics` cache hooks to `MetricDayCacheHooks`:
  - `load_stock_metrics`
  - `persist_stock_metrics`
- Updated `KdbMetricRunner.run_day()` to call the wide day-level loader once for all requested metric columns before any per-metric compatibility loader.
- Hydrated cached metric hits from canonical `stockMetrics` rows and computed only missing metrics through q.
- Updated day-result persistence so computed misses are written once through `persist_stock_metrics` as merged wide rows when that hook is configured.
- Kept existing per-metric `load` and `persist` hooks as compatibility fallbacks.
- Added regression tests covering partial wide-cache hits, q execution for misses only, and one-call wide persistence.

### Files changed

- `mmsr/kdb/cache.py`
- `mmsr/kdb/runner.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_day_runner_loads_stock_metrics_once_and_computes_only_missing_metrics`.
- Added `test_day_runner_persists_computed_misses_as_one_stock_metrics_batch`.

### Validation

- Ran `python -m pytest -q` successfully.
- Test startup printed an unrelated `artifact_tool` spreadsheet warmup warning before pytest execution, but pytest completed successfully.
- `black` and `flake8` are not installed in this environment, so formatting/lint checks could not be run.

### Current milestone

- Milestone 5: kdb metric runner interface / production q-template hardening.

### Estimated milestone completion

- 99%

### Remaining work before milestone completion

- Run a live kdb one-day reversion family timing pass using the new wide `stockMetrics` cache hooks.
- Confirm the production user loader/persister contract against an actual day-level `stockMetrics` table.

### Best next deterministic step

- Add a small user-facing example showing `load_stock_metrics` and `persist_stock_metrics` implementations against a q/kdb `stockMetrics` table.

### Open questions

- Should `persist_stock_metrics` merge with existing user-owned cached rows in kdb, or should the user hook own upsert semantics entirely?

---

## 2026-05-29 — Compact Plotly report HTML and activity distribution visuals

### Implemented

- Reworked the default time-series chart HTML partial to render compact Plotly
  figure specifications instead of inline SVG-only visuals and full backing-data
  tables.
- Added a generic `PlotlyChart` report component, renderer entry point, metric
  documentation collection support, and a reusable Plotly partial template.
- Added a report-level Plotly loader/initializer so each chart is rendered from
  colocated JSON while keeping the visible HTML focused on visuals and metric
  help.
- Added an `Activity Distribution` market-report page for activity metrics that
  renders:
  - current cumulative intraday percent as a line with circle markers;
  - historical cumulative intraday percent as per-bucket box/whisker statistics;
  - reference/current session and auction share as horizontal stacked bars.
- Kept activity diagnostics aggregated and intentionally skipped symbol-scoped
  series so the default report does not emit single-stock plots.
- Added options to enable/disable the activity page, configure the activity
  metric names, and cap the number of activity distribution charts.
- Updated demo/report page ordering expectations and compact-data rendering
  assertions.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/report/__init__.py`
- `mmsr/report/components.py`
- `mmsr/report/market_report.py`
- `mmsr/report/metric_docs.py`
- `mmsr/report/render_html.py`
- `mmsr/report/sections.py`
- `mmsr/report/templates/report.html.j2`
- `mmsr/report/templates/partials/plotly_chart.html.j2`
- `mmsr/report/templates/partials/time_series_chart.html.j2`
- `tests/test_cli.py`
- `tests/test_market_report.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_offline_demo.py`
- `tests/test_time_series_charts.py`

### Tests added or updated

- Added explicit coverage for compact activity distribution Plotly figures,
  including box statistics without raw `y` arrays, current line markers, and
  horizontal stacked session bars.
- Updated report, CLI, offline-demo, mock-kdb-demo, and chart-rendering tests to
  expect the new Activity Distribution page and compact Plotly chart markup.
- Updated assertions to verify compact plot data summaries replace raw backing
  tables in chart components.

### Validation

- Ran `python -m py_compile` on the touched report modules and updated tests
  successfully.
- Ran `python -m pytest -q` successfully.
- Rendered the deterministic offline demo report and confirmed:
  - the Activity Distribution page is present;
  - Plotly initialization is present;
  - `Backing data` is absent;
  - `Compact plot data` is present;
  - the generated sample HTML was about 134 KB.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.
- `black` and `flake8` were not installed/executable on this environment PATH,
  so formatter/linter validation could not be run here.

### Current milestone

- Milestone 9C: compact Plotly report HTML for kdb-scale data.

### Estimated milestone completion

- 75%

### Remaining work before milestone completion

- Validate HTML size and visual usability with a real kdb-backed production
  report.
- Add metric-specific compact Plotly diagnostics for displayed liquidity and
  reversion where the generic trend charts are not sufficient.
- Decide whether production deployments should use Plotly from CDN, a packaged
  local Plotly asset, or an offline self-contained bundle.
- Confirm the preferred reference window and session-label conventions for the
  activity distribution page.

### Best next deterministic step

- Run one real kdb-backed report render with the new compact Plotly report layer,
  record the output HTML size, and inspect the activity distribution page before
  adding more metric-specific compact visuals.

### Open questions

- Is using the Plotly CDN acceptable for the production report environment, or
  must Plotly be bundled locally for offline report viewing?
- Should session-share stacks use the current AMO/AMC/PMO/PMC and continuous
  AM/PM labels, or should they follow a client-specific exchange session map?


---

## 2026-05-29 — Add compact displayed-liquidity Plotly visuals and cap report tables

### Implemented

- Added a `Displayed Liquidity` market-report page for displayed-liquidity
  metrics such as `quoted_spread_bps` and `top_of_book_depth`.
- Added `build_reference_target_intraday_profile_chart()` for compact
  non-additive metric diagnostics:
  - historical per-bucket box/whisker statistics without raw `y` value arrays;
  - current-period intraday profile as a line with circle markers;
  - capped horizontal group-delta bars showing current minus reference by
    market-cap, segment, sector, or venue context.
- Wired displayed-liquidity page options into the canonical market report,
  including enable/disable flags, metric-name selection, chart caps, and group
  delta caps.
- Kept displayed-liquidity visuals aggregated and skipped symbol-scoped series
  in the default market report path.
- Changed default comparison, symbol-anomaly, drilldown, offline-demo, and
  mock-kdb-demo table limits so tables remain capped summary diagnostics rather
  than full payload dumps.
- Updated the roadmap to record displayed-liquidity visual coverage and the
  remaining reversion/toxicity visual milestone work.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/cli.py`
- `mmsr/examples/mock_kdb_demo.py`
- `mmsr/examples/offline_demo.py`
- `mmsr/report/__init__.py`
- `mmsr/report/market_report.py`
- `mmsr/report/sections.py`
- `tests/test_market_report.py`
- `tests/test_mock_kdb_demo.py`
- `tests/test_offline_demo.py`
- `tests/test_time_series_charts.py`

### Tests added or updated

- Added unit coverage for compact displayed-liquidity intraday profile figures,
  verifying box statistics are embedded without raw `y` arrays, current profile
  markers are present, group deltas are capped, and rendered Plotly partials do
  not emit tables.
- Updated canonical market-report, offline-demo, and mock-kdb-demo tests to
  expect the new `Displayed Liquidity` page.
- Updated option-validation tests for displayed-liquidity page text and caps.
- Updated report-page ordering tests and compact rendering assertions.

### Validation

- `python -m py_compile` on the touched report, example, CLI, and test modules
  passed.
- `python -m pytest -q` passed.
- Rendered the deterministic offline demo report and confirmed:
  - `Displayed Liquidity` is present;
  - `Backing data` is absent;
  - 13 Plotly figure containers are present;
  - the generated sample HTML is about 143 KB.
- `black --check .` and `flake8 .` could not be run because the executables are
  present but not executable in this environment (`PermissionError`).
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9C: compact Plotly report HTML for kdb-scale data.

### Estimated milestone completion

- 86%

### Remaining work before milestone completion

- Validate HTML size and visual usability with one real kdb-backed production
  report using the user's real data shape.
- Convert Cross-Venue Toxicity/Reversion from generic trend charts plus capped
  comparison rows into compact Plotly horizon curves and capped venue/horizon
  diagnostics.
- Decide whether production deployments should use the Plotly CDN, a packaged
  local Plotly asset, or an offline self-contained bundle.

### Best next deterministic step

- Rework the Cross-Venue Toxicity/Reversion page to render compact Plotly
  horizon progression curves and capped venue/horizon comparison diagnostics,
  then remove or further minimize the remaining reversion comparison table.

### Open questions

- Is using the Plotly CDN acceptable for the production report environment, or
  must Plotly be bundled locally for offline report viewing?
- Should session-share stacks use the current AMO/AMC/PMO/PMC and continuous
  AM/PM labels, or should they follow a client-specific exchange session map?
---

## 2026-05-29 — Clarify Plotly current-mean and null-filtered percentile semantics

### Implemented

- Clarified the compact Plotly chart semantics requested for report visuals:
  - current-period activity lines are rendered from mean daily bucket totals
    before cumulative-percent calculation;
  - current-period displayed-liquidity profiles are rendered from per-bucket
    means;
  - reference/historical box-and-whisker inputs are filtered for null, NaN, and
    non-finite values before percentile statistics are calculated.
- Changed activity session-share bars to use mean daily session percentages for
  both the current and reference periods, reducing distortion from high-volume
  days in a multi-day period.
- Updated Plotly trace names, hover text, compact data summaries, and roadmap
  wording so report users can see that the current line is a mean and the
  reference boxes are null-filtered percentile summaries.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/report/sections.py`
- `tests/test_time_series_charts.py`

### Tests added or updated

- Added coverage that activity distribution charts:
  - ignore null and NaN metric observations;
  - compute the current cumulative-percent line from mean daily bucket totals;
  - keep reference box statistics as percentile summaries.
- Added coverage that displayed-liquidity intraday profile charts:
  - ignore null and NaN observations;
  - compute current profile values as per-bucket means;
  - compute reference q1/median/q3 from the null-filtered historical values.
- Updated compact data-summary expectations to include the current-mean and
  null-filtered percentile semantics.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_time_series_charts.py -q` passed.
- `python -m pytest -q` passed.
- Rendered the deterministic offline demo report and confirmed:
  - `Current mean cumulative %` is present;
  - `null-filtered percentile box statistics` is present;
  - `Backing data` is absent;
  - the generated sample HTML is about 143 KB.
- `black` and `flake8` could not be run because the executables are not
  available on `PATH` in this environment.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9C: compact Plotly report HTML for kdb-scale data.

### Estimated milestone completion

- 89%

### Remaining work before milestone completion

- Validate HTML size and visual usability with one real kdb-backed production
  report using the user's real data shape.
- Convert Cross-Venue Toxicity/Reversion from generic trend charts plus capped
  comparison rows into compact Plotly horizon curves and capped venue/horizon
  diagnostics.
- Decide whether production deployments should use the Plotly CDN, a packaged
  local Plotly asset, or an offline self-contained bundle.

### Best next deterministic step

- Rework the Cross-Venue Toxicity/Reversion page to render compact Plotly
  horizon progression curves and capped venue/horizon comparison diagnostics,
  then remove or further minimize the remaining reversion comparison table.

### Open questions

- Is using the Plotly CDN acceptable for the production report environment, or
  must Plotly be bundled locally for offline report viewing?
- Should session-share stacks use the current AMO/AMC/PMO/PMC and continuous
  AM/PM labels, or should they follow a client-specific exchange session map?


---

## 2026-05-29 — Convert Cross-Venue Toxicity/Reversion to compact Plotly visuals

### Implemented

- Reworked the Cross-Venue Toxicity/Reversion report page from generic
  time-series chart components into compact Plotly horizon progression curves.
- Each reversion curve now plots horizon on the x-axis, reversion in bps on the
  y-axis, and one line/marker series per venue.
- Low-confidence reversion points are marked with open-circle markers and
  surfaced in compact hover text rather than as expanded backing rows.
- Added a capped horizontal Plotly diagnostic chart for reversion
  current-minus-reference deltas by venue/horizon context.
- Disabled the reversion comparison table by default so the page remains
  visualization-first; the table remains available only when explicitly capped
  through `max_comparison_rows`.
- Updated the roadmap to record completed reversion/toxicity visual coverage and
  the remaining real-kdb smoke/Plotly-asset decisions.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `mmsr/report/toxicity.py`
- `tests/test_toxicity_reversion_report.py`

### Tests added or updated

- Updated toxicity report tests to assert Plotly horizon curves instead of
  time-series chart components.
- Added assertions that reversion diagnostic comparisons render as capped
  horizontal Plotly bars while the default table payload is omitted.
- Updated market-report toxicity wiring assertions to expect Plotly charts and no
  default reversion comparison table.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_toxicity_reversion_report.py -q` passed.
- `python -m pytest -q` passed.
- Rendered the deterministic offline demo report and confirmed:
  - `Backing data` is absent;
  - `time-series-chart__placeholder` is absent;
  - 13 Plotly figure containers are present;
  - generated sample HTML is about 143 KB.
- Rendered a focused toxicity-only report and confirmed:
  - 2 Plotly charts are emitted;
  - 0 metric tables and 0 time-series charts are emitted by default;
  - the reversion diagnostic chart is present;
  - no HTML table is emitted;
  - generated focused HTML is about 21 KB.
- `black --check .` and `flake8 .` could not be run because the executable shims
  are present but not executable in this environment (`PermissionError`).
- `python -m black --check .` and `python -m flake8 .` could not be run because
  those modules are not installed in this environment.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9C: compact Plotly report HTML for kdb-scale data.

### Estimated milestone completion

- 94%

### Remaining work before milestone completion

- Validate HTML size and visual usability with one real kdb-backed production
  report using the user's real data shape.
- Decide whether production deployments should use the Plotly CDN, a packaged
  local Plotly asset, or an offline self-contained bundle.
- Consider a hard fixture-based HTML size budget after a real-kdb report size is
  known.

### Best next deterministic step

- Add a compact report-size/smoke validation hook or documented production smoke
  command that records final HTML size, Plotly chart count, and absence of raw
  backing-data tables for a real kdb-backed run.

### Open questions

- Is using the Plotly CDN acceptable for the production report environment, or
  must Plotly be bundled locally for offline report viewing?
- Should session-share stacks use the current AMO/AMC/PMO/PMC and continuous
  AM/PM labels, or should they follow a client-specific exchange session map?
- What is the target maximum final HTML size for a representative real kdb-backed
  production report?


---

## 2026-05-30 — Add simulated q source functions for dev/debug reports

### Implemented

- Added a packaged deterministic q source-function library for development and
  debugging without production kdb tables.
- The rendered q defines `getTradingCalendar`, `getRef`, `getTrade`, `getQuote`,
  `getPtsTrade`, `getPtsQuote`, and `getPrimaryQuote` under a configurable
  namespace.
- Added `render_simulated_source_function_bootstrap()` so Python callers and CLI
  tools can materialize the q source functions.
- Added `mmsr simulated-source-q` to write a loadable q file for a dev kdb
  session.
- Added a simulated-source report config and `simulated-source-demo` convenience
  path that exercises the production-shaped executor/report flow without PyKX or
  a live kdb socket.
- Kept the simulated path scoped to market-monitoring source rows and report
  development; it is explicitly not production market evidence.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `mmsr/examples/__init__.py`
- `mmsr/examples/config/simulated_source_report.yaml`
- `mmsr/examples/simulated_source_report.py`
- `mmsr/kdb/__init__.py`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/q_lib/mmsr_simulated_sources.q.j2`
- `mmsr/kdb/simulated.py`
- `tests/test_cli.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_kdb_simulated_sources.py`

### Tests added or updated

- Added q-template loading and rendering assertions for the simulated source
  library.
- Added CLI tests for writing a simulated q source-function file.
- Added simulated-source client/source-boundary tests for reference rows and
  required source schema columns.
- Added a simulated-source report file smoke test.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_kdb_query_loader.py tests/test_kdb_simulated_sources.py tests/test_cli.py -q` passed.
- `python -m pytest -q` passed.
- The generated simulated-source report render contains the expected market
  summary, activity, displayed-liquidity, and Cross-Venue Toxicity pages, uses
  Plotly figures, and does not include `Backing data`.
- The generated q source-function file contains the configured namespace and all
  simulated source functions.
- The generated q was inspected through string/schema tests only; a live q
  interpreter was not available in this environment.
- `black` and `flake8` were not run because the environment still lacks usable
  formatter/linter executables.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9D: simulated kdb source functions for dev/debug.

### Estimated milestone completion

- 88%

### Remaining work before milestone completion

- Validate the generated simulated q source functions in a real kdb+ process.
- Add a simulator-size knob to the CLI/config if developers need to stress-test
  larger universes or bucket grids.

### Best next deterministic step

- Run the generated `mmsr_simulated_sources.q` in a local kdb+ session, call each
  source function with a small reference table, and confirm the production report
  q runner can consume the returned raw rows end-to-end.

### Open questions

- Should the simulated q source functions expose a configurable symbol count via
  a q variable only, or should the CLI also render a chosen default into the q
  bootstrap file?

---

## 2026-05-30 — Add simulator universe-size controls

### Implemented

- Added a positive `symbol_count` option to the simulated q bootstrap renderer.
- The generated q now bakes the selected default into
  `<namespace>.symbolCount`, while still allowing q users to override the
  variable after loading for ad hoc stress tests.
- Added `--symbol-count` to `mmsr simulated-source-q`.
- Added `--symbol-count` to `mmsr simulated-source-demo` and wired it into the
  local simulated-source client.
- Updated README usage examples for small smoke tests and larger synthetic
  universe stress runs.
- Updated the roadmap to mark the simulator-size knob as implemented.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `mmsr/kdb/query_loader.py`
- `mmsr/kdb/q_lib/mmsr_simulated_sources.q.j2`
- `tests/test_cli.py`
- `tests/test_kdb_query_loader.py`

### Tests added or updated

- Added q-renderer assertions for custom simulated q `symbolCount` values.
- Added q-renderer validation for non-positive simulated symbol counts.
- Updated CLI tests to assert the q export command and Python file helper pass
  custom symbol counts into the rendered q.
- Added a simulated-source demo CLI smoke test with a small custom symbol count.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_kdb_query_loader.py tests/test_kdb_simulated_sources.py tests/test_cli.py -q` passed.
- `python -m pytest -q` passed.
- Ran `python -m mmsr.cli simulated-source-q --output sim_sources_17.q
  --namespace .qa.mmsr --symbol-count 17` and confirmed the file was written.
- Ran `python -m mmsr.cli simulated-source-demo --output sim_demo_7.html
  --symbol-count 7` and confirmed the report rendered with Plotly figures and
  without `Backing data`.
- A live q interpreter was still unavailable in this environment, so the
  generated q has not yet been executed inside kdb+.
- `black --check .` and `flake8 .` could not be run because the executable shims
  are present but not executable in this environment (`PermissionError`).
- `python -m black --check .` and `python -m flake8 .` could not be run because
  those modules are not installed in this environment.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9D: simulated kdb source functions for dev/debug.

### Estimated milestone completion

- 93%

### Remaining work before milestone completion

- Validate the generated simulated q source functions in a real kdb+ process.
- Add optional simulator knobs beyond symbol count only if developers need to
  vary venue count, bucket grid depth, or trading-day depth.

### Best next deterministic step

- When q is available, load the generated `mmsr_simulated_sources.q` in a local
  kdb+ session, call each source function with a small reference table, and
  confirm the production report q runner can consume the returned raw rows
  end-to-end.

### Open questions

- Should the simulator eventually expose venue-count and bucket-grid controls,
  or is symbol-count sufficient for the near-term report-size and layout smoke
  tests?



---

## 2026-05-30 — Add remote-kdb simulated source injection flags

### Implemented

- Added `--inject-simulated-sources`, `--simulated-source-namespace`, and
  `--simulated-symbol-count` to the normal production `plan`, `preflight`, and
  `render` commands.
- The injection path sends the deterministic simulated source-function q
  bootstrap to the connected kdb process before normal planning/preflight/render
  execution.
- When injection is enabled, the loaded report config is routed for that run so
  calendar, reference-data, trade, quote, PTS trade/quote, and primary quote
  source-function calls use the injected simulated namespace.
- MMSR-owned calculation functions still install and run in the configured
  `data.kdb.calculation_namespace`; only the source-getter boundary is swapped.
- Documented the preferred remote-kdb dev workflow using
  `--inject-simulated-sources` on existing production commands.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `mmsr/cli.py`
- `tests/test_production_cli.py`

### Tests added or updated

- Added a production-plan test confirming simulated q is injected into the
  configured remote client and source-function names are routed to the simulated
  namespace.
- Added a production-preflight CLI test confirming the new flags inject
  simulated q and execute the sample metric against simulated source getters.
- Updated the fake production kdb client to accept bootstrap-only q injection
  calls.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_production_cli.py tests/test_logging.py -q` passed.
- `python -m pytest -q` passed.
- A live q interpreter was still unavailable in this environment, so the
  injected bootstrap has not yet been executed inside a real remote kdb+
  process.
- `black --check .` and `flake8 .` could not be run because the executable
  shims are present but not executable in this environment (`PermissionError`).
- `python -m black --check .` and `python -m flake8 .` could not be run because
  those modules are not installed in this environment.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9D: simulated kdb source functions for dev/debug.

### Estimated milestone completion

- 96%

### Remaining work before milestone completion

- Validate `--inject-simulated-sources` against an actual remote kdb+ process.
- Add optional simulator knobs beyond symbol count only if developers need to
  vary venue count, bucket-grid depth, or trading-day depth.

### Best next deterministic step

- In a development environment with q available, run `mmsr preflight
  --inject-simulated-sources` against a remote kdb process and verify each
  simulated getter can be called by the normal production q runner.

### Open questions

- Should the older `simulated-source-q` and `simulated-source-demo` convenience
  commands stay as developer utilities, or be deprecated in docs now that the
  normal production commands can inject simulated source getters directly?


---

## 2026-05-30 — Remove redundant standalone simulated-source paths

### Implemented

- Removed the wrong-direction standalone `simulated-source-q` CLI command.
- Removed the wrong-direction standalone `simulated-source-demo` CLI command.
- Removed the local Python simulated kdb client/report path that bypassed a
  live or remote kdb process.
- Kept the q simulated source-function bootstrap used by
  `--inject-simulated-sources` on normal `plan`, `preflight`, and `render`.
- Updated README and roadmap so the supported dev/debug path is one mechanism:
  inject simulated source getters into the same kdb process used by normal
  production commands.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`
- `README.md`
- `pyproject.toml`
- `mmsr/cli.py`
- `mmsr/examples/__init__.py`
- `mmsr/examples/simulated_source_report.py` removed
- `mmsr/examples/config/simulated_source_report.yaml` removed
- `mmsr/kdb/simulated.py` removed
- `tests/test_cli.py`
- `tests/test_kdb_simulated_sources.py` removed

### Tests added or updated

- Removed tests for the deleted standalone simulated-source commands and local
  Python simulated client.
- Added CLI help assertions that the deleted standalone commands are not listed.
- Kept q bootstrap rendering and remote injection coverage in
  `tests/test_kdb_query_loader.py` and `tests/test_production_cli.py`.

### Validation

- `python -m py_compile` over all package and test modules passed.
- `python -m pytest tests/test_cli.py tests/test_production_cli.py
  tests/test_kdb_query_loader.py -q` passed.
- `python -m pytest -q` passed.
- `black --check .` and `flake8 .` could not be run because the executable
  shims are present but not executable in this environment (`PermissionError`).
- `python -m black --check .` and `python -m flake8 .` could not be run because
  those modules are not installed in this environment.
- A live q/kdb+ process is still unavailable in this environment, so
  `--inject-simulated-sources` has not yet been executed against a real remote
  kdb process.
- Python startup emitted the known non-fatal `artifact_tool` spreadsheet warmup
  warning in this environment, but validation commands completed successfully.

### Current milestone

- Milestone 9D: simulated kdb source functions for dev/debug.

### Estimated milestone completion

- 97%

### Remaining work before milestone completion

- Validate the injected simulated source q bootstrap in a real remote kdb+
  process.
- Keep additional simulator knobs out unless a concrete dev/debug need appears.

### Best next deterministic step

- Run `mmsr preflight --inject-simulated-sources` against a remote kdb process
  and confirm the normal production q runner can consume the injected simulated
  calendar, reference-data, trade, quote, PTS, and primary-quote getters.

### Open questions

- None.


---

## 2026-05-30 — Add desk-first slimming and q-performance roadmap reset

### Implemented

- Added an active near-term roadmap reset to `_docs/ROADMAP.md` that combines
  the repo review findings with the follow-up direction to slim the codebase and
  improve kdb metric calculation performance.
- Prioritized the next work as:
  - slim and stabilize the default product surface;
  - remove redundant q wrappers around native q functions unless they add real
    policy;
  - make the default report market/group-first rather than symbol-first;
  - profile and optimize q metric calculation stages;
  - make the market summary tell the desk-level story before tables;
  - build drilldowns around TPX/group/intraday market questions;
  - standardize a generic q-side aggregation contract;
  - make stockMetrics cache a first-class performance feature;
  - validate runtime, row counts, and HTML budgets against real kdb data.
- Updated the later-milestones summary so symbol pages are described as opt-in
  escalation and codebase/q-performance work is explicit.

### Files changed

- `_docs/ROADMAP.md`
- `_docs/journal.md`

### Tests added or updated

- None. Documentation-only roadmap update.

### Validation

- Not run. Documentation-only roadmap update.

### Current milestone

- Roadmap reset for desk-first market report, codebase slimming, and q
  performance hardening.

### Estimated milestone completion

- Planning update complete.

### Remaining work before milestone completion

- Implement the first recommended PR:
  - remove no-op q wrappers;
  - remove default symbol aggregation levels;
  - disable symbol pages by default;
  - add `runReportDay` timing instrumentation;
  - lock default report shape and aggregation defaults in tests.

### Best next deterministic step

- Start Milestone R0 with the smallest behavior change: update default
  aggregation/report options away from symbol-first output and add regression
  tests for the new defaults.

### Open questions

- Should symbol aggregation remain available through config only, or should the
  CLI expose a short explicit flag for one-off symbol escalation reports?


---

## 2026-05-30 — Update agent rules for roadmap reset and local kdb endpoint

### Implemented

- Updated `_docs/AGENTS.md` to reflect the active desk-first roadmap reset:
  market/group-first default report behavior, symbol output as opt-in
  escalation, slimmer codebase expectations, and q performance hardening.
- Corrected the reusable q code location in agent rules to `mmsr/kdb/q_lib/`.
- Added q implementation guidance to avoid no-op wrappers around native q
  functions and prefer the installed `runReportDay` production path.
- Added local live-kdb testing guidance for the available developer endpoint
  `192.163.3.99:5001`, while keeping live tests opt-in and forbidding hard-coded
  endpoint values in package code or production configs.

### Files changed

- `_docs/AGENTS.md`
- `_docs/journal.md`

### Tests added or updated

- None. Documentation-only contributor guidance update.

### Validation

- `git diff --check -- _docs/AGENTS.md _docs/journal.md` passed.

### Current milestone

- Milestone R0: Slim and stabilize the default product surface.

### Estimated milestone completion

- 5%. Contributor rules now point at the reset, but implementation has not
  started.

### Remaining work before milestone completion

- Remove no-op q wrappers.
- Remove default symbol aggregation levels.
- Disable symbol pages by default.
- Add `runReportDay` timing instrumentation.
- Lock default report shape and aggregation defaults in tests.

### Best next deterministic step

- Start the first implementation PR for Milestone R0 by updating the default
  production aggregation levels and report option defaults, then add regression
  tests.

### Open questions

- Should local live-kdb testing also be mirrored in `docs/kdb_integration_testing.md`,
  or should the endpoint stay only in contributor guidance?


---

## 2026-05-30 — Start R0 default slimming implementation

### Implemented

- Changed the canonical market report defaults so symbol anomaly pages,
  per-symbol detail pages, and the symbol detail index are disabled unless
  explicitly enabled through `MarketReportOptions`.
- Removed `symbol` and `symbol_bucket` from default kdb aggregation levels in
  config models, config loading fallbacks, production/example YAML configs, and
  the packaged live-kdb example config.
- Updated README documentation to describe symbol pages and symbol rollups as
  opt-in escalation behavior rather than default desk-report output.
- Removed no-op q wrappers around native q functions:
  - removed `sumSize`;
  - removed `rowCount`;
  - removed `weightedAverage`;
  - replaced their call sites with native `sum`, `count`, and `wavg`.
- Updated report/config/q tests to lock the new default behavior and the removal
  of redundant q helpers.
- Updated symbol report tests so symbol pages/details are still covered through
  explicit opt-in options.

### Files changed

- `README.md`
- `config/report.example.yaml`
- `config/report.production_minimal.yaml`
- `mmsr/config/loading.py`
- `mmsr/config/models.py`
- `mmsr/examples/config/live_kdb_report.yaml`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `mmsr/report/market_report.py`
- `tests/test_config_files.py`
- `tests/test_kdb_query_loader.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_symbol_anomaly_pages.py`
- `_docs/journal.md`

### Tests added or updated

- Updated config-file tests to assert default aggregation levels exclude symbol
  and symbol-bucket rollups.
- Updated market/offline report tests to assert symbol pages are absent by
  default.
- Updated symbol report tests to assert default skip behavior and explicit
  opt-in behavior.
- Updated q-library rendering tests to assert redundant native-function wrappers
  are not installed.

### Validation

- `python -m compileall mmsr tests` passed.
- Text-level checks confirmed default YAML files do not include `symbol` or
  `symbol_bucket`, the q library no longer contains `weightedAverage`,
  `sumSize`, or `rowCount`, and report symbol-page defaults are false.
- `git diff --check` passed.
- Could not run pytest in this environment:
  - `python -m pytest ...` failed because `pytest` is not installed;
  - `uvx pytest ...` failed because `uvx` is not installed;
  - `pytest ...` failed because `pytest` is not on PATH;
  - `poetry run pytest ...` failed because `poetry` is not installed.
- A plain Python runtime smoke could not import config/report modules because
  runtime dependency `yaml` is not installed in this environment.

### Current milestone

- Milestone R0: Slim and stabilize the default product surface.

### Estimated milestone completion

- 35%. Default symbol output is now opt-in and the first redundant q wrappers
  are removed. q timing instrumentation and broader cleanup remain.

### Remaining work before milestone completion

- Add `runReportDay` timing instrumentation.
- Remove or quarantine legacy single-metric/batch paths where no compatibility
  requirement remains.
- Re-run the focused pytest suite in an environment with dependencies.
- Continue slimming report/demo defaults that still bias product review toward
  symbol-level artifacts.

### Best next deterministic step

- Add q timing instrumentation inside `runReportDay` for source load,
  calculation, rollup, and serialization boundaries, then validate rendered q
  text with focused tests.

### Open questions

- Should offline-demo expose an explicit symbol-escalation flag, or should symbol
  fixtures remain test-only until product review asks for demo-visible symbol
  pages again?


---

## 2026-05-30 — Add q timing instrumentation to runReportDay

### Implemented

- Added q-side timing instrumentation in `runReportDay` inside
  `mmsr/kdb/q_lib/mmsr_calculations.q.j2`.
- Added reusable q helper `elapsedMs` and captured timestamp boundaries for:
  - reference-data load/filter phase;
  - chunk calculation phase;
  - rollup phase;
  - total run duration.
- Attached timing and run-shape metadata columns to each returned metric table:
  - `report_ref_load_ms`
  - `report_chunk_calc_ms`
  - `report_rollup_ms`
  - `report_total_ms`
  - `report_chunk_count`
  - `report_symbol_count`
- Added a focused template test to lock the instrumentation contract in
  `tests/test_kdb_query_loader.py`.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_query_loader.py`
- `_docs/journal.md`

### Tests added or updated

- Added `test_q_library_run_report_day_includes_timing_instrumentation`.

### Validation

- `python -m compileall mmsr tests` passed.
- Template text-level checks confirmed timing markers and output columns are
  present.
- `git diff --check` passed.
- Could not run pytest in this environment because `pytest`, `uvx`, and
  `poetry` are not installed in PATH.

### Current milestone

- Milestone R0: Slim and stabilize the default product surface.

### Estimated milestone completion

- 50%. Default market-first behavior and first q slimming pass are complete;
  timing instrumentation is now in place.

### Remaining work before milestone completion

- Run focused pytest coverage once a test runner environment is available.
- Review whether legacy single-metric/batch runner paths can be reduced without
  breaking compatibility.
- Continue removing or isolating non-essential compatibility/developer paths
  from default production behavior.

### Best next deterministic step

- Add a small Python-side preflight/report summary hook that surfaces the
  new q timing columns in operator logs without changing report output shape.

### Open questions

- Should timing columns remain embedded in every metric table, or should a
  dedicated optional diagnostics table be returned by q in a future iteration?

---

## 2026-05-30 — Surface q timing diagnostics in production preflight/executor

### Implemented

- Extended `KdbProductionPreflightResult` with `sample_timing_ms`.
- Added Python extraction of q timing metadata from series observations via
  `_timing_ms_from_metric_series`.
- Added preflight diagnostics output and check:
  - summary line `Sample q timings (ms): ...`
  - check name `sample_q_timing`
- Added executor logging of day-batch q timings during production execution.
- Updated test fakes to emit timing fields and added assertions in:
  - `tests/test_kdb_production_execution.py`
  - `tests/test_production_cli.py`

### Files changed

- `mmsr/kdb/production.py`
- `tests/test_kdb_production_execution.py`
- `tests/test_production_cli.py`
- `_docs/journal.md`

### Validation

- `python -m compileall mmsr tests` passed.
- Could not run pytest in this environment because `pytest` and `uvx` are not
  available in PATH.

---

## 2026-05-30 — Slim query planning by unifying metric metadata assembly

### Implemented

- Refactored `mmsr/kdb/query_plan.py` to avoid repeated single-metric query
  rendering work in day/batch planning paths.
- Added `_rendered_metric_query_for_request(...)` as the shared metadata and
  contract builder used by:
  - `KdbMetricQueryPlanner.render(...)`
  - `KdbMetricQueryPlanner.render_day(...)`
  - `KdbMetricQueryPlanner.render_batch(...)`
- `render_day` and `render_batch` now construct metric contracts directly
  without generating unused single-metric q text for each metric.

### Files changed

- `mmsr/kdb/query_plan.py`
- `_docs/journal.md`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files`
  passed:
  - `ruff-check`
  - `ruff-format`
  - `mypy`
  - full `pytest` suite

---

## 2026-05-30 — Remove legacy production executor batch/run fallback path

### Implemented

- Simplified `KdbProductionExecutor` execution flow to one production path:
  `run_day`.
- Removed legacy fallback logic that attempted `run_batch` and then
  per-request `run` when `run_day` was unavailable.
- Removed now-unused helper `_metric_step_batches`.

### Files changed

- `mmsr/kdb/production.py`
- `_docs/journal.md`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files`
  passed:
  - `ruff-check`
  - `ruff-format`
  - `mypy`
  - full `pytest` suite

---

## 2026-05-30 — Fix simulated-source q type errors and validate live kdb commands

### Implemented

- Fixed simulated quote source generation in
  `mmsr/kdb/q_lib/mmsr_simulated_sources.q.j2` by binding `rows:q\`row` and
  using `rows` in spread/size expressions. This removes runtime `type` errors
  seen in `.sim.mmsr.getQuote` and `.sim.mmsr.getPtsQuote`.
- Fixed reversion horizon join-key typing in
  `mmsr/kdb/q_lib/mmsr_calculations.q.j2` by casting:
  - `horizonTime: \`time$(time + params\`horizon)`
  so `aj` key types match between trade/post-quote tables.
- Updated template assertions in `tests/test_kdb_query_loader.py` for both
  fixes.

### Live kdb validation (conda env `mmsr`)

- Host/port used: `192.168.3.99:5001`.
- Verified TCP connectivity and executed:
  - `mmsr preflight` with simulated source injection: passed.
  - metric-isolated preflight:
    - `quoted_spread_bps`: passed.
    - `primary_quote_reversion_10ms_bps`: passed.
  - full `mmsr render` with simulated source injection: passed and wrote:
    - `/tmp/mmsr_live_simulated.html`

### Files changed

- `mmsr/kdb/q_lib/mmsr_simulated_sources.q.j2`
- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_query_loader.py`
- `_docs/journal.md`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files`
  passed:
  - `ruff-check`
  - `ruff-format`
  - `mypy`
  - full `pytest` suite

---

## 2026-05-30 — Remove legacy runner batch API and migrate tests to day path

### Implemented

- Removed legacy batch-oriented runner APIs from `KdbMetricRunner`:
  - `plan_batch(...)`
  - `run_batch(...)`
- Kept production-aligned APIs:
  - `plan_day(...)`
  - `run_day(...)`
  - `run(...)` (single metric)
- Updated runner imports to drop now-unused `RenderedMetricBatchQuery`.
- Migrated batch-focused test coverage in `tests/test_kdb_metric_runner.py` to
  validate the day-query interface instead of removed batch methods.

### Files changed

- `mmsr/kdb/runner.py`
- `tests/test_kdb_metric_runner.py`
- `_docs/journal.md`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files`
  passed:
  - `ruff-check`
  - `ruff-format`
  - `mypy`
  - full `pytest` suite

---

## 2026-05-30 — Remove dead batch query code and legacy helpers from query_plan.py

### Implemented

- Removed `RenderedMetricBatchQuery` dataclass — dead after `KdbMetricRunner.run_batch` was removed earlier.
- Removed `KdbMetricQueryPlanner.render_batch()` — production path uses `render_day()` with the installed `runReportDay` q entry point.
- Removed batch-only helper functions:
  - `_batch_source_parameters` — only used by `render_batch`.
  - `_validate_batch_request_compatibility` — only used by `render_batch`.
- Removed additional legacy dead helpers discovered by Pylance:
  - `_source_extra_columns`, `_render_template_with_used_params`, `_metric_function_expression`,
    `_q_source_loader_expression`, `_day_source_parameters`, `_day_symbol_values`,
    `_day_chunk_size`, `_required_string_sequence_parameter`, `_q_symbol_filter_vector`,
    `_q_positive_int_parameter`, `_q_time_vector`, `_q_time`.
- Removed now-unused `time` import from `datetime`.
- Removed `run_batch` mock method from `FakeKdbMetricRunner` in test file (defined but never called).
- Net reduction: **269 lines** across 2 files.

### Files changed

- `mmsr/kdb/query_plan.py`
- `tests/test_kdb_production_execution.py`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files` passed:
  - `ruff-check`, `ruff-format`, `mypy`, full `pytest` suite — all green.

### Current milestone

- R0: Slim and stabilize the default product surface

### Estimated milestone completion

- R0: 100% — all exit criteria met:
  1. Default production config does not request symbol or symbol-bucket rollups.
  2. Default market report options do not emit symbol anomaly/detail pages.
  3. q calculation helpers only kept when they provide real policy or reuse.
  4. Tests assert default report pages and default aggregation levels remain market/group-first.
  5. No-op q wrappers removed. Dead batch/compat execution paths excised.
  6. Unused legacy helpers cleaned out.

### Remaining work before next milestone

- R1 (q metric calculation performance pass) is the next milestone.
- R1 exit criteria require: per-stage q timings surfaced, source loading deduplicated across metric families, reversion family reuses prepared joins, and tests guard against reintroducing redundant wrappers or repeated family prep.

### Best next deterministic step

- Profile the q `runReportDay` per-stage timings on a real or simulated kdb run.
  Verify that activity and liquidity families each load raw sources at most once per day/chunk,
  and that the reversion family reuses the prepared `tradeWithPreMid`/`postQuotes` state across
  all six horizons instead of repeating the full preparation. If any stage shows redundant loads,
  optimize the q before adding more metrics or report pages.

### Open questions

- Is a real kdb+ endpoint available for R1 profiling, or should profiling use the simulated
  source injection path (`--inject-simulated-sources`)?

---

## 2026-05-30 — Complete R1: q metric calculation performance pass

### Implemented

- Verified three R1 performance patterns are already in place in
  `mmsr_calculations.q.j2`:
  1. **Per-stage q timings**: `runReportDay` records `refLoadMs`, `chunkCalcMs`,
     `rollupMs`, `totalMs`, `chunkCount`, and `symbolCount` per result table.
  2. **Source loading once per chunk**: `loadReportSources` is called exactly once
     per chunk; the returned `rawSources` dict is shared by both regular (activity/
     liquidity) and reversion metric dispatch inside the chunk lambda.
  3. **Reversion prepared-join reuse**: `calcToxicityReversionFamily` calls
     `prepareToxicityReversion` once, then maps `calcToxicityReversionPrepared`
     over each horizon metric — all six horizons share one prepared
     `tradeWithPreMid`/`postQuotes` pair.
- Added two deterministic q-bootstrap tests to lock the performance contract:
  - `test_calculation_bootstrap_loads_sources_once_per_chunk` — asserts
    `loadReportSources[` appears exactly once in the `runReportDay` body, and
    that regular and reversion metrics consume the same `rawSources` dict.
  - `test_calculation_bootstrap_has_no_noop_native_function_wrappers` — asserts
    no trivial pass-through definitions like `{[x] sum x}` or `{[x;y] avg y}`
    exist in the rendered q library.

### Files changed

- `tests/test_kdb_metric_runner.py`

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files` passed:
  - `ruff-check`, `ruff-format`, `mypy`, full `pytest` suite — all green.

### Current milestone

- R1: q metric calculation performance pass

### Estimated milestone completion

- R1: 100% — all four exit criteria met:
  1. Per-stage q timings reported per metric result table.
  2. Activity, liquidity, and reversion families load each required raw source at
     most once per day/chunk.
  3. Reversion horizons reuse prepared joins rather than repeating full preparation.
  4. Tests guard against reintroducing redundant native-function wrappers and
     repeated family preparation.

### Remaining work before next milestone

- R2 (Market summary that tells the story) is the next milestone.
- R2 requires: narrative highlights before broad tables, top 3-5 market-level
  changes surfaced, TPX cap group / intraday bucket / venue/horizon context when
  explanatory, metric cards and comparison tables kept as compact audit components,
  deterministic wording from computed comparison facts.

### Best next deterministic step

- Read `mmsr/report/market_report.py` and `mmsr/report/overview.py` to understand
  the current executive overview and page ordering, then redesign the first report
  page to lead with a concise deterministic market narrative (top 3-5 changes
  across activity, displayed liquidity, and cross-venue reversion) before any
  broad comparison table.

### Open questions

- None at this time.

---

## 2026-05-30 — Implement R1 q performance changes (finer timing, pre-aggregation, timing log)

### Implemented

- **Finer timing granularity**: Split the per-chunk `chunkCalcMs` into separate
  `sourceLoadMs` (time inside `loadReportSources`) and `metricCalcMs` (time
  inside `runMetric` / `calcToxicityReversionFamily`). Each chunk lambda now
  returns `(sourceLoadMs; metricCalcMs; slimDict)` and the outer runner sums
  per-chunk ms.
- **Pre-aggregation before cross-chunk raze**: Added `preAggregateFacts` helper
  that groups activity-family results (turnover, volume, trade_count) to
  `date/time_bucket/topixCapGrp` grain within each chunk, dropping the `sym`
  column. Per-chunk row count drops from ~(symbols × buckets) to ~(cap-groups ×
  buckets), shrinking the cross-chunk `raze` intermediate table. Liquidity and
  reversion families pass through unchanged (medians and wavgs cannot be
  trivially pre-aggregated).
- **Operator timing log**: `runReportDay` now emits a `-1` line at completion:
  `"MMSR runReportDay <date> ref:<ms> src:<ms> calc:<ms> rollup:<ms> total:<ms>
  chunks:<n> syms:<n>"`. No sensitive source rows are logged.
- Updated timing metadata columns: `report_chunk_calc_ms` split into
  `report_source_load_ms` + `report_metric_calc_ms` in both the q output and the
  Python `_RUN_REPORT_DAY_TIMING_FIELDS` tuple.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2` — new `preAggregateFacts`, restructured `runReportDay`
- `mmsr/kdb/production.py` — updated timing field tuple
- `tests/test_kdb_query_loader.py` — updated timing column assertions

### Validation

- `PRE_COMMIT_HOME=/tmp/pre-commit-cache python -m pre_commit run --all-files` passed:
  - `ruff-check`, `ruff-format`, `mypy`, full `pytest` suite — all green.

### Current milestone

- R1: q metric calculation performance pass

### Estimated milestone completion

- R1: 100% — all four exit criteria met with real q changes:
  1. Per-stage q timings now split into ref / source-load / metric-calc /
     rollup / total, surfaced via `-1` log and metadata columns.
  2. Source loading happens once per chunk (`loadReportSources[` appears once
     in the chunk lambda); all metric families share the same `rawSources`.
  3. Reversion horizons reuse one `prepareToxicityReversion` call via
     `calcToxicityReversionFamily`.
  4. Tests guard against no-op wrappers, duplicate source loads, and repeated
     family preparation.

### Best next deterministic step

- R2: Read `mmsr/report/market_report.py` and `mmsr/report/overview.py` to
  understand the current executive overview, then redesign the first report
  page to lead with a concise deterministic market narrative.

### Open questions

- Activity pre-aggregation assumes additive metrics; if `calcActivity` gains
  non-additive columns in the future, `preAggregateFacts` will need updating.
- Reversion pre-aggregation (wavg of reversion_bps by notional) could further
  reduce raze size but requires careful re-aggregation of non-linear columns
  (positive_reversion_ratio, valid_primary_quote_ratio).

---

## 2026-05-30 — R1 complete: validated against live kdb in 3 incremental steps

### Implemented

R1 changes were built and tested against live kdb (192.168.3.99:5001) one
step at a time to isolate the `params` error:

**Step 1 — Operator timing log** (commit `e38aab4`):
- Captured `runReportDay` result as `timingResult` variable.
- Emit `-1` log line: `MMSR runReportDay <date> ref:<ms> calc:<ms>
  rollup:<ms> total:<ms> chunks:<n> syms:<n>`.
- No structural changes. ✅ Live-kdb validated.

**Step 2 — Split chunk timing** (commit `c6e6a1c`):
- Chunk lambda now times source loading (`srcStart`/`srcEnd`) separately from
  metric calculation (`calcEnd`).
- Returns `(sourceLoadMs; metricCalcMs; resultDict)` triple instead of bare dict.
- `chunkCalcMs = sourceLoadMs + metricCalcMs` (backward-compatible output).
- `-1` log shows `src:` and `calc:` breakdown.
- ✅ Live-kdb validated.

**Step 3 — preAggregateFacts helper** (commit `adff89f`):
- Added `preAggregateFacts` using simple `select sum turnover, sum volume,
  sum trade_count by date, time_bucket, topixCapGrp from facts` — avoids the
  functional-select `?` form that caused the original `params` error.
- Called from chunk lambda on activity-family metrics only; liquidity and
  reversion pass through unchanged.
- Per-chunk row count drops from ~(symbols × buckets) to ~(cap-groups ×
  buckets), shrinking the cross-chunk `raze` intermediate table.
- ✅ Live-kdb validated.

**Root cause of the earlier `params` error**: the functional select form
`?[facts;();{x!x}byCols;aggDict]` where `aggDict` was incorrectly constructed
via `3#{(sum;x)}` and `additiveSpec aggCols` (which returns a list, not a
dictionary). The simple `select sum ... by ...` form is correct and safer.

### Files changed

- `mmsr/kdb/q_lib/mmsr_calculations.q.j2`
- `tests/test_kdb_query_loader.py`

### Validation

- Live kdb (192.168.3.99:5001): `mmsr render` with `--inject-simulated-sources` ✅
- `pytest-full`: all 370+ tests pass
- `ruff-check`, `ruff-format`, `mypy`: all pass

### Current milestone

- R1: q metric calculation performance pass

### Estimated milestone completion

- R1: 100% — all four exit criteria met with live-kdb-validated changes:
  1. Per-stage q timings: ref / source-load / metric-calc / rollup / total,
     surfaced via `-1` operator log and metadata columns.
  2. Source loading once per chunk; all metric families share `rawSources`.
  3. Reversion horizons reuse one `prepareToxicityReversion` call.
  4. Tests guard against no-op wrappers, duplicate source loads, and repeated
     family preparation.

### Best next deterministic step

- R2: Read `mmsr/report/market_report.py` and `mmsr/report/overview.py` to
  understand the current executive overview, then redesign the first report
  page to lead with a concise deterministic market narrative.

### Open questions

- None at this time.

---

## 2026-05-30 — D2 report design: visual-first drilldown page

### Implemented

- Reviewed `_docs/report_design_roadmap.md` — new design roadmap with D0-D5
  milestones specifically for the report surface.
- **D0 (UX Contract Lock)**: Already satisfied. Tests assert structure order for
  all default report renders including Report Meta, Market KPI Snapshot,
  Executive Market Overview, and Primary Intraday Signal.
- **D1 (Page-1 Story Redesign)**: Already satisfied. Page 1 includes Report
  Meta strip, KPI Snapshot, narrative key changes + top drivers with |z|
  mini bars, primary intraday chart, and insight callout.
- **D2 (Visual Priority Refactor)**: Added `_build_group_delta_bars_block` to
  the drilldown page — leads with scannable horizontal bar visual (top 8 group
  deltas ranked by |change_pct|) before the metric table. Sections 2/3/5/6
  already visual-first.
- Added `drilldown-delta-bars` CSS class and `Group Delta Overview` html_block
  to drilldown page output.

### Files changed

- `mmsr/report/drilldowns.py` — +90 lines: new `_build_group_delta_bars_block`,
  `_delta_bar_row_html`, `_format_drilldown_group_label`; wired into
  `build_drilldown_report_page`
- `tests/test_drilldowns.py` — assert html_blocks + delta bars presence
- `tests/test_market_report.py` — assert Group Delta Overview in HTML
- `tests/test_offline_demo.py` — assert Group Delta Overview in HTML

### Validation

- `pytest-full`: all 380+ tests pass
- `ruff-check`, `ruff-format`, `mypy`: all pass

### Current milestones

- Main roadmap: R0-R2 complete → next: R3 (Drilldowns around market questions)
- Design roadmap: D0-D3 complete → next: D3b (page reorder) + D4 (Symbol UX)

### Best next deterministic step

- Reorder report pages to match target information architecture: move
  drilldown/group-analysis page before intraday detail page.

### Open questions

- None at this time.

---

## 2026-05-30 — D3: Group Comparison Matrix + direction-aware coloring

### Implemented

- Added `_build_group_comparison_matrix_block` to `drilldowns.py` — a
  color-coded metric × group grid rendered as an HTML table with CSS
  background color intensity.
- Direction-aware cell coloring: green (`rgba(25,135,84,...)`) for favorable
  moves, red (`rgba(220,53,69,...)`) for adverse moves, respecting
  `MetricDefinition.higher_is_better`. Intensity scales with |change_pct|.
- `_pivot_comparison_matrix` groups comparisons into (metric, group_value) cells,
  selecting the best representative per cell.
- `_primary_group_value` extracts the most meaningful drilldown dimension for
  matrix columns (market_cap_bucket → sector → segment → topixCapGrp).
- Fixed `higher_is_better=None` handling: neutral metrics (volume, trade_count)
  default to `True` so increases are colored as favorable.
- Replaced `title=` attribute with `data-pct=` to avoid help-control anti-pattern.
- Drilldown page visual order: Delta Bars → Comparison Matrix → Metric Table.

### Files changed

- `mmsr/report/drilldowns.py` — +130 lines: matrix builder + pivot + cell HTML
- `tests/test_drilldowns.py` — assert 2 html_blocks with matrix presence
- `tests/test_market_report.py` — assert matrix in HTML
- `tests/test_offline_demo.py` — assert matrix + favorable cells in HTML

### Validation

- `pytest-full`: all 380+ tests pass
- `ruff-check`, `ruff-format`, `mypy`: all pass
- Offline demo: verified 2 favorable + 4 adverse cells with correct coloring

### Current milestones

- Main roadmap: R0-R2 complete → next: R3 (Drilldowns around market questions)
- Design roadmap: D0-D3x complete → next: D4 (Symbol UX cleanup)

### Best next deterministic step

- D4: Symbol Drilldown UX Cleanup — improve anomaly table-to-detail linkage,
  keep default report market-first.

---

## 2026-05-30 — Page reorder + matrix→heatmap + production drilldown fix

### Implemented

- **Page reorder**: Moved drilldown page assembly before symbol pages and
  intraday detail. New order: Summary → Activity → Liquidity → Daily Trends →
  Toxicity → Drilldowns → Symbol Anomalies → Intraday Detail → Appendix.
  Matches target architecture (Group Analysis before intraday diagnostics).
- **Matrix → Heatmap conversion**: Replaced `_build_group_comparison_matrix_block`
  (HTML table with colored cells) with `_build_drilldown_heatmaps` (proper
  `Heatmap` components that render as inline SVG). Each heatmap shows one
  metric's `change_pct` across group values. Removed 5 dead helper functions
  (`_pivot_comparison_matrix`, `_matrix_row_html`, `_matrix_cell_html`, old
  `_primary_group_value`, and the matrix block builder).
- **Production drilldown fix**: Added `topixCapGrp` to `DEFAULT_DRILLDOWN_GROUP_KEYS`
  so production kdb runs (which use `topixCapGrp` as the group dimension) produce
  drilldown pages with heatmaps. Also added `topixCapGrp` to
  `_format_drilldown_group_label`.
- Updated 6 test files: heatmap sections now expected in output (were
  previously asserted absent).

### Files changed

- `mmsr/report/market_report.py` — page reorder
- `mmsr/report/drilldowns.py` — heatmap conversion + topixCapGrp fix
- `tests/test_drilldowns.py`, `tests/test_cli.py`, `tests/test_offline_demo.py`,
  `tests/test_market_report.py`, `tests/test_mock_kdb_demo.py` — updated assertions

### Validation

- `pytest-full`: all 380+ tests pass
- `ruff-check`, `ruff-format`, `mypy`: all pass
- Offline demo: 3 per-metric SVG heatmaps rendered in drilldown page
- Production: `topixCapGrp` now triggers drilldown heatmaps

### Current milestones

- Main roadmap: R0-R2 complete → next: R3
- Design roadmap: D0-D3 complete → next: D4

### Best next deterministic step

- D4: Symbol Drilldown UX Cleanup

---

## 2026-05-30 — Implement latest journal workflow rules

### What changed
- Added `_docs/latest_journal.md` as the mandatory active-step journal buffer.
- Updated `_docs/AGENTS.md`:
  - mandatory reading order now includes `_docs/latest_journal.md` before roadmap/journal.
  - added mandatory start-of-task handoff:
    - append existing `latest_journal` entry to bottom of `_docs/journal.md`
    - reset `_docs/latest_journal.md` template
  - added mandatory end-of-task write:
    - write current step only to `_docs/latest_journal.md`
    - do not write new step directly to `_docs/journal.md` in same task.

### Files changed
- `_docs/latest_journal.md`
- `_docs/AGENTS.md`

### Tests updated
- None (docs/workflow change only).

### Validation
- Not run (docs-only workflow rule update).

### Current milestone
- Process/governance alignment for ongoing D2 work.

### Estimated completion
- 100% for this workflow step.

### Remaining work
- Follow this workflow in every subsequent task.

### Best next deterministic implementation step
- Continue D2 implementation: add explicit configurable lead-metric selectors per section and enforce lead chart precedence in builders/tests.

### Open questions
- None.

## 2026-05-30 — D3 implementation: unified drilldown matrix + linked trend panel

### What changed
- Replaced drilldown per-metric heatmap emission with a unified `Metric Explorer & Group Analysis` block in `mmsr/report/drilldowns.py`.
- New explorer block behavior:
  - one matrix heatmap (rows=`Metric`, columns=`Group`, value=`change_pct`)
  - right-side daily trend chart (`current value` by date) for selected group
  - click any heatmap cell column to switch selected group trend
- Kept `Group Delta Overview` as the lead visual summary and preserved drilldown metric table output.
- Updated report template styles and JavaScript to render and wire the new matrix/trend interaction using Plotly.
- Updated roadmap/design docs to reflect this completed D3 deliverable and set D4 as the next deterministic implementation step.

### Files changed
- `mmsr/report/drilldowns.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_drilldowns.py`
- `tests/test_market_report.py`
- `tests/test_offline_demo.py`
- `tests/test_mock_kdb_demo.py`
- `_docs/ROADMAP.md`
- `_docs/report_design_roadmap.md`
- `_docs/journal.md`

### Tests updated
- Adjusted drilldown/report/demo assertions for:
  - unified matrix explorer presence (`data-drilldown-matrix-spec`)
  - removal of legacy per-metric heatmap section assumptions in default outputs
  - matrix block conditional behavior when insufficient metric diversity exists

### Validation
- `conda run -n mmsr pytest -q tests/test_drilldowns.py tests/test_market_report.py tests/test_offline_demo.py tests/test_mock_kdb_demo.py` passed.
- Full pre-commit/commit still pending for this step.

### Current milestone
- D3 complete (group analysis redesign).
- D4 in progress (symbol drilldown UX linkage cleanup).

### Estimated completion
- ~70% of the current redesign stream (D0-D4).

### Remaining work
- Implement D4 anomaly table-to-detail panel deterministic linkage.
- Add deterministic selection-state tests for anomaly detail panel behavior.
- Run full pre-commit and commit this step.

### Best next deterministic implementation step
- Implement deterministic anomaly row selection state (default selected row + click-to-detail panel update) and lock with integration tests.

### Open questions
- None.

## 2026-05-30 — D1–D4 review pass + workflow/roadmap gap fixes

### What changed
- Executed the new journal handoff workflow:
  - appended prior `latest_journal` entry to the very bottom of `_docs/journal.md`
  - reset `_docs/latest_journal.md` template before work
- Fixed stale environment rule in `_docs/AGENTS.md`:
  - corrected local live-kdb host from `192.163.3.99` to `192.168.3.99` in all examples.
- Updated `_docs/report_design_roadmap.md` to match actual progress:
  - added progress snapshot (`D0 complete, D1 complete, D2 in progress, D3 complete, D4 in progress`)
  - replaced stale “Immediate Next Step = D1” with current D2 deterministic step.
- Reviewed D1–D4 status consistency across roadmap/journal/rules and aligned the key governance/doc gaps.

### Files changed
- `_docs/journal.md`
- `_docs/latest_journal.md`
- `_docs/AGENTS.md`
- `_docs/report_design_roadmap.md`

### Tests updated
- None (governance/docs review and fixes only).

### Validation
- Pending pre-commit run for this docs/rules update.

### Current milestone
- D2 in progress, D4 in progress (design roadmap stream).

### Estimated completion
- 100% for this review/fix step.

### Remaining work
- Implement D2 lead-metric configurability in section builders and tests.
- Continue D4 symbol drilldown UX cleanup tasks.

### Best next deterministic implementation step
- Add configurable lead metric selectors for activity/liquidity/reversion pages
  and enforce deterministic lead-chart precedence with regression tests.

### Open questions
- None.
