"""Load and render the canonical MMSR q library."""

from __future__ import annotations

import re
from importlib import resources
from pathlib import PurePath

_PLACEHOLDER_RE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")
_PLACEHOLDER_BLOCK_RE = re.compile(r"{{(?P<body>.*?)}}", re.DOTALL)


class QueryTemplateError(ValueError):
    """Raised when a q template cannot be rendered deterministically."""


def load_q_template(name: str) -> str:
    """Deprecated metric-template loader.

    Runtime query planning no longer loads per-metric q templates. All MMSR q
    functions are installed from ``q_lib/mmsr_calculations.q.j2``.
    """

    raise FileNotFoundError(f"metric q template files were removed; use installed q functions instead: {name}")


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


def load_metric_calculation_block(name: str) -> str:
    """Deprecated metric-block loader; metric q is installed as functions."""

    return load_q_template(name)


load_metric_q_template = load_metric_calculation_block


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
            raise QueryTemplateError(f"invalid q template placeholder {block!r}; expected {{{{ name }}}}")
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
        raise QueryTemplateError("invalid q template parameter name(s): " + ", ".join(invalid_keys))

    missing = sorted(required - supplied)
    if missing:
        raise QueryTemplateError("missing q template parameter(s): " + ", ".join(missing))

    unused = sorted(supplied - required)
    if unused:
        raise QueryTemplateError("unused q template parameter(s): " + ", ".join(unused))

    non_string_keys = sorted(key for key, value in params.items() if not isinstance(value, str))
    if non_string_keys:
        raise TypeError("q template parameter value(s) must be strings: " + ", ".join(non_string_keys))

    return _PLACEHOLDER_RE.sub(lambda match: params[match.group(1)], template)


def _is_valid_parameter_name(name: str) -> bool:
    """Return whether ``name`` is accepted as a template parameter name."""
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name))


def _validate_q_namespace(value: str, field_name: str) -> str:
    """Validate and return a q namespace used for rendered q bootstraps."""

    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if not value.startswith("."):
        raise ValueError(f"{field_name} must start with '.'")
    if (
        re.fullmatch(
            r"\.[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)*",
            value,
        )
        is None
    ):
        raise ValueError(f"invalid {field_name}: {value!r}")
    return value


def _validate_positive_int(value: int, field_name: str) -> int:
    """Validate positive integer q bootstrap options."""

    if not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 1:
        raise ValueError(f"{field_name} must be positive")
    return value


def _shared_q_library_template() -> str:
    """Return the single canonical q library template."""

    return load_q_library_template("mmsr_calculations.q.j2")


def render_calculation_function_bootstrap(calculation_namespace: str) -> str:
    """Render MMSR-owned reusable q helper functions for a calculation namespace.

    User-owned kdb functions should only supply calendar, symbols, and raw
    canonical source rows. MMSR installs/uses these helper functions in the
    configured namespace so metric aggregation logic remains owned by the
    package rather than by the user's source-data boundary.
    """

    calculation_namespace = _validate_q_namespace(
        calculation_namespace,
        "calculation_namespace",
    )
    return render_template(
        _shared_q_library_template(),
        {"calculation_namespace": calculation_namespace},
    )


def _simulated_source_q_library_template() -> str:
    """Return the deterministic dev/debug q source-function template."""

    return load_q_library_template("mmsr_simulated_sources.q.j2")


def render_simulated_source_function_bootstrap(
    source_namespace: str = ".sim.mmsr",
    *,
    symbol_count: int = 240,
) -> str:
    """Render deterministic q source functions for development/debugging.

    The rendered q defines ``getTradingCalendar``, ``getRef``, ``getTrade``,
    ``getQuote``, ``getPtsTrade``, ``getPtsQuote``, and ``getPrimaryQuote`` in
    ``source_namespace``. These functions implement the same source boundary as
    the production runner but synthesize deterministic rows so a developer can
    generate reports without production trade/quote/reference tables.

    ``symbol_count`` controls the default q universe size baked into the
    bootstrap file. Operators may still override ``<namespace>.symbolCount`` in
    q after loading the generated file for ad hoc stress tests.
    """

    source_namespace = _validate_q_namespace(source_namespace, "source_namespace")
    symbol_count_value = _validate_positive_int(symbol_count, "symbol_count")
    return render_template(
        _simulated_source_q_library_template(),
        {
            "source_namespace": source_namespace,
            "symbol_count": str(symbol_count_value),
        },
    )
