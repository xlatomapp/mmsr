# mmsr

A Python package for generating Japanese market microstructure monitoring reports from level 1 trade and quote data stored in kdb+.

## Goals

- kdb-first calculation using PyKX.
- Configurable intraday buckets such as `1m`, `5m`, `30m`, with explicit auction buckets and sortable bucket grids.
- Time-series-native metric results and comparable reference comparisons.
- Market-wide, market-cap, segment, sector, intraday, and symbol-level breakdowns.
- First-class metric definitions with help text for reports.
- kdb-backed trading calendar access for production report dates.
- Deterministic template commentary by default.
- Optional LLM commentary only when explicitly enabled.

## Report scope guardrails

`mmsr` is a market-monitoring report package, not a transaction-cost analysis
(TCA), execution quality, execution-quality, smart-order-routing,
venue-ranking, or generic validation-framework / generic validation package. Future implementation should stay centered on
market activity, displayed liquidity, volatility/market quality where clearly
market-state focused, intraday/taxonomy/symbol drilldowns, and Cross-Venue
Toxicity/Reversion.

The default report metric set is intentionally limited to `turnover`, `volume`,
`trade_count`, `quoted_spread_bps`, `top_of_book_depth`, and the six
`primary_quote_reversion_*_bps` horizons. Execution-cost metrics such as
effective spread, implementation shortfall, slippage, and price impact must not
be added to default configs or report sections unless the product scope is
explicitly changed. See `docs/report_scope.md` before choosing a future roadmap
or implementation step.



## Python support

This project targets Python 3.12 and 3.13.

## HTML report templates

HTML output is template-driven so reports stay visually consistent across runs.
The default template lives at `mmsr/report/templates/report.html.j2`.
Branding options such as header image, footer image, logo image, and footer text are configured in `config/report.example.yaml`.



### Production kdb render

The production entrypoint is `mmsr render`. It reads the YAML config, connects to
kdb+ through the lazy PyKX-backed client, obtains target and reference trading
days from the configured calendar function, asks the configured reference-data universe
function for each trading day, and runs the bounded production executor. Metric q
remains MMSR-owned and namespaced. User-owned q functions are responsible only for
calendar dates, reference-data universe selection, reference data, and canonicalized
trade/quote rows.

MMSR installs reusable q aggregation helpers such as `.desk.mmsr.sumNotional`,
`.desk.mmsr.medianQuotedSpreadBps`, `.desk.mmsr.weightedAverage`, and
`.desk.mmsr.timeBucket` inside the configured
`data.kdb.calculation_namespace`. The time-bucket helper uses the per-tick
`session` and `auction` columns returned by your source functions, so production
configs should not hard-code static session start/end times.

The live data path is intentionally streaming-by-result rather than persisted in
kdb. Production execution is batched by one trading day and one symbol chunk.
For each day/chunk batch, the rendered q query builds `refs` from the raw
reference universe, calls each configured raw source function at most once for
the source roles required by the configured metrics, and then passes the loaded
raw tables into MMSR calculation functions such as
`.desk.mmsr.calcFlow[rawTrades;refs]`. The top-level q expression returns a
dictionary keyed by metric name, where each value is the aggregated result table
for that metric. PyKX returns that dictionary to Python through
`KdbClient.execute`; `KdbMetricRunner` validates each metric output schema and
normalizes each table into `MetricTimeSeries` for report rendering and reference
comparison. MMSR does not persist result tables in kdb unless a future
operator-owned sink is explicitly added.


`config/report.production_minimal.yaml` is the recommended first live-kdb
configuration in the repo. The same example is packaged in
`mmsr/examples/config/live_kdb_report.yaml` for installed wheels/sdists. It is
intentionally scoped to market-monitoring metrics only: `turnover`, `volume`,
`trade_count`, `quoted_spread_bps`, `top_of_book_depth`, and the six
primary-quote reversion horizons from `primary_quote_reversion_10ms_bps` through
`primary_quote_reversion_10s_bps`.

```bash
mmsr render \
  --config config/report.production_minimal.yaml \
  --output report.html \
  --kdb-host localhost \
  --kdb-port 5001 \
  --symbol 7203 \
  --symbol 6758
```

