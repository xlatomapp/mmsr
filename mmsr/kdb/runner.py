"""Metric runner interface for kdb-backed calculations."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from numbers import Real
from typing import Any

from mmsr.kdb.cache import (
    MetricDayCacheHooks,
    MetricDayCacheKey,
    merge_stock_metrics_rows,
    metric_series_from_stock_metrics_rows,
    stock_metrics_rows_from_series,
)
from mmsr.kdb.client import KdbClient
from mmsr.kdb.query_loader import render_calculation_function_bootstrap
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
        cache_hooks: MetricDayCacheHooks | None = None,
    ) -> None:
        self.client = client
        self.query_planner = KdbMetricQueryPlanner() if query_planner is None else query_planner
        self.cache_hooks = MetricDayCacheHooks() if cache_hooks is None else cache_hooks
        self._installed_calculation_namespaces: set[str] = set()

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
        self.client.execute(render_calculation_function_bootstrap(calculation_namespace))
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

        When ``cache_hooks`` are configured, this method first asks the preferred
        wide ``stockMetrics`` loader for all requested metric columns, then falls
        back to any per-metric loader. Fully cached requests do not execute kdb.
        Cache misses are run through the normal q path and persisted after schema
        validation and normalization.
        """

        clean_requests = tuple(requests)
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
        raw_result = self.client.execute(plan.query)
        LOGGER.info("Received kdb day result for metrics=%s", ", ".join(plan.metric_names))
        result_by_metric = _coerce_batch_result(
            raw_result,
            fallback_metric_name=plan.metric_names[0] if len(plan.metric_names) == 1 else None,
        )
        computed_by_metric: dict[str, MetricTimeSeries] = {}
        request_by_metric = {request.metric.name: request for request in missing_requests}
        for metric_query in plan.metric_queries:
            if metric_query.metric_name not in result_by_metric:
                available = ", ".join(sorted(result_by_metric)) or "none"
                raise KdbMetricRunnerError(
                    f"day result is missing metric {metric_query.metric_name!r}; available metrics: {available}"
                )
            metric_result = result_by_metric[metric_query.metric_name]
            metric_query.validate_result_schema(metric_result)
            LOGGER.debug("Validated day result schema for metric=%s", metric_query.metric_name)
            series = normalize_metric_result(
                metric_name=metric_query.metric_name,
                result=metric_result,
                group_by=metric_query.result_group_by,
                metadata={
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
                    "cache_status": "miss",
                },
            )
            computed_by_metric[metric_query.metric_name] = series

        self._persist_day_results(
            tuple(request_by_metric[name] for name in plan.metric_names),
            tuple(computed_by_metric[name] for name in plan.metric_names),
        )

        combined = {**cached_by_metric, **computed_by_metric}
        return tuple(combined[request.metric.name] for request in clean_requests)

    def _load_cached_day_results(
        self,
        requests: Sequence[MetricRunRequest],
    ) -> tuple[dict[str, MetricTimeSeries], tuple[MetricRunRequest, ...]]:
        """Load cached day results and return misses in request order.

        The preferred production path is ``load_stock_metrics`` because it lets a
        user read one wide day-level ``stockMetrics`` table for all requested
        metrics. Per-metric ``load`` remains as a compatibility fallback for
        cache implementations that have not moved to the wide table shape.
        """

        if not (self.cache_hooks.load_stock_metrics is not None or self.cache_hooks.load is not None):
            return {}, tuple(requests)

        cached_by_metric: dict[str, MetricTimeSeries] = {}
        keys_by_metric = {request.metric.name: MetricDayCacheKey.from_request(request) for request in requests}

        if self.cache_hooks.load_stock_metrics is not None and requests:
            keys = tuple(keys_by_metric[request.metric.name] for request in requests)
            rows = self.cache_hooks.load_stock_metrics(
                keys[0].trading_day,
                tuple(requests),
                keys,
                tuple(request.metric.name for request in requests),
            )
            if rows is not None:
                stock_metric_rows = tuple(rows)
                for request in requests:
                    metric_name = request.metric.name
                    series = metric_series_from_stock_metrics_rows(
                        metric_name,
                        stock_metric_rows,
                        metadata={"storage": "stockMetrics"},
                    )
                    if series is None:
                        continue
                    key = keys_by_metric[metric_name]
                    _validate_cached_day_series(key, series)
                    cached_by_metric[metric_name] = _with_cache_status(series, "hit")

        missing_requests = [request for request in requests if request.metric.name not in cached_by_metric]

        if self.cache_hooks.load is not None:
            still_missing: list[MetricRunRequest] = []
            for request in missing_requests:
                key = keys_by_metric[request.metric.name]
                series = self.cache_hooks.load(key, request)
                if series is None:
                    still_missing.append(request)
                    continue
                _validate_cached_day_series(key, series)
                cached_by_metric[request.metric.name] = _with_cache_status(series, "hit")
            missing_requests = still_missing

        return cached_by_metric, tuple(missing_requests)

    def _persist_day_results(
        self,
        requests: Sequence[MetricRunRequest],
        series_items: Sequence[MetricTimeSeries],
    ) -> None:
        """Persist computed day results through the preferred configured hook."""

        if not requests:
            return

        keys = tuple(MetricDayCacheKey.from_request(request) for request in requests)
        if self.cache_hooks.persist_stock_metrics is not None:
            rows = merge_stock_metrics_rows(
                [stock_metrics_rows_from_series(key, series) for key, series in zip(keys, series_items, strict=True)]
            )
            self.cache_hooks.persist_stock_metrics(
                keys[0].trading_day,
                tuple(requests),
                keys,
                rows,
            )
            return

        if self.cache_hooks.persist is None:
            return

        for key, request, series in zip(keys, requests, series_items, strict=True):
            self.cache_hooks.persist(key, request, series)

    def run(self, request: MetricRunRequest) -> MetricTimeSeries:
        """Run a supported metric request and return normalized observations.

        Query templates are rendered into an explicit query plan before
        execution. The plan's output schema contract is validated against the
        returned table-like object before row normalization.
        """

        plan = self.plan_query(request)
        LOGGER.info(
            "Running kdb metric query: metric=%s family=%s",
            request.metric.name,
            metric_family_for_metric(request.metric.name),
        )
        self.ensure_calculation_functions(plan.calculation_namespace)
        raw_result = self.client.execute(plan.query)
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


