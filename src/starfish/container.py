"""Starfish 默认 composition root。

本模块是 Starfish 生产默认 wiring 的集中入口。

职责边界：
- 允许同时 import adapters 与 infrastructure；
- 负责创建默认 config loader、backend factory、driver adapter factory；
- 负责将 infrastructure backend 注入 adapter；
- 负责构建默认 runtime context；
- 不承载业务规则、协议编解码、driver 运行逻辑。

Clean Architecture 定位：
- container.py 不是架构分层之一；
- 它是 composition root；
- application、domain、adapters 不应在本模块外直接依赖 infrastructure 具体实现。
"""

from __future__ import annotations

from pathlib import Path

from starfish.adapters.drivers.factory import StarfishDriverFactory
from starfish.application.ports.config_loader import ConfigLoaderPort
from starfish.application.ports.driver_factory import DriverFactoryPort
from starfish.application.ports.driver_port import DriverPort
from starfish.application.runtime.context import StarfishRuntimeContext
from starfish.application.use_cases import BuildRuntimeContextWorkflow
from starfish.infrastructure.drivers.backend_factory import StarfishBackendFactory
from starfish.infrastructure.file_loaders.server_config_json_loader import (
    ServerConfigJsonLoader,
)


# ---------------------------------------------------------------------------
# Default providers
# ---------------------------------------------------------------------------


def create_default_config_loader() -> ConfigLoaderPort:
    """创建默认配置加载器。

    默认实现读取 JSON 配置文件。返回 application port 类型，避免调用方依赖
    infrastructure 具体类。
    """
    return ServerConfigJsonLoader()


def create_default_backend_factory() -> StarfishBackendFactory:
    """创建默认 infrastructure backend factory。"""
    return StarfishBackendFactory()


def create_default_driver_factory(
    backend_factory: StarfishBackendFactory | None = None,
) -> DriverFactoryPort:
    """创建默认 driver adapter factory。

    Args:
        backend_factory: 可选 backend factory。测试或定制环境可传入 fake /
            custom backend factory；未传入时使用默认 infrastructure backend factory。

    Returns:
        DriverFactoryPort: application 层看到的 driver factory 抽象。
    """
    return StarfishDriverFactory(
        backend_factory=backend_factory or create_default_backend_factory(),
    )


def build_default_runtime_context(
    input_path: Path,
    *,
    config_loader: ConfigLoaderPort | None = None,
    driver_factory: DriverFactoryPort | None = None,
) -> StarfishRuntimeContext:
    """使用默认外层实现构建 runtime context。

    Args:
        input_path: 配置文件路径。
        config_loader: 可选配置加载 port。未传入时使用默认 JSON loader。
        driver_factory: 可选 driver factory port。未传入时使用默认 driver factory。

    Returns:
        StarfishRuntimeContext: application runtime kernel root。
    """
    return BuildRuntimeContextWorkflow(
        config_loader=config_loader or create_default_config_loader(),
        driver_factory=driver_factory or create_default_driver_factory(),
    ).execute(input_path)


# ---------------------------------------------------------------------------
# Driver adapter providers
# ---------------------------------------------------------------------------


