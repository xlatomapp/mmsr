# kdb integration testing

MMSR keeps deterministic mock-kdb tests and live-kdb integration tests separate.
The mock path is the default local and CI validation path. It exercises q-template
rendering, `KdbMetricRunner`, output schema contracts, normalization, reference
comparison, and report rendering without importing PyKX or connecting to kdb+.

Live-kdb tests are an opt-in production-environment check. They should be run
only when a small, production-like kdb+ process is available and the raw
source-function result schemas have been confirmed with the owning market-data
team. The package now keeps validation utilities intentionally small; broader
cross-report validation should live in a shared framework outside `mmsr` once
multiple reports exist.

## Production plan and preflight commands

Use `mmsr plan` when operators need to review the bounded run scope before any
production metric q is executed. The command uses the live trading-calendar
source, derives target and reference trading days, applies configured symbol
chunking, renders source-function/input and output schema contracts, and exits
without calling metric source functions.

```bash
mmsr plan \
  --config config/report.production_minimal.yaml \
  --kdb-host localhost \
  --kdb-port 5001 \
  --symbol 7203 \
  --symbol 6758
```

Use `mmsr preflight` before a full `mmsr render` run. The command uses the live
production path, but stops after one planned trading-day/chunk/metric step.
It validates YAML config loading, configured q namespace/source-function names,
kdb trading-calendar access, query planning, and the output schema returned by
that one sample metric query. By default it checks the first configured metric;
pass `--metric` to validate one configured metric family at a time, for example
activity, liquidity, and reversion source-function contracts.

```bash
mmsr preflight \
  --config config/report.production_minimal.yaml \
  --kdb-host localhost \
  --kdb-port 5001 \
  --symbol 7203 \
  --metric quoted_spread_bps
```

For full-universe production checks, omit `--symbol`; for tightly bounded preflight
checks, pass one or more symbols and let `data.kdb.symbol_chunk_size` bound the
planned or sample request. Prefer `config/report.production_minimal.yaml` for
the first live run because it lists only the market-monitoring metrics that
belong in this report: activity, displayed liquidity, and cross-venue
primary-quote reversion. The minimal config does not enable transaction-cost
metrics such as effective spread or price impact. Optional market-microstructure
add-ons, such as tick-normalized spread, quote-mid realized volatility, and
feed-signed order-flow imbalance, remain covered by offline q-template planning
and schema-contract tests when a future report design explicitly needs them.

## Default mock-kdb boundary

The deterministic mock-kdb demo:

- renders the default market-monitoring `activity.q`, `liquidity.q`, and
  `toxicity_reversion.q` templates used by the minimal production config;
- keeps optional market-microstructure add-ons such as `liquidity_ticks.q`,
  `realized_volatility.q`, and `flow.q` covered by the same offline q-template
  planning and schema contract tests used by production execution;
- keeps transaction-cost templates outside the default market report even though
  their schema contracts remain tested for compatibility with existing code;
- executes mock-demo templates through `KdbMetricRunner`;
- validates starter output schema contracts before normalization;
- normalizes rows into `MetricTimeSeries`;
- renders through the canonical production-format report builder.

It intentionally does **not** validate live raw-data functions, feed
permissions, calendar completeness, data freshness, venue coverage, or
market-data quality.
Use it as a contract and report-shape check, not as proof that a production kdb+
environment is ready.



## Production source-function direction

The production report path should call user-defined q functions rather than
directly querying physical trade, quote, calendar, or reference tables. Configure
functions such as `.sb.mmsr.getTrade`, `.sb.mmsr.getQuote`,
`.sb.mmsr.getPtsTrade`, `.sb.mmsr.getPtsQuote`, `.sb.mmsr.getRef`,
and `.sb.mmsr.getTradingCalendar`; those functions can
route between HDB/RDB, cleanse rows, return client-approved reference-data universes,
and normalize canonical columns to MMSR q.

MMSR calculation templates are rendered into the configured calculation
namespace, such as `.desk.mmsr`, and should not write intermediate calculations
to the global namespace. MMSR-owned helpers include `.desk.mmsr.timeBucket`,
which derives continuous buckets plus `AMO`/`AMC`/`PMO`/`PMC` auction buckets
from per-tick `session` and `auction` columns. Production configs should not
hard-code static session start/end times because those can vary by symbol and
day.

`KdbProductionExecutor` builds the production execution path from the trading
calendar: one date-bounded `MetricRunRequest` per trading day, metric, and
optional symbol chunk. `build_plan_summary()` covers the same target and
reference calendar windows and renders schema contracts without metric IO.
`run()` covers the target period; `run_reference()` derives the previous
`reference.lookback_days` trading days from the same kdb calendar and uses the
same bounded execution path. Raw source functions receive only `date` and
`syms`; the reference-data universe function controls which symbols are analyzed for
each trading day, and the reference-data function returns TOPIX/cap/lot-size
metadata for those symbols before MMSR q executes metric calculations.

## Live-kdb environment variables

Use these environment variables for future live tests and local smoke scripts.
They are intentionally not required by the default test suite.

