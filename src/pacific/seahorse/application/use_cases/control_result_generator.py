"""seahorse 控制回写响应生成器。

本模块提供生成控制命令执行结果的能力，模拟设备对控制命令的响应。
支持 dry run、写禁用、写成功、回读匹配、回读不匹配、超时、
不支持操作等常见控制回写场景。

所有生成结果均为 `GeneratedControlResult`，不写入数据库或执行实际设备控制。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
- 确定性：相同输入 + 相同 deterministic_seed 产生相同控制结果序列。
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Callable

from pacific.seahorse.domain.generation import GeneratedControlResult
from pacific.seahorse.domain.plan import SeedEntity


# 控制结果状态常量，用于统一引用和扩展
CONTROL_STATUS_ACCEPTED = "ACCEPTED"               # 写操作已接受
CONTROL_STATUS_WRITE_DISABLED = "WRITE_DISABLED"    # 写功能已禁用
CONTROL_STATUS_DRY_RUN_ACCEPTED = "DRY_RUN_ACCEPTED" # dry run 模式已接受但不实际执行
CONTROL_STATUS_READBACK_MATCHED = "READBACK_MATCHED" # 写后回读匹配
CONTROL_STATUS_READBACK_MISMATCH = "READBACK_MISMATCH" # 写后回读不匹配
CONTROL_STATUS_TIMEOUT = "TIMEOUT"                   # 控制命令超时
CONTROL_STATUS_UNSUPPORTED = "UNSUPPORTED"           # 不支持的操作


class ControlResultGenerator:
    """控制回写响应生成器。

    根据控制类型、目标值和设备状态生成控制执行结果。
    支持多种回写状态，可在构造时注入自定义结果生成函数。

    确定性保证：
    所有决策使用 deterministic_seed 初始化的 RNG，
    相同 seed 和输入产生相同结果序列。

    Attributes:
        _rng: 确定性伪随机数生成器。
        _scenario_id: 关联的场景标识。
        _control_counter: 全局控制编号计数器，保证 control_id 唯一。
        _custom_handlers: 控制类型 -> 结果生成函数的映射。
    """

    def __init__(
        self,
        *,
        scenario_id: str,
        deterministic_seed: int = 42,
        custom_handlers: dict[str, Callable[..., GeneratedControlResult]] | None = None,
    ) -> None:
        """初始化控制结果生成器。

        Args:
            scenario_id: 场景唯一标识，所有控制结果的 control_id 前缀。
            deterministic_seed: 确定性随机种子。
            custom_handlers: 自定义控制结果处理器字典，
                key 为 control_type，value 为生成函数。
                未指定的类型使用内置默认处理。
        """
        self._rng = random.Random(deterministic_seed)
        self._scenario_id = scenario_id
        self._control_counter = 0
        self._custom_handlers = custom_handlers or {}

    def generate(
        self,
        *,
        entity: SeedEntity,
        control_type: str,
        target_value: float = 0.0,
        timestamp: datetime | None = None,
    ) -> GeneratedControlResult:
        """生成单条控制回写结果。

        根据控制类型和实体信息生成控制执行结果。
        默认行为按照确定性规则选择合理的结果状态。

        Args:
            entity: 目标种子实体。
            control_type: 控制类型（如 "START"、"STOP"、"SETPOINT"）。
            target_value: 控制目标值。
            timestamp: 控制执行时间，None 时使用当前 UTC 时间。

        Returns:
            完整 GeneratedControlResult 实例。

        Raises:
            ValueError: 当 control_type 为空字符串时。
        """
        if not control_type:
            raise ValueError("control_type 不能为空字符串")

        ts = timestamp or datetime.now(timezone.utc)

        # 优先使用自定义处理器
        if control_type in self._custom_handlers:
            return self._custom_handlers[control_type](
                entity=entity,
                control_type=control_type,
                target_value=target_value,
                timestamp=ts,
            )

        # 默认行为：根据控制类型确定性选择结果
        status, result_value, message = self._default_result(
            entity=entity,
            control_type=control_type,
            target_value=target_value,
        )

        return self._build_result(
            entity=entity,
            control_type=control_type,
            target_value=target_value,
            status=status,
            result_value=result_value,
            timestamp=ts,
            message=message,
        )

    def generate_batch(
        self,
        *,
        entity: SeedEntity,
        controls: list[tuple[str, float]],
        timestamp: datetime | None = None,
    ) -> list[GeneratedControlResult]:
        """批量生成控制回写结果。

        Args:
            entity: 目标种子实体。
            controls: 控制操作列表，每项为 (control_type, target_value) 元组。
            timestamp: 批量控制的时间戳，None 时使用当前 UTC 时间。

        Returns:
            控制回写结果列表，长度与 controls 一致。
        """
        ts = timestamp or datetime.now(timezone.utc)
        results: list[GeneratedControlResult] = []
        for ctrl_type, target_val in controls:
            results.append(self.generate(
                entity=entity,
                control_type=ctrl_type,
                target_value=target_val,
                timestamp=ts,
            ))
        return results

    def _default_result(
        self,
        *,
        entity: SeedEntity,
        control_type: str,
        target_value: float,
    ) -> tuple[str, float, str]:
        """确定默认控制结果。

        使用确定性算法选择结果状态：
        基于 (control_type, entity_id, target_value) 生成 hash seed，
        确保相同输入产生相同结果。

        Args:
            entity: 目标实体。
            control_type: 控制类型。
            target_value: 目标值。

        Returns:
            (status, result_value, message) 三元组。
        """
        # 对不支持的操作类型直接返回不支持
        unsupported_types = {"REBOOT", "FIRMWARE_UPDATE", "FACTORY_RESET"}
        if control_type in unsupported_types:
            return CONTROL_STATUS_UNSUPPORTED, 0.0, f"不支持的操作类型: {control_type}"

        # 基于确定性 seed 选择结果
        # 使用 entity_id + control_type (+ target_value) 与 RNG 混合
        sub_seed = hash((entity.entity_id, control_type, target_value)) & 0x7FFFFFFF
        sub_rng = random.Random(sub_seed ^ self._rng.randint(0, 2**31 - 1))
        roll = sub_rng.random()

        # 概率分布（保证可重现）：
        # ACCEPTED 60%, TIMEOUT 10%, READBACK_MATCHED 15%,
        # READBACK_MISMATCH 8%, WRITE_DISABLED 5%, UNSUPPORTED 2%
        if roll < 0.60:
            return CONTROL_STATUS_ACCEPTED, target_value, f"控制已接受: {control_type}"
        elif roll < 0.70:
            return CONTROL_STATUS_TIMEOUT, 0.0, f"控制超时: {control_type}"
        elif roll < 0.85:
            # 回读匹配：写后回读值与目标值一致
            return CONTROL_STATUS_READBACK_MATCHED, target_value, f"回读匹配: {control_type}"
        elif roll < 0.93:
            # 回读不匹配：实际值与目标值存在小偏差
            mismatch = target_value * (1.0 + sub_rng.uniform(-0.05, 0.05))
            return CONTROL_STATUS_READBACK_MISMATCH, round(mismatch, 3), f"回读不匹配: target={target_value}, actual={mismatch:.3f}"
        elif roll < 0.98:
            return CONTROL_STATUS_WRITE_DISABLED, 0.0, f"写功能已禁用: {control_type}"
        else:
            return CONTROL_STATUS_UNSUPPORTED, 0.0, f"操作不被当前设备支持: {control_type}"

    def _build_result(
        self,
        *,
        entity: SeedEntity,
        control_type: str,
        target_value: float,
        status: str,
        result_value: float,
        timestamp: datetime,
        message: str,
    ) -> GeneratedControlResult:
        """构造单条控制回写结果。

        control_id 使用全局计数器保证唯一性。

        Args:
            entity: 目标实体。
            control_type: 控制类型。
            target_value: 目标值。
            status: 执行状态。
            result_value: 实际结果值。
            timestamp: 执行时间戳。
            message: 结果描述。

        Returns:
            完整 GeneratedControlResult 实例。
        """
        self._control_counter += 1
        control_id = f"{self._scenario_id}_ctrl_{self._control_counter:05d}"
        return GeneratedControlResult(
            control_id=control_id,
            entity_id=entity.entity_id,
            control_type=control_type,
            target_value=target_value,
            result_value=result_value,
            status=status,
            timestamp=timestamp,
            message=message,
        )


__all__ = [
    "CONTROL_STATUS_ACCEPTED",
    "CONTROL_STATUS_WRITE_DISABLED",
    "CONTROL_STATUS_DRY_RUN_ACCEPTED",
    "CONTROL_STATUS_READBACK_MATCHED",
    "CONTROL_STATUS_READBACK_MISMATCH",
    "CONTROL_STATUS_TIMEOUT",
    "CONTROL_STATUS_UNSUPPORTED",
    "ControlResultGenerator",
]
