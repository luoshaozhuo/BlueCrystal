"""数据分类标记。

Turtle 全局数据分类枚举，供审计和存储策略决策使用。
"""

from __future__ import annotations

from enum import StrEnum


class DataClassification(StrEnum):
    """运维数据简单分类标签。

    Attributes:
        PUBLIC: 公开数据。
        INTERNAL: 内部数据。
        CONFIDENTIAL: 机密数据。
        RESTRICTED: 受限数据。
    """

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

