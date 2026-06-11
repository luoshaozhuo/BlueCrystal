"""starfish ServerPlan JSON 驱动加载器。

本模块提供 load_server_plan 函数，从 Seahorse 导出的
starfish_server_plan.json 文件读取并校验 ServerPlan 契约。

负责：
- 从文件读取 Seahorse handoff JSON。
- 校验 schema_version、scenario_id、synthetic、
  endpoints、points、capabilities、initial_values、payload_hash。
- payload_hash 复算校验（检测 mismatch）。
- 构建 StarfishServerPlan 内存模型。

不负责：
- 真实协议 server 启动。
- 数据持久化或落库。
- Seahorse Python 类型导入。

安全边界：
- 不得 import seahorse。
- 不得 import whale.ingest / whale.shared.source。
- 文件 I/O 仅读取。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from starfish.domain import (
    StarfishServerPlan,
    StarfishEndpointPlan,
    StarfishPointPlan,
    LoadResult,
    ValidationResult,
)

# Seahorse ServerPlan handoff JSON 契约当前版本
_EXPECTED_SCHEMA_VERSION = "1.0.0"

# Starfish 强制要求的顶层字段
_REQUIRED_FIELDS = [
    "schema_version",
    "scenario_id",
    "synthetic",
    "endpoints",
    "points",
    "capabilities",
    "initial_values",
    "payload_hash",
]


def _compute_payload_hash(data: dict[str, Any]) -> str:
    """计算 JSON payload 的 SHA256 哈希。

    排除 payload_hash 自身和 generated_at（每次生成时变化）后计算，
    使同一内容在不同时间产生相同哈希。

    Args:
        data: 完整的 JSON payload dict。

    Returns:
        SHA256 十六进制哈希字符串（64 字符）。
    """
    content = {
        k: v for k, v in data.items()
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


def _parse_endpoints(raw_endpoints: list[dict[str, Any]]) -> list[StarfishEndpointPlan]:
    """从 JSON dict 列表解析端点契约。

    Args:
        raw_endpoints: JSON 中的 endpoints 数组。

    Returns:
        StarfishEndpointPlan 列表。
    """
    result: list[StarfishEndpointPlan] = []
    for ep in raw_endpoints:
        result.append(StarfishEndpointPlan(
            endpoint_id=ep.get("endpoint_id", ""),
            protocol=ep.get("protocol", ""),
            host=ep.get("host", ""),
            port=ep.get("port", 0),
            bind_host=ep.get("bind_host"),
            bind_port=ep.get("bind_port"),
            endpoint_name=ep.get("endpoint_name"),
        ))
    return result


def _parse_points(raw_points: list[dict[str, Any]]) -> list[StarfishPointPlan]:
    """从 JSON dict 列表解析点位契约。

    Args:
        raw_points: JSON 中的 points 数组。

    Returns:
        StarfishPointPlan 列表。
    """
    result: list[StarfishPointPlan] = []
    for pt in raw_points:
        result.append(StarfishPointPlan(
            point_id=pt.get("point_id", ""),
            point_name=pt.get("point_name", ""),
            node_key=pt.get("node_key", ""),
            variable_key=pt.get("variable_key", ""),
            value_type=pt.get("value_type", ""),
            access_mode=pt.get("access_mode", "RO"),
            data_type=pt.get("data_type", "FLOAT64"),
        ))
    return result


def _validate_and_build(data: dict[str, Any]) -> tuple[StarfishServerPlan | None, ValidationResult]:
    """校验 JSON dict 并构建 StarfishServerPlan。

    校验包括：必填字段存在性、schema_version 匹配、
    endpoints/points 结构完整性、synthetic 标识、
    payload_hash 复算一致性。

    Args:
        data: 已解析的 JSON dict。

    Returns:
        二元组 (plan, validation_result)。plan 在校验失败时为 None，
        但基础字段仍尝试填充以便调用方降级使用。
    """
    result = ValidationResult()

    # 1. 必填字段存在性
    for field in _REQUIRED_FIELDS:
        if field not in data:
            result.add_error(f"缺少必填字段: {field}")

    # 2. schema_version 校验
    sv = data.get("schema_version", "")
    if sv and sv != _EXPECTED_SCHEMA_VERSION:
        result.add_warning(
            f"schema_version 不匹配: 期望 {_EXPECTED_SCHEMA_VERSION}，实际 {sv}"
        )
    elif sv:
        result.add_pass(f"schema_version 匹配: {sv}")

    # 3. scenario_id 存在性
    sid = data.get("scenario_id", "")
    if not sid:
        result.add_error("scenario_id 缺失或为空")
    else:
        result.add_pass(f"scenario_id 存在: {sid}")

    # 4. synthetic 存在性
    synthetic = data.get("synthetic")
    if synthetic is None:
        result.add_error("synthetic 字段缺失")
    elif not isinstance(synthetic, bool):
        result.add_error(f"synthetic 应为布尔类型，实际: {type(synthetic).__name__}")
    elif synthetic is False:
        result.add_warning("synthetic=False，请确认数据来源")
    else:
        result.add_pass("synthetic 标识存在且为 True")

    # 5. endpoints 结构
    raw_endpoints = data.get("endpoints", [])
    if not isinstance(raw_endpoints, list):
        result.add_error("endpoints 应为列表")
    elif not raw_endpoints:
        result.add_error("endpoints 为空，至少需要一个端点")
    else:
        result.add_pass(f"endpoints 包含 {len(raw_endpoints)} 个端点")
        for i, ep in enumerate(raw_endpoints):
            if not isinstance(ep, dict):
                result.add_error(f"endpoints[{i}] 不是合法 dict")
                continue
            if not ep.get("endpoint_id"):
                result.add_error(f"endpoints[{i}] 缺少 endpoint_id")
            if not ep.get("protocol"):
                result.add_error(f"endpoints[{i}] 缺少 protocol")

    # 6. points 结构
    raw_points = data.get("points", [])
    if not isinstance(raw_points, list):
        result.add_error("points 应为列表")
    elif not raw_points:
        result.add_error("points 为空，至少需要一个点位")
    else:
        result.add_pass(f"points 包含 {len(raw_points)} 个点位")
        for i, pt in enumerate(raw_points):
            if not isinstance(pt, dict):
                result.add_error(f"points[{i}] 不是合法 dict")
                continue
            if not pt.get("point_id"):
                result.add_error(f"points[{i}] 缺少 point_id")

    # 7. capabilities 类型
    raw_caps = data.get("capabilities", [])
    if not isinstance(raw_caps, list):
        result.add_warning(f"capabilities 应为列表，实际: {type(raw_caps).__name__}")
    else:
        result.add_pass(f"capabilities 声明: {raw_caps}")

    # 8. initial_values 类型
    raw_iv = data.get("initial_values", {})
    if not isinstance(raw_iv, dict):
        result.add_warning(f"initial_values 应为 dict，实际: {type(raw_iv).__name__}")

    # 9. payload_hash 复算
    stored_hash = data.get("payload_hash", "")
    if stored_hash:
        computed = _compute_payload_hash(data)
        if computed != stored_hash:
            result.add_error(
                f"payload_hash 不匹配: 存储值={stored_hash[:16]}...，"
                f"计算值={computed[:16]}..."
            )
        else:
            result.add_pass("payload_hash 校验通过")
    else:
        result.add_warning("payload_hash 为空，跳过完整性校验")

    # 构建 ServerPlan（即使部分校验失败仍尝试填充可用字段）
    plan = StarfishServerPlan(
        schema_version=data.get("schema_version", ""),
        scenario_id=data.get("scenario_id", ""),
        generator_version=data.get("generator_version", ""),
        generated_at=data.get("generated_at", ""),
        synthetic=data.get("synthetic", True),
        server_name=data.get("server_name", ""),
        strategy_id=data.get("strategy_id", ""),
        endpoints=_parse_endpoints(raw_endpoints) if isinstance(raw_endpoints, list) else [],
        points=_parse_points(raw_points) if isinstance(raw_points, list) else [],
        capabilities=list(raw_caps) if isinstance(raw_caps, list) else [],
        update_policy=dict(data.get("update_policy", {})),
        initial_values=dict(raw_iv) if isinstance(raw_iv, dict) else {},
        payload_hash=stored_hash,
    )

    return plan, result


def load_server_plan(file_path: str | Path) -> LoadResult:
    """从 JSON 文件加载并校验 Starfish ServerPlan。

    读取 Seahorse 导出的 starfish_server_plan.json 文件，
    执行结构校验、字段完整性和 payload_hash 一致性检查，
    返回可操作的 LoadResult。

    本函数仅依赖 JSON/dict/schema，不 import seahorse 模块。

    Args:
        file_path: ServerPlan JSON 文件路径。

    Returns:
        LoadResult 实例，包含解析后的 StarfishServerPlan（如成功）
        和校验明细。

    Raises:
        FileNotFoundError: 文件不存在。
        json.JSONDecodeError: JSON 解析失败。
        ValueError: 顶层 JSON 不是 dict 类型。
    """
    file_path = Path(file_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"ServerPlan JSON 文件不存在: {file_path}")

    raw_text = file_path.read_text(encoding="utf-8")
    data = json.loads(raw_text)

    if not isinstance(data, dict):
        raise ValueError(
            f"ServerPlan JSON 顶层应为 dict，实际: {type(data).__name__}"
        )

    plan, validation = _validate_and_build(data)
    return LoadResult(
        plan=plan,
        validation=validation,
        file_path=str(file_path),
    )


__all__ = ["load_server_plan"]