For full-universe reports, omit repeated `--symbol` filters and let the
configured symbol function choose the analysis universe for each trading day.
When a symbol list is supplied, `data.kdb.symbol_chunk_size` bounds each
production request to one trading day and one symbol chunk before q execution.
The same bounded daily/chunk execution shape is used for reference observations
derived from `reference.lookback_days`, and `mmsr render` wires those reference
observations into current-vs-reference comparison tables and trend charts.

Run `mmsr plan` before executing production metric q when operators need to
review the bounded run scope. It loads the config, queries the trading-calendar
function, derives target and reference trading days, applies configured symbol
chunking, and prints the source-function/input and output schema contracts
without running metric q:

```bash
mmsr plan \
  --config config/report.production_minimal.yaml \
  --kdb-host localhost \
  --kdb-port 5001 \
  --symbol 7203 \
  --symbol 6758
```

Run `mmsr preflight` before a full production render to validate config loading,
q namespace/source-function names, kdb calendar access, query planning, and one
bounded sample metric result schema. By default it checks the first configured
metric. Pass `--metric` to validate a specific configured metric family, such as
an activity, liquidity, or reversion metric, before broadening the live check:

```bash
mmsr preflight \
  --config config/report.production_minimal.yaml \
  --kdb-host localhost \
  --kdb-port 5001 \
  --symbol 7203 \
  --metric quoted_spread_bps
```

The plan command does not execute metric q. The preflight uses the same
production executor boundary but executes only one planned
trading-day/chunk/metric step for the default or selected metric.


## Development workflow

Before implementing anything, read:

1. `_docs/AGENTS.md`
2. `_docs/ROADMAP.md`
3. `_docs/journal.md`

After every implementation step, update `_docs/journal.md`.

## Installation profiles

Runtime installs stay lean by default and include only the production package,
the Typer-powered `mmsr` CLI, and report-rendering dependencies. PyKX, plotting,
development, and documentation tooling are excluded unless explicitly requested.

```bash
# Runtime package only.
poetry install --only main

# Runtime package plus kdb/PyKX support for production connectivity.
poetry install --extras kdb

# Contributor tooling for tests, type checks, formatters, and pre-commit hooks.
poetry install --with dev

# Documentation tooling for the MkDocs site.
poetry install --with doc
poetry run mkdocs build --strict
```

The `doc` dependency group exists because `mkdocs.yml` uses the Material theme and
`mkdocstrings`; keeping those dependencies outside the runtime path preserves a
minimal production install.

## Quickstart

```bash
poetry install
poetry run pytest
```

### Mock-data production-format report

Render the deterministic HTML demo without a live kdb+ connection, PyKX import, or LLM call:

```bash
poetry run mmsr offline-demo --output reports/offline_demo.html
```

The command uses synthetic normalized metrics and precomputed comparisons from
`mmsr.examples.offline_fixtures`, adapts them into the canonical
`MarketReportInput`, and routes them through `build_market_monitor_report()`.
Production kdb-backed runs should use the same report builder and packaged Jinja
template; only the data source changes. The output path is treated as a file
path, and missing parent directories are created automatically.

Useful options:

```bash
poetry run mmsr offline-demo \
  --output reports/offline_demo_no_appendix.html \
  --title "MMSR Offline Demo" \
  --brand-name "Example Desk" \
  --max-drilldown-rows 10 \
  --no-appendix

poetry run mmsr offline-demo \
  --output reports/offline_demo_no_drilldown.html \
  --no-drilldown-page

poetry run mmsr offline-demo \
  --output reports/offline_demo_with_heatmaps.html \
  --include-intraday-heatmaps
```

Use `--max-drilldown-rows` for compact sector, segment, and market-cap tables,
and `--no-drilldown-page` when a smoke-test artifact should omit that page.
Dense intraday time-bucket line charts remain the default; use
`--include-intraday-heatmaps` only when a sample report should also include the
matrix-style bucket × group diagnostic views.

Use the mock-data demo as a smoke test for the production report format and
documentation layout only. It does not query kdb+, validate production table
schemas, or use real market data.

### Mock-kdb integration report

Render the deterministic integration demo that executes rendered q templates
through `KdbMetricRunner` and a deterministic mock kdb client before using the
same canonical report builder:

```bash
poetry run mmsr mock-kdb-demo --output reports/mock_kdb_demo.html
```

This path validates the q-template and normalization boundary without a live
kdb+ connection or PyKX import. It is still synthetic: use it to check integration
plumbing and report shape, not production table schemas or market data quality.
It exposes the same drilldown and explicit heatmap opt-in controls as the
offline demo:

