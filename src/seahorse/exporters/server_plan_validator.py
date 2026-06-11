"""seahorse ServerConfig 契约校验器。

本模块对 ServerConfig 的结构合法性和 Starfish 契约兼容性执行独立校验。
校验覆盖顶层元数据、server members、endpoints/points 结构完整性、
capabilities 一致性和 initial_values 可追溯性。
"""
from __future__ import annotations

from seahorse.exporters.bundle_validator import ValidationResult
from seahorse.models.plan import ServerConfig, ServerMemberConfig


_TCP_LIKE_PROTOCOLS: frozenset[str] = frozenset({
    "OPC_UA", "OPC_UA_TCP", "OPCUA", "OPCUA_TCP",
    "MODBUS_TCP", "MODBUS", "MQTT", "HTTP", "HTTPS",
    "IEC_104", "IEC104", "DNP3_TCP", "ADS", "BECKHOFF_ADS", "TCP",
})


def _is_tcp_like(protocol: str) -> bool:
    """判断协议是否属于 TCP 类，需要 host/port 校验。"""
    upper = protocol.upper()
    return upper in _TCP_LIKE_PROTOCOLS or any(upper.startswith(item) for item in _TCP_LIKE_PROTOCOLS)


def _validate_host(host: str) -> bool:
    """简单校验 host 字段非空。"""
    return bool(host and host.strip())


def _validate_port(port: int) -> bool:
    """校验 port 在合法 TCP 端口范围内。"""
    return 1 <= port <= 65535


def validate_server_config(server_config: ServerConfig) -> ValidationResult:
    """对 ServerConfig 执行 Starfish 契约兼容性校验。"""
    result = ValidationResult()

    if not server_config.scenario_id:
        result.add_error("ServerConfig.scenario_id 缺失或为空")
    else:
        result.add_pass(f"scenario_id 存在: {server_config.scenario_id}")

    if not isinstance(server_config.synthetic, bool):
        result.add_error(
            f"ServerConfig.synthetic 应为布尔类型，当前类型: {type(server_config.synthetic).__name__}"
        )
    elif server_config.synthetic is False:
        result.add_warning("ServerConfig.synthetic=False，请确认数据来源")
    else:
        result.add_pass("synthetic 标识存在且为 True")

    if not server_config.servers:
        result.add_error("ServerConfig.servers 为空，至少需要一个 server member")
        return result

    result.add_pass(f"servers 包含 {len(server_config.servers)} 个 server members")
    for index, server in enumerate(server_config.servers):
        _validate_server_member(server, index, result)
    return result


def _validate_server_member(
    server: ServerMemberConfig,
    index: int,
    result: ValidationResult,
) -> None:
    """校验单个 server member 的 endpoint、point 和能力声明。"""
    label = server.server_id or server.server_name or f"servers[{index}]"
    if not server.endpoints:
        result.add_error(f"servers[{index}] ({label}) endpoints 为空")
    else:
        result.add_pass(f"servers[{index}] ({label}) 含 {len(server.endpoints)} 个 endpoints")

    for ep_index, ep in enumerate(server.endpoints):
        if not ep.protocol:
            result.add_error(f"servers[{index}].endpoints[{ep_index}] 缺少 protocol")
        if not ep.endpoint_id:
            result.add_error(f"servers[{index}].endpoints[{ep_index}] 缺少 endpoint_id")
        if _is_tcp_like(ep.protocol):
            ep_host = ep.host or ep.bind_host
            ep_port = ep.port or ep.bind_port
            if not _validate_host(ep_host):
                result.add_error(
                    f"servers[{index}].endpoints[{ep_index}] 协议 {ep.protocol} 的 host 无效: '{ep_host}'"
                )
            if not _validate_port(ep_port):
                result.add_error(
                    f"servers[{index}].endpoints[{ep_index}] 协议 {ep.protocol} 的 port 无效: {ep_port}"
                )

    if not server.points:
        result.add_error(f"servers[{index}] ({label}) points 为空")
    else:
        result.add_pass(f"servers[{index}] ({label}) 含 {len(server.points)} 个 points")

    for pt_index, pt in enumerate(server.points):
        if not pt.point_id:
            result.add_error(f"servers[{index}].points[{pt_index}] 缺少 point_id")
            continue
        has_key = bool(pt.node_key and pt.node_key.strip())
        has_var = bool(pt.variable_key and pt.variable_key.strip())
        has_vt = bool(pt.value_type and pt.value_type.strip())
        if not (has_key or has_var or has_vt):
            result.add_warning(
                f"servers[{index}].points[{pt_index}] (point_id={pt.point_id}) 缺少 node_key/variable_key/value_type"
            )

    caps_upper = {c.upper() for c in server.capabilities}
    if not caps_upper:
        result.add_warning(f"servers[{index}] ({label}) capabilities 为空")
    else:
        write_points = [pt.point_id for pt in server.points if pt.access_mode.upper() in ("WO", "RW")]
        read_points = [pt.point_id for pt in server.points if pt.access_mode.upper() in ("RO", "RW")]
        has_write = "WRITE" in caps_upper or "RW" in caps_upper
        has_read = "READ" in caps_upper or "RW" in caps_upper
        if write_points and not has_write:
            result.add_warning(f"servers[{index}] ({label}) 有可写点位但未声明 WRITE 能力")
        if read_points and not has_read:
            result.add_warning(f"servers[{index}] ({label}) 有可读点位但未声明 READ 能力")
        if (not write_points or has_write) and (not read_points or has_read):
            result.add_pass(f"servers[{index}] ({label}) capabilities 与 points access_mode 无冲突")

    if not server.initial_values:
        result.add_pass(f"servers[{index}] ({label}) initial_values 为空，跳过追溯检查")
        return

    point_ids = {pt.point_id for pt in server.points if pt.point_id}
    orphan_keys = [key for key in server.initial_values if key not in point_ids]
    if orphan_keys:
        result.add_warning(
            f"servers[{index}] ({label}) initial_values 中有 {len(orphan_keys)} 个 key 无法追溯到 points"
        )
    else:
        result.add_pass(
            f"servers[{index}] ({label}) initial_values 全部 {len(server.initial_values)} 个 key 可追溯到 points"
        )


