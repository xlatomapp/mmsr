"""Query planning for kdb-backed metric execution.

The query planner is the stable boundary between MMSR's Python orchestration and
manual q-template edits. It renders q text, records the source-table contracts
the template expects, and exposes the exact output columns the kdb result must
return before the runner executes anything.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, time
from typing import Any

from mmsr.kdb.query_loader import load_q_template, render_template
from mmsr.kdb.schema_contracts import (
    QTemplateInputTableSchemaContract,
    QTemplateOutputSchemaContract,
    activity_input_schema_contract,
    liquidity_input_schema_contract,
    output_schema_contract_for_template,
    toxicity_reversion_input_schema_contracts,
)
from mmsr.metrics.base import MetricDefinition
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


class KdbMetricQueryPlanError(RuntimeError):
    """Raised when a metric query cannot be planned safely."""


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


@dataclass(frozen=True)
class RenderedMetricQuery:
    """Rendered q query plus the schemas expected at the kdb boundary."""

    metric_name: str
    template_name: str
    query: str
    requested_group_by: tuple[str, ...]
    result_group_by: tuple[str, ...]
    table_names: tuple[tuple[str, str], ...]
    input_contracts: tuple[QTemplateInputTableSchemaContract, ...]
    output_contract: QTemplateOutputSchemaContract

    @property
    def required_output_columns(self) -> tuple[str, ...]:
        """Columns a kdb result must return before normalization can proceed."""

        return self.output_contract.required_columns

    @property
    def optional_output_columns(self) -> tuple[str, ...]:
        """Supported non-required columns consumed as row metadata when present."""

        return self.output_contract.optional_columns

    @property
    def documented_output_columns(self) -> tuple[str, ...]:
        """Required plus supported optional columns for manual q edits."""

        return self.output_contract.documented_columns

    def validate_result_schema(self, result: Any) -> None:
        """Validate a kdb/PyKX/offline result before normalization."""

        self.output_contract.validate_result(result)


class KdbMetricQueryPlanner:
    """Render metric q and expose source/output schema contracts without IO."""

    def render(self, request: MetricRunRequest) -> RenderedMetricQuery:
        """Render ``request`` into a deterministic query plan."""

        template_name = template_for_metric(request.metric.name)
        template = load_q_template(template_name)
        query_group_by = _query_group_by_for_template(template_name, request.group_by)
        result_group_by = group_by_for_metric_result(
            request.metric.name,
            request.group_by,
        )

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
        if template_name in {"activity.q", "liquidity.q"}:
            params["symbol_filter"] = _optional_symbol_filter(
                request.parameters.get("symbol")
            )
        if template_name == _REVERSION_TEMPLATE:
            params.update(_reversion_template_parameters(request))

        query = render_template(template, params)
        return RenderedMetricQuery(
            metric_name=request.metric.name,
            template_name=template_name,
            query=query,
            requested_group_by=tuple(request.group_by),
            result_group_by=tuple(result_group_by),
            table_names=tuple(sorted(request.table_names.items())),
            input_contracts=tuple(
                _input_contracts_for_template(
                    template_name=template_name,
                    table_names=request.table_names,
                    query_group_by=query_group_by,
                    parameters=request.parameters,
                )
            ),
            output_contract=output_schema_contract_for_template(
                template_name=template_name,
                metric_name=request.metric.name,
                group_by=result_group_by,
            ),
        )


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


def _input_contracts_for_template(
    *,
    template_name: str,
    table_names: Mapping[str, str],
    query_group_by: Sequence[str],
    parameters: Mapping[str, Any],
) -> Sequence[QTemplateInputTableSchemaContract]:
    if template_name == "activity.q":
        extra = _source_extra_columns(query_group_by, parameters)
        return (
            activity_input_schema_contract(
                trades_table=table_names["trades"],
                extra_required_columns=extra,
            ),
        )
    if template_name == "liquidity.q":
        extra = _source_extra_columns(query_group_by, parameters)
        return (
            liquidity_input_schema_contract(
                quotes_table=table_names["quotes"],
                extra_required_columns=extra,
            ),
        )
    if template_name == _REVERSION_TEMPLATE:
        return toxicity_reversion_input_schema_contracts(
            venue_trades_table=table_names["venue_trades"],
            primary_quotes_table=table_names["primary_quotes"],
            extra_required_columns=query_group_by,
        )
    return ()


def _source_extra_columns(
    query_group_by: Sequence[str],
    parameters: Mapping[str, Any],
) -> tuple[str, ...]:
    extra = list(query_group_by)
    if parameters.get("symbol") not in {None, ""}:
        extra.append("sym")
    return tuple(_dedupe(extra))


def _table_parameters(
    template_name: str,
    table_names: Mapping[str, str],
    metric_name: str,
) -> dict[str, str]:
    params: dict[str, str] = {}
    for table_key, table_parameter in _METRIC_TABLE_PARAMETER_MAP[template_name]:
        if table_key not in table_names:
            raise KdbMetricQueryPlanError(
                f"missing table_names entry {table_key!r} for metric {metric_name!r}"
            )
        params[table_parameter] = _q_identifier(table_names[table_key], "table name")
    return params


def _optional_symbol_filter(symbol: Any) -> str:
    """Return an optional q where-clause suffix for a single symbol smoke slice."""

    if symbol is None or symbol == "":
        return ""
    if not isinstance(symbol, str):
        raise KdbMetricQueryPlanError(
            "parameter 'symbol' must be a string when provided"
        )
    return f", sym = {_q_symbol_from_string(symbol)}"


def _reversion_template_parameters(request: MetricRunRequest) -> dict[str, str]:
    horizon = _reversion_horizon_from_metric(request.metric.name)
    primary_venue = _required_string_parameter(request, "primary_venue")
    venues = _required_string_sequence_parameter(request, "venues")
    max_primary_quote_age = request.parameters.get("max_primary_quote_age", "1s")
    if not isinstance(max_primary_quote_age, str):
        raise KdbMetricQueryPlanError(
            "parameter 'max_primary_quote_age' must be a string"
        )

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
        raise KdbMetricQueryPlanError(
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
        raise KdbMetricQueryPlanError(
            f"invalid primary quote reversion metric: {metric_name!r}"
        )
    return match.group("horizon")


def _required_string_parameter(request: MetricRunRequest, name: str) -> str:
    if name not in request.parameters:
        raise KdbMetricQueryPlanError(
            f"missing parameter {name!r} for metric {request.metric.name!r}"
        )
    value = request.parameters[name]
    if not isinstance(value, str) or not value:
        raise KdbMetricQueryPlanError(
            f"parameter {name!r} must be a non-empty string"
        )
    return value


def _required_string_sequence_parameter(
    request: MetricRunRequest,
    name: str,
) -> tuple[str, ...]:
    if name not in request.parameters:
        raise KdbMetricQueryPlanError(
            f"missing parameter {name!r} for metric {request.metric.name!r}"
        )

    value = request.parameters[name]
    if isinstance(value, (str, bytes, bytearray)) or not isinstance(value, Sequence):
        raise KdbMetricQueryPlanError(
            f"parameter {name!r} must be a sequence of strings"
        )

    strings = tuple(item for item in value if isinstance(item, str) and item)
    if len(strings) != len(value) or not strings:
        raise KdbMetricQueryPlanError(
            f"parameter {name!r} must contain only non-empty strings"
        )
    return strings


def _date_filter(start: date, end: date) -> str:
    return f"date within ({_q_date(start)};{_q_date(end)})"


def _time_filter(sessions: Sequence[TradingSession]) -> str:
    if not sessions:
        raise KdbMetricQueryPlanError(
            "period must contain at least one trading session"
        )

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
    raise KdbMetricQueryPlanError(f"unsupported bucket unit: {bucket.unit}")


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
        raise KdbMetricQueryPlanError(f"{label} must be non-empty")
    if not all(part.replace("_", "a").isalnum() for part in value.split(".")):
        raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}")
    if any(part[0].isdigit() for part in value.split(".") if part):
        raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}")
    return value


def _q_symbol(value: str, label: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}")
    return f"`{value}"


def _q_symbol_vector(values: Sequence[str], label: str) -> str:
    symbols = tuple(_q_symbol(value, label) for value in values)
    if not symbols:
        raise KdbMetricQueryPlanError(f"{label} must contain at least one value")
    if len(symbols) == 1:
        return f"enlist {symbols[0]}"
    return "".join(symbols)


def _q_symbol_from_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'$"{escaped}"'


_DURATION_RE = re.compile(r"^(?P<size>[1-9][0-9]*)(?P<unit>ms|s|m|h)$")


def _q_duration(value: str, label: str) -> str:
    match = _DURATION_RE.fullmatch(value)
    if match is None:
        raise KdbMetricQueryPlanError(
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
