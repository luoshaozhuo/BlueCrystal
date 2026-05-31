"""IEC101 ServerSimulatorFacade 实现。"""

from __future__ import annotations

import asyncio
import socket
import struct

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
from tools.source_lab.protocols.common.simulators import Iec101Simulator


class Iec101SimulatorFacade(BaseSimulatorFacade):
    """IEC101 simulator facade。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: Iec101Simulator | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "iec101"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            sim = Iec101Simulator(self._source)
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
            host = self._source.connection.host if self._source else "127.0.0.1"
            port = self._source.connection.port if self._source else 0
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            try:
                sock.connect((host, port))
                return SimulatorHealth(
                    SimulatorStatus.OK, running=True,
                    uptime_ms=_now_ms() - self._start_time_ms,
                )
            except OSError:
                return SimulatorHealth(
                    SimulatorStatus.UNAVAILABLE, running=False,
                    message="port unreachable",
                )
            finally:
                sock.close()
        except Exception as exc:
            return SimulatorHealth(SimulatorStatus.ERROR, message=str(exc))

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.OK)

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """真实 IEC101 CS101 协议读取。"""
        if self._sim is None:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING)
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        if port <= 0:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0,
            )
            try:
                # 发送 C_IC_NA_1 询问帧
                writer.write(b"\x10\x49\x00\x49\x16")
                await writer.drain()

                response = await asyncio.wait_for(reader.read(8192), timeout=10.0)

                values: dict[str, str | int | float | bool | None] = {}
                pos = 0
                while pos < len(response):
                    if response[pos] == 0x10:
                        # 固定帧 (5B): 0x10 CI ADDR CHK 0x16 — 跳过
                        pos += 5
                        continue
                    if response[pos] != 0x68:
                        pos += 1
                        continue

                    # 可变帧: 0x68 LEN LEN 0x68 CI ADDR ASDU... CHK 0x16
                    if pos + 3 >= len(response):
                        break
                    L = response[pos + 1]
                    # 帧边界 = pos + 3 + L + 1(0x16)
                    frame_end = pos + 3 + L + 1
                    if frame_end > len(response):
                        break

                    asdu_start = pos + 6  # 0x68 LEN LEN 0x68 CI ADDR = 6B，ASDU 从第7B开始
                    if asdu_start + 1 > len(response):
                        pos = frame_end
                        continue

                    type_id = response[asdu_start] if asdu_start < len(response) else 0
                    vsq = response[asdu_start + 1] if asdu_start + 1 < len(response) else 1
                    elements = vsq if vsq > 0 else 1

                    # ASDU 体 = TYPE(1) + VSQ(1) + COT(1) + OA(1) + CA(2) + BODY
                    body_start = asdu_start + 6

                    if type_id == 0x0D:  # M_ME_NC_1: IOA(3) + VALUE(4) + QDS(1) = 8B per element
                        entry_size = 8
                        for _i in range(elements):
                            if body_start + entry_size > len(response):
                                break
                            ioa = int.from_bytes(response[body_start:body_start + 3], "big")
                            fval = struct.unpack(">f", response[body_start + 3:body_start + 7])[0]
                            idx = ioa - 1
                            if 0 <= idx < len(self._source.points):
                                key = self._source.points[idx].key
                                values[key] = fval
                            body_start += entry_size
                    elif type_id == 0x01:  # M_SP_NA_1: IOA(3) + SIQ(1) = 4B per element
                        entry_size = 4
                        for _i in range(elements):
                            if body_start + entry_size > len(response):
                                break
                            ioa = int.from_bytes(response[body_start:body_start + 3], "big")
                            siq = response[body_start + 3]
                            idx = ioa - 1
                            if 0 <= idx < len(self._source.points):
                                key = self._source.points[idx].key
                                values[key] = bool(siq & 0x01)
                            body_start += entry_size

                    pos = frame_end

                status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
                return ReadSimulatorResult(status, values=values)
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def update_values(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            filtered = {k: v for k, v in values.items() if v is not None}
            self._sim.writes(filtered)
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))


def _now_ms() -> int:
    return int(asyncio.get_event_loop().time() * 1000)
