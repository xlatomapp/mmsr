from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import (
    CommentaryBlock,
    MetricCard,
    ReportBranding,
    ReportDocument,
    ReportPage,
)
from mmsr.report.render_html import render_metric_card, render_report

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