def _validate_cached_day_series(
    key: MetricDayCacheKey,
    series: MetricTimeSeries,
) -> None:
    """Validate a user-loaded cached series before returning it."""

    if series.metric_name != key.metric_name:
        raise KdbMetricRunnerError(
            f"cached metric day result for {key.metric_name!r} returned series {series.metric_name!r}"
        )
    wrong_dates = sorted({observation.date for observation in series.observations} - {key.trading_day})
    if wrong_dates:
        raise KdbMetricRunnerError(
            f"cached metric day result for {key.metric_name!r} contains "
            f"date(s) outside {key.trading_day}: {wrong_dates}"
        )


def _with_cache_status(series: MetricTimeSeries, status: str) -> MetricTimeSeries:
    """Return ``series`` with cache metadata without mutating user objects."""

    metadata = dict(series.metadata)
    metadata["cache_status"] = status
    return MetricTimeSeries(
        metric_name=series.metric_name,
        observations=series.observations,
        metadata=metadata,
    )


def _coerce_batch_result(
    result: Any,
    *,
    fallback_metric_name: str | None = None,
) -> dict[str, Any]:
    """Coerce a q dictionary/Python mapping of metric name to result table."""

    converted = _maybe_to_python(result)
    if not isinstance(converted, Mapping):
        if fallback_metric_name is not None:
            return {fallback_metric_name: converted}
        raise KdbMetricRunnerError("batch metric result must be a mapping")
    out: dict[str, Any] = {}
    for raw_key, value in converted.items():
        key = _coerce_batch_metric_key(raw_key)
        out[key] = value
    return out


def _coerce_batch_metric_key(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode()
    key = str(value)
    return key[1:] if key.startswith("`") else key


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
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing value column {metric_name!r}")
        if "date" not in row:
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing 'date'")

        group = _extract_group(row, group_by, row_index)
        used_columns = {"date", "time_bucket", metric_name, *group_by}
        row_metadata = {key: value for key, value in row.items() if key not in used_columns}

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
    group: dict[str, str] = {}
    for column in group_by:
        if column not in row:
            raise KdbMetricRunnerError(f"metric result row {row_index} is missing group column {column!r}")
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
