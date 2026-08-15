"""身份模型。

Turtle 全局身份模型，用于访问控制决策中的主体表达。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Principal:
    """认证后的系统或用户身份，代表一次操作的主体。

    Attributes:
        principal_id: 主体唯一标识。
        principal_type: 主体类型（service/user/system）。
        roles: 主体拥有的角色列表。
        attributes: 附加属性（如组织、部门）。
    """

    principal_id: str
    principal_type: str
    roles: tuple[str, ...] = ()
    attributes: dict[str, str] = field(default_factory=dict)

