# Report Design Roadmap

## Goal

Redesign the default `mmsr` report so the first screen tells a clear market story with visual priority, while preserving current data/metric semantics and deterministic behavior.

This roadmap is design-and-delivery scoped for the report surface only. It does not change metric definitions, reference-comparison math, or source-function contracts.

## Design Principles

1. Market-first: page 1 represents one market state, not row-level bucket noise.
2. Story-before-table: key change narrative + visuals come before dense tables.
3. Deterministic ranking: no LLM logic in default path.
4. Drilldown escalation: symbol-level views remain optional and secondary.
5. Compact, repeatable layout: stable structure across daily runs.

## Rendering Strategy (Python-first)

For redesign work, prefer Python component builders over new Jinja partials.

- Keep `report.html.j2` as a thin document shell and shared base styles.
- Build section content, ordering, and deterministic HTML in Python modules
  (`overview.py`, `market_report.py`, `sections.py`, `toxicity.py`).
- Avoid adding new `.j2` partial templates unless there is a clear reuse gain.
- Treat Jinja as a final assembly layer, not a logic layer.

Rationale:
- easier deterministic testing at function level
- lower template branching complexity
- less fragile UI behavior from template-side conditionals

## Metric Coverage Matrix (Reference vs MMSR Default)

The reference image is layout guidance only. Metric content in `mmsr` must stay
aligned to the default report scope.

| Design reference metric/card | Keep as-is? | MMSR default metric mapping | Notes |
| --- | --- | --- | --- |
| Traded Value | Yes | `turnover` | Primary activity KPI. |
| Quoted Spread | Yes | `quoted_spread_bps` | Primary displayed-liquidity cost proxy. |
| Quoted Depth | Yes | `top_of_book_depth` | Primary displayed-liquidity capacity proxy. |
| Price Impact | No (rename/replace) | Cross-venue reversion family: `primary_quote_reversion_{10ms,100ms,500ms,1s,5s,10s}_bps` | Do not label as execution-cost "price impact" in default report. |
| Intraday spread curve | Yes | `quoted_spread_bps` target vs reference profile | Keep as primary page-1 intraday visual. |
| Group heatmap (spread/volatility style) | Partial | Spread/depth/activity deltas by TPX/sector/segment from existing comparisons | Use current comparison facts; no new volatility family required for MVP. |
| Security anomaly table | Yes (optional default-lite) | Symbol anomaly rows from existing comparison facts | Keep symbol escalation secondary/opt-in. |
| Venue reversion curves | Yes | Reversion family by venue/horizon | Core MMSR default family. |
| Daily trend chart | Yes | Daily trend for activity + displayed-liquidity + selected reversion lines | Preserve market-monitoring focus. |

### Required MVP default metric families

1. Activity: `turnover`, `volume`, `trade_count`
2. Displayed liquidity: `quoted_spread_bps`, `top_of_book_depth`
3. Cross-venue toxicity/reversion:
   - `primary_quote_reversion_10ms_bps`
   - `primary_quote_reversion_100ms_bps`
   - `primary_quote_reversion_500ms_bps`
   - `primary_quote_reversion_1s_bps`
   - `primary_quote_reversion_5s_bps`
   - `primary_quote_reversion_10s_bps`

### Metrics intentionally not default in this redesign

- execution-cost/TCA metrics (implementation shortfall, slippage, explicit
  "price impact" framing)
- non-required volatility families not already in default scope
- symbol-first KPIs on page 1

## Target Information Architecture

### Section 1: Market Overview (page 1, above the fold)

- Header strip:
  - period
  - benchmark/reference window
  - data freshness / run tag
- KPI row (4 cells):
  - activity proxy (turnover/volume)
  - spread
  - depth
  - impact/toxicity proxy
- Key Changes block:
  - max 5 bullets
  - market+date aggregated, time-bucket collapsed
  - diversified selection (metric default; optional family mode)
- Top Market Drivers block:
  - ranked list + mini intensity bars
  - TPX-first context ordering
- One primary intraday comparison visual:
  - target vs benchmark profile
  - light uncertainty/reference band

### Section 2: Intraday Microstructure

- 1 large chart per priority metric family:
  - activity
  - displayed liquidity
  - toxicity/reversion
