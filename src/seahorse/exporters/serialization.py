"""seahorse 序列化辅助 —— 校验和计算与规范化 JSON 导出。

本模块提供 dataclass 到 JSON 可序列化 dict 的转换，以及基于内容
的确定性 SHA256 校验和计算。不依赖特定 ORM 或网络服务。

校验和确定性说明：
    同一 ScenarioConfig 与 deterministic_seed 产生的内容完全相同，
    因此基于内容的校验和在不同时间、不同主机上均可重现。
    注意：使用 datetime.now(timezone.utc) 作为默认 start_time
    或 created_at 的 bundle 其校验和不可重现，须显式设置固定时间戳。

安全边界：
- 不得 import whale.ingest。
- 所有转换仅操作内存数据，无外部副作用。
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from seahorse.models.bundle import ScenarioBundle, _make_serializable


def compute_bundle_checksum(bundle: ScenarioBundle) -> str:
    """计算场景包内容的确定性校验和。

    对场景包的核心产出内容（场景配置、种子计划、服务端配置、
    信号值序列、告警事件和控制结果）进行规范化序列化后计算
    SHA256 哈希。

    不参与校验和计算的字段：
        - created_at（每次生成时变化）
        - generator_version（版本升级不应影响数据一致性校验）
        - schema_version（序列化格式变化不应影响内容校验）
        - checksum 自身（避免循环依赖）
        - scenario_metadata.generated_at（运行时生成）

    校验和覆盖的内容字段（全部由 config + seed 确定）：
        scenario_config, seed_plan, server_config,
        generated_timeseries_sample, alarm_events, control_results,
        scenario_id, deterministic_seed, name, scenario_version.

    Args:
        bundle: 已填充内容的场景包。

    Returns:
        SHA256 十六进制哈希字符串（64 字符）。
    """
    # 仅提取参与校验和的内容字段
    content: dict[str, Any] = {
        "scenario_id": bundle.scenario_id,
        "name": bundle.name,
        "deterministic_seed": bundle.deterministic_seed,
        "scenario_version": bundle.scenario_version,
        "scenario_config": bundle.scenario_config,
        "seed_plan": bundle.seed_plan,
        "server_config": bundle.server_config,
        "generated_timeseries_sample": bundle.generated_timeseries_sample,
        "alarm_events": bundle.alarm_events,
        "control_results": bundle.control_results,
    }

    serializable = _make_serializable(content)
    canonical = json.dumps(
        serializable,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def bundle_to_serializable(bundle: ScenarioBundle) -> dict[str, Any]:
    """将场景包转换为 JSON 可序列化的 dict。

    与校验和不同，此方法转换 bundle 的全部字段（包括 created_at、
    generator_version 等），用于完整的 JSON 导出。

    Args:
        bundle: 已填充内容的场景包。

    Returns:
        JSON 可序列化的 dict，可通过 json.dump 直接写出。
    """
    result = _make_serializable(bundle)
    if not isinstance(result, dict):
        raise TypeError(f"_make_serializable 未返回 dict，实际类型: {type(result)}")
    return result


__all__ = ["compute_bundle_checksum", "bundle_to_serializable"]
