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

from mmsr.kdb.query_loader import render_template, template_parameters
from mmsr.kdb.schema_contracts import (
    QTemplateInputTableSchemaContract,
    QTemplateOutputSchemaContract,
    activity_input_schema_contract,
    liquidity_input_schema_contract,
    output_schema_contract_for_template,
    reference_data_input_schema_contract,
    toxicity_reversion_input_schema_contracts,
)
from mmsr.metrics.base import MetricDefinition
from mmsr.periods.models import IntradayBucketSpec, ReportPeriod

_ACTIVITY_METRICS = frozenset({"turnover", "volume", "trade_count"})
_LIQUIDITY_METRICS = frozenset({"quoted_spread_bps", "top_of_book_depth"})
_REVERSION_METRIC_PATTERN = re.compile(r"^primary_quote_reversion_(?P<horizon>10ms|100ms|500ms|1s|5s|10s)_bps$")
_REVERSION_GROUP_COLUMNS = ("venue", "horizon")
_REVERSION_HORIZON_SORT_ORDER = {
    "10ms": 1,
    "100ms": 2,
    "500ms": 3,
    "1s": 4,
    "5s": 5,
    "10s": 6,
}
_REVERSION_TEMPLATE = "toxicity_reversion"
_REVERSION_METRICS = frozenset(
    f"primary_quote_reversion_{horizon}_bps" for horizon in ("10ms", "100ms", "500ms", "1s", "5s", "10s")
)

