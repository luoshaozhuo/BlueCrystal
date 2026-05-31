"""OPC UA ServerSimulatorFacade 实现。"""

from __future__ import annotations

import asyncio
import socket

from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)
from tools.source_lab.protocols.opcua.open62541_source_simulator import (
    Open62541SourceSimulator,
)


class _NoopHandler:
    """占位 OPC UA 订阅 handler，用于验证 create_subscription 可用性。

    不处理实际数据变更通知，仅满足 asyncua 类型签名要求。
    """

    async def datachange_notification(self, node: object, val: object, data: object) -> None:
        pass


class OpcUaSimulatorFacade(BaseSimulatorFacade):
    """OPC UA simulator facade，包装 Open62541SourceSimulator。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: Open62541SourceSimulator | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "opcua"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            write=True,
            subscribe=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            sim = Open62541SourceSimulator(self._source)
            await asyncio.to_thread(sim.start)
            self._sim = sim
            self._start_time_ms = _now_ms()
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            await asyncio.to_thread(self._sim.stop)
            self._sim = None
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def health(self) -> SimulatorHealth:
        if self._sim is None:
            return SimulatorHealth(SimulatorStatus.NOT_RUNNING)
        try:
            endpoint = self._sim.endpoint
            host_port = endpoint.replace("opc.tcp://", "")
            host, _, port_str = host_port.rpartition(":")
            port = int(port_str) if port_str.isdigit() else 0
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            try:
                sock.connect((host, port))
                return SimulatorHealth(
                    SimulatorStatus.OK,
                    running=True,
                    uptime_ms=_now_ms() - self._start_time_ms,
                )
            except OSError:
                return SimulatorHealth(
                    SimulatorStatus.UNAVAILABLE, running=False,
                    message="endpoint unreachable",
                )
            finally:
                sock.close()
        except Exception as exc:
            return SimulatorHealth(SimulatorStatus.ERROR, message=str(exc))

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.OK)

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """真实 OPC UA 协议读取。"""
        if self._sim is None:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            from whale.shared.source.models import SourceConnectionProfile
            from whale.shared.source.opcua.reader import OpcUaSourceReader

            endpoint = self._sim.endpoint
            conn = SourceConnectionProfile(endpoint=endpoint, timeout_seconds=10.0)
            reader = OpcUaSourceReader(conn)
            async with reader:
                plan = reader.prepare_read(list(point_keys))
                result = await reader.read_prepared_raw(plan)

            if not result.ok:
                return ReadSimulatorResult(
                    SimulatorStatus.ERROR,
                    message=result.error_reason or result.exception or "read failed",
                )
            values: dict[str, str | int | float | bool | None] = {}
            for i, key in enumerate(point_keys):
                if i < len(result.data_values):
                    v = result.data_values[i]
                    if v is not None:
                        values[key] = v  # type: ignore[assignment]
            return ReadSimulatorResult(SimulatorStatus.OK, values=values)
        except ImportError as exc:
            return ReadSimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, f"production client not available: {exc}")
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            filtered = {k: v for k, v in values.items() if v is not None}
            await asyncio.to_thread(self._sim.writes, filtered)
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        """真实 OPC UA 订阅验证。"""
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")

        try:
            from tools.source_lab.protocols.opcua.address_space import logical_path

            endpoint = self._sim.endpoint
            node_ids: list[str] = []
            for point in self._source.points:
                if point.key in point_keys or not point_keys:
                    path = logical_path(self._source.connection, point)
                    if path.startswith("ns="):
                        node_ids.append(path)
                    else:
                        node_ids.append(f"ns=2;s={path}")

            if not node_ids:
                node_ids.append("ns=2;s=WPPD1.TotW")

            from asyncua import Client

            client = Client(endpoint, timeout=10)
            await client.connect()

            try:
                # asyncua create_subscription 第二个参数不接受 None，
                # 使用占位 _NoopHandler 创建初始订阅以验证功能可用
                sub = await client.create_subscription(500, _NoopHandler())
                if sub is None:
                    return SimulatorResult(SimulatorStatus.ERROR, "failed to create subscription")

                received_event = asyncio.Event()
                received_values: dict[str, object] = {}

                class _Handler:
                    async def datachange_notification(self, node, val, data):
                        node_str = str(node)
                        received_values[node_str] = val
                        received_event.set()

                handler = _Handler()
                await sub.delete()
                sub = await client.create_subscription(500, handler)

                for nid in node_ids[:3]:
                    node = client.get_node(nid)
                    await sub.subscribe_data_change(node)

                try:
                    await asyncio.wait_for(received_event.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    await sub.delete()
                    return SimulatorResult(
                        SimulatorStatus.PARTIAL_SUCCESS,
                        "subscription created but no data change received within timeout",
                    )

                await sub.delete()
                return SimulatorResult(
                    SimulatorStatus.OK,
                    f"OPC UA subscription verified with {len(received_values)} data changes",
                )
            except Exception as exc:
                return SimulatorResult(SimulatorStatus.ERROR, str(exc))
            finally:
                await client.disconnect()
        except ImportError as exc:
            return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, f"asyncua not available: {exc}")
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def update_values(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            filtered = {k: v for k, v in values.items() if v is not None}
            await asyncio.to_thread(self._sim.writes, filtered)
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))


def _now_ms() -> int:
    return int(asyncio.get_event_loop().time() * 1000)
