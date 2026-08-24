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

    示例场景：
    - 服务启动时：
    - service_name = "billing-api"
    - service_instance_id = "pod-7" 或 "api-01"
    - source 通常还未绑定到请求/任务边界，更多是进程级初始化信息

    - HTTP 请求进入时：
    - request_id = "req-8f1f5c6d-37c8-4ef8-9c05-5d4ab61e2c90"
    - correlation_id = "corr-8b8a3d5a-6d94-4c93-9f1a-700fbd4a2523"
    - actor = "alice@example.com"
    - source = "http"

    - 调度器接到任务后：
    - job_id = "job-daily-report-2026-08-22"
    - execution_id = "exec-9b5a54bf-6b09-4d1e-b4ca-3fd19bb25145"
    - source = "scheduler"

    - Worker 执行时：
    - execution_id 继续沿用同一条任务执行链路
    - attributes["tenant_id"] = "tenant-42"
    - attributes["region"] = "cn-shanghai"

    说明：
    - service_name: 进程或服务的名称；通常在启动时设置，属于“服务级别”信息。
    - service_instance_id: 进程实例或部署实例的唯一标识；通常在启动时注入。
    - request_id: 单次 HTTP 请求唯一标识；在请求入口创建。
    - correlation_id: 跨请求、调度、Worker 的统一链路 ID；在入口创建并贯穿整个流程。
    - actor: 发起者；例如用户、系统账号、计划任务。
    - source: 事件来源边界，常见值为 "http"、"scheduler"、"worker"。
    - job_id: 调度任务 ID；在调度器创建任务时设置。
    - execution_id: 实际执行实例 ID；在任务真正执行时生成或绑定。
    - attributes: 应用级扩展字段；不属于通用核心字段时放这里。
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
