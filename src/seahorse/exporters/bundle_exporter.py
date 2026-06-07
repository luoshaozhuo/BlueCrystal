"""seahorse JSON 包导出器。

本模块提供场景包到 JSON 文件的导出能力，支持完整包导出和
仅时序数据导出。导出使用 UTF-8 编码，日期时间以 ISO 8601
格式存储，确保可读性和跨语言兼容。

安全边界：
- 不得 import whale.ingest。
- 文件 I/O 以原子方式完成，避免中断导致损坏。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from seahorse.models.bundle import ScenarioBundle
from seahorse.exporters.serialization import bundle_to_serializable


def export_bundle_to_json(bundle: ScenarioBundle, *, indent: int = 2) -> str:
    """将场景包序列化为 JSON 字符串。

    包含 bundle 的全部字段（包括 created_at、checksum 等元数据），
    使用紧凑但可读的缩进格式。

    Args:
        bundle: 已填充内容并计算校验和的场景包。
        indent: JSON 缩进空格数，默认 2。

    Returns:
        UTF-8 JSON 字符串。
    """
    serializable: dict[str, Any] = bundle_to_serializable(bundle)
    return json.dumps(serializable, ensure_ascii=False, indent=indent, default=str)


def save_bundle(
    bundle: ScenarioBundle,
    output_dir: str | Path,
    *,
    filename: str | None = None,
) -> Path:
    """将场景包保存为 JSON 文件。

    输出文件名默认为 ``{scenario_id}_bundle.json``，可通过 filename
    参数覆盖。父目录不存在时自动创建。

    Args:
        bundle: 已填充内容并计算校验和的场景包。
        output_dir: 输出目录路径。
        filename: 自定义文件名，None 时自动生成。

    Returns:
        已写入文件的 Path 对象。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        filename = f"{bundle.scenario_id}_bundle.json"
    output_path = output_dir / filename

    json_str = export_bundle_to_json(bundle)
    # 使用临时文件 + 原子重命名避免写入中断损坏
    tmp_path = output_path.with_suffix(".tmp")
    tmp_path.write_text(json_str, encoding="utf-8")
    os.replace(tmp_path, output_path)
    return output_path


__all__ = ["export_bundle_to_json", "save_bundle"]
