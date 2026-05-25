"""Schema contracts for kdb q-template boundaries.

These contracts make the expected input and output shapes of q templates
explicit and unit-testable without a live kdb+ connection. They intentionally
validate the table/result boundary, not raw tick-level business logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

ACTIVITY_TRADES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "trade_price",
    "trade_size",
)
ACTIVITY_TRADES_ASSUMPTIONS: tuple[str, ...] = (
    "trade_price and trade_size are positive for included trades",
    "optional symbol filtering requires a sym column",
    "requested group_by columns must be present on the source table",
)
ACTIVITY_OUTPUT_AGGREGATE_COLUMNS: tuple[str, ...] = (
    "turnover",
    "volume",
    "trade_count",
)

LIQUIDITY_QUOTES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "bid_price",
    "ask_price",
    "bid_size",
    "ask_size",
)
LIQUIDITY_QUOTES_ASSUMPTIONS: tuple[str, ...] = (
    "bid_price and ask_price are positive numeric prices with ask_price > bid_price",
    "bid_size and ask_size are numeric top-of-book displayed sizes",
    "optional symbol filtering requires a sym column",
    "requested group_by columns must be present on the source table",
)
LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS: tuple[str, ...] = (
    "quoted_spread_bps",
    "top_of_book_depth",
)

STARTER_OUTPUT_BASE_COLUMNS: tuple[str, ...] = ("date", "time_bucket")

REVERSION_OUTPUT_METADATA_COLUMNS: tuple[str, ...] = (
    "horizon_sort_order",
    "trade_count",
    "notional",
    "positive_reversion_ratio",
    "valid_primary_quote_ratio",
)
REVERSION_OPTIONAL_OUTPUT_METADATA_COLUMNS: tuple[str, ...] = (
    "context_sort_order",
)
REVERSION_REQUIRED_GROUP_COLUMNS: tuple[str, ...] = ("venue", "horizon")
REVERSION_OUTPUT_BASE_COLUMNS: tuple[str, ...] = (
    "date",
    "time_bucket",
    *REVERSION_REQUIRED_GROUP_COLUMNS,
)
REVERSION_VENUE_TRADES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    "venue",
    "trade_price",
    "trade_size",
    "aggressor_side",
)
REVERSION_PRIMARY_QUOTES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    "venue",
    "bid_price",
    "ask_price",
)
REVERSION_VENUE_TRADES_ASSUMPTIONS: tuple[str, ...] = (
    "aggressor_side uses buy=1 and sell=-1",
    "trade_price and trade_size are positive for included trades",
    "requested group_by columns must be present after the template join/aggregation",
)
REVERSION_PRIMARY_QUOTES_ASSUMPTIONS: tuple[str, ...] = (
    "venue identifies the primary exchange quote source",
    "bid_price and ask_price are positive numeric prices with ask_price > bid_price",
)


class OutputSchemaContractError(ValueError):
    """Raised when a q-template boundary does not satisfy its schema contract."""


@dataclass(frozen=True)
class QTemplateInputTableSchemaContract:
    """Required source-table columns for a q template.

    ``table_role`` is the logical role used by the template, for example
    ``venue_trades`` or ``primary_quotes``. ``table_name`` is the configured
    production table name to display in validation errors.
    """

    template_name: str
    table_role: str
    table_name: str
    required_columns: tuple[str, ...]
    assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.template_name:
            raise ValueError("template_name must be non-empty")
        if not self.table_role:
            raise ValueError("table_role must be non-empty")
        if not self.table_name:
            raise ValueError("table_name must be non-empty")
        if not self.required_columns:
            raise ValueError("required_columns must contain at least one column")

    def validate_columns(self, columns: Sequence[str]) -> None:
        """Validate that a source table exposes every required column."""

        available = _column_name_set(columns)
        missing = [
            column for column in self.required_columns if column not in available
        ]
        if missing:
            raise OutputSchemaContractError(
                f"{self.template_name} input table {self.table_name!r} "
                f"for role {self.table_role!r} is missing required column(s): "
                + ", ".join(missing)
            )

    def validate_result_schema(self, result: Any) -> None:
        """Validate a table-like object by extracting its column names."""

        self.validate_columns(extract_result_columns(result))


@dataclass(frozen=True)
class QTemplateOutputSchemaContract:
    """Expected output columns for a q template after aggregation.

    ``metric_value_column`` is dynamic for templates that render the requested
    metric name as the value column. ``group_columns`` includes mandatory
    template-level groups and any caller-requested report breakdown columns.
    ``optional_columns`` documents extra columns the report layer understands
    when present, but does not require them for production queries.
    """

    template_name: str
    metric_value_column: str
    base_columns: tuple[str, ...]
    metadata_columns: tuple[str, ...] = ()
    group_columns: tuple[str, ...] = ()
    optional_columns: tuple[str, ...] = ()

    @property
    def required_columns(self) -> tuple[str, ...]:
        """All required columns in deterministic report-boundary order."""

        return _dedupe(
            (
                *self.base_columns,
                *self.group_columns,
                self.metric_value_column,
                *self.metadata_columns,
            )
        )

    @property
    def documented_columns(self) -> tuple[str, ...]:
        """Required plus supported optional columns in deterministic order."""

        return _dedupe((*self.required_columns, *self.optional_columns))

    def validate_columns(self, columns: Sequence[str]) -> None:
        """Validate that ``columns`` contain every required output column.

        Extra columns are allowed because production q may preserve diagnostic
        metadata. Supported optional columns are documented separately through
        ``optional_columns`` so manual q edits know which extra fields the
        Python report path already consumes.
        """

        available = _column_name_set(columns)
        missing = [
            column for column in self.required_columns if column not in available
        ]
        if missing:
            raise OutputSchemaContractError(
                f"{self.template_name} output is missing required column(s): "
                + ", ".join(missing)
            )

    def validate_result(self, result: Any) -> None:
        """Validate a dict/list/PyKX-like result against this contract."""

        self.validate_columns(extract_result_columns(result))


def activity_input_schema_contract(
    *,
    trades_table: str = "trades",
    extra_required_columns: Sequence[str] = (),
) -> QTemplateInputTableSchemaContract:
    """Return the source-table contract for ``activity.q``.

    ``extra_required_columns`` should include requested grouping columns and
    ``sym`` when callers render a symbol-bounded smoke/report query.
    """

    return QTemplateInputTableSchemaContract(
        template_name="activity.q",
        table_role="trades",
        table_name=trades_table,
        required_columns=_dedupe(
            (*ACTIVITY_TRADES_REQUIRED_COLUMNS, *extra_required_columns)
        ),
        assumptions=ACTIVITY_TRADES_ASSUMPTIONS,
    )


def liquidity_input_schema_contract(
    *,
    quotes_table: str = "quotes",
    extra_required_columns: Sequence[str] = (),
) -> QTemplateInputTableSchemaContract:
    """Return the source-table contract for ``liquidity.q``."""

    return QTemplateInputTableSchemaContract(
        template_name="liquidity.q",
        table_role="quotes",
        table_name=quotes_table,
        required_columns=_dedupe(
            (*LIQUIDITY_QUOTES_REQUIRED_COLUMNS, *extra_required_columns)
        ),
        assumptions=LIQUIDITY_QUOTES_ASSUMPTIONS,
    )


def activity_output_schema_contract(
    metric_name: str,
    *,
    group_by: Sequence[str] = (),
) -> QTemplateOutputSchemaContract:
    """Return the output-schema contract for ``activity.q``.

    ``activity.q`` emits every starter activity aggregate on each row, even when
    the runner is normalizing one requested metric. Keeping the sibling
    aggregate columns required makes the template boundary explicit and ensures
    those values remain available as row metadata for report diagnostics.
    """

    if metric_name not in ACTIVITY_OUTPUT_AGGREGATE_COLUMNS:
        raise OutputSchemaContractError(
            "activity.q schema contracts only apply to activity metrics: "
            + ", ".join(ACTIVITY_OUTPUT_AGGREGATE_COLUMNS)
        )

    return QTemplateOutputSchemaContract(
        template_name="activity.q",
        metric_value_column=metric_name,
        base_columns=STARTER_OUTPUT_BASE_COLUMNS,
        metadata_columns=tuple(
            column
            for column in ACTIVITY_OUTPUT_AGGREGATE_COLUMNS
            if column != metric_name
        ),
        group_columns=tuple(group_by),
    )


def liquidity_output_schema_contract(
    metric_name: str,
    *,
    group_by: Sequence[str] = (),
) -> QTemplateOutputSchemaContract:
    """Return the output-schema contract for ``liquidity.q``.

    ``liquidity.q`` emits every starter liquidity aggregate on each row. The
    non-requested aggregate column is required so the report boundary preserves
    it as deterministic row metadata.
    """

    if metric_name not in LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS:
        raise OutputSchemaContractError(
            "liquidity.q schema contracts only apply to liquidity metrics: "
            + ", ".join(LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS)
        )

    return QTemplateOutputSchemaContract(
        template_name="liquidity.q",
        metric_value_column=metric_name,
        base_columns=STARTER_OUTPUT_BASE_COLUMNS,
        metadata_columns=tuple(
            column
            for column in LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS
            if column != metric_name
        ),
        group_columns=tuple(group_by),
    )


def validate_activity_output_schema(
    *,
    metric_name: str,
    result: Any,
    group_by: Sequence[str] = (),
) -> None:
    """Validate an ``activity.q`` result object against its schema contract."""

    activity_output_schema_contract(metric_name, group_by=group_by).validate_result(
        result
    )


def validate_liquidity_output_schema(
    *,
    metric_name: str,
    result: Any,
    group_by: Sequence[str] = (),
) -> None:
    """Validate a ``liquidity.q`` result object against its schema contract."""

    liquidity_output_schema_contract(metric_name, group_by=group_by).validate_result(
        result
    )


def toxicity_reversion_input_schema_contracts(
    *,
    venue_trades_table: str = "venue_trades",
    primary_quotes_table: str = "primary_quotes",
    extra_required_columns: Sequence[str] = (),
) -> tuple[QTemplateInputTableSchemaContract, QTemplateInputTableSchemaContract]:
    """Return required production input-table schemas for ``toxicity_reversion.q``.

    These contracts intentionally encode only the columns and feed conventions
    the q template requires. They do not validate business quality, symbol
    coverage, or whether the input tables have enough observations for a report.
    """

    return (
        QTemplateInputTableSchemaContract(
            template_name="toxicity_reversion.q",
            table_role="venue_trades",
            table_name=venue_trades_table,
            required_columns=_dedupe(
                (*REVERSION_VENUE_TRADES_REQUIRED_COLUMNS, *extra_required_columns)
            ),
            assumptions=REVERSION_VENUE_TRADES_ASSUMPTIONS,
        ),
        QTemplateInputTableSchemaContract(
            template_name="toxicity_reversion.q",
            table_role="primary_quotes",
            table_name=primary_quotes_table,
            required_columns=REVERSION_PRIMARY_QUOTES_REQUIRED_COLUMNS,
            assumptions=REVERSION_PRIMARY_QUOTES_ASSUMPTIONS,
        ),
    )


def validate_toxicity_reversion_input_schemas(
    *,
    venue_trades_columns: Sequence[str],
    primary_quotes_columns: Sequence[str],
    venue_trades_table: str = "venue_trades",
    primary_quotes_table: str = "primary_quotes",
) -> None:
    """Validate source-table columns for ``toxicity_reversion.q``."""

    venue_contract, quote_contract = toxicity_reversion_input_schema_contracts(
        venue_trades_table=venue_trades_table,
        primary_quotes_table=primary_quotes_table,
    )
    venue_contract.validate_columns(venue_trades_columns)
    quote_contract.validate_columns(primary_quotes_columns)


def toxicity_reversion_output_schema_contract(
    metric_name: str,
    *,
    group_by: Sequence[str] = (),
) -> QTemplateOutputSchemaContract:
    """Return the output-schema contract for ``toxicity_reversion.q``.

    The reversion template must always emit ``venue`` and ``horizon`` in
    addition to the rendered metric value column. Caller-provided report groups,
    such as ``sym`` or ``sector``, are allowed but remain required in the result
    once requested.
    """

    if not metric_name.startswith("primary_quote_reversion_"):
        raise OutputSchemaContractError(
            "toxicity_reversion.q schema contracts only apply to "
            "primary_quote_reversion_* metrics"
        )

    return QTemplateOutputSchemaContract(
        template_name="toxicity_reversion.q",
        metric_value_column=metric_name,
        base_columns=REVERSION_OUTPUT_BASE_COLUMNS,
        metadata_columns=REVERSION_OUTPUT_METADATA_COLUMNS,
        group_columns=tuple(group_by),
        optional_columns=REVERSION_OPTIONAL_OUTPUT_METADATA_COLUMNS,
    )


def validate_toxicity_reversion_output_schema(
    *,
    metric_name: str,
    result: Any,
    group_by: Sequence[str] = (),
) -> None:
    """Validate a reversion result object against the offline schema contract."""

    toxicity_reversion_output_schema_contract(
        metric_name,
        group_by=group_by,
    ).validate_result(result)


def output_schema_contract_for_template(
    *,
    template_name: str,
    metric_name: str,
    group_by: Sequence[str] = (),
) -> QTemplateOutputSchemaContract:
    """Return the normalized output contract for a rendered q template."""

    if template_name == "activity.q":
        return activity_output_schema_contract(metric_name, group_by=group_by)
    if template_name == "liquidity.q":
        return liquidity_output_schema_contract(metric_name, group_by=group_by)
    if template_name == "toxicity_reversion.q":
        return toxicity_reversion_output_schema_contract(
            metric_name,
            group_by=group_by,
        )
    raise OutputSchemaContractError(
        f"no output schema contract is registered for q template {template_name!r}"
    )


def validate_output_schema_for_template(
    *,
    template_name: str,
    metric_name: str,
    result: Any,
    group_by: Sequence[str] = (),
) -> None:
    """Validate a rendered q template result against its registered contract."""

    output_schema_contract_for_template(
        template_name=template_name,
        metric_name=metric_name,
        group_by=group_by,
    ).validate_result(result)


def extract_result_columns(result: Any) -> tuple[str, ...]:
    """Extract result columns from offline dict/list and PyKX-like objects.

    Supported offline forms mirror ``normalize_metric_result``:

    - dict of column names to values;
    - dict representing one scalar row;
    - non-empty list/tuple of row dictionaries.

    A real zero-row kdb table should retain column metadata after ``.py()``. An
    empty Python list has no schema information, so it cannot satisfy a contract.
    """

    converted = _maybe_to_python(result)

    if isinstance(converted, Mapping):
        return tuple(str(column) for column in converted)

    if isinstance(converted, Sequence) and not isinstance(
        converted,
        (str, bytes, bytearray),
    ):
        if not converted:
            raise OutputSchemaContractError(
                "cannot validate output schema from an empty row list"
            )
        first_row = converted[0]
        if not isinstance(first_row, Mapping):
            raise OutputSchemaContractError(
                "list-like results must contain row dictionaries for schema validation"
            )
        return tuple(str(column) for column in first_row)

    raise OutputSchemaContractError(
        "result must be a dict of columns, one row dict, a list of row dicts, "
        "or a PyKX-like object with .py()"
    )


def _maybe_to_python(result: Any) -> Any:
    converter = getattr(result, "py", None)
    if callable(converter):
        return converter()
    return result


def _column_name_set(columns: Sequence[str]) -> set[str]:
    if isinstance(columns, (str, bytes, bytearray)):
        raise OutputSchemaContractError("columns must be a sequence of column names")
    return {str(column) for column in columns}


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return tuple(deduped)
