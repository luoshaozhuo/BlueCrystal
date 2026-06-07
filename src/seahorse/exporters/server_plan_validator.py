"""seahorse ServerPlan 契约校验器。

本模块对 ServerPlan 的结构合法性和 Starfish 契约兼容性执行独立校验。
校验覆盖字段存在性、endpoints/points 结构完整性、capabilities 一致性
和 initial_values 可追溯性。校验结果以结构化 ValidationResult 返回。

校验项：
    1. scenario_id 存在且非空
    2. synthetic 标识存在（布尔类型）
    3. endpoints 非空
    4. 每个 endpoint 有 protocol、endpoint_id
    5. TCP 类协议 host/port 合法性
    6. points 非空
    7. 每个 point 有 point_id，以及 node_key/variable_key/value_type 至少一个
    8. capabilities 与 points 声明无冲突
    9. initial_values 可追溯到 points 中的 point_id

安全边界：
- 不得 import whale.ingest。
- 不得 import starfish；所有 Starfish 类型以 JSON/dict 契约隔离。
- 校验仅操作内存数据，无外部副作用。
"""
from __future__ import annotations

from seahorse.models.plan import ServerPlan
from seahorse.exporters.bundle_validator import ValidationResult


# TCP 类协议名称前缀集合，用于 host/port 合法性检查
_TCP_LIKE_PROTOCOLS: frozenset[str] = frozenset({
    "OPC_UA", "OPC_UA_TCP", "OPCUA", "opcua",
    "MODBUS_TCP", "MODBUS", "modbus",
    "MQTT", "mqtt",
    "HTTP", "http", "HTTPS", "https",
    "IEC_104", "IEC104", "DNP3_TCP",
    "ADS", "BECKHOFF_ADS",
    "TCP",
})


def _is_tcp_like(protocol: str) -> bool:
    """判断协议是否属于 TCP 类，需要 host/port 校验。

    通过协议名前缀匹配判断，不区分大小写。

    Args:
        protocol: 协议名称字符串。

    Returns:
        True 表示该协议需要合法的 host 和 port。
    """
    upper = protocol.upper()
    if upper in _TCP_LIKE_PROTOCOLS:
        return True
    for known in _TCP_LIKE_PROTOCOLS:
        if upper.startswith(known):
            return True
    return False


def _validate_host(host: str) -> bool:
    """简单校验 host 字段非空且至少包含分隔符或非空白字符。

    不做完整 IP 地址或域名解析，仅确保字段不为纯空白。
    完整解析由 Starfish runtime 在启动时完成。

    Args:
        host: 主机地址字符串。

    Returns:
        True 表示 host 格式可接受。
    """
    return bool(host and host.strip())


def _validate_port(port: int) -> bool:
    """校验 port 在合法 TCP 端口范围内。

    Args:
        port: 端口号。

    Returns:
        True 表示 port 在 1-65535 范围内。
    """
    return 1 <= port <= 65535


