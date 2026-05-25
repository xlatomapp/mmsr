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


## Python support

This project targets Python 3.12 and 3.13.

## HTML report templates

HTML output is template-driven so reports stay visually consistent across runs.
The default template lives at `mmsr/report/templates/report.html.j2`.
Branding options such as header image, footer image, logo image, and footer text are configured in `config/report.example.yaml`.

## Development workflow

Before implementing anything, read:

1. `_docs/AGENTS.md`
2. `_docs/ROADMAP.md`
3. `_docs/journal.md`

After every implementation step, update `_docs/journal.md`.

## Installation profiles

Runtime installs stay lean by default and do not include PyKX, plotting,
development, or documentation tooling unless explicitly requested.

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
```

Use `--max-drilldown-rows` for compact sector, segment, and market-cap tables,
and `--no-drilldown-page` when a smoke-test artifact should omit that page.

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
It exposes the same drilldown controls as the offline demo:

```bash
poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_compact_drilldown.html \
  --max-drilldown-rows 10

poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_no_drilldown.html \
  --no-drilldown-page
```

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
detail pages with deterministic trend charts and intraday heatmaps for the
selected symbols. These detail pages format existing normalized rows only; they
do not query kdb+, calculate additional metrics, or call an LLM. When detail
pages are emitted, the `Symbol Anomalies` page also includes a compact
`Symbol Detail Index` with deterministic links to each emitted detail page.
Set `include_symbol_detail_pages=False` to omit the detail pages or
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

See `config/report.example.yaml`.

## Package flow

```text
config -> kdb calendar -> period/session/bucket grid -> metric registry -> PyKX/kdb metric runner -> metric time-series result -> comparable reference comparison -> visuals -> template commentary -> report renderer
```

## Notes

This skeleton is designed to be copied into or generated alongside a ppw project. ppw provides a Poetry/MkDocs/Pytest/tox/pre-commit style project foundation; this package adds the market microstructure-specific modules and governance docs.

## Cross-venue toxicity reversion

The production report includes a dedicated `Cross-Venue Toxicity` page when normalized kdb-backed primary-quote reversion rows are present. It renders deterministic SVG venue reversion curves with horizon progression on the x-axis, reversion in bps on the y-axis, and one line per venue such as TSE, SBIJ, and ODX. The page consumes already-computed `MetricTimeSeries` rows and does not query kdb+, calculate raw-tick metrics, or call an LLM in the report layer.

When production output contains many date, intraday bucket, sector, segment, or symbol contexts, the toxicity page ranks contexts deterministically before applying the chart limit. The default ranking surfaces the contexts with the largest positive reversion first because positive values indicate adverse movement in the aggressive-trade direction. Production callers can set `MarketReportOptions.toxicity_reversion_context_ranking` to `max_positive_reversion`, `max_absolute_reversion`, `lowest_confidence`, `context_sort_order`, or `chronological`. When normalized kdb-backed rows include optional `context_sort_order` metadata, `context_sort_order` ranks smaller numeric values first, then falls back to adverse reversion and chronological ordering for ties or missing values.

By default, when the dedicated `Cross-Venue Toxicity` page is present, `build_market_monitor_report()` suppresses the `primary_quote_reversion_*_bps` family from the generic `Intraday Detail` page so the same venue/horizon curves are not duplicated. Production callers that explicitly want both displays can set `MarketReportOptions.include_toxicity_reversion_metrics_in_detail_page=True`; if the dedicated toxicity page is disabled or absent, the generic detail page still renders any supplied reversion series.

## CI

GitHub Actions CI is configured under `.github/workflows/ci.yml` to run the test suite on Python 3.12 and 3.13. Publishing to PyPI is intentionally omitted from the skeleton.

## Intraday bucket grid

`mmsr.periods.build_intraday_bucket_grid` builds report-ready buckets such as `AMO`, `9:00-9:01`, `9:01-9:02`, `AMC`, `PMO`, and `PMC`. Each row includes a numeric `sort_order` column so report tables and charts can preserve true market order.

## Reference comparison

Reference comparison is built around a configured observation unit. The default is `trading_day`, so raw quote/trade data is first aggregated to one value per comparable daily observation, such as `date × time_bucket × market_cap_bucket × metric`. Current values are then compared with the historical distribution for the same comparable keys.

Z-scores are optional anomaly diagnostics, not mandatory report fields. The default policy requires at least 30 comparable reference observations before a z-score or normal-score percentile is treated as a headline statistic. With one reference observation the report shows only current-vs-reference change; with fewer than 30 observations it prefers empirical rank, range position, and a low-confidence flag.

For non-technical readers, prefer empirical percentile or normal-score percentile language over raw z-scores. For example, say “current spread ranked above 95% of comparable observations” or “normal-score percentile: 97.5%” rather than presenting only `z = 1.96`.
