"""跨 HTTP、调度器与 Worker 传播的通用关联上下文。"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ObservationContext:
    """一次观测作用域中的可选关联字段。

    字段不假设固定链路起点。``attributes`` 用于承载应用命名空间字段，
    避免把 task 等领域概念固化到通用核心。
    """

    service_name: str | None = None
    service_instance_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    actor: str | None = None
    source: str | None = None
    job_id: str | None = None
    execution_id: str | None = None
    attributes: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        """冻结扩展属性的浅表副本，阻止调用方事后修改上下文。"""
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))