def validate_server_config_from_dict(data: dict) -> ValidationResult:
    """从 JSON/dict 数据直接校验 ServerConfig 契约。"""
    result = ValidationResult()

    scenario_id = data.get("scenario_id", "")
    if not scenario_id:
        result.add_error("scenario_id 缺失或为空")
    else:
        result.add_pass(f"scenario_id 存在: {scenario_id}")

    synthetic = data.get("synthetic")
    if synthetic is None:
        result.add_error("synthetic 字段缺失")
    elif not isinstance(synthetic, bool):
        result.add_error(f"synthetic 应为布尔类型，实际: {type(synthetic).__name__}")

    servers = data.get("servers")
    if servers is None and ("endpoints" in data or "points" in data):
        servers = [
            {
                "server_id": f"{scenario_id}_server" if scenario_id else "",
                "server_name": data.get("server_name", data.get("config_name", "")),
                "endpoints": data.get("endpoints", []),
                "points": data.get("points", []),
                "capabilities": data.get("capabilities", []),
                "update_policy": data.get("update_policy", {}),
                "initial_values": data.get("initial_values", {}),
            }
        ]
        result.add_warning("检测到旧版扁平 ServerConfig dict，已按单 server 结构归一校验")
    if servers is None:
        servers = []
    if not isinstance(servers, list) or not servers:
        result.add_error("servers 为空")
        return result

    result.add_pass(f"servers 包含 {len(servers)} 个 server members")
    for index, server in enumerate(servers):
        endpoints = server.get("endpoints", [])
        points = server.get("points", [])
        if not endpoints:
            result.add_error(f"servers[{index}] endpoints 为空")
        if not points:
            result.add_error(f"servers[{index}] points 为空")
        for ep_index, ep in enumerate(endpoints):
            protocol = ep.get("protocol", "")
            if not protocol:
                result.add_error(f"servers[{index}].endpoints[{ep_index}] 缺少 protocol")
            if not ep.get("endpoint_id"):
                result.add_error(f"servers[{index}].endpoints[{ep_index}] 缺少 endpoint_id")
            if _is_tcp_like(protocol):
                ep_host = ep.get("host", "") or ep.get("bind_host", "")
                ep_port = ep.get("port", 0) or ep.get("bind_port", 0)
                if not _validate_host(ep_host):
                    result.add_error(f"servers[{index}].endpoints[{ep_index}] host 无效: '{ep_host}'")
                if not _validate_port(ep_port):
                    result.add_error(f"servers[{index}].endpoints[{ep_index}] port 无效: {ep_port}")
        for pt_index, pt in enumerate(points):
            if not pt.get("point_id"):
                result.add_error(f"servers[{index}].points[{pt_index}] 缺少 point_id")
        initial_values = server.get("initial_values", {})
        if isinstance(initial_values, dict) and initial_values:
            point_ids = {pt.get("point_id", "") for pt in points}
            orphans = [key for key in initial_values if key not in point_ids]
            if orphans:
                result.add_warning(
                    f"servers[{index}] initial_values 中有 {len(orphans)} 个 key 无法追溯到 points"
                )
    return result


__all__ = [
    "validate_server_config",
    "validate_server_config_from_dict",
]
