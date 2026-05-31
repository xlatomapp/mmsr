from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import (
    CommentaryBlock,
    MetricCard,
    ReportBranding,
    ReportDocument,
    ReportPage,
)
from mmsr.report.render_html import render_metric_card, render_report, render_report_v2

QUOTED_SPREAD_BPS = next(m for m in STARTER_METRICS if m.name == "quoted_spread_bps")


def test_metric_card_renders_info_button() -> None:
    card = MetricCard(
        metric=QUOTED_SPREAD_BPS,
        value_text="12.4 bps",
        reference_text="9.8 bps",
        status="alert",
    )

    html = render_metric_card(card)

    assert "Quoted Spread" in html
    assert "12.4 bps" in html
    assert "metric-info" in html
    assert "metric-card--alert" in html


def test_report_template_renders_branding_images() -> None:
    document = ReportDocument(
        title="Daily Market Microstructure Monitor",
        branding=ReportBranding(
            brand_name="Example Securities",
            logo_image_src="assets/logo.png",
            header_image_src="assets/header.png",
            footer_image_src="assets/footer.png",
            footer_text="Internal use only",
        ),
        generated_at_text="2026-05-24 08:00 JST",
        pages=[
            ReportPage(
                title="Executive Summary",
                metric_cards=[MetricCard(metric=QUOTED_SPREAD_BPS, value_text="12.4 bps")],
                commentary_blocks=[CommentaryBlock(title="Commentary", comments=["Spread widened."])],
            )
        ],
    )

    html = render_report(document)

    assert "Example Securities" in html
    assert "assets/logo.png" in html
    assert "assets/header.png" in html
    assert "assets/footer.png" in html
    assert "Internal use only" in html
    assert "Executive Summary" in html
    assert "Spread widened." in html


def test_report_v2_template_renders_fresh_top_header() -> None:
    document = ReportDocument(
        title="Equity Microstructure Intelligence Report",
        branding=ReportBranding(brand_name="Microstructure AI"),
        pages=[],
        header_meta={
            "subtitle": "Japanese Market Quantitative Analysis",
            "period_text": "2023-10-27 to 2023-11-27 (20 days)",
            "universe": "TSE",
            "benchmark_period_text": "2023-09-25 to 2023-10-25 (20 days)",
        },
    )

    html = render_report_v2(document)

    assert "report-header-v2" in html
    assert "Equity Microstructure Intelligence Report" in html
    assert "TSE" in html
    assert "2023-10-27 to 2023-11-27 (20 days)" in html
    assert "2023-09-25 to 2023-10-25 (20 days)" in html
    assert "Export PDF" in html
