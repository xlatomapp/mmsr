"""Metric runner interface for kdb-backed calculations."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import replace
from datetime import date, datetime, time
from numbers import Real
from typing import Any

from mmsr.kdb.client import KdbClient
from mmsr.kdb.query_loader import (
    render_calculation_function_bootstrap,
    render_calculation_function_bootstrap_steps,
)
from mmsr.kdb.query_plan import (
    KdbMetricQueryPlanError,
    KdbMetricQueryPlanner,
    MetricRunRequest,
    RenderedMetricDayQuery,
    RenderedMetricQuery,
    metric_family_for_metric,
)
from mmsr.metrics.results import MetricObservation, MetricTimeSeries

KdbMetricRunnerError = KdbMetricQueryPlanError

LOGGER = logging.getLogger(__name__)

class KdbMetricRunner:
    """Runs planned metric queries through kdb+ and normalizes their output."""

    def __init__(
        self,
        client: KdbClient,
        *,
        query_planner: KdbMetricQueryPlanner | None = None,
        q_day_cache_functions: Mapping[str, Any] | None = None,
        isolate_calculation_namespace_per_run: bool = False,
        keep_isolated_calculation_namespace: bool = False,
    ) -> None:
        self.client = client
        self.query_planner = KdbMetricQueryPlanner() if query_planner is None else query_planner
        self.q_day_cache_functions = {} if q_day_cache_functions is None else dict(q_day_cache_functions)
        self._installed_calculation_namespaces: set[str] = set()
        self._installed_report_config_by_namespace: dict[str, str] = {}
        self.isolate_calculation_namespace_per_run = isolate_calculation_namespace_per_run
        self.keep_isolated_calculation_namespace = keep_isolated_calculation_namespace

    def install_calculation_functions(
        self,
        calculation_namespace: str = ".mmsr",
    ) -> None:
        """Install MMSR-owned reusable q helpers into ``calculation_namespace``.

        Production source functions remain user-owned and should return raw
        canonical rows. This method installs the package-owned calculation and
        aggregation helpers that metric templates use inside kdb+.
        """

        LOGGER.info("Installing MMSR q calculations into %s", calculation_namespace)
        try:
            bootstrap_steps = render_calculation_function_bootstrap_steps(calculation_namespace)
        except Exception:
            LOGGER.exception(
                "Failed to split rendered q bootstrap into per-function steps; falling back to one-shot install"
            )
            self.client.execute(render_calculation_function_bootstrap(calculation_namespace))
        else:
            for function_name, source_block in bootstrap_steps:
                LOGGER.info("Installing q function %s.%s", calculation_namespace, function_name)
                self.client.execute(source_block)
        self._installed_calculation_namespaces.add(calculation_namespace)
        LOGGER.info("Installed MMSR q calculations into %s", calculation_namespace)

    def ensure_calculation_functions(
        self,
        calculation_namespace: str = ".mmsr",
    ) -> None:
        """Install MMSR q helpers once per calculation namespace."""

        if not isinstance(self.client, KdbClient):
            return
        if calculation_namespace not in self._installed_calculation_namespaces:
            self.install_calculation_functions(calculation_namespace)

    def plan_query(self, request: MetricRunRequest) -> RenderedMetricQuery:
        """Render q and expose required/optional kdb table schema without IO."""

        return self.query_planner.render(request)

    def plan_day(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> RenderedMetricDayQuery:
        """Render one q query that loops chunks and rolls up one full day."""

        return self.query_planner.render_day(requests)

    def render_query(self, request: MetricRunRequest) -> tuple[str, str]:
        """Render the q query for ``request`` and return ``(query, template_name)``.

        Prefer ``plan_query`` for new code because it also exposes input and
        output table contracts for production query hardening.
        """

        plan = self.plan_query(request)
        return plan.query, plan.template_name

    def run_day(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> tuple[MetricTimeSeries, ...]:
        """Run one full trading-day query with q-side chunking and rollups.

        When a q day-cache load function is configured, this method first asks
        that function for the unified day fact table. Fully cached requests do
        not execute ``runReportDay``. Cache misses are run through the normal q
        path and may then be persisted through the configured q day-cache
        persist function.
        """

        clean_requests = tuple(requests)
        run_namespace = self._ephemeral_namespace_for_requests(clean_requests)
        if run_namespace is not None:
            clean_requests = tuple(
                replace(request, calculation_namespace=run_namespace) for request in clean_requests
            )
        cached_by_metric, missing_requests = self._load_cached_day_results(clean_requests)
        if not missing_requests:
            return tuple(cached_by_metric[request.metric.name] for request in clean_requests)

        plan = self.plan_day(missing_requests)
        LOGGER.info(
            "Running kdb day query: metrics=%s chunk_size=%s universe=kdb-owned",
            ", ".join(plan.metric_names),
            plan.chunk_size,
        )
        self.ensure_calculation_functions(plan.metric_queries[0].calculation_namespace)
        calculation_namespace = plan.metric_queries[0].calculation_namespace
        current_report_config = self._installed_report_config_by_namespace.get(calculation_namespace)
        if current_report_config != plan.report_config_expression:
            self.client.execute(f"{calculation_namespace}.reportConfig:{plan.report_config_expression}")
            self._installed_report_config_by_namespace[calculation_namespace] = plan.report_config_expression
        try:
            raw_result = self.client.execute(plan.query)
        finally:
            self._cleanup_ephemeral_namespace(run_namespace)
        LOGGER.info("Received kdb day result for metrics=%s", ", ".join(plan.metric_names))
        result_by_metric, unified_rows = _coerce_day_result(
            raw_result,
            metric_names=plan.metric_names,
        )
        computed_by_metric = self._normalize_day_metric_rows(
            plan,
            result_by_metric=result_by_metric,
            unified_rows=unified_rows,
            cache_status="miss",
            require_all_metrics=True,
        )

        self._persist_q_cached_day_rows(missing_requests, plan, unified_rows)

        combined = {**cached_by_metric, **computed_by_metric}
        return tuple(combined[request.metric.name] for request in clean_requests)

    def _ephemeral_namespace_for_requests(self, requests: Sequence[MetricRunRequest]) -> str | None:
        if not self.isolate_calculation_namespace_per_run or not requests:
            return None
        base_namespace = requests[0].calculation_namespace
        token = f"run_{uuid.uuid4().hex}"
        return f"{base_namespace}.{token}"

    def _cleanup_ephemeral_namespace(self, namespace: str | None) -> None:
        if namespace is None or self.keep_isolated_calculation_namespace or not isinstance(self.client, KdbClient):
            return
        parts = namespace.split(".")
        if len(parts) < 3:
            return
        parent = "." + ".".join(parts[1:-1])
        child = parts[-1]
        try:
            self.client.execute(f"delete {child} from `{parent}")
            self._installed_calculation_namespaces.discard(namespace)
            self._installed_report_config_by_namespace.pop(namespace, None)
        except Exception:
            LOGGER.exception("Failed to cleanup ephemeral calculation namespace %s", namespace)

    def _load_cached_day_results(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> tuple[dict[str, MetricTimeSeries], tuple[MetricRunRequest, ...]]:
        """Load cached day results and return misses in request order.

        The only supported day-cache path is a configured q load function that
        returns the unified day fact table for one trading day.
        """

        if not bool(self.q_day_cache_functions.get("use_load")):
            return {}, tuple(requests)

        cached_by_metric = self._load_q_cached_day_results(requests)
        missing_requests = [request for request in requests if request.metric.name not in cached_by_metric]
        return cached_by_metric, tuple(missing_requests)

    def _load_q_cached_day_results(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> dict[str, MetricTimeSeries]:
        load_function = self.q_day_cache_functions.get("load")
        if not self.q_day_cache_functions.get("use_load") or not isinstance(load_function, str) or not requests:
            return {}
        plan = self.plan_day(requests)
        raw_result = self.client.execute(
            f"{{[tradingDay] {load_function}[tradingDay]}}",
            requests[0].period.start_date,
        )
        converted = _maybe_to_python(raw_result)
        unified_rows = _coerce_unified_day_rows(converted)
        if unified_rows is None:
            candidate_rows = _coerce_rows(converted)
            if candidate_rows:
                raise KdbMetricRunnerError(
                    "configured q day-cache load function returned rows that do not match the unified metric fact schema"
                )
            return {}
        if not unified_rows:
            return {}
        result_by_metric, unified_rows = _coerce_day_result(
            unified_rows,
            metric_names=plan.metric_names,
        )
        return self._normalize_day_metric_rows(
            plan,
            result_by_metric=result_by_metric,
            unified_rows=unified_rows,
            cache_status="hit",
            require_all_metrics=False,
        )

    def _persist_q_cached_day_rows(
        self,
        requests: Sequence[MetricRunRequest],
        plan: RenderedMetricDayQuery,
        unified_rows: Sequence[Mapping[str, Any]],
    ) -> None:
        persist_function = self.q_day_cache_functions.get("persist")
        persist_mode = self.q_day_cache_functions.get("persist_mode", "upsert")
        if (
            not self.q_day_cache_functions.get("use_persist")
            or not isinstance(persist_function, str)
            or not plan.metric_queries
        ):
            return
        if persist_mode not in {"overwrite", "upsert"}:
            raise KdbMetricRunnerError(
                f"configured q day-cache persist_mode must be 'overwrite' or 'upsert', got {persist_mode!r}"
            )
        persisted = self.client.execute(
            f"{{[tradingDay;rows;persistMode] {persist_function}[tradingDay;rows;persistMode]}}",
            _coerce_date(unified_rows[0]["date"], 0) if unified_rows else requests[0].period.start_date,
            tuple(dict(row) for row in unified_rows),
            persist_mode,
        )
        if not bool(_maybe_to_python(persisted)):
            raise KdbMetricRunnerError("configured q day-cache persist function returned false")

    def _normalize_day_metric_rows(
        self,
        plan: RenderedMetricDayQuery,
        *,
        result_by_metric: Mapping[str, Sequence[dict[str, Any]]],
        unified_rows: Sequence[dict[str, Any]],
        cache_status: str,
        require_all_metrics: bool,
    ) -> dict[str, MetricTimeSeries]:
        normalized: dict[str, MetricTimeSeries] = {}
        for metric_query in plan.metric_queries:
            metric_rows = result_by_metric.get(metric_query.metric_name, ())
            series_metadata = {
                "metric_family": metric_family_for_metric(metric_query.metric_name),
                "query": plan.query,
                "requested_group_by": metric_query.requested_group_by,
                "group_by": metric_query.result_group_by,
                "required_output_columns": metric_query.required_output_columns,
                "optional_output_columns": metric_query.optional_output_columns,
                "source_functions": metric_query.source_functions,
                "calculation_namespace": metric_query.calculation_namespace,
                "day_metrics": plan.metric_names,
                "chunk_size": plan.chunk_size,
                "execution_shape": "day_q_chunk_rollup",
                "cache_status": cache_status,
            }
            if require_all_metrics and metric_query.metric_name not in result_by_metric:
                available = ", ".join(sorted(result_by_metric)) or "none"
                raise KdbMetricRunnerError(
                    f"day result is missing metric {metric_query.metric_name!r}; available metrics: {available}"
                )
            if not metric_rows:
                if metric_query.metric_name in result_by_metric:
                    normalized[metric_query.metric_name] = MetricTimeSeries.from_observations(
                        (),
                        metric_name=metric_query.metric_name,
                        metadata=series_metadata,
                    )
                continue
            normalized_result: Any = [
                row
                for row in unified_rows
                if row["metricName"] == metric_query.metric_name
                and _row_matches_group_by(row, metric_query.result_group_by)
            ]
            supplemental_symbol_rows: list[dict[str, Any]] = []
            if "sym" not in metric_query.result_group_by:
                supplemental_symbol_rows = [
                    row
                    for row in unified_rows
                    if row["metricName"] == metric_query.metric_name
                    and _row_matches_group_by(row, ("sym",))
                ]
            series = normalize_metric_result(
                metric_name=metric_query.metric_name,
                result=normalized_result,
                group_by=metric_query.result_group_by,
                metadata=series_metadata,
            )
            if supplemental_symbol_rows:
                supplemental_symbol_series = normalize_metric_result(
                    metric_name=metric_query.metric_name,
                    result=supplemental_symbol_rows,
                    group_by=("sym",),
                    metadata={},
                )
                series = replace(
                    series,
                    metadata={
                        **series.metadata,
                        "supplemental_symbol_observations": supplemental_symbol_series.observations,
                    },
                )
            normalized[metric_query.metric_name] = series
        return normalized

    def run(self, request: MetricRunRequest) -> MetricTimeSeries:
        """Run a supported metric request and return normalized observations.

        Query templates are rendered into an explicit query plan before
        execution. The plan's output schema contract is validated against the
        returned table-like object before row normalization.
        """

        run_namespace = self._ephemeral_namespace_for_requests((request,))
        if run_namespace is not None:
            request = replace(request, calculation_namespace=run_namespace)
        plan = self.plan_query(request)
        LOGGER.info(
            "Running kdb metric query: metric=%s family=%s",
            request.metric.name,
            metric_family_for_metric(request.metric.name),
        )
        self.ensure_calculation_functions(plan.calculation_namespace)
        try:
            raw_result = self.client.execute(plan.query)
        finally:
            self._cleanup_ephemeral_namespace(run_namespace)
        plan.validate_result_schema(raw_result)
        LOGGER.debug("Validated metric result schema for metric=%s", request.metric.name)
        return normalize_metric_result(
            metric_name=request.metric.name,
            result=raw_result,
            group_by=plan.result_group_by,
            metadata={
                "template": plan.template_name,
                "query": plan.query,
                "requested_group_by": plan.requested_group_by,
                "group_by": plan.result_group_by,
                "required_output_columns": plan.required_output_columns,
                "optional_output_columns": plan.optional_output_columns,
                "source_functions": plan.source_functions,
                "calculation_namespace": plan.calculation_namespace,
            },
        )

def _coerce_batch_metric_key(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode()
    key = str(value)
    return key[1:] if key.startswith("`") else key


def _coerce_day_result(
    result: Any,
    *,
    metric_names: Sequence[str],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Coerce a q day result into the canonical unified long-row day shape."""

    converted = _maybe_to_python(result)
    unified_rows = _coerce_unified_day_rows(converted)
    if unified_rows is None:
        raise KdbMetricRunnerError("day result must be a unified metric fact table with metricName rows")
    metric_row_groups: dict[str, list[dict[str, Any]]] = {}
    for row in unified_rows:
        metric_name = _coerce_batch_metric_key(row["metricName"])
        row["metricName"] = metric_name
        metric_row_groups.setdefault(metric_name, []).append(row)
    result_by_metric = {
        metric_name: metric_row_groups.get(metric_name, [])
        for metric_name in metric_names
    }
    return result_by_metric, unified_rows


