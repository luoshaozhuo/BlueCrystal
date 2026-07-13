"""Starfish core 使用的 simulator definition。

这些 dataclass 是 DB view、协议 adapter 与 manager 之间的稳定语言。它们
不包含 SQLAlchemy row、CLI 参数或 native runner 对象；具体外部来源由
adapter 映射到这些纯结构。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PointItemDefinition:
    """一个 simulator point item 的运行定义。

    Args:
        point_item_id: Whale point item 主键。
        point_identifier: 外部可读点位标识。
        semantic_name: 点位语义名称。
        data_type: Starfish 侧用于初始化和状态展示的数据类型。
        type_id: IEC104 等协议侧类型标识。
        io_address: 协议侧信息体地址或等价地址。
        initial_value: simulator 启动时的保守初始值。
        metadata: 协议或 view 特有的附加字段。
    """

    point_item_id: int
    point_identifier: str
    semantic_name: str
    data_type: str
    type_id: str
    io_address: int | str
    initial_value: Any = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskDefinition:
    """一个 connection 下的 Starfish 启动相关 task 定义。"""

    task_id: int
    task_identifier: str
    task_type: str
    task_status: str
    params: dict[str, Any] = field(default_factory=dict)
    point_item_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class ServerDefinition:
    """一个 connection 对应的 simulator server 定义。

    Args:
        connection_id: `vw_connection_object_full.connection_id`。
        name: server 展示名。
        protocol: 归一化协议名，当前首个实现为 `IEC104`。
        bind_host: simulator server 监听地址。
        bind_port: simulator server 监听端口。
        connection_params: DB view 提供的协议连接参数。
        tasks: 关联 task 定义。
        point_items: 关联 point item 定义。
        capabilities: 从 task/protocol 派生的能力声明。
        metadata: view 或资产层附加信息。
    """

    connection_id: int
    name: str
    protocol: str
    bind_host: str
    bind_port: int
    connection_params: dict[str, Any] = field(default_factory=dict)
    tasks: tuple[TaskDefinition, ...] = ()
    point_items: tuple[PointItemDefinition, ...] = ()
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ServerStatus:
    """manager 对外返回的单 server 状态快照。"""

    connection_id: int
    protocol: str
    status: str
    mode: str
    running: bool
    point_count: int
    reason: str | None = None
    detail: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "PointItemDefinition",
    "ServerDefinition",
    "ServerStatus",
    "TaskDefinition",
]
