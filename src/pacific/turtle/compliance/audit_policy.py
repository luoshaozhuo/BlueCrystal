"""审计事件模型和 sink 端口。

Turtle 全局审计事件模型和审计 sink 契约，供各模块的审计适配器实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from pacific.turtle.compliance.data_classification import DataClassification


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """一次审计级别的运维事件。

    Attributes:
        event_name: 事件名称。
        observed_at: 事件发生时间。
        classification: 数据分类级别。
        actor_id: 操作主体标识（可选）。
        resource_id: 资源标识（可选）。
        outcome: 操作结果（success/failure）。
        attributes: 附加属性。
    """

    event_name: str
    observed_at: datetime
    classification: DataClassification
    actor_id: str | None = None
    resource_id: str | None = None
    outcome: str = "success"
    attributes: dict[str, str] = field(default_factory=dict)


class AuditEventSinkPort(Protocol):
    """消费审计事件，使调用方无需绑定到特定审计后端。

    各模块可实现此协议接入外部 SIEM、数据库审计表或文件审计日志。
    """

    def emit(self, event: AuditEvent) -> None:
        """持久化或转发一条审计事件。

        Args:
            event: 审计事件对象。

        Notes:
            - 实现应为 best-effort，emit 失败不得阻断主业务链路。
            - 调用方应通过 _emit_audit_best_effort 包装 emit 调用。
        """