def validate_server_plan(server_plan: ServerPlan) -> ValidationResult:
    """对 ServerPlan 执行 Starfish 契约兼容性校验。

    按顺序执行所有检查项，单项错误不影响后续检查的执行。

    Args:
        server_plan: Seahorse 生成的完整 ServerPlan 实例。

    Returns:
        包含所有检查明细的 ValidationResult 实例。
    """
    result = ValidationResult()

    # 1. scenario_id 存在性
    if not server_plan.scenario_id:
        result.add_error("ServerPlan.scenario_id 缺失或为空")
    else:
        result.add_pass(f"scenario_id 存在: {server_plan.scenario_id}")

    # 2. synthetic 标识存在
    if not isinstance(server_plan.synthetic, bool):
        result.add_error(
            f"ServerPlan.synthetic 应为布尔类型，当前类型: {type(server_plan.synthetic).__name__}"
        )
    elif server_plan.synthetic is False:
        result.add_warning(
            "ServerPlan.synthetic=False，该计划可能不是合成数据，请确认来源"
        )
    else:
        result.add_pass("synthetic 标识存在且为 True")

    # 3. endpoints 非空
    if not server_plan.endpoints:
        result.add_error("ServerPlan.endpoints 为空，至少需要一个端点")
    else:
        result.add_pass(f"endpoints 包含 {len(server_plan.endpoints)} 个端点")

    # 4. 每个 endpoint 有 protocol、endpoint_id
    for i, ep in enumerate(server_plan.endpoints):
        if not ep.protocol:
            result.add_error(f"endpoints[{i}] 缺少 protocol")
        if not ep.endpoint_id:
            result.add_error(f"endpoints[{i}] 缺少 endpoint_id")
        else:
            result.add_pass(
                f"endpoints[{i}] ({ep.endpoint_id}) protocol={ep.protocol}"
            )

    # 5. TCP 类协议的 host/port 合法性
    for i, ep in enumerate(server_plan.endpoints):
        if _is_tcp_like(ep.protocol):
            ep_host = ep.host or ep.bind_host
            ep_port = ep.port or ep.bind_port
            if not _validate_host(ep_host):
                result.add_error(
                    f"endpoints[{i}] ({ep.endpoint_name or ep.endpoint_id}) "
                    f"协议 {ep.protocol} 为 TCP 类协议，但 host 无效: '{ep_host}'"
                )
            if not _validate_port(ep_port):
                result.add_error(
                    f"endpoints[{i}] ({ep.endpoint_name or ep.endpoint_id}) "
                    f"协议 {ep.protocol} 为 TCP 类协议，但 port 无效: {ep_port}"
                )
            if _validate_host(ep_host) and _validate_port(ep_port):
                result.add_pass(
                    f"endpoints[{i}] TCP host/port 合法: {ep_host}:{ep_port}"
                )

    # 6. points 非空
    if not server_plan.points:
        result.add_error("ServerPlan.points 为空，至少需要一个点位")
    else:
        result.add_pass(f"points 包含 {len(server_plan.points)} 个点位")

    # 7. 每个 point 有 point_id 及至少一个契约标识字段
    for i, pt in enumerate(server_plan.points):
        if not pt.point_id:
            result.add_error(f"points[{i}] 缺少 point_id")
            continue
        # node_key / variable_key / value_type 至少一个非空
        has_key = bool(pt.node_key and pt.node_key.strip())
        has_var = bool(pt.variable_key and pt.variable_key.strip())
        has_vt = bool(pt.value_type and pt.value_type.strip())
        if not (has_key or has_var or has_vt):
            result.add_warning(
                f"points[{i}] (point_id={pt.point_id}) 缺少 node_key、"
                f"variable_key 和 value_type（至少需要一个非空）"
            )
        else:
            result.add_pass(f"points[{i}] (point_id={pt.point_id}) 契约字段完整")

    # 8. capabilities 与 points 声明无冲突
    _check_capability_point_conflict(server_plan, result)

    # 9. initial_values 可追溯到 point
    _check_initial_values_traceability(server_plan, result)

    return result


def _check_capability_point_conflict(
    server_plan: ServerPlan,
    result: ValidationResult,
) -> None:
    """检查 capabilities 声明与 points 实际 access_mode 是否存在冲突。

    例如：capabilities 中未声明 "WRITE" 但存在 access_mode="WO" 或 "RW"
    的 point，则视为不匹配。

    Args:
        server_plan: 被校验的 ServerPlan。
        result: 校验结果对象，结果直接追加。
    """
    caps_upper = {c.upper() for c in server_plan.capabilities}

    if not caps_upper:
        result.add_warning("capabilities 为空，无法判断与 points 的兼容性")
        return

    # 检查 write 能力
    has_write = "WRITE" in caps_upper or "RW" in caps_upper
    write_points = [
        pt.point_id
        for pt in server_plan.points
        if pt.access_mode.upper() in ("WO", "RW")
    ]
    if write_points and not has_write:
        result.add_warning(
            f"points 中存在 {len(write_points)} 个可写点位（WO/RW），"
            f"但 capabilities 未声明 WRITE 能力: {write_points[:3]}..."
        )

    # 检查 read 能力
    has_read = "READ" in caps_upper or "RW" in caps_upper
    read_points = [
        pt.point_id
        for pt in server_plan.points
        if pt.access_mode.upper() in ("RO", "RW")
    ]
    if read_points and not has_read:
        result.add_warning(
            f"points 中存在 {len(read_points)} 个可读点位（RO/RW），"
            f"但 capabilities 未声明 READ 能力: {read_points[:3]}..."
        )

    if (not write_points or has_write) and (not read_points or has_read):
        result.add_pass(
            f"capabilities ({sorted(caps_upper)}) 与 points access_mode 无冲突"
        )


def _check_initial_values_traceability(
    server_plan: ServerPlan,
    result: ValidationResult,
) -> None:
    """检查 initial_values 中每个 key 是否可追溯到 points 中的 point_id。

    不可追溯的 key 记录为警告，不阻止校验通过，因为可能是 Starfish
    运行时扩展字段。

    Args:
        server_plan: 被校验的 ServerPlan。
        result: 校验结果对象，结果直接追加。
    """
    if not server_plan.initial_values:
        result.add_pass("initial_values 为空，跳过追溯检查")
        return

    point_ids: set[str] = {pt.point_id for pt in server_plan.points if pt.point_id}
    orphan_keys = [
        key for key in server_plan.initial_values if key not in point_ids
    ]
    if orphan_keys:
        result.add_warning(
            f"initial_values 中有 {len(orphan_keys)} 个 key 无法追溯到 points "
            f"中的 point_id: {orphan_keys[:5]}..."
        )
    else:
        result.add_pass(
            f"initial_values 全部 {len(server_plan.initial_values)} 个 key "
            "可追溯到 points 中的 point_id"
        )


