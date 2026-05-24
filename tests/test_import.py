from mmsr import __version__


def test_version() -> None:
    assert __version__ == "0.1.0"


def test_kdb_public_runner_api_imports() -> None:
    from mmsr.kdb import (
        KdbMetricRunner,
        MetricRunRequest,
        normalize_metric_result,
        toxicity_reversion_input_schema_contracts,
        toxicity_reversion_output_schema_contract,
    )

    assert KdbMetricRunner is not None
    assert MetricRunRequest is not None
    assert normalize_metric_result is not None
    assert toxicity_reversion_input_schema_contracts is not None
    assert toxicity_reversion_output_schema_contract is not None


def test_config_public_api_imports() -> None:
    from mmsr.config import ReportConfig, ToxicityConfig

    assert ReportConfig is not None
    assert ToxicityConfig is not None


def test_visual_public_api_imports() -> None:
    from mmsr.visuals import (
        ReversionCurvePoint,
        flag_reversion_curve_confidence,
        reversion_commentary_facts_from_curve_points,
        reversion_curve_points_from_timeseries,
    )

    assert ReversionCurvePoint is not None
    assert flag_reversion_curve_confidence is not None
    assert reversion_commentary_facts_from_curve_points is not None
    assert reversion_curve_points_from_timeseries is not None


def test_analysis_public_api_imports() -> None:
    from mmsr.analysis import (
        CommentaryFact,
        TemplateCommentaryEngine,
        commentary_facts_from_comparisons,
        compare_reversion_metric_timeseries,
        section_summary_fact_from_comparisons,
    )

    assert CommentaryFact is not None
    assert TemplateCommentaryEngine is not None
    assert commentary_facts_from_comparisons is not None
    assert compare_reversion_metric_timeseries is not None
    assert section_summary_fact_from_comparisons is not None


def test_report_public_api_imports() -> None:
    from mmsr.report import (
        ComparisonSectionOptions,
        Heatmap,
        HeatmapCell,
        MetricDefinitionsAppendixOptions,
        MetricTable,
        MetricTableRow,
        TimeSeriesChart,
        TimeSeriesChartPoint,
        append_metric_definitions_appendix,
        build_comparison_metric_table,
        build_comparison_report_page,
        build_heatmap,
        build_metric_definitions_appendix_page,
        build_time_series_chart,
        collect_metric_definitions_from_pages,
        metric_definitions_markdown,
    )

    assert ComparisonSectionOptions is not None
    assert Heatmap is not None
    assert HeatmapCell is not None
    assert MetricDefinitionsAppendixOptions is not None
    assert MetricTable is not None
    assert MetricTableRow is not None
    assert TimeSeriesChart is not None
    assert TimeSeriesChartPoint is not None
    assert append_metric_definitions_appendix is not None
    assert build_comparison_metric_table is not None
    assert build_comparison_report_page is not None
    assert build_heatmap is not None
    assert build_metric_definitions_appendix_page is not None
    assert build_time_series_chart is not None
    assert collect_metric_definitions_from_pages is not None
    assert metric_definitions_markdown is not None

def test_examples_public_api_imports() -> None:
    from mmsr.examples import (
        OfflineDemoReportOptions,
        OfflineSampleMetrics,
        SAMPLE_REFERENCE_DATES,
        SAMPLE_REPORT_DATE,
        build_offline_demo_report,
        build_offline_metric_comparisons,
        build_offline_metric_time_series,
        build_offline_reference_time_series,
        build_offline_sample_metrics,
    )

    assert OfflineDemoReportOptions is not None
    assert OfflineSampleMetrics is not None
    assert SAMPLE_REFERENCE_DATES is not None
    assert SAMPLE_REPORT_DATE is not None
    assert build_offline_demo_report is not None
    assert build_offline_metric_comparisons is not None
    assert build_offline_metric_time_series is not None
    assert build_offline_reference_time_series is not None
    assert build_offline_sample_metrics is not None

