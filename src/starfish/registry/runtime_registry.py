"""starfish 运行时注册表 —— 协议 facade 工厂。

本模块提供工厂函数，根据 ServerPlan 端点的 protocol 字段
创建对应的 ServerSimulatorFacade。支持以下模式：

- real:              已实现的协议专用真实 facade（HTTP_REST、MODBUS_TCP）。
- mqtt-lightweight:   MQTT 轻量级端点（TCP JSON 行协议，非完整 MQTT broker）。
- real/native:       OPC_UA / IEC104 / IEC61850_MMS / IEC61850_REPORT 的 C runner 子进程模式（binary 可用时）。
- unavailable:       OPC_UA / IEC104 binary 缺失时的安全回退。
- report-lightweight: IEC61850_REPORT binary 缺失时的轻量 report shell。
- codec-enhanced:    IEC101 增强编解码器就绪（Round 15 新增，信息体 + ASDU 列表 + FT1.2 帧）。
- codec-skeleton:    IEC101 编解码器骨架就绪（Round 14，ASDU/COT/IOA/CA 编解码）。
- codebase-pending:  MODBUS_RTU / Beckhoff ADS 协议 stub（实现环境未就绪）。
- environment-pending: GOOSE / SV 协议 stub（网络/硬件环境未就绪）。
- stub:              未实现协议的 in-memory stub fallback。

工厂 dispatch 规则：
    - HTTP_REST -> HttpRestFacade（real mode）
    - MODBUS_TCP -> ModbusTcpFacade（real mode）
    - MQTT -> MqttFacade（mqtt-lightweight mode）
    - OPC_UA -> OpcUaFacade（binary 可用时 real，缺失时 unavailable）
    - IEC_104 / IEC104 -> Iec104Facade（binary 可用时 real，缺失时 unavailable）
    - IEC61850_MMS -> Iec61850MmsFacade（binary 可用时 real，缺失时 unavailable）
    - IEC61850_REPORT -> Iec61850ReportFacade（binary 可用时 real，缺失时 report-lightweight）
    - IEC101 / IEC_101 -> Iec101Facade（codec-enhanced / codec-skeleton / environment-pending / codebase-pending）
    - MODBUS_RTU -> ModbusRtuFacade（rtu-lightweight / codebase-pending）
    - BECKHOFF_ADS / ADS -> AdsFacade（codebase-pending mode）
    - GOOSE -> GooseFacade（environment-pending mode）
    - SV -> SvFacade（environment-pending mode）
    - 其他协议 -> ServerSimulatorFacade（stub mode）

职责：
- 根据 endpoint.protocol 创建 facade。
- OPC_UA / IEC104 / IEC61850_MMS / IEC61850_REPORT 根据环境探测结果返回对应模式。
- IEC101 根据增强/基础编解码器和 binary 可用性返回对应模式。
- 不支持协议返回 stub fallback，标记 mode="stub"。
- 不得调用 Whale shared_source production client。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from starfish.models.plan import StarfishServerPlan, StarfishEndpointPlan


@dataclass
class FacadeEntry:
    """注册表中的 facade 条目。

    Attributes:
        endpoint: 关联的端点信息。
        facade: 创建的 facade 实例（类型因协议而异但共享相同接口）。
        available: 是否可用（unsupported 协议时为 False）。
        reason: unavailable 时的原因说明。
        mode: 运行模式（"real" / "mqtt-lightweight" / "stub" / "unavailable"）。
    """

    endpoint: StarfishEndpointPlan
    facade: Any = None
    available: bool = True
    reason: str = ""
    mode: str = "stub"


@dataclass
class RuntimeRegistry:
    """运行时注册表 —— 管理一个 ServerPlan 对应的全部 facade。

    根据 ServerPlan 的每个 endpoint 创建对应的 facade，
    提供统一的 start/stop/health 查询入口。

    Attributes:
        plan: 关联的 StarfishServerPlan。
        entries: 每个 endpoint 对应的 facade 条目列表。
    """

    plan: StarfishServerPlan
    entries: list[FacadeEntry] = field(default_factory=list)

    def start_all(self) -> None:
        """启动所有可用的 facade。"""
        for entry in self.entries:
            if entry.available and entry.facade is not None:
                entry.facade.start()

    def stop_all(self) -> None:
        """停止所有可用的 facade。"""
        for entry in self.entries:
            if entry.available and entry.facade is not None:
                entry.facade.stop()

    def health_all(self) -> dict[str, Any]:
        """返回所有 facade 的聚合健康状态。

        Returns:
            包含每个 endpoint 健康信息的 dict。
        """
        result: dict[str, Any] = {}
        for entry in self.entries:
            ep_id = entry.endpoint.endpoint_id or entry.endpoint.endpoint_name or "unknown"
            if entry.facade is not None and entry.available:
                result[ep_id] = entry.facade.health()
            else:
                result[ep_id] = {
                    "status": "unavailable",
                    "reason": entry.reason or "NOT_IMPLEMENTED",
                }
        return result


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

# codec-enhanced 协议集合（Round 15 新增，信息体 + ASDU 列表 + FT1.2 帧）
# IEC101 增强编解码器可用时为 codec-enhanced 模式
_CODEC_ENHANCED_PROTOCOLS: frozenset[str] = frozenset({
    "IEC101", "IEC_101",
})

# codec-enhanced-plus 协议集合（Round 16 新增，CP56Time2a + 带时标 TypeID +
# C_SC_NA_1 QU 结构化 + link-layer skeleton）
# IEC101 时间增强编解码器可用时为 codec-enhanced-plus 模式
_CODEC_ENHANCED_PLUS_PROTOCOLS: frozenset[str] = frozenset({
    "IEC101", "IEC_101",
})

# codebase-pending 协议集合（有 facade 定义但实现未就绪）
# MODBUS_RTU 在 PTY 可用时为 rtu-lightweight 模式，不再是 codebase-pending
# IEC101 在编解码器或 C binary 可用时不再是 codebase-pending
_CODABASE_PENDING_PROTOCOLS: frozenset[str] = frozenset({
    "BECKHOFF_ADS", "ADS",
})

# environment-pending 协议集合（实现可能就绪但运行环境不满足）
_ENVIRONMENT_PENDING_PROTOCOLS: frozenset[str] = frozenset({
    "GOOSE", "SV",
})


def create_facade_for_endpoint(
    endpoint: StarfishEndpointPlan,
    plan: StarfishServerPlan,
) -> FacadeEntry:
    """为单个端点创建对应的协议 facade。

    根据 endpoint.protocol 选择真实 facade、轻量级 facade、stub fallback 或
    unavailable 状态。已实现真实 server 的协议使用协议专用 facade（mode="real"），
    MQTT 使用轻量级端点（mode="mqtt-lightweight"），
    其他协议使用 in-memory stub（mode="stub"）。

    Args:
        endpoint: 端点契约信息。
        plan: 完整的 ServerPlan（用于 load_points）。

    Returns:
        包含 facade 实例、可用性状态和运行模式的 FacadeEntry。
    """
    protocol = _normalize_protocol(endpoint.protocol or "")

    if protocol == "HTTP_REST":
        from starfish.facade.http_rest_facade import HttpRestFacade
        facade: Any = HttpRestFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> real HTTP REST server (ThreadingHTTPServer)",
            mode="real",
        )

    if protocol == "MODBUS_TCP":
        from starfish.facade.modbus_tcp_facade import ModbusTcpFacade
        facade = ModbusTcpFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> real Modbus TCP server (FC03/FC06)",
            mode="real",
        )

    if protocol == "MQTT":
        from starfish.facade.mqtt_facade import MqttFacade
        facade = MqttFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> lightweight MQTT-like endpoint "
                   f"(TCP JSON line protocol, subscribe via polling queue; "
                   f"非完整 MQTT broker)",
            mode="mqtt-lightweight",
        )

    # OPC_UA: 依赖 open62541 C runner 子进程
    if protocol == "OPC_UA":
        from starfish.facade.opcua_facade import OpcUaFacade, probe_opcua_binary
        binary_ok, binary_reason = probe_opcua_binary()
        facade = OpcUaFacade()
        facade.load_points(plan)
        mode = facade.mode
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
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC104: 依赖 iec104_simulator_server C runner 子进程
    # 归一化：IEC_104 和 IEC104 均视为 IEC104
    if protocol in ("IEC_104", "IEC104"):
        from starfish.facade.iec104_facade import Iec104Facade, probe_iec104_binary
        binary_ok, binary_reason = probe_iec104_binary()
        facade = Iec104Facade()
        facade.load_points(plan)
        mode = facade.mode
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
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC61850_MMS: 依赖 iec61850_simulator_server C runner 子进程
    if protocol in ("IEC61850_MMS",):
        from starfish.facade.iec61850_mms_facade import (
            Iec61850MmsFacade,
            probe_iec61850_mms_binary,
        )
        binary_ok, binary_reason = probe_iec61850_mms_binary()
        facade = Iec61850MmsFacade()
        facade.load_points(plan)
        mode = facade.mode
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
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=available,
            reason=reason,
            mode=mode,
        )

    # IEC61850_REPORT: 依赖 iec61850_simulator_server + iec61850_report_runner
    if protocol in ("IEC61850_REPORT",):
        from starfish.facade.iec61850_report_facade import (
            Iec61850ReportFacade,
            probe_iec61850_report_binary,
        )
        binary_ok, binary_reason = probe_iec61850_report_binary()
        facade = Iec61850ReportFacade()
        facade.load_points(plan)
        mode = facade.mode
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
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=available,
            reason=reason,
            mode=mode,
        )

    # ── codebase-pending 协议 ────────────────────────────────────────────────────

    # IEC101: 串口链路协议
    # 模式分级（Round 16 更新）:
    #   codec-enhanced-plus > codec-enhanced > codec-skeleton >
    #   environment-pending > codebase-pending
    if protocol in ("IEC101", "IEC_101"):
        from starfish.facade.iec101_facade import Iec101Facade
        facade = Iec101Facade()
        facade.load_points(plan)
        current_mode = facade.mode
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
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=reason,
            mode=current_mode,
        )

    # MODBUS_RTU: 串口链路协议，与 MODBUS_TCP 不同（无 MBAP 头，使用 CRC）
    # 根据 PTY 可用性选择 rtu-lightweight 或 codebase-pending 模式
    if protocol == "MODBUS_RTU":
        from starfish.facade.modbus_rtu_facade import (
            ModbusRtuFacade,
            probe_modbus_rtu_binary,
        )
        pty_ok, pty_reason = probe_modbus_rtu_binary()
        if pty_ok:
            mode = "rtu-lightweight"
            facade = ModbusRtuFacade(mode="rtu-lightweight")
            reason = (
                f"protocol={protocol} -> Modbus RTU PTY lightweight mode "
                f"(local PTY simulation, 不等同真实串口)"
            )
        else:
            mode = "codebase-pending"
            facade = ModbusRtuFacade(mode="codebase-pending")
            reason = (
                f"protocol={protocol} -> Modbus RTU codebase-pending stub "
                f"(串口/PTY 链路环境未就绪: {pty_reason})"
            )
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=reason,
            mode=mode,
        )

    # Beckhoff ADS: 需 .NET/TwinCAT runtime
    if protocol in ("BECKHOFF_ADS", "ADS"):
        from starfish.facade.ads_facade import AdsFacade
        facade = AdsFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> Beckhoff ADS codebase-pending stub "
                   f"(.NET/TwinCAT runtime 未就绪，source_lab 有 dotnet 参考实现待迁移)",
            mode="codebase-pending",
        )

    # ── environment-pending 协议 ─────────────────────────────────────────────────

    # GOOSE: L2 veth 多播协议
    if protocol == "GOOSE":
        from starfish.facade.goose_facade import GooseFacade
        facade = GooseFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> GOOSE environment-pending stub "
                   f"(需 L2 veth 网络环境，不可 localhost 回环)",
            mode="environment-pending",
        )

    # SV (Sampled Values): L2 veth + PTP 时间同步
    if protocol == "SV":
        from starfish.facade.sv_facade import SvFacade
        facade = SvFacade()
        facade.load_points(plan)
        return FacadeEntry(
            endpoint=endpoint,
            facade=facade,
            available=True,
            reason=f"protocol={protocol} -> SV environment-pending stub "
                   f"(需 L2 veth 网络环境 + 硬件 PTP 时间同步)",
            mode="environment-pending",
        )

    # fallback: in-memory stub
    from starfish.facade.server_simulator_facade import ServerSimulatorFacade
    facade = ServerSimulatorFacade()
    facade.load_points(plan)
    return FacadeEntry(
        endpoint=endpoint,
        facade=facade,
        available=True,
        reason=f"protocol={protocol} -> in-memory stub facade (mode=stub)",
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


def get_lightweight_protocols() -> list[str]:
    """返回已实现轻量级端点的协议列表。

    MODBUS_RTU 动态决定：PTY 可用时为 rtu-lightweight 模式。

    Returns:
        协议名列表（如 ["MODBUS_RTU", "MQTT"]）。
    """
    result = sorted(_LIGHTWEIGHT_PROTOCOLS - {"MODBUS_RTU"})
    # 动态判断 MODBUS_RTU 是否在 lightweight 集合中
    from starfish.facade.modbus_rtu_facade import probe_modbus_rtu_binary
    pty_ok, _ = probe_modbus_rtu_binary()
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


def get_codec_skeleton_protocols() -> list[str]:
    """返回编解码器骨架就绪的协议列表（Round 14 新增）。

    这些协议有编解码器骨架实现，但缺少完整 server 能力。
    IEC101 动态决定：基础编解码器可用时（未升级到 codec-enhanced）为
    codec-skeleton 模式。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    from starfish.facade.iec101_facade import Iec101Facade
    if Iec101Facade().mode == "codec-skeleton":
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codec_enhanced_protocols() -> list[str]:
    """返回编解码器增强就绪的协议列表（Round 15 新增）。

    这些协议有增强编解码器实现（信息体 + ASDU 列表 + 链路层帧），
    但缺少完整 server 能力。
    IEC101 动态决定：增强编解码器全部组件可用时为 codec-enhanced 模式。
    注意：Round 16 引入 codec-enhanced-plus 高阶模式，当处于 plus 时
    仍视为已满足 codec-enhanced 增强基线。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    from starfish.facade.iec101_facade import Iec101Facade
    if Iec101Facade().mode in ("codec-enhanced", "codec-enhanced-plus"):
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codec_enhanced_plus_protocols() -> list[str]:
    """返回编解码器时间增强就绪的协议列表（Round 16 新增）。

    这些协议有时间增强编解码器（CP56Time2a + 带时标 TypeID +
    C_SC_NA_1 QU 结构化 + link-layer skeleton），但 link-layer 仅为
    skeleton，缺少完整 server 能力。
    IEC101 动态决定：时间增强编解码器全部组件可用时为
    codec-enhanced-plus 模式。

    Returns:
        协议名列表（如 ["IEC101", "IEC_101"]）。
    """
    result: list[str] = []
    from starfish.facade.iec101_facade import Iec101Facade
    if Iec101Facade().mode == "codec-enhanced-plus":
        result.extend(["IEC101", "IEC_101"])
        result.sort()
    return result


def get_codebase_pending_protocols() -> list[str]:
    """返回 codebase-pending 状态的协议列表。

    这些协议有 facade 定义，但实现代码（binary 或 Python 原生实现）尚未就绪。
    MODBUS_RTU 动态决定：PTY 可用时为 rtu-lightweight 模式，
    PTY 不可用时为 codebase-pending。
    IEC101 动态决定：编解码器和 binary 均不可用时为 codebase-pending。

    Returns:
        协议名列表（如 ["ADS", "BECKHOFF_ADS"]，
        含 "MODBUS_RTU" 当 PTY 不可用时，含 "IEC101"/"IEC_101" 当全部不可用时）。
    """
    result = sorted(_CODABASE_PENDING_PROTOCOLS)
    # 动态判断 MODBUS_RTU
    from starfish.facade.modbus_rtu_facade import probe_modbus_rtu_binary
    pty_ok, _ = probe_modbus_rtu_binary()
    if not pty_ok:
        result.append("MODBUS_RTU")
    # 动态判断 IEC101：编解码器和 binary 均不可用时为 codebase-pending
    from starfish.facade.iec101_facade import Iec101Facade
    if Iec101Facade().mode == "codebase-pending":
        result.append("IEC101")
        result.append("IEC_101")
    result.sort()
    return result


def get_environment_pending_protocols() -> list[str]:
    """返回 environment-pending 状态的协议列表。

    这些协议可能有实现代码，但运行环境（L2 网络、硬件等）不满足要求。
    IEC101 动态判断：C binary 已编译但编解码器不可用时为 environment-pending。

    Returns:
        协议名列表（如 ["GOOSE", "IEC101", "IEC_101", "SV"]）。
    """
    result = sorted(_ENVIRONMENT_PENDING_PROTOCOLS)
    # 动态判断 IEC101：binary 已编译但编解码器不可用且串口环境缺失时为 environment-pending
    from starfish.facade.iec101_facade import Iec101Facade
    if Iec101Facade().mode == "environment-pending":
        result.append("IEC101")
        result.append("IEC_101")
        result.sort()
    return result


def create_facades(plan: StarfishServerPlan) -> RuntimeRegistry:
    """根据 ServerPlan 创建完整的运行时注册表。

    为 plan 中的每个 endpoint 创建对应的 facade。

    Args:
        plan: 已加载并校验的 StarfishServerPlan。

    Returns:
        包含所有 facade 条目的 RuntimeRegistry。
    """
    registry = RuntimeRegistry(plan=plan)
    for ep in plan.endpoints:
        entry = create_facade_for_endpoint(ep, plan)
        registry.entries.append(entry)
    return registry


__all__ = [
    "RuntimeRegistry",
    "FacadeEntry",
    "create_facade_for_endpoint",
    "create_facades",
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
