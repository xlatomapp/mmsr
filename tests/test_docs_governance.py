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
    assert "does not query kdb+" in text
