"""Seahorse runtime 快照契约。

快照输出稳定诊断视图，只包含标量、列表和 dict，不暴露 repository、
writer、scheduler 或其他 infrastructure 对象。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from pacific.seahorse.application.runtime.graph import RuntimeGraph
from pacific.seahorse.application.runtime.state import RuntimeState

SnapshotScalar = str | int | float | bool | None
"""快照诊断视图允许的标量值。"""

SnapshotValue = SnapshotScalar | list[SnapshotScalar] | dict[str, SnapshotScalar]
"""快照诊断视图允许的字段值。"""


@dataclass(slots=True)
class RuntimeSnapshot:
    """运行态快照。

    Attributes:
        runtime_id: 运行实例标识。
        captured_at: 快照时间。
        state: 快照时状态。
        graph: 快照时运行图。
        diagnostics: executor 或 runtime 组件提供的纯标量诊断字段。
    """

    runtime_id: str
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    state: RuntimeState = field(default_factory=RuntimeState)
    graph: RuntimeGraph = field(default_factory=RuntimeGraph)
    diagnostics: dict[str, SnapshotScalar] = field(default_factory=dict)

    def to_diagnostic_view(self) -> dict[str, SnapshotValue]:
        """输出稳定诊断视图。

        Returns:
            仅包含运行标识、状态、图节点/边数量、采集时间和可选诊断字段的 dict。
        """
        return {
            "runtime_id": self.runtime_id,
            "captured_at": self.captured_at.isoformat(),
            "phase": self.state.phase.value,
            "reason": self.state.reason,
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "node_ids": [node.node_id for node in self.graph.nodes],
            "diagnostics": self.diagnostics,
        }


__all__ = ["RuntimeSnapshot", "SnapshotScalar", "SnapshotValue"]
