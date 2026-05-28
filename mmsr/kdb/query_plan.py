"""Query planning for kdb-backed metric execution.

The query planner is the stable boundary between MMSR's Python orchestration and
q code executed inside kdb+. It renders q text, records the raw source contracts
that user-provided functions must return, and exposes the exact output columns
the kdb result must return before the runner executes anything.
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
    effective_spread_input_schema_contracts,
    flow_input_schema_contract,
    liquidity_input_schema_contract,
    liquidity_ticks_input_schema_contract,
    output_schema_contract_for_template,
    price_impact_input_schema_contracts,
    realized_volatility_input_schema_contract,
    reference_data_input_schema_contract,
    toxicity_reversion_input_schema_contracts,
)
from mmsr.metrics.base import MetricDefinition
from mmsr.periods.models import IntradayBucketSpec, ReportPeriod


_ACTIVITY_METRICS = frozenset({"turnover", "volume", "trade_count"})
_LIQUIDITY_METRICS = frozenset({"quoted_spread_bps", "top_of_book_depth"})
_LIQUIDITY_TICKS_METRICS = frozenset({"quoted_spread_ticks"})
_FLOW_METRICS = frozenset({"signed_turnover", "trade_imbalance"})
_EFFECTIVE_SPREAD_METRICS = frozenset({"effective_spread_bps"})
_PRICE_IMPACT_METRICS = frozenset({"price_impact_30s_bps"})
_REALIZED_VOLATILITY_METRICS = frozenset({"realized_volatility"})
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
    **{metric_name: "liquidity_ticks.q" for metric_name in _LIQUIDITY_TICKS_METRICS},
    **{
        metric_name: "realized_volatility.q"
        for metric_name in _REALIZED_VOLATILITY_METRICS
    },
    **{metric_name: "flow.q" for metric_name in _FLOW_METRICS},
    **{metric_name: "effective_spread.q" for metric_name in _EFFECTIVE_SPREAD_METRICS},
    **{metric_name: "price_impact.q" for metric_name in _PRICE_IMPACT_METRICS},
    **{metric_name: _REVERSION_TEMPLATE for metric_name in _REVERSION_METRICS},
}
_METRIC_TABLE_PARAMETER_MAP = {
    "activity.q": (("trades", "trades_table"), ("reference_data", "ref_table")),
    "liquidity.q": (("quotes", "quotes_table"), ("reference_data", "ref_table")),
    "liquidity_ticks.q": (("quotes", "quotes_table"), ("reference_data", "ref_table")),
    "realized_volatility.q": (("quotes", "quotes_table"), ("reference_data", "ref_table")),
    "flow.q": (("trades", "trades_table"), ("reference_data", "ref_table")),
    "effective_spread.q": (
        ("trades", "trades_table"),
        ("quotes", "quotes_table"),
        ("reference_data", "ref_table"),
    ),
    "price_impact.q": (
        ("trades", "trades_table"),
        ("quotes", "quotes_table"),
        ("reference_data", "ref_table"),
    ),
    _REVERSION_TEMPLATE: (
        ("pts_trades", "pts_trades_table"),
        ("pts_quotes", "pts_quotes_table"),
        ("primary_quotes", "primary_quotes_table"),
        ("reference_data", "ref_table"),
    ),
}


class KdbMetricQueryPlanError(RuntimeError):
    """Raised when a metric query cannot be planned safely."""


@dataclass(frozen=True)
class MetricRunRequest:
    """Request to run one metric over a period and grouping.

    Production requests should prefer ``source_functions`` over direct
    ``table_names``. The reference-data function is a user-defined q function that
    accepts ``date`` and returns the active universe/reference table. Raw trade
    and quote functions accept ``date`` plus that filtered reference table; MMSR-
    owned q then performs the metric aggregation inside ``calculation_namespace``.

    ``parameters`` carries metric-family-specific scalar settings that are not
    source names. The first user is the cross-venue reversion family, which needs
    ``primary_venue`` and optionally ``venues``/quote-age settings.
    """

    metric: MetricDefinition
    period: ReportPeriod
    group_by: list[str]
    table_names: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    source_functions: dict[str, str] = field(default_factory=dict)
    calculation_namespace: str = ".mmsr"


@dataclass(frozen=True)
class RenderedMetricQuery:
    """Rendered q query plus the schemas expected at the kdb boundary."""

    metric_name: str
    template_name: str
    query: str
    requested_group_by: tuple[str, ...]
    result_group_by: tuple[str, ...]
    table_names: tuple[tuple[str, str], ...]
    source_functions: tuple[tuple[str, str], ...]
    calculation_namespace: str
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

        calculation_namespace = _q_namespace(
            request.calculation_namespace,
            "calculation_namespace",
        )
        params = {
            **_source_parameters(
                template_name=template_name,
                table_names=request.table_names,
                source_functions=request.source_functions,
                request=request,
            ),
            "date_filter": _date_filter(
                request.period.start_date,
                request.period.end_date,
            ),
            "bucket_expr": _bucket_expr(request.period.bucket, calculation_namespace),
            "group_by": _group_by_suffix(query_group_by),
            "calculation_namespace": calculation_namespace,
            "ref_filter": _ref_symbol_filter(request.parameters),
        }
        if template_name in {
            "activity.q",
            "liquidity.q",
            "liquidity_ticks.q",
            "realized_volatility.q",
            "flow.q",
            "effective_spread.q",
            "price_impact.q",
        }:
            params["symbol_filter"] = _optional_symbol_filter(request.parameters)
        if template_name == "effective_spread.q":
            params.update(_effective_spread_template_parameters(request))
        if template_name == "price_impact.q":
            params.update(_price_impact_template_parameters(request))
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
            source_functions=tuple(sorted(request.source_functions.items())),
            calculation_namespace=_q_namespace(
                request.calculation_namespace,
                "calculation_namespace",
            ),
            input_contracts=tuple(
                _input_contracts_for_template(
                    template_name=template_name,
                    table_names=request.table_names,
                    source_functions=request.source_functions,
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
    source_functions: Mapping[str, str],
    query_group_by: Sequence[str],
    parameters: Mapping[str, Any],
) -> Sequence[QTemplateInputTableSchemaContract]:
    if template_name == "activity.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            activity_input_schema_contract(
                trades_table=_source_label("trades", table_names, source_functions),
                extra_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label(
                    "reference_data",
                    table_names,
                    source_functions,
                ),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "liquidity.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            liquidity_input_schema_contract(
                quotes_table=_source_label("quotes", table_names, source_functions),
                extra_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label(
                    "reference_data",
                    table_names,
                    source_functions,
                ),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "liquidity_ticks.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            liquidity_ticks_input_schema_contract(
                quotes_table=_source_label("quotes", table_names, source_functions),
                extra_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label("reference_data", table_names, source_functions),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "realized_volatility.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            realized_volatility_input_schema_contract(
                quotes_table=_source_label("quotes", table_names, source_functions),
                extra_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label("reference_data", table_names, source_functions),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "flow.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            flow_input_schema_contract(
                trades_table=_source_label("trades", table_names, source_functions),
                extra_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label("reference_data", table_names, source_functions),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "effective_spread.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            *effective_spread_input_schema_contracts(
                trades_table=_source_label("trades", table_names, source_functions),
                quotes_table=_source_label("quotes", table_names, source_functions),
                extra_trade_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label("reference_data", table_names, source_functions),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == "price_impact.q":
        raw_extra = _raw_source_extra_columns(parameters)
        ref_extra = _reference_extra_columns(query_group_by)
        return (
            *price_impact_input_schema_contracts(
                trades_table=_source_label("trades", table_names, source_functions),
                quotes_table=_source_label("quotes", table_names, source_functions),
                extra_trade_required_columns=raw_extra,
            ),
            reference_data_input_schema_contract(
                reference_table=_source_label("reference_data", table_names, source_functions),
                extra_required_columns=ref_extra,
                template_name=template_name,
            ),
        )
    if template_name == _REVERSION_TEMPLATE:
        return toxicity_reversion_input_schema_contracts(
            pts_trades_table=_source_label(
                "pts_trades",
                table_names,
                source_functions,
            ),
            pts_quotes_table=_source_label(
                "pts_quotes",
                table_names,
                source_functions,
            ),
            primary_quotes_table=_source_label(
                "primary_quotes",
                table_names,
                source_functions,
            ),
            reference_table=_source_label(
                "reference_data",
                table_names,
                source_functions,
            ),
            extra_required_columns=_reference_extra_columns(query_group_by),
        )
    return ()


def _source_extra_columns(
    query_group_by: Sequence[str],
    parameters: Mapping[str, Any],
) -> tuple[str, ...]:
    extra = list(query_group_by)
    if _symbol_filter_values(parameters):
        extra.append("sym")
    return tuple(_dedupe(extra))


def _raw_source_extra_columns(parameters: Mapping[str, Any]) -> tuple[str, ...]:
    """Return extra raw tick columns required by filters."""

    if _symbol_filter_values(parameters):
        return ("sym",)
    return ()


def _reference_extra_columns(query_group_by: Sequence[str]) -> tuple[str, ...]:
    """Return group columns expected from the reference-data source."""

    return tuple(_dedupe(list(query_group_by)))


def _source_parameters(
    *,
    template_name: str,
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
    request: MetricRunRequest,
) -> dict[str, str]:
    params: dict[str, str] = {}
    for source_key, template_parameter in _METRIC_TABLE_PARAMETER_MAP[template_name]:
        params[template_parameter] = _q_source_expression(
            source_key=source_key,
            table_names=table_names,
            source_functions=source_functions,
            request=request,
        )
    return params


def _q_source_expression(
    *,
    source_key: str,
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
    request: MetricRunRequest,
) -> str:
    resolved_source_key = _resolve_source_key(source_key, table_names, source_functions)
    if resolved_source_key in source_functions:
        function_name = _q_function_identifier(
            source_functions[resolved_source_key],
            f"source_functions[{resolved_source_key!r}]",
        )
        if source_key == "reference_data":
            return f"({function_name}[{_q_date(request.period.start_date)}])"
        return f"({function_name}[{_q_date(request.period.start_date)};0!refs])"

    if resolved_source_key in table_names:
        return _q_identifier(table_names[resolved_source_key], "table name")

    if source_key == "reference_data":
        return (
            "([]date:0#0Nd;"
            "sym:`symbol$();"
            "ric:`symbol$();"
            "topixCapGrp:`symbol$();"
            "lotSize:0#0N)"
        )

    raise KdbMetricQueryPlanError(
        f"missing source_functions or table_names entry {source_key!r} "
        f"for metric {request.metric.name!r}"
    )


def _source_label(
    source_key: str,
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
) -> str:
    resolved_source_key = _resolve_source_key(source_key, table_names, source_functions)
    if resolved_source_key in source_functions:
        return source_functions[resolved_source_key]
    if resolved_source_key in table_names:
        return table_names[resolved_source_key]
    return source_key


def _resolve_source_key(
    source_key: str,
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
) -> str:
    if source_key in source_functions or source_key in table_names:
        return source_key
    legacy_aliases = {
        "pts_trades": "venue_trades",
        "pts_quotes": "venue_quotes",
    }
    alias = legacy_aliases.get(source_key)
    if alias is not None and (alias in source_functions or alias in table_names):
        return alias
    return source_key


def _optional_symbol_filter(parameters: Mapping[str, Any]) -> str:
    """Return an optional q where-clause suffix for requested symbols.

    ``symbol`` is retained for legacy/smoke callers. Production execution uses
    ``symbols`` so one date can be split into deterministic symbol chunks without
    making raw source functions scan a multi-day period.
    """

    symbols = _symbol_filter_values(parameters)
    if not symbols:
        return ""
    if len(symbols) == 1:
        return f", sym = {_q_symbol_from_string(symbols[0])}"
    return f", sym in {_q_symbol_vector_from_strings(symbols)}"


def _effective_spread_template_parameters(request: MetricRunRequest) -> dict[str, str]:
    """Return effective-spread q parameters with a conservative freshness default."""

    max_quote_age = request.parameters.get("max_quote_age", "1s")
    if not isinstance(max_quote_age, str):
        raise KdbMetricQueryPlanError("parameter 'max_quote_age' must be a string")
    return {
        "max_quote_age": _q_duration(max_quote_age, "max_quote_age"),
    }


def _price_impact_template_parameters(request: MetricRunRequest) -> dict[str, str]:
    """Return price-impact q parameters for the fixed 30s metric horizon."""

    max_quote_age = request.parameters.get("max_quote_age", "1s")
    max_horizon_quote_age = request.parameters.get("max_horizon_quote_age", "1s")
    if not isinstance(max_quote_age, str):
        raise KdbMetricQueryPlanError("parameter 'max_quote_age' must be a string")
    if not isinstance(max_horizon_quote_age, str):
        raise KdbMetricQueryPlanError(
            "parameter 'max_horizon_quote_age' must be a string"
        )
    return {
        "horizon": _q_duration("30s", "price_impact horizon"),
        "max_quote_age": _q_duration(max_quote_age, "max_quote_age"),
        "max_horizon_quote_age": _q_duration(
            max_horizon_quote_age,
            "max_horizon_quote_age",
        ),
    }


def _reversion_template_parameters(request: MetricRunRequest) -> dict[str, str]:
    horizon = _reversion_horizon_from_metric(request.metric.name)
    primary_venue = _required_string_parameter(request, "primary_venue")
    venues = _optional_string_sequence_parameter(request, "venues")
    max_primary_quote_age = request.parameters.get("max_primary_quote_age", "1s")
    max_pts_quote_age = request.parameters.get(
        "max_pts_quote_age",
        request.parameters.get("max_venue_quote_age", max_primary_quote_age),
    )
    if not isinstance(max_primary_quote_age, str):
        raise KdbMetricQueryPlanError(
            "parameter 'max_primary_quote_age' must be a string"
        )
    if not isinstance(max_pts_quote_age, str):
        raise KdbMetricQueryPlanError(
            "parameter 'max_pts_quote_age' must be a string"
        )

    exclude_auction = bool(request.parameters.get("exclude_auction", False))

    primary_venue_symbol = _q_symbol(primary_venue, "primary_venue")
    return {
        "value_column": _q_identifier(request.metric.name, "metric value column"),
        "primary_venue": primary_venue_symbol,
        "venue_filter": (
            f"venue in {_q_symbol_vector(venues, 'venues')}"
            if venues
            else f"(not null venue) & venue <> {primary_venue_symbol}"
        ),
        "auction_filter": "null auction" if exclude_auction else "1b",
        "horizon": _q_duration(horizon, "horizon"),
        "horizon_label": _q_symbol_from_string(horizon),
        "horizon_sort_order": str(_reversion_horizon_sort_order(horizon)),
        "max_primary_quote_age": _q_duration(
            max_primary_quote_age,
            "max_primary_quote_age",
        ),
        "max_pts_quote_age": _q_duration(
            max_pts_quote_age,
            "max_pts_quote_age",
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
    return _string_sequence_parameter(value, name)


def _optional_string_sequence_parameter(
    request: MetricRunRequest,
    name: str,
) -> tuple[str, ...] | None:
    value = request.parameters.get(name)
    if value in (None, ""):
        return None
    return _string_sequence_parameter(value, name)


def _string_sequence_parameter(value: Any, name: str) -> tuple[str, ...]:
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


def _ref_symbol_filter(parameters: Mapping[str, Any]) -> str:
    """Return a q where predicate for filtering the reference universe."""

    symbols = _symbol_filter_values(parameters)
    if not symbols:
        return "1b"
    if len(symbols) == 1:
        return f"sym = {_q_symbol_from_string(symbols[0])}"
    return f"sym in {_q_symbol_vector_from_strings(symbols)}"


def _q_symbol_filter_vector(parameters: Mapping[str, Any]) -> str:
    symbols = _symbol_filter_values(parameters)
    if not symbols:
        return "0#`"
    if len(symbols) == 1:
        return f"enlist {_q_symbol_from_string(symbols[0])}"
    return _q_symbol_vector_from_strings(symbols)


def _symbol_filter_values(parameters: Mapping[str, Any]) -> tuple[str, ...]:
    """Return symbol filters from either production ``symbols`` or legacy ``symbol``."""

    symbols_value = parameters.get("symbols")
    symbol_value = parameters.get("symbol")

    if symbols_value not in (None, ""):
        if isinstance(symbols_value, str) or not isinstance(symbols_value, Sequence):
            raise KdbMetricQueryPlanError(
                "parameter 'symbols' must be a sequence of strings when provided"
            )
        symbols = tuple(
            value for value in symbols_value if isinstance(value, str) and value
        )
        if len(symbols) != len(symbols_value):
            raise KdbMetricQueryPlanError(
                "parameter 'symbols' must contain only non-empty strings"
            )
        if symbol_value not in (None, "") and tuple(symbols) != (symbol_value,):
            raise KdbMetricQueryPlanError(
                "parameters 'symbol' and 'symbols' conflict"
            )
        return symbols

    if symbol_value in (None, ""):
        return ()
    if not isinstance(symbol_value, str):
        raise KdbMetricQueryPlanError(
            "parameter 'symbol' must be a string when provided"
        )
    return (symbol_value,)


def _q_symbol_vector_from_strings(values: Sequence[str]) -> str:
    if not values:
        return "0#`"
    rendered = ";".join(_q_symbol_from_string(value) for value in values)
    if len(values) == 1:
        return f"enlist {rendered}"
    return f"({rendered})"


def _q_positive_int_parameter(value: Any, label: str) -> str:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise KdbMetricQueryPlanError(f"parameter {label!r} must be a positive integer")
    return str(value)


def _q_symbol_vector_or_empty(value: Any) -> str:
    if value is None or value == "":
        return "0#`"
    if isinstance(value, str):
        return f"enlist {_q_symbol(value, 'venues')}"
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise KdbMetricQueryPlanError(
            "parameter 'venues' must be a sequence of strings when provided"
        )
    return _q_symbol_vector(value, "venues")


def _q_time_vector(values: Sequence[time]) -> str:
    if not values:
        return "()"
    rendered = ";".join(_q_time(value) for value in values)
    if len(values) == 1:
        return f"enlist {rendered}"
    return f"({rendered})"


def _date_filter(start: date, end: date) -> str:
    return f"date within ({_q_date(start)};{_q_date(end)})"


def _bucket_expr(bucket: IntradayBucketSpec, calculation_namespace: str) -> str:
    if bucket.unit == "m":
        duration = f"0D00:{bucket.size:02d}:00.000"
    elif bucket.unit == "h":
        duration = f"0D{bucket.size:02d}:00:00.000"
    elif bucket.unit == "d":
        duration = "1D00:00:00.000"
    else:
        raise KdbMetricQueryPlanError(f"unsupported bucket unit: {bucket.unit}")
    return f"{calculation_namespace}.timeBucket[time; session; auction; {duration}]"


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


def _q_namespace(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise KdbMetricQueryPlanError(f"{label} must be a non-empty string")
    if not value.startswith("."):
        raise KdbMetricQueryPlanError(f"{label} must start with '.'")
    _validate_q_dotted_identifier(value[1:], label)
    return value


def _q_function_identifier(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise KdbMetricQueryPlanError(f"{label} must be a non-empty string")
    if value.startswith("."):
        _validate_q_dotted_identifier(value[1:], label)
        return value
    _validate_q_dotted_identifier(value, label)
    return value


def _validate_q_dotted_identifier(value: str, label: str) -> None:
    parts = value.split(".")
    if not parts or any(part == "" for part in parts):
        raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}")
    for part in parts:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", part):
            raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}")


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
