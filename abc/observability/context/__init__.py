"""关联上下文公共 API。"""

from uuid import uuid4

from .manager import (
    bind_observation_context,
    bind_request_context,
    bind_scheduler_context,
    bind_scheduler_execution_context,
    bind_worker_context,
    get_observation_context,
    initialize_runtime_context,
)
from .models import ObservationContext


def new_request_id() -> str:
    """生成不包含业务语义的请求关联 ID。"""
    return uuid4().hex


__all__ = [
    "ObservationContext",
    "bind_observation_context",
    "bind_request_context",
    "bind_scheduler_context",
    "bind_scheduler_execution_context",
    "bind_worker_context",
    "get_observation_context",
    "initialize_runtime_context",
    "new_request_id",
]
