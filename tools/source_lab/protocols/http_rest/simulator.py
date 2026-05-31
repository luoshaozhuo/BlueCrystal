"""HTTP REST ServerSimulatorFacade 实现。"""

from __future__ import annotations

import asyncio
import json
import socket
from urllib.request import build_opener, ProxyHandler

_no_proxy_opener = build_opener(ProxyHandler({}))

# 必须在全局 opener 创建后导入项目模块，确保 urllib 全局状态已初始化
from tools.source_lab.model import SimulatedSource  # noqa: E402
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade  # noqa: E402
from tools.source_lab.protocols.common.simulator_models import (  # noqa: E402
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)
from tools.source_lab.protocols.common.simulators import HttpRestSimulator  # noqa: E402


class HttpRestSimulatorFacade(BaseSimulatorFacade):
    """HTTP REST simulator facade。"""

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._sim: HttpRestSimulator | None = None
        self._start_time_ms: int = 0

    @property
    def protocol(self) -> str:
        return "http_rest"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(read=True, update_values=True)

    async def start(self) -> SimulatorResult:
        if self._sim is not None:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            sim = HttpRestSimulator(self._source)
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
                    message="endpoint unreachable",
                )
            finally:
                sock.close()
        except Exception as exc:
            return SimulatorHealth(SimulatorStatus.ERROR, message=str(exc))

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        return SimulatorResult(SimulatorStatus.OK)

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        """真实 HTTP GET 读取。"""
        if self._sim is None:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING)
        if self._source is None:
            return ReadSimulatorResult(SimulatorStatus.BAD_REQUEST, message="no source configured")
        host = self._source.connection.host or "127.0.0.1"
        port = int(self._source.connection.port or 0)
        try:
            from urllib.parse import urlencode
            query = urlencode({"points": ",".join(point_keys)})
            url = f"http://{host}:{port}/points?{query}"
            body: str = await asyncio.to_thread(
                lambda: _no_proxy_opener.open(url, timeout=5.0).read().decode("utf-8"),
            )
            payload = json.loads(body)
            values: dict[str, str | int | float | bool | None] = {}
            for entry in payload.get("values", []):
                key = entry.get("point", "")
                if key in point_keys:
                    values[key] = entry.get("value")
            status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
            return ReadSimulatorResult(status, values=values)
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
