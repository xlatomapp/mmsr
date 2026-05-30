from __future__ import annotations

import logging

import pytest

from mmsr.cli import build_cli_app
from mmsr.logging import configure_logging


def _command_options(command: str) -> set[str]:
    click_command = __import__("typer.main", fromlist=["get_command"]).get_command(build_cli_app()).commands[command]
    option_names: set[str] = set()
    for param in click_command.params:
        option_names.update(param.opts)
        option_names.update(param.secondary_opts)
    return option_names


@pytest.mark.parametrize("command", ("plan", "preflight", "render"))
def test_production_commands_expose_verbose_logging_options(command: str) -> None:
    option_names = _command_options(command)

    assert "--verbose" in option_names
    assert "-v" in option_names
    assert "--log-level" in option_names


def test_configure_logging_verbose_enables_debug_for_mmsr_logger() -> None:
    level = configure_logging(verbose=True)

    assert level == logging.DEBUG
    assert logging.getLogger("mmsr").getEffectiveLevel() == logging.DEBUG


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid log level"):
        configure_logging(log_level="NOPE")
