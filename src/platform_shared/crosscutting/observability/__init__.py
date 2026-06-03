"""Observability primitives for logging, metrics, and audit bridging."""

from platform_shared.crosscutting.observability.logging import (
    ErrorEvent,
    OperationLogFields,
    StructuredLogContext,
)
from platform_shared.crosscutting.observability.metrics import MetricsSinkPort

# SensitiveDataMasker 已迁入 platform_shared.security_primitives，
# 但为保持 observability 包完整性，暂不在此重新导出。
# 调用方如果同时需要 observability 和 masking，应分别 import。

__all__ = [
    "ErrorEvent",
    "MetricsSinkPort",
    "OperationLogFields",
    "StructuredLogContext",
]
