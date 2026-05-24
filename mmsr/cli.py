"""Command line interface for mmsr."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from mmsr.examples import OfflineDemoReportOptions, build_offline_demo_report
from mmsr.report.render_html import render_report


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(
        prog="mmsr",
        description=(
            "Generate Japanese market microstructure monitoring report artifacts."
        ),
    )
    subparsers = parser.add_subparsers(dest="command")

    offline_demo = subparsers.add_parser(
        "offline-demo",
        help="Render the deterministic offline demo HTML report.",
        description=(
            "Render a deterministic synthetic HTML report without importing PyKX, "
            "connecting to kdb+, or calling an LLM."
        ),
    )
    offline_demo.add_argument(
        "-o",
        "--output",
        default="mmsr_offline_demo.html",
        help="Output HTML path. Parent directories are created automatically.",
    )
    offline_demo.add_argument(
        "--template-dir",
        default=None,
        help="Optional directory containing report.html.j2 and partial templates.",
    )
    offline_demo.add_argument(
        "--title",
        default=None,
        help="Override the offline demo report title.",
    )
    offline_demo.add_argument(
        "--brand-name",
        default=None,
        help="Override the rendered report brand name.",
    )
    offline_demo.add_argument(
        "--generated-at-text",
        default=None,
        help="Override the generated-at text shown in the rendered report.",
    )
    offline_demo.add_argument(
        "--no-appendix",
        action="store_true",
        help="Omit the metric definitions appendix from the offline demo.",
    )
    offline_demo.add_argument(
        "--max-metric-cards",
        type=int,
        default=None,
        help="Optional limit for summary metric cards.",
    )
    offline_demo.add_argument(
        "--max-comments",
        type=int,
        default=None,
        help="Optional limit for deterministic commentary lines.",
    )
    offline_demo.add_argument(
        "--max-table-rows",
        type=int,
        default=None,
        help="Optional limit for comparison table rows.",
    )
    offline_demo.add_argument(
        "--max-chart-points",
        type=int,
        default=None,
        help="Optional limit for points per time-series chart placeholder.",
    )
    offline_demo.add_argument(
        "--max-heatmap-cells",
        type=int,
        default=None,
        help="Optional limit for cells per heatmap placeholder.",
    )
    offline_demo.set_defaults(handler=_handle_offline_demo)

    return parser


def render_offline_demo_report_file(
    output_path: str | Path,
    *,
    options: OfflineDemoReportOptions | None = None,
    template_dir: str | Path | None = None,
) -> Path:
    """Render the deterministic offline demo report to an HTML file.

    The function is intentionally offline-only. It delegates report assembly to
    ``build_offline_demo_report()`` and HTML rendering to ``render_report()``,
    then writes the deterministic HTML artifact to ``output_path``.
    """

    resolved_output_path = Path(output_path)
    if resolved_output_path.exists() and resolved_output_path.is_dir():
        raise ValueError("output_path must be a file path, not a directory")

    document = build_offline_demo_report(options=options)
    html = render_report(document, template_dir=template_dir)

    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    resolved_output_path.write_text(html, encoding="utf-8")
    return resolved_output_path


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return int(args.handler(args))


def _handle_offline_demo(args: argparse.Namespace) -> int:
    options = _offline_demo_options_from_args(args)
    output_path = render_offline_demo_report_file(
        args.output,
        options=options,
        template_dir=args.template_dir,
    )
    print(f"Rendered offline demo report: {output_path}")
    return 0


def _offline_demo_options_from_args(
    args: argparse.Namespace,
) -> OfflineDemoReportOptions:
    defaults = OfflineDemoReportOptions()
    return OfflineDemoReportOptions(
        title=args.title or defaults.title,
        brand_name=args.brand_name or defaults.brand_name,
        generated_at_text=args.generated_at_text or defaults.generated_at_text,
        summary_page_title=defaults.summary_page_title,
        detail_page_title=defaults.detail_page_title,
        comparison_table_title=defaults.comparison_table_title,
        comparison_help_text=defaults.comparison_help_text,
        detail_help_text=defaults.detail_help_text,
        include_metric_definitions_appendix=not args.no_appendix,
        max_metric_cards=_default_when_none(
            args.max_metric_cards,
            defaults.max_metric_cards,
        ),
        max_comments=_default_when_none(args.max_comments, defaults.max_comments),
        max_table_rows=args.max_table_rows,
        max_chart_points=args.max_chart_points,
        max_heatmap_cells=args.max_heatmap_cells,
    )


def _default_when_none(value: int | None, default: int) -> int:
    if value is None:
        return default
    return value


if __name__ == "__main__":
    raise SystemExit(main())