```bash
poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_compact_drilldown.html \
  --max-drilldown-rows 10

poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_no_drilldown.html \
  --no-drilldown-page

poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_with_heatmaps.html \
  --include-intraday-heatmaps
```

### Production kdb source-function boundary

Production metric runs call user-owned q functions instead of querying physical
tables directly. Those functions can route between HDB/RDB, cleanse data,
normalize venue codes, enrich permissions, and map internal schemas to MMSR's
canonical boundary. MMSR then joins reference data, infers trade side when
needed, and runs the metric aggregation q inside the configured calculation
namespace.

Example configuration shape:

```yaml
data:
  source: kdb
  kdb:
    calculation_namespace: ".desk.mmsr"
    enforce_daily_raw_scope: true
    # Process reference symbols in bounded chunks and keep symbol-level
    # aggregation inside each chunk before unioning chunk results.
    symbol_chunk_size: 500
    symbol_chunk_group_by: [sym]
    raw_data_functions:
      namespace: ".sb.mmsr"
      trade: "getTrade"
      quote: "getQuote"
      # Toxicity-only PTS source; falls back to trade when omitted.
      pts_trade: "getPtsTrade"
      # Same-PTS quote source used to infer aggressorSide per venue/sym.
      pts_quote: "getPtsQuote"
      # Primary/TSE quote source used as the reversion target.
      primary_quote: "getQuote"
      reference_data: "getRef"

calendar:
  source: kdb
  namespace: ".sb.mmsr"
  function: "getTradingCalendar"
  date_column: date

reference_data:
  source: kdb
  namespace: ".sb.mmsr"
  function: "getRef"
  symbol_column: sym
  ric_column: ric
```

The required user q function signatures are positional and intentionally small:

```q
.sb.mmsr.getTradingCalendar
.sb.mmsr.getRef[date]
.sb.mmsr.getTrade[date;ref]
.sb.mmsr.getQuote[date;ref]
.sb.mmsr.getPtsTrade[date;ref]
.sb.mmsr.getPtsQuote[date;ref]
```

Trade rows may include `auction` so MMSR can label `AMO`/`AMC`/`PMO`/`PMC`
buckets. Quote rows are continuous-session rows only; `getQuote` and
`getPtsQuote` are not expected to return an `auction` column, and quote metrics
use `timeBucketContinuous[time;bucket]`.

`getRef[date]` controls the active universe for the date and returns one row per
analysis symbol with at least `date`, `sym`, `ric`, `topixCapGrp`, and `lotSize`.
MMSR filters that reference table for CLI `--symbol` runs or configured symbol
chunks, then passes the filtered table into each configured raw source function:
main `getTrade`/`getQuote` for activity and liquidity, `getPtsTrade`/`getPtsQuote`
for toxicity-side inference, and `getQuote` or another configured primary quote
function for TSE/primary mids. This lets source functions filter by `sym`, `ric`,
or any other user-owned reference column without MMSR knowing the raw vendor
schema.

Trade and quote rows must carry per-tick market-state columns. `session` should
identify the market session, for example `am` or `pm`. `auction` should identify
auction ticks, for example `open` or `close`; continuous-session ticks should
have null `auction`. MMSR uses those columns to derive continuous intraday
buckets and explicit auction buckets such as `AMO`, `AMC`, `PMO`, and `PMC`,
instead of relying on a static configured session-time grid.

Canonical trade rows should expose `date`, `time`, `sym`, `ric`, `session`,
`auction`, `venue`, `tradePrice`, and `tradeSize`. Canonical quote rows should
expose `date`, `time`, `sym`, `ric`, `session`, `auction`, `venue`, `bidPrice`,
`askPrice`, `bidSize`, and `askSize`. MMSR derives `aggressorSide` in q for reversion by joining each PTS trade to
the prevailing same-PTS-venue/same-symbol PTS quote and comparing trade price to
that PTS midpoint; source functions do not need to provide `aggressorSide` for
the default live report. TSE/primary quotes are used separately only for the
at-trade and future reversion mids.

Market-cap group is intentionally not required by the live starter boundary. Add
any additional grouping columns, such as `sector` or `market_segment`, to
`getRef` before including those names in the config `groups` list.

