"""Offline example fixtures and demo helpers."""

from mmsr.examples.offline_demo import (
    OfflineDemoReportOptions,
    build_offline_demo_report,
)
from mmsr.examples.mock_kdb_demo import (
    DeterministicMockKdbClient,
    MockKdbIntegrationDemoOptions,
    MockKdbIntegrationDemoResult,
    build_mock_kdb_integration_demo_report,
    build_mock_kdb_integration_demo_result,
)
from mmsr.examples.offline_fixtures import (
    OfflineSampleMetrics,
    SAMPLE_REFERENCE_DATES,
    SAMPLE_REPORT_DATE,
    build_offline_metric_comparisons,
    build_offline_metric_time_series,
    build_offline_reference_time_series,
    build_offline_sample_metrics,
    build_offline_symbol_metric_comparisons,
    build_offline_symbol_metric_time_series,
)

__all__ = [
    "DeterministicMockKdbClient",
    "MockKdbIntegrationDemoOptions",
    "MockKdbIntegrationDemoResult",
    "OfflineDemoReportOptions",
    "OfflineSampleMetrics",
    "SAMPLE_REFERENCE_DATES",
    "SAMPLE_REPORT_DATE",
    "build_mock_kdb_integration_demo_report",
    "build_mock_kdb_integration_demo_result",
    "build_offline_demo_report",
    "build_offline_metric_comparisons",
    "build_offline_metric_time_series",
    "build_offline_reference_time_series",
    "build_offline_sample_metrics",
    "build_offline_symbol_metric_comparisons",
    "build_offline_symbol_metric_time_series",
]
