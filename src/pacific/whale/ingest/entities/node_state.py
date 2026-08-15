"""节点状态实体。

定义 ingest 节点的运行时状态，
包括节点 ID、心跳时间、运行状态等。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NodeState:
    """单个节点的最小状态快照。"""

    node_id: str
    value: object | None = None