def _coerce_unified_day_rows(result: Any) -> list[dict[str, Any]] | None:
    if isinstance(result, Mapping):
        keyed_mapping = _unkey_mapping(result)
        column_mapping = keyed_mapping if keyed_mapping is not None else result
        if "metricName" in column_mapping:
            return _rows_from_column_mapping(column_mapping)
    rows = _coerce_rows(result)
    if not rows:
        return None
    if "metricName" not in rows[0]:
        return None
    return rows


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
        value_column = "metricValue" if "metricValue" in row else metric_name
        if value_column not in row:
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing value column {metric_name!r}")
        if "date" not in row:
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing 'date'")

        group = _extract_group(row, group_by, row_index)
        used_columns = {"date", "timeBucket", "metricName", value_column, *group_by}
        row_metadata = {key: value for key, value in row.items() if key not in used_columns}

        observations.append(
            MetricObservation(
                metric_name=metric_name,
                date=_coerce_date(row["date"], row_index),
                time_bucket=_coerce_time_bucket(row.get("timeBucket")),
                group=group,
                value=_coerce_numeric_value(row[value_column], row_index, metric_name),
                metadata=row_metadata,
            )
        )

    return MetricTimeSeries.from_observations(
        observations,
        metric_name=metric_name,
        metadata={} if metadata is None else dict(metadata),
    )