def validate_server_plan_from_dict(data: dict) -> ValidationResult:
    """从 JSON/dict 数据重建 ServerPlan 并校验。

    不依赖 seahorse 模型模块以外的类型，用于已有 JSON 契约文件
    的后加载场景。

    Args:
        data: 包含 ServerPlan 序列化字段的 dict。

    Returns:
        ValidationResult 实例。
    """
    from seahorse.exporters.bundle_validator import ValidationResult

    result = ValidationResult()

    # 1. scenario_id 存在性
    scenario_id = data.get("scenario_id", "")
    if not scenario_id:
        result.add_error("scenario_id 缺失或为空")
    else:
        result.add_pass(f"scenario_id 存在: {scenario_id}")

    # 2. synthetic 标识
    synthetic = data.get("synthetic")
    if synthetic is None:
        result.add_error("synthetic 字段缺失")
    elif not isinstance(synthetic, bool):
        result.add_error(f"synthetic 应为布尔类型，实际: {type(synthetic).__name__}")
    elif synthetic is False:
        result.add_warning("synthetic=False，请确认数据来源")
    else:
        result.add_pass("synthetic 标识存在且为 True")

    # 3. endpoints 非空
    endpoints = data.get("endpoints", [])
    if not endpoints:
        result.add_error("endpoints 为空")
    else:
        result.add_pass(f"endpoints 包含 {len(endpoints)} 个端点")

    # 4. 每个 endpoint 有 protocol、endpoint_id
    for i, ep in enumerate(endpoints):
        if not ep.get("protocol"):
            result.add_error(f"endpoints[{i}] 缺少 protocol")
        if not ep.get("endpoint_id"):
            result.add_error(f"endpoints[{i}] 缺少 endpoint_id")

    # 5. TCP host/port 检查
    for i, ep in enumerate(endpoints):
        protocol = ep.get("protocol", "")
        if _is_tcp_like(protocol):
            ep_host = ep.get("host", "") or ep.get("bind_host", "")
            ep_port = ep.get("port", 0) or ep.get("bind_port", 0)
            if not _validate_host(ep_host):
                result.add_error(
                    f"endpoints[{i}] 协议 {protocol} 的 host 无效: '{ep_host}'"
                )
            if not _validate_port(ep_port):
                result.add_error(
                    f"endpoints[{i}] 协议 {protocol} 的 port 无效: {ep_port}"
                )

    # 6. points 非空
    points = data.get("points", [])
    if not points:
        result.add_error("points 为空")
    else:
        result.add_pass(f"points 包含 {len(points)} 个点位")

    # 7. 每个 point 有 point_id 及契约字段
    for i, pt in enumerate(points):
        if not pt.get("point_id"):
            result.add_error(f"points[{i}] 缺少 point_id")
        else:
            has_key = bool(pt.get("node_key", ""))
            has_var = bool(pt.get("variable_key", ""))
            has_vt = bool(pt.get("value_type", ""))
            if not (has_key or has_var or has_vt):
                result.add_warning(
                    f"points[{i}] 缺少 node_key/variable_key/value_type"
                )

    # 8. capabilities 与 points 不冲突
    caps = data.get("capabilities", [])
    caps_upper = {c.upper() for c in caps} if isinstance(caps, list) else set()
    has_write = "WRITE" in caps_upper or "RW" in caps_upper
    has_read = "READ" in caps_upper or "RW" in caps_upper

    if caps and isinstance(caps, list):
        write_pts = [
            pt.get("point_id", "")
            for pt in points
            if pt.get("access_mode", "").upper() in ("WO", "RW")
        ]
        if write_pts and not has_write:
            result.add_warning(
                f"points 中 {len(write_pts)} 个可写点位但 capabilities 未声明 WRITE"
            )
        read_pts = [
            pt.get("point_id", "")
            for pt in points
            if pt.get("access_mode", "").upper() in ("RO", "RW")
        ]
        if read_pts and not has_read:
            result.add_warning(
                f"points 中 {len(read_pts)} 个可读点位但 capabilities 未声明 READ"
            )

    # 9. initial_values 可追溯
    initial_values = data.get("initial_values", {})
    if isinstance(initial_values, dict) and initial_values:
        point_ids = {pt.get("point_id", "") for pt in points}
        orphans = [k for k in initial_values if k not in point_ids]
        if orphans:
            result.add_warning(
                f"initial_values 中 {len(orphans)} 个 key 无法追溯到 points"
            )

    return result


__all__ = [
    "validate_server_plan",
    "validate_server_plan_from_dict",
]
