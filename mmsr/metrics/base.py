"""Metric definition domain objects."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MetricDefinition:
    """First-class definition and documentation for a report metric."""

    name: str
    label: str
    category: str
    description: str
    formula: str
    interpretation: str
    unit: str
    higher_is_better: bool | None
    default_aggregation: str
    supports_intraday: bool
    supports_symbol_level: bool
    required_tables: list[str]
    required_columns: list[str]
    caveats: list[str] = field(default_factory=list)
    formula_latex: str | None = None

    def help_text(self) -> str:
        """Return user-facing help text for info icons or appendices."""
        caveats = "\n".join(f"- {item}" for item in self.caveats) or "- None"
        return (
            f"{self.label}\n\n"
            f"What it measures:\n{self.description}\n\n"
            f"Formula:\n{self.formula}\n\n"
            f"How to interpret:\n{self.interpretation}\n\n"
            f"Unit: {self.unit}\n"
            f"Default aggregation: {self.default_aggregation}\n\n"
            f"Caveats:\n{caveats}"
        )
