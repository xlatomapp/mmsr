# mmsr

Japanese market microstructure surveillance and reporting toolkit.

## Quickstart

Install the package and run the deterministic offline test suite:

```bash
poetry install
poetry run pytest
```

Build the documentation site with the dedicated documentation dependency group:

```bash
poetry install --with doc
poetry run mkdocs build --strict
```

## Report scope

Before choosing a new implementation step, read the [report scope guardrails](report_scope.md)
(`docs/report_scope.md`). The default package output is a Japanese market
microstructure market-monitoring report, not a transaction-cost analysis,
execution quality, execution-quality, smart-order-routing, venue-ranking, or
generic validation-framework / generic validation package. Execution-cost
features such as price impact stay outside the default report. Default report work must
stay focused on activity, displayed liquidity, market-state volatility/quality,
intraday/taxonomy/symbol breakdowns, and Cross-Venue Toxicity/Reversion.


## Demo reports

### Mock-data production-format report

Render the deterministic production-format HTML report from synthetic normalized
metrics and precomputed comparison facts:

```bash
poetry run mmsr offline-demo --output reports/offline_demo.html
```

The offline demo routes synthetic fixtures through the same
`build_market_monitor_report()` path used by production kdb-backed runs. It does not query kdb+, import PyKX, use real market data, or call an LLM.

By default, the generated report includes the sector, segment, and market-cap
drilldown page when the fixture contains matching group-level comparison rows.
Use `--max-drilldown-rows` for a compact table or `--no-drilldown-page` to omit
the drilldown page entirely. Dense intraday line charts are the default; use
`--include-intraday-heatmaps` only when a demo artifact should also show the
matrix-style intraday diagnostics:

```bash
poetry run mmsr offline-demo \
  --output reports/offline_demo_compact_drilldown.html \
  --max-drilldown-rows 10

poetry run mmsr offline-demo \
  --output reports/offline_demo_no_drilldown.html \
  --no-drilldown-page

poetry run mmsr offline-demo \
  --output reports/offline_demo_with_heatmaps.html \
  --include-intraday-heatmaps
```

### Mock-kdb integration report

Render the deterministic mock-kdb integration report through rendered q
templates, `KdbMetricRunner`, and the same canonical report builder:

```bash
poetry run mmsr mock-kdb-demo --output reports/mock_kdb_demo.html
```

This path validates the q-template and normalized-result boundary without a live
kdb+ connection or PyKX import. It remains synthetic and should be used for
integration plumbing and report-shape checks, not production schema validation.

The mock-kdb demo exposes the same drilldown controls and explicit intraday
heatmap opt-in as the offline demo:

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

## Live kdb integration testing

Live kdb+ validation is opt-in because it requires PyKX, credentials, confirmed
source schemas, and a small production-like data slice. See
[kdb integration testing](kdb_integration_testing.md) for the mock-vs-live
boundary and required `MMSR_KDB_*` environment variables.

## Production readiness

Before adding richer sector-specific offline fixtures or running broader live
validation, use the [production readiness checklist](production_readiness.md).
It records the sector taxonomy, segment labels, market-cap bucket rules, symbol
metadata joins, required kdb+ table fields, and bounded live-smoke validation
steps that must be confirmed with the market-data owner.
