"""seahorse 回放生成策略。

支持从内存 rows 和 JSONL 文件中回放信号值序列，
通过字段映射将源数据转换为 GeneratedSignalValue 标准结构。
支持时间轴偏移和加速倍率。

安全边界：
- 不得 import whale.ingest。
- 确定性：相同输入源 + 相同参数 → 相同输出。
- 不修改输入文件，只读取。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from seahorse.models.generation import GeneratedAlarmEvent, GeneratedControlResult, GeneratedSignalValue
from seahorse.models.plan import SeedEntity, SignalProfileItemPlan

# 策略标识常量
STRATEGY_ID_REPLAY = "replay_generation"

# 默认字段映射：row key -> GeneratedSignalValue 字段
_DEFAULT_FIELD_MAP = {
    "signal_id": "signal_id",
    "scenario_id": "scenario_id",
    "source_id": "source_id",
    "device_id": "device_id",
    "profile_item_id": "profile_item_id",
    "node_key": "node_key",
    "variable_key": "variable_key",
    "timestamp": "timestamp",
    "value": "value",
    "quality": "quality",
    "unit": "unit",
    "strategy_id": "strategy_id",
    "synthetic": "synthetic",
}


class ReplayGenerationStrategy:
    """回放生成策略。

    从内存 rows（list[dict]）或 JSONL 文件中读取历史数据，
    按字段映射转换为 GeneratedSignalValue 序列。
    支持时间轴偏移（offset_seconds）和加速倍率（speed_factor）。

    每条 row 必须包含至少 value 字段，否则抛出 KeyError。
    不存在静默吞缺。

    Attributes:
        _scenario_id: 场景标识。
        _source_id: 数据源标识。
        _field_map: 自定义字段映射字典。
        _rows: 内存 rows 缓存（非 None 时优先于文件）。
        _jsonl_path: JSONL 文件路径。
    """

    def __init__(
        self,
        *,
        scenario_id: str = "",
        source_id: str = "",
        field_map: dict[str, str] | None = None,
    ) -> None:
        """初始化回放策略。

        初始化后使用 load_from_rows() 或 load_from_jsonl() 加载数据。

        Args:
            scenario_id: 场景唯一标识。
            source_id: 数据源标识。
            field_map: 自定义字段映射，key 为 row 中的字段名，
                value 为 GeneratedSignalValue 属性名。
                未指定时使用 _DEFAULT_FIELD_MAP。
        """
        self._scenario_id = scenario_id
        self._source_id = source_id
        self._field_map = field_map or dict(_DEFAULT_FIELD_MAP)
        self._rows: list[dict[str, Any]] | None = None
        self._jsonl_path: Path | None = None

    @property
    def strategy_id(self) -> str:
        """返回策略标识字符串。"""
        return STRATEGY_ID_REPLAY

    def load_from_rows(self, rows: list[dict[str, Any]]) -> None:
        """从内存 rows 加载回放数据。

        Args:
            rows: 数据行列表，每行是一个 dict。
                每条 row 必须包含至少 'value' 键，否则在生成时抛出 KeyError。
        """
        if not isinstance(rows, list):
            raise TypeError(f"rows 必须为 list[dict]，实际为 {type(rows).__name__}")
        self._rows = list(rows)
        self._jsonl_path = None

    def load_from_jsonl(self, filepath: str | Path) -> None:
        """从 JSONL 文件加载回放数据。

        JSONL 文件每行为一个 JSON 对象。
        文件必须存在且可读，否则抛出 FileNotFoundError。

        Args:
            filepath: JSONL 文件路径。

        Raises:
            FileNotFoundError: 文件不存在。
            json.JSONDecodeError: JSON 解析失败时传播原始异常。
        """
        path = Path(filepath).resolve()
        if not path.exists():
            raise FileNotFoundError(f"JSONL 文件不存在: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"路径不是文件: {path}")

        rows: list[dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    row = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise json.JSONDecodeError(
                        f"JSONL 文件解析失败: {path}, 第 {line_num} 行",
                        exc.doc,
                        exc.pos,
                    ) from exc
                if not isinstance(row, dict):
                    raise TypeError(
                        f"JSONL 文件 {path} 第 {line_num} 行不是 JSON 对象"
                    )
                rows.append(row)

        self._rows = rows
        self._jsonl_path = path

    @property
    def row_count(self) -> int:
        """返回已加载的数据行数。"""
        return len(self._rows) if self._rows else 0

    @property
    def is_loaded(self) -> bool:
        """返回数据是否已加载。"""
        return self._rows is not None

    def generate_signals(
        self,
        *,
        entity: SeedEntity,
        signal_plan: SignalProfileItemPlan,
        start_time: float,
        duration_seconds: float,
        deterministic_seed: int,
    ) -> list[GeneratedSignalValue]:
        """回放已加载的数据行，生成 GeneratedSignalValue 序列。

        每行数据通过字段映射转换为 GeneratedSignalValue。
        时间戳处理规则：
        - 如果 row 中有 timestamp 字段，以该值为基准加 offset。
        - 如果 row 中没有 timestamp 字段，使用 start_time + 行序号 * interval。

        加速倍率：通过 speed_factor 参数（内部从 signal_plan 的
        generation_hint 解析）控制回放速度。speed_factor > 1 表示加速。

        Args:
            entity: 目标种子实体。
            signal_plan: 信号点位规划（用于提取 sample_interval_ms 和
                generation_hint 中的 speed_factor）。
            start_time: 起始 Unix 时间戳（秒），用作时间偏移基准。
            duration_seconds: 生成时长（秒），超出此范围的 row 将被截断。
            deterministic_seed: 确定性随机种子（回放策略不使用 RNG，
                但保留参数以符合 Protocol 契约）。

        Returns:
            GeneratedSignalValue 列表，按原始行序排列。
            长度不超过 duration_seconds 约束。

        Raises:
            ValueError: 如果数据未加载（rows 为 None）。
            KeyError: 如果 row 中缺少 'value' 字段且字段映射未覆盖。
        """
        if self._rows is None:
            raise ValueError("数据未加载，请先调用 load_from_rows() 或 load_from_jsonl()")

        # 解析 speed_factor（从 generation_hint 取，格式如 "REPLAY:2.0"）
        speed_factor = 1.0
        hint = signal_plan.generation_hint.upper()
        if hint.startswith("REPLAY:") or hint.startswith("REPLAY@"):
            try:
                speed_factor = float(hint.split(":", 1)[-1].split("@", 1)[-1])
            except (ValueError, IndexError):
                speed_factor = 1.0

        interval_s = signal_plan.sample_interval_ms / 1000.0
        if interval_s <= 0:
            interval_s = 0.1

        results: list[GeneratedSignalValue] = []
        base_time = datetime.fromtimestamp(start_time, tz=timezone.utc)

        for idx, row in enumerate(self._rows):
            # 检查必填字段
            value = self._extract_field(row, "value")
            if value is None:
                raise KeyError(f"row[{idx}] 缺少必填字段 'value'")

            # 时间戳处理
            raw_ts = self._extract_field(row, "timestamp")
            if raw_ts is not None:
                # 将 row 中的 timestamp 解析为 datetime
                if isinstance(raw_ts, (int, float)):
                    ts = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
                elif isinstance(raw_ts, str):
                    ts = datetime.fromisoformat(raw_ts)
                elif isinstance(raw_ts, datetime):
                    ts = raw_ts
                else:
                    raise TypeError(
                        f"row[{idx}] timestamp 类型不支持: {type(raw_ts).__name__}"
                    )
                # 应用加速倍率：时间偏移 = (raw_ts - first_ts) / speed_factor
                # 首先确定基准时间
                if idx == 0:
                    ref_ts = ts
                    ref_epoch = base_time
                elapsed = (ts - ref_ts).total_seconds() / speed_factor  # type: ignore[has-type]
                actual_ts = base_time + timedelta(seconds=elapsed) if idx == 0 else \
                    ref_epoch + timedelta(seconds=elapsed)  # type: ignore[has-type, possibly-used-before-assignment]
            else:
                # 无 timestamp 字段时按序号生成
                actual_ts = base_time + timedelta(seconds=idx * interval_s / speed_factor)

            # 检查时间是否超出 duration
            elapsed_from_start = (actual_ts - base_time).total_seconds()
            if elapsed_from_start > duration_seconds:
                break

            # 构造 GeneratedSignalValue，优先使用 row 值，其次用 signal_plan 默认值
            sv = GeneratedSignalValue(
                signal_id=str(self._extract_field(row, "signal_id") or signal_plan.signal_id),
                scenario_id=str(self._extract_field(row, "scenario_id") or self._scenario_id),
                source_id=str(self._extract_field(row, "source_id") or self._source_id),
                device_id=str(self._extract_field(row, "device_id") or entity.entity_id),
                profile_item_id=str(self._extract_field(row, "profile_item_id") or signal_plan.signal_id),
                node_key=str(self._extract_field(row, "node_key") or signal_plan.ln_class),
                variable_key=str(self._extract_field(row, "variable_key") or signal_plan.signal_name),
                timestamp=actual_ts,
                value=float(value),
                quality=int(self._extract_field(row, "quality") or 0),
                unit=str(self._extract_field(row, "unit") or signal_plan.unit),
                strategy_id=STRATEGY_ID_REPLAY,
                synthetic=True,
            )
            results.append(sv)

        return results

    def _extract_field(self, row: dict[str, Any], target: str) -> Any:
        """从 row 的字段映射中提取目标字段值。

        Args:
            row: 数据行（dict）。
            target: GeneratedSignalValue 的属性名。

        Returns:
            映射后的值，如果 row 中没有对应字段则返回 None。
        """
        # 从 field_map 反向查找: target -> row_key
        row_key = None
        for rk, tv in self._field_map.items():
            if tv == target:
                row_key = rk
                break

        if row_key is None:
            # 字段映射中无此 target，直接尝试 row key
            return row.get(target)

        return row.get(row_key)

    def generate_alarms(
        self,
        *,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
        deterministic_seed: int,
    ) -> list[GeneratedAlarmEvent]:
        """生成告警事件（回放策略最小实现）。

        回放策略默认不生成告警事件，返回空列表。
        告警事件由 SeahorseGenerator 通过 AlarmGenerator 统一管理。

        Args:
            entity: 目标实体。
            signal_values: 信号值序列。
            deterministic_seed: 确定性随机种子。

        Returns:
            空列表。
        """
        return []

    def generate_controls(
        self,
        *,
        entity: SeedEntity,
        deterministic_seed: int,
    ) -> list[GeneratedControlResult]:
        """生成控制回写结果（回放策略最小实现）。

        回放策略默认不生成控制结果，返回空列表。
        控制结果由 SeahorseGenerator 通过 ControlResultGenerator 统一管理。

        Args:
            entity: 目标实体。
            deterministic_seed: 确定性随机种子。

        Returns:
            空列表。
        """
        return []


__all__ = ["STRATEGY_ID_REPLAY", "ReplayGenerationStrategy", "_DEFAULT_FIELD_MAP"]
