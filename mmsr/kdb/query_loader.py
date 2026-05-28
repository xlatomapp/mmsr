"""Load and render q/Jinja-style query templates from package resources."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import PurePath


_PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")
_PLACEHOLDER_BLOCK_RE = re.compile(r"{{(?P<body>.*?)}}", re.DOTALL)


class QueryTemplateError(ValueError):
    """Raised when a q template cannot be rendered deterministically."""


def load_q_template(name: str) -> str:
    """Load a q template by filename from the query_templates package directory.

    Template names must be simple ``.q.j2`` filenames. A legacy ``.q`` name is
    accepted and mapped to ``.q.j2`` so older callers fail less abruptly, but the
    repository stores rendered templates with the explicit template suffix.
    """
    if not name:
        raise ValueError("q template name must be non-empty")
    if PurePath(name).name != name:
        raise ValueError("q template name must be a filename, not a path")
    if name.endswith(".q"):
        name = name + ".j2"
    if not name.endswith(".q.j2"):
        raise ValueError("q template name must end with .q.j2")

    package = "mmsr.kdb.query_templates"
    template_path = resources.files(package).joinpath(name)
    if not template_path.is_file():
        raise FileNotFoundError(f"q template not found: {name}")
    return template_path.read_text(encoding="utf-8")



def load_q_library_template(name: str) -> str:
    """Load a reusable q library template by filename from the q_lib package."""

    if not name:
        raise ValueError("q library template name must be non-empty")
    if PurePath(name).name != name:
        raise ValueError("q library template name must be a filename, not a path")
    if not name.endswith(".q.j2"):
        raise ValueError("q library template name must end with .q.j2")

    package = "mmsr.kdb.q_lib"
    template_path = resources.files(package).joinpath(name)
    if not template_path.is_file():
        raise FileNotFoundError(f"q library template not found: {name}")
    return template_path.read_text(encoding="utf-8")

def template_parameters(template: str) -> frozenset[str]:
    """Return the unique named placeholders required by ``template``.

    Placeholders must use the explicit ``{{ name }}`` form, where ``name`` is a
    Python/q-friendly identifier. Invalid placeholder blocks fail early instead
    of being left unresolved in rendered q.
    """
    parameters: set[str] = set()
    for match in _PLACEHOLDER_BLOCK_RE.finditer(template):
        block = match.group(0)
        body = match.group("body").strip()
        placeholder = _PLACEHOLDER_RE.fullmatch(block)
        if placeholder is None:
            raise QueryTemplateError(
                f"invalid q template placeholder {block!r}; expected {{{{ name }}}}"
            )
        parameters.add(body)
    return frozenset(parameters)


def render_template(template: str, params: dict[str, str]) -> str:
    """Render a q template using strict explicit named placeholders.

    Rendering is intentionally conservative:

    - every placeholder in the template must be provided in ``params``;
    - every supplied parameter must be used by the template;
    - parameter names must be valid identifiers;
    - parameter values must already be q snippets represented as strings.

    The renderer only substitutes complete ``{{ name }}`` placeholders. It does
    not evaluate expressions or perform implicit escaping.
    """
    required = template_parameters(template)
    supplied = frozenset(params)

    invalid_keys = sorted(key for key in supplied if not _is_valid_parameter_name(key))
    if invalid_keys:
        raise QueryTemplateError(
            "invalid q template parameter name(s): " + ", ".join(invalid_keys)
        )

    missing = sorted(required - supplied)
    if missing:
        raise QueryTemplateError(
            "missing q template parameter(s): " + ", ".join(missing)
        )

    unused = sorted(supplied - required)
    if unused:
        raise QueryTemplateError("unused q template parameter(s): " + ", ".join(unused))

    non_string_keys = sorted(
        key for key, value in params.items() if not isinstance(value, str)
    )
    if non_string_keys:
        raise TypeError(
            "q template parameter value(s) must be strings: "
            + ", ".join(non_string_keys)
        )

    return _PLACEHOLDER_RE.sub(lambda match: params[match.group(1)], template)


def _is_valid_parameter_name(name: str) -> bool:
    """Return whether ``name`` is accepted as a template parameter name."""
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))


def render_calculation_function_bootstrap(calculation_namespace: str) -> str:
    """Render MMSR-owned reusable q helper functions for a calculation namespace.

    User-owned kdb functions should only supply calendar, symbols, and raw
    canonical source rows. MMSR installs/uses these helper functions in the
    configured namespace so metric aggregation logic remains owned by the
    package rather than by the user's source-data boundary.
    """
    if not isinstance(calculation_namespace, str) or not calculation_namespace:
        raise ValueError("calculation_namespace must be a non-empty string")
    if not calculation_namespace.startswith("."):
        raise ValueError("calculation_namespace must start with '.'")
    if not re.fullmatch(
        r"\.[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*",
        calculation_namespace,
    ):
        raise ValueError(f"invalid calculation_namespace: {calculation_namespace!r}")
    return render_template(
        load_q_library_template("mmsr_calculations.q.j2"),
        {"calculation_namespace": calculation_namespace},
    )
