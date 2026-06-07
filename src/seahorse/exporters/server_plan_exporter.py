"""seahorse ServerPlan handoff 导出器。

本模块将 ServerPlan（或 ScenarioBundle 中的 ServerPlan）导出为
Starfish runtime 可直接解析的 JSON 契约文件（starfish_server_plan.json）。
导出使用原子写入，包含 checksum/payload_hash 用于完整性验证。

Starfish 契约隔离：
- 导出产物为纯 JSON，不依赖任何 seahorse 或 starfish Python 类型。
- Starfish runtime 只需读取 JSON 文件，无需 import seahorse。
- 本模块不得 import starfish。

安全边界：
- 不得 import whale.ingest。
- 文件 I/O 以原子方式完成。
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from seahorse.models.plan import ServerPlan, ServerEndpointPlan, ServerPointPlan
from seahorse.models.bundle import ScenarioBundle


# Starfish ServerPlan 契约 JSON schema 当前版本
_SERVER_PLAN_SCHEMA_VERSION = "1.0.0"


def _server_endpoint_to_dict(ep: ServerEndpointPlan) -> dict[str, Any]:
    """将 ServerEndpointPlan 转换为 Starfish 契约 dict。

    Starfish 契约层关注 endpoint_id、protocol、host、port；
    绑定层信息（bind_host、bind_port）保留为参考字段。

    Args:
        ep: Seahorse 服务端点规划。

    Returns:
        Starfish 契约兼容的端点 dict。
    """
    d: dict[str, Any] = {
        "endpoint_id": ep.endpoint_id or ep.endpoint_name,
        "protocol": ep.protocol,
        "host": ep.host or ep.bind_host,
        "port": ep.port or ep.bind_port,
    }
    # 保留绑定层字段用于调试和容器化场景
    if ep.bind_host and ep.bind_host != d["host"]:
        d["bind_host"] = ep.bind_host
    if ep.bind_port and ep.bind_port != d["port"]:
        d["bind_port"] = ep.bind_port
    if ep.endpoint_name and ep.endpoint_name != ep.endpoint_id:
        d["endpoint_name"] = ep.endpoint_name
    return d


def _server_point_to_dict(pt: ServerPointPlan) -> dict[str, Any]:
    """将 ServerPointPlan 转换为 Starfish 契约 dict。

    包含契约层必需字段（point_id、node_key、variable_key、value_type）
    以及 access_mode、data_type 等辅助字段。

    Args:
        pt: Seahorse 服务点位规划。

    Returns:
        Starfish 契约兼容的点位 dict。
    """
    return {
        "point_id": pt.point_id,
        "point_name": pt.point_name,
        "node_key": pt.node_key,
        "variable_key": pt.variable_key,
        "value_type": pt.value_type or pt.data_type,
        "access_mode": pt.access_mode,
        "data_type": pt.data_type,
    }


def build_server_plan_payload(server_plan: ServerPlan) -> dict[str, Any]:
    """从 ServerPlan 构建 Starfish 契约 payload dict（不含 payload_hash）。

    将 Seahorse 内部模型转为纯 dict 结构，Starfish 可无需 import
    seahorse 直接解析。payload_hash 由调用方在序列化前注入。

    Args:
        server_plan: Seahorse 生成的完整 ServerPlan。

    Returns:
        Starfish 契约兼容的 dict，结构如下::

            {
                "schema_version": "1.0.0",
                "scenario_id": "...",
                "generator_version": "0.2.0",
                "generated_at": "2024-01-01T00:00:00+00:00",
                "synthetic": true,
                "server_name": "...",
                "strategy_id": "...",
                "endpoints": [...],
                "points": [...],
                "capabilities": [...],
                "update_policy": {...},
                "initial_values": {...},
                "payload_hash": ""
            }
    """
    payload: dict[str, Any] = {
        "schema_version": _SERVER_PLAN_SCHEMA_VERSION,
        "scenario_id": server_plan.scenario_id,
        "generator_version": "0.2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "synthetic": server_plan.synthetic,
        "server_name": server_plan.server_name,
        "strategy_id": server_plan.strategy_id,
        "endpoints": [_server_endpoint_to_dict(ep) for ep in server_plan.endpoints],
        "points": [_server_point_to_dict(pt) for pt in server_plan.points],
        "capabilities": list(server_plan.capabilities),
        "update_policy": dict(server_plan.update_policy),
        "initial_values": dict(server_plan.initial_values),
        "payload_hash": "",
    }
    return payload


def _compute_payload_hash(payload: dict[str, Any]) -> str:
    """计算 ServerPlan 契约 payload 的 SHA256 哈希。

    排除 payload_hash 自身和 generated_at（每次生成时变化）后计算，
    确保相同内容在不同时间产生相同哈希。

    Args:
        payload: 包含 payload_hash="" 的完整 payload dict。

    Returns:
        SHA256 十六进制哈希字符串（64 字符）。
    """
    # 排除可变字段以确保证确定性
    content = {
        k: v for k, v in payload.items()
        if k not in ("payload_hash", "generated_at")
    }
    canonical = json.dumps(
        content,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def export_server_plan_to_json(
    server_plan: ServerPlan,
    *,
    indent: int = 2,
) -> str:
    """将 ServerPlan 导出为 Starfish 契约 JSON 字符串。

    输出的 JSON 包含完整的 endpoints、points、capabilities、
    update_policy、initial_values 以及 SHA256 payload_hash。

    Args:
        server_plan: Seahorse 生成的完整 ServerPlan。
        indent: JSON 缩进空格数，默认 2。

    Returns:
        UTF-8 JSON 字符串，可直接写入 starfish_server_plan.json。
    """
    payload = build_server_plan_payload(server_plan)
    # 注入 payload_hash（hash 自身字段当前为空）
    payload["payload_hash"] = _compute_payload_hash(payload)
    return json.dumps(payload, ensure_ascii=False, indent=indent, default=str)


def export_server_plan_from_bundle(
    bundle: ScenarioBundle,
    *,
    indent: int = 2,
) -> str:
    """从 ScenarioBundle 导出 ServerPlan 为 Starfish 契约 JSON 字符串。

    自动从 bundle 中提取 server_plan、generator_version 和 scenario_id。

    Args:
        bundle: 已填充的 ScenarioBundle 实例。
        indent: JSON 缩进空格数，默认 2。

    Returns:
        UTF-8 JSON 字符串。

    Raises:
        ValueError: 如果 bundle.server_plan 为 None。
    """
    if bundle.server_plan is None:
        raise ValueError("ScenarioBundle.server_plan 为 None，无法导出 ServerPlan")
    return export_server_plan_to_json(bundle.server_plan, indent=indent)


def save_server_plan(
    server_plan: ServerPlan,
    output_dir: str | Path,
    *,
    filename: str | None = None,
) -> Path:
    """将 ServerPlan 以原子方式保存为 starfish_server_plan.json。

    使用临时文件 + 原子重命名确保写入过程中断不会损坏已有文件。
    父目录不存在时自动创建。

    Args:
        server_plan: Seahorse 生成的完整 ServerPlan。
        output_dir: 输出目录路径。
        filename: 自定义文件名，None 时使用 ``{scenario_id}_server_plan.json``。

    Returns:
        已写入文件的 Path 对象。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{server_plan.scenario_id}_server_plan.json"
    output_path = output_dir / filename

    json_str = export_server_plan_to_json(server_plan)
    tmp_path = output_path.with_suffix(".tmp")
    tmp_path.write_text(json_str, encoding="utf-8")
    os.replace(tmp_path, output_path)
    return output_path


def save_server_plan_from_bundle(
    bundle: ScenarioBundle,
    output_dir: str | Path,
    *,
    filename: str | None = None,
) -> Path:
    """从 ScenarioBundle 以原子方式保存 ServerPlan 为 starfish_server_plan.json。

    自动提取 bundle 中的 server_plan 并调用 save_server_plan。

    Args:
        bundle: 已填充的 ScenarioBundle 实例。
        output_dir: 输出目录路径。
        filename: 自定义文件名。

    Returns:
        已写入文件的 Path 对象。

    Raises:
        ValueError: 如果 bundle.server_plan 为 None。
    """
    if bundle.server_plan is None:
        raise ValueError("ScenarioBundle.server_plan 为 None，无法导出 ServerPlan")
    return save_server_plan(bundle.server_plan, output_dir, filename=filename)


__all__ = [
    "build_server_plan_payload",
    "export_server_plan_to_json",
    "export_server_plan_from_bundle",
    "save_server_plan",
    "save_server_plan_from_bundle",
]
