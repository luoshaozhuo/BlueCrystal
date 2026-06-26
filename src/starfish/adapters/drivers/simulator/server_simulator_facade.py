"""starfish ServerSimulatorFacade —— 最小 in-memory stub 实现。

本模块提供协议 server 模拟的最小门面，用于验证 ServerPlan 加载、
点位读取和基本健康检查能力。当前采用 in-memory 存储方案，
不启动真实协议 server 进程。

当前实现状态：
- 已实现: start() / stop() / health() / load_points() / read() /
  update_values() / capabilities()
- NOT_IMPLEMENTED: write() / subscribe() / report()
  （调用时抛出 UnsupportedOperation）

禁止事项：
- 不得伪装真实协议 server 已完成。
- 不得将 stub 写成真实生产闭环。
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from starfish.domain import (
    StarfishServerMemberConfig,
    UnsupportedOperation,
)


class ServerSimulatorFacade:
    """协议 server 模拟门面 —— in-memory stub 实现。

    维护内存中的点位值存储，支持 read、health 和 capabilities 查询。
    write/subscribe/report 方法明确返回 NOT_IMPLEMENTED。

    不负责：真实协议 server 启动、网络 I/O、协议帧编解码。

    Attributes:
        _plan: 加载的 StarfishServerMemberConfig。
        _started: 是否已调用 start()。
        _values: 内存点位值存储 (point_id -> value)。
        _started_at: start() 调用时间。
    """

    def __init__(self) -> None:
        self._plan: StarfishServerMemberConfig | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None

    def connect(self) -> None:
        """完成 DriverPort 预连接；in-memory stub 无需外部连接。"""
        return None

    def start(self) -> None:
        """启动模拟门面。

        将内存状态置为已启动，记录启动时间。
        重复调用安全（幂等）。
        """
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止模拟门面。

        将内存状态置为已停止。不删除已加载的 plan 和 values，
        以便停止后仍可查询。
        重复调用安全（幂等）。
        """
        self._started = False

    def health(self) -> dict[str, Any]:
        """返回当前门面的可观测健康状态。

        健康状态包括：是否已启动、是否已加载 plan、
        当前点位数、能力声明和启动时间。

        Returns:
            包含 health 信息的 dict，结构如下::

                {
                    "status": "started" | "stopped",
                    "plan_loaded": bool,
                    "point_count": int,
                    "endpoint_count": int,
                    "capabilities": [...],
                    "started_at": "..." | null,
                    "synthetic": bool,
                }
        """
        return {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
        }

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """从 StarfishServerMemberConfig 加载点位定义和初始值。

        使用 plan.initial_values 填充内存存储。
        已存在的值会被覆盖。

        Args:
            plan: 已加载并校验的 StarfishServerMemberConfig 实例。
        """
        self._plan = plan
        self._values = dict(plan.initial_values)

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取当前点位值。

        可从内存存储读取 initial_values 或 update_values 后的当前值。
        如果 point_ids 为 None 则返回全部已加载点位。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        if point_ids is None:
            return dict(self._values)
        return {pid: self._values.get(pid) for pid in point_ids}

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值。

        **当前未实现。** 总是抛出 UnsupportedOperation。
        待后续轮次实现真实协议 write 能力。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "ServerSimulatorFacade.write 尚未实现，"
            "待后续轮次接入真实协议 write handler",
        )

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知。

        **当前未实现。** 总是抛出 UnsupportedOperation。
        待后续轮次实现 PUB/SUB 或 push 通知机制。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "ServerSimulatorFacade.subscribe 尚未实现，"
            "待后续轮次接入真实协议 subscribe handler",
        )

    def report(self) -> dict[str, Any]:
        """上报当前门面状态摘要。

        **当前未实现。** 待后续轮次实现结构化 report/telemetry。

        Returns:
            永远不会正常返回。

        Raises:
            UnsupportedOperation: 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "ServerSimulatorFacade.report 尚未实现，"
            "待后续轮次实现结构化 telemetry report",
        )

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新点位值到内存存储。

        用于模拟数据推进。更新后 read() 可读取新值。

        Args:
            values: point_id -> 新值 的 dict。
        """
        self._values.update(values)

    def capabilities(self) -> list[str]:
        """返回当前加载 plan 的能力声明列表。

        如果尚未 load_points，返回空列表。

        Returns:
            能力声明字符串列表，如 ["READ", "WRITE"]。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)


__all__ = ["ServerSimulatorFacade"]
