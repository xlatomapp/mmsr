from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def load_pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_runtime_dependencies_stay_lean() -> None:
    data = load_pyproject()
    runtime_dependencies = set(data["tool"]["poetry"]["dependencies"])

    assert "jinja2" in runtime_dependencies
    assert "typer" in runtime_dependencies
    assert "pykx" in runtime_dependencies
    assert "pytest" not in runtime_dependencies
    assert "black" not in runtime_dependencies
    assert "mkdocs" not in runtime_dependencies
    assert "mkdocs-material" not in runtime_dependencies
    assert "mkdocstrings" not in runtime_dependencies


def test_dev_and_doc_dependency_groups_are_explicit() -> None:
    data = load_pyproject()
    groups = data["tool"]["poetry"]["group"]

    assert "dev" in groups
    assert "doc" in groups

    dev_dependencies = set(groups["dev"]["dependencies"])
    doc_dependencies = set(groups["doc"]["dependencies"])

    assert {"pytest", "black", "isort", "flake8", "mypy", "tox", "pre-commit"} <= (
        dev_dependencies
    )
    assert {"mkdocs", "mkdocs-material", "mkdocstrings"} <= doc_dependencies


def test_readme_documents_installation_profiles() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "## Installation profiles" in text
    assert "poetry install --only main" in text
    assert "poetry install --extras kdb" in text
    assert "poetry install --with dev" in text
    assert "poetry install --with doc" in text
    assert "poetry run mkdocs build --strict" in text
    assert "outside the runtime path preserves a\nminimal production install" in text


def test_tox_and_ci_validate_documentation_build_path() -> None:
    tox_text = (ROOT / "tox.ini").read_text(encoding="utf-8")
    ci_text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "docs" in tox_text
    assert "poetry install --with doc" in tox_text
    assert "poetry run mkdocs build --strict" in tox_text

    assert "Documentation build" in ci_text
    assert "poetry install --with doc --no-interaction" in ci_text
    assert "poetry run mkdocs build --strict" in ci_text


def test_roadmap_records_packaging_progress_and_remaining_cli_work() -> None:
    text = (ROOT / "_docs" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "A dedicated `doc` Poetry group" in text
    assert "`mkdocs`, `mkdocs-material`, and `mkdocstrings[python]`" in text
    assert "CLI behavior snapshots preserve the Typer command surface" in text
    assert "The CLI now uses Typer as an explicit runtime dependency" in text
