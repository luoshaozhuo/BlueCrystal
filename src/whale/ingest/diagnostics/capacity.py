"""Ingest runtime capacity —— 轻量端点/点位/读取容量扫描。

对 endpoint_count / point_count / read_count 做轻量扫描，
输出 PASS/FAIL/NOT_RUN、max_tested_points 和 reason。
不做生产级容量规划或压测。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CapacityResult:
    """容量扫描结果。"""

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


_CAPACITY_SUPPORTED: frozenset[str] = frozenset({
    "HTTP_REST",
    "MODBUS_TCP",
    "MQTT",
    "OPC_UA",
    "IEC104",
    "IEC61850_MMS",
    "IEC61850_REPORT",
    "MODBUS_RTU",
})


def capacity_scan(
    facade: Any,
    point_ids: list[str] | None = None,
    read_count: int = 10,
    endpoint_id: str = "",
    scenario_id: str = "",
) -> CapacityResult:
    """对单个 driver 执行轻量容量扫描。

    Args:
        facade: 运行时 driver。
        point_ids: 指定读取点位，`None` 表示全部。
        read_count: read 调用次数。
        endpoint_id: 端点标识。
        scenario_id: 场景标识。

    Returns:
        `CapacityResult`，包含扫描统计和执行状态。
    """
    result = CapacityResult()
    result.endpoint_id = endpoint_id
    result.scenario_id = scenario_id
    result.read_count = read_count

    try:
        result.protocol = getattr(facade, "protocol", "")
        result.mode = getattr(facade, "mode", "")
    except Exception:
        pass

    if result.protocol not in _CAPACITY_SUPPORTED:
        result.status = "NOT_RUN"
        result.reason = (
            f"协议 '{result.protocol}' 不在容量扫描支持列表中 "
            f"(仅支持 {sorted(_CAPACITY_SUPPORTED)})"
        )
        return result

    if result.mode == "unavailable":
        result.status = "NOT_RUN"
        result.reason = (
            f"协议 '{result.protocol}' 当前为 unavailable 模式，"
            f"容量扫描不执行（environment-pending）。"
            f"原因: {getattr(facade, 'binary_reason', 'native binary 缺失')}"
        )
        return result

    try:
        health = facade.health()
        result.endpoint_count = health.get("endpoint_count", 0)
        result.point_count = health.get("point_count", 0)
    except Exception as exc:
        result.status = "FAIL"
        result.reason = f"facade.health() 失败: {exc}"
        return result

    max_points = 0
    failed_reads = 0
    for _ in range(read_count):
        try:
            values = facade.read(point_ids)
            max_points = max(max_points, len(values))
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
