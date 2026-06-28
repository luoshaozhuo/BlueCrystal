"""Driver adapter 使用的 backend 协议。

adapters 层只依赖这些结构化 Protocol，不直接依赖 infrastructure 的具体
backend 类。真实 backend 由 container 或 infrastructure factory 创建后
通过构造函数注入 adapter。
"""

from __future__ import annotations

from typing import Any, Protocol

from starfish.domain import StarfishServerMemberConfig


class DriverBackend(Protocol):
    """Driver adapter 可委托的最小 backend 契约。"""

    def connect(self) -> None:
        """建立预连接或执行空操作。"""

    def start(self) -> None:
        """启动 backend 生命周期。"""

    def stop(self) -> None:
        """停止 backend 生命周期。"""

    def health(self) -> dict[str, Any]:
        """返回 backend 可观测状态。"""

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """加载 server member 的点位与初始值。"""

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """读取点位值。"""

    def write(self, point_id: str, value: Any) -> None:
        """写入点位值。"""

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新点位值。"""

    def capabilities(self) -> list[str]:
        """返回能力声明。"""


class DriverBackendFactory(Protocol):
    """adapter factory 依赖的 backend 创建与探测契约。"""

    def create_http_rest_backend(self) -> DriverBackend:
        """创建 HTTP REST backend。"""

    def create_modbus_tcp_backend(self) -> DriverBackend:
        """创建 Modbus TCP backend。"""

    def create_mqtt_backend(self) -> DriverBackend:
        """创建 MQTT-like backend。"""

    def create_opcua_backend(self) -> DriverBackend:
        """创建 OPC UA native backend。"""

    def create_iec104_backend(self) -> DriverBackend:
        """创建 IEC104 native backend。"""

    def create_iec61850_mms_backend(self) -> DriverBackend:
        """创建 IEC61850 MMS native backend。"""

    def create_iec61850_report_backend(self) -> DriverBackend:
        """创建 IEC61850 Report native backend。"""

    def create_iec101_backend(self) -> DriverBackend:
        """创建 IEC101 backend。"""

    def create_modbus_rtu_backend(self, *, mode: str) -> DriverBackend:
        """按运行模式创建 Modbus RTU backend。"""

    def create_ads_backend(self) -> DriverBackend:
        """创建 ADS backend。"""

    def create_goose_backend(self) -> DriverBackend:
        """创建 GOOSE backend。"""

    def create_sv_backend(self) -> DriverBackend:
        """创建 SV backend。"""

    def create_simulator_backend(self) -> DriverBackend:
        """创建未知协议 fallback backend。"""

    def probe_binary(self, name: str) -> tuple[bool, str]:
        """按协议名探测 backend 运行环境。"""


class DelegatingDriverAdapter:
    """通过构造注入 backend 的通用委托 adapter 基类。"""

    def __init__(self, backend: DriverBackend) -> None:
        self._backend = backend

    @property
    def backend(self) -> DriverBackend:
        """返回注入的 backend，供测试和组合根检查 wiring。"""
        return self._backend

    def __getattr__(self, name: str) -> Any:
        """把 DriverPort 调用委托给注入的 backend。"""
        return getattr(self._backend, name)


__all__ = ["DelegatingDriverAdapter", "DriverBackend", "DriverBackendFactory"]
