"""Deterministic template commentary."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricComparison
from mmsr.presentation.labels import (
    format_group_label,
    format_intraday_bucket_label,
    format_reference_observation_unit_label,
)


@dataclass(frozen=True)
class CommentaryFact:
    """A grounded fact used by the template commentary engine."""

    metric_label: str
    group: dict[str, str]
    value_text: str
    reference_text: str | None
    change_text: str | None
    z_score: float | None
    status: str
    direction_word: str
    caveats: list[str] = field(default_factory=list)
    fact_type: str = "metric"


class TemplateCommentaryEngine:
    """Generate deterministic commentary from structured facts."""

    def generate(self, facts: list[CommentaryFact], max_comments: int = 5) -> list[str]:
        """Generate deterministic comments."""
        comments: list[str] = []
        priority = {"alert": 0, "watch": 1, "comparison_only": 2, "normal": 3}
        sorted_facts = sorted(
            facts,
            key=lambda fact: (
                0 if fact.fact_type == "section_summary" else 1,
                priority.get(fact.status, 99),
            ),
        )
        for fact in sorted_facts[:max_comments]:
            group = format_group_label(fact.group) or "the selected universe"
            caveat_text = _format_caveats(fact.caveats)
            if fact.fact_type == "section_summary":
                comments.append(f"{fact.metric_label} headline: {fact.value_text}.{caveat_text}")
            elif fact.status == "normal":
                comments.append(f"{fact.metric_label} was within the normal range for {group}.{caveat_text}")
            elif fact.status == "comparison_only":
                ref_text = "" if fact.reference_text is None else f" versus reference {fact.reference_text}"
                change_text = "" if fact.change_text is None else f" ({fact.change_text})"
                comments.append(
                    f"{fact.metric_label} comparison for {group}: current "
                    f"{fact.value_text}{ref_text}{change_text}; statistical score "
                    f"not shown.{caveat_text}"
                )
            else:
                z_text = "" if fact.z_score is None else f" with z-score {fact.z_score:.1f}"
                ref_text = "" if fact.reference_text is None else f" versus reference {fact.reference_text}"
                change_text = "" if fact.change_text is None else f" ({fact.change_text})"
                comments.append(
                    f"{fact.metric_label} was {fact.direction_word} for {group}: "
                    f"current {fact.value_text}{ref_text}{change_text}{z_text}."
                    f"{caveat_text}"
                )
        return comments


def commentary_facts_from_comparisons(
    comparisons: Sequence[MetricComparison],
    *,
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition] | None = None,
    max_facts: int | None = None,
) -> tuple[CommentaryFact, ...]:
    """Convert comparison results into grounded deterministic commentary facts.

    The function does not infer facts from raw data or use an LLM. It only formats
    already-computed ``MetricComparison`` values, preserving the comparison status,
    reference sample size, z-score availability, and metric direction metadata.
    """

    if max_facts is not None and max_facts < 0:
        raise ValueError("max_facts must be non-negative")

    definitions = _metric_definition_map(metric_definitions)
    facts = tuple(_commentary_fact_from_comparison(comparison, definitions) for comparison in comparisons)
    ordered = tuple(sorted(facts, key=_comparison_fact_sort_key))
    if max_facts is None:
        return ordered
    return ordered[:max_facts]


def section_summary_fact_from_comparisons(
    section_title: str,
    comparisons: Sequence[MetricComparison],
    *,
    scope_label: str = "all comparisons",
) -> CommentaryFact:
    """Build a deterministic section-level status summary fact.

    The fact only counts already-computed comparison statuses. It intentionally
    does not recalculate analytics, infer causes, or call an LLM.
    """

    title = section_title.strip()
    if not title:
        raise ValueError("section_title must not be empty")

    scope = scope_label.strip()
    if not scope:
        raise ValueError("scope_label must not be empty")

    status_counts = _comparison_status_counts(comparisons)
    total = sum(status_counts.values())
    status = _section_summary_status(status_counts)
    return CommentaryFact(
        metric_label=title,
        group={},
        value_text=_format_section_summary_value(status_counts, total, scope),
        reference_text=None,
        change_text=None,
        z_score=None,
        status=status,
        direction_word="summary",
        caveats=[],
        fact_type="section_summary",
    )


def _commentary_fact_from_comparison(
    comparison: MetricComparison,
    metric_definitions: Mapping[str, MetricDefinition],
) -> CommentaryFact:
    definition = metric_definitions.get(comparison.metric_name)
    unit = "" if definition is None else definition.unit
    label = comparison.metric_name if definition is None else definition.label

    return CommentaryFact(
        metric_label=label,
        group=_comparison_group(comparison),
        value_text=_format_metric_value(comparison.value, unit),
        reference_text=(
            None if comparison.reference_value is None else _format_metric_value(comparison.reference_value, unit)
        ),
        change_text=_format_change(comparison, unit),
        z_score=comparison.z_score,
        status=comparison.status,
        direction_word=_comparison_direction_word(comparison),
        caveats=_comparison_caveats(comparison),
    )


def _comparison_status_counts(
    comparisons: Sequence[MetricComparison],
) -> dict[str, int]:
    counts = {
        "alert": 0,
        "watch": 0,
        "comparison_only": 0,
        "normal": 0,
        "other": 0,
    }
    for comparison in comparisons:
        if comparison.status in counts:
            counts[comparison.status] += 1
        else:
            counts["other"] += 1
    return counts


def _section_summary_status(status_counts: Mapping[str, int]) -> str:
    if status_counts.get("alert", 0) > 0:
        return "alert"
    if status_counts.get("watch", 0) > 0:
        return "watch"
    if status_counts.get("comparison_only", 0) > 0:
        return "comparison_only"
    return "normal"


def _format_section_summary_value(
    status_counts: Mapping[str, int],
    total: int,
    scope_label: str,
) -> str:
    if total == 0:
        return f"no comparison rows were available across {scope_label}"

    parts = [
        _pluralize(status_counts.get("alert", 0), "alert"),
        _pluralize(status_counts.get("watch", 0), "watch item"),
        _pluralize(status_counts.get("comparison_only", 0), "comparison-only item"),
        _pluralize(status_counts.get("normal", 0), "normal item"),
    ]
    other_count = status_counts.get("other", 0)
    if other_count:
        parts.append(_pluralize(other_count, "other item"))

    return f"{_join_phrase(parts)} across {_pluralize(total, 'comparison')} in {scope_label}"


def _pluralize(count: int, singular: str) -> str:
    if count == 1:
        return f"1 {singular}"
    if singular.endswith("y"):
        return f"{count} {singular[:-1]}ies"
    return f"{count} {singular}s"


def _join_phrase(parts: Sequence[str]) -> str:
    if len(parts) <= 1:
        return "".join(parts)
    if len(parts) == 2:
        return " and ".join(parts)
    return ", ".join(parts[:-1]) + f", and {parts[-1]}"


def _metric_definition_map(
    metric_definitions: Mapping[str, MetricDefinition] | Iterable[MetricDefinition] | None,
) -> dict[str, MetricDefinition]:
    if metric_definitions is None:
        return {}
    if isinstance(metric_definitions, Mapping):
        return dict(metric_definitions)
    return {definition.name: definition for definition in metric_definitions}


def _comparison_group(comparison: MetricComparison) -> dict[str, str]:
    group = {str(key): str(value) for key, value in comparison.group.items()}
    if comparison.time_bucket is not None and "time_bucket" not in group:
        bucket_label = format_intraday_bucket_label(comparison.time_bucket)
        if bucket_label is not None:
            group["time_bucket"] = bucket_label
    return group


def _format_metric_value(value: float | int | None, unit: str) -> str:
    if value is None:
        return "not available"

    numeric = float(value)
    if not isfinite(numeric):
        return "not available"

    if unit == "ratio":
        return f"{numeric:.4f}"
    if unit == "count":
        return f"{numeric:,.0f}"
    if unit == "JPY":
        return f"{numeric:,.0f} JPY"
    if unit:
        return f"{numeric:,.4f} {unit}"
    return f"{numeric:,.4f}"


def _format_change(comparison: MetricComparison, unit: str) -> str | None:
    parts: list[str] = []
    if comparison.change_abs is not None:
        parts.append(f"change {_format_signed_metric_value(comparison.change_abs, unit)}")
    if comparison.change_pct is not None:
        parts.append(f"{comparison.change_pct:+.1%}")
    return " ".join(parts) if parts else None


def _format_signed_metric_value(value: float, unit: str) -> str:
    if not isfinite(float(value)):
        return "not available"
    if unit == "ratio":
        return f"{value:+.4f}"
    if unit == "count":
        return f"{value:+,.0f}"
    if unit == "JPY":
        return f"{value:+,.0f} JPY"
    if unit:
        return f"{value:+,.4f} {unit}"
    return f"{value:+,.4f}"


def _comparison_direction_word(comparison: MetricComparison) -> str:
    if comparison.change_abs is None:
        return "changed"
    if comparison.change_abs > 0:
        return "higher"
    if comparison.change_abs < 0:
        return "lower"
    return "unchanged"


def _comparison_caveats(comparison: MetricComparison) -> list[str]:
    caveats: list[str] = []
    sample_size = comparison.reference_sample_size
    confidence = comparison.comparison_confidence

    if sample_size == 0:
        caveats.append("No comparable reference observations were available.")
    elif sample_size == 1:
        caveats.append("One reference observation; z-score is intentionally omitted.")
    elif confidence in {"insufficient", "weak"}:
        caveats.append(f"Low confidence: {sample_size} reference observations; statistical scores are limited.")

    if comparison.z_score is None and sample_size is not None and sample_size < 30:
        caveats.append("No z-score shown because fewer than 30 comparable observations were available.")

    reference_unit = comparison.metadata.get("reference_observation_unit")
    reference_unit_label = format_reference_observation_unit_label(reference_unit)
    if reference_unit_label:
        caveats.append(f"Reference observation unit: {reference_unit_label}.")

    return list(dict.fromkeys(caveats))


def _comparison_fact_sort_key(fact: CommentaryFact) -> tuple[int, float, str, str]:
    priority = {"alert": 0, "watch": 1, "comparison_only": 2, "normal": 3}
    z_magnitude = -abs(fact.z_score) if fact.z_score is not None else 0.0
    return (
        priority.get(fact.status, 99),
        z_magnitude,
        fact.metric_label,
        repr(sorted(fact.group.items())),
    )


def _format_caveats(caveats: list[str]) -> str:
    """Format grounded caveats for deterministic commentary output."""

    if not caveats:
        return ""
    return " Caveats: " + " ".join(caveats)
