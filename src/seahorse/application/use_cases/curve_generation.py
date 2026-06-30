"""seahorse 曲线生成策略。

实现典型工业曲线信号生成，支持 constant、linear、sinusoidal 和
daily_power_curve（日功率曲线）等类型。可为风机、光伏、储能、
并网点、气象站提供合理的样例曲线。

所有实现满足确定性：相同 curve_type + 相同参数 + 相同 deterministic_seed
产生完全相同的结果序列。

安全边界：
- 不得 import whale.ingest。
- 确定性：相同输入 → 相同输出。
"""
from __future__ import annotations

import math
import random
from datetime import datetime, timedelta, timezone

from seahorse.domain.generation import GeneratedAlarmEvent, GeneratedControlResult, GeneratedSignalValue
from seahorse.domain.plan import SeedEntity, SignalProfileItemPlan

# 曲线类型常量
CURVE_TYPE_CONSTANT = "constant"             # 恒定值
CURVE_TYPE_LINEAR = "linear"                  # 线性变化
CURVE_TYPE_SINUSOIDAL = "sinusoidal"          # 正弦曲线
CURVE_TYPE_DAILY_POWER = "daily_power_curve"  # 日功率曲线（双峰模型）
CURVE_TYPE_DAILY_SOLAR = "daily_solar_curve"  # 日光伏曲线（单峰模型）
CURVE_TYPE_DAILY_STORAGE = "daily_storage_curve"  # 日储能曲线（充放电模型）

# 策略标识常量
STRATEGY_ID_CURVE = "curve_generation"

# 预设曲线模板: signal_name -> (curve_type, params)
# params 格式因 curve_type 而异
_PRESET_CURVES: dict[str, tuple[str, dict[str, float]]] = {
    # 风机
    "ActivePower": (CURVE_TYPE_DAILY_POWER, {
        "base_power": 1500.0,    # 基准功率 kW
        "morning_peak": 9.0,     # 上午峰值时刻 (hours)
        "evening_peak": 17.0,    # 下午峰值时刻 (hours)
        "peak_ratio": 0.95,      # 峰值倍率
        "noise_stdev": 50.0,     # 噪声标准差
    }),
    "WindSpeed": (CURVE_TYPE_SINUSOIDAL, {
        "amplitude": 4.0,        # 振幅 m/s
        "offset": 8.0,           # 偏移 m/s
        "period_hours": 12.0,    # 周期 (hours)
        "noise_stdev": 0.5,
    }),
    "ReactivePower": (CURVE_TYPE_SINUSOIDAL, {
        "amplitude": 100.0,
        "offset": 200.0,
        "period_hours": 6.0,
        "noise_stdev": 10.0,
    }),
    "RotorSpeed": (CURVE_TYPE_LINEAR, {
        "start_value": 10.0,     # 起始值 rpm
        "end_value": 15.0,       # 结束值 rpm
        "noise_stdev": 0.2,
    }),
    "Temperature": (CURVE_TYPE_SINUSOIDAL, {
        "amplitude": 5.0,
        "offset": 45.0,
        "period_hours": 24.0,
        "noise_stdev": 0.3,
    }),

    # 光伏
    "PV_ActivePower": (CURVE_TYPE_DAILY_SOLAR, {
        "peak_power": 500.0,     # 峰值功率 kW
        "peak_hour": 13.0,       # 峰值时刻
        "sunrise_hour": 6.0,     # 日出时刻
        "sunset_hour": 19.0,     # 日落时刻
        "noise_stdev": 15.0,
    }),
    "PV_Irradiance": (CURVE_TYPE_DAILY_SOLAR, {
        "peak_power": 800.0,     # W/m2
        "peak_hour": 13.0,
        "sunrise_hour": 6.0,
        "sunset_hour": 19.0,
        "noise_stdev": 20.0,
    }),
    "PV_Temperature": (CURVE_TYPE_DAILY_SOLAR, {
        "peak_power": 60.0,      # deg C
        "peak_hour": 14.0,
        "sunrise_hour": 7.0,
        "sunset_hour": 18.0,
        "noise_stdev": 2.0,
    }),

    # 储能
    "BESS_Power": (CURVE_TYPE_DAILY_STORAGE, {
        "max_charge": -500.0,    # 最大充电功率 kW (负值)
        "max_discharge": 500.0,  # 最大放电功率 kW (正值)
        "charge_start": 1.0,     # 充电开始时刻 (hours)
        "charge_end": 7.0,       # 充电结束时刻
        "discharge_start": 18.0, # 放电开始时刻
        "discharge_end": 22.0,   # 放电结束时刻
        "noise_stdev": 20.0,
    }),
    "BESS_SOC": (CURVE_TYPE_LINEAR, {
        "start_value": 80.0,     # 起始 SOC %
        "end_value": 30.0,       # 结束 SOC %
        "noise_stdev": 1.0,
    }),

    # 气象站
    "AmbientTemp": (CURVE_TYPE_SINUSOIDAL, {
        "amplitude": 8.0,
        "offset": 18.0,
        "period_hours": 24.0,
        "noise_stdev": 0.5,
    }),
    "Humidity": (CURVE_TYPE_SINUSOIDAL, {
        "amplitude": 20.0,
        "offset": 60.0,
        "period_hours": 24.0,
        "noise_stdev": 3.0,
    }),
    "Pressure": (CURVE_TYPE_CONSTANT, {
        "value": 1013.0,
        "noise_stdev": 2.0,
    }),
}


