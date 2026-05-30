from mmsr.examples.mock_kdb_demo import build_mock_kdb_integration_demo_report
from mmsr.examples.offline_demo import build_offline_demo_report
from mmsr.report.budgets import (
    ReportBudgetLimits,
    evaluate_report_budget,
    snapshot_report_budget,
)
from mmsr.report.render_html import render_report


def test_offline_demo_report_stays_within_default_budget_limits() -> None:
    document = build_offline_demo_report()
    html = render_report(document)
    snapshot = snapshot_report_budget(document, html)
    violations = evaluate_report_budget(snapshot, ReportBudgetLimits())

    assert violations == ()
    assert snapshot.page_count >= 5
    assert snapshot.total_chart_count >= 3


def test_mock_kdb_demo_report_stays_within_default_budget_limits() -> None:
    document = build_mock_kdb_integration_demo_report()
    html = render_report(document)
    snapshot = snapshot_report_budget(document, html)
    violations = evaluate_report_budget(snapshot, ReportBudgetLimits())

    assert violations == ()
    assert snapshot.metric_row_count > 0
    assert snapshot.metric_table_count >= 1


def test_budget_evaluator_reports_exceeded_limits() -> None:
    document = build_offline_demo_report()
    html = render_report(document)
    snapshot = snapshot_report_budget(document, html)
    limits = ReportBudgetLimits(
        max_html_size_bytes=100,
        max_total_chart_count=1,
        max_metric_table_count=0,
        max_metric_row_count=1,
        max_page_count=1,
    )
    violations = evaluate_report_budget(snapshot, limits)

    assert violations
    assert any("html_size_bytes" in violation for violation in violations)
    assert any("total_chart_count" in violation for violation in violations)
