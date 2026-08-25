"""Opinionated observability integration runtime 的最小公共 API。

根包不导入 FastAPI 或 APScheduler。
"""

from .audit import audit_action
from .config import ObservabilityConfig, load_observability_config
from .context import (
    ObservationContext,
    bind_observation_context,
    get_observation_context,
)
from .logs import get_logger
from .runtime import (
    ObservabilityRuntime,
    create_observability,
    install_observability,
)

__all__ = [
    "ObservationContext",
    "ObservabilityConfig",
    "ObservabilityRuntime",
    "audit_action",
    "bind_observation_context",
    "create_observability",
    "get_observation_context",
    "get_logger",
    "install_observability",
    "load_observability_config",
]
