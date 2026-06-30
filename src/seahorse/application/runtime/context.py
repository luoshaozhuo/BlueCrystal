"""Seahorse runtime 上下文骨架。

该上下文只保存未来运行时引擎装配所需的稳定标识和状态引用，不创建
scheduler、writer、driver 或外部连接。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from seahorse.application.runtime.graph import RuntimeGraph
from seahorse.application.runtime.state import RuntimeState
from seahorse.domain.runtime_contract import WritePlan


@dataclass(slots=True)
class RuntimeContext:
    """运行时上下文。

    Attributes:
        runtime_id: 运行实例标识。
        scenario_id: 关联场景标识。
        write_plan: 当前内存运行计划；tick 期间不得重新查询 Whale DB。
        graph: 由 write_plan 派生的执行拓扑。
        state: 当前运行状态快照。
        metadata: 非协议关键元数据；不得放入真实连接句柄。
    """

    runtime_id: str
    scenario_id: str = ""
    write_plan: WritePlan | None = None
    graph: RuntimeGraph = field(default_factory=RuntimeGraph)
    state: RuntimeState = field(default_factory=RuntimeState)
    metadata: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_write_plan(
        cls,
        *,
        runtime_id: str,
        write_plan: WritePlan,
        scenario_id: str = "",
    ) -> "RuntimeContext":
        """从内存 WritePlan 构建 RuntimeContext。

        Args:
            runtime_id: 运行实例标识。
            write_plan: 已构建的内存运行计划。
            scenario_id: 可选场景标识。

        Returns:
            携带拓扑图的 RuntimeContext。
        """
        return cls(
            runtime_id=runtime_id,
            scenario_id=scenario_id,
            write_plan=write_plan,
            graph=RuntimeGraph.from_write_plan(write_plan),
        )


__all__ = ["RuntimeContext"]
