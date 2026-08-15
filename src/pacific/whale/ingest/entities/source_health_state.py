"""数据源健康状态实体。

定义数据源的健康评估指标和状态。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SourceHealthState:
    """单个数据源的最小健康状态。"""

    source_id: str
    status: str
