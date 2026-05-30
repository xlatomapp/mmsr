# AGENTS.md

This file defines the mandatory project rules for any AI coding agent, custom GPT, or human contributor working on this repository.

## 1. Project mission

Build `mmsr`, a Python package that generates market microstructure monitoring reports for Japanese market data using level 1 trade and quote data stored in kdb+.

The package must support:

- kdb-first computation through PyKX.
- Time-series-native report periods.
- Configurable intraday buckets such as `1m`, `5m`, `30m`, with explicit auction buckets such as `AMO`, `AMC`, `PMO`, and `PMC`.
- Market-wide, market-cap, segment, sector, intraday, and optional symbol-level breakdowns.
- First-class metric definitions.
- Report visuals and metric cards with metric information/help text.
- Deterministic template commentary by default.
- Optional LLM commentary only when explicitly enabled.

## 1A. Product scope guardrails

Before choosing a roadmap or implementation step, treat `docs/report_scope.md`
as a scope gate. `mmsr` is a Japanese market microstructure market-monitoring
report package. It is not a transaction-cost analysis (TCA), execution quality,
execution-quality, smart-order-routing, venue-ranking, or generic
validation-framework / generic validation package.

Default report implementation must stay centered on:

- market activity: `turnover`, `volume`, and `trade_count`;
- displayed liquidity: `quoted_spread_bps` and `top_of_book_depth`;
- Cross-Venue Toxicity/Reversion using the six `primary_quote_reversion_*_bps`
  horizons;
- market-wide, intraday, taxonomy, and venue views by default;
- symbol-level views only as explicit opt-in escalation from market/group
  changes, not as the default product shape;
- volatility or market-quality extensions only when they describe market state
  rather than a specific execution outcome.

Do not add default config entries, report sections, executive-summary language,
or next-step roadmap items for effective spread, implementation shortfall,
slippage, price impact, order-routing analytics, or other execution-cost/TCA
features unless the user explicitly changes the product scope. Do not keep production runner paths for these transaction-cost metrics unless the product scope explicitly changes.

Do not expand report-local validation helpers into a reusable validation
framework inside this package. After several reports exist, repeated validation
needs should be designed above `mmsr`.

## 1B. Active near-term direction

The active roadmap reset is: desk-first report, slimmer code, faster q. Future
work should prioritize the `Current roadmap reset` section in
`_docs/ROADMAP.md`.

Default implementation should:

- lead with a high-level market summary for trading-desk review;
- highlight important market-level changes before detailed diagnostics;
- drill down to TPX cap group, sector, segment, venue, and intraday
  distributions;
- treat symbol pages and symbol rollups as explicit opt-in escalation;
- keep calculation in kdb and return aggregated report facts to Python;
- keep the codebase small by removing redundant wrappers, stale compatibility
  paths, and demo-only behavior that leaks into production defaults.

The first recommended implementation sequence is:

1. Remove no-op q wrappers around native q functions.
2. Remove `symbol` and `symbol_bucket` from default production aggregation
   levels.
3. Disable symbol anomaly/detail pages by default.
4. Add q timing instrumentation inside `runReportDay`.
5. Add tests that lock the new default report shape and aggregation defaults.

## 2. Mandatory reading order before any code change

Before modifying code, tests, config, docs, or roadmap, read these files in order:

1. `_docs/AGENTS.md`
2. `_docs/latest_journal.md`
3. `_docs/ROADMAP.md`
4. `_docs/journal.md`
5. Relevant source files and tests for the current task

Do not proceed without checking the current milestone and previous journal entries.

## 3. Mandatory journal update after every step

After every implementation step, use this two-file journal workflow:

### 3A. Start-of-task journal handoff (mandatory)

- Read `_docs/latest_journal.md` first.
- If `_docs/latest_journal.md` contains a completed step entry, append it to the
  **very bottom** of `_docs/journal.md` before starting new work.
- After appending, reset `_docs/latest_journal.md` back to its template.

### 3B. End-of-task journal write (mandatory)

- Write the current completed step entry to `_docs/latest_journal.md`.
- Do not write the new step directly to `_docs/journal.md` during the same task.
- The next task start performs the append-to-`journal.md` handoff.

Each completed step entry must include:

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

The journal workflow is part of the implementation contract. A change is
incomplete if `_docs/latest_journal.md` is not updated at task finish, or if
the next task does not perform the append handoff into `_docs/journal.md`.

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
- Put reusable q code under `mmsr/kdb/q_lib/`.
- Validate all query parameters before constructing q queries.
- Prefer query templates with explicit parameter substitution over ad hoc string concatenation.
- Test query rendering separately from query execution.
- Prefer the installed q `runReportDay[runDate; reportConfig]` production path.
  Older single-metric or batch query paths should not be expanded unless there
  is an explicit compatibility requirement.
- Do not wrap native q functions such as `sum`, `count`, `med`, or `wavg` just
  to rename them. A q helper is justified only when it adds real policy, null
  handling, validation, reuse, or a domain-specific convention.
- Profile and optimize q at the source-load, metric-calculation, rollup,
  cache, and serialization stages before adding more metric families or report
  pages.
- Load raw sources once per day/chunk where possible, reuse prepared family
  state, and avoid returning raw or near-raw rows to Python.
- Keep `stockMetrics` cache work focused on aggregated metric facts, not raw
  trade or quote persistence.

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

## 12A. Local live-kdb testing

The default test suite must remain offline and deterministic. Live kdb tests are
opt-in only and should stay marked with `kdb_integration`.

For local live-kdb smoke testing, the currently available endpoint is:

```text
host: 192.168.3.99
port: 5001
```

Use the endpoint through CLI flags or environment variables, for example:

```bash
MMSR_KDB_HOST=192.168.3.99 MMSR_KDB_PORT=5001 poetry run pytest -m kdb_integration
```

or:

```bash
poetry run mmsr preflight \
  --config config/report.production_minimal.yaml \
  --kdb-host 192.168.3.99 \
  --kdb-port 5001
```

Do not hard-code this host or port into production configs or package code. Treat
it as a local developer/test endpoint only.

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
