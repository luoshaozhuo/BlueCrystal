"""IEC104 ServerSimulatorFacade 实现。

启动真实 C iec104_simulator_server 子进程（而非 Python TCP stub），
使 IEC104 原生 runner 可通过 interrogation 建立完整协议链路。
Python Iec104Simulator 只作为数据持有器，不绑定端口。
"""

from __future__ import annotations

import asyncio
import os
import socket
import subprocess
import threading
from pathlib import Path
from typing import Any

from tools.source_lab.access.runners.protocol import (
    ProtocolDiagnostics,
    start_stderr_drain_thread,
)
from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade
from tools.source_lab.protocols.common._interactive_runner import _resolve_executable
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)
from tools.source_lab.protocols.common.simulators import Iec104Simulator

_RawIec104ReadResult: Any = None
_Iec104SourceReader: Any = None


def _lazy_import_iec104_client() -> None:
    """延迟导入生产 IEC104 读取器，避免 import 失败。"""
    global _Iec104SourceReader, _RawIec104ReadResult  # noqa: PLW0603
    if _Iec104SourceReader is not None:
        return
    try:
        from whale.shared.source.iec104.reader import Iec104SourceReader as _R  # type: ignore[import-untyped]
        _Iec104SourceReader = _R
    except ImportError:
        _Iec104SourceReader = None  # type: ignore[assignment]

    try:
        from whale.shared.source.iec104.backends import RawIec104ReadResult as _RR  # type: ignore[import-untyped]
        _RawIec104ReadResult = _RR
    except ImportError:
        _RawIec104ReadResult = None  # type: ignore[assignment]


class Iec104SimulatorFacade(BaseSimulatorFacade):
    """IEC104 simulator facade。

    启动真实 C iec104_simulator_server 子进程实现完整 IEC104 协议链路，
    Python Iec104Simulator 只作为数据持有器供 update_values 使用。
    """

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: Iec104Simulator | None = None
        self._sim_proc: subprocess.Popen[str] | None = None
        self._sim_stderr_thread: threading.Thread | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "iec104"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(read=True, update_values=True)

    async def start(self) -> SimulatorResult:
        if self._sim_proc is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            port = int(self._source.connection.port or 0)
            if port <= 0:
                return SimulatorResult(SimulatorStatus.BAD_REQUEST, f"invalid port: {port}")

            # Keep Python stub as data holder (no port binding — don't call .start())
            self._sim = Iec104Simulator(self._source)

            # Start native C iec104_simulator_server
            sim_path = _resolve_executable("iec104_simulator_server")
            if not sim_path.exists():
                return SimulatorResult(
                    SimulatorStatus.NOT_IMPLEMENTED,
                    f"iec104 simulator server not compiled: {sim_path}",
                )

            proc = subprocess.Popen(
                [str(sim_path), str(port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
            assert proc.stdout is not None

            ready_line = await asyncio.to_thread(proc.stdout.readline)
            if ready_line.strip() != "READY":
                proc.terminate()
                return SimulatorResult(
                    SimulatorStatus.ERROR,
                    f"iec104 simulator server: expected READY, got {ready_line!r}",
                )

            self._sim_proc = proc
            self._sim_stderr_thread = start_stderr_drain_thread(
                proc.stderr, ProtocolDiagnostics()
            )
            self._start_time_ms = _now_ms()
            return SimulatorResult(SimulatorStatus.OK)
        except Exception as exc:
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        # Stop C simulator
        if self._sim_proc is not None:
            proc = self._sim_proc
            self._sim_proc = None
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass
        if self._sim_stderr_thread is not None:
            self._sim_stderr_thread.join(timeout=1.0)
            self._sim_stderr_thread = None
        # Stop Python data holder via base
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
        """真实 IEC104 协议读取。通过生产 Iec104SourceReader interrogation。"""
        _lazy_import_iec104_client()
        if _Iec104SourceReader is None:
            return ReadSimulatorResult(
                SimulatorStatus.NOT_IMPLEMENTED,
                message="IEC104 production client not available",
            )
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, message="no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        if port <= 0:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, message=f"invalid port: {port}")

        # 从 point_keys 解析 IOA (do_name)
        points_by_key = {p.key: p for p in self._source.points}
        ioa_list: list[int] = []
        key_to_ioa: dict[str, int] = {}
        for key in point_keys:
            point = points_by_key.get(key)
            if point is None:
                continue
            try:
                ioa = int(point.do_name)
            except ValueError:
                continue
            ioa_list.append(ioa)
            key_to_ioa[key] = ioa
        if not ioa_list:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, message="no valid IOA addresses found")

        try:
            reader = _Iec104SourceReader(host, port, common_addr=1)
            async with reader:
                result = await reader.read(ioa_list)

            if not result.ok:
                return ReadSimulatorResult(
                    SimulatorStatus.ERROR,
                    message=result.error_reason or result.exception or "interrogation failed",
                )
            # values: dict[int, tuple[str, str]] — IOA -> (type_tag, value_str)
            raw_vals: dict[int, tuple[str, str]] = result.values
            values: dict[str, str | int | float | bool | None] = {}
            for key, ioa in key_to_ioa.items():
                entry = raw_vals.get(ioa)
                if entry is not None:
                    _type_tag, val_str = entry
                    # 尝试解析为数值
                    try:
                        if "." in val_str:
                            values[key] = float(val_str)
                        else:
                            values[key] = int(val_str)
                    except ValueError:
                        values[key] = val_str
            status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
            return ReadSimulatorResult(status, values=values, message="")
        except Exception as exc:
            return ReadSimulatorResult(SimulatorStatus.ERROR, message=str(exc))

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
