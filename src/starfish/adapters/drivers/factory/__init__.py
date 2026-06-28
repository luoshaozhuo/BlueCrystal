"""Starfish 协议 driver adapter factory。

本模块位于 adapters 层，根据 endpoint.protocol 选择具体 adapter，
并完成环境探测、driver 实例化与 load_points。application 层只通过
DriverFactoryPort 的结构化方法调用本模块，不直接 import concrete driver。

支持以下模式：

- real:              已实现的协议专用真实 adapter（HTTP_REST、MODBUS_TCP）。
- mqtt-lightweight:   MQTT 轻量级端点（TCP JSON 行协议，非完整 MQTT broker）。
- real/native:       OPC_UA / IEC104 / IEC61850_MMS / IEC61850_REPORT 的 C runner 子进程模式（binary 可用时）。
- unavailable:       OPC_UA / IEC104 binary 缺失时的安全回退。
- report-lightweight: IEC61850_REPORT binary 缺失时的轻量 report shell。
- codec-enhanced:    IEC101 增强编解码器就绪（信息体 + ASDU 列表 + FT1.2 帧）。
- codec-skeleton:    IEC101 编解码器骨架就绪（ASDU/COT/IOA/CA 编解码）。
- codebase-pending:  MODBUS_RTU / Beckhoff ADS 协议 stub（实现环境未就绪）。
- environment-pending: GOOSE / SV 协议 stub（网络/硬件环境未就绪）。
- stub:              未实现协议的 in-memory stub fallback。

工厂 dispatch 规则：
    - HTTP_REST -> HttpRestDriverAdapter（real mode）
    - MODBUS_TCP -> ModbusTcpDriverAdapter（real mode）
    - MQTT -> MqttDriverAdapter（mqtt-lightweight mode）
    - OPC_UA -> OpcUaDriverAdapter（binary 可用时 real，缺失时 unavailable）
    - IEC_104 / IEC104 -> Iec104DriverAdapter（binary 可用时 real，缺失时 unavailable）
    - IEC61850_MMS -> Iec61850MmsDriverAdapter（binary 可用时 real，缺失时 unavailable）
    - IEC61850_REPORT -> Iec61850ReportDriverAdapter（binary 可用时 real，缺失时 report-lightweight）
    - IEC101 / IEC_101 -> Iec101DriverAdapter（codec-enhanced / codec-skeleton / environment-pending / codebase-pending）
    - MODBUS_RTU -> ModbusRtuDriverAdapter（rtu-lightweight / codebase-pending）
    - BECKHOFF_ADS / ADS -> AdsDriverAdapter（codebase-pending mode）
    - GOOSE -> GooseDriverAdapter（environment-pending mode）
    - SV -> SvDriverAdapter（environment-pending mode）
    - 其他协议 -> ServerSimulatorDriverAdapter（stub mode）

职责：
- 根据 endpoint.protocol 创建 adapter。
- OPC_UA / IEC104 / IEC61850_MMS / IEC61850_REPORT 根据环境探测结果返回对应模式。
- IEC101 根据增强/基础编解码器和 binary 可用性返回对应模式。
- 不支持协议返回 stub fallback，标记 mode="stub"。
- 不得调用 Whale shared_source production client。

不负责：
- runtime graph entries 的生命周期聚合。
- CLI/API/usecase 编排。
- domain 协议 codec 的定义。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from typing import Any

from starfish.adapters.drivers.backend_ports import DriverBackendFactory
from starfish.domain import DriverEntry, StarfishEndpointConfig, StarfishServerConfig, StarfishServerMemberConfig


def _normalize_protocol(protocol: str) -> str:
    """归一化协议名字符串。

    将不同来源的协议名（大小写变体、缩写等）归一化为标准形式，
    用于 factory dispatch 匹配。

    Args:
        protocol: 原始协议名字符串。

    Returns:
        归一化后的协议名（大写，下划线分隔）。
    """
    return protocol.strip().upper().replace(" ", "_").replace("-", "_")


# 已实现真实 server 的协议集合（含完整 TCP server 生命周期）
_REAL_PROTOCOLS: frozenset[str] = frozenset({"HTTP_REST", "MODBUS_TCP"})

# 已实现轻量级端点的协议集合（有真实 server，但非完整协议实现）
# MODBUS_RTU 在 PTY 可用时属于 rtu-lightweight 模式
_LIGHTWEIGHT_PROTOCOLS: frozenset[str] = frozenset({"MQTT", "MODBUS_RTU"})

# 依赖 native C runner 的协议集合（real 模式需 binary 存在）
_NATIVE_RUNNER_PROTOCOLS: frozenset[str] = frozenset({
    "OPC_UA", "IEC_104", "IEC104",
    "IEC61850_MMS", "IEC61850_REPORT",
})

# codec-skeleton 协议集合（编解码器骨架就绪但不具备完整 server 能力）
# IEC101 编解码器骨架可用时为 codec-skeleton 模式
_CODEC_SKELETON_PROTOCOLS: frozenset[str] = frozenset({
    "IEC101", "IEC_101",
})

# codec-enhanced 协议集合（信息体 + ASDU 列表 + FT1.2 帧）
# IEC101 增强编解码器可用时为 codec-enhanced 模式
_CODEC_ENHANCED_PROTOCOLS: frozenset[str] = frozenset({
    "IEC101", "IEC_101",
})

# codec-enhanced-plus 协议集合（CP56Time2a + 带时标 TypeID +
# C_SC_NA_1 QU 结构化 + link-layer skeleton）
# IEC101 时间增强编解码器可用时为 codec-enhanced-plus 模式
_CODEC_ENHANCED_PLUS_PROTOCOLS: frozenset[str] = frozenset({
    "IEC101", "IEC_101",
})

# codebase-pending 协议集合（有 adapter 定义但实现未就绪）
# MODBUS_RTU 在 PTY 可用时为 rtu-lightweight 模式，不再是 codebase-pending
# IEC101 在编解码器或 C binary 可用时不再是 codebase-pending
_CODABASE_PENDING_PROTOCOLS: frozenset[str] = frozenset({
    "BECKHOFF_ADS", "ADS",
})

# environment-pending 协议集合（实现可能就绪但运行环境不满足）
_ENVIRONMENT_PENDING_PROTOCOLS: frozenset[str] = frozenset({
    "GOOSE", "SV",
    })


class StarfishDriverFactory:
    """Starfish 默认协议 driver factory adapter。"""

    def __init__(self, backend_factory: DriverBackendFactory) -> None:
        """接收 infrastructure backend factory。

        Args:
            backend_factory: 由 composition root 创建并注入的 backend factory。
        """
        self._backend_factory = backend_factory

    def create_driver_for_endpoint(
        self,
        server: StarfishServerMemberConfig,
        endpoint: StarfishEndpointConfig,
    ) -> DriverEntry:
        """创建单个 endpoint 的 driver entry。

        Args:
            server: endpoint 所属 server member。
            endpoint: 待装配的 endpoint。

        Returns:
            包含 adapter、mode、available 和 reason 的 DriverEntry。
        """
        return create_driver_for_endpoint(server, endpoint, backend_factory=self._backend_factory)


def create_driver_for_endpoint(
    server_or_endpoint: StarfishServerMemberConfig | StarfishEndpointConfig,
    endpoint_or_config: StarfishEndpointConfig | StarfishServerConfig | StarfishServerMemberConfig,
    *,
    backend_factory: DriverBackendFactory,
) -> DriverEntry:
    """为单个端点创建对应的协议 adapter。

    根据 endpoint.protocol 选择真实 adapter、轻量级 adapter、stub fallback 或
    unavailable 状态。已实现真实 server 的协议使用协议专用 adapter（mode="real"），
    MQTT 使用轻量级端点（mode="mqtt-lightweight"），
    其他协议使用 in-memory stub（mode="stub"）。

    Args:
        server_or_endpoint: 新签名下为 server member；旧签名下为 endpoint。
        endpoint_or_config: 新签名下为 endpoint；旧签名下为顶层 config 或单 member。

    Returns:
        包含驱动实例、可用性状态和运行模式的 DriverEntry。
    """
    if isinstance(server_or_endpoint, StarfishEndpointConfig):
        endpoint = server_or_endpoint
        config = endpoint_or_config
        if isinstance(config, StarfishServerConfig):
            server = config.servers[0]
        elif isinstance(config, StarfishServerMemberConfig):
            server = config
        else:
            raise TypeError("create_driver_for_endpoint 第二个参数必须是 StarfishServerConfig 或 StarfishServerMemberConfig")
    else:
        server = server_or_endpoint
        candidate_endpoint = endpoint_or_config
        if not isinstance(candidate_endpoint, StarfishEndpointConfig):
            raise TypeError("create_driver_for_endpoint 第二个参数必须是 StarfishEndpointConfig")
        endpoint = candidate_endpoint

    protocol = _normalize_protocol(endpoint.protocol or "")

    if protocol == "HTTP_REST":
        from starfish.adapters.drivers.protocol.http.http_rest_driver_adapter import HttpRestDriverAdapter
        adapter: Any = HttpRestDriverAdapter(backend_factory.create_http_rest_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> real HTTP REST server (infrastructure backend)",
            mode="real",
        )

    if protocol == "MODBUS_TCP":
        from starfish.adapters.drivers.modbus.modbus_tcp_driver_adapter import ModbusTcpDriverAdapter
        adapter = ModbusTcpDriverAdapter(backend_factory.create_modbus_tcp_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> real Modbus TCP server (FC03/FC06)",
            mode="real",
        )

    if protocol == "MQTT":
        from starfish.adapters.drivers.protocol.mqtt.mqtt_driver_adapter import MqttDriverAdapter
        adapter = MqttDriverAdapter(backend_factory.create_mqtt_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> lightweight MQTT-like endpoint "
                   f"(TCP JSON line protocol, subscribe via polling queue; "
                   f"非完整 MQTT broker)",
            mode="mqtt-lightweight",
        )

    # OPC_UA: 依赖 open62541 C runner 子进程
    if protocol == "OPC_UA":
        from starfish.adapters.drivers.native.opcua.opcua_driver_adapter import OpcUaDriverAdapter
        binary_ok, binary_reason = backend_factory.probe_binary("OPC_UA")
        adapter = OpcUaDriverAdapter(backend_factory.create_opcua_backend())
        adapter.load_points(server)
        mode = adapter.mode
        available = binary_ok
        if binary_ok:
            reason = (
                f"protocol={protocol} -> OPC UA real mode "
                f"(open62541 C runner 子进程)"
            )
        else:
            reason = (
                f"protocol={protocol} -> OPC UA unavailable mode: "
                f"{binary_reason}"
            )
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC104: 依赖 iec104_simulator_server C runner 子进程
    # 归一化：IEC_104 和 IEC104 均视为 IEC104
    if protocol in ("IEC_104", "IEC104"):
        from starfish.adapters.drivers.native.iec.iec104_driver_adapter import Iec104DriverAdapter
        binary_ok, binary_reason = backend_factory.probe_binary("IEC104")
        adapter = Iec104DriverAdapter(backend_factory.create_iec104_backend())
        adapter.load_points(server)
        mode = adapter.mode
        available = binary_ok
        if binary_ok:
            reason = (
                f"protocol={protocol} -> IEC104 real mode "
                f"(iec104_simulator_server C runner 子进程)"
            )
        else:
            reason = (
                f"protocol={protocol} -> IEC104 unavailable mode: "
                f"{binary_reason}"
            )
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC61850_MMS: 依赖 iec61850_simulator_server C runner 子进程
    if protocol in ("IEC61850_MMS",):
        from starfish.adapters.drivers.native.iec.iec61850_mms_driver_adapter import (
            Iec61850MmsDriverAdapter,
        )
        binary_ok, binary_reason = backend_factory.probe_binary("IEC61850_MMS")
        adapter = Iec61850MmsDriverAdapter(backend_factory.create_iec61850_mms_backend())
        adapter.load_points(server)
        mode = adapter.mode
        available = binary_ok
        if binary_ok:
            reason = (
                f"protocol={protocol} -> IEC61850 MMS real mode "
                f"(iec61850_simulator_server C runner 子进程)"
            )
        else:
            reason = (
                f"protocol={protocol} -> IEC61850 MMS unavailable mode: "
                f"{binary_reason}"
            )
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC61850_REPORT: 依赖 iec61850_simulator_server + iec61850_report_runner
    if protocol in ("IEC61850_REPORT",):
        from starfish.adapters.drivers.native.iec.iec61850_report_driver_adapter import (
            Iec61850ReportDriverAdapter,
        )
        binary_ok, binary_reason = backend_factory.probe_binary("IEC61850_REPORT")
        adapter = Iec61850ReportDriverAdapter(backend_factory.create_iec61850_report_backend())
        adapter.load_points(server)
        mode = adapter.mode
        available = binary_ok
        if binary_ok:
            reason = (
                f"protocol={protocol} -> IEC61850 Report real mode "
                f"(iec61850_simulator_server + iec61850_report_runner C runner 子进程)"
            )
        else:
            reason = (
                f"protocol={protocol} -> IEC61850 Report report-lightweight mode: "
                f"{binary_reason}. 不等同完整 IEC61850 Report server，"
                f"真实 runner 标记 environment-pending"
            )
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=available,
            reason=reason,
            mode=mode,
        )

    # ── codebase-pending 协议 ────────────────────────────────────────────────────

    # IEC101: 串口链路协议
    # 模式分级:
    #   codec-enhanced-plus > codec-enhanced > codec-skeleton >
    #   environment-pending > codebase-pending
    if protocol in ("IEC101", "IEC_101"):
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        adapter.load_points(server)
        current_mode = adapter.mode
        if current_mode == "codec-enhanced-plus":
            reason = (
                f"protocol={protocol} -> IEC101 codec-enhanced-plus "
                f"(CP56Time2a + 带时标 M_SP_TA_1/M_DP_TA_1/M_ME_TA_1 + C_SC_NA_1 QU "
                f"结构化 + link-layer skeleton + 信息体/ASDU 列表 SQ=0/SQ=1/FT1.2 帧，"
                f"不等同完整 server；link-layer skeleton 非 server)"
            )
        elif current_mode == "codec-enhanced":
            reason = (
                f"protocol={protocol} -> IEC101 codec-enhanced "
                f"(信息体 + ASDU 列表 SQ=0/SQ=1 + FT1.2 帧 + checksum 编解码就绪，"
                f"不等同完整 server)"
            )
        elif current_mode == "codec-skeleton":
            reason = (
                f"protocol={protocol} -> IEC101 codec-skeleton "
                f"(ASDU/COT/IOA/CA 编解码就绪，不等同完整 server)"
            )
        elif current_mode == "environment-pending":
            reason = (
                f"protocol={protocol} -> IEC101 environment-pending "
                f"(C runner 已编译但串口链路环境未就绪)"
            )
        else:
            reason = (
                f"protocol={protocol} -> IEC101 codebase-pending stub "
                f"(串口链路环境未就绪，编解码器和 C runner 均不可用)"
            )
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=reason,
            mode=current_mode,
        )

    # MODBUS_RTU: 串口链路协议，与 MODBUS_TCP 不同（无 MBAP 头，使用 CRC）
    # 根据 PTY 可用性选择 rtu-lightweight 或 codebase-pending 模式
    if protocol == "MODBUS_RTU":
        from starfish.adapters.drivers.modbus.modbus_rtu_driver_adapter import (
            ModbusRtuDriverAdapter,
        )
        pty_ok, pty_reason = backend_factory.probe_binary("MODBUS_RTU")
        if pty_ok:
            mode = "rtu-lightweight"
            adapter = ModbusRtuDriverAdapter(backend_factory.create_modbus_rtu_backend(mode="rtu-lightweight"))
            reason = (
                f"protocol={protocol} -> Modbus RTU PTY lightweight mode "
                f"(local PTY simulation, 不等同真实串口)"
            )
        else:
            mode = "codebase-pending"
            adapter = ModbusRtuDriverAdapter(backend_factory.create_modbus_rtu_backend(mode="codebase-pending"))
            reason = (
                f"protocol={protocol} -> Modbus RTU codebase-pending stub "
                f"(串口/PTY 链路环境未就绪: {pty_reason})"
            )
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=reason,
            mode=mode,
        )

    # Beckhoff ADS: 需 .NET/TwinCAT runtime
    if protocol in ("BECKHOFF_ADS", "ADS"):
        from starfish.adapters.drivers.ads.ads_driver_adapter import AdsDriverAdapter
        adapter = AdsDriverAdapter(backend_factory.create_ads_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> Beckhoff ADS codebase-pending stub "
                   f"(.NET/TwinCAT runtime 未就绪，source_lab 有 dotnet 参考实现待迁移)",
            mode="codebase-pending",
        )

    # ── environment-pending 协议 ─────────────────────────────────────────────────

    # GOOSE: L2 veth 多播协议
    if protocol == "GOOSE":
        from starfish.adapters.drivers.iec.goose_driver_adapter import GooseDriverAdapter
        adapter = GooseDriverAdapter(backend_factory.create_goose_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> GOOSE environment-pending stub "
                   f"(需 L2 veth 网络环境，不可 localhost 回环)",
            mode="environment-pending",
        )

    # SV (Sampled Values): L2 veth + PTP 时间同步
    if protocol == "SV":
        from starfish.adapters.drivers.iec.sv_driver_adapter import SvDriverAdapter
        adapter = SvDriverAdapter(backend_factory.create_sv_backend())
        adapter.load_points(server)
        return DriverEntry(
            server=server,
            endpoint=endpoint,
            driver=adapter,
            available=True,
            reason=f"protocol={protocol} -> SV environment-pending stub "
                   f"(需 L2 veth 网络环境 + 硬件 PTP 时间同步)",
            mode="environment-pending",
        )

    # fallback: in-memory stub
    from starfish.adapters.drivers.simulator.server_simulator_driver_adapter import ServerSimulatorDriverAdapter
    adapter = ServerSimulatorDriverAdapter(backend_factory.create_simulator_backend())
    adapter.load_points(server)
    return DriverEntry(
        server=server,
        endpoint=endpoint,
        driver=adapter,
        available=True,
        reason=f"protocol={protocol} -> in-memory stub adapter (mode=stub)",
        mode="stub",
    )


def get_supported_protocols() -> list[str]:
    """返回所有已注册协议（含 real、lightweight、native-runner、codec-skeleton、
    codec-enhanced、codebase-pending 和 environment-pending）。

    不含 stub-only 协议。
    MODBUS_RTU 根据 PTY 可用性动态归属。
    IEC101 根据增强/基础编解码器和 binary 可用性动态归属。

    Returns:
        协议名列表（按字母排序）。
    """
    protocols = set(
        _REAL_PROTOCOLS
        | _LIGHTWEIGHT_PROTOCOLS
        | _NATIVE_RUNNER_PROTOCOLS
        | _CODEC_SKELETON_PROTOCOLS
        | _CODEC_ENHANCED_PROTOCOLS
        | _CODEC_ENHANCED_PLUS_PROTOCOLS
        | _CODABASE_PENDING_PROTOCOLS
        | _ENVIRONMENT_PENDING_PROTOCOLS
    )
    # MODBUS_RTU 总是受支持
    protocols.add("MODBUS_RTU")
    return sorted(protocols)


def get_real_protocols() -> list[str]:
    """返回已实现完整真实 server 的协议列表。

    Returns:
        协议名列表（当前 ["HTTP_REST", "MODBUS_TCP"]）。
    """
    return sorted(_REAL_PROTOCOLS)


def get_lightweight_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回已实现轻量级端点的协议列表。

    MODBUS_RTU 动态决定：PTY 可用时为 rtu-lightweight 模式。

    Returns:
        协议名列表（如 ["MODBUS_RTU", "MQTT"]）。
    """
    result = sorted(_LIGHTWEIGHT_PROTOCOLS - {"MODBUS_RTU"})
    pty_ok = False
    if backend_factory is not None:
        pty_ok, _ = backend_factory.probe_binary("MODBUS_RTU")
    if pty_ok:
        result.append("MODBUS_RTU")
        result.sort()
    return result


