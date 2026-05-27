from mmsr.examples import OfflineDemoReportOptions, build_offline_demo_report
from mmsr.report.components import HtmlBlock, ReportDocument, ReportPage
from mmsr.report.render_html import render_report


def test_report_metric_help_controls_are_expandable_not_title_only_buttons() -> None:
    html = render_report(
        build_offline_demo_report(
            options=OfflineDemoReportOptions(include_intraday_heatmaps=True)
        )
    )

    assert '<details class="metric-help">' in html
    assert '<summary class="metric-help__summary metric-info"' in html
    assert "Metric definition" in html
    assert "Table help" in html
    assert "Chart help" in html
    assert "Heatmap help" in html
    assert "Formula:" in html
    assert "Mock current observations compared with 30 historical trading-day" in html
    assert "<button" not in html
    assert ' title="' not in html


def test_trusted_html_blocks_use_same_accessible_help_control() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Appendix",
                html_blocks=[
                    HtmlBlock(
                        title="Metric Definitions",
                        body_html="<p>Definitions body.</p>",
                        help_text="Definitions are sourced from the metric registry.",
                    )
                ],
            )
        ],
    )

    html = render_report(document)

    assert "Section help" in html
    assert "Definitions are sourced from the metric registry." in html
    assert '<details class="metric-help">' in html
    assert "<button" not in html
    assert ' title="' not in html
