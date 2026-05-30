# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`mmsr` is a Python package that generates Japanese market microstructure monitoring reports from level 1 trade and quote data stored in kdb+. Python orchestrates; kdb+ does the heavy calculation through PyKX. The package targets Python 3.12–3.13.

## Commands

```bash
# Install with all dev tooling
poetry install --with dev

# Run the full test suite (offline, no kdb+ required)
poetry run pytest

# Run a single test
poetry run pytest tests/test_comparison.py::test_function_name

# Run kdb integration tests (requires live kdb+ and MMSR_KDB_* env vars)
poetry run pytest -m kdb_integration

# Lint and type-check
poetry run black --check mmsr tests
poetry run isort --check-only mmsr tests
poetry run flake8 mmsr tests
poetry run mypy mmsr

# Format code
poetry run black mmsr tests
poetry run isort mmsr tests

# Run offline demo report (no kdb+/PyKX/LLM needed)
poetry run mmsr offline-demo --output reports/demo.html
poetry run mmsr mock-kdb-demo --output reports/mock_demo.html

# Build docs
poetry install --with doc
poetry run mkdocs build --strict

# Run all tox environments
poetry run tox
```

## Mandatory workflow before every code change

Always start by reading these three files to understand project rules, current status, and the next step:

1. **`_docs/AGENTS.md`** — project rules, architecture constraints, scope guardrails, style/testing/commit rules
2. **`_docs/MILESTONE_STATUS.md`** — per-milestone audit of what's complete and what remains, plus the **recommended next deterministic step**
3. **`_docs/journal.md`** — chronological implementation log with the most recent state

Then read relevant source files and tests. Do not proceed without understanding the current milestone status and previous journal entries.

## Mandatory update after every implementation step

After every code change, update these files as needed. The **minimum** is `_docs/journal.md` with:

- Date/time of the step
- Summary of what was implemented
- The current step completed, the **next desirable step**, and **how far we are from reaching the next milestone**
- Files changed
- Tests added or updated
- Validation run and result
- Open questions, if any

If milestone completion changed, also update `_docs/MILESTONE_STATUS.md`. A change is incomplete until these docs reflect it.

Commit after updating: `git commit -m "<short imperative summary>"`

## Architecture

The canonical data pipeline is:

```
config (YAML, Pydantic/dataclass models)
  → period/session/bucket model (trading calendar from kdb)
  → metric registry (MetricDefinition lookup)
  → KdbMetricQueryPlanner (renders q templates, validates schemas before IO)
  → KdbMetricRunner (installs MMSR q lib, executes against kdb, validates output)
  → MetricTimeSeries (normalized time-series rows with date/bucket/group columns)
  → reference comparison (robust z-score, empirical percentile, change stats)
  → visuals/tables (Plotly, Jinja2 partials)
  → deterministic commentary (template-based, no LLM by default)
  → HTML report (Jinja2 template at mmsr/report/templates/report.html.j2)
```

### Package structure (key modules)

| Module | Role |
|---|---|
| `mmsr/cli.py` | Typer CLI: `render`, `plan`, `preflight`, `offline-demo`, `mock-kdb-demo` |
| `mmsr/config/models.py` | `ReportConfig` and sub-models (branding, kdb, calendar, toxicity, reference) |
| `mmsr/config/loading.py` | YAML config loading + `ReportPeriod` parsing |
| `mmsr/periods/` | `ReportPeriod`, trading calendar, intraday bucket grid, symbol universe |
| `mmsr/metrics/base.py` | `MetricDefinition` dataclass (name, label, category, formula, interpretation, etc.) |
| `mmsr/metrics/registry.py` | `MetricRegistry` + `build_default_registry()` |
| `mmsr/metrics/starter_definitions.py` | The 11 default market-monitoring metric definitions |
| `mmsr/metrics/results.py` | `MetricTimeSeries`, `MetricObservation`, `MetricComparison` |
| `mmsr/kdb/client.py` | `KdbClient` wrapping PyKX (lazily imported) |
| `mmsr/kdb/query_plan.py` | `KdbMetricQueryPlanner` — renders q, exposes schema contracts before IO |
| `mmsr/kdb/runner.py` | `KdbMetricRunner` — installs q lib, executes, validates, normalizes |
| `mmsr/kdb/production.py` | `KdbProductionExecutor`, `KdbProductionPreflight`, `KdbProductionPlanSummary` |
| `mmsr/kdb/q_lib/mmsr_calculations.q.j2` | Single canonical q calculation library (all metric formulas) |
| `mmsr/kdb/q_lib/mmsr_simulated_sources.q.j2` | Deterministic dev/debug source getters for kdb injection |
| `mmsr/analysis/comparison.py` | Reference comparison engine (z-scores, percentiles, change stats) |
| `mmsr/analysis/commentary.py` | Deterministic template commentary from comparison facts |
| `mmsr/report/market_report.py` | `build_market_monitor_report()` — canonical report assembly |
| `mmsr/report/render_html.py` | Jinja2 HTML rendering |
| `mmsr/report/sections.py` | Comparison tables, time-series charts, heatmaps |
| `mmsr/report/symbols.py` | Symbol anomaly/detail pages |
| `mmsr/report/drilldowns.py` | Sector/segment/market-cap drilldown pages |
| `mmsr/report/toxicity.py` | Cross-Venue Toxicity/Reversion page |
| `mmsr/report/overview.py` | Executive market overview |
| `mmsr/report/templates/` | Jinja2 templates and partials |
| `mmsr/examples/` | Offline and mock-kdb demo report builders |
| `mmsr/presentation/labels.py` | Human-readable display labels |
| `mmsr/llm/` | Optional LLM commentary (disabled by default, extras-only) |
| `mmsr/visuals/` | SVG/visual placeholders |

