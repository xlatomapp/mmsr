"""Schema contracts for kdb q-template boundaries.

These contracts make the expected input and output shapes of q templates
explicit and unit-testable without a live kdb+ connection. They intentionally
validate the raw source/result boundary, not raw tick-level business logic.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

TICK_STATE_REQUIRED_COLUMNS: tuple[str, ...] = ("session", "auction")
REFERENCE_DATA_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "sym",
    "ric",
    "topixCapGrp",
    "lotSize",
)
REFERENCE_DATA_ASSUMPTIONS: tuple[str, ...] = (
    "one row per analysis symbol and date is required before joining to ticks",
    "topixCapGrp is the day-specific TOPIX capitalization group label",
    "lotSize is the round-lot size applicable to the requested symbol/date",
)

ACTIVITY_TRADES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    *TICK_STATE_REQUIRED_COLUMNS,
    "tradePrice",
    "tradeSize",
)
ACTIVITY_TRADES_ASSUMPTIONS: tuple[str, ...] = (
    "tradePrice and tradeSize are positive for included trades",
    "optional symbol filtering requires a sym column",
    "session uses `am`pm symbols and auction uses integer codes: 1=open, 2=close, 0=continuous",
    "requested group_by columns may be supplied by the reference-data source",
)
ACTIVITY_OUTPUT_AGGREGATE_COLUMNS: tuple[str, ...] = (
    "turnover",
    "volume",
    "trade_count",
)

LIQUIDITY_QUOTES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    "bidPrice",
    "askPrice",
    "bidSize",
    "askSize",
)
LIQUIDITY_QUOTES_ASSUMPTIONS: tuple[str, ...] = (
    "bidPrice and askPrice are positive numeric prices with askPrice > bidPrice",
    "bidSize and askSize are numeric top-of-book displayed sizes",
    "optional symbol filtering requires a sym column",
    "quotes are continuous-session rows and do not require an auction column",
    "requested group_by columns may be supplied by the reference-data source",
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
REVERSION_PTS_TRADES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    *TICK_STATE_REQUIRED_COLUMNS,
    "venue",
    "tradePrice",
    "tradeSize",
)
REVERSION_PTS_QUOTES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    "venue",
    "bidPrice",
    "askPrice",
)
REVERSION_PRIMARY_QUOTES_REQUIRED_COLUMNS: tuple[str, ...] = (
    "date",
    "time",
    "sym",
    "venue",
    "bidPrice",
    "askPrice",
)
REVERSION_PTS_TRADES_ASSUMPTIONS: tuple[str, ...] = (
    "MMSR infers aggressorSide from the same-PTS-venue/same-symbol prevailing quote midpoint",
    "tradePrice and tradeSize are positive for included trades",
    "requested group_by columns must be present after the template join/aggregation",
)
REVERSION_PTS_QUOTES_ASSUMPTIONS: tuple[str, ...] = (
    "venue identifies the PTS quote source used for same-venue aggressor-side inference",
    "bidPrice and askPrice are positive numeric prices with askPrice > bidPrice",
)
REVERSION_PRIMARY_QUOTES_ASSUMPTIONS: tuple[str, ...] = (
    "venue identifies the primary quote source; rows for the configured primary venue are used for TSE/primary mids",
    "bidPrice and askPrice are positive numeric prices with askPrice > bidPrice",
)


class OutputSchemaContractError(ValueError):
    """Raised when a q-template boundary does not satisfy its schema contract."""


@dataclass(frozen=True)
class QTemplateInputTableSchemaContract:
    """Required raw source columns for a q template.

    ``table_role`` is the logical role used by the template, for example
    ``pts_trades``, ``pts_quotes``, or ``primary_quotes``. ``table_name`` is
    the configured production table or raw function name to display in
    validation errors.
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
        """Validate that a raw source exposes every required column."""

        available = _column_name_set(columns)
        missing = [
            column for column in self.required_columns if column not in available
        ]
        if missing:
            raise OutputSchemaContractError(
                f"{self.template_name} input source {self.table_name!r} "
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


def reference_data_input_schema_contract(
    *,
    reference_table: str = "reference_data",
    extra_required_columns: Sequence[str] = (),
    template_name: str = "reference_data",
) -> QTemplateInputTableSchemaContract:
    """Return the day/symbol reference-data source contract."""

    return QTemplateInputTableSchemaContract(
        template_name=template_name,
        table_role="reference_data",
        table_name=reference_table,
        required_columns=_dedupe(
            (*REFERENCE_DATA_REQUIRED_COLUMNS, *extra_required_columns)
        ),
        assumptions=REFERENCE_DATA_ASSUMPTIONS,
    )


def activity_input_schema_contract(
    *,
    trades_table: str = "trades",
    extra_required_columns: Sequence[str] = (),
) -> QTemplateInputTableSchemaContract:
    """Return the raw source contract for ``activity``.

    ``extra_required_columns`` should include requested grouping columns and
    ``sym`` when callers render a symbol-bounded smoke/report query.
    """

    return QTemplateInputTableSchemaContract(
        template_name="activity",
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
    """Return the raw source contract for ``liquidity``."""

    return QTemplateInputTableSchemaContract(
        template_name="liquidity",
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
    """Return the output-schema contract for ``activity``.

    ``activity`` emits every starter activity aggregate on each row, even when
    the runner is normalizing one requested metric. Keeping the sibling
    aggregate columns required makes the template boundary explicit and ensures
    those values remain available as row metadata for report diagnostics.
    """

    if metric_name not in ACTIVITY_OUTPUT_AGGREGATE_COLUMNS:
        raise OutputSchemaContractError(
            "activity schema contracts only apply to activity metrics: "
            + ", ".join(ACTIVITY_OUTPUT_AGGREGATE_COLUMNS)
        )

    return QTemplateOutputSchemaContract(
        template_name="activity",
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
    """Return the output-schema contract for ``liquidity``.

    ``liquidity`` emits every starter liquidity aggregate on each row. The
    non-requested aggregate column is required so the report boundary preserves
    it as deterministic row metadata.
    """

    if metric_name not in LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS:
        raise OutputSchemaContractError(
            "liquidity schema contracts only apply to liquidity metrics: "
            + ", ".join(LIQUIDITY_OUTPUT_AGGREGATE_COLUMNS)
        )

    return QTemplateOutputSchemaContract(
        template_name="liquidity",
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
    """Validate an ``activity`` result object against its schema contract."""

    activity_output_schema_contract(metric_name, group_by=group_by).validate_result(
        result
    )


def validate_liquidity_output_schema(
    *,
    metric_name: str,
    result: Any,
    group_by: Sequence[str] = (),
) -> None:
    """Validate a ``liquidity`` result object against its schema contract."""

    liquidity_output_schema_contract(metric_name, group_by=group_by).validate_result(
        result
    )


def toxicity_reversion_input_schema_contracts(
    *,
    pts_trades_table: str = "pts_trades",
    pts_quotes_table: str = "pts_quotes",
    primary_quotes_table: str = "primary_quotes",
    reference_table: str = "reference_data",
    extra_required_columns: Sequence[str] = (),
) -> tuple[
    QTemplateInputTableSchemaContract,
    QTemplateInputTableSchemaContract,
    QTemplateInputTableSchemaContract,
    QTemplateInputTableSchemaContract,
]:
    """Return required production raw-source schemas for ``toxicity_reversion``.

    These contracts intentionally encode only the columns and feed conventions
    the q template requires. They do not validate business quality, symbol
    coverage, or whether the input sources have enough observations for a report.
    """

    return (
        QTemplateInputTableSchemaContract(
            template_name="toxicity_reversion",
            table_role="pts_trades",
            table_name=pts_trades_table,
            required_columns=_dedupe(
                (*REVERSION_PTS_TRADES_REQUIRED_COLUMNS, *extra_required_columns)
            ),
            assumptions=REVERSION_PTS_TRADES_ASSUMPTIONS,
        ),
        QTemplateInputTableSchemaContract(
            template_name="toxicity_reversion",
            table_role="pts_quotes",
            table_name=pts_quotes_table,
            required_columns=REVERSION_PTS_QUOTES_REQUIRED_COLUMNS,
            assumptions=REVERSION_PTS_QUOTES_ASSUMPTIONS,
        ),
        QTemplateInputTableSchemaContract(
            template_name="toxicity_reversion",
            table_role="primary_quotes",
            table_name=primary_quotes_table,
            required_columns=REVERSION_PRIMARY_QUOTES_REQUIRED_COLUMNS,
            assumptions=REVERSION_PRIMARY_QUOTES_ASSUMPTIONS,
        ),
        reference_data_input_schema_contract(
            reference_table=reference_table,
            extra_required_columns=extra_required_columns,
            template_name="toxicity_reversion",
        ),
    )


def validate_toxicity_reversion_input_schemas(
    *,
    pts_trades_columns: Sequence[str],
    pts_quotes_columns: Sequence[str],
    primary_quotes_columns: Sequence[str],
    pts_trades_table: str = "pts_trades",
    pts_quotes_table: str = "pts_quotes",
    primary_quotes_table: str = "primary_quotes",
) -> None:
    """Validate raw-source columns for ``toxicity_reversion``."""

    (
        pts_contract,
        pts_quote_contract,
        primary_quote_contract,
        _reference_contract,
    ) = toxicity_reversion_input_schema_contracts(
        pts_trades_table=pts_trades_table,
        pts_quotes_table=pts_quotes_table,
        primary_quotes_table=primary_quotes_table,
    )
    pts_contract.validate_columns(pts_trades_columns)
    pts_quote_contract.validate_columns(pts_quotes_columns)
    primary_quote_contract.validate_columns(primary_quotes_columns)


def toxicity_reversion_output_schema_contract(
    metric_name: str,
    *,
    group_by: Sequence[str] = (),
) -> QTemplateOutputSchemaContract:
    """Return the output-schema contract for ``toxicity_reversion``.

    The reversion template must always emit ``venue`` and ``horizon`` in
    addition to the rendered metric value column. Caller-provided report groups,
    such as ``sym`` or ``sector``, are allowed but remain required in the result
    once requested.
    """

    if not metric_name.startswith("primary_quote_reversion_"):
        raise OutputSchemaContractError(
            "toxicity_reversion schema contracts only apply to "
            "primary_quote_reversion_* metrics"
        )

    return QTemplateOutputSchemaContract(
        template_name="toxicity_reversion",
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

    if template_name == "activity":
        return activity_output_schema_contract(metric_name, group_by=group_by)
    if template_name == "liquidity":
        return liquidity_output_schema_contract(metric_name, group_by=group_by)
    if template_name == "toxicity_reversion":
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
        keyed_columns = _columns_from_keyed_table_mapping(converted)
        if keyed_columns is not None:
            return keyed_columns
        return tuple(str(column) for column in converted)

    dataframe_columns = _columns_from_dataframe_like(converted)
    if dataframe_columns is not None:
        return dataframe_columns

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




def _columns_from_keyed_table_mapping(result: Mapping[Any, Any]) -> tuple[str, ...] | None:
    """Return columns for common keyed-table Python representations.

    Some PyKX keyed table conversions preserve key/value parts separately.
    Schema validation must treat the key columns as ordinary table columns,
    equivalent to q ``0!keyedTable``.
    """

    keys_part: Any | None = None
    values_part: Any | None = None
    for key_name in ("key", "keys"):
        if key_name in result:
            keys_part = result[key_name]
            break
    for value_name in ("value", "values"):
        if value_name in result:
            values_part = result[value_name]
            break

    if not isinstance(keys_part, Mapping) or not isinstance(values_part, Mapping):
        return None

    return _dedupe(
        (
            *tuple(str(column) for column in keys_part),
            *tuple(str(column) for column in values_part),
        )
    )


def _columns_from_dataframe_like(result: Any) -> tuple[str, ...] | None:
    """Return columns for pandas/polars-like table objects without importing them."""

    columns = getattr(result, "columns", None)
    if columns is None:
        return None

    names: list[str] = []
    index = getattr(result, "index", None)
    index_names = getattr(index, "names", None)
    if index_names is not None:
        names.extend(str(name) for name in index_names if name is not None)

    names.extend(str(column) for column in columns)
    return tuple(_dedupe(tuple(names)))


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