The production execution path is driven by `KdbProductionExecutor`, which asks a
trading-calendar function for dates, asks `getRef[date]` for the reference-data
universe on each trading day, and builds one `MetricRunRequest` per trading day,
metric, and optional symbol chunk. Do not request or hold a multi-day full-market
raw trade/quote window in Python.

### kdb query plans and schema contracts

The kdb execution boundary is explicit and testable before a query is sent to a
live process. `KdbMetricQueryPlanner` renders the q template and returns a
`RenderedMetricQuery` containing:

- the rendered q text;
- required source-table column contracts for each logical input table;
- required output columns that must come back from kdb before normalization;
- supported optional output columns, such as `context_sort_order` for the
  reversion report page.

This lets production users manually adjust q templates while preserving the
Python report contract: change the q as needed, but keep the returned table in
the documented shape.

```python
from mmsr.kdb import KdbMetricQueryPlanner, MetricRunRequest

plan = KdbMetricQueryPlanner().render(
    MetricRunRequest(
        metric=registry.get("quoted_spread_bps"),
        period=period,
        group_by=["sector"],
        table_names={"quotes": "quote_l1"},
    )
)

print(plan.required_output_columns)
# ("date", "time_bucket", "sector", "quoted_spread_bps", "top_of_book_depth")

# Validate an offline/PyKX-like result before normalization.
plan.validate_result_schema(result)
```

The normal `KdbMetricRunner.run()` path uses the same query plan internally, so
runner validation and manual q hardening share one schema source of truth.

### Symbol-level anomaly pages

When normalized comparisons include a symbol-like group key such as `symbol`,
`ticker`, `security_code`, or `sym`, the canonical report builder can insert a
deterministic "Symbol Anomalies" page. The page is built from existing
`MetricComparison` facts only: it does not query kdb+, calculate new metrics, or
call an LLM. By default it keeps the worst alert/watch comparison per symbol and
renders a metric table with metric help text and human-readable scope labels.

```python
from mmsr.report import MarketReportOptions, build_market_monitor_report

document = build_market_monitor_report(
    report_input,
    options=MarketReportOptions(max_symbol_anomalies=20),
)
```

Set `include_symbol_anomaly_page=False` when a report should omit this page even
if symbol-scoped rows are present. Use `MarketReportOptions.symbol_group_keys`
when a client schema uses a different identifier column such as
`client_symbol`, `issue_code`, or `local_code`; the same configured key order is
used for the anomaly summary page and any per-symbol detail pages. When callers
also provide symbol-scoped `MetricTimeSeries` rows through
`MarketReportInput.symbol_series`, the report can insert optional per-symbol
detail pages with deterministic intraday time-bucket line charts for the
selected symbols. Dense intraday bucket grids such as `1m` are shown with the
bucket on the x-axis by default; heatmaps remain available through
`include_intraday_heatmaps=True` for clients that explicitly want matrix-style
diagnostics. These detail pages format existing normalized rows only; they do
not query kdb+, calculate additional metrics, or call an LLM. When detail pages
are emitted, the `Symbol Anomalies` page also includes a compact `Symbol Detail
Index` with deterministic links to each emitted detail page. Set
`include_symbol_detail_pages=False` to omit the detail pages or
`include_symbol_detail_index=False` to keep the details while omitting the index.

The bundled `offline-demo` includes three synthetic symbol-scoped comparison rows
and matching symbol detail series, so both the summary anomaly page and
per-symbol detail pages are visible without real market data, live kdb+, PyKX, or
LLM access.

### Sector, segment, and market-cap drilldowns

The report layer includes deterministic helpers for sector, segment, and
market-cap drilldown pages. They work from existing `MetricComparison` facts and
do not query kdb+, calculate new metrics, or call an LLM. By default they select
rows with group keys such as `market_cap_bucket`, `market_segment`, `segment`, or
`sector`, exclude symbol-scoped rows so they do not duplicate the symbol anomaly
page, and return a stable severity-first order.

```python
from mmsr.report import (
    DrilldownReportPageOptions,
    DrilldownSelectionOptions,
    build_drilldown_report_page,
    select_drilldown_comparisons,
)

drilldown_rows = select_drilldown_comparisons(
    report_input.comparisons,
    options=DrilldownSelectionOptions(
        group_keys=("market_cap_bucket", "segment", "sector"),
        max_rows=50,
    ),
)

drilldown_page = build_drilldown_report_page(
    report_input.comparisons,
    report_input.metric_definitions,
    options=DrilldownReportPageOptions(
        selection=DrilldownSelectionOptions(max_rows=50),
    ),
)
```

