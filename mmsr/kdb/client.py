"""PyKX client abstraction.

PyKX is imported lazily so unit tests and docs can run without installing PyKX.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class KdbConfig:
    """kdb+ connection configuration."""

    host: str
    port: int
    username: str | None = None
    password: str | None = None


class KdbClient:
    """Thin wrapper around a PyKX QConnection."""

    def __init__(self, config: KdbConfig) -> None:
        self.config = config
        self._connection: Any | None = None

    def connect(self) -> None:
        """Open the PyKX connection."""
        try:
            import pykx as kx  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "PyKX is required for kdb connectivity. Install with: "
                "poetry install --extras kdb"
            ) from exc

        self._connection = kx.QConnection(
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
        )

    def execute(self, query: str, *args: Any) -> Any:
        """Execute a q query."""
        if self._connection is None:
            self.connect()
        assert self._connection is not None
        return self._connection(query, *args)
