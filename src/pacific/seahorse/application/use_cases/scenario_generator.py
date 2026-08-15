"""seahorse 场景生成编排器 —— SeahorseGenerator。

负责解析场景配置，调用生成策略，装配种子计划和服务器计划，
并生成连续信号值序列、告警事件和控制回写结果。
是 Seahorse 的顶层入口，不直接处理数据库或协议细节。

安全边界：
- 不访问生产数据库。
- 不 import whale.ingest。
- 确定性：相同输入总是产生相同输出。
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import asdict
from typing import TYPE_CHECKING

from pacific.seahorse.domain.scenario import ScenarioConfig, ScenarioMetadata
from pacific.seahorse.domain.plan import (
    AcquisitionTaskPlan,
    EndpointPlan,
    SeedEntity,
    SeedPlan,
    ServerConfig,
    ServerEndpointConfig,
    ServerMemberConfig,
    ServerPointConfig,
    SignalProfileItemPlan,
    SignalProfilePlan,
)
from pacific.seahorse.domain.generation import (
    GeneratedAlarmEvent,
    GeneratedControlResult,
    GeneratedSignalValue,
)

if TYPE_CHECKING:
    from pacific.seahorse.application.ports.generation_strategy_port import GenerationStrategy
    from pacific.seahorse.application.use_cases.strategy_registry import StrategyRegistry


class SeahorseGenerator:
    """Seahorse 场景生成器 —— 根据 ScenarioConfig 产生完整的样例场站数据。

    支持注册一个或多个 GenerationStrategy，根据实体类型和信号规划
    生成确定性信号值序列。同时支持告警事件和控制回写结果的独立生成。

    确定性保证：
    所有生成操作使用 deterministic_seed 初始化的伪随机数生成器，
    相同 config 产生相同的 seed_plan、server_config、信号值、告警和控制结果。

    Attributes:
        _config: 当前生成使用的场景配置。
        _metadata: 生成元数据，包含版本、时间戳和统计信息。
        _rng: 由 deterministic_seed 初始化的伪随机数生成器。
        _registry: 策略注册表（可选）。
        _default_strategy: 未匹配注册表时的默认策略。
        _signal_values: 最近一次生成的信号值缓存（用于告警检测）。
    """

    def __init__(
        self,
        config: ScenarioConfig,
        *,
        registry: "StrategyRegistry | None" = None,
        default_strategy: "GenerationStrategy | None" = None,
    ) -> None:
        """初始化生成器。

        Args:
            config: 场景配置，其中 deterministic_seed 将用于初始化伪随机数生成器。
            registry: 可选的策略注册表，用于按实体类型选择策略。
            default_strategy: 注册表未匹配时的默认策略。
        """
        self._config = config
        self._rng = random.Random(config.deterministic_seed)
        self._metadata = ScenarioMetadata(
            scenario_id=config.scenario_id,
            config_snapshot=asdict(config),
        )
        self._registry = registry
        self._default_strategy = default_strategy
        self._signal_values: list[GeneratedSignalValue] = []

    @property
    def config(self) -> ScenarioConfig:
        """返回当前场景配置（只读）。"""
        return self._config

    @property
    def metadata(self) -> ScenarioMetadata:
        """返回生成元数据。"""
        return self._metadata

    @property
    def registry(self) -> "StrategyRegistry | None":
        """返回当前注册的策略注册表（只读）。"""
        return self._registry

    @property
    def signal_values(self) -> list[GeneratedSignalValue]:
        """返回最近一次生成的信号值序列（只读）。"""
        return list(self._signal_values)

    def set_strategy(
        self,
        strategy: "GenerationStrategy",
    ) -> None:
        """设置默认生成策略。

        注册表同时存在时，该方法设置的策略仅在注册表未匹配时生效。

        Args:
            strategy: GenerationStrategy 实现实例。
        """
        self._default_strategy = strategy

    def set_registry(self, registry: "StrategyRegistry") -> None:
        """设置策略注册表。

        Args:
            registry: StrategyRegistry 实例。
        """
        self._registry = registry

    def _resolve_strategy(
        self,
        entity: SeedEntity,
    ) -> "GenerationStrategy":
        """按实体类型解析策略。

        优先使用注册表中的实体类型覆盖，其次默认策略。

        Args:
            entity: 目标种子实体。

        Returns:
            GenerationStrategy 实例。

        Raises:
            ValueError: 如果既无注册表也无默认策略。
        """
        from pacific.seahorse.application.use_cases.random_generation import RandomGenerationStrategy

        if self._registry:
            try:
                return self._registry.get_for_entity(entity.entity_type)
            except (KeyError, ValueError):
                pass

        if self._default_strategy:
            return self._default_strategy

        # 最终 fallback: 内置随机策略
        return RandomGenerationStrategy(
            scenario_id=self._config.scenario_id,
            source_id=self._config.protocol_targets[0] if self._config.protocol_targets else "OPC_UA",
        )

    def generate(
        self,
    ) -> tuple[SeedPlan, ServerConfig, list[GeneratedSignalValue], list[GeneratedAlarmEvent], list[GeneratedControlResult]]:
        """执行完整场景生成。

        生成顺序：SeedPlan → ServerConfig → 信号值 → 告警事件 → 控制结果。

        Returns:
            (seed_plan, server_config, signal_values, alarm_events, control_results) 五元组。
            信号值按时间升序排列，告警按触发时间排序，控制结果按生成序。
        """
        seed_plan = self._build_minimal_seed_plan()
        server_config = self._build_minimal_server_config()

        # 生成信号值序列
        signal_values = self._generate_all_signals(seed_plan)

        # 基于信号值生成告警事件
        alarm_events = self._generate_all_alarms(seed_plan, signal_values)

        # 生成控制回写结果
        control_results = self._generate_all_controls(seed_plan)

        # 缓存信号值供外部查询
        self._signal_values = signal_values

        # 更新元数据统计
        self._metadata.stats = {
            "entity_count": len(seed_plan.entities),
            "signal_value_count": len(signal_values),
            "alarm_count": len(alarm_events),
            "control_result_count": len(control_results),
        }

        return seed_plan, server_config, signal_values, alarm_events, control_results

    def generate_minimal(
        self,
    ) -> tuple[SeedPlan, ServerConfig]:
        """执行最小场景生成（仅生成计划容器，不生成信号/告警/控制）。

        保持向后兼容，与 Round 1 的行为一致。

        Returns:
            (seed_plan, server_config) 元组。
        """
        seed_plan = self._build_minimal_seed_plan()
        server_config = self._build_minimal_server_config()
        return seed_plan, server_config

    def _generate_all_signals(
        self,
        seed_plan: SeedPlan,
    ) -> list[GeneratedSignalValue]:
        """为种子计划中所有实体和信号点位生成信号值。

        对每个实体的每个信号点位，调用对应策略的 generate_signals()。
        信号值按 (entity_id, signal_id, timestamp) 排序。

        Args:
            seed_plan: 种子计划。

        Returns:
            所有生成的信号值列表，按时间升序排列。
        """
        all_signals: list[GeneratedSignalValue] = []
        start_time_epoch = self._config.start_time.timestamp()
        duration = self._config.duration_seconds

        for entity in seed_plan.entities:
            strategy = self._resolve_strategy(entity)

            for profile in seed_plan.signal_profiles:
                # 简化匹配: profile_id 包含 entity 前缀
                if not profile.profile_id.startswith(self._config.scenario_id):
                    continue

                for item in profile.items:
                    # 为每个信号点位创建独立的 deterministic_seed
                    item_seed = self._config.deterministic_seed ^ hash(item.signal_id)

                    signals = strategy.generate_signals(
                        entity=entity,
                        signal_plan=item,
                        start_time=start_time_epoch,
                        duration_seconds=duration,
                        deterministic_seed=item_seed,
                    )
                    all_signals.extend(signals)

        # 按时间排序
        all_signals.sort(key=lambda sv: sv.timestamp)
        return all_signals

    def _generate_all_alarms(
        self,
        seed_plan: SeedPlan,
        signal_values: list[GeneratedSignalValue],
    ) -> list[GeneratedAlarmEvent]:
        """基于信号值序列生成告警事件。

        为每个实体分别调用 AlarmGenerator，按 entity_id 分组信号值
        后生成告警。

        Args:
            seed_plan: 种子计划。
            signal_values: 已生成的信号值序列。

        Returns:
            告警事件列表，按触发时间排序。
        """
        from pacific.seahorse.application.use_cases.alarm_generator import AlarmGenerator

        all_alarms: list[GeneratedAlarmEvent] = []

        # 按 entity_id 分组信号值
        entity_signals: dict[str, list[GeneratedSignalValue]] = {}
        for sv in signal_values:
            eid = sv.device_id or ""
            if eid not in entity_signals:
                entity_signals[eid] = []
            entity_signals[eid].append(sv)

        for entity in seed_plan.entities:
            alarm_gen = AlarmGenerator(
                scenario_id=self._config.scenario_id,
                deterministic_seed=self._config.deterministic_seed ^ hash(entity.entity_id),
            )
            alarms = alarm_gen.generate(
                entity=entity,
                signal_values=entity_signals.get(entity.entity_id, []),
            )
            all_alarms.extend(alarms)

        all_alarms.sort(key=lambda a: a.timestamp)
        return all_alarms

    def _generate_all_controls(
        self,
        seed_plan: SeedPlan,
    ) -> list[GeneratedControlResult]:
        """为所有实体生成样例控制回写结果。

        对每个实体生成一组典型控制命令的响应（启动、停止、设值等）。

        Args:
            seed_plan: 种子计划。

        Returns:
            控制回写结果列表。
        """
        from pacific.seahorse.application.use_cases.control_result_generator import ControlResultGenerator

        all_controls: list[GeneratedControlResult] = []
        # 典型控制类型
        default_control_types = [
            ("START", 1.0),
            ("STOP", 0.0),
            ("SETPOINT", 1500.0),
            ("SETPOINT", 0.95),
        ]

        for entity in seed_plan.entities:
            ctrl_gen = ControlResultGenerator(
                scenario_id=self._config.scenario_id,
                deterministic_seed=self._config.deterministic_seed ^ hash(entity.entity_id),
            )
            controls = ctrl_gen.generate_batch(
                entity=entity,
                controls=default_control_types,
                timestamp=self._config.start_time,
            )
            all_controls.extend(controls)

        return all_controls

    def _build_minimal_seed_plan(self) -> SeedPlan:
        """构建最小种子计划。

        根据 asset_count 创建对应数量的 SeedEntity，
        并为每个实体创建默认信号点表和端点规划。
        """
        entities: list[SeedEntity] = []
        signal_profiles: list[SignalProfilePlan] = []
        endpoints: list[EndpointPlan] = []
        tasks: list[AcquisitionTaskPlan] = []

        for i in range(self._config.asset_count):
            entity_id = f"{self._config.scenario_id}_entity_{i:03d}"
            entity = SeedEntity(
                entity_id=entity_id,
                entity_type="WTG",
                display_name=f"风机 {i + 1:02d}",
            )
            entities.append(entity)

            profile_id = f"{self._config.scenario_id}_profile_{i:03d}"
            default_items = self._build_default_signal_items(profile_id)
            signal_profiles.append(
                SignalProfilePlan(
                    profile_id=profile_id,
                    profile_name=f"点表 {i + 1:02d}",
                    standard_family="GB_T_30966",
                    items=default_items,
                )
            )

            for protocol in self._config.protocol_targets or ["OPC_UA"]:
                endpoint_id = f"{entity_id}_{protocol}_ep"
                endpoints.append(
                    EndpointPlan(
                        endpoint_id=endpoint_id,
                        application_protocol=protocol,
                        service_type="READ",
                        transport="TCP",
                    )
                )
                tasks.append(
                    AcquisitionTaskPlan(
                        task_id=f"{endpoint_id}_task",
                        acquisition_mode="POLLING",
                        associated_endpoint_id=endpoint_id,
                        associated_profile_id=profile_id,
                    )
                )

        plan_id = f"plan_{self._config.scenario_id}"
        return SeedPlan(
            plan_id=plan_id,
            scenario_id=self._config.scenario_id,
            entities=entities,
            signal_profiles=signal_profiles,
            endpoints=endpoints,
            acquisition_tasks=tasks,
        )

    def _build_minimal_server_config(self) -> ServerConfig:
        """构建最小服务端配置。

        为每个目标协议创建服务端点，为每个种子实体创建默认点位。
        同时填充 Starfish 契约层字段（endpoint_id、host、port、
        capabilities、update_policy、initial_values 等）。
        """
        endpoints: list[ServerEndpointConfig] = []
        points: list[ServerPointConfig] = []

        for i, protocol in enumerate(self._config.protocol_targets or ["OPC_UA"]):
            base_port = 4840 + i
            ep_name = f"{protocol}_server_ep"
            ep_id = f"{self._config.scenario_id}_{protocol}_server_ep"
            endpoints.append(
                ServerEndpointConfig(
                    endpoint_name=ep_name,
                    endpoint_id=ep_id,
                    protocol=protocol,
                    bind_host="0.0.0.0",
                    bind_port=base_port,
                    host="127.0.0.1",
                    port=base_port,
                )
            )

        for i in range(self._config.asset_count):
            entity_id = f"{self._config.scenario_id}_entity_{i:03d}"
            point_id = f"{entity_id}_active_power"
            points.append(
                ServerPointConfig(
                    point_id=point_id,
                    point_name="ActivePower",
                    data_type="FLOAT64",
                    access_mode="RO",
                    associated_signal_id=f"{entity_id}_ActivePower",
                    node_key=f"ns=2;s={entity_id}.ActivePower",
                    variable_key="Value",
                    value_type="Float",
                )
            )

        server_id = f"server_{self._config.scenario_id}"
        server_member = ServerMemberConfig(
            server_id=server_id,
            server_name=f"Seahorse Server {self._config.scenario_id}",
            source_name=self._config.scenario_id,
            logical_device_name=f"LD_{self._config.scenario_id}",
            endpoints=endpoints,
            points=points,
            capabilities=["READ"],
            update_policy={"default": {"mode": "poll", "interval_ms": 100}},
            initial_values={point_id: 0.0 for pt in points if (point_id := pt.point_id)},
        )
        return ServerConfig(
            config_id=f"server_config_{self._config.scenario_id}",
            scenario_id=self._config.scenario_id,
            config_name=f"Seahorse Server Config {self._config.scenario_id}",
            servers=[server_member],
            synthetic=True,
            strategy_id="seahorse_minimal_v1",
        )

    @staticmethod
    def _build_default_signal_items(profile_id: str) -> list[SignalProfileItemPlan]:
        """为点表创建默认信号点位规划。

        包含有功功率、风速、状态等基础风电场点位。
        """
        default_signals = [
            ("ActivePower", "kW", "FLOAT64", "MMXU", "MV"),
            ("ReactivePower", "kVAr", "FLOAT64", "MMXU", "MV"),
            ("WindSpeed", "m/s", "FLOAT64", "WMET", "MV"),
            ("RotorSpeed", "rpm", "FLOAT64", "WROT", "MV"),
            ("Status", "", "INT32", "WTUR", "SPS"),
            ("Temperature", "deg C", "FLOAT64", "WTUR", "MV"),
        ]
        return [
            SignalProfileItemPlan(
                signal_id=f"{profile_id}_{name}",
                signal_name=name,
                unit=unit,
                data_type=dtype,
                ln_class=ln_class,
                cdc=cdc,
                generation_hint="RANDOM" if cdc == "MV" else "DISCRETE",
            )
            for name, unit, dtype, ln_class, cdc in default_signals
        ]

    def compute_checksum(self) -> str:
        """计算当前配置的校验和。

        用于验证生成的可重现性。相同 config 应产生相同 checksum。

        Returns:
            配置序列化的 SHA256 哈希前 16 位十六进制字符串。
        """
        raw = f"{self._config.scenario_id}|{self._config.deterministic_seed}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


__all__ = ["SeahorseGenerator"]