def get_native_runner_protocols() -> list[str]:
    """返回依赖 native C runner 子进程的协议列表。

    这些协议在 binary 可用时为 real 模式，缺失时为 unavailable。

    Returns:
        协议名列表（如 ["IEC_104", "IEC104", "IEC61850_MMS", "IEC61850_REPORT", "OPC_UA"]）。
    """
    return sorted(_NATIVE_RUNNER_PROTOCOLS)


def get_codec_skeleton_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回编解码器骨架就绪的协议列表。

    这些协议有编解码器骨架实现，但缺少完整 server 能力。
    IEC101 动态决定：基础编解码器可用时（未升级到 codec-enhanced）为
    codec-skeleton 模式。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    if backend_factory is not None:
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        mode = adapter.mode
    else:
        mode = "codec-skeleton"
    if mode == "codec-skeleton":
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codec_enhanced_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回编解码器增强就绪的协议列表。

    这些协议有增强编解码器实现（信息体 + ASDU 列表 + 链路层帧），
    但缺少完整 server 能力。
    IEC101 动态决定：增强编解码器全部组件可用时为 codec-enhanced 模式。
    注意：codec-enhanced-plus 是更高阶模式，当处于 plus 时
    仍视为已满足 codec-enhanced 增强基线。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    if backend_factory is not None:
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        mode = adapter.mode
    else:
        mode = "codec-enhanced-plus"
    if mode in ("codec-enhanced", "codec-enhanced-plus"):
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codec_enhanced_plus_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回编解码器时间增强就绪的协议列表。

    这些协议有时间增强编解码器（CP56Time2a + 带时标 TypeID +
    C_SC_NA_1 QU 结构化 + link-layer skeleton），但 link-layer 仅为
    skeleton，缺少完整 server 能力。
    IEC101 动态决定：时间增强编解码器全部组件可用时为
    codec-enhanced-plus 模式。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    if backend_factory is not None:
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        mode = adapter.mode
    else:
        mode = "codec-enhanced-plus"
    if mode == "codec-enhanced-plus":
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codebase_pending_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回 codebase-pending 状态的协议列表。

    这些协议有 adapter 定义，但实现代码（binary 或 Python 原生实现）尚未就绪。
    MODBUS_RTU 动态决定：PTY 可用时为 rtu-lightweight 模式，
    PTY 不可用时为 codebase-pending。
    IEC101 动态决定：编解码器和 binary 均不可用时为 codebase-pending。

    Returns:
        协议名列表（如 ["ADS", "BECKHOFF_ADS"]，
        含 "MODBUS_RTU" 当 PTY 不可用时，含 "IEC101"/"IEC_101" 当全部不可用时）。
    """
    result = sorted(_CODABASE_PENDING_PROTOCOLS)
    pty_ok = False
    if backend_factory is not None:
        pty_ok, _ = backend_factory.probe_binary("MODBUS_RTU")
    if not pty_ok:
        result.append("MODBUS_RTU")
    # 动态判断 IEC101：编解码器和 binary 均不可用时为 codebase-pending
    if backend_factory is not None:
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        iec101_mode = adapter.mode
    else:
        iec101_mode = ""
    if iec101_mode == "codebase-pending":
        result.append("IEC101")
        result.append("IEC_101")
    result.sort()
    return result


def get_environment_pending_protocols(backend_factory: DriverBackendFactory | None = None) -> list[str]:
    """返回 environment-pending 状态的协议列表。

    这些协议可能有实现代码，但运行环境（L2 网络、硬件等）不满足要求。
    IEC101 动态判断：C binary 已编译但编解码器不可用时为 environment-pending。

    Returns:
        协议名列表（如 ["GOOSE", "IEC101", "IEC_101", "SV"]）。
    """
    result = sorted(_ENVIRONMENT_PENDING_PROTOCOLS)
    # 动态判断 IEC101：binary 已编译但编解码器不可用且串口环境缺失时为 environment-pending
    if backend_factory is not None:
        from starfish.adapters.drivers.iec.iec101_driver_adapter import Iec101DriverAdapter
        adapter = Iec101DriverAdapter(backend_factory.create_iec101_backend())
        iec101_mode = adapter.mode
    else:
        iec101_mode = ""
    if iec101_mode == "environment-pending":
        result.append("IEC101")
        result.append("IEC_101")
        result.sort()
    return result


__all__ = [
    "StarfishDriverFactory",
    "create_driver_for_endpoint",
    "get_supported_protocols",
    "get_real_protocols",
    "get_lightweight_protocols",
    "get_native_runner_protocols",
    "get_codec_skeleton_protocols",
    "get_codec_enhanced_protocols",
    "get_codec_enhanced_plus_protocols",
    "get_codebase_pending_protocols",
    "get_environment_pending_protocols",
]
