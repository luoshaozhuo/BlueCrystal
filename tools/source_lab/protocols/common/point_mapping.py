"""协议无关点位映射辅助。"""

from __future__ import annotations

from dataclasses import dataclass

from tools.source_lab.model import SimulatedPoint


def normalize_data_type(value: str) -> str:
    """归一化数据类型。

    Args:
        value: 原始类型字符串。

    Returns:
        统一后的类型。
    """

    text = value.strip().upper()
    if text in {"BOOL", "BOOLEAN"}:
        return "BOOLEAN"
    if text in {"INT8", "INT16", "INT32", "INT64", "UINT8", "UINT16", "UINT32"}:
        return "INT32"
    if text in {"FLOAT", "FLOAT32", "FLOAT64", "DOUBLE"}:
        return "FLOAT64"
    if text in {"STRING", "VISSTRING255", "TEXT"}:
        return "STRING"
    if text in {"TIMESTAMP", "DATETIME"}:
        return "DATETIME"
    return "FLOAT64"


@dataclass(frozen=True, slots=True)
class PointMapping:
    """统一点位映射结果。"""

    key: str
    logical_name: str
    data_type: str
    generated_address: str


def build_point_mapping(point: SimulatedPoint, *, protocol: str, index: int) -> PointMapping:
    """构建协议点位映射。

    Args:
        point: 点位定义。
        protocol: 协议名。
        index: 点位索引。

    Returns:
        统一映射对象。
    """

    normalized_type = normalize_data_type(point.data_type)
    logical_name = point.display_name or point.key
    if protocol == "modbus_tcp":
        generated_address = str(40001 + index)
    elif protocol == "modbus_rtu":
        generated_address = str(30001 + index)
    else:
        generated_address = point.locator
    return PointMapping(
        key=point.key,
        logical_name=logical_name,
        data_type=normalized_type,
        generated_address=generated_address,
    )


def build_simulator_value(data_type: str, *, index: int) -> str | int | float | bool:
    """生成协议 simulator 更新值。

    Args:
        data_type: 归一化后数据类型。
        index: 点位序号。

    Returns:
        与类型匹配的 simulator 值。
    """

    if data_type == "BOOLEAN":
        return bool(index % 2)
    if data_type == "INT32":
        return index
    if data_type == "STRING":
        return f"value-{index}"
    if data_type == "DATETIME":
        return "2026-01-01T00:00:00Z"
    return float(index)
