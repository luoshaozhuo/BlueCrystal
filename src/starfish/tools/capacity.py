"""Starfish capacity —— 轻量端点/点位/读取容量扫描。

对 endpoint_count / point_count / read_count 做轻量扫描，
输出 PASS/FAIL/NOT_RUN、max_tested_points 和 reason。
不做生产级容量规划或压测。

支持 HTTP_REST / MODBUS_TCP / MQTT / OPC_UA / IEC104 / IEC61850_MMS / IEC61850_REPORT
已实现 facade 的容量扫描。
IEC61850_MMS / IEC61850_REPORT 在 unavailable 或 report-lightweight 模式下
返回 NOT_RUN + environment-pending reason。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapacityResult:
    """容量扫描结果。

    Attributes:
        status: 扫描结论（"PASS" / "FAIL" / "NOT_RUN"）。
        protocol: 协议名。
        mode: 运行模式。
        scenario_id: 场景标识。
        endpoint_id: 端点标识。
        endpoint_count: 端点总数。
        point_count: 点位总数。
        max_tested_points: 实际测试的最大点位数。
        read_count: 执行的 read 调用次数。
        reason: 非 PASS 时的原因说明。
        details: 额外详情（如各 endpoint 统计）。
    """

    status: str = "NOT_RUN"
    protocol: str = ""
    mode: str = ""
    scenario_id: str = ""
    endpoint_id: str = ""
    endpoint_count: int = 0
    point_count: int = 0
    max_tested_points: int = 0
    read_count: int = 0
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


# 容量扫描支持的协议（已实现 real / lightweight / native-runner 的协议）
_CAPACITY_SUPPORTED: frozenset[str] = frozenset({
    "HTTP_REST", "MODBUS_TCP", "MQTT", "OPC_UA", "IEC104",
    "IEC61850_MMS", "IEC61850_REPORT", "MODBUS_RTU",
})


def capacity_scan(
    facade: Any,
    point_ids: list[str] | None = None,
    read_count: int = 10,
    endpoint_id: str = "",
    scenario_id: str = "",
) -> CapacityResult:
    """对单个 facade 执行轻量容量扫描。

    扫描步骤：
        1. 收集 facade 元信息（protocol/mode/endpoint/point 数量）。
        2. 如果 facade 协议不在支持列表中，返回 NOT_RUN。
        3. 调用 facade.health() 获取点位数。
        4. 按 read_count 次调用 facade.read()，每次测量返回的点位数。
        5. 记录 max_tested_points 和总 read_count。

    Args:
        facade: facade 实例。
        point_ids: 读取的点位 ID 列表，None 表示全部。
        read_count: read 调用次数，默认 10。
        endpoint_id: 端点标识。
        scenario_id: 场景标识。

    Returns:
        CapacityResult 包含扫描统计和执行状态。
    """
    result = CapacityResult()
    result.endpoint_id = endpoint_id
    result.scenario_id = scenario_id
    result.read_count = read_count

    # 收集元信息
    try:
        result.protocol = getattr(facade, "protocol", "")
        result.mode = getattr(facade, "mode", "")
    except Exception:
        pass

    # 检查协议是否在支持列表中
    if result.protocol not in _CAPACITY_SUPPORTED:
        result.status = "NOT_RUN"
        result.reason = (
            f"协议 '{result.protocol}' 不在容量扫描支持列表中 "
            f"(仅支持 {sorted(_CAPACITY_SUPPORTED)})"
        )
        return result

    # 检查 facade 是否为 unavailable 模式（native binary 缺失）
    if result.mode == "unavailable":
        result.status = "NOT_RUN"
        result.reason = (
            f"协议 '{result.protocol}' 当前为 unavailable 模式，"
            f"容量扫描不执行（environment-pending）。"
            f"原因: {getattr(facade, 'binary_reason', 'native binary 缺失')}"
        )
        return result

    # 获取 health 信息以统计点数
    try:
        h = facade.health()
        result.endpoint_count = h.get("endpoint_count", 0)
        result.point_count = h.get("point_count", 0)
    except Exception as exc:
        result.status = "FAIL"
        result.reason = f"facade.health() 失败: {exc}"
        return result

    # 执行 N 次 read，记录最大 points 数量
    max_points = 0
    failed_reads = 0
    for i in range(read_count):
        try:
            values = facade.read(point_ids)
            point_count = len(values)
            if point_count > max_points:
                max_points = point_count
        except Exception:
            failed_reads += 1

    result.max_tested_points = max_points

    if failed_reads > 0:
        result.status = "FAIL"
        result.reason = (
            f"容量扫描: {failed_reads}/{read_count} 次 read 失败, "
            f"max_tested_points={max_points}"
        )
        result.details["failed_reads"] = failed_reads
        return result

    result.status = "PASS"
    result.reason = (
        f"容量扫描通过: {read_count} 次 read, "
        f"max_tested_points={max_points}, "
        f"endpoint_count={result.endpoint_count}, "
        f"point_count={result.point_count}"
    )
    return result


__all__ = ["CapacityResult", "capacity_scan"]