- Single chart narrative callout under each chart.

### Section 3: Metric Explorer & Group Analysis

- Group heatmap (sector/TPX/segment)
- Group comparison bars (top deltas)
- Distribution chart (target vs reference)

### Section 4: Security Drilldown & Anomalies (optional default-lite)

- Compact anomaly table (top N only)
- Right-side detail panel for selected symbol/context
- Keep symbol pages opt-in for full detail.

### Section 5: Venue Reversion Analysis

- Reversion curves by venue and horizon
- Summary insight panel with deterministic text.

### Section 6: Daily Trend

- Daily aggregate trend lines for key metrics
- Keep this after intraday diagnostics.

## Milestones

## Progress Snapshot (2026-05-30)

- D0: Complete
- D1: Complete
- D2: In progress
- D3: Complete (matrix + linked trend explorer landed)
- D4: Complete
- D5: In progress

## D0 — UX Contract Lock

Scope:
- Freeze section order, naming, and visual hierarchy.
- Freeze page-1 card/chart/table ordering contract.

Deliverables:
- HTML structure contract doc (classes/sections)
- test checklist for ordering and presence

Exit criteria:
- tests assert structure order for all default report renders.

## D1 — Page-1 Story Redesign

Scope:
- Implement market-overview layout matching target:
  - KPI row
  - key changes
  - top drivers + mini bars
  - primary intraday chart
- Ensure page-1 content uses market+date aggregation.

Deliverables:
- updated `overview.py` composition
- updated template styles for compact dashboard look
- updated summary selection tests

Exit criteria:
- no repeated bucket-level duplicates in key changes/drivers
- top blocks appear before tables in all default renders.

## D2 — Visual Priority Refactor (Tables Demoted)

Scope:
- Make visuals primary in sections 2/3/5/6.
- Keep tables as compact diagnostics below charts.

Deliverables:
- template render order updates
- chart sizing and spacing normalization

Exit criteria:
- each section starts with at least one visual component
- tables never appear above primary section visual by default.

## D3 — Group Analysis Upgrade

Scope:
- Improve TPX/sector/segment diagnostics:
  - clearer heatmap labels
  - top movers panel
  - distribution comparison panel

Deliverables:
- improved group visuals and deterministic selection rules
- tests for group ranking and label formatting

Exit criteria:
- group-level insights are scannable without reading raw tables.

## D4 — Symbol Drilldown UX Cleanup

Scope:
- Keep default report compact while preserving symbol escalation path.
- Improve anomaly table-to-detail linkage.

Deliverables:
- cleaner anomaly block layout
- deterministic selected-symbol detail panel behavior

Exit criteria:
- default report remains market-first
- symbol details remain accessible with explicit opt-in/escalation.

## D5 — Polish + Accessibility + Budget

Scope:
- visual polish (spacing, contrast, typographic hierarchy)
- accessibility pass (keyboard, focus, labels, semantics)
- performance/size budget lock

Deliverables:
- CSS polish pass
- a11y checklist + fixes
- report budget assertions

Exit criteria:
- pre-commit + tests pass
- budget tests pass
- no layout overlap across target viewport sizes.

## Acceptance Criteria (Global)

- First viewport communicates:
  - what changed
  - where it changed (TPX/group context)
  - how severe it is
- Default output avoids repeated same-metric noise.
- Visuals lead; tables support.
- Deterministic and reproducible output from same inputs.
- No regression in source-function and comparison contracts.

## Mapping to Current Code Areas

- Composition:
  - `mmsr/report/market_report.py`
  - `mmsr/report/overview.py`
- Visual builders:
  - `mmsr/report/sections.py`
  - `mmsr/report/toxicity.py`
- Template/CSS:
  - `mmsr/report/templates/report.html.j2`
  - partials under `mmsr/report/templates/partials/`
- Regression tests:
  - `tests/test_market_report.py`
  - `tests/test_executive_overview.py`
  - `tests/test_offline_demo.py`
  - `tests/test_mock_kdb_demo.py`

## Immediate Next Deterministic Implementation Step

Implement D5 polish/a11y/budget hardening:
- finalize accessibility attributes and live-region semantics for interactive panels
- lock render assertions for interactive panel accessibility hooks
- keep report budget checks green for default offline/mock runs.
