import pytest

from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.starter_definitions import STARTER_METRICS
from mmsr.report.components import MetricCard, ReportDocument, ReportPage
from mmsr.report.metric_docs import (
    MetricDefinitionsAppendixOptions,
    append_metric_definitions_appendix,
    build_metric_definitions_appendix_page,
    collect_metric_definitions_from_pages,
    metric_definitions_markdown,
)
from mmsr.report.render_html import render_report


QUOTED_SPREAD_BPS = next(
    metric for metric in STARTER_METRICS if metric.name == "quoted_spread_bps"
)
VOLUME = next(metric for metric in STARTER_METRICS if metric.name == "volume")


def test_collect_metric_definitions_from_pages_deduplicates_and_sorts() -> None:
    pages = [
        ReportPage(
            title="Liquidity",
            metric_cards=[
                MetricCard(metric=QUOTED_SPREAD_BPS, value_text="12.4 bps"),
                MetricCard(metric=VOLUME, value_text="1,000 shares"),
            ],
        ),
        ReportPage(
            title="Activity",
            metric_cards=[MetricCard(metric=VOLUME, value_text="900 shares")],
        ),
    ]

    definitions = collect_metric_definitions_from_pages(pages)

    assert [definition.name for definition in definitions] == [
        "volume",
        "quoted_spread_bps",
    ]


def test_collect_metric_definitions_rejects_conflicting_duplicate_names() -> None:
    changed_volume = MetricDefinition(
        name=VOLUME.name,
        label="Changed Volume",
        category=VOLUME.category,
        description=VOLUME.description,
        formula=VOLUME.formula,
        interpretation=VOLUME.interpretation,
        unit=VOLUME.unit,
        higher_is_better=VOLUME.higher_is_better,
        default_aggregation=VOLUME.default_aggregation,
        supports_intraday=VOLUME.supports_intraday,
        supports_symbol_level=VOLUME.supports_symbol_level,
        required_tables=VOLUME.required_tables,
        required_columns=VOLUME.required_columns,
    )

    with pytest.raises(ValueError, match="conflicting metric definitions"):
        collect_metric_definitions_from_pages(
            [
                ReportPage(
                    title="A",
                    metric_cards=[MetricCard(metric=VOLUME, value_text="1")],
                ),
                ReportPage(
                    title="B",
                    metric_cards=[MetricCard(metric=changed_volume, value_text="2")],
                ),
            ]
        )


def test_build_metric_definitions_appendix_page_contains_full_help_fields() -> None:
    page = build_metric_definitions_appendix_page([QUOTED_SPREAD_BPS, VOLUME])

    assert page.title == "Metric Definitions Appendix"
    assert len(page.html_blocks) == 1
    html = page.html_blocks[0].body_html

    assert "Quoted Spread" in html
    assert "Formula" in html
    assert "askPrice" in html
    assert "Default aggregation" in html
    assert "Lower values are generally better" in html
    assert "Required tables" in html
    assert "quotes" in html
    assert "Caveats" in html
    assert page.html_blocks[0].help_text is not None


def test_metric_definitions_appendix_escapes_metric_text() -> None:
    metric = MetricDefinition(
        name="unsafe_metric",
        label="<Unsafe>",
        category="Test",
        description="Contains <script> tags.",
        formula="sum(<x>)",
        interpretation="Do not execute <anything>.",
        unit="bps",
        higher_is_better=False,
        default_aggregation="median",
        supports_intraday=True,
        supports_symbol_level=False,
        required_tables=["quotes<script>"],
        required_columns=["bidPrice"],
        caveats=["Watch <html> escaping."],
    )

    html = build_metric_definitions_appendix_page([metric]).html_blocks[0].body_html

    assert "&lt;Unsafe&gt;" in html
    assert "<script>" not in html
    assert "quotes&lt;script&gt;" in html


def test_append_metric_definitions_appendix_collects_from_document_pages() -> None:
    document = ReportDocument(
        title="MMSR",
        pages=[
            ReportPage(
                title="Liquidity",
                metric_cards=[
                    MetricCard(metric=QUOTED_SPREAD_BPS, value_text="12.4 bps")
                ],
            )
        ],
    )

    enriched = append_metric_definitions_appendix(document)

    assert len(document.pages) == 1
    assert len(enriched.pages) == 2
    assert enriched.pages[-1].title == "Metric Definitions Appendix"
    assert "Quoted Spread" in render_report(enriched)
    assert "Metric documentation" in render_report(enriched)


def test_metric_definitions_markdown_is_deterministic_and_complete() -> None:
    markdown = metric_definitions_markdown([QUOTED_SPREAD_BPS])

    assert "## Quoted Spread" in markdown
    assert "**Name:** `quoted_spread_bps`" in markdown
    assert "**Formula:** `10000 * (askPrice - bidPrice)" in markdown
    assert "**Direction:** Lower values are generally better" in markdown
    assert "**Caveats:** Can be distorted by stale" in markdown


def test_metric_definitions_appendix_options_validate_text() -> None:
    with pytest.raises(ValueError, match="title"):
        MetricDefinitionsAppendixOptions(title=" ")

    with pytest.raises(ValueError, match="block_title"):
        MetricDefinitionsAppendixOptions(block_title=" ")

    with pytest.raises(ValueError, match="help_text"):
        MetricDefinitionsAppendixOptions(help_text=" ")
