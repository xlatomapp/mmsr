"""Environment-gated live-kdb smoke-test helpers.

The helpers in this module keep live validation opt-in and intentionally small:
they build bounded starter-template requests from documented ``MMSR_KDB_*``
environment variables, run them through ``KdbMetricRunner``, and therefore reuse
the same output schema-contract validation as deterministic mock-kdb tests.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, time
import os

from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.runner import KdbMetricRunner, MetricRunRequest
from mmsr.metrics import build_default_registry
from mmsr.metrics.results import MetricTimeSeries
from mmsr.periods import IntradayBucketSpec, ReportPeriod, TradingSession


REQUIRED_LIVE_ACTIVITY_SMOKE_ENV_VARS: tuple[str, ...] = (
    "MMSR_KDB_HOST",
    "MMSR_KDB_PORT",
    "MMSR_KDB_TRADES_TABLE",
    "MMSR_KDB_CALENDAR_TABLE",
    "MMSR_KDB_TEST_DATE",
)
REQUIRED_LIVE_LIQUIDITY_SMOKE_ENV_VARS: tuple[str, ...] = (
    "MMSR_KDB_HOST",
    "MMSR_KDB_PORT",
    "MMSR_KDB_QUOTES_TABLE",
    "MMSR_KDB_CALENDAR_TABLE",
    "MMSR_KDB_TEST_DATE",
)


@dataclass(frozen=True)
class LiveKdbActivitySmokeConfig:
    """Configuration for the smallest live ``activity.q`` smoke test.

    ``calendar_table`` is retained even though the first smoke request does not
    query it directly. Requiring the variable keeps the harness aligned with the
    documented production boundary: report dates must come from a dedicated kdb
    calendar source before a live environment is considered ready.
    """

    host: str
    port: int
    trades_table: str
    calendar_table: str
    test_date: date
    username: str | None = None
    password: str | None = None
    test_symbol: str | None = None
    bucket_size: str = "5m"

    @classmethod
    def missing_required_env_vars(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        """Return required live-smoke variables absent from ``env``."""

        return _missing_required_env_vars(
            REQUIRED_LIVE_ACTIVITY_SMOKE_ENV_VARS,
            env,
        )

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "LiveKdbActivitySmokeConfig":
        """Build an activity smoke config from documented ``MMSR_KDB_*`` vars."""

        source = os.environ if env is None else env
        missing = cls.missing_required_env_vars(source)
        if missing:
            raise ValueError(
                "missing required live-kdb smoke environment variable(s): "
                + ", ".join(missing)
            )

        return cls(
            host=_required_env_value(source, "MMSR_KDB_HOST"),
            port=_parse_port(_required_env_value(source, "MMSR_KDB_PORT")),
            trades_table=_required_env_value(source, "MMSR_KDB_TRADES_TABLE"),
            calendar_table=_required_env_value(source, "MMSR_KDB_CALENDAR_TABLE"),
            test_date=_parse_test_date(
                _required_env_value(source, "MMSR_KDB_TEST_DATE")
            ),
            username=_optional_env_value(source, "MMSR_KDB_USERNAME"),
            password=_optional_env_value(source, "MMSR_KDB_PASSWORD"),
            test_symbol=_optional_env_value(source, "MMSR_KDB_TEST_SYMBOL"),
        )

    def to_kdb_config(self) -> KdbConfig:
        """Return the PyKX connection config for this live smoke test."""

        return KdbConfig(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )

    def build_request(self) -> MetricRunRequest:
        """Build a bounded ``turnover`` request for ``activity.q``.

        When ``test_symbol`` is provided, the request applies a q symbol filter
        and groups by ``sym`` so the normalized result proves the bounded slice
        survived the report-boundary schema contract.
        """

        registry = build_default_registry()
        group_by = ["sym"] if self.test_symbol else []
        parameters = {"symbol": self.test_symbol} if self.test_symbol else {}
        return MetricRunRequest(
            metric=registry.get("turnover"),
            period=_single_day_period(self.test_date, self.bucket_size),
            group_by=group_by,
            table_names={"trades": self.trades_table},
            parameters=parameters,
        )


@dataclass(frozen=True)
class LiveKdbLiquiditySmokeConfig:
    """Configuration for the smallest live ``liquidity.q`` smoke test.

    The liquidity smoke mirrors the activity smoke, but it reads the documented
    quotes table and requests ``quoted_spread_bps`` so live validation covers the
    starter quote template and its output schema contract.
    """

    host: str
    port: int
    quotes_table: str
    calendar_table: str
    test_date: date
    username: str | None = None
    password: str | None = None
    test_symbol: str | None = None
    bucket_size: str = "5m"

    @classmethod
    def missing_required_env_vars(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> tuple[str, ...]:
        """Return required live-liquidity-smoke variables absent from ``env``."""

        return _missing_required_env_vars(
            REQUIRED_LIVE_LIQUIDITY_SMOKE_ENV_VARS,
            env,
        )

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
    ) -> "LiveKdbLiquiditySmokeConfig":
        """Build a liquidity smoke config from documented ``MMSR_KDB_*`` vars."""

        source = os.environ if env is None else env
        missing = cls.missing_required_env_vars(source)
        if missing:
            raise ValueError(
                "missing required live-kdb liquidity smoke environment variable(s): "
                + ", ".join(missing)
            )

        return cls(
            host=_required_env_value(source, "MMSR_KDB_HOST"),
            port=_parse_port(_required_env_value(source, "MMSR_KDB_PORT")),
            quotes_table=_required_env_value(source, "MMSR_KDB_QUOTES_TABLE"),
            calendar_table=_required_env_value(source, "MMSR_KDB_CALENDAR_TABLE"),
            test_date=_parse_test_date(
                _required_env_value(source, "MMSR_KDB_TEST_DATE")
            ),
            username=_optional_env_value(source, "MMSR_KDB_USERNAME"),
            password=_optional_env_value(source, "MMSR_KDB_PASSWORD"),
            test_symbol=_optional_env_value(source, "MMSR_KDB_TEST_SYMBOL"),
        )

    def to_kdb_config(self) -> KdbConfig:
        """Return the PyKX connection config for this live smoke test."""

        return KdbConfig(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )

    def build_request(self) -> MetricRunRequest:
        """Build a bounded ``quoted_spread_bps`` request for ``liquidity.q``."""

        registry = build_default_registry()
        group_by = ["sym"] if self.test_symbol else []
        parameters = {"symbol": self.test_symbol} if self.test_symbol else {}
        return MetricRunRequest(
            metric=registry.get("quoted_spread_bps"),
            period=_single_day_period(self.test_date, self.bucket_size),
            group_by=group_by,
            table_names={"quotes": self.quotes_table},
            parameters=parameters,
        )


def run_live_activity_smoke(
    config: LiveKdbActivitySmokeConfig,
) -> MetricTimeSeries:
    """Execute the live ``activity.q`` smoke request through ``KdbMetricRunner``."""

    runner = KdbMetricRunner(KdbClient(config.to_kdb_config()))
    return runner.run(config.build_request())


def run_live_liquidity_smoke(
    config: LiveKdbLiquiditySmokeConfig,
) -> MetricTimeSeries:
    """Execute the live ``liquidity.q`` smoke request through ``KdbMetricRunner``."""

    runner = KdbMetricRunner(KdbClient(config.to_kdb_config()))
    return runner.run(config.build_request())


def _missing_required_env_vars(
    names: tuple[str, ...],
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    source = os.environ if env is None else env
    return tuple(name for name in names if not source.get(name))


def _single_day_period(test_date: date, bucket_size: str) -> ReportPeriod:
    return ReportPeriod(
        start_date=test_date,
        end_date=test_date,
        sessions=[
            TradingSession(start=time(9, 0), end=time(11, 30), name="AM"),
            TradingSession(start=time(12, 30), end=time(15, 30), name="PM"),
        ],
        bucket=IntradayBucketSpec(bucket_size),
    )


def _required_env_value(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise ValueError(f"environment variable {name} must be non-empty")
    return value


def _optional_env_value(env: Mapping[str, str], name: str) -> str | None:
    value = env.get(name)
    if value is None or value == "":
        return None
    return value


def _parse_port(raw_port: str) -> int:
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("MMSR_KDB_PORT must be an integer") from exc
    if not 0 < port < 65536:
        raise ValueError("MMSR_KDB_PORT must be between 1 and 65535")
    return port


def _parse_test_date(raw_date: str) -> date:
    normalized = raw_date.replace(".", "-")
    try:
        return date.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(
            "MMSR_KDB_TEST_DATE must be an ISO date such as 2026-05-01 "
            "or a q date such as 2026.05.01"
        ) from exc
