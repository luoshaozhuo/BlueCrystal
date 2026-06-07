"""Starfish probe —— 最小启动-健康-读取探测。

对 facade 执行最简可用性探测：
1. 启动 facade（如未启动）。
2. 执行 health 检查。
3. 加载点位（如需要）。
4. 读取一个或多个点位。
5. 返回 PASS/FAIL/NOT_RUN + reason。

探针不负责：
- 长时间运行或压测。
- 替代生产级健康检查。
- 模拟并发客户端行为。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProbeResult:
    """探针执行结果。

    Attributes:
        status: 探测结论（"PASS" / "FAIL" / "NOT_RUN"）。
        protocol: 协议名（取自 facade 或 endpoint）。
        mode: 运行模式（"real" / "mqtt-lightweight" / "stub" / "unavailable"）。
        scenario_id: 关联的场景标识（如有）。
        endpoint_id: 关联的端点标识（如有）。
        reason: 非 PASS 时的原因说明。
        details: 额外的探测详情（如 health、read 结果）。
    """

    status: str = "NOT_RUN"
    protocol: str = ""
    mode: str = ""
    scenario_id: str = ""
    endpoint_id: str = ""
    reason: str = ""
    details: dict[str, Any] = field(default_factory=dict)


def probe_facade(
    facade: Any,
    plan: Any | None = None,
    endpoint_id: str = "",
    read_point_ids: list[str] | None = None,
    skip_start: bool = False,
) -> ProbeResult:
    """对单个 facade 执行最小可用性探测。

    探测步骤：
        1. 如 plan 非 None，调用 facade.load_points(plan)。
        2. 如未启动且 skip_start 为 False，调用 facade.start()。
        3. 调用 facade.health() 获取健康状态。
        4. 调用 facade.read() 读取点位值（指定或全部）。
        5. 任一步骤失败则返回 FAIL。

    Args:
        facade: facade 实例（需有 start/stop/health/load_points/read 接口）。
        plan: StarfishServerPlan（可选，提供时执行 load_points）。
        endpoint_id: 端点标识（用于输出）。
        read_point_ids: 要读取的点位 ID 列表，None 表示全部。
        skip_start: True 时跳过 start 步骤（facade 已由外部启动）。

    Returns:
        ProbeResult 包含状态、模式、协议、原因和详情。
    """
    result = ProbeResult()

    # 收集 facade 元信息
    try:
        result.protocol = getattr(facade, "protocol", "")
        result.mode = getattr(facade, "mode", "")
    except Exception:
        pass
    result.endpoint_id = endpoint_id
    if plan is not None:
        try:
            result.scenario_id = getattr(plan, "scenario_id", "")
        except Exception:
            pass

    # 步骤 1: load_points（可选，必须在 start 前执行。
    # 部分 facade（如 OpcUaFacade 在 real 模式下）的 start 依赖已加载的 plan）
    if plan is not None:
        try:
            facade.load_points(plan)
            result.details["load_points"] = "ok"
        except Exception as exc:
            result.status = "FAIL"
            result.reason = f"facade.load_points() 失败: {exc}"
            result.details["step_failed"] = "load_points"
            return result

    # 步骤 2: start
    # 注意: unavailable 模式的 facade 探测仍会执行 start/health/read，
    # 结果中的 mode 字段会反映真实模式（"unavailable" / "real" / ...）。

    if not skip_start:
        try:
            facade.start()
        except Exception as exc:
            result.status = "FAIL"
            result.reason = f"facade.start() 失败: {exc}"
            result.details["step_failed"] = "start"
            return result

    # 步骤 3: health
    try:
        h = facade.health()
        result.details["health"] = h
    except Exception as exc:
        result.status = "FAIL"
        result.reason = f"facade.health() 失败: {exc}"
        result.details["step_failed"] = "health"
        return result

    # 步骤 4: read
    try:
        values = facade.read(read_point_ids)
        result.details["read"] = {
            "point_count": len(values),
            "sample": dict(list(values.items())[:5]),
        }
    except Exception as exc:
        result.status = "FAIL"
        result.reason = f"facade.read() 失败: {exc}"
        result.details["step_failed"] = "read"
        return result

    # 全部通过
    result.status = "PASS"
    result.reason = "probe 全部步骤通过 (load_points/start/health/read)"
    return result


__all__ = ["ProbeResult", "probe_facade"]
