"""Analysis helpers for MMSR reports."""

from mmsr.analysis.commentary import (
    CommentaryFact,
    TemplateCommentaryEngine,
    commentary_facts_from_comparisons,
    section_summary_fact_from_comparisons,
)
from mmsr.analysis.comparison import (
    ComparisonPolicy,
    ReferenceObservationSpec,
    compare_metric_timeseries,
    compare_reversion_metric_timeseries,
)

__all__ = [
    "CommentaryFact",
    "ComparisonPolicy",
    "ReferenceObservationSpec",
    "TemplateCommentaryEngine",
    "compare_metric_timeseries",
    "commentary_facts_from_comparisons",
    "section_summary_fact_from_comparisons",
    "compare_reversion_metric_timeseries",
]