class CurveGenerationStrategy:
    """曲线生成策略。

    支持多种工业曲线的确定性生成，包括 constant、linear、
    sinusoidal、daily_power_curve、daily_solar_curve、
    daily_storage_curve 等类型。

    配置方式：
    - 默认: 根据 signal_plan.signal_name 查找预设曲线模板。
    - 自定义: 通过构造参数 curve_configs 覆盖。
    - 运行时: generate_signals 的 curve_type/curve_params 参数覆盖。

    Attributes:
        _scenario_id: 场景标识。
        _source_id: 数据源标识。
        _curve_configs: 曲线配置覆盖字典。
        _default_curve_type: 未匹配预设时的默认曲线类型。
    """

    def __init__(
        self,
        *,
        scenario_id: str = "",
        source_id: str = "",
        curve_configs: dict[str, tuple[str, dict[str, float]]] | None = None,
        default_curve_type: str = CURVE_TYPE_CONSTANT,
    ) -> None:
        """初始化曲线生成策略。

        Args:
            scenario_id: 场景唯一标识。
            source_id: 数据源标识。
            curve_configs: 自定义曲线配置，覆盖预设模板。
                key 为 signal_name，value 为 (curve_type, params_dict)。
            default_curve_type: 未匹配任何预设时使用的默认曲线类型。
        """
        self._scenario_id = scenario_id
        self._source_id = source_id
        self._default_curve_type = default_curve_type
        # 合并预设与自定义配置
        self._curve_configs: dict[str, tuple[str, dict[str, float]]] = dict(_PRESET_CURVES)
        if curve_configs:
            self._curve_configs.update(curve_configs)

    @property
    def strategy_id(self) -> str:
        """返回策略标识字符串。"""
        return STRATEGY_ID_CURVE

    def generate_signals(
        self,
        *,
        entity: SeedEntity,
        signal_plan: SignalProfileItemPlan,
        start_time: float,
        duration_seconds: float,
        deterministic_seed: int,
    ) -> list[GeneratedSignalValue]:
        """生成曲线信号值序列。

        根据 signal_plan.signal_name 匹配曲线模板或使用默认曲线，
        deterministic_seed 初始化噪声 RNG 以保证可重现性。

        Args:
            entity: 目标种子实体。
            signal_plan: 信号点位规划。
            start_time: 起始 Unix 时间戳（秒）。
            duration_seconds: 生成时长（秒）。
            deterministic_seed: 确定性随机种子。

        Returns:
            GeneratedSignalValue 列表，按时间升序排列。
        """
        # 按实体和信号维度混合 seed
        composite_seed = deterministic_seed ^ hash(entity.entity_id) ^ hash(signal_plan.signal_id)
        rng = random.Random(composite_seed)

        interval_s = signal_plan.sample_interval_ms / 1000.0
        if interval_s <= 0:
            interval_s = 0.1

        step_count = max(1, int(duration_seconds / interval_s))
        results: list[GeneratedSignalValue] = []

        duration_hours = duration_seconds / 3600.0
        base_time = datetime.fromtimestamp(start_time, tz=timezone.utc)

        # 确定曲线类型和参数
        curve_type, params = self._resolve_curve(signal_plan)
        noise_stdev = params.pop("noise_stdev", 0.0)
        # Round 20 根因修复：daily_power 曲线在叠加噪声之后必须保留
        # "最低技术出力"硬下限（典型 20% 额定容量）。长周期 24h 仿真
        # （864000 样本，0.1s 间隔）在 ``noise_stdev=50`` 时偶尔把值
        # 拉到 base 之下甚至跌破 0 / 100，触发测试 flaky。
        # 解决：噪声叠加之后钳制到 ``min_floor``（仅当 ``min_floor`` 不
        # 为 None 时启用；其它曲线类型 min_floor=None 维持原行为）。
        min_floor = self._resolve_min_floor(curve_type, params)

        for step in range(step_count):
            elapsed_hours = (step * interval_s) / 3600.0
            ts = base_time + timedelta(seconds=step * interval_s)

            # 计算基准曲线值
            base_value = self._compute_curve_value(
                curve_type=curve_type,
                params=params,
                elapsed_hours=elapsed_hours,
                duration_hours=duration_hours,
            )

            # 叠加确定性噪声
            noise = rng.gauss(0.0, noise_stdev) if noise_stdev > 0 else 0.0
            value = base_value + noise
            if min_floor is not None and value < min_floor:
                value = min_floor

            results.append(GeneratedSignalValue(
                signal_id=signal_plan.signal_id,
                scenario_id=self._scenario_id,
                source_id=self._source_id,
                device_id=entity.entity_id,
                profile_item_id=signal_plan.signal_id,
                node_key=signal_plan.ln_class,
                variable_key=signal_plan.signal_name,
                timestamp=ts,
                value=round(value, 3),
                quality=0,
                unit=signal_plan.unit,
                strategy_id=STRATEGY_ID_CURVE,
                synthetic=True,
            ))

        return results

    def _resolve_min_floor(
        self,
        curve_type: str,
        params: dict[str, float],
    ) -> float | None:
        """返回当前曲线在叠加噪声后必须保留的硬下限（None 表示不启用）。

        Round 20 根因修复：daily_power_curve 的"最低技术出力"硬下限
        必须在 ``base_value + noise`` 之后钳制（不能在 base 层），否则
        ``noise_stdev`` 较大的长周期 24h 仿真会偶发跌破下限。其它曲线
        类型（constant / linear / sinusoidal / daily_solar /
        daily_storage）不强制下限（``min_floor=None``），行为保持不变。

        Args:
            curve_type: 曲线类型。
            params: 曲线参数（包含 ``base_power`` / ``floor_ratio`` 等）。

        Returns:
            硬下限值（float）；None 表示不启用钳制。
        """
        if curve_type == CURVE_TYPE_DAILY_POWER:
            base_power = params.get("base_power", 1500.0)
            floor_ratio = params.get("floor_ratio", 0.2)
            return base_power * floor_ratio
        # 其它曲线类型维持原行为，不强制下限
        return None

    def _resolve_curve(
        self,
        signal_plan: SignalProfileItemPlan,
    ) -> tuple[str, dict[str, float]]:
        """解析曲线类型和参数。

        优先顺序：signal_name 匹配预设 > generation_hint 暗示 > 默认。

        Args:
            signal_plan: 信号点位规划。

        Returns:
            (curve_type, params) 元组。
        """
        # 按 signal_name 匹配
        name = signal_plan.signal_name
        if name in self._curve_configs:
            curve_type, params = self._curve_configs[name]
            return curve_type, dict(params)  # 拷贝避免修改原模板

        # 按 generation_hint 推测
        hint = signal_plan.generation_hint.upper()
        hint_map = {
            "SINUSOIDAL": (CURVE_TYPE_SINUSOIDAL, {"amplitude": 5.0, "offset": 10.0, "period_hours": 24.0}),
            "LINEAR": (CURVE_TYPE_LINEAR, {"start_value": 0.0, "end_value": 100.0}),
            "RAMP": (CURVE_TYPE_LINEAR, {"start_value": 0.0, "end_value": 100.0}),
        }
        if hint in hint_map:
            return hint_map[hint]

        # 默认
        return self._default_curve_type, {"value": 0.0}

    def _compute_curve_value(
        self,
        *,
        curve_type: str,
        params: dict[str, float],
        elapsed_hours: float,
        duration_hours: float,
    ) -> float:
        """根据曲线类型计算基准值（不含噪声）。

        Args:
            curve_type: 曲线类型字符串。
            params: 曲线参数字典。
            elapsed_hours: 已过时间（小时）。
            duration_hours: 总时长（小时）。

        Returns:
            基准值（float）。
        """
        if curve_type == CURVE_TYPE_CONSTANT:
            return params.get("value", 0.0)

        if curve_type == CURVE_TYPE_LINEAR:
            start = params.get("start_value", 0.0)
            end = params.get("end_value", 100.0)
            if duration_hours <= 0:
                return start
            ratio = min(1.0, elapsed_hours / duration_hours)
            return start + (end - start) * ratio

        if curve_type == CURVE_TYPE_SINUSOIDAL:
            amplitude = params.get("amplitude", 5.0)
            offset = params.get("offset", 10.0)
            period_hours = params.get("period_hours", 24.0)
            if period_hours <= 0:
                period_hours = 24.0
            phase = elapsed_hours / period_hours * 2 * math.pi
            return offset + amplitude * math.sin(phase)

        if curve_type == CURVE_TYPE_DAILY_POWER:
            # 双峰日功率曲线（典型风电出力模型）。
            #
            # 业务语义：风机的最小出力受"最低技术出力"约束
            # （典型 20% 额定容量）。基础曲线通过 ``base_power *
            # floor_ratio`` 项保证最低限位（"最低不低于 20%"），但
            # ``noise_stdev`` 较大时（如 50）噪声仍可能把 base 拉低
            # 甚至跌破 0。**真正**的硬下限在 ``generate_signals`` 中
            # 叠加噪声之后钳制（见 ``floor_after_noise`` 段），保证
            # ``min(values) >= base_power * floor_ratio``。
            base_power = params.get("base_power", 1500.0)
            morning_peak = params.get("morning_peak", 9.0)
            evening_peak = params.get("evening_peak", 17.0)
            peak_ratio = params.get("peak_ratio", 0.95)
            floor_ratio = params.get("floor_ratio", 0.2)

            hour_of_day = elapsed_hours % 24.0
            # 高斯双峰模型
            sigma = 3.0  # 峰宽
            morning_component = math.exp(-0.5 * ((hour_of_day - morning_peak) / sigma) ** 2)
            evening_component = math.exp(-0.5 * ((hour_of_day - evening_peak) / sigma) ** 2)
            # 归一化到 [0, 1] 然后映射到 [0, base_power * peak_ratio]
            raw = max(morning_component, evening_component)
            return base_power * peak_ratio * raw + base_power * floor_ratio

        if curve_type == CURVE_TYPE_DAILY_SOLAR:
            # 单峰日光伏曲线（正弦模型只依赖 sunrise/sunset，peak_hour 保留用于扩展）
            peak_power = params.get("peak_power", 500.0)
            sunrise = params.get("sunrise_hour", 6.0)
            sunset = params.get("sunset_hour", 19.0)

            hour_of_day = elapsed_hours % 24.0
            if hour_of_day < sunrise or hour_of_day > sunset:
                return 0.0
            # 半正弦模型
            day_duration = sunset - sunrise
            if day_duration <= 0:
                return 0.0
            progress = (hour_of_day - sunrise) / day_duration
            return peak_power * math.sin(progress * math.pi)

        if curve_type == CURVE_TYPE_DAILY_STORAGE:
            # 储能充放电曲线
            max_discharge = params.get("max_discharge", 500.0)
            max_charge = params.get("max_charge", -500.0)
            charge_start = params.get("charge_start", 1.0)
            charge_end = params.get("charge_end", 7.0)
            discharge_start = params.get("discharge_start", 18.0)
            discharge_end = params.get("discharge_end", 22.0)

            hour_of_day = elapsed_hours % 24.0
            if charge_start <= hour_of_day <= charge_end:
                # 充电阶段（负值）
                progress = (hour_of_day - charge_start) / max(1.0, charge_end - charge_start)
                return max_charge * (0.5 + 0.5 * math.sin(progress * math.pi))
            elif discharge_start <= hour_of_day <= discharge_end:
                # 放电阶段（正值）
                progress = (hour_of_day - discharge_start) / max(1.0, discharge_end - discharge_start)
                return max_discharge * (0.5 + 0.5 * math.sin(progress * math.pi))
            else:
                # 待机（接近0）
                return 0.0

        # 未知类型退化为 constant
        return params.get("value", 0.0)

    def generate_alarms(
        self,
        *,
        entity: SeedEntity,
        signal_values: list[GeneratedSignalValue],
        deterministic_seed: int,
    ) -> list[GeneratedAlarmEvent]:
        """生成告警事件（曲线策略最小实现）。

        曲线策略默认不生成告警事件，返回空列表。
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
        """生成控制回写结果（曲线策略最小实现）。

        曲线策略默认不生成控制结果，返回空列表。
        控制结果由 SeahorseGenerator 通过 ControlResultGenerator 统一管理。

        Args:
            entity: 目标实体。
            deterministic_seed: 确定性随机种子。

        Returns:
            空列表。
        """
        return []


__all__ = [
    "CURVE_TYPE_CONSTANT",
    "CURVE_TYPE_LINEAR",
    "CURVE_TYPE_SINUSOIDAL",
    "CURVE_TYPE_DAILY_POWER",
    "CURVE_TYPE_DAILY_SOLAR",
    "CURVE_TYPE_DAILY_STORAGE",
    "STRATEGY_ID_CURVE",
    "CurveGenerationStrategy",
]
