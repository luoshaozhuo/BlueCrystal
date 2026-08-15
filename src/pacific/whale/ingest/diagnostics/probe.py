"""Ingest runtime probe —— 最小启动-健康-读取探测。

对统一 driver 执行最简可用性探测：
1. 启动 driver（如未启动）。
2. 执行 health 检查。
3. 加载点位（如需要）。
4. 读取一个或多个点位。
5. 返回 PASS/FAIL/NOT_RUN + reason。

探针不负责：
- 长时间运行或压测。
- 替代生产级健康检查。
- 模拟并发客户端行为。

边界说明：
- 该模块位于 ingest 侧，只消费统一 runtime 接口。
- 不直接 import `starfish`，避免把诊断工具反向耦合进 runtime 核心。
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
        mode: 运行模式。
        scenario_id: 关联的场景标识（如有）。
        endpoint_id: 关联的端点标识（如有）。
        reason: 非 PASS 时的原因说明。
        details: 额外探测详情（如 health、read 结果）。
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
    """对单个 driver 执行最小可用性探测。

    Args:
        facade: 具备 start/health/load_points/read 接口的运行时 driver。
        plan: 可选场景计划，提供时先执行 `load_points`。
        endpoint_id: 端点标识。
        read_point_ids: 指定读取的点位列表，`None` 表示读取全部。
        skip_start: 为 True 时跳过 `start()`，适合外部已启动场景。

    Returns:
        `ProbeResult`，包含状态、原因与步骤详情。
    """
    result = ProbeResult()

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

    if plan is not None:
        try:
            facade.load_points(plan)
            result.details["load_points"] = "ok"
        except Exception as exc:
            result.status = "FAIL"
            result.reason = f"facade.load_points() 失败: {exc}"
            result.details["step_failed"] = "load_points"
            return result

    if not skip_start:
        try:
            facade.start()
        except Exception as exc:
            result.status = "FAIL"
            result.reason = f"facade.start() 失败: {exc}"
            result.details["step_failed"] = "start"
            return result

    try:
        health = facade.health()
        result.details["health"] = health
    except Exception as exc:
        result.status = "FAIL"
        result.reason = f"facade.health() 失败: {exc}"
        result.details["step_failed"] = "health"
        return result

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

    result.status = "PASS"
    result.reason = "probe 全部步骤通过 (load_points/start/health/read)"
    return result


__all__ = ["ProbeResult", "probe_facade"]
