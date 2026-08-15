"""访问策略端口抽象。

Turtle 全局访问策略端口，定义主体对受保护资源的权限评估契约。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from pacific.turtle.auth.authorizer import AccessDecision
from pacific.turtle.auth.identity import Principal


@dataclass(frozen=True, slots=True)
class Permission:
    """对单个受保护资源的请求操作。

    Attributes:
        resource_type: 资源类型（如 source_connection、source_write）。
        action: 操作名称（如 read、write、subscribe）。
        resource_id: 资源标识（可选）。
        attributes: 附加属性。
    """

    resource_type: str
    action: str
    resource_id: str | None = None
    attributes: dict[str, str] = field(default_factory=dict)


class AccessPolicyPort(Protocol):
    """评估主体是否可以执行某项受权限保护的操作。

    各模块应实现此协议以提供模块特定访问策略。
    调用方通过此端口解耦具体策略实现。
    """

    def evaluate(self, principal: Principal, permission: Permission) -> AccessDecision:
        """返回针对请求操作的访问决策。

        Args:
            principal: 请求主体。
            permission: 请求的权限。

        Returns:
            AccessDecision: 包含允许/拒绝决定和拒绝原因的决策对象。
        """

