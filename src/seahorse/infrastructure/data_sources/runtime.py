"""Seahorse 内存 DataSource runtime adapter。

本模块实现 application `DataSourcePort` 的最小基础设施适配器。它只从
内存配置生成 random/sample/function/replay 值，不读取 Whale DB、不写
Starfish、不启动 scheduler，也不做真实 replay 文件 streaming。
"""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from seahorse.application.exceptions import DataSourceRuntimeError
from seahorse.application.ports.data_source_port import DataSourcePort
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    DataSourceValueKind,
    PointFieldValue,
    ScalarValue,
)


def _stable_seed(spec: DataSourceSpec, *, timestamp_ns: int, tick_index: int) -> int:
    """根据 spec/tick 生成跨进程稳定的伪随机 seed。"""
    raw = f"{spec.source_id}|{spec.seed or 0}|{timestamp_ns}|{tick_index}".encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], byteorder="big")


@dataclass(slots=True)
class InMemoryDataSourceRuntime(DataSourcePort):
    """内存 DataSource runtime。

    Attributes:
        samples: sample 数据源使用的 key-value 映射，key 可为 source_id 或 reference。
        replay_rows: replay 数据源使用的内存行，key 可为 source_id 或 reference。
    """

    samples: Mapping[str, PointFieldValue] = field(default_factory=dict)
    replay_rows: Mapping[str, Sequence[PointFieldValue]] = field(default_factory=dict)

    def resolve_value(
        self,
        spec: DataSourceSpec,
        *,
        timestamp_ns: int,
        tick_index: int = 0,
    ) -> PointFieldValue:
        """解析单个数据源的当前 tick 值。

        Args:
            spec: 数据源契约。
            timestamp_ns: 本次取值时间戳，单位纳秒。
            tick_index: 逻辑 tick 序号。

        Returns:
            可写入 WriteBatch 的字段值。

        Raises:
            DataSourceRuntimeError: 数据源配置缺失或引用不支持。
        """
        if spec.kind is DataSourceKind.RANDOM:
            return self._resolve_random(spec, timestamp_ns=timestamp_ns, tick_index=tick_index)
        if spec.kind is DataSourceKind.SAMPLE:
            return self._resolve_sample(spec)
        if spec.kind is DataSourceKind.FUNCTION:
            return self._resolve_function(spec, timestamp_ns=timestamp_ns, tick_index=tick_index)
        if spec.kind is DataSourceKind.REPLAY:
            return self._resolve_replay(spec, tick_index=tick_index)
        raise DataSourceRuntimeError(f"不支持的数据源类型: {spec.kind}")

    def resolve_batch(
        self,
        specs: tuple[DataSourceSpec, ...],
        *,
        timestamp_ns: int,
        tick_index: int = 0,
    ) -> dict[str, PointFieldValue]:
        """批量解析同一 tick 的 source_id 到值映射。

        Args:
            specs: 数据源契约集合。
            timestamp_ns: 本次取值时间戳，单位纳秒。
            tick_index: 逻辑 tick 序号。

        Returns:
            以 source_id 为 key 的值映射。
        """
        return {
            spec.source_id: self.resolve_value(
                spec,
                timestamp_ns=timestamp_ns,
                tick_index=tick_index,
            )
            for spec in specs
        }

    def _resolve_random(
        self,
        spec: DataSourceSpec,
        *,
        timestamp_ns: int,
        tick_index: int,
    ) -> PointFieldValue:
        """按 value_type 生成稳定伪随机值。"""
        generator = random.Random(
            _stable_seed(spec, timestamp_ns=timestamp_ns, tick_index=tick_index)
        )
        if spec.value_type is DataSourceValueKind.BOOL:
            return bool(generator.randint(0, 1))
        if spec.value_type is DataSourceValueKind.STRING:
            return f"{spec.source_id}-{generator.randint(0, 9999):04d}"
        if spec.value_type is DataSourceValueKind.NOMINAL:
            choices = self._nominal_choices(spec.reference)
            return choices[generator.randrange(len(choices))]
        return round(generator.random(), 6)

    def _resolve_sample(self, spec: DataSourceSpec) -> PointFieldValue:
        """从内存样本映射取值。"""
        key = self._lookup_key(spec)
        if key not in self.samples:
            raise DataSourceRuntimeError(f"sample 数据源未加载: {key}")
        return self.samples[key]

    def _resolve_function(
        self,
        spec: DataSourceSpec,
        *,
        timestamp_ns: int,
        tick_index: int,
    ) -> PointFieldValue:
        """执行最小内置函数，不引入外部依赖。"""
        reference = spec.reference or "tick"
        if reference == "tick":
            return tick_index
        if reference == "time_seconds":
            return timestamp_ns / 1_000_000_000
        if reference.startswith("constant:"):
            return self._parse_scalar(reference.removeprefix("constant:"))
        if reference.startswith("linear:"):
            slope, offset = self._parse_numbers(reference, expected=2)
            return slope * tick_index + offset
        if reference.startswith("sine:"):
            amplitude, offset = self._parse_numbers(reference, expected=2)
            return round(math.sin(tick_index) * amplitude + offset, 6)
        raise DataSourceRuntimeError(f"不支持的 function 数据源引用: {reference}")

    def _resolve_replay(self, spec: DataSourceSpec, *, tick_index: int) -> PointFieldValue:
        """从已加载内存 rows 选择 replay 值。"""
        key = self._lookup_key(spec)
        rows = self.replay_rows.get(key)
        if not rows:
            raise DataSourceRuntimeError(f"replay 数据源未加载: {key}")
        return rows[tick_index % len(rows)]

    def _lookup_key(self, spec: DataSourceSpec) -> str:
        """按 reference 优先、source_id 兜底得到内存数据 key。"""
        return spec.reference or spec.source_id

    def _nominal_choices(self, reference: str) -> tuple[str, ...]:
        """从 reference 解析 nominal 候选值。"""
        if reference.startswith("nominal:"):
            raw_choices = reference.removeprefix("nominal:")
            choices = tuple(choice.strip() for choice in raw_choices.split(",") if choice.strip())
            if choices:
                return choices
        return ("nominal_a", "nominal_b", "nominal_c")

    def _parse_numbers(self, reference: str, *, expected: int) -> tuple[float, ...]:
        """解析冒号分隔的 float 参数。"""
        parts = reference.split(":")[1:]
        if len(parts) != expected:
            raise DataSourceRuntimeError(f"function 参数数量不匹配: {reference}")
        try:
            return tuple(float(part) for part in parts)
        except ValueError as exc:
            raise DataSourceRuntimeError(f"function 参数不是数字: {reference}") from exc

    def _parse_scalar(self, raw: str) -> ScalarValue:
        """解析 constant 函数的标量值。"""
        lowered = raw.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        try:
            if "." in lowered:
                return float(lowered)
            return int(lowered)
        except ValueError:
            return raw


__all__ = ["InMemoryDataSourceRuntime"]
