"""ServerSimulatorFacade — 统一的 Server Simulator Facade 契约。"""

from __future__ import annotations

from typing import Protocol

from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
)


class ServerSimulatorFacade(Protocol):
    """统一的 Server Simulator Facade 契约。

    每个协议实现此 Protocol，提供统一的生命周期/IO 接口。
    NOT_IMPLEMENTED 操作返回 SimulatorStatus.NOT_IMPLEMENTED，
    不抛出异常。
    """

    @property
    def protocol(self) -> str:
        """返回归一化的协议名，如 opcua / modbus_tcp / iec61850_mms。"""
        ...

    @property
    def capabilities(self) -> SimulatorCapabilities:
        """返回此 simulator 的能力矩阵。"""
        ...

    async def start(self) -> SimulatorResult:
        """启动 simulator 进程/线程。"""
        ...

    async def stop(self) -> SimulatorResult:
        """停止 simulator 进程/线程。"""
        ...

    async def health(self) -> SimulatorHealth:
        """检测 simulator 健康状态。"""
        ...

    async def load_points(
        self, points: list[SimulatorPoint],
    ) -> SimulatorResult:
        """加载点位配置。"""
        ...

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """读取指定点位的值。"""
        ...

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        """写入点位值。"""
        ...

    async def subscribe(
        self, point_keys: list[str],
    ) -> SimulatorResult:
        """订阅点位变化。"""
        ...

    async def report(self, point_keys: list[str]) -> SimulatorResult:
        """启用 Report 订阅（IEC61850 Report 专用）。"""
        ...

    async def update_values(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        """更新 simulator 内部值（不涉及协议写操作）。"""
        ...
