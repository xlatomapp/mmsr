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

## Quickstart

```bash
poetry install
poetry run pytest
```

### Offline demo report

Render the deterministic HTML demo without a live kdb+ connection, PyKX import, or LLM call:

```bash
poetry run mmsr offline-demo --output reports/offline_demo.html
```

The command uses synthetic normalized metrics and precomputed comparisons from
`mmsr.examples.offline_fixtures`, then routes them through the same comparison,
template commentary, metric help, and HTML rendering layers used by the package.
The output path is treated as a file path, and missing parent directories are
created automatically.

Useful options:

```bash
poetry run mmsr offline-demo \
  --output reports/offline_demo_no_appendix.html \
  --title "MMSR Offline Demo" \
  --brand-name "Example Desk" \
  --no-appendix
```

Use the offline demo as a smoke test for report rendering and documentation
layout only. It does not query kdb+, validate production table schemas, or use
real market data.

## Example configuration

See `config/report.example.yaml`.

## Package flow

```text
config -> kdb calendar -> period/session/bucket grid -> metric registry -> PyKX/kdb metric runner -> metric time-series result -> comparable reference comparison -> visuals -> template commentary -> report renderer
```

## Notes

This skeleton is designed to be copied into or generated alongside a ppw project. ppw provides a Poetry/MkDocs/Pytest/tox/pre-commit style project foundation; this package adds the market microstructure-specific modules and governance docs.

## Cross-venue toxicity reversion

The roadmap includes a dedicated toxicity section that compares aggressive-trade reversion across venues such as TSE, SBIJ, and ODX using the primary exchange quote as the common benchmark. The default visual is a venue reversion curve with horizon progression on the x-axis and reversion in bps on the y-axis.

## CI

GitHub Actions CI is configured under `.github/workflows/ci.yml` to run the test suite on Python 3.12 and 3.13. Publishing to PyPI is intentionally omitted from the skeleton.

## Intraday bucket grid

`mmsr.periods.build_intraday_bucket_grid` builds report-ready buckets such as `AMO`, `9:00-9:01`, `9:01-9:02`, `AMC`, `PMO`, and `PMC`. Each row includes a numeric `sort_order` column so report tables and charts can preserve true market order.

## Reference comparison

Reference comparison is built around a configured observation unit. The default is `trading_day`, so raw quote/trade data is first aggregated to one value per comparable daily observation, such as `date × time_bucket × market_cap_bucket × metric`. Current values are then compared with the historical distribution for the same comparable keys.

Z-scores are optional anomaly diagnostics, not mandatory report fields. The default policy requires at least 30 comparable reference observations before a z-score or normal-score percentile is treated as a headline statistic. With one reference observation the report shows only current-vs-reference change; with fewer than 30 observations it prefers empirical rank, range position, and a low-confidence flag.

For non-technical readers, prefer empirical percentile or normal-score percentile language over raw z-scores. For example, say “current spread ranked above 95% of comparable observations” or “normal-score percentile: 97.5%” rather than presenting only `z = 1.96`.