| Variable | Required | Purpose |
| --- | --- | --- |
| `MMSR_KDB_HOST` | Yes | kdb+ host name or IP address. |
| `MMSR_KDB_PORT` | Yes | kdb+ IPC port. |
| `MMSR_KDB_USERNAME` | No | kdb+ username when authentication is enabled. |
| `MMSR_KDB_PASSWORD` | No | kdb+ password when authentication is enabled. |
| `MMSR_KDB_TRADE_FUNCTION` | Yes | User source function for `activity.q` starter metrics. |
| `MMSR_KDB_QUOTE_FUNCTION` | Yes | User source function for `liquidity.q` starter metrics. |
| `MMSR_KDB_REF_FUNCTION` | No | User reference-data function; defaults to `.sb.mmsr.getRef`. |
| `MMSR_KDB_CALENDAR_FUNCTION` | Yes | User trading-calendar function for production date selection. |
| `MMSR_KDB_SYMBOL_FUNCTION` | Production runs | User reference-data universe function for selecting analysis symbols by trading date. |
| `MMSR_KDB_PTS_TRADE_FUNCTION` | Reversion only | PTS trade source function for `toxicity_reversion.q`. |
| `MMSR_KDB_PTS_QUOTE_FUNCTION` | Reversion only | PTS quote source function for `toxicity_reversion.q` aggressor-side inference. |
| `MMSR_KDB_PRIMARY_QUOTE_FUNCTION` | Reversion only | Primary/TSE quote source function for `toxicity_reversion.q` reversion mids. |
| `MMSR_KDB_TEST_DATE` | Yes | A single known-good trading date for bounded smoke checks. |
| `MMSR_KDB_TEST_SYMBOL` | Optional | A liquid symbol used to limit live smoke-query size. |

`MMSR_KDB_PORT` should be parsed as an integer before constructing `KdbConfig`.
Do not commit secrets, local credentials, or client host names to this repository.

Raw source functions must accept positional arguments in this order:
`date; syms`. The calendar function must accept `start; end`. The symbol
universe function must accept `date` and return a symbol vector or a table/dict
with a configured symbol column. The reference function must accept `date; syms`.

## Starter source-function and schema assumptions

Live tests for `activity.q` assume the configured trade function accepts
`date; syms` and returns at least:

- `date`
- `time`
- `sym`
- `session`
- `auction`
- `tradePrice`
- `tradeSize`

Live tests for `liquidity.q` assume the configured quote function accepts
`date; syms` and returns at least:

- `date`
- `time`
- `sym`
- `session`
- `auction`
- `bidPrice`
- `askPrice`
- `bidSize`
- `askSize`

`session` should be `am` or `pm` for standard Japanese trading sessions.
`auction` should be `open` or `close` on auction ticks and null on continuous
ticks. MMSR uses these columns for bucket assignment instead of a static
configured session grid.

The live source-function signatures are:

```q
.sb.mmsr.getTradingCalendar[start;end]
.sb.mmsr.getRef[date]
.sb.mmsr.getTrade[date;ref]
.sb.mmsr.getQuote[date;ref]
```

The configured reference-data function accepts `date` and returns the active
analysis universe plus symbol metadata for that day. It must return at least:

- `date`
- `sym`
- `ric`
- `topixCapGrp`
- `lotSize`

MMSR filters that reference table for CLI symbol overrides or configured symbol
chunks, then passes the filtered table into source functions as `ref`.

Configured trade functions accept `date;ref` and should return at least:

- `date`
- `time`
- `sym`
- `ric`
- `session`
- `auction`
- `venue`
- `tradePrice`
- `tradeSize`

Configured quote functions accept `date;ref` and should return at least:

- `date`
- `time`
- `sym`
- `ric`
- `session`
- `auction`
- `venue`
- `bidPrice`
- `askPrice`
- `bidSize`
- `askSize`

`quoted_spread_ticks` uses `liquidity_ticks.q` and additionally requires
`tick_size`. `realized_volatility` uses `realized_volatility.q` and requires
`sym` on the canonical quote source so log returns are calculated by `date ×
sym` before bucket/group aggregation.

For Cross-Venue Toxicity/Reversion, MMSR infers `aggressorSide` inside its
calculation namespace by joining each trade to the prevailing same-venue,
same-symbol quote and comparing trade price to that venue midpoint. The source
trade function does not need to provide `aggressorSide` for the default live
report. The reversion target remains the TSE/primary quote: future and at-trade
primary mids are joined separately to calculate the reversion value. Quote rows
should satisfy `askPrice > bidPrice`. Production calendar data must come from
`getTradingCalendar[start;end]`; weekday-only assumptions are not valid for
production report generation.

## Production preflight path

Use the packaged `mmsr plan`, `mmsr preflight`, and `mmsr render` commands for
live checks. The previous package-internal live-smoke harness has been removed so
operators use one config-driven production path.

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

Live integration tests skip themselves when required
environment variables are missing, query only `MMSR_KDB_TEST_DATE` and optionally
`MMSR_KDB_TEST_SYMBOL`, and validate q-template output through
`mmsr.kdb.schema_contracts` before normalizing the result into
`MetricTimeSeries`.
