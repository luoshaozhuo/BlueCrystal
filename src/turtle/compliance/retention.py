"""数据保留策略模型。

Turtle 全局数据保留策略模型，供各模块引用。
"""

from __future__ import annotations

from dataclasses import dataclass

from turtle.compliance.data_classification import DataClassification


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    """单条数据流或事件类别的保留规则。

    Attributes:
        classification: 数据分类级别。
        retention_days: 保留天数。
        purge_required: 到期后是否必须清除（vs 可归档）。
    """

    classification: DataClassification
    retention_days: int
    purge_required: bool = False

