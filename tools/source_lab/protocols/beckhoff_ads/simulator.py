"""Beckhoff ADS ServerSimulatorFacade 实现。

当前提供两种 backend：
1. `backend_kind=in_process` — 进程内 lightweight ADS simulator，协议证据等级 L3；
2. `backend_kind=beckhoff_dotnet` — 真实 .NET virtual ADS server + native AdsLib
   客户端 read/write/readback 闭环，协议证据等级 L4+（需环境满足）。
"""

from __future__ import annotations

import asyncio
import logging

from tools.source_lab.model import SimulatedSource
from tools.source_lab.protocols.beckhoff_ads.runtime import (
    ADS_SIMULATOR_REGISTRY,
    AdsRuntimeUnavailableError,
    AdsValidationError,
)
from tools.source_lab.protocols.common._base_facade import BaseSimulatorFacade
from tools.source_lab.protocols.common.simulator_models import (
    ReadSimulatorResult,
    SimulatorCapabilities,
    SimulatorHealth,
    SimulatorPoint,
    SimulatorResult,
    SimulatorStatus,
)


class BeckhoffAdsSimulatorFacade(BaseSimulatorFacade):
    """source_lab 工具层 ADS simulator facade。

    当前实现是进程内 simulator + Python lightweight client/readback 闭环。
    它只服务 source_lab 验证，不代表 shared_source production ADS backend，
    也不等于 Beckhoff.TwinCAT.Ads.Server / AdsLib native 的真实协议证据。
    """

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._running = False
        self._start_time_ms = 0

    @property
    def protocol(self) -> str:
        return "beckhoff_ads"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            write=True,
            update_values=True,
        )

    async def start(self) -> SimulatorResult:
        if self._running:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        try:
            ADS_SIMULATOR_REGISTRY.register(self._source)
            self._running = True
            self._start_time_ms = _now_ms()
            return SimulatorResult(SimulatorStatus.OK)
        except AdsValidationError as exc:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - unexpected path
            return SimulatorResult(SimulatorStatus.ERROR, str(exc))

    async def stop(self) -> SimulatorResult:
        if not self._running or self._source is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        ADS_SIMULATOR_REGISTRY.unregister(self._source)
        self._running = False
        return SimulatorResult(SimulatorStatus.OK)

    async def health(self) -> SimulatorHealth:
        if not self._running or self._source is None:
            return SimulatorHealth(SimulatorStatus.NOT_RUNNING)
        try:
            server = ADS_SIMULATOR_REGISTRY.get(self._source)
            return SimulatorHealth(
                SimulatorStatus.OK,
                running=True,
                points_count=len(server.point_states_by_key),
                uptime_ms=_now_ms() - self._start_time_ms,
            )
        except AdsRuntimeUnavailableError as exc:
            return SimulatorHealth(SimulatorStatus.UNAVAILABLE, running=False, message=str(exc))

    async def load_points(self, points: list[SimulatorPoint]) -> SimulatorResult:
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        if not self._source.points:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "source has no ADS points")
        try:
            # 通过 register 前置校验复用点位合法性检查，但不保留注册状态。
            ADS_SIMULATOR_REGISTRY.register(self._source)
            ADS_SIMULATOR_REGISTRY.unregister(self._source)
            return SimulatorResult(SimulatorStatus.OK)
        except AdsValidationError as exc:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, str(exc))

    async def read(self, point_keys: list[str]) -> ReadSimulatorResult:
        if not self._running or self._source is None:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            values = ADS_SIMULATOR_REGISTRY.read(self._source, point_keys)
            status = SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS
            return ReadSimulatorResult(status, values=values)
        except AdsRuntimeUnavailableError as exc:
            return ReadSimulatorResult(SimulatorStatus.UNAVAILABLE, message=str(exc))

    async def write(
        self,
        values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if not self._running or self._source is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            readback, errors = ADS_SIMULATOR_REGISTRY.write(self._source, values)
            if errors:
                status = SimulatorStatus.PARTIAL_SUCCESS if readback else SimulatorStatus.BAD_REQUEST
                return SimulatorResult(status, "; ".join(errors))
            return SimulatorResult(SimulatorStatus.OK)
        except AdsRuntimeUnavailableError as exc:
            return SimulatorResult(SimulatorStatus.UNAVAILABLE, str(exc))

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        return SimulatorResult(
            SimulatorStatus.NOT_IMPLEMENTED,
            "Beckhoff ADS notification path is not implemented in source_lab simulator",
        )

    async def report(self, point_keys: list[str]) -> SimulatorResult:
        return SimulatorResult(
            SimulatorStatus.NOT_IMPLEMENTED,
            "Beckhoff ADS report path is not implemented in source_lab simulator",
        )

    async def update_values(
        self,
        values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        if not self._running or self._source is None:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)
        try:
            errors = ADS_SIMULATOR_REGISTRY.update_values(self._source, values)
            if errors:
                return SimulatorResult(SimulatorStatus.PARTIAL_SUCCESS, "; ".join(errors))
            return SimulatorResult(SimulatorStatus.OK)
        except AdsRuntimeUnavailableError as exc:
            return SimulatorResult(SimulatorStatus.UNAVAILABLE, str(exc))


def _now_ms() -> int:
    return int(asyncio.get_event_loop().time() * 1000)


_log = logging.getLogger(__name__)


class BeckhoffDotnetAdsSimulatorFacade(BaseSimulatorFacade):
    """基于真实 .NET virtual ADS server + AdsLib 客户端的 simulator facade。

    此 facade 用于 `backend_kind=beckhoff_dotnet`，提供 L4+ 真实协议证据。
    它与 in_process facade 的区别：
    - 服务端：通过 dotnet run 启动 Beckhoff AdsServer 示例项目；
    - 客户端：优先使用 AdsLib native runner（PyAdsClient 编排）；
    - 读写闭环：read -> write -> readback 完整流程；
    - 只有在真实 virtual server 启动成功且 client read/write/readback 均
      成功时，才设置 protocol_evidence=true。

    环境不足时（缺 dotnet、缺 AdsServer 项目、缺 AdsLib binary），操作
    返回 UNAVAILABLE，不制造假通过。
    """

    def __init__(self, source: SimulatedSource | None = None) -> None:
        self._source = source
        self._running = False
        self._start_time_ms = 0
        self._server: object | None = None  # VirtualAdsServerLifecycle | None
        self._client: object | None = None  # PyAdsClient | None
        self._detected_pid: int = 0
        self._protocol_evidence = False

    @property
    def protocol(self) -> str:
        return "beckhoff_ads"

    @property
    def capabilities(self) -> SimulatorCapabilities:
        return SimulatorCapabilities(
            read=True,
            write=True,
            update_values=True,
        )

    @property
    def protocol_evidence(self) -> bool:
        """返回当前 session 是否获得了真实协议证据。

        只有在真实 .NET server 启动成功且至少完成一次
        client read/write/readback 闭环后才为 True。
        """
        return self._protocol_evidence

    async def start(self) -> SimulatorResult:
        """启动 .NET virtual ADS server 子进程。

        执行以下步骤：
        1. 探测 dotnet 环境（probe_dotnet_environment）；
        2. 如环境不满足，返回 UNAVAILABLE；
        3. 创建 VirtualAdsServerLifecycle 实例；
        4. 调用 server.start() 编译并启动；
        5. 启动成功后设置运行状态。

        Returns:
            SimulatorResult。
        """
        if self._running:
            return SimulatorResult(SimulatorStatus.ALREADY_RUNNING)

        from tools.source_lab.protocols.beckhoff_ads.dotnet_virtual_server import (
            create_virtual_ads_server,
            probe_dotnet_environment,
        )

        # 解析连接参数
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")

        ams_net_id = str(self._source.connection.params.get("ams_net_id", "5.32.160.1.1.1"))
        ads_port = int(self._source.connection.params.get("ads_server_port", 851))
        router_port = int(self._source.connection.port or 0)

        # 环境探测
        probe = probe_dotnet_environment()
        if not probe.overall_environment_ready:
            return SimulatorResult(
                SimulatorStatus.UNAVAILABLE,
                "ADS .NET virtual server environment not ready: "
                + "; ".join(probe.missing_components),
            )

        # 创建并启动 server
        server = create_virtual_ads_server(
            ams_net_id=ams_net_id,
            ads_port=ads_port,
            router_port=router_port if router_port > 0 else 48898,
        )

        start_result = server.start()
        if not start_result.success:
            return SimulatorResult(
                SimulatorStatus.UNAVAILABLE,
                f"Failed to start .NET ADS virtual server: {start_result.message}",
            )

        self._server = server
        self._detected_pid = start_result.pid
        self._running = True
        self._start_time_ms = _now_ms()

        # 创建 client
        from tools.source_lab.protocols.beckhoff_ads.ads_client import PyAdsClient
        try:
            self._client = PyAdsClient(
                host="127.0.0.1",
                ads_port=ads_port,
                ams_net_id=ams_net_id,
            )
        except Exception as exc:
            _log.warning("Failed to create ADS client: %s", exc)
            # 不影响 server 启动；client 在 read/write 时会报错

        _log.info(
            "Beckhoff .NET ADS virtual server started: "
            "ams_net_id=%s, ads_port=%d, pid=%d",
            ams_net_id,
            ads_port,
            self._detected_pid,
        )
        return SimulatorResult(SimulatorStatus.OK)

    async def stop(self) -> SimulatorResult:
        """停止 .NET virtual ADS server 子进程（可靠清理）。

        Returns:
            SimulatorResult。
        """
        if not self._running:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)

        errors: list[str] = []
        if self._server is not None:
            try:
                from tools.source_lab.protocols.beckhoff_ads.dotnet_virtual_server import (
                    VirtualAdsServerLifecycle,
                )
                if isinstance(self._server, VirtualAdsServerLifecycle):
                    self._server.stop()
            except Exception as exc:
                errors.append(f"server stop error: {exc}")
        self._server = None
        self._client = None
        self._running = False
        self._protocol_evidence = False

        if errors:
            return SimulatorResult(
                SimulatorStatus.PARTIAL_SUCCESS,
                "; ".join(errors),
            )
        return SimulatorResult(SimulatorStatus.OK)

    async def health(self) -> SimulatorHealth:
        """检测 .NET ADS server 运行状态。

        Returns:
            SimulatorHealth。
        """
        if not self._running:
            return SimulatorHealth(SimulatorStatus.NOT_RUNNING)
        if self._server is None:
            return SimulatorHealth(SimulatorStatus.UNAVAILABLE, running=False)
        return SimulatorHealth(
            SimulatorStatus.OK,
            running=True,
            points_count=len(self._source.points) if self._source else 0,
            uptime_ms=_now_ms() - self._start_time_ms,
        )

    async def load_points(self, points: list) -> SimulatorResult:
        """加载点位配置（当前仅验证基本结构，不实际注册到 server）。"""
        if self._source is None:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "no SimulatedSource provided")
        if not self._source.points:
            return SimulatorResult(SimulatorStatus.BAD_REQUEST, "source has no ADS points")
        return SimulatorResult(SimulatorStatus.OK)

    async def read(
        self,
        point_keys: list[str],
    ) -> ReadSimulatorResult:
        """通过真实 ADS 客户端读取点位值。

        当 client 可用（即 AdsLib native runner 存在）时走真实协议读取；
        否则降级到 in_process simulator。

        Args:
            point_keys: 要读取的点位键列表。

        Returns:
            ReadSimulatorResult。
        """
        if not self._running:
            return ReadSimulatorResult(SimulatorStatus.NOT_RUNNING)

        # 尝试真实 client read
        if self._client is not None:
            from tools.source_lab.protocols.beckhoff_ads.ads_client import PyAdsClient
            if isinstance(self._client, PyAdsClient) and self._client.protocol_evidence:
                try:
                    result = self._client.read(point_keys)
                    if result.ok:
                        self._protocol_evidence = True
                        return ReadSimulatorResult(
                            SimulatorStatus.OK,
                            values=result.values,
                        )
                    return ReadSimulatorResult(
                        SimulatorStatus.PARTIAL_SUCCESS,
                        values=result.values,
                        message="; ".join(result.errors) if result.errors else "",
                    )
                except Exception as exc:
                    return ReadSimulatorResult(
                        SimulatorStatus.ERROR,
                        message=str(exc),
                    )

        # Fallback: 使用进程内 simulator
        try:
            from tools.source_lab.protocols.beckhoff_ads.runtime import (
                ADS_SIMULATOR_REGISTRY,
                AdsRuntimeUnavailableError,
            )
            assert self._source is not None
            values = ADS_SIMULATOR_REGISTRY.read(self._source, point_keys)
            return ReadSimulatorResult(
                SimulatorStatus.OK if values else SimulatorStatus.PARTIAL_SUCCESS,
                values=values,
            )
        except AdsRuntimeUnavailableError as exc:
            return ReadSimulatorResult(SimulatorStatus.UNAVAILABLE, message=str(exc))

    async def write(
        self,
        values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        """通过真实 ADS 客户端写入点位值。

        Args:
            values: 点位键 -> 值的映射。

        Returns:
            SimulatorResult。
        """
        if not self._running:
            return SimulatorResult(SimulatorStatus.NOT_RUNNING)

        if self._client is not None:
            from tools.source_lab.protocols.beckhoff_ads.ads_client import PyAdsClient
            if isinstance(self._client, PyAdsClient) and self._client.protocol_evidence:
                try:
                    result = self._client.write(values)
                    if result.ok:
                        self._protocol_evidence = True
                        return SimulatorResult(SimulatorStatus.OK)
                    return SimulatorResult(
                        SimulatorStatus.PARTIAL_SUCCESS,
                        "; ".join(result.errors) if result.errors else "write failed",
                    )
                except Exception as exc:
                    return SimulatorResult(SimulatorStatus.ERROR, str(exc))

        # Fallback: 使用进程内 simulator
        try:
            from tools.source_lab.protocols.beckhoff_ads.runtime import (
                ADS_SIMULATOR_REGISTRY,
                AdsRuntimeUnavailableError,
            )
            assert self._source is not None
            readback, errors = ADS_SIMULATOR_REGISTRY.write(self._source, values)
            if errors:
                return SimulatorResult(
                    SimulatorStatus.PARTIAL_SUCCESS,
                    "; ".join(errors),
                )
            return SimulatorResult(SimulatorStatus.OK)
        except AdsRuntimeUnavailableError as exc:
            return SimulatorResult(SimulatorStatus.UNAVAILABLE, str(exc))

    async def subscribe(self, point_keys: list[str]) -> SimulatorResult:
        """ADS_NOTIFICATION 仍为 NOT_IMPLEMENTED，不 fake subscribe。"""
        return SimulatorResult(
            SimulatorStatus.NOT_IMPLEMENTED,
            "Beckhoff ADS notification path is not implemented in source_lab",
        )

    async def report(self, point_keys: list[str]) -> SimulatorResult:
        """ADS report 路径仍为 NOT_IMPLEMENTED。"""
        return SimulatorResult(
            SimulatorStatus.NOT_IMPLEMENTED,
            "Beckhoff ADS report path is not implemented in source_lab",
        )

    async def update_values(
        self,
        values: dict[str, str | int | float | bool | None],
    ) -> SimulatorResult:
        """更新模拟器内部值——delegate 到 write 逻辑。"""
        return await self.write(values)


__all__ = ["BeckhoffAdsSimulatorFacade", "BeckhoffDotnetAdsSimulatorFacade"]