`build_drilldown_report_page()` formats the selected rows as a metric table with
registry-backed metric help controls and human-readable scope labels such as
`Market cap bucket: Large cap` or `Intraday bucket: AM opening auction`. Use
custom `group_keys` for client-specific normalized dimensions. Set
`include_symbol_scoped=True` only when a drilldown page should intentionally mix
symbol-scoped rows into sector or segment diagnostics.

The canonical `build_market_monitor_report()` path now inserts this page
automatically when matching group-level comparison rows are present. Configure it
through `MarketReportOptions.include_drilldown_page`,
`drilldown_page_title`, `drilldown_table_title`, `drilldown_help_text`,
`drilldown_group_keys`, and `max_drilldown_rows`. The bundled `offline-demo`
and `mock-kdb-demo` commands expose the same inclusion and row-limit controls
through `--no-drilldown-page` and `--max-drilldown-rows`, so sample reports can
demonstrate the default page, opt-out behavior, and compact drilldown tables
from the command line. The bundled `offline-demo` renders the page from
synthetic market-cap and segment comparison facts without real market data, live
kdb+, PyKX, or LLM access.

### Live kdb integration-test boundary

The default test suite remains offline and deterministic. Live kdb+ validation is
opt-in because it requires PyKX, credentials, confirmed source schemas, and a
small production-like data slice. See `docs/kdb_integration_testing.md` for the
mock-vs-live boundary, required `MMSR_KDB_*` environment variables, starter
trade/quote/reversion table assumptions, the environment-gated
`LiveKdbActivitySmokeConfig` and `LiveKdbLiquiditySmokeConfig` harnesses, and
`@pytest.mark.kdb_integration` skip policy.

```bash
poetry run pytest
poetry run pytest -m kdb_integration
```

The starter live harnesses validate one bounded `activity.q` turnover query and
one bounded `liquidity.q` quoted-spread query through `KdbMetricRunner` and the
existing output schema contracts. Set `MMSR_KDB_TEST_SYMBOL` to add a symbol
slice filter for the smoke runs.

### Production readiness checklist

Before adding richer sector-specific offline fixtures or enabling broader live
validation, review `docs/production_readiness.md`. The checklist records the
sector taxonomy, segment labels, market-cap bucket thresholds, symbol metadata
join rules, required kdb+ source fields, and bounded live-smoke validation gates
that need market-data owner sign-off.

## Example configuration

Use `config/report.production_minimal.yaml` for the first live-kdb run because
it includes only the market-monitoring metrics that belong in this report.
`config/report.example.yaml` uses the same default metric scope and adds fuller
commentary, branding, grouping, and toxicity/reversion settings for reference.

## Package flow

```text
config -> kdb calendar/symbol/ref functions -> metric registry -> PyKX/kdb metric runner -> per-tick session/auction-aware time-series result -> comparable reference comparison -> visuals -> template commentary -> report renderer
```

## Notes

This skeleton is designed to be copied into or generated alongside a ppw project. ppw provides a Poetry/MkDocs/Pytest/tox/pre-commit style project foundation; this package adds the market microstructure-specific modules and governance docs.

## Cross-venue toxicity reversion

The production report includes a dedicated `Cross-Venue Toxicity` page when normalized kdb-backed primary-quote reversion rows are present. Production analysis targets TSE through `toxicity.primary_venue: TSE`; the reversion q then discovers the trade/quote venues present in the source rows, unless `toxicity.venues` is explicitly configured as a narrow filter. It renders deterministic SVG venue reversion curves with horizon progression on the x-axis, reversion in bps on the y-axis, and one line per venue such as TSE, SBIJ, and ODX. The page consumes already-computed `MetricTimeSeries` rows and does not query kdb+, calculate raw-tick metrics, or call an LLM in the report layer.

