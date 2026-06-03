"""Offline example fixtures and demo helpers."""

from mmsr.examples.offline_demo import (
    OfflineDemoReportOptions,
    build_offline_demo_report,
)
from mmsr.examples.offline_fixtures import (
    SAMPLE_REFERENCE_DATES,
    SAMPLE_REPORT_DATE,
    OfflineSampleMetrics,
    build_offline_metric_comparisons,
    build_offline_metric_time_series,
    build_offline_reference_time_series,
    build_offline_sample_metrics,
    build_offline_symbol_metric_comparisons,
    build_offline_symbol_metric_time_series,
)

__all__ = [
    "OfflineDemoReportOptions",
    "OfflineSampleMetrics",
    "SAMPLE_REFERENCE_DATES",
    "SAMPLE_REPORT_DATE",
    "build_offline_demo_report",
    "build_offline_metric_comparisons",
    "build_offline_metric_time_series",
    "build_offline_reference_time_series",
    "build_offline_sample_metrics",
    "build_offline_symbol_metric_comparisons",
    "build_offline_symbol_metric_time_series",
]
