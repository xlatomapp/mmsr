"""Reference-data-backed universe source abstractions.

Production reference-data universes come from the user-owned reference-data function.
The same ``getRef[date]`` function controls the analysis universe and returns
symbol attributes used for grouping and raw-source filtering.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Protocol

LOGGER = logging.getLogger(__name__)


class SymbolUniverseSource(Protocol):
    """Interface for retrieving analysis symbols from reference data."""

    def symbols_for_day(self, day: date) -> list[str]:
        """Return symbols to analyze for ``day``."""


@dataclass(frozen=True)
class KdbSymbolUniverseSource:
    """Symbol universe source backed by the user-defined reference function.

    The configured function must accept one positional ``date`` argument and
    return a reference table/dict containing at least ``symbol_column``.
    """

    client: Any
    function: str = ".mmsr.getRef"
    symbol_column: str = "sym"

    def symbols_for_day(self, day: date) -> list[str]:
        """Return analysis symbols by querying the configured reference function."""

        query = f"{{[date] {_q_function_identifier(self.function)}[date]}}"
        LOGGER.info(
            "Calling kdb reference-data universe function %s for %s",
            self.function,
            day,
        )
        result = self.client.execute(query, day)
        symbols = _coerce_symbol_values(result, self.symbol_column)
        LOGGER.info("Reference-data universe returned %s symbol(s)", len(symbols))
        return symbols


def _coerce_symbol_values(result: Any, symbol_column: str) -> list[str]:
    """Coerce common kdb/PyKX-like symbol results into Python strings."""

    if result is None:
        return []

    if isinstance(result, dict):
        return _coerce_symbol_sequence(result.get(symbol_column, []))

    if isinstance(result, list):
        if not result:
            return []
        if isinstance(result[0], dict):
            return _coerce_symbol_sequence(row[symbol_column] for row in result)
        return _coerce_symbol_sequence(result)

    if isinstance(result, tuple):
        return _coerce_symbol_sequence(result)

    if hasattr(result, "py"):
        return _coerce_symbol_values(result.py(), symbol_column)

    return _coerce_symbol_sequence([result])


def _coerce_symbol_sequence(values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        if isinstance(value, bytes):
            text = value.decode()
        else:
            text = str(value)
        if text:
            out.append(text)
    return out


def _q_function_identifier(value: str) -> str:
    """Validate and return a q function identifier used in a symbol call."""

    if not isinstance(value, str) or not value:
        raise ValueError("reference-data function must be a non-empty q function name")
    candidate = value[1:] if value.startswith(".") else value
    parts = candidate.split(".")
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"invalid reference-data function: {value!r}")
    for part in parts:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part) is None:
            raise ValueError(f"invalid reference-data function: {value!r}")
    return value
