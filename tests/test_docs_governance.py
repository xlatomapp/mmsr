from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_journal_lives_under_docs() -> None:
    assert (ROOT / "_docs" / "journal.md").is_file()
    assert not (ROOT / "journal.md").exists()


def test_governance_docs_reference_canonical_journal_path() -> None:
    checked = [
        ROOT / "README.md",
        ROOT / "_docs" / "AGENTS.md",
        ROOT / "_docs" / "CUSTOM_GPT_INSTRUCTIONS.md",
        ROOT / "_docs" / "ROADMAP.md",
    ]

    for path in checked:
        text = path.read_text(encoding="utf-8")
        assert "_docs/journal.md" in text


def test_readme_documents_offline_demo_quickstart() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "poetry run mmsr offline-demo --output reports/offline_demo.html" in text
    assert "synthetic normalized metrics" in text
    assert "without a live kdb+ connection, PyKX import, or LLM call" in text
    assert "build_market_monitor_report()" in text
    assert "only the data source changes" in text
    assert "does not query kdb+" in text


def test_readme_documents_mock_kdb_demo_quickstart() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "poetry run mmsr mock-kdb-demo --output reports/mock_kdb_demo.html" in text
    assert "executes rendered q templates" in text
    assert "KdbMetricRunner" in text
    assert "without a live\nkdb+ connection or PyKX import" in text


def test_mkdocs_quickstart_documents_drilldown_demo_options() -> None:
    doc = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    required_terms = [
        "poetry run mmsr offline-demo --output reports/offline_demo.html",
        "poetry run mmsr mock-kdb-demo --output reports/mock_kdb_demo.html",
        "--max-drilldown-rows",
        "--no-drilldown-page",
        "--include-intraday-heatmaps",
        "sector, segment, and market-cap",
        "does not query kdb+",
        "without a live\nkdb+ connection or PyKX import",
    ]

    for term in required_terms:
        assert term in doc
        assert term in readme


def test_roadmap_tracks_packaging_and_cli_backlog() -> None:
    text = (ROOT / "_docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "ppw packaging parity and CLI ergonomics" in text
    assert "`dev` and `doc` optional dependency support" in text
    assert "Typer" in text
    assert "Runtime install remains lean" in text


def test_docs_document_live_kdb_integration_boundary() -> None:
    doc = (ROOT / "docs" / "kdb_integration_testing.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "_docs" / "ROADMAP.md").read_text(encoding="utf-8")
    status = (ROOT / "_docs" / "MILESTONE_STATUS.md").read_text(encoding="utf-8")
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    required_terms = [
        "MMSR_KDB_HOST",
        "MMSR_KDB_PORT",
        "MMSR_KDB_TRADE_FUNCTION",
        "MMSR_KDB_QUOTE_FUNCTION",
        "MMSR_KDB_CALENDAR_FUNCTION",
        "@pytest.mark.kdb_integration",
        "skipped by default",
        "toxicity_reversion",
        "MetricTimeSeries",
        "mmsr plan",
        "mmsr preflight",
        "getRef[date]",
        "getTrade[date;ref]",
        "getQuote[date;ref]",
        "Production preflight path",
    ]

    for term in required_terms:
        assert term in doc

    assert "docs/kdb_integration_testing.md" in readme
    assert "poetry run pytest -m kdb_integration" in readme
    assert "mmsr preflight" in readme
    assert "mock-vs-live integration-test" in roadmap
    assert "live-kdb integration-test guidance" in status
    assert "kdb_integration_testing.md" in mkdocs


def test_docs_document_production_readiness_checklist() -> None:
    doc = (ROOT / "docs" / "production_readiness.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    roadmap = (ROOT / "_docs" / "ROADMAP.md").read_text(encoding="utf-8")
    status = (ROOT / "_docs" / "MILESTONE_STATUS.md").read_text(encoding="utf-8")

    required_terms = [
        "Production readiness checklist",
        "sector taxonomy",
        "market-cap bucket",
        "Symbol metadata / taxonomy table",
        "Trading calendar function",
        "Trade raw-data function for `activity`",
        "Quote raw-data function for `liquidity`",
        "PTS trade raw-data function for `toxicity_reversion`",
        "PTS quote raw-data function for `toxicity_reversion`",
        "Primary quote raw-data function for `toxicity_reversion`",
        "bounded validation slice",
        "market-data owner",
    ]

    for term in required_terms:
        assert term in doc

    assert "docs/production_readiness.md" in readme
    assert "production_readiness.md" in index
    assert "Production readiness checklist: production_readiness.md" in mkdocs
    assert "Production readiness requirements are documented" in status
    assert "docs/production_readiness.md" in roadmap
    assert "production kdb source-function boundary" in roadmap
    assert ".sb.mmsr.getTrade" in readme
    assert ".sb.mmsr.getPtsQuote" in readme


def test_docs_define_report_scope_guardrails() -> None:
    scope = (ROOT / "docs" / "report_scope.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    index = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
    agents = (ROOT / "_docs" / "AGENTS.md").read_text(encoding="utf-8")
    custom = (ROOT / "_docs" / "CUSTOM_GPT_INSTRUCTIONS.md").read_text(encoding="utf-8")
    roadmap = (ROOT / "_docs" / "ROADMAP.md").read_text(encoding="utf-8")
    status = (ROOT / "_docs" / "MILESTONE_STATUS.md").read_text(encoding="utf-8")
    production = (ROOT / "docs" / "production_readiness.md").read_text(encoding="utf-8")
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    required_scope_terms = [
        "market-monitoring report",
        "not a transaction-cost analysis",
        "execution-quality",
        "smart order-routing",
        "generic validation-framework",
        "Default report metric set",
        "primary_quote_reversion_10ms_bps",
        "primary_quote_reversion_10s_bps",
        "Out of scope for the default report",
        "effective spread",
        "implementation shortfall",
        "slippage",
        "price impact",
        "Implementation gate",
        "docs/report_scope.md",
    ]

    for term in required_scope_terms:
        assert term in scope

    required_cross_doc_terms = [
        "docs/report_scope.md",
        "transaction-cost analysis",
        "execution quality",
        "price impact",
        "generic validation",
    ]

    for doc in [readme, index, agents, custom, roadmap, status, production]:
        for term in required_cross_doc_terms:
            assert term in doc

    assert "Report scope guardrails: report_scope.md" in mkdocs
