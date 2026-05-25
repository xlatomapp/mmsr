# kdb integration testing

MMSR keeps deterministic mock-kdb tests and live-kdb integration tests separate.
The mock path is the default local and CI validation path. It exercises q-template
rendering, `KdbMetricRunner`, output schema contracts, normalization, reference
comparison, and report rendering without importing PyKX or connecting to kdb+.

Live-kdb tests are an opt-in production-environment check. They should be run
only when a small, production-like kdb+ process is available and the source table
schemas have been confirmed with the owning market-data team.

## Default mock-kdb boundary

The deterministic mock-kdb demo:

- renders `activity.q` and `liquidity.q`;
- executes them through `KdbMetricRunner`;
- validates starter output schema contracts before normalization;
- normalizes rows into `MetricTimeSeries`;
- renders through the canonical production-format report builder.

It intentionally does **not** validate live table names, feed permissions,
calendar completeness, data freshness, venue coverage, or market-data quality.
Use it as a contract and report-shape check, not as proof that a production kdb+
environment is ready.

## Live-kdb environment variables

Use these environment variables for future live tests and local smoke scripts.
They are intentionally not required by the default test suite.

| Variable | Required | Purpose |
| --- | --- | --- |
| `MMSR_KDB_HOST` | Yes | kdb+ host name or IP address. |
| `MMSR_KDB_PORT` | Yes | kdb+ IPC port. |
| `MMSR_KDB_USERNAME` | No | kdb+ username when authentication is enabled. |
| `MMSR_KDB_PASSWORD` | No | kdb+ password when authentication is enabled. |
| `MMSR_KDB_TRADES_TABLE` | Yes | Source table for `activity.q` starter metrics. |
| `MMSR_KDB_QUOTES_TABLE` | Yes | Source table for `liquidity.q` starter metrics. |
| `MMSR_KDB_CALENDAR_TABLE` | Yes | Dedicated trading-calendar table for production date selection. |
| `MMSR_KDB_VENUE_TRADES_TABLE` | Reversion only | Venue trade table for `toxicity_reversion.q`. |
| `MMSR_KDB_PRIMARY_QUOTES_TABLE` | Reversion only | Primary quote table for `toxicity_reversion.q`. |
| `MMSR_KDB_TEST_DATE` | Yes | A single known-good trading date for bounded smoke checks. |
| `MMSR_KDB_TEST_SYMBOL` | Optional | A liquid symbol used to limit live smoke-query size. |

`MMSR_KDB_PORT` should be parsed as an integer before constructing `KdbConfig`.
Do not commit secrets, local credentials, or client host names to this repository.

## Starter table and schema assumptions

Live tests for `activity.q` assume the configured trades table has at least:

- `date`
- `time`
- `sym`
- `price`
- `size`

Live tests for `liquidity.q` assume the configured quotes table has at least:

- `date`
- `time`
- `sym`
- `bid_price`
- `ask_price`
- `bid_size`
- `ask_size`

Live tests for `toxicity_reversion.q` assume the configured venue-trade table
has at least:

- `date`
- `time`
- `sym`
- `venue`
- `trade_price`
- `trade_size`
- `aggressor_side`

Live tests for `toxicity_reversion.q` assume the configured primary-quote table
has at least:

- `date`
- `time`
- `sym`
- `venue`
- `bid_price`
- `ask_price`

The reversion side convention is `buy=1`, `sell=-1`. Primary quote rows should
satisfy `ask_price > bid_price`. Production calendar data must come from
`MMSR_KDB_CALENDAR_TABLE`; weekday-only assumptions are not valid for production
report generation.


## Implemented starter live-smoke harnesses

`mmsr.kdb.live_smoke.LiveKdbActivitySmokeConfig` implements the
environment-gated activity smoke harness. It reads the documented connection,
calendar, trades-table, and bounded test-date variables, then builds a single
`turnover` request for `activity.q`.

`mmsr.kdb.live_smoke.LiveKdbLiquiditySmokeConfig` implements the matching
environment-gated liquidity smoke harness. It reads the documented connection,
calendar, quotes-table, and bounded test-date variables, then builds a single
`quoted_spread_bps` request for `liquidity.q`.

Both harnesses use `MMSR_KDB_TEST_DATE` as a one-day date filter. When
`MMSR_KDB_TEST_SYMBOL` is present, the rendered starter q query adds a
`symbol_filter` clause for `sym = $"<symbol>"` and groups by `sym`, keeping the
result small and proving the symbol slice survives normalization.

The corresponding pytests are
`tests/test_live_kdb_smoke.py::test_live_kdb_activity_smoke_validates_starter_output_schema`
and
`tests/test_live_kdb_smoke.py::test_live_kdb_liquidity_smoke_validates_starter_output_schema`.
They skip safely when required variables are missing, import PyKX only after the
environment gate passes, execute through `KdbMetricRunner`, and validate starter
template output through the existing schema contracts before returning a
`MetricTimeSeries`.

## Live test skip behavior

Live integration tests are marked with `@pytest.mark.kdb_integration` and remain
skipped by default. The default command stays offline:

```bash
poetry run pytest
```

After schemas and access are confirmed, run live tests explicitly with:

```bash
poetry run pytest -m kdb_integration
```

The implemented starter live-smoke tests skip themselves when required
environment variables are missing, query only `MMSR_KDB_TEST_DATE` and optionally
`MMSR_KDB_TEST_SYMBOL`, and validate q-template output through
`mmsr.kdb.schema_contracts` before normalizing the result into
`MetricTimeSeries`.