def create_http_rest_driver_adapter(
    *,
    bind_host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 HTTP REST backend 的 driver adapter。"""
    from starfish.adapters.drivers.protocol.http.http_rest_driver_adapter import (
        HttpRestDriverAdapter,
    )
    from starfish.infrastructure.drivers.protocol.http.http_rest_server_backend import (
        HttpRestServerBackend,
    )

    return HttpRestDriverAdapter(
        HttpRestServerBackend(bind_host=bind_host, port=port),
    )


def create_modbus_tcp_driver_adapter(
    *,
    bind_host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 Modbus TCP backend 的 driver adapter。"""
    from starfish.adapters.drivers.modbus.modbus_tcp_driver_adapter import (
        ModbusTcpDriverAdapter,
    )
    from starfish.infrastructure.drivers.modbus.modbus_tcp_server_backend import (
        ModbusTcpServerBackend,
    )

    return ModbusTcpDriverAdapter(
        ModbusTcpServerBackend(bind_host=bind_host, port=port),
    )


def create_mqtt_driver_adapter(
    *,
    bind_host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 MQTT-like backend 的 driver adapter。"""
    from starfish.adapters.drivers.protocol.mqtt.mqtt_driver_adapter import (
        MqttDriverAdapter,
    )
    from starfish.infrastructure.drivers.protocol.mqtt.mqtt_server_backend import (
        MqttServerBackend,
    )

    return MqttDriverAdapter(
        MqttServerBackend(bind_host=bind_host, port=port),
    )


def create_modbus_rtu_driver_adapter(
    *,
    mode: str = "rtu-lightweight",
) -> DriverPort:
    """创建注入 Modbus RTU backend 的 driver adapter。"""
    from starfish.adapters.drivers.modbus.modbus_rtu_driver_adapter import (
        ModbusRtuDriverAdapter,
    )
    from starfish.infrastructure.drivers.modbus.modbus_rtu_pty_backend import (
        ModbusRtuPtyBackend,
    )

    return ModbusRtuDriverAdapter(
        ModbusRtuPtyBackend(mode=mode),
    )


def create_opcua_driver_adapter(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 OPC UA native backend 的 driver adapter。"""
    from starfish.adapters.drivers.native.opcua.opcua_driver_adapter import (
        OpcUaDriverAdapter,
    )
    from starfish.infrastructure.drivers.native.opcua.opcua_native_backend import (
        OpcUaNativeBackend,
    )

    return OpcUaDriverAdapter(
        OpcUaNativeBackend(bind_host=host, port=port),
    )


def create_iec104_driver_adapter(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 IEC104 native backend 的 driver adapter。"""
    from starfish.adapters.drivers.native.iec.iec104_driver_adapter import (
        Iec104DriverAdapter,
    )
    from starfish.infrastructure.drivers.native.iec.iec104_native_backend import (
        Iec104NativeBackend,
    )

    return Iec104DriverAdapter(
        Iec104NativeBackend(bind_host=host, port=port),
    )


def create_iec61850_mms_driver_adapter(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 IEC61850 MMS native backend 的 driver adapter。"""
    from starfish.adapters.drivers.native.iec.iec61850_mms_driver_adapter import (
        Iec61850MmsDriverAdapter,
    )
    from starfish.infrastructure.drivers.native.iec.iec61850_mms_native_backend import (
        Iec61850MmsNativeBackend,
    )

    return Iec61850MmsDriverAdapter(
        Iec61850MmsNativeBackend(bind_host=host, port=port),
    )


def create_iec61850_report_driver_adapter(
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> DriverPort:
    """创建注入 IEC61850 Report native backend 的 driver adapter。"""
    from starfish.adapters.drivers.native.iec.iec61850_report_driver_adapter import (
        Iec61850ReportDriverAdapter,
    )
    from starfish.infrastructure.drivers.native.iec.iec61850_report_native_backend import (
        Iec61850ReportNativeBackend,
    )

    return Iec61850ReportDriverAdapter(
        Iec61850ReportNativeBackend(bind_host=host, port=port),
    )


def create_iec101_driver_adapter() -> DriverPort:
    """创建注入 IEC101 backend 的 driver adapter。"""
    from starfish.adapters.drivers.iec.iec101_driver_adapter import (
        Iec101DriverAdapter,
    )
    from starfish.infrastructure.drivers.iec.iec101_backend import Iec101Backend

    return Iec101DriverAdapter(Iec101Backend())


def create_ads_driver_adapter() -> DriverPort:
    """创建注入 ADS backend 的 driver adapter。"""
    from starfish.adapters.drivers.ads.ads_driver_adapter import AdsDriverAdapter
    from starfish.infrastructure.drivers.ads.ads_backend import AdsBackend

    return AdsDriverAdapter(AdsBackend())


def create_goose_driver_adapter() -> DriverPort:
    """创建注入 GOOSE backend 的 driver adapter。"""
    from starfish.adapters.drivers.iec.goose_driver_adapter import GooseDriverAdapter
    from starfish.infrastructure.drivers.iec.goose_backend import GooseBackend

    return GooseDriverAdapter(GooseBackend())


def create_sv_driver_adapter() -> DriverPort:
    """创建注入 SV backend 的 driver adapter。"""
    from starfish.adapters.drivers.iec.sv_driver_adapter import SvDriverAdapter
    from starfish.infrastructure.drivers.iec.sv_backend import SvBackend

    return SvDriverAdapter(SvBackend())


def create_server_simulator_driver_adapter() -> DriverPort:
    """创建注入 in-memory simulator backend 的 driver adapter。"""
    from starfish.adapters.drivers.simulator.server_simulator_driver_adapter import (
        ServerSimulatorDriverAdapter,
    )
    from starfish.infrastructure.drivers.simulator.server_simulator_backend import (
        ServerSimulatorBackend,
    )

    return ServerSimulatorDriverAdapter(ServerSimulatorBackend())


__all__ = [
    "build_default_runtime_context",
    "create_ads_driver_adapter",
    "create_default_backend_factory",
    "create_default_config_loader",
    "create_default_driver_factory",
    "create_goose_driver_adapter",
    "create_http_rest_driver_adapter",
    "create_iec101_driver_adapter",
    "create_iec104_driver_adapter",
    "create_iec61850_mms_driver_adapter",
    "create_iec61850_report_driver_adapter",
    "create_modbus_rtu_driver_adapter",
    "create_modbus_tcp_driver_adapter",
    "create_mqtt_driver_adapter",
    "create_opcua_driver_adapter",
    "create_server_simulator_driver_adapter",
    "create_sv_driver_adapter",
]