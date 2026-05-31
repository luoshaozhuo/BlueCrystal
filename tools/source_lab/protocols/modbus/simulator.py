"""Modbus ServerSimulatorFacade 实现（含 modbus_tcp / modbus_rtu）。"""

from __future__ import annotations

import asyncio
import socket
import struct

from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade
from tools.source_lab.protocols.common._interactive_runner import (
    NativeInteractiveRunner,
)
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)
from tools.source_lab.protocols.common.simulators import (
    ModbusRtuSimulator,
    ModbusTcpSimulator,
)


def _crc16(data: bytes) -> int:
    """标准 Modbus CRC-16。"""
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc & 0xFFFF


class _BaseModbusFacade(BaseSimulatorFacade):
    """Modbus 通用基类。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: ModbusTcpSimulator | ModbusRtuSimulator | None = None
        self._start_time_ms: int = 0

    async def _start_sim(self, sim_cls: type) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            sim = sim_cls(self._source)
            await asyncio.to_thread(sim.start)
            self._sim = sim  # type: ignore[assignment]
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
        return ReadSimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, "read not implemented at facade level")

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

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, "write not implemented at facade level")


class ModbusTcpSimulatorFacade(_BaseModbusFacade):
    """Modbus TCP simulator facade with real write via native runner."""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        super().__init__(source)
        self._client: NativeInteractiveRunner | None = None

    @property
    def protocol(self) -> str:
        return "modbus_tcp"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            write=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            # 1. Start Python stub as Modbus TCP server
            sim = ModbusTcpSimulator(self._source)
            await asyncio.to_thread(sim.start)
            self._sim = sim
            self._start_time_ms = _now_ms()

            # 2. Start native interactive runner for real Modbus write
            runner = NativeInteractiveRunner("modbus_tcp_polling_runner")
            try:
                await asyncio.to_thread(runner.start)
            except RuntimeError:
                # Native runner not compiled — continue without real write
                self._client = None
                return SimulatorResult(SimulatorStatus.OK)
            self._client = runner
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        if self._client is not None:
            try:
                await asyncio.to_thread(self._client.stop)
            except Exception:
                pass
            self._client = None
        return await super().stop()

    async def write(
        self, values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if self._client is None or not self._client.running:
            return SimulatorResult(SimulatorStatus.NOT_IMPLEMENTED, "native write runner not available")
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        try:
            host = self._source.connection.host or "127.0.0.1"
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            unit_id = 1  # default Modbus unit ID
            points_by_key = {p.key: p for p in self._source.points}
            errors: list[str] = []

            for key, val in values.items():
                if val is None:
                    continue
                point = points_by_key.get(key)
                if point is None:
                    errors.append(f"point not found: {key}")
                    continue

                # Use do_name as register address
                try:
                    reg_addr = int(point.do_name)
                except ValueError:
                    errors.append(f"invalid reg_addr for {key}: {point.do_name}")
                    continue

                dt = point.data_type.upper()
                if dt == "BOOLEAN":
                    vt = "bool"
                    val_str = "true" if val else "false"
                else:
                    vt = "uint16"
                    val_str = str(int(val) & 0xFFFF)

                cmd = f"WRITE\t{key}\t{host}\t{port}\t{unit_id}\t{reg_addr}\t{vt}\t{val_str}"
                response = await asyncio.to_thread(self._client.command, cmd)
                if "\tok=1\t" not in response:
                    errors.append(f"write failed for {key}: {response}")

            status = SimulatorStatus.PARTIAL_SUCCESS if errors else SimulatorStatus.OK
            return SimulatorResult(status, "; ".join(errors) if errors else "")
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """真实 Modbus FC03 读取。优先使用 native runner，fallback 到 raw TCP socket。"""
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        if port <= 0:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

        # 从 point_keys 解析寄存器地址
        points_by_key = {p.key: p for p in self._source.points}
        reg_addrs: list[int] = []
        key_to_addr: dict[str, int] = {}
        for key in point_keys:
            point = points_by_key.get(key)
            if point is None:
                continue
            try:
                addr = int(point.do_name)
            except ValueError:
                continue
            reg_addrs.append(addr)
            key_to_addr[key] = addr

        if not reg_addrs:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no valid register addresses found")

        unit_id = 1
        min_addr = min(reg_addrs)
        max_addr = max(reg_addrs)
        count = max_addr - min_addr + 1

        if count > 125:
            return ReadSimulatorResult(
                SimulatorStatus.BAD_REQUEST,
                f"address range too wide: {count} registers (max 125)",
            )

        # 方式 1：通过 native runner READ 命令读取
        if self._client is not None and self._client.running:
            try:
                cmd = f"READ\tread1\t{host}\t{port}\t{unit_id}\t{min_addr}\t{count}"
                response = await asyncio.to_thread(self._client.command, cmd)
                # READ_RESULT\tread1\tok=1\tOK\tval0\tval1\t...
                parts = response.split("\t")
                if len(parts) >= 4 and parts[0] == "READ_RESULT" and parts[2] == "ok=1":
                    raw_values: list[int] = []
                    for v in parts[4:]:
                        try:
                            raw_values.append(int(v))
                        except ValueError:
                            break
                    values: dict[str, str | int | float | bool | None] = {}
                    for key, addr in key_to_addr.items():
                        idx = addr - min_addr
                        if 0 <= idx < len(raw_values):
                            values[key] = raw_values[idx]
                    status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
                    return ReadSimulatorResult(status, values=values)
            except Exception:
                pass

        # 方式 2：raw TCP socket FC03 fallback
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0
            )
            try:
                req_len = 6
                mbap = struct.pack(">HHHB", 1, 0, req_len, unit_id)
                pdu = struct.pack(">BHH", 0x03, min_addr, count)
                writer.write(mbap + pdu)
                await writer.drain()

                resp = await asyncio.wait_for(reader.read(1024), timeout=5.0)
                if len(resp) < 9:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, message=f"short FC03 response: {len(resp)} bytes"
                    )
                fc = resp[7]
                if fc == 0x83:
                    exc_code = resp[8] if len(resp) > 8 else 0
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, message=f"FC03 exception: code={exc_code}"
                    )
                if fc != 0x03:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, message=f"unexpected FC: 0x{fc:02x}"
                    )
                _byte_count = resp[8]
                raw_vals: list[int] = []
                for i in range(count):
                    off = 9 + i * 2
                    if off + 2 > len(resp):
                        break
                    raw_vals.append(struct.unpack(">H", resp[off:off+2])[0])

                values = {}
                for key, addr in key_to_addr.items():
                    idx = addr - min_addr
                    if 0 <= idx < len(raw_vals):
                        values[key] = raw_vals[idx]
                status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
                return ReadSimulatorResult(status, values=values, message="")
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, str(exc))


class ModbusRtuSimulatorFacade(_BaseModbusFacade):
    """Modbus RTU simulator facade with real read via FC03 RTU over TCP。"""

    @property
    def protocol(self) -> str:
        return "modbus_rtu"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        return await self._start_sim(ModbusRtuSimulator)

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """真实 Modbus FC03 RTU 读取（TCP gateway 模式）。"""
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        if port <= 0:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

        points_by_key = {p.key: p for p in self._source.points}
        reg_addrs: list[int] = []
        key_to_addr: dict[str, int] = {}
        for key in point_keys:
            point = points_by_key.get(key)
            if point is None:
                continue
            try:
                addr = int(point.do_name)
            except ValueError:
                continue
            reg_addrs.append(addr)
            key_to_addr[key] = addr

        if not reg_addrs:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, "no valid register addresses")

        unit_id = 1
        min_addr = min(reg_addrs)
        max_addr = max(reg_addrs)
        count = max_addr - min_addr + 1
        if count > 125:
            return ReadSimulatorResult(
                SimulatorStatus.BAD_REQUEST,
                f"address range too wide: {count} registers (max 125)",
            )

        # 构建 FC03 RTU 帧
        pdu = struct.pack(">BBHH", unit_id, 0x03, min_addr, count)
        crc = _crc16(pdu)
        frame = pdu + struct.pack("<H", crc)

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=5.0,
            )
            try:
                writer.write(frame)
                await writer.drain()

                resp = await asyncio.wait_for(reader.read(1024), timeout=5.0)
                if len(resp) < 5:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, f"short FC03 response: {len(resp)} bytes",
                    )
                if resp[1] & 0x80:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, f"FC03 exception: code={resp[2]}",
                    )
                if resp[1] != 0x03:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR, f"unexpected FC: 0x{resp[1]:02x}",
                    )

                _byte_count = resp[2]
                values: dict[str, str | int | float | bool | None] = {}
                for key, addr in key_to_addr.items():
                    idx = addr - min_addr
                    off = 3 + idx * 2
                    if off + 2 <= len(resp):
                        values[key] = struct.unpack(">H", resp[off:off+2])[0]

                status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
                return ReadSimulatorResult(status, values=values)
            finally:
                writer.close()
                await writer.wait_closed()
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, str(exc))


def _now_ms() -> int:
    return int(asyncio.get_event_loop().time() * 1000)
