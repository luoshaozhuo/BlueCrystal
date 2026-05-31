"""MQTT ServerSimulatorFacade 实现。"""

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
from tools.source_lab.protocols.common.simulators import MqttSimulator


def _encode_remaining_length(value: int) -> bytes:
    chunks: list[int] = []
    remaining = value
    while True:
        byte = remaining % 128
        remaining //= 128
        if remaining > 0:
            byte |= 0x80
        chunks.append(byte)
        if remaining == 0:
            break
    return bytes(chunks)


def _mqtt_connect_packet(client_id: str) -> bytes:
    payload = len(client_id).to_bytes(2, "big") + client_id.encode("utf-8")
    vh = b"\x00\x04MQTT\x04\x02\x00\x3c"
    return b"\x10" + _encode_remaining_length(len(vh) + len(payload)) + vh + payload


def _mqtt_subscribe_packet(packet_id: int, topic: str) -> bytes:
    topic_bytes = topic.encode("utf-8")
    payload = len(topic_bytes).to_bytes(2, "big") + topic_bytes + b"\x00"
    vh = packet_id.to_bytes(2, "big")
    return b"\x82" + _encode_remaining_length(len(vh) + len(payload)) + vh + payload


class MqttSimulatorFacade(BaseSimulatorFacade):
    """MQTT simulator facade。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: MqttSimulator | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "mqtt"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(subscribe=True, update_values=True)

    async def start(self) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            sim = MqttSimulator(self._source)
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
        return ReadSimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, message="read not implemented at facade level")

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        """真实 MQTT 订阅验证。"""
        if self._sim is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0,
            )
            try:
                writer.write(_mqtt_connect_packet("source-lab-facade-subscribe"))
                await writer.drain()
                connack = await asyncio.wait_for(reader.read(4), timeout=5.0)
                if len(connack) < 4 or connack[0] != 0x20 or connack[3] != 0x00:
                    return SimulatorResult(SimulatorStatus.ERROR, "MQTT CONNACK failed")

                topic = "source_lab/points"
                writer.write(_mqtt_subscribe_packet(1, topic))
                await writer.drain()
                suback = await asyncio.wait_for(reader.read(8), timeout=5.0)
                if not suback or suback[0] != 0x90:
                    return SimulatorResult(SimulatorStatus.ERROR, "MQTT SUBACK failed")

                return SimulatorResult(SimulatorStatus.OK, "MQTT subscribe verified")
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

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
