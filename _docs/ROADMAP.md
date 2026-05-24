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

**Exit criteria:**

- Metric definitions exist for each configured horizon.
- q template exists for primary-quote reversion calculation.
- Config supports venues, primary venue, horizons, side source, clustering, stale quote filters, and sample-size confidence thresholds.
- Visual placeholder or production visual supports venue reversion curves.
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

## Milestone 9: End-to-end offline demo

**Goal:** Build a demo report from synthetic/offline fixture data without live kdb.

**Exit criteria:**

- Example config runs locally.
- Synthetic metric results flow through comparison, commentary, and HTML report rendering.
- README includes quickstart.

## Milestone 10: kdb integration demo

**Goal:** Run against a real or mock kdb connection using PyKX.

**Exit criteria:**

- Example kdb query executes.
- q templates validated against expected schema.
- Integration tests documented.

## Later milestones

- Advanced visualizations.
- Symbol-level anomaly pages.
- Sector/segment/market-cap drilldowns.
- Optional LLM commentary extras.
- PDF rendering.
- Scheduling and distribution.
- Alert delivery to email/Slack/Symphony.


## HTML template and branding milestone details

The HTML report layer must provide:

- A default Jinja report template committed under `mmsr/report/templates/`.
- Partial templates for repeated blocks such as metric cards and commentary.
- A renderer that accepts packaged templates by default and an override template directory for client-specific customization.
- Branding options for `brand_name`, `logo_image_src`, `header_image_src`, `footer_image_src`, and `footer_text`.
- Tests that verify default rendering and custom branding values.