def _maybe_to_python(result: Any) -> Any:
    converter = getattr(result, "py", None)
    if callable(converter):
        return converter()
    return result


def _coerce_rows(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, Mapping):
        keyed_mapping = _unkey_mapping(result)
        if keyed_mapping is not None:
            return _rows_from_column_mapping(keyed_mapping)
        return _rows_from_column_mapping(result)

    dataframe_rows = _rows_from_dataframe_like(result)
    if dataframe_rows is not None:
        return dataframe_rows

    if isinstance(result, Sequence) and not isinstance(result, (str, bytes, bytearray)):
        rows: list[dict[str, Any]] = []
        for index, row in enumerate(result):
            if not isinstance(row, Mapping):
                raise KdbMetricRunnerError(
                    f"list-like metric results must contain row dictionaries; row {index} has type {type(row).__name__}"
                )
            rows.append(dict(row))
        return rows

    raise KdbMetricRunnerError("metric result must be a dict of columns or a list of row dictionaries")


def _unkey_mapping(result: Mapping[Any, Any]) -> dict[str, Any] | None:
    """Merge common keyed-table mapping representations into column mappings."""

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

    merged: dict[str, Any] = {}
    merged.update({str(column): values for column, values in keys_part.items()})
    merged.update({str(column): values for column, values in values_part.items()})
    return merged


