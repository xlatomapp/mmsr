from datetime import date
import os

import pytest

from mmsr.kdb.live_smoke import (
    LiveKdbActivitySmokeConfig,
    LiveKdbLiquiditySmokeConfig,
    REQUIRED_LIVE_ACTIVITY_SMOKE_ENV_VARS,
    REQUIRED_LIVE_LIQUIDITY_SMOKE_ENV_VARS,
    run_live_activity_smoke,
    run_live_liquidity_smoke,
)


def _valid_activity_env() -> dict[str, str]:
    return {
        "MMSR_KDB_HOST": "localhost",
        "MMSR_KDB_PORT": "5000",
        "MMSR_KDB_TRADES_TABLE": "trade",
        "MMSR_KDB_CALENDAR_TABLE": "trading_calendar",
        "MMSR_KDB_TEST_DATE": "2026-05-01",
    }


def _valid_liquidity_env() -> dict[str, str]:
    return {
        "MMSR_KDB_HOST": "localhost",
        "MMSR_KDB_PORT": "5000",
        "MMSR_KDB_QUOTES_TABLE": "quote",
        "MMSR_KDB_CALENDAR_TABLE": "trading_calendar",
        "MMSR_KDB_TEST_DATE": "2026-05-01",
    }


def test_live_activity_smoke_config_reports_missing_required_env_vars() -> None:
    missing = LiveKdbActivitySmokeConfig.missing_required_env_vars({})

    assert missing == REQUIRED_LIVE_ACTIVITY_SMOKE_ENV_VARS


def test_live_liquidity_smoke_config_reports_missing_required_env_vars() -> None:
    missing = LiveKdbLiquiditySmokeConfig.missing_required_env_vars({})

    assert missing == REQUIRED_LIVE_LIQUIDITY_SMOKE_ENV_VARS


def test_live_activity_smoke_config_parses_env_and_optional_credentials() -> None:
    env = {
        **_valid_activity_env(),
        "MMSR_KDB_USERNAME": "user",
        "MMSR_KDB_PASSWORD": "secret",
        "MMSR_KDB_TEST_SYMBOL": "7203",
    }

    config = LiveKdbActivitySmokeConfig.from_env(env)

    assert config.host == "localhost"
    assert config.port == 5000
    assert config.trades_table == "trade"
    assert config.calendar_table == "trading_calendar"
    assert config.test_date == date(2026, 5, 1)
    assert config.username == "user"
    assert config.password == "secret"
    assert config.test_symbol == "7203"
    assert config.to_kdb_config().port == 5000


def test_live_liquidity_smoke_config_parses_env_and_optional_credentials() -> None:
    env = {
        **_valid_liquidity_env(),
        "MMSR_KDB_USERNAME": "user",
        "MMSR_KDB_PASSWORD": "secret",
        "MMSR_KDB_TEST_SYMBOL": "7203",
    }

    config = LiveKdbLiquiditySmokeConfig.from_env(env)

    assert config.host == "localhost"
    assert config.port == 5000
    assert config.quotes_table == "quote"
    assert config.calendar_table == "trading_calendar"
    assert config.test_date == date(2026, 5, 1)
    assert config.username == "user"
    assert config.password == "secret"
    assert config.test_symbol == "7203"
    assert config.to_kdb_config().port == 5000


def test_live_activity_smoke_config_accepts_q_date_format() -> None:
    env = {**_valid_activity_env(), "MMSR_KDB_TEST_DATE": "2026.05.01"}

    assert LiveKdbActivitySmokeConfig.from_env(env).test_date == date(2026, 5, 1)


def test_live_liquidity_smoke_config_accepts_q_date_format() -> None:
    env = {**_valid_liquidity_env(), "MMSR_KDB_TEST_DATE": "2026.05.01"}

    assert LiveKdbLiquiditySmokeConfig.from_env(env).test_date == date(2026, 5, 1)


def test_live_activity_smoke_config_rejects_invalid_port() -> None:
    env = {**_valid_activity_env(), "MMSR_KDB_PORT": "not-a-port"}

    with pytest.raises(ValueError, match="MMSR_KDB_PORT"):
        LiveKdbActivitySmokeConfig.from_env(env)


def test_live_liquidity_smoke_config_rejects_invalid_port() -> None:
    env = {**_valid_liquidity_env(), "MMSR_KDB_PORT": "not-a-port"}

    with pytest.raises(ValueError, match="MMSR_KDB_PORT"):
        LiveKdbLiquiditySmokeConfig.from_env(env)


def test_live_activity_smoke_config_builds_bounded_activity_request() -> None:
    env = {**_valid_activity_env(), "MMSR_KDB_TEST_SYMBOL": "7203"}
    config = LiveKdbActivitySmokeConfig.from_env(env)

    request = config.build_request()

    assert request.metric.name == "turnover"
    assert request.period.start_date == date(2026, 5, 1)
    assert request.period.end_date == date(2026, 5, 1)
    assert request.period.bucket.value == "5m"
    assert request.group_by == ["sym"]
    assert request.table_names == {"trades": "trade"}
    assert request.parameters == {"symbol": "7203"}


def test_live_liquidity_smoke_config_builds_bounded_liquidity_request() -> None:
    env = {**_valid_liquidity_env(), "MMSR_KDB_TEST_SYMBOL": "7203"}
    config = LiveKdbLiquiditySmokeConfig.from_env(env)

    request = config.build_request()

    assert request.metric.name == "quoted_spread_bps"
    assert request.period.start_date == date(2026, 5, 1)
    assert request.period.end_date == date(2026, 5, 1)
    assert request.period.bucket.value == "5m"
    assert request.group_by == ["sym"]
    assert request.table_names == {"quotes": "quote"}
    assert request.parameters == {"symbol": "7203"}


@pytest.mark.kdb_integration
def test_live_kdb_activity_smoke_validates_starter_output_schema() -> None:
    missing = LiveKdbActivitySmokeConfig.missing_required_env_vars(os.environ)
    if missing:
        pytest.skip(
            "missing required live-kdb smoke environment variable(s): "
            + ", ".join(missing)
        )

    pytest.importorskip("pykx", reason="live kdb smoke tests require PyKX")

    config = LiveKdbActivitySmokeConfig.from_env(os.environ)
    series = run_live_activity_smoke(config)

    assert series.metric_name == "turnover"
    assert series.metadata["template"] == "activity.q"
    assert series.metadata["requested_group_by"] == (
        ("sym",) if config.test_symbol else ()
    )


@pytest.mark.kdb_integration
def test_live_kdb_liquidity_smoke_validates_starter_output_schema() -> None:
    missing = LiveKdbLiquiditySmokeConfig.missing_required_env_vars(os.environ)
    if missing:
        pytest.skip(
            "missing required live-kdb liquidity smoke environment variable(s): "
            + ", ".join(missing)
        )

    pytest.importorskip("pykx", reason="live kdb smoke tests require PyKX")

    config = LiveKdbLiquiditySmokeConfig.from_env(os.environ)
    series = run_live_liquidity_smoke(config)

    assert series.metric_name == "quoted_spread_bps"
    assert series.metadata["template"] == "liquidity.q"
    assert series.metadata["requested_group_by"] == (
        ("sym",) if config.test_symbol else ()
    )
