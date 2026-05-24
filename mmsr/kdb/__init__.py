"""kdb client, query loading, and metric runner APIs."""

from mmsr.kdb.client import KdbClient, KdbConfig
from mmsr.kdb.query_loader import (
    QueryTemplateError,
    load_q_template,
    render_template,
    template_parameters,
)
from mmsr.kdb.schema_contracts import (
    OutputSchemaContractError,
    QTemplateInputTableSchemaContract,
    QTemplateOutputSchemaContract,
    extract_result_columns,
    toxicity_reversion_input_schema_contracts,
    toxicity_reversion_output_schema_contract,
    validate_toxicity_reversion_input_schemas,
    validate_toxicity_reversion_output_schema,
)

from mmsr.kdb.runner import (
    KdbMetricRunner,
    KdbMetricRunnerError,
    MetricRunRequest,
    normalize_metric_result,
    template_for_metric,
)

__all__ = [
    "KdbClient",
    "KdbConfig",
    "KdbMetricRunner",
    "KdbMetricRunnerError",
    "MetricRunRequest",
    "OutputSchemaContractError",
    "QTemplateInputTableSchemaContract",
    "QTemplateOutputSchemaContract",
    "extract_result_columns",
    "toxicity_reversion_input_schema_contracts",
    "toxicity_reversion_output_schema_contract",
    "validate_toxicity_reversion_input_schemas",
    "validate_toxicity_reversion_output_schema",
    "QueryTemplateError",
    "load_q_template",
    "normalize_metric_result",
    "render_template",
    "template_for_metric",
    "template_parameters",
]
