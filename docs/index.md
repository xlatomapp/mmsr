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
the drilldown page entirely:

```bash
poetry run mmsr offline-demo \
  --output reports/offline_demo_compact_drilldown.html \
  --max-drilldown-rows 10

poetry run mmsr offline-demo \
  --output reports/offline_demo_no_drilldown.html \
  --no-drilldown-page
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

The mock-kdb demo exposes the same drilldown controls as the offline demo:

```bash
poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_compact_drilldown.html \
  --max-drilldown-rows 10

poetry run mmsr mock-kdb-demo \
  --output reports/mock_kdb_demo_no_drilldown.html \
  --no-drilldown-page
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

