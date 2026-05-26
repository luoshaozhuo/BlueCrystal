"""BaseSimulatorFacade — 默认 NOT_IMPLEMENTED 的基类。"""

from __future__ import annotations

from typing import Any

from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)


class BaseSimulatorFacade:
    """默认所有能力返回 NOT_IMPLEMENTED 的基类。

    子类只需 override 真正实现的能力即可。
    """

    @property
    def protocol(self) -> str:
        raise NotImplementedError

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities()

    async def start(self) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def stop(self) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def health(self) -> SimulatorHealth:
        return SimulatorHealth(SimulatorStatus.NOT_IMPLEMENTED)

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        return ReadSimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def report(self, point_keys: list[str]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)

    async def update_values(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED)
