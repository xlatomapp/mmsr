"""Symbol-universe source abstractions.

Production symbol universes should come from a dedicated user-owned data source.
For this project, that source is expected to be a kdb+ function that returns the
symbols to analyze for a single trading day.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Any, Protocol


class SymbolUniverseSource(Protocol):
    """Interface for retrieving analysis symbols for a trading day."""

    def symbols_for_day(self, day: date) -> list[str]:
        """Return symbols to analyze for ``day``."""


@dataclass(frozen=True)
class KdbSymbolUniverseSource:
    """Symbol universe source backed by a user-defined kdb+ function.

    The configured function must accept one positional ``date`` argument and
    return either a symbol vector or a table/dict with ``symbol_column``.
    """

    client: Any
    function: str = ".mmsr.getSymbols"
    symbol_column: str = "sym"

    def symbols_for_day(self, day: date) -> list[str]:
        """Return analysis symbols by querying the configured universe function."""

        query = f"{{[date] {_q_function_identifier(self.function)}[date]}}"
        result = self.client.execute(query, day)
        return _coerce_symbol_values(result, self.symbol_column)


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
        raise ValueError("symbol universe function must be a non-empty q function name")
    candidate = value[1:] if value.startswith(".") else value
    parts = candidate.split(".")
    if not parts or any(part == "" for part in parts):
        raise ValueError(f"invalid symbol universe function: {value!r}")
    for part in parts:
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part) is None:
            raise ValueError(f"invalid symbol universe function: {value!r}")
    return value
