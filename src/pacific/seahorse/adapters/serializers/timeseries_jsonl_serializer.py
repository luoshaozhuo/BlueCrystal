"""seahorse JSONL 时序导出器。

本模块提供信号值序列到 JSONL（每行一个 JSON 对象）的导出能力，
避免大样本时序数据全部塞进单个 JSON 数组导致的内存和解析问题。

第一阶段策略：
    bundle JSON 仍包含 generated_timeseries_sample 作为采样，
    但大体积时序数据应优先通过 JSONL 格式导出和消费。

安全边界：
- 不得 import whale.ingest。
- 文件 I/O 以原子方式完成。
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from pacific.seahorse.domain.generation import GeneratedSignalValue
from pacific.seahorse.domain.bundle import _make_serializable


def export_timeseries_to_jsonl(
    signal_values: list[GeneratedSignalValue],
) -> str:
    """将信号值序列序列化为 JSONL 字符串。

    每行一个 JSON 对象，表示一条 GeneratedSignalValue。
    行内字段为信号值的完整属性集合。

    Args:
        signal_values: 生成的信号值序列列表。

    Returns:
        JSONL 格式字符串，每行以换行符分隔。
    """
    lines: list[str] = []
    for sv in signal_values:
        serializable = _make_serializable(sv)
        lines.append(json.dumps(serializable, ensure_ascii=False, default=str))
    return "\n".join(lines) + "\n"


def save_timeseries(
    signal_values: list[GeneratedSignalValue],
    output_dir: str | Path,
    *,
    scenario_id: str = "",
    filename: str | None = None,
) -> Path:
    """将信号值序列保存为 JSONL 文件。

    输出文件名默认为 ``{scenario_id}_timeseries.jsonl``，可通过
    filename 参数覆盖。父目录不存在时自动创建。

    Args:
        signal_values: 生成的信号值序列列表。
        output_dir: 输出目录路径。
        scenario_id: 场景标识，用于生成默认文件名。
        filename: 自定义文件名，None 时自动生成。

    Returns:
        已写入文件的 Path 对象。
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        prefix = scenario_id or "seahorse"
        filename = f"{prefix}_timeseries.jsonl"
    output_path = output_dir / filename

    content = export_timeseries_to_jsonl(signal_values)
    # 使用临时文件 + 原子重命名避免写入中断损坏
    tmp_path = output_path.with_suffix(".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, output_path)
    return output_path


__all__ = ["export_timeseries_to_jsonl", "save_timeseries"]