### Data flow in production (kdb-backed) runs

1. CLI loads YAML config → `ReportConfig` + `ReportPeriod`
2. `KdbClient` connects via PyKX (lazy import)
3. Trading calendar function (user-owned, e.g. `.sb.mmsr.getTradingCalendar`) returns valid trading days
4. Reference-data function (`.sb.mmsr.getRef[date]`) returns the symbol universe per day
5. MMSR installs its q calculation library into the configured namespace (e.g. `.desk.mmsr`)
6. `KdbProductionExecutor` iterates one trading day + one symbol chunk at a time — never fetches multi-day full-market raw data
7. Each batch: q loads raw trade/quote via user source functions, runs MMSR calc functions, returns aggregated result tables
8. `KdbMetricRunner` validates each result against output schema contracts, normalizes to `MetricTimeSeries`
9. Reference comparison engine produces `MetricComparison` objects (robust z-score, empirical percentile)
10. `build_market_monitor_report()` assembles the canonical report document
11. Jinja2 renders HTML from `mmsr/report/templates/report.html.j2`

### Offline / demo data flow

`mmsr offline-demo` and `mmsr mock-kdb-demo` use synthetic fixture data but route through the **same** `build_market_monitor_report()` and the same Jinja2 template. They never import PyKX or call an LLM.

## Key design rules

- **kdb-first**: Metric aggregation happens in q, not Python. Raw trade/quote data never enters Python memory.
- **Lazy PyKX**: `pykx` is an optional extra. All kdb imports are lazy so tests/docs run without it.
- **Deterministic by default**: Commentary is template-based. LLM commentary is opt-in, disabled by default, and must only polish existing facts.
- **Schema contracts**: `KdbMetricQueryPlanner` exposes required input/output columns before any IO. Query rendering and execution are separate testable steps.
- **One q library file**: All MMSR-owned q functions live in `mmsr/kdb/q_lib/mmsr_calculations.q.j2`.
- **Production boundary**: User-owned q functions provide calendar, reference data, trade, and quote rows. MMSR owns the metric calculation q.
- **Bounded execution**: Production runs are batched by single trading day and optional symbol chunk. Multi-day full-market windows are never requested.

## Product scope (from `docs/report_scope.md`)

This is a **market-monitoring** report package. Default metrics: `turnover`, `volume`, `trade_count`, `quoted_spread_bps`, `top_of_book_depth`, and six `primary_quote_reversion_*_bps` horizons. It is **not** a TCA, execution-quality, smart-order-routing, or venue-ranking package. Do not add execution-cost metrics (effective spread, implementation shortfall, slippage, price impact) to default configs or report sections unless the product scope is explicitly changed.

## Reference comparison rules

- Default observation unit: `trading_day` (compare same metric/bucket/group across days).
- 1 reference observation → current-vs-reference change only, no z-score.
- < 30 observations → empirical rank/range position with low-confidence flag.
- ≥ 30 observations → robust z-score (median/MAD, preferred for skewed metrics) and standard z-score available.
- Z-score-to-probability must be labeled "normal-score percentile", not literal probability.
- Direction-aware adverse tails: upper tail for higher-is-worse (spread), lower tail for lower-is-worse (depth).

## Installation profiles

- `poetry install --only main` — runtime only, no PyKX/plotly
- `poetry install --extras kdb` — runtime + PyKX
- `poetry install --with dev` — runtime + tests/lint/type-check
- `poetry install --with doc` — runtime + MkDocs
- `poetry install --extras all --with dev,doc` — everything
