"""Seahorse runtime 图契约。

图结构用于表达 WritePlan 下 server、endpoint、field 与 data source
之间的拓扑关系；本轮不调度真实任务、不执行数据流。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pacific.seahorse.domain.runtime_contract import WritePlan


class RuntimeNodeKind(StrEnum):
    """运行图节点类型。"""

    PLAN = "plan"
    SERVER = "server"
    ENDPOINT = "endpoint"
    FIELD = "field"
    DATA_SOURCE = "data_source"


@dataclass(frozen=True, slots=True)
class RuntimeNode:
    """运行图节点描述。

    Attributes:
        node_id: 节点唯一标识。
        node_type: 节点类型，例如 data_source、strategy、writer。
    """

    node_id: str
    node_type: RuntimeNodeKind
    label: str = ""


@dataclass(slots=True)
class RuntimeGraph:
    """运行图纯数据容器。

    Attributes:
        nodes: 节点列表。
        edges: 有向边列表，元素为 (source_id, target_id)。
    """

    nodes: list[RuntimeNode] = field(default_factory=list)
    edges: list[tuple[str, str]] = field(default_factory=list)

    @classmethod
    def from_write_plan(cls, plan: WritePlan) -> "RuntimeGraph":
        """从 WritePlan 构建纯内存执行拓扑。

        Args:
            plan: 内存运行计划。

        Returns:
            只包含稳定标识的 RuntimeGraph，不包含基础设施对象。
        """
        nodes: list[RuntimeNode] = [
            RuntimeNode(
                node_id=plan.plan_id.value,
                node_type=RuntimeNodeKind.PLAN,
                label=plan.plan_id.value,
            )
        ]
        edges: list[tuple[str, str]] = []
        for source in plan.data_sources:
            source_node_id = f"source:{source.source_id}"
            nodes.append(
                RuntimeNode(
                    node_id=source_node_id,
                    node_type=RuntimeNodeKind.DATA_SOURCE,
                    label=source.kind.value,
                )
            )
        for server in plan.servers:
            server_node_id = f"server:{server.server_id}"
            nodes.append(
                RuntimeNode(
                    node_id=server_node_id,
                    node_type=RuntimeNodeKind.SERVER,
                    label=server.server_id,
                )
            )
            edges.append((plan.plan_id.value, server_node_id))
            for endpoint in server.endpoints:
                endpoint_node_id = f"{server_node_id}:endpoint:{endpoint.endpoint_id}"
                nodes.append(
                    RuntimeNode(
                        node_id=endpoint_node_id,
                        node_type=RuntimeNodeKind.ENDPOINT,
                        label=endpoint.protocol,
                    )
                )
                edges.append((server_node_id, endpoint_node_id))
                for field_binding in endpoint.fields:
                    field_node_id = f"{endpoint_node_id}:field:{field_binding.field_id}"
                    nodes.append(
                        RuntimeNode(
                            node_id=field_node_id,
                            node_type=RuntimeNodeKind.FIELD,
                            label=field_binding.target.stable_key(),
                        )
                    )
                    edges.append((endpoint_node_id, field_node_id))
                    edges.append((f"source:{field_binding.source_id}", field_node_id))
        return cls(nodes=nodes, edges=edges)


__all__ = ["RuntimeGraph", "RuntimeNode", "RuntimeNodeKind"]
