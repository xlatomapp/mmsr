# AGENTS.md

This file defines the mandatory project rules for any AI coding agent, custom GPT, or human contributor working on this repository.

## 1. Project mission

Build `mmsr`, a Python package that generates market microstructure monitoring reports for Japanese market data using level 1 trade and quote data stored in kdb+.

The package must support:

- kdb-first computation through PyKX.
- Time-series-native report periods.
- Configurable intraday buckets such as `1m`, `5m`, `30m`, with explicit auction buckets such as `AMO`, `AMC`, `PMO`, and `PMC`.
- Market-wide, market-cap, segment, sector, intraday, and symbol-level breakdowns.
- First-class metric definitions.
- Report visuals and metric cards with metric information/help text.
- Deterministic template commentary by default.
- Optional LLM commentary only when explicitly enabled.

## 2. Mandatory reading order before any code change

Before modifying code, tests, config, docs, or roadmap, read these files in order:

1. `_docs/AGENTS.md`
2. `_docs/ROADMAP.md`
3. `_docs/journal.md`
4. Relevant source files and tests for the current task

Do not proceed without checking the current milestone and previous journal entries.

## 3. Mandatory journal update after every step

After every implementation step, update `_docs/journal.md` with:

- Date/time of the step.
- Summary of what was implemented.
- Files changed.
- Tests added or updated.
- Validation run and result.
- Current milestone name.
- Estimated milestone completion percentage.
- Remaining work for the milestone.
- The single best next deterministic step.
- Open questions, if any.

The journal is part of the implementation contract. A change is incomplete if `_docs/journal.md` is not updated.

## 4. Deterministic implementation rule

Always choose the smallest deterministic next step that moves the project toward the next roadmap milestone.

Avoid:

- Large rewrites.
- Unrequested refactors.
- Introducing many abstractions at once.
- Adding dependencies without justification.
- Mixing unrelated changes.
- Implementing LLM-dependent features before deterministic template features.

Prefer:

- Small typed models.
- Isolated modules.
- Unit tests for every new behavior.
- Stable interfaces before implementations.
- Query templates that can be tested without connecting to production kdb.

## 5. Architecture rules

The canonical pipeline is:

```text
config
  -> period/session/bucket model
  -> metric registry
  -> PyKX/kdb query runner
  -> metric time-series result
  -> reference comparison
  -> visuals/tables
  -> deterministic commentary
  -> optional LLM commentary
  -> report renderer
```

Python should orchestrate the workflow. kdb+ should do the heavy calculation.

## 6. kdb / PyKX rules

- Use PyKX for kdb+ connectivity.
- Keep the PyKX dependency lazily imported where possible so documentation and unit tests can run without a live kdb connection.
- Do not fetch raw full-day trade/quote data into Python for normal report generation.
- Put reusable q code under `mmsr/kdb/q_templates/`.
- Validate all query parameters before constructing q queries.
- Prefer query templates with explicit parameter substitution over ad hoc string concatenation.
- Test query rendering separately from query execution.

## 7. Period, calendar, and intraday bucket rules

- Treat periods as time series, not as one static current/reference pair.
- Preserve `date`, `time_bucket`, and grouping columns in metric outputs.
- Intraday bucket size must be configurable.
- Build a deterministic intraday bucket grid from the configured sessions and bucket size.
- Auction buckets must be explicit rows, using labels such as `AMO`, `AMC`, `PMO`, and `PMC`.
- Bucket grids must include a numeric `sort_order` column so report outputs and joins preserve true trading order, for example `AMO` = 1, `09:00-09:01` = 2, and so on.
- Session breaks, especially Japan's lunch break, must be represented explicitly in config or period/session models.
- Calendar/trading-day data must come from a dedicated data source. The production source for this project is kdb+. Do not use weekday-only assumptions in production report generation.
- Comparisons should default to same intraday bucket over a reference window where possible.

## 8. Metric definition rules

Every metric must have a `MetricDefinition` with:

- `name`
- `label`
- `category`
- `description`
- `formula`
- `interpretation`
- `unit`
- `higher_is_better`
- `default_aggregation`
- `supports_intraday`
- `supports_symbol_level`
- `required_tables`
- `required_columns`
- `caveats`

A metric is not complete until it is registered and covered by tests.

## 9. Report documentation/help rules

Every report component that displays a metric should be able to expose metric help text.

- HTML: info icon / tooltip / expandable details.
- Excel: comment/note or metric definitions sheet.
- PDF/static output: appendix or inline definition block.

The metric registry is the source of truth for these descriptions.

## 10. Commentary rules

The default commentary engine must be deterministic and template-based.

LLM commentary:

- Must be optional.
- Must be disabled by default.
- Must never be required to produce a report.
- Must only polish or summarize facts already generated by deterministic code.
- Must not introduce new facts, causal claims, or speculation.

## 11. Reference comparison and z-score rules

