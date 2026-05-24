"""Metric runner interface for kdb-backed calculations."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, time
from numbers import Real
from typing import Any

from mmsr.kdb.client import KdbClient
from mmsr.kdb.query_loader import load_q_template, render_template
from mmsr.kdb.schema_contracts import validate_toxicity_reversion_output_schema
from mmsr.metrics.base import MetricDefinition
from mmsr.metrics.results import MetricObservation, MetricTimeSeries
from mmsr.periods.models import IntradayBucketSpec, ReportPeriod, TradingSession


_ACTIVITY_METRICS = frozenset({"turnover", "volume", "trade_count"})
_LIQUIDITY_METRICS = frozenset({"quoted_spread_bps", "top_of_book_depth"})
_REVERSION_METRIC_PATTERN = re.compile(
    r"^primary_quote_reversion_(?P<horizon>10ms|100ms|500ms|1s|5s|10s)_bps$"
)
_REVERSION_GROUP_COLUMNS = ("venue", "horizon")
_REVERSION_HORIZON_SORT_ORDER = {
    "10ms": 1,
    "100ms": 2,
    "500ms": 3,
    "1s": 4,
    "5s": 5,
    "10s": 6,
}
_REVERSION_TEMPLATE = "toxicity_reversion.q"
_REVERSION_METRICS = frozenset(
    f"primary_quote_reversion_{horizon}_bps"
    for horizon in ("10ms", "100ms", "500ms", "1s", "5s", "10s")
)

_METRIC_TEMPLATE_MAP = {
    **{metric_name: "activity.q" for metric_name in _ACTIVITY_METRICS},
    **{metric_name: "liquidity.q" for metric_name in _LIQUIDITY_METRICS},
    **{metric_name: _REVERSION_TEMPLATE for metric_name in _REVERSION_METRICS},
}
_METRIC_TABLE_PARAMETER_MAP = {
    "activity.q": (("trades", "trades_table"),),
    "liquidity.q": (("quotes", "quotes_table"),),
    _REVERSION_TEMPLATE: (
        ("venue_trades", "venue_trades_table"),
        ("primary_quotes", "primary_quotes_table"),
    ),
}


class KdbMetricRunnerError(RuntimeError):
    """Raised when a metric request cannot be rendered or normalized safely."""


@dataclass(frozen=True)
class MetricRunRequest:
    """Request to run one metric over a period and grouping.

    ``parameters`` carries metric-family-specific scalar settings that are not
    table names. The first user is the cross-venue reversion family, which needs
    ``primary_venue``, ``venues``, and optionally ``max_primary_quote_age``.
    """

    metric: MetricDefinition
    period: ReportPeriod
    group_by: list[str]
    table_names: dict[str, str]
    parameters: dict[str, Any] = field(default_factory=dict)


class KdbMetricRunner:
    """Runs registered metric queries through kdb+ and normalizes their output."""

    def __init__(self, client: KdbClient) -> None:
        self.client = client

    def run(self, request: MetricRunRequest) -> MetricTimeSeries:
        """Run a supported metric request and return normalized observations.

        Query templates are rendered with strict parameter validation before
        execution, and the returned table-like object is normalized into the
        package's ``MetricTimeSeries`` boundary model.
        """

        query, template_name = self.render_query(request)
        raw_result = self.client.execute(query)
        normalization_group_by = group_by_for_metric_result(
            request.metric.name,
            request.group_by,
        )
        if template_name == _REVERSION_TEMPLATE:
            validate_toxicity_reversion_output_schema(
                metric_name=request.metric.name,
                result=raw_result,
                group_by=normalization_group_by,
            )
        return normalize_metric_result(
            metric_name=request.metric.name,
            result=raw_result,
            group_by=normalization_group_by,
            metadata={
                "template": template_name,
                "query": query,
                "requested_group_by": tuple(request.group_by),
                "group_by": tuple(normalization_group_by),
            },
        )

    def render_query(self, request: MetricRunRequest) -> tuple[str, str]:
        """Render the q query for ``request`` and return ``(query, template_name)``."""

        template_name = template_for_metric(request.metric.name)
        template = load_q_template(template_name)
        query_group_by = _query_group_by_for_template(template_name, request.group_by)

        params = {
            **_table_parameters(
                template_name,
                request.table_names,
                request.metric.name,
            ),
            "date_filter": _date_filter(
                request.period.start_date,
                request.period.end_date,
            ),
            "time_filter": _time_filter(request.period.sessions),
            "bucket_expr": _bucket_expr(request.period.bucket),
            "group_by": _group_by_suffix(query_group_by),
        }
        if template_name == _REVERSION_TEMPLATE:
            params.update(_reversion_template_parameters(request))

        return render_template(template, params), template_name


def template_for_metric(metric_name: str) -> str:
    """Return the q template filename for a supported metric name."""

    try:
        return _METRIC_TEMPLATE_MAP[metric_name]
    except KeyError as exc:
        supported = ", ".join(sorted(_METRIC_TEMPLATE_MAP))
        raise NotImplementedError(
            f"metric {metric_name!r} is not yet supported by KdbMetricRunner; "
            f"supported metrics: {supported}"
        ) from exc


def group_by_for_metric_result(metric_name: str, group_by: Sequence[str]) -> list[str]:
    """Return the group columns expected in normalized result rows.

    Reversion results always carry ``venue`` and ``horizon`` so the report can
    render a venue reversion curve even when callers only request symbol or
    sector grouping.
    """

    if template_for_metric(metric_name) != _REVERSION_TEMPLATE:
        return list(group_by)
    return _dedupe([*_REVERSION_GROUP_COLUMNS, *group_by])


def normalize_metric_result(
    *,
    metric_name: str,
    result: Any,
    group_by: Sequence[str],
    metadata: Mapping[str, Any] | None = None,
) -> MetricTimeSeries:
    """Normalize dict/list-like kdb results into ``MetricTimeSeries``.

    Supported offline forms are:

    - a dict of column names to list-like column values;
    - a dict of scalar column values representing one row;
    - a list/tuple of row dictionaries.

    PyKX objects that provide a ``.py()`` method are converted first, keeping
    PyKX optional and lazy for unit tests.
    """

    converted = _maybe_to_python(result)
    rows = _coerce_rows(converted)
    observations: list[MetricObservation] = []

    for row_index, row in enumerate(rows):
        if metric_name not in row:
            raise KdbMetricRunnerError(
                f"metric result row {row_index} is missing value column {metric_name!r}"
            )
        if "date" not in row:
            raise KdbMetricRunnerError(
                f"metric result row {row_index} is missing 'date'"
            )

        group = _extract_group(row, group_by, row_index)
        used_columns = {"date", "time_bucket", metric_name, *group_by}
        row_metadata = {
            key: value
            for key, value in row.items()
            if key not in used_columns
        }

        observations.append(
            MetricObservation(
                metric_name=metric_name,
                date=_coerce_date(row["date"], row_index),
                time_bucket=_coerce_time_bucket(row.get("time_bucket")),
                group=group,
                value=_coerce_numeric_value(row[metric_name], row_index, metric_name),
                metadata=row_metadata,
            )
        )

    return MetricTimeSeries.from_observations(
        observations,
        metric_name=metric_name,
        metadata={} if metadata is None else dict(metadata),
    )


def _table_parameters(
    template_name: str,
    table_names: Mapping[str, str],
    metric_name: str,
) -> dict[str, str]:
    params: dict[str, str] = {}
    for table_key, table_parameter in _METRIC_TABLE_PARAMETER_MAP[template_name]:
        if table_key not in table_names:
            raise KdbMetricRunnerError(
                f"missing table_names entry {table_key!r} for metric {metric_name!r}"
            )
        params[table_parameter] = _q_identifier(table_names[table_key], "table name")
    return params


def _reversion_template_parameters(request: MetricRunRequest) -> dict[str, str]:
    horizon = _reversion_horizon_from_metric(request.metric.name)
    primary_venue = _required_string_parameter(request, "primary_venue")
    venues = _required_string_sequence_parameter(request, "venues")
    max_primary_quote_age = request.parameters.get("max_primary_quote_age", "1s")
    if not isinstance(max_primary_quote_age, str):
        raise KdbMetricRunnerError("parameter 'max_primary_quote_age' must be a string")

    return {
        "value_column": _q_identifier(request.metric.name, "metric value column"),
        "primary_venue": _q_symbol(primary_venue, "primary_venue"),
        "venue_filter": f"venue in {_q_symbol_vector(venues, 'venues')}",
        "horizon": _q_duration(horizon, "horizon"),
        "horizon_label": _q_symbol_from_string(horizon),
        "horizon_sort_order": str(_reversion_horizon_sort_order(horizon)),
        "max_primary_quote_age": _q_duration(
            max_primary_quote_age,
            "max_primary_quote_age",
        ),
    }


def _reversion_horizon_sort_order(horizon: str) -> int:
    """Return deterministic report order for the configured reversion horizon."""

    try:
        return _REVERSION_HORIZON_SORT_ORDER[horizon]
    except KeyError as exc:
        raise KdbMetricRunnerError(
            f"unsupported primary quote reversion horizon: {horizon!r}"
        ) from exc


def _query_group_by_for_template(
    template_name: str,
    group_by: Sequence[str],
) -> list[str]:
    if template_name != _REVERSION_TEMPLATE:
        return list(group_by)
    reserved = set(_REVERSION_GROUP_COLUMNS)
    return [column for column in group_by if column not in reserved]


def _reversion_horizon_from_metric(metric_name: str) -> str:
    match = _REVERSION_METRIC_PATTERN.fullmatch(metric_name)
    if match is None:
        raise KdbMetricRunnerError(
            f"invalid primary quote reversion metric: {metric_name!r}"
        )
    return match.group("horizon")


def _required_string_parameter(request: MetricRunRequest, name: str) -> str:
    if name not in request.parameters:
        raise KdbMetricRunnerError(
            f"missing parameter {name!r} for metric {request.metric.name!r}"
        )
    value = request.parameters[name]
    if not isinstance(value, str) or not value:
        raise KdbMetricRunnerError(f"parameter {name!r} must be a non-empty string")
    return value


def _required_string_sequence_parameter(
    request: MetricRunRequest,
    name: str,
) -> tuple[str, ...]:
    if name not in request.parameters:
        raise KdbMetricRunnerError(
            f"missing parameter {name!r} for metric {request.metric.name!r}"
        )

    value = request.parameters[name]
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise KdbMetricRunnerError(f"parameter {name!r} must be a sequence of strings")

    strings = tuple(item for item in value if isinstance(item, str) and item)
    if len(strings) != len(value) or not strings:
        raise KdbMetricRunnerError(
            f"parameter {name!r} must contain only non-empty strings"
        )
    return strings


def _maybe_to_python(result: Any) -> Any:
    converter = getattr(result, "py", None)
    if callable(converter):
        return converter()
    return result


def _coerce_rows(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, Mapping):
        return _rows_from_column_mapping(result)

    if isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(result):
            if not isinstance(row, Mapping):
                raise KdbMetricRunnerError(
                    "list-like metric results must contain row dictionaries; "
                    f"row {index} has type {type(row).__name__}"
                )
            rows.append(dict(row))
        return rows

    raise KdbMetricRunnerError(
        "metric result must be a dict of columns or a list of row dictionaries"
    )


def _rows_from_column_mapping(columns: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not columns:
        return []

    column_values = {
        str(column_name): _as_column_values(raw_values)
        for column_name, raw_values in columns.items()
    }
    row_count = max(len(values) for values in column_values.values())

    for column_name, values in column_values.items():
        if len(values) not in {1, row_count}:
            raise KdbMetricRunnerError(
                "column lengths in metric result do not match; "
                f"column {column_name!r} has {len(values)} value(s), "
                f"expected {row_count}"
            )

    rows: list[dict[str, Any]] = []
    for row_index in range(row_count):
        rows.append(
            {
                column_name: values[0] if len(values) == 1 else values[row_index]
                for column_name, values in column_values.items()
            }
        )
    return rows


def _as_column_values(value: Any) -> list[Any]:
    converted = _maybe_to_python(value)
    if isinstance(converted, Sequence) and not isinstance(
        converted,
        (str, bytes, bytearray),
    ):
        return list(converted)
    return [converted]


def _extract_group(
    row: Mapping[str, Any],
    group_by: Sequence[str],
    row_index: int,
) -> dict[str, str]:
    group: dict[str, str] = {}
    for column in group_by:
        if column not in row:
            raise KdbMetricRunnerError(
                f"metric result row {row_index} is missing group column {column!r}"
            )
        value = row[column]
        if value is not None:
            group[column] = str(value)
    return group


def _coerce_date(value: Any, row_index: int) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            if "." in value and "-" not in value:
                year, month, day = value.split(".")
                return date(int(year), int(month), int(day))
            return date.fromisoformat(value)
        except ValueError as exc:
            raise KdbMetricRunnerError(
                f"metric result row {row_index} has invalid date value {value!r}"
            ) from exc
    raise KdbMetricRunnerError(
        f"metric result row {row_index} has unsupported date value {value!r}"
    )


def _coerce_time_bucket(value: Any) -> time | str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, time):
        return value
    return str(value)


def _coerce_numeric_value(
    value: Any,
    row_index: int,
    metric_name: str,
) -> float | int | None:
    converted = _maybe_to_python(value)
    item = getattr(converted, "item", None)
    if callable(item):
        converted = item()

    if converted is None:
        return None
    if isinstance(converted, bool):
        return int(converted)
    if isinstance(converted, Real):
        return converted
    raise KdbMetricRunnerError(
        f"metric result row {row_index} has non-numeric value for "
        f"{metric_name!r}: {converted!r}"
    )


def _date_filter(start: date, end: date) -> str:
    return f"date within ({_q_date(start)};{_q_date(end)})"


def _time_filter(sessions: Sequence[TradingSession]) -> str:
    if not sessions:
        raise KdbMetricRunnerError("period must contain at least one trading session")

    clauses = [
        f"time within ({_q_time(session.start)};{_q_time(session.end)})"
        for session in sessions
    ]
    if len(clauses) == 1:
        return clauses[0]
    return "(" + " | ".join(f"({clause})" for clause in clauses) + ")"


def _bucket_expr(bucket: IntradayBucketSpec) -> str:
    if bucket.unit == "m":
        return f"0D00:{bucket.size:02d}:00.000 xbar time"
    if bucket.unit == "h":
        return f"0D{bucket.size:02d}:00:00.000 xbar time"
    if bucket.unit == "d":
        return "date"
    raise KdbMetricRunnerError(f"unsupported bucket unit: {bucket.unit}")


def _group_by_suffix(group_by: Sequence[str]) -> str:
    if not group_by:
        return ""
    identifiers = [_q_identifier(column, "group_by column") for column in group_by]
    return ", " + ", ".join(identifiers)


def _q_date(value: date) -> str:
    return f"{value.year:04d}.{value.month:02d}.{value.day:02d}"


def _q_time(value: time) -> str:
    return (
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}."
        f"{value.microsecond // 1000:03d}"
    )


def _q_identifier(value: str, label: str) -> str:
    if not value:
        raise KdbMetricRunnerError(f"{label} must be non-empty")
    if not all(part.replace("_", "a").isalnum() for part in value.split(".")):
        raise KdbMetricRunnerError(f"invalid {label}: {value!r}")
    if any(part[0].isdigit() for part in value.split(".") if part):
        raise KdbMetricRunnerError(f"invalid {label}: {value!r}")
    return value


def _q_symbol(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise KdbMetricRunnerError(f"invalid {label}: {value!r}")
    return f"`{value}"


def _q_symbol_vector(values: Sequence[str], label: str) -> str:
    symbols = tuple(_q_symbol(value, label) for value in values)
    if not symbols:
        raise KdbMetricRunnerError(f"{label} must contain at least one value")
    if len(symbols) == 1:
        return f"enlist {symbols[0]}"
    return "".join(symbols)


def _q_symbol_from_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\"')
    return f'$"{escaped}"'


_DURATION_RE = re.compile(r"^(?P<size>[1-9][0-9]*)(?P<unit>ms|s|m|h)$")


def _q_duration(value: str, label: str) -> str:
    match = _DURATION_RE.fullmatch(value)
    if match is None:
        raise KdbMetricRunnerError(
            f"invalid {label}: {value!r}; expected durations such as '10ms' or '1s'"
        )

    size = int(match.group("size"))
    unit = match.group("unit")
    hours = minutes = seconds = milliseconds = 0
    if unit == "ms":
        milliseconds = size
    elif unit == "s":
        seconds = size
    elif unit == "m":
        minutes = size
    elif unit == "h":
        hours = size

    seconds += milliseconds // 1000
    milliseconds %= 1000
    minutes += seconds // 60
    seconds %= 60
    hours += minutes // 60
    minutes %= 60

    return f"0D{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
