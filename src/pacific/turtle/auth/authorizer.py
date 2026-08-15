"""授权决策模型。

Turtle 全局授权决策模型，供各业务模块的访问策略端口和适配器使用。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AccessDecision:
    """一次访问策略评估的决策结果。

    Attributes:
        allowed: 是否允许访问。
        reason: 拒绝原因（允许时为 None）。
        obligations: 访问允许后必须履行的义务（如审计）。
        attributes: 附加属性（如限制条件）。
    """

    allowed: bool
    reason: str | None = None
    obligations: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)

