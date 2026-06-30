"""seahorse 告警事件生成器。

本模块提供从信号值序列中检测并生成告警事件的能力，
支持阈值告警、设备状态告警、通信告警和品质降级告警。

所有生成结果均为 `GeneratedAlarmEvent`，不写入数据库或
外部系统，仅作为内存结果返回。

安全边界：
- 本模块不得 import whale.ingest。
- 本模块不得访问生产数据库。
- 确定性：相同输入 + 相同 deterministic_seed 产生相同输出。
"""
from __future__ import annotations

import random
from datetime import datetime

from seahorse.domain.generation import GeneratedAlarmEvent, GeneratedSignalValue
from seahorse.domain.plan import SeedEntity


# 告警类型常量，用于统一引用和扩展
ALARM_TYPE_THRESHOLD = "THRESHOLD"        # 阈值告警：信号值超出预设阈值范围
ALARM_TYPE_DEVICE_STATE = "DEVICE_STATE"   # 设备状态告警：设备运行状态异常
ALARM_TYPE_COMMUNICATION = "COMMUNICATION" # 通信告警：通信链路或协议异常
ALARM_TYPE_QUALITY = "QUALITY"             # 品质降级告警：信号品质码非 0


class AlarmGenerator:
    """告警事件生成器。

    根据信号值序列和设备信息生成告警事件，支持多种告警类型。
    不修改输入数据，不访问外部系统。

    确定性保证：
    所有随机决策使用 deterministic_seed 初始化的 RNG，
    相同 seed 和输入产生相同告警序列。

    Attributes:
        _rng: 确定性伪随机数生成器。
        _scenario_id: 关联的场景标识。
        _alarm_counter: 全局告警编号计数器，保证 alarm_id 唯一。
        _thresholds: 阈值规则字典，key 为 variable_key，value 为 (min, max) 元组。
    """

    def __init__(
        self,
        *,
        scenario_id: str,
        deterministic_seed: int = 42,
        thresholds: dict[str, tuple[float, float]] | None = None,
    ) -> None:
        """初始化告警生成器。

        Args:
            scenario_id: 场景唯一标识，所有生成告警的 alarm_id 前缀。
            deterministic_seed: 确定性随机种子。
            thresholds: 自定义阈值规则，格式为 {variable_key: (min, max)}。
                未指定的变量使用内置默认阈值。
        """
        self._rng = random.Random(deterministic_seed)
        self._scenario_id = scenario_id
        self._alarm_counter = 0
        self._thresholds = self._default_thresholds()
        if thresholds:
            self._thresholds.update(thresholds)

    @staticmethod
    def _default_thresholds() -> dict[str, tuple[float, float]]:
        """返回内置默认阈值规则。

        覆盖风电场景常见告警边界。阈值按照 GB/T 30966 参考值设定。

        Returns:
            默认阈值字典，key 为变量名，value 为 (最小值, 最大值)。
        """
        return {
            # 有功功率应在额定范围 0~1600 kW 内
            "ActivePower": (0.0, 1600.0),
            # 风速正常范围 0~40 m/s
            "WindSpeed": (0.0, 40.0),
            # 转子转速 0~20 rpm
            "RotorSpeed": (0.0, 20.0),
            # 温度 -20~80 deg C
            "Temperature": (-20.0, 80.0),
            # 发电机温度 -20~120 deg C
            "SttTmp": (-20.0, 120.0),
            # 振动 > 0.5 m/s2 触发告警
            "VbrX": (0.0, 0.5),
            "VbrY": (0.0, 0.5),
            "VbrZ": (0.0, 0.5),
        }

    def generate(
        self,
        *,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """从信号值序列生成告警事件。

        对每条信号值执行阈值检查、品质检查和设备状态检查，
        符合告警条件则生成对应告警事件。

        Args:
            entity: 目标种子实体。
            signal_values: 信号值序列，按时间升序排列。

        Returns:
            生成的告警事件列表，始终包含 alarm_id、entity_id、
            alarm_type、severity、timestamp 等完整字段。
        """
        alarms: list[GeneratedAlarmEvent] = []

        if not signal_values:
            return alarms

        # 阈值检查：对所有 MEASUREMENT 类信号进行阈值检测
        alarms.extend(self._check_thresholds(entity, signal_values))

        # 品质降级检查：品质码非 0 的信号
        alarms.extend(self._check_quality(entity, signal_values))

        # 设备状态检查：基于实体类型和信号值判断设备异常
        alarms.extend(self._check_device_state(entity, signal_values))

        # 通信告警：基于信号值缺失或零值模式判断
        alarms.extend(self._check_communication(entity, signal_values))

        return alarms

    def _check_thresholds(
        self,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """阈值告警检测。

        对匹配阈值规则的信号值进行 min/max 边界检查。
        每条越限信号值生成一条告警。

        Args:
            entity: 目标种子实体。
            signal_values: 信号值序列。

        Returns:
            阈值告警事件列表。
        """
        alarms: list[GeneratedAlarmEvent] = []
        for sv in signal_values:
            varkey = sv.variable_key or sv.signal_id
            if varkey not in self._thresholds:
                continue
            lo, hi = self._thresholds[varkey]
            if sv.value < lo:
                alarms.append(self._build_alarm(
                    entity=entity,
                    alarm_type=ALARM_TYPE_THRESHOLD,
                    severity="MAJOR",
                    timestamp=sv.timestamp,
                    message=f"{varkey} 低于阈值: value={sv.value}, threshold={lo}",
                ))
            elif sv.value > hi:
                alarms.append(self._build_alarm(
                    entity=entity,
                    alarm_type=ALARM_TYPE_THRESHOLD,
                    severity="MAJOR",
                    timestamp=sv.timestamp,
                    message=f"{varkey} 超过阈值: value={sv.value}, threshold={hi}",
                ))
        return alarms

    def _check_quality(
        self,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """品质降级告警检测。

        检测品质码非 0 的信号值，品质码 1 为 uncertain（WARNING），
        品质码 2 及以上为 bad（MAJOR）。

        Args:
            entity: 目标种子实体。
            signal_values: 信号值序列。

        Returns:
            品质降级告警事件列表。
        """
        alarms: list[GeneratedAlarmEvent] = []
        for sv in signal_values:
            if sv.quality == 0:
                continue
            severity = "MAJOR" if sv.quality >= 2 else "WARNING"
            alarms.append(self._build_alarm(
                entity=entity,
                alarm_type=ALARM_TYPE_QUALITY,
                severity=severity,
                timestamp=sv.timestamp,
                message=f"信号品质降级: quality={sv.quality}, signal_id={sv.signal_id}",
            ))
        return alarms

    def _check_device_state(
        self,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """设备状态告警检测。

        基于信号值模式判断设备运行状态。例如连续多点为 0 表示停机，
        但当前仅对状态类信号（quality code 或离散值）做基础检查。

        Args:
            entity: 目标种子实体。
            signal_values: 信号值序列。

        Returns:
            设备状态告警事件列表。
        """
        alarms: list[GeneratedAlarmEvent] = []
        if not signal_values:
            return alarms

        # 检查最后几个信号值，判断是否存在全零（疑似停机）模式
        window = signal_values[-min(10, len(signal_values)):]
        # 对信号值做全零检查（覆盖所有类型信号）
        all_zero = all(sv.value == 0.0 for sv in window)
        if all_zero and len(window) >= 5:
            # 连续 5 个以上全零意味着设备可能异常停机
            severity = "CRITICAL"
            message = f"设备疑似异常停机: 连续 {len(window)} 个信号点为 0"
        elif all_zero:
            severity = "WARNING"
            message = f"设备信号异常: 连续 {len(window)} 个信号点为 0"
        else:
            return alarms

        alarms.append(self._build_alarm(
            entity=entity,
            alarm_type=ALARM_TYPE_DEVICE_STATE,
            severity=severity,
            timestamp=signal_values[-1].timestamp,
            message=message,
        ))
        return alarms

    def _check_communication(
        self,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """通信告警检测。

        通过信号值的时间间隔判断通信状态。
        使用确定性随机决策模拟通信断链模式：

        - 时间跨度超过窗口且信号数少于一小时的预期值
          视为通信异常。

        注意：本方法使用 RNG 模拟通信异常，因此相同 seed 产生一致结果。

        Args:
            entity: 目标种子实体。
            signal_values: 信号值序列。

        Returns:
            通信告警事件列表。
        """
        if len(signal_values) < 2:
            return []

        first_ts = signal_values[0].timestamp
        last_ts = signal_values[-1].timestamp
        duration_hours = (last_ts - first_ts).total_seconds() / 3600.0

        # 如果时间跨度超过 1 小时但信号数少于 30，可能存在通信断链
        # 使用 RNG 做确定性决策
        if duration_hours > 1.0 and len(signal_values) < 30:
            # 确定性模拟: 每小时有 10% 概率触发通信告警（基于 seed）
            if self._rng.random() < 0.1:
                return [self._build_alarm(
                    entity=entity,
                    alarm_type=ALARM_TYPE_COMMUNICATION,
                    severity="MAJOR",
                    timestamp=last_ts,
                    message=f"通信异常: {duration_hours:.1f}h 内仅收到 {len(signal_values)} 个信号",
                )]

        return []

    def _build_alarm(
        self,
        *,
        entity: SeedEntity,
        alarm_type: str,
        severity: str,
        timestamp: datetime,
        message: str,
    ) -> GeneratedAlarmEvent:
        """构造单条告警事件。

        alarm_id 使用全局计数器保证唯一性。

        Args:
            entity: 目标实体。
            alarm_type: 告警类型。
            severity: 严重等级。
            timestamp: 告警时间。
            message: 告警描述。

        Returns:
            完整 GeneratedAlarmEvent 实例。
        """
        self._alarm_counter += 1
        alarm_id = f"{self._scenario_id}_alarm_{self._alarm_counter:05d}"
        return GeneratedAlarmEvent(
            alarm_id=alarm_id,
            entity_id=entity.entity_id,
            alarm_type=alarm_type,
            severity=severity,
            timestamp=timestamp,
            message=message,
        )


__all__ = [
    "ALARM_TYPE_THRESHOLD",
    "ALARM_TYPE_DEVICE_STATE",
    "ALARM_TYPE_COMMUNICATION",
    "ALARM_TYPE_QUALITY",
    "AlarmGenerator",
]