When production output contains many date, intraday bucket, sector, segment, or symbol contexts, the toxicity page ranks contexts deterministically before applying the chart limit. The default ranking surfaces the contexts with the largest positive reversion first because positive values indicate future TSE/primary-mid movement in the direction of the aggressor inferred from each trade's own PTS quote under `aggressorSide * (future_primary_mid - primary_mid_at_trade) / future_primary_mid * 10000`. Production callers can set `MarketReportOptions.toxicity_reversion_context_ranking` to `max_positive_reversion`, `max_absolute_reversion`, `lowest_confidence`, `context_sort_order`, or `chronological`. When normalized kdb-backed rows include optional `context_sort_order` metadata, `context_sort_order` ranks smaller numeric values first, then falls back to adverse reversion and chronological ordering for ties or missing values.

By default, when the dedicated `Cross-Venue Toxicity` page is present, `build_market_monitor_report()` suppresses the `primary_quote_reversion_*_bps` family from the generic `Intraday Detail` page so the same venue/horizon curves are not duplicated. Production callers that explicitly want both displays can set `MarketReportOptions.include_toxicity_reversion_metrics_in_detail_page=True`; if the dedicated toxicity page is disabled or absent, the generic detail page still renders any supplied reversion series.

## CI

GitHub Actions CI is configured under `.github/workflows/ci.yml` to run the test suite on Python 3.12 and 3.13. Publishing to PyPI is intentionally omitted from the skeleton.

## Intraday bucket grid

`mmsr.periods.build_intraday_bucket_grid` builds report-ready buckets such as `AMO`, `9:00-9:01`, `9:01-9:02`, `AMC`, `PMO`, and `PMC`. Each row includes a numeric `sort_order` column so report tables and charts can preserve true market order.

## Reference comparison

Reference comparison is built around a configured observation unit. The default is `trading_day`, so raw quote/trade data is first aggregated to one value per comparable daily observation, such as `date × time_bucket × topixCapGrp × metric`. Current values are then compared with the historical distribution for the same comparable keys.

Z-scores are optional anomaly diagnostics, not mandatory report fields. The default policy requires at least 30 comparable reference observations before a z-score or normal-score percentile is treated as a headline statistic. With one reference observation the report shows only current-vs-reference change; with fewer than 30 observations it prefers empirical rank, range position, and a low-confidence flag.

For non-technical readers, prefer empirical percentile or normal-score percentile language over raw z-scores. For example, say “current spread ranked above 95% of comparable observations” or “normal-score percentile: 97.5%” rather than presenting only `z = 1.96`.


When callers provide `MarketReportInput.reference_series` together with the
target/current series, the default report includes a `Reference and Target Daily
Trends` page. This plots the reference trading days followed by the target period
on a daily x-axis so reviewers can see the time series that produced the
comparison summary.


## Production q-side execution shape

Production kdb runs now execute one trading day at a time. Python obtains the
day's reference universe, passes an explicit `allSyms` vector and `chunkSize`
into the rendered q wrapper, and q cuts the symbols into chunks internally. For
each chunk, q loads the required raw sources once, passes the loaded trade/quote
tables into MMSR calc functions, razes the chunk outputs inside kdb, and returns
final metric result tables to Python via PyKX.

The default rollup levels are configured under `data.kdb.aggregation_levels`:

- `market`
- `market_bucket`
- `topix_cap_group`
- `topix_cap_group_bucket`
- `symbol`
- `symbol_bucket`

Quote source contracts no longer require an `auction` column. Quotes are treated
as continuous-session rows and use continuous intraday buckets; trade-side
calculations still use auction labels where trade rows expose `session` and
`auction`.

There is no separate q template directory. Metric identifiers such as
`liquidity.q` and `activity.q` still work in Python APIs, but they are resolved
from the single canonical q calculation library instead of per-metric q files.


### kdb calculation library loading

MMSR keeps every package-owned q function definition in one library:

```text
mmsr/kdb/q_lib/mmsr_calculations.q.j2
```

`KdbMetricRunner` renders this library into the configured `calculation_namespace`
and installs it into a real PyKX-backed kdb process before metric execution.
Metric-specific calculation functions, shared utilities such as `timeBucket`,
`timeBucketContinuous`, `sumNotional`, and `rollupMetricResult`, and the
request-level metric blocks all live in that one file.

This keeps the runtime shape clear:

```text
install MMSR q library once per namespace
for each trading day:
  q cuts symbols into chunks
  q loads trade/quote/PTS sources once per chunk
  q calculates chunk facts/results
  q razes and rollups requested aggregation levels
  PyKX returns the final result tables to Python
```

Quote source functions are continuous-session quote sources and do not need an
`auction` column. Auction-aware bucketing remains trade-only.
