"""Starfish profile —— 对 read 执行 N 次采样并统计耗时。

profile 不替代生产级性能测试，不做伪性能结论。
仅提供本地点位读取的轻量耗时统计。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProfileResult:
    """Profile 采样结果。

    Attributes:
        protocol: 协议名。
        mode: 运行模式。
        scenario_id: 场景标识。
        endpoint_id: 端点标识。
        iterations: 采样次数。
        duration_ms: 全部采样总耗时（毫秒）。
        stats: 统计信息 dict，包含 count/min/max/avg（单位 ms）。
        samples: 每次采样的耗时列表（毫秒）。
        status: 执行状态（"PASS" / "FAIL" / "NOT_RUN"）。
        reason: 非 PASS 时的原因说明。
    """

    protocol: str = ""
    mode: str = ""
    scenario_id: str = ""
    endpoint_id: str = ""
    iterations: int = 0
    duration_ms: float = 0.0
    stats: dict[str, Any] = field(default_factory=dict)
    samples: list[float] = field(default_factory=list)
    status: str = "NOT_RUN"
    reason: str = ""


def profile_facade(
    facade: Any,
    iterations: int = 100,
    point_ids: list[str] | None = None,
    endpoint_id: str = "",
    scenario_id: str = "",
) -> ProfileResult:
    """对 facade.read() 执行 N 次采样并统计耗时。

    每次采样计时：
        1. 记录开始时间。
        2. 调用 facade.read(point_ids)。
        3. 记录结束时间，计算耗时。

    统计量：count / min / max / avg（单位毫秒）。
    不做预热、不做平均偏差、不做 p50/p95/p99 分位数。

    Args:
        facade: facade 实例（需实现 read 接口）。
        iterations: 采样次数，默认 100。
        point_ids: 读取的点位 ID 列表，None 表示全部。
        endpoint_id: 端点标识。
        scenario_id: 场景标识。

    Returns:
        ProfileResult 包含耗时统计和执行状态。
    """
    result = ProfileResult()
    result.iterations = iterations
    result.endpoint_id = endpoint_id
    result.scenario_id = scenario_id

    # 收集元信息
    try:
        result.protocol = getattr(facade, "protocol", "")
        result.mode = getattr(facade, "mode", "")
    except Exception:
        pass

    if iterations < 1:
        result.status = "FAIL"
        result.reason = f"iterations 必须 >= 1，收到 {iterations}"
        return result

    samples: list[float] = []
    total_start = time.perf_counter()

    for i in range(iterations):
        try:
            t0 = time.perf_counter()
            facade.read(point_ids)
            t1 = time.perf_counter()
            samples.append((t1 - t0) * 1000.0)  # 转换为毫秒
        except Exception as exc:
            result.status = "FAIL"
            result.reason = f"第 {i + 1}/{iterations} 次 read 失败: {exc}"
            result.samples = samples
            return result

    total_end = time.perf_counter()
    result.duration_ms = (total_end - total_start) * 1000.0
    result.samples = samples

    if samples:
        result.stats = {
            "count": len(samples),
            "min": round(min(samples), 4),
            "max": round(max(samples), 4),
            "avg": round(sum(samples) / len(samples), 4),
        }

    result.status = "PASS"
    result.reason = f"profile 完成: {iterations} 次采样, avg={result.stats.get('avg', 'N/A')}ms"
    return result


__all__ = ["ProfileResult", "profile_facade"]