- A z-score is an optional anomaly diagnostic over comparable historical aggregated observations, not a proof that the metric is normally distributed.
- The package must explicitly define the reference observation unit before calculating any statistical score. The default observation unit is `trading_day`.
- For a metric such as quoted spread, first calculate the current aggregate at the report level, for example median quoted spread for a market-cap bucket and intraday bucket.
- Build the reference distribution from comparable historical aggregates, for example one value per historical trading day for the same metric, group, and intraday bucket.
- Do not compare a 09:00 spread against all-day spread history unless that is explicitly configured and documented.
- Do not calculate or display a z-score when there is only one reference observation. Show current value, reference value, absolute change, and percentage change instead.
- With fewer than 30 comparable reference observations, treat z-score-style outputs as low-confidence diagnostics. Prefer empirical rank, reference range position, and clear low-confidence wording.
- With at least 30 comparable reference observations, robust z-score, standard z-score, empirical percentile, and normal-score percentile can be calculated if dispersion is non-zero.
- If z-score is converted to probability space, label it as a `normal-score percentile` or `normal approximation tail probability`; do not phrase it as a literal probability unless the modelling assumptions are explicitly stated.
- Direction matters: for higher-is-worse metrics such as quoted spread, the adverse tail is the upper tail; for lower-is-worse metrics such as depth, the adverse tail is the lower tail.
- Prefer robust z-scores based on median/MAD or empirical percentiles for skewed metrics such as spread, depth, price impact, and reversion.
- Standard z-scores using mean/std are allowed, but only when the sample size and distribution are appropriate.

## 12. Testing rules

For each feature, add the most focused tests possible.

Minimum expected test areas:

- Period/session/bucket construction, including auction bucket sort order.
- Metric definition validation.
- Metric registry lookup and docs generation.
- q template loading/rendering.
- Reference comparison calculations.
- Template commentary generation.
- Report component metric help rendering.

Tests should not require a live kdb instance unless explicitly marked as integration tests.

## 13. Style rules

- Use type hints for public functions and dataclasses.
- Keep modules small and cohesive.
- Prefer pure functions for transformations.
- Use clear domain names: `ReportPeriod`, `IntradayBucket`, `MetricDefinition`, `MetricTimeSeries`, `MetricComparison`, `CommentaryFact`.
- Do not hide business logic inside rendering code.

## 14. Dependency rules

Baseline dependencies should remain minimal.

Expected dependencies:

- `pykx` for kdb+ connectivity.
- `pydantic` or dataclasses for typed configuration/domain models.
- `pandas` or `polars` only at report boundary if needed.
- `jinja2` for report templates.
- `plotly` or `matplotlib` for visualisation, chosen deliberately.
- `pytest` for tests.

Do not add LLM SDK dependencies to the core package. Place optional LLM integrations behind extras.

## 15. Milestone progress rule

Milestone progress percentage is an estimate, but it must be honest and specific.

Good:

```text
Milestone 2: Domain models
Progress: 45%
Implemented: ReportPeriod and IntradayBucket parsing.
Remaining: MetricResult model, validation tests, serialization helpers.
```

Bad:

```text
Progress: going well
```

## 16. Stop conditions

Stop and record an open question in `_docs/journal.md` if:

- The next step requires production schema details not yet known.
- A metric formula depends on unavailable fields.
- A dependency choice would materially constrain the package.
- A live kdb connection is required but not configured.

When blocked, still choose the best deterministic next step that can be completed offline.


## HTML template rules

- HTML reports must use stable Jinja templates by default.
- The default template path is `mmsr/report/templates/report.html.j2`.
- Header image, footer image, logo image, brand name, and footer text must be configurable through report configuration.
- Do not generate one-off ad hoc HTML layouts for core report pages; add or extend templates instead.
- Any metric or visual in HTML must expose metric help text through an info/help control where available.

## 17. Git commit rule

Every implementation step must be committed with git after tests/validation and after `_docs/journal.md` is updated.

Required sequence:

1. Read `_docs/AGENTS.md`, `_docs/ROADMAP.md`, and `_docs/journal.md`.
2. Implement the smallest deterministic change.
3. Run focused tests or record why tests could not be run.
4. Update `_docs/journal.md`.
5. Run `git status --short` and review the changed files.
6. Run `git add` for the intended files only.
7. Run `git commit -m "<short imperative summary>"`.

If the working directory is not yet a git repository, initialize it with `git init` before the first implementation commit. Do not commit generated caches, local virtual environments, private data, report outputs, or secrets.

## 18. Toxicity reversion terminology rule

The cross-venue toxicity section may use the section title `Cross-Venue Toxicity`, but the metric family must use `reversion` terminology.

Use labels such as:

- `+10ms Reversion`
- `+100ms Reversion`
- `+500ms Reversion`
- `+1s Reversion`
- `+5s Reversion`
- `+10s Reversion`

The default visualization for this section is a venue reversion curve where the x-axis is horizon progression, the y-axis is reversion in bps, and each series is a venue.