_METRIC_TEMPLATE_MAP = {
    **{metric_name: "activity" for metric_name in _ACTIVITY_METRICS},
    **{metric_name: "liquidity" for metric_name in _LIQUIDITY_METRICS},
    **{metric_name: _REVERSION_TEMPLATE for metric_name in _REVERSION_METRICS},
}
_METRIC_TABLE_PARAMETER_MAP = {
    "activity": (("trades", "trades_table"), ("reference_data", "ref_table")),
    "liquidity": (("quotes", "quotes_table"), ("reference_data", "ref_table")),
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


@dataclass(frozen=True)
class RenderedMetricBatchQuery:
    """Rendered q query that loads one day/chunk once and returns metric tables.

    The q expression returns a dictionary keyed by metric name. Each dictionary
    value is the aggregated result table for that metric, which Python validates
    and normalizes using the same per-metric output contracts as single-metric
    execution.
    """

    query: str
    metric_queries: tuple[RenderedMetricQuery, ...]

    @property
    def metric_names(self) -> tuple[str, ...]:
        """Metric names returned by the batch query in dictionary order."""

        return tuple(metric_query.metric_name for metric_query in self.metric_queries)


@dataclass(frozen=True)
class RenderedMetricDayQuery:
    """Rendered q query that calls the installed top-level MMSR day runner.

    Python renders only validated scalar/report configuration literals. kdb owns
    reference loading, universe filtering, symbol discovery, chunking, raw source
    loading, metric dispatch, and rollup.
    """

    query: str
    metric_queries: tuple[RenderedMetricQuery, ...]
    chunk_size: int

    @property
    def metric_names(self) -> tuple[str, ...]:
        """Metric names returned by the day query in dictionary order."""

        return tuple(metric_query.metric_name for metric_query in self.metric_queries)

    @property
    def required_output_columns(self) -> tuple[str, ...]:
        """Required columns for a single-metric day query."""

        if len(self.metric_queries) != 1:
            raise KdbMetricQueryPlanError("required_output_columns is only defined for single-metric day queries")
        return self.metric_queries[0].required_output_columns

    @property
    def template_name(self) -> str:
        """Legacy single-metric family identifier for older callers."""

        if len(self.metric_queries) != 1:
            raise KdbMetricQueryPlanError("template_name is only defined for single-metric day queries")
        return self.metric_queries[0].template_name


class KdbMetricQueryPlanner:
    """Render metric q and expose source/output schema contracts without IO."""

    def render(self, request: MetricRunRequest) -> RenderedMetricQuery:
        """Render ``request`` into a deterministic query plan."""

        template_name = template_for_metric(request.metric.name)
        query_group_by = _query_group_by_for_template(template_name, request.group_by)
        result_group_by = group_by_for_metric_result(
            request.metric.name,
            request.group_by,
        )

        params = _template_parameters_for_request(request)

        query = _single_metric_execution_block(
            template_name=template_name,
            metric_name=request.metric.name,
            params=params,
            request=request,
        )
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

    def render_day(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> RenderedMetricDayQuery:
        """Render one q call to the installed top-level MMSR report-day runner."""

        clean_requests = tuple(requests)
        if not clean_requests:
            raise KdbMetricQueryPlanError("day query requires at least one request")

        _validate_day_request_compatibility(clean_requests)

        representative_requests = _representative_metric_requests(clean_requests)
        metric_queries = tuple(self.render(request) for request in representative_requests)
        calculation_namespace = _q_namespace(
            clean_requests[0].calculation_namespace,
            "calculation_namespace",
        )
        aggregation_levels = _aggregation_level_values(clean_requests[0].parameters)
        chunk_size = _configured_chunk_size(clean_requests[0].parameters)
        source_roles = _batch_source_roles(representative_requests)
        source_functions = _source_function_dictionary(
            ("reference_data", *source_roles),
            clean_requests[0].table_names,
            clean_requests[0].source_functions,
        )
        metric_params = _metric_parameter_dictionary(representative_requests)
        universe_filters = _universe_filter_dictionary(clean_requests[0].parameters)

        report_config = _q_dictionary_expression(
            [
                "sourceFunctions",
                "metricNames",
                "metricParams",
                "universeFilters",
                "aggregationLevels",
                "chunkSize",
            ],
            [
                source_functions,
                _q_symbol_vector_from_strings([metric_query.metric_name for metric_query in metric_queries]),
                metric_params,
                universe_filters,
                _q_symbol_vector(aggregation_levels, "aggregation_levels"),
                str(chunk_size),
            ],
            "report_config",
        )

        query = f"""{calculation_namespace}.runReportDay[
    {_q_date(clean_requests[0].period.start_date)};
    {report_config}]"""

        return RenderedMetricDayQuery(
            query=query,
            metric_queries=metric_queries,
            chunk_size=chunk_size,
        )

    def render_batch(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> RenderedMetricBatchQuery:
        """Render one q query for one day/chunk and multiple metrics.

        The batch query sources reference/trade/quote tables once, passes those
        raw tables into each MMSR calculation function, and returns a q
        dictionary of aggregated result tables keyed by metric name.
        """

        clean_requests = tuple(requests)
        if not clean_requests:
            raise KdbMetricQueryPlanError("batch query requires at least one request")

        metric_queries = tuple(self.render(request) for request in clean_requests)
        _validate_batch_request_compatibility(clean_requests)

        batch_params = _batch_source_parameters(clean_requests)
        source_roles = _batch_source_roles(clean_requests)
        body_lines = [
            "{[]",
            f"    rawRefs: select from {batch_params['ref_table']};",
            f"    refs: `sym xkey select from rawRefs where {batch_params['ref_filter']};",
            "    chunkSyms: exec sym from 0!refs;",
        ]
        body_lines.extend(_batch_source_load_lines(source_roles, batch_params))
        result_symbols: list[str] = []
        result_variables: list[str] = []
        for index, (request, metric_query) in enumerate(
            zip(clean_requests, metric_queries, strict=True),
            start=1,
        ):
            result_variable = f"metricResult{index}"
            body_lines.append("")
            body_lines.append(
                f"    {result_variable}: {_metric_call_expression(metric_query.metric_name, metric_query.template_name, metric_query.calculation_namespace, _metric_params_expression(request))};"  # noqa: E501
            )
            result_symbols.append(_q_symbol_from_string(metric_query.metric_name))
            result_variables.append(result_variable)

        body_lines.append("    " + _q_symbol_list(result_symbols) + "!(" + ";".join(result_variables) + ")")
        body_lines.append("    }[]")
        return RenderedMetricBatchQuery(
            query="\n".join(body_lines),
            metric_queries=metric_queries,
        )


def template_for_metric(metric_name: str) -> str:
    """Return the q template filename for a supported metric name."""

    try:
        return _METRIC_TEMPLATE_MAP[metric_name]
    except KeyError as exc:
        supported = ", ".join(sorted(_METRIC_TEMPLATE_MAP))
        raise NotImplementedError(
            f"metric {metric_name!r} is not yet supported by KdbMetricRunner; supported metrics: {supported}"
        ) from exc


def metric_family_for_metric(metric_name: str) -> str:
    """Return the q metric family for logs and diagnostics."""

    template_name = template_for_metric(metric_name)
    return template_name


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
    if template_name == "activity":
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
    if template_name == "liquidity":
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


def _render_template_with_used_params(
    template: str,
    params: Mapping[str, str],
) -> str:
    """Render q template using only placeholders that the template defines."""

    required = template_parameters(template)
    return render_template(
        template,
        {name: params[name] for name in required},
    )


def _template_parameters_for_request(request: MetricRunRequest) -> dict[str, str]:
    """Return all render parameters for a single metric request."""

    template_name = template_for_metric(request.metric.name)
    query_group_by = _query_group_by_for_template(template_name, request.group_by)
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
        "bucket_expr": _bucket_expr_for_template(
            template_name,
            request.period.bucket,
            calculation_namespace,
        ),
        "group_by": _group_by_suffix(query_group_by),
        "calculation_namespace": calculation_namespace,
        "ref_filter": _ref_symbol_filter(request.parameters),
    }
    if template_name in {"activity", "liquidity"}:
        params["symbol_filter"] = _optional_symbol_filter(request.parameters)
    if template_name == _REVERSION_TEMPLATE:
        params.update(_reversion_template_parameters(request))
    return params


def _single_metric_execution_block(
    *,
    template_name: str,
    metric_name: str,
    params: Mapping[str, str],
    request: MetricRunRequest,
) -> str:
    """Return the top-level q expression for a single metric query."""

    source_roles = _source_roles_for_template(template_name)
    lines = [
        "{[]",
        f"    rawRefs: select from {params['ref_table']};",
        f"    refs: `sym xkey select from rawRefs where {params['ref_filter']};",
        "    chunkSyms: exec sym from 0!refs;",
    ]
    lines.extend(_batch_source_load_lines(source_roles, params))
    lines.append(
        "    result: "
        + _metric_call_expression(
            metric_name,
            template_name,
            params["calculation_namespace"],
            _metric_params_expression(request),
        )
        + ";"
    )
    lines.append("    result")
    lines.append("    }[]")
    return "\n".join(lines)


def _metric_call_expression(
    metric_name: str,
    template_name: str,
    calculation_namespace: str,
    metric_params: str,
) -> str:
    """Return the q call that passes already-loaded raw rows into calc function."""

    calls = {
        "activity": f"{calculation_namespace}.calcActivity[rawTrades;refs;{metric_params}]",
        "liquidity": f"{calculation_namespace}.calcLiquidity[rawQuotes;refs;{metric_params}]",
        _REVERSION_TEMPLATE: (
            f"{calculation_namespace}.calcToxicityReversion["
            f"rawPtsTradeRows;rawPtsQuoteRows;rawPrimaryQuoteRows;refs;{metric_params}]"
        ),
    }
    try:
        return calls[template_name]
    except KeyError as exc:
        raise KdbMetricQueryPlanError(f"unsupported q template for metric call: {template_name!r}") from exc


def _metric_function_expression(
    metric_name: str,
    template_name: str,
    calculation_namespace: str,
    request: MetricRunRequest,
) -> str:
    """Return an anonymous q function that runs one metric against loaded sources."""

    metric_params = _metric_params_expression(request)
    activity_call = (
        f"{{[rawSources] {calculation_namespace}.calcActivity[rawSources`trades;rawSources`refs;{metric_params}]}}"
    )
    liquidity_call = (
        f"{{[rawSources] {calculation_namespace}.calcLiquidity[rawSources`quotes;rawSources`refs;{metric_params}]}}"
    )
    calls = {
        "activity": activity_call,
        "liquidity": liquidity_call,
        _REVERSION_TEMPLATE: (
            f"{{[rawSources] {calculation_namespace}.calcToxicityReversion["
            f"rawSources`pts_trades;rawSources`pts_quotes;rawSources`primary_quotes;rawSources`refs;{metric_params}]}}"
        ),
    }
    try:
        return calls[template_name]
    except KeyError as exc:
        raise KdbMetricQueryPlanError(f"unsupported q template for metric function: {template_name!r}") from exc


def _metric_params_expression(request: MetricRunRequest) -> str:
    """Return a q dictionary of scalar metric parameters for installed q functions."""

    template_name = template_for_metric(request.metric.name)
    bucket = _bucket_duration(request.period.bucket)
    keys = ["bucket", "start_date", "end_date"]
    values = [
        bucket,
        _q_date(request.period.start_date),
        _q_date(request.period.end_date),
    ]

    if template_name == _REVERSION_TEMPLATE:
        extra = _reversion_template_parameters(request)
        keys.extend(
            [
                "value_column",
                "primary_venue",
                "venues",
                "exclude_auction",
                "horizon",
                "horizon_label",
                "horizon_sort_order",
                "max_primary_quote_age",
                "max_pts_quote_age",
            ]
        )
        values.extend(
            [
                extra["value_column"],
                extra["primary_venue"],
                _q_symbol_vector_or_empty(request.parameters.get("venues")),
                "1b" if request.parameters.get("exclude_auction", False) else "0b",
                extra["horizon"],
                extra["horizon_label"],
                extra["horizon_sort_order"],
                extra["max_primary_quote_age"],
                extra["max_pts_quote_age"],
            ]
        )

    return _q_dictionary_expression(keys, values, "metric parameter keys")


def _q_dictionary_expression(keys: Sequence[str], values: Sequence[str], label: str) -> str:
    """Return q dictionary syntax for rendered symbol keys and rendered values.

    Singleton dictionaries must use the unambiguous q shape
    ``enlist[`key]!enlist value``. In particular, do not render
    ``enlist `key!value`` because q associates that as ``enlist (`key!value)``
    and produces the wrong type/shape.
    """

    if len(keys) != len(values) or not keys:
        raise KdbMetricQueryPlanError(f"{label} and values must be non-empty and aligned")
    rendered_key_values = [_q_symbol(key, label) for key in keys]
    rendered_keys = _q_symbol_list(rendered_key_values)
    if len(values) == 1:
        return _q_singleton_dictionary_expression(rendered_keys, values[0])
    return f"{rendered_keys}!(" + ";".join(values) + ")"


def _q_singleton_dictionary_expression(rendered_single_key_list: str, value: str) -> str:
    """Return q syntax for a one-pair dictionary.

    ``rendered_single_key_list`` must already be an enlisted one-item symbol list,
    for example ``enlist[`refs]`` or ``enlist[`$"7203"]``. Composite values are
    parenthesized so q enlists the value itself rather than part of a right-side
    expression.
    """

    return f"{rendered_single_key_list}!enlist {_q_singleton_dictionary_value(value)}"


def _q_singleton_dictionary_value(value: str) -> str:
    stripped = value.strip()
    if "!" in stripped or stripped.startswith("enlist ") or stripped.startswith("enlist[") or ";" in stripped:
        return f"({stripped})"
    return stripped


def _q_source_loader_expression(
    *,
    source_key: str,
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
) -> str:
    """Return a q function taking ``runDate`` and filtered ``refs``."""

    resolved_source_key = _resolve_source_key(source_key, table_names, source_functions)
    if resolved_source_key in source_functions:
        function_name = _q_function_identifier(
            source_functions[resolved_source_key],
            f"source_functions[{resolved_source_key!r}]",
        )
        if source_key == "reference_data":
            return f"{{[runDate;refs] {function_name}[runDate]}}"
        return f"{{[runDate;refs] {function_name}[runDate;refs]}}"

    if resolved_source_key in table_names:
        table_name = _q_identifier(table_names[resolved_source_key], "table name")
        return f"{{[runDate;refs] select from {table_name}}}"

    if source_key == "reference_data":
        return "{[runDate;refs] ([]date:0#0Nd;sym:`symbol$();ric:`symbol$();topixCapGrp:`symbol$();lotSize:0#0N)}"

    raise KdbMetricQueryPlanError(f"missing source_functions or table_names entry {source_key!r}")


def _q_function_dictionary(
    keys: Sequence[str],
    values: Sequence[str],
    *,
    label: str,
) -> str:
    """Return a q dictionary with function values.

    Function values must be enlisted one by one; otherwise q applies ``!`` to a
    projected function list differently from a plain value list. Singleton keys
    are rendered as ``enlist[`key]`` so q does not enlist the dictionary result.
    """

    if len(keys) != len(values):
        raise KdbMetricQueryPlanError(f"{label} keys and values length mismatch")
    if not keys:
        return "()!()"
    rendered_keys = _q_symbol_list([_q_symbol(key, label) for key in keys])
    if len(values) == 1:
        return _q_singleton_dictionary_expression(rendered_keys, values[0])
    return f"{rendered_keys}!({';'.join(values)})"


def _source_function_dictionary(
    roles: Sequence[str],
    table_names: Mapping[str, str],
    source_functions: Mapping[str, str],
) -> str:
    """Return q dictionary of configured source function handles.

    Production report-day execution is kdb-owned; Python only passes handles for
    user-owned source functions. Direct table-name fallbacks remain for older
    single/batch callers and are not supported by the report-day runner.
    """

    keys: list[str] = []
    values: list[str] = []
    for role in roles:
        resolved_role = _resolve_source_key(role, table_names, source_functions)
        if resolved_role not in source_functions:
            raise KdbMetricQueryPlanError(
                "day query requires source_functions for role "
                f"{role!r}; table-name execution is only supported by legacy "
                "single/batch query paths"
            )
        keys.append(role)
        values.append(
            _q_function_identifier(
                source_functions[resolved_role],
                f"source_functions[{resolved_role!r}]",
            )
        )
    return _q_function_dictionary(keys, values, label="source_functions")


def _metric_parameter_dictionary(requests: Sequence[MetricRunRequest]) -> str:
    """Return q dictionary keyed by metric name with each metric parameter dict."""

    keys = [request.metric.name for request in requests]
    values = [_metric_params_expression(request) for request in requests]
    return _q_dictionary_expression(keys, values, "metric parameter dictionary")


def _universe_filter_dictionary(parameters: Mapping[str, Any]) -> str:
    """Return q dictionary of high-level universe filters.

    Python may pass user-requested CLI/config filters, but it must not discover
    or render the full production symbol universe. The installed q runner loads
    refs and derives/chunks the universe in kdb.
    """

    symbols = _symbol_filter_values(parameters)
    return _q_dictionary_expression(
        ["symbols"],
        [_q_symbol_vector_from_strings(symbols)],
        "universe filter dictionary",
    )


def _configured_chunk_size(parameters: Mapping[str, Any]) -> int:
    """Return configured q-side symbol chunk size."""

    value = parameters.get("chunk_size", parameters.get("symbol_chunk_size", 500))
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise KdbMetricQueryPlanError("parameter 'chunk_size' must be a positive integer")
    return value


def _source_roles_for_template(template_name: str) -> tuple[str, ...]:
    """Return source roles required by one template, excluding reference_data."""

    return tuple(
        source_key
        for source_key, _template_parameter in _METRIC_TABLE_PARAMETER_MAP[template_name]
        if source_key != "reference_data"
    )


def _batch_source_roles(requests: Sequence[MetricRunRequest]) -> tuple[str, ...]:
    roles: list[str] = []
    for request in requests:
        roles.extend(_source_roles_for_template(template_for_metric(request.metric.name)))
    return tuple(_dedupe(roles))


def _batch_source_parameters(requests: Sequence[MetricRunRequest]) -> dict[str, str]:
    """Return source parameters shared by a compatible day/chunk batch."""

    merged: dict[str, str] = {}
    for request in requests:
        params = _template_parameters_for_request(request)
        for key, value in params.items():
            if key.endswith("_table") or key == "ref_filter":
                existing = merged.get(key)
                if existing is not None and existing != value:
                    raise KdbMetricQueryPlanError(f"batch request has conflicting q source parameter {key!r}")
                merged[key] = value
    if "ref_table" not in merged:
        raise KdbMetricQueryPlanError("batch query requires reference-data source")
    merged.setdefault("ref_filter", "1b")
    return merged


def _batch_source_load_lines(
    source_roles: Sequence[str],
    params: Mapping[str, str],
) -> list[str]:
    """Return q assignments that load each raw source table once."""

    lines: list[str] = []
    for role in source_roles:
        local_name = _source_local_name(role)
        param_name = _source_param_name(role)
        if param_name not in params:
            raise KdbMetricQueryPlanError(f"batch query missing source parameter {param_name!r}")
        source_expr = params[param_name]
        lines.append(f"    {local_name}: {source_expr};")
        if role == "trades":
            lines.append(f"    rawTradeRows: rawTrades; / rawTradeRows: {source_expr};")
        elif role == "quotes":
            lines.append(f"    rawQuoteRows: rawQuotes; / rawQuoteRows: {source_expr};")
    return lines


def _source_param_name(role: str) -> str:
    mapping = {
        "trades": "trades_table",
        "quotes": "quotes_table",
        "pts_trades": "pts_trades_table",
        "pts_quotes": "pts_quotes_table",
        "primary_quotes": "primary_quotes_table",
    }
    try:
        return mapping[role]
    except KeyError as exc:
        raise KdbMetricQueryPlanError(f"unsupported source role {role!r}") from exc


def _source_local_name(role: str) -> str:
    mapping = {
        "trades": "rawTrades",
        "quotes": "rawQuotes",
        "pts_trades": "rawPtsTradeRows",
        "pts_quotes": "rawPtsQuoteRows",
        "primary_quotes": "rawPrimaryQuoteRows",
    }
    try:
        return mapping[role]
    except KeyError as exc:
        raise KdbMetricQueryPlanError(f"unsupported source role {role!r}") from exc


def _day_source_parameters(
    params: Mapping[str, str],
    trading_day: date,
) -> dict[str, str]:
    """Replace the rendered day literal in source calls with the runDate arg."""

    day_literal = _q_date(trading_day)
    return {key: value.replace(day_literal, "runDate") for key, value in params.items()}


def _representative_metric_requests(
    requests: Sequence[MetricRunRequest],
) -> tuple[MetricRunRequest, ...]:
    """Return one request per metric name in the first-seen production order."""

    seen: set[str] = set()
    out: list[MetricRunRequest] = []
    for request in requests:
        if request.metric.name in seen:
            continue
        seen.add(request.metric.name)
        out.append(request)
    return tuple(out)


def _day_symbol_values(requests: Sequence[MetricRunRequest]) -> tuple[str, ...]:
    """Return explicit day symbols from chunked request parameters."""

    symbols: list[str] = []
    for request in requests:
        symbols.extend(_symbol_filter_values(request.parameters))
    return tuple(_dedupe(symbols))


def _day_chunk_size(
    requests: Sequence[MetricRunRequest],
    all_symbols: Sequence[str],
) -> int:
    """Infer the configured chunk size from production chunk requests."""

    chunk_lengths = [
        len(_symbol_filter_values(request.parameters))
        for request in requests
        if _symbol_filter_values(request.parameters)
    ]
    if chunk_lengths:
        return max(chunk_lengths)
    return max(1, len(all_symbols))


def _aggregation_level_values(parameters: Mapping[str, Any]) -> tuple[str, ...]:
    """Return requested q-side rollup levels for production day execution."""

    raw = parameters.get(
        "aggregation_levels",
        (
            "market",
            "market_bucket",
            "topix_cap_group",
            "topix_cap_group_bucket",
            "symbol",
            "symbol_bucket",
        ),
    )
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise KdbMetricQueryPlanError("parameter 'aggregation_levels' must be a sequence of strings")
    levels = tuple(value for value in raw if isinstance(value, str) and value)
    if len(levels) != len(raw) or not levels:
        raise KdbMetricQueryPlanError("parameter 'aggregation_levels' must contain only non-empty strings")
    return levels


def _validate_day_request_compatibility(
    requests: Sequence[MetricRunRequest],
) -> None:
    """Validate requests can be run by one q-side day/chunk/rollup call."""

    first = requests[0]
    first_day = first.period.start_date
    first_source_functions = dict(first.source_functions)
    first_table_names = dict(first.table_names)
    first_namespace = first.calculation_namespace
    for request in requests:
        if request.period.start_date != first_day or request.period.end_date != first_day:
            raise KdbMetricQueryPlanError("day query requests must be single-day")
        if dict(request.source_functions) != first_source_functions:
            raise KdbMetricQueryPlanError("day query requests must share source_functions")
        if dict(request.table_names) != first_table_names:
            raise KdbMetricQueryPlanError("day query requests must share table_names")
        if request.calculation_namespace != first_namespace:
            raise KdbMetricQueryPlanError("day query requests must share calculation_namespace")


def _validate_batch_request_compatibility(
    requests: Sequence[MetricRunRequest],
) -> None:
    first = requests[0]
    first_symbols = _symbol_filter_values(first.parameters)
    first_period = first.period
    first_source_functions = dict(first.source_functions)
    first_table_names = dict(first.table_names)
    first_namespace = first.calculation_namespace
    for request in requests[1:]:
        if request.period != first_period:
            raise KdbMetricQueryPlanError("batch requests must share one trading-day period")
        if _symbol_filter_values(request.parameters) != first_symbols:
            raise KdbMetricQueryPlanError("batch requests must share one symbol chunk")
        if dict(request.source_functions) != first_source_functions:
            raise KdbMetricQueryPlanError("batch requests must share source_functions")
        if dict(request.table_names) != first_table_names:
            raise KdbMetricQueryPlanError("batch requests must share table_names")
        if request.calculation_namespace != first_namespace:
            raise KdbMetricQueryPlanError("batch requests must share calculation_namespace")


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
        return "([]date:0#0Nd;sym:`symbol$();ric:`symbol$();topixCapGrp:`symbol$();lotSize:0#0N)"

    raise KdbMetricQueryPlanError(
        f"missing source_functions or table_names entry {source_key!r} for metric {request.metric.name!r}"
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
        raise KdbMetricQueryPlanError("parameter 'max_primary_quote_age' must be a string")
    if not isinstance(max_pts_quote_age, str):
        raise KdbMetricQueryPlanError("parameter 'max_pts_quote_age' must be a string")

    exclude_auction = bool(request.parameters.get("exclude_auction", False))

    primary_venue_symbol = _q_symbol(primary_venue, "primary_venue")
    return {
        "value_column": _q_symbol_from_string(request.metric.name),
        "primary_venue": primary_venue_symbol,
        "venue_filter": (
            f"venue in {_q_symbol_vector(venues, 'venues')}"
            if venues
            else f"(not null venue) & venue <> {primary_venue_symbol}"
        ),
        "auction_filter": "auction = 0" if exclude_auction else "1b",
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
        raise KdbMetricQueryPlanError(f"unsupported primary quote reversion horizon: {horizon!r}") from exc


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
        raise KdbMetricQueryPlanError(f"invalid primary quote reversion metric: {metric_name!r}")
    return match.group("horizon")


def _required_string_parameter(request: MetricRunRequest, name: str) -> str:
    if name not in request.parameters:
        raise KdbMetricQueryPlanError(f"missing parameter {name!r} for metric {request.metric.name!r}")
    value = request.parameters[name]
    if not isinstance(value, str) or not value:
        raise KdbMetricQueryPlanError(f"parameter {name!r} must be a non-empty string")
    return value


def _required_string_sequence_parameter(
    request: MetricRunRequest,
    name: str,
) -> tuple[str, ...]:
    if name not in request.parameters:
        raise KdbMetricQueryPlanError(f"missing parameter {name!r} for metric {request.metric.name!r}")

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
        raise KdbMetricQueryPlanError(f"parameter {name!r} must be a sequence of strings")

    strings = tuple(item for item in value if isinstance(item, str) and item)
    if len(strings) != len(value) or not strings:
        raise KdbMetricQueryPlanError(f"parameter {name!r} must contain only non-empty strings")
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
            raise KdbMetricQueryPlanError("parameter 'symbols' must be a sequence of strings when provided")
        symbols = tuple(value for value in symbols_value if isinstance(value, str) and value)
        if len(symbols) != len(symbols_value):
            raise KdbMetricQueryPlanError("parameter 'symbols' must contain only non-empty strings")
        if symbol_value not in (None, "") and tuple(symbols) != (symbol_value,):
            raise KdbMetricQueryPlanError("parameters 'symbol' and 'symbols' conflict")
        return symbols

    if symbol_value in (None, ""):
        return ()
    if not isinstance(symbol_value, str):
        raise KdbMetricQueryPlanError("parameter 'symbol' must be a string when provided")
    return (symbol_value,)


def _q_symbol_list(rendered_symbols: Sequence[str]) -> str:
    """Return a q symbol list from already-rendered q symbol expressions.

    The singleton form uses bracket application so expressions like
    ``enlist[`refs]!enlist refs`` are parsed as a dictionary keyed by ``refs``,
    not as ``enlist (`refs!enlist refs)``.
    """

    if not rendered_symbols:
        return "0#`"
    if len(rendered_symbols) == 1:
        return f"enlist[{rendered_symbols[0]}]"
    return "(" + ";".join(rendered_symbols) + ")"


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
        raise KdbMetricQueryPlanError("parameter 'venues' must be a sequence of strings when provided")
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


def _bucket_expr_for_template(
    template_name: str,
    bucket: IntradayBucketSpec,
    calculation_namespace: str,
) -> str:
    """Return the bucket expression appropriate for trade or quote rows."""

    if template_name == "liquidity":
        duration = _bucket_duration(bucket)
        return f"{calculation_namespace}.timeBucketContinuous[time; {duration}]"
    return _bucket_expr(bucket, calculation_namespace)


def _bucket_expr(bucket: IntradayBucketSpec, calculation_namespace: str) -> str:
    duration = _bucket_duration(bucket)
    return f"{calculation_namespace}.timeBucket[time; session; auction; {duration}]"


def _bucket_duration(bucket: IntradayBucketSpec) -> str:
    if bucket.unit == "m":
        return f"0D00:{bucket.size:02d}:00.000"
    if bucket.unit == "h":
        return f"0D{bucket.size:02d}:00:00.000"
    if bucket.unit == "d":
        return "1D00:00:00.000"
    raise KdbMetricQueryPlanError(f"unsupported bucket unit: {bucket.unit}")


def _group_by_suffix(group_by: Sequence[str]) -> str:
    if not group_by:
        return ""
    identifiers = [_q_identifier(column, "group_by column") for column in group_by]
    return ", " + ", ".join(identifiers)


def _q_date(value: date) -> str:
    return f"{value.year:04d}.{value.month:02d}.{value.day:02d}"


def _q_time(value: time) -> str:
    return f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}.{value.microsecond // 1000:03d}"


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
    """Return a q symbol cast for any string value.

    Numeric Japanese security codes and configuration keys that contain
    underscores must be rendered with the leading backtick, for example
    `` `$"7203"`` or `` `$"reference_data"``. Rendering only ``$"..."`` sends an
    invalid expression to q instead of a symbol.
    """

    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'`$"{escaped}"'


_DURATION_RE = re.compile(r"^(?P<size>[1-9][0-9]*)(?P<unit>ms|s|m|h)$")


def _q_duration(value: str, label: str) -> str:
    match = _DURATION_RE.fullmatch(value)
    if match is None:
        raise KdbMetricQueryPlanError(f"invalid {label}: {value!r}; expected durations such as '10ms' or '1s'")

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