def _rows_from_dataframe_like(result: Any) -> list[dict[str, Any]] | None:
    """Convert pandas-like DataFrames, including keyed-table indexes, to rows."""

    columns = getattr(result, "columns", None)
    if columns is None:
        return None

    index = getattr(result, "index", None)
    index_names = tuple(str(name) for name in getattr(index, "names", ()) if name is not None)
    reset_index = getattr(result, "reset_index", None)
    if index_names and callable(reset_index):
        result = reset_index()
        columns = getattr(result, "columns", columns)

    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        records = to_dict("records")
        if isinstance(records, list):
            return [dict(row) for row in records]

    return None


def _rows_from_column_mapping(columns: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not columns:
        return []

    column_values = {str(column_name): _as_column_values(raw_values) for column_name, raw_values in columns.items()}
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
    derived_group = _group_from_unified_row(row)
    group: dict[str, str] = {}
    for column in group_by:
        if column in derived_group:
            value = derived_group[column]
        elif column in row:
            value = row[column]
        else:
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing group column {column!r}")
        if value is not None:
            group[column] = str(value)
    return group


def _row_matches_group_by(row: Mapping[str, Any], group_by: Sequence[str]) -> bool:
    derived_group = _group_from_unified_row(row)
    expected = set(group_by)
    if any(column not in expected for column in derived_group):
        return False
    return all(column in derived_group or column in row for column in group_by)


def _group_from_unified_row(row: Mapping[str, Any]) -> dict[str, str]:
    if "groupType" not in row or "groupValue" not in row:
        return {}
    raw_group_type = row["groupType"]
    raw_group_value = row["groupValue"]

    if _is_sequence_group_descriptor(raw_group_type) or _is_sequence_group_descriptor(raw_group_value):
        group_types = _group_descriptor_sequence(raw_group_type)
        group_values = _group_descriptor_sequence(raw_group_value)
        if len(group_types) == len(group_values):
            return {
                str(group_key): str(group_value)
                for group_key, group_value in zip(group_types, group_values, strict=True)
            }
        return {}

    group_type = str(raw_group_type)
    group_value = str(raw_group_value)

    if group_type == "market" and group_value in {"ALL", "TSE"}:
        return {}
    if group_type in {"symbol", "sym"}:
        return {"sym": group_value}
    return {group_type: group_value}


def _is_sequence_group_descriptor(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _group_descriptor_sequence(value: Any) -> list[Any]:
    if _is_sequence_group_descriptor(value):
        return list(value)
    return [value]


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
            raise KdbMetricRunnerError(f"metric result row {row_index} has invalid date value {value!r}") from exc
    raise KdbMetricRunnerError(f"metric result row {row_index} has unsupported date value {value!r}")


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
        f"metric result row {row_index} has non-numeric value for {metric_name!r}: {converted!r}"
    )
