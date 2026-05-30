"""Pluggable metric-result cache hooks for kdb-backed day runs."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, time
from typing import Any, Protocol

from mmsr.kdb.query_plan import MetricRunRequest
from mmsr.metrics.results import MetricObservation, MetricTimeSeries

STOCK_METRICS_DIMENSION_COLUMNS: tuple[str, ...] = (
    "date",
    "timeBucket",
    "bucketSize",
    "sym",
    "groupType",
    "groupValue",
)


class MetricDayCacheLoader(Protocol):
    """User-provided function that can load one day/metric result.

    Return ``None`` when the requested metric/day is not available in the cache.
    Implementations may use the supplied ``MetricDayCacheKey`` and full request
    to include grouping, bucket, universe, or metric parameters in their storage
    layout.

    The recommended storage shape is the wide ``stockMetrics`` table produced by
    :func:`stock_metrics_rows_from_series`. Loader implementations can read that
    table and return one normalized :class:`~mmsr.metrics.results.MetricTimeSeries`
    for the requested metric.
    """

    def __call__(
        self,
        key: MetricDayCacheKey,
        request: MetricRunRequest,
    ) -> MetricTimeSeries | None:
        """Load cached normalized metric data for ``key`` if available."""


class MetricDayCachePersister(Protocol):
    """User-provided function that persists one day/metric result.

    Persisters should prefer the canonical ``stockMetrics`` shape with columns
    ``date``, ``timeBucket``, ``bucketSize``, ``sym``, ``groupType``,
    ``groupValue``, and metric columns. MMSR keeps the hook normalized for
    backwards compatibility, and provides :func:`stock_metrics_rows_from_series`
    to build the rows to persist.
    """

    def __call__(
        self,
        key: MetricDayCacheKey,
        request: MetricRunRequest,
        series: MetricTimeSeries,
    ) -> None:
        """Persist normalized metric data for ``key``."""


class StockMetricsDayCacheLoader(Protocol):
    """User-provided function that loads wide ``stockMetrics`` rows once per day.

    The loader is called once by :meth:`mmsr.kdb.runner.KdbMetricRunner.run_day`
    before any per-metric fallback loader. It should return rows at the canonical
    ``stockMetrics`` grain for the requested day and metrics, or ``None`` when no
    day cache is available. MMSR hydrates whichever requested metric columns are
    present and computes only the missing metrics.
    """

    def __call__(
        self,
        trading_day: date,
        requests: Sequence[MetricRunRequest],
        keys: Sequence[MetricDayCacheKey],
        metric_names: Sequence[str],
    ) -> Iterable[Mapping[str, Any]] | None:
        """Load canonical wide ``stockMetrics`` rows for one trading day."""


class StockMetricsDayCachePersister(Protocol):
    """User-provided function that persists wide ``stockMetrics`` rows once.

    The persister receives only newly computed metric rows after q execution and
    schema normalization. Existing cached rows are not passed back to avoid
    rewriting user-owned cache data unnecessarily.
    """

    def __call__(
        self,
        trading_day: date,
        requests: Sequence[MetricRunRequest],
        keys: Sequence[MetricDayCacheKey],
        rows: Sequence[Mapping[str, Any]],
    ) -> None:
        """Persist canonical wide ``stockMetrics`` rows for one trading day."""


@dataclass(frozen=True)
class MetricDayCacheKey:
    """Stable cache identity for one normalized metric/day result.

    ``bucket_size`` records the configured continuous-session interval such as
    ``5m``. Individual rows should store the actual ``timeBucket`` separately,
    for example ``09:00-09:05`` or ``AMO``. MMSR does not persist a bucket type or
    sort key in the cache contract because those are inferable from the bucket
    label and configured bucket size.
    """

    trading_day: date
    metric_name: str
    bucket_size: str
    group_by: tuple[str, ...]
    parameters: tuple[tuple[str, str], ...]
    source_functions: tuple[tuple[str, str], ...]
    table_names: tuple[tuple[str, str], ...]
    calculation_namespace: str

    @classmethod
    def from_request(cls, request: MetricRunRequest) -> MetricDayCacheKey:
        """Build a cache key from a single-day metric run request."""

        return cls(
            trading_day=request.period.start_date,
            metric_name=request.metric.name,
            bucket_size=request.period.bucket.value,
            group_by=tuple(request.group_by),
            parameters=_stable_items(request.parameters),
            source_functions=tuple(sorted((str(k), str(v)) for k, v in request.source_functions.items())),
            table_names=tuple(sorted((str(k), str(v)) for k, v in request.table_names.items())),
            calculation_namespace=request.calculation_namespace,
        )

    @property
    def bucket(self) -> str:
        """Backward-compatible alias for the configured bucket size."""

        return self.bucket_size

    @property
    def fingerprint(self) -> tuple[object, ...]:
        """Return execution-shaping fields beyond the metric/day identity."""

        return (
            self.bucket_size,
            self.group_by,
            self.parameters,
            self.source_functions,
            self.table_names,
            self.calculation_namespace,
        )


@dataclass(frozen=True)
class MetricDayCacheHooks:
    """Optional user plug-in hooks for loading and persisting metric day data.

    ``load_stock_metrics`` and ``persist_stock_metrics`` are the preferred hooks
    for production caches because they read/write one wide day table for all
    requested metric columns. ``load`` and ``persist`` remain supported as
    per-metric compatibility hooks.
    """

    load: MetricDayCacheLoader | None = None
    persist: MetricDayCachePersister | None = None
    load_stock_metrics: StockMetricsDayCacheLoader | None = None
    persist_stock_metrics: StockMetricsDayCachePersister | None = None

    @property
    def enabled(self) -> bool:
        """Return ``True`` when any cache hook is configured."""

        return any(
            hook is not None
            for hook in (
                self.load,
                self.persist,
                self.load_stock_metrics,
                self.persist_stock_metrics,
            )
        )


def stock_metrics_rows_from_series(
    key: MetricDayCacheKey,
    series: MetricTimeSeries,
) -> tuple[dict[str, Any], ...]:
    """Convert one normalized metric series into canonical ``stockMetrics`` rows.

    The canonical persisted dimensions are deliberately narrow:

    - ``date``
    - ``timeBucket``
    - ``bucketSize``
    - ``sym``
    - ``groupType``
    - ``groupValue``

    ``timeBucket`` is the actual report segment label from the metric result,
    such as ``09:00-09:05`` or ``AMO``. ``bucketSize`` is the configured
    continuous-session interval such as ``5m``. No bucket type or sort column is
    stored because MMSR can infer those when rendering/reporting.
    """

    rows: list[dict[str, Any]] = []
    for observation in series.observations:
        group_type, group_value = _stock_metric_group(observation.group)
        row: dict[str, Any] = {
            "date": observation.date,
            "timeBucket": _stock_metric_time_bucket(observation.time_bucket),
            "bucketSize": key.bucket_size,
            "sym": observation.group.get("sym", "ALL"),
            "groupType": group_type,
            "groupValue": group_value,
            series.metric_name: observation.value,
        }
        rows.append(row)
    return tuple(rows)


def metric_series_from_stock_metrics_rows(
    metric_name: str,
    rows: Iterable[Mapping[str, Any]],
    *,
    metadata: Mapping[str, Any] | None = None,
) -> MetricTimeSeries | None:
    """Build one metric series from canonical ``stockMetrics`` rows.

    Return ``None`` when the requested metric column is absent from every row.
    This is intended for user cache loaders that read a wide day-level table and
    need to hydrate the normalized MMSR result expected by the runner.
    """

    observations: list[MetricObservation] = []
    metric_seen = False
    for index, row in enumerate(rows):
        if metric_name not in row:
            continue
        metric_seen = True
        observations.append(
            MetricObservation(
                metric_name=metric_name,
                date=_coerce_stock_metric_date(row.get("date"), index),
                time_bucket=row.get("timeBucket"),
                group=_group_from_stock_metric_row(row),
                value=row[metric_name],  # validated by normal runner on q misses.
                metadata={
                    key: value
                    for key, value in row.items()
                    if key
                    not in {
                        *STOCK_METRICS_DIMENSION_COLUMNS,
                        metric_name,
                    }
                },
            )
        )

    if not metric_seen:
        return None

    return MetricTimeSeries.from_observations(
        observations,
        metric_name=metric_name,
        metadata={} if metadata is None else dict(metadata),
    )


def merge_stock_metrics_rows(
    row_sets: Sequence[Iterable[Mapping[str, Any]]],
) -> tuple[dict[str, Any], ...]:
    """Merge stockMetrics rows by persisted dimensions into wide metric rows.

    This helper lets a persister combine several metric-specific series into a
    single wide table keyed by ``date``, ``timeBucket``, ``bucketSize``, ``sym``,
    ``groupType``, and ``groupValue``.
    """

    merged: dict[tuple[Any, ...], dict[str, Any]] = {}
    for rows in row_sets:
        for raw_row in rows:
            row = dict(raw_row)
            dimension_key = tuple(row.get(column) for column in STOCK_METRICS_DIMENSION_COLUMNS)
            if dimension_key not in merged:
                merged[dimension_key] = {column: row.get(column) for column in STOCK_METRICS_DIMENSION_COLUMNS}
            merged[dimension_key].update(
                {column: value for column, value in row.items() if column not in STOCK_METRICS_DIMENSION_COLUMNS}
            )
    return tuple(merged.values())


def _stock_metric_time_bucket(value: time | str | None) -> str:
    if value is None:
        return "FULL_DAY"
    if isinstance(value, time):
        return f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}"
    return str(value)


def _stock_metric_group(group: Mapping[str, str]) -> tuple[str, str]:
    if not group:
        return "market", "ALL"

    if set(group) == {"sym"}:
        sym = group["sym"]
        return "symbol", sym

    non_symbol_items = tuple((key, value) for key, value in group.items() if key != "sym")
    if len(non_symbol_items) == 1:
        return non_symbol_items[0]

    return (
        "|".join(key for key, _ in non_symbol_items),
        "|".join(value for _, value in non_symbol_items),
    )


def _group_from_stock_metric_row(row: Mapping[str, Any]) -> dict[str, str]:
    group_type = str(row.get("groupType", "market"))
    group_value = str(row.get("groupValue", "ALL"))
    sym = str(row.get("sym", "ALL"))

    if group_type == "market" and group_value == "ALL":
        return {}
    if group_type == "symbol":
        return {"sym": group_value}

    group = {group_type: group_value}
    if sym != "ALL":
        group["sym"] = sym
    return group


def _coerce_stock_metric_date(value: Any, row_index: int) -> date:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            if "." in value and "-" not in value:
                year, month, day = value.split(".")
                return date(int(year), int(month), int(day))
            return date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"stockMetrics row {row_index} has invalid date value {value!r}") from exc
    raise ValueError(f"stockMetrics row {row_index} has unsupported date {value!r}")


def _stable_items(values: Mapping[str, object]) -> tuple[tuple[str, str], ...]:
    """Represent request parameters deterministically for cache keys."""

    return tuple(sorted((str(key), repr(value)) for key, value in values.items()))
