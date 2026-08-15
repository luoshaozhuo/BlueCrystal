"""Seahorse facade。

该 facade 汇总当前已存在的离线场景生成、bundle 导出/校验、
ServerConfig/ServerPlan JSON handoff 和内存 runtime smoke 链路能力。
它不实现 50Hz runtime、真实 Starfish writer 或 Whale->WritePlan 读取
链路；smoke workflow 仅在内存中串联已注入的端口与原子用例。

facade 只调用 ``seahorse.application``、``seahorse.adapters`` 的
serializers / gateways 与 ``seahorse.domain``，不直接 new infrastructure
backend，也不暴露 ``RuntimeContext``。

薄 CLI 入口 ``__main__.py`` 通过 :class:`SeahorseFacade` 暴露的
``generate_bundle_from_cli_params`` /
``generate_minimal_server_config_from_cli_params`` 接收 primitives /
Path / list / dict，并在内部构造 :class:`ScenarioConfig`；CLI 自身
不得 import ``seahorse.domain`` / ``seahorse.application`` /
``seahorse.adapters`` / ``seahorse.infrastructure``。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

from pacific.seahorse.adapters.gateways.server_plan_handoff_gateway import (
    export_server_config_from_bundle,
    export_server_config_to_json,
    save_server_config,
    save_server_config_from_bundle,
)
from pacific.seahorse.adapters.gateways.server_plan_validator import validate_server_config
from pacific.seahorse.adapters.serializers.bundle_json_serializer import (
    export_bundle_to_json,
    save_bundle,
)
from pacific.seahorse.adapters.serializers.timeseries_jsonl_serializer import (
    export_timeseries_to_jsonl,
    save_timeseries,
)
from pacific.seahorse.application.use_cases import SeahorseGenerator
from pacific.seahorse.application.use_cases.atomic import RuntimeSmokeReport, RuntimeSmokeWorkflow
from pacific.seahorse.application.use_cases.bundle_validator import (
    ValidationResult,
    validate_bundle,
    validate_bundle_from_dict,
)
from pacific.seahorse.domain.bundle import ScenarioBundle
from pacific.seahorse.domain.bundle_checksum import compute_bundle_checksum
from pacific.seahorse.domain.generation import GeneratedSignalValue
from pacific.seahorse.domain.plan import (
    ServerConfig,
    ServerEndpointConfig,
    ServerMemberConfig,
    ServerPointConfig,
)
from pacific.seahorse.domain.runtime_contract import WritePlan
from pacific.seahorse.domain.scenario import ScenarioConfig, ScenarioMetadata

if TYPE_CHECKING:
    pass


class SeahorseFacade:
    """Seahorse 当前稳定能力的门面。

    facade 面向 CLI、脚本或测试调用方暴露离线生成、JSON handoff 和
    内存 runtime smoke workflow。其方法只操作内存模型和文件
    serializer，不连接 Whale DB 或 Starfish runtime。
    """

    def generate_bundle(self, config: ScenarioConfig) -> ScenarioBundle:
        """根据配置生成完整 ScenarioBundle。

        Args:
            config: 场景生成配置。

        Returns:
            已计算 checksum 的 ScenarioBundle。
        """
        generator = SeahorseGenerator(config)
        seed_plan, server_config, signals, alarms, controls = generator.generate()
        bundle = ScenarioBundle(
            schema_version="1.0.0",
            scenario_version="1.0.0",
            generator_version="0.2.0",
            created_at=datetime.now(timezone.utc),
            scenario_id=config.scenario_id,
            name=config.name,
            deterministic_seed=config.deterministic_seed,
            synthetic=True,
            scenario_config=config,
            scenario_metadata=ScenarioMetadata(
                scenario_id=config.scenario_id,
                config_snapshot=_scenario_config_snapshot(config),
                stats=dict(generator.metadata.stats),
            ),
            seed_plan=seed_plan,
            server_config=server_config,
            generated_timeseries_sample=signals,
            alarm_events=alarms,
            control_results=controls,
        )
        bundle.checksum = compute_bundle_checksum(bundle)
        return bundle

    def generate_minimal_server_config(self, config: ScenarioConfig) -> ServerConfig:
        """生成最小 ServerConfig（不生成信号/告警/控制结果）。

        Args:
            config: 场景生成配置。

        Returns:
            :class:`ServerConfig` 实例，包含最小资产点位。
        """
        generator = SeahorseGenerator(config)
        _, server_config = generator.generate_minimal()
        return server_config

    def generate_bundle_from_cli_params(
        self,
        *,
        scenario_id: str,
        name: str,
        deterministic_seed: int,
        start_time: datetime | None,
        duration_seconds: float,
        sample_interval_ms: int,
        asset_count: int,
        protocol_targets: list[str],
    ) -> ScenarioBundle:
        """从 CLI primitives 组装 :class:`ScenarioConfig` 并生成完整 bundle。

        该 wrapper 供 :mod:`seahorse.__main__` 薄 Typer CLI 调用；它
        允许 CLI 只传 primitives / Path / list / dict，由 facade 在
        内部构造 :class:`ScenarioConfig`。CLI 自身不构造 domain model。

        Args:
            scenario_id: 场景唯一标识。
            name: 场景可读名称。
            deterministic_seed: 确定性伪随机种子。
            start_time: 可选模拟起始时间；为 None 时使用 UTC 当前时间。
            duration_seconds: 模拟总时长（秒）。
            sample_interval_ms: 信号采样间隔（毫秒）。
            asset_count: 要生成的资产数量。
            protocol_targets: 目标协议列表，例如 ["OPC_UA", "MODBUS"]。

        Returns:
            已计算 checksum 的 :class:`ScenarioBundle`。
        """
        config = self._build_cli_scenario_config(
            scenario_id=scenario_id,
            name=name,
            deterministic_seed=deterministic_seed,
            start_time=start_time,
            duration_seconds=duration_seconds,
            sample_interval_ms=sample_interval_ms,
            asset_count=asset_count,
            protocol_targets=protocol_targets,
        )
        return self.generate_bundle(config)

    def generate_minimal_server_config_from_cli_params(
        self,
        *,
        scenario_id: str,
        deterministic_seed: int,
        asset_count: int,
        protocol_targets: list[str],
    ) -> ServerConfig:
        """从 CLI primitives 组装 :class:`ScenarioConfig` 并生成最小 ServerConfig。

        与 :meth:`generate_bundle_from_cli_params` 类似，但只生成最小
        ServerConfig，不生成信号 / 告警 / 控制结果，供
        ``export-server-config`` 子命令直接生成模式使用。

        Args:
            scenario_id: 场景唯一标识。
            deterministic_seed: 确定性伪随机种子。
            asset_count: 要生成的资产数量。
            protocol_targets: 目标协议列表。

        Returns:
            :class:`ServerConfig` 实例。
        """
        config = self._build_cli_scenario_config(
            scenario_id=scenario_id,
            name="",
            deterministic_seed=deterministic_seed,
            start_time=None,
            duration_seconds=0.0,
            sample_interval_ms=0,
            asset_count=asset_count,
            protocol_targets=protocol_targets,
        )
        return self.generate_minimal_server_config(config)

    @staticmethod
    def _build_cli_scenario_config(
        *,
        scenario_id: str,
        name: str,
        deterministic_seed: int,
        start_time: datetime | None,
        duration_seconds: float,
        sample_interval_ms: int,
        asset_count: int,
        protocol_targets: list[str],
    ) -> ScenarioConfig:
        """根据 CLI primitives 构造 :class:`ScenarioConfig`。

        Args:
            scenario_id: 场景唯一标识。
            name: 场景可读名称。
            deterministic_seed: 确定性伪随机种子。
            start_time: 可选起始时间。
            duration_seconds: 模拟总时长（秒）。
            sample_interval_ms: 信号采样间隔（毫秒）。
            asset_count: 资产数量。
            protocol_targets: 目标协议列表。

        Returns:
            填充完毕的 :class:`ScenarioConfig`。
        """
        if start_time is None:
            return ScenarioConfig(
                scenario_id=scenario_id,
                name=name,
                deterministic_seed=deterministic_seed,
                duration_seconds=duration_seconds,
                sample_interval_ms=sample_interval_ms,
                asset_count=asset_count,
                protocol_targets=protocol_targets,
            )
        return ScenarioConfig(
            scenario_id=scenario_id,
            name=name,
            deterministic_seed=deterministic_seed,
            start_time=start_time,
            duration_seconds=duration_seconds,
            sample_interval_ms=sample_interval_ms,
            asset_count=asset_count,
            protocol_targets=protocol_targets,
        )

    def export_bundle_json(self, bundle: ScenarioBundle, *, indent: int = 2) -> str:
        """导出 bundle JSON 字符串。

        Args:
            bundle: 已生成的 ScenarioBundle。
            indent: JSON 缩进空格数，默认 2。

        Returns:
            UTF-8 JSON 字符串。
        """
        return export_bundle_to_json(bundle, indent=indent)

    def save_bundle(self, bundle: ScenarioBundle, output_dir: str | Path) -> Path:
        """保存 bundle JSON 文件。

        Args:
            bundle: 已生成的 ScenarioBundle。
            output_dir: 输出目录路径。

        Returns:
            已写入文件的 Path 对象。
        """
        return save_bundle(bundle, output_dir)

    def export_timeseries_jsonl(self, signal_values: list[GeneratedSignalValue]) -> str:
        """导出信号值序列为 JSONL 字符串。

        Args:
            signal_values: 生成的信号值序列。

        Returns:
            JSONL 字符串，每行一个 JSON 对象。
        """
        return export_timeseries_to_jsonl(signal_values)

    def save_timeseries(
        self,
        signal_values: list[GeneratedSignalValue],
        output_dir: str | Path,
        *,
        scenario_id: str = "",
        filename: str | None = None,
    ) -> Path:
        """将信号值序列保存为 JSONL 时序文件。

        Args:
            signal_values: 生成的信号值序列。
            output_dir: 输出目录路径。
            scenario_id: 用于生成默认文件名的场景标识。
            filename: 自定义文件名，None 时使用 ``{scenario_id}_timeseries.jsonl``。

        Returns:
            已写入文件的 Path 对象。
        """
        return save_timeseries(
            signal_values,
            output_dir,
            scenario_id=scenario_id,
            filename=filename,
        )

    def generator_metadata_stats(self, bundle: ScenarioBundle) -> dict[str, int]:
        """读取 bundle 内嵌的生成器元数据统计字段。

        Args:
            bundle: 已生成的 ScenarioBundle。

        Returns:
            ``scenario_metadata.stats`` 字典；如缺失返回空 dict。
        """
        if bundle.scenario_metadata is None:
            return {}
        return dict(bundle.scenario_metadata.stats)

    def validate_bundle(self, bundle: ScenarioBundle) -> ValidationResult:
        """校验内存中的 ScenarioBundle。

        Args:
            bundle: 已生成的 ScenarioBundle。

        Returns:
            :class:`ValidationResult`，包含 errors / warnings / passed_checks。
        """
        return validate_bundle(bundle)

    def validate_bundle_dict(self, data: dict[str, Any]) -> ValidationResult:
        """校验从 JSON 反序列化得到的 bundle dict。

        Args:
            data: 由 bundle JSON 反序列化得到的 dict。

        Returns:
            :class:`ValidationResult`。
        """
        return validate_bundle_from_dict(data)

    def load_and_validate_bundle(self, input_path: str | Path) -> ValidationResult:
        """读取 bundle JSON 并执行校验。

        Args:
            input_path: bundle JSON 文件路径。

        Returns:
            :class:`ValidationResult`。

        Raises:
            TypeError: 当顶层不是 dict 时。
        """
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("bundle JSON 顶层必须是 object")
        return validate_bundle_from_dict(data)

    def load_server_config_from_bundle_json(
        self,
        bundle_json_path: str | Path,
    ) -> ServerConfig:
        """从 bundle JSON 文件中加载并重构 ServerConfig。

        Args:
            bundle_json_path: bundle JSON 文件路径。

        Returns:
            :class:`ServerConfig` 实例。

        Raises:
            FileNotFoundError: 输入路径不存在。
            ValueError: bundle JSON 中缺少 ``server_config`` 字段。
        """
        bundle_json_path = Path(bundle_json_path)
        if not bundle_json_path.is_file():
            raise FileNotFoundError(f"输入 bundle JSON 不存在: {bundle_json_path}")
        raw = json.loads(bundle_json_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError("bundle JSON 顶层必须是 object")
        server_config_raw = raw.get("server_config")
        if not server_config_raw:
            raise ValueError("输入 bundle JSON 中缺少 server_config 字段")

        def _server_member(server: dict[str, Any]) -> ServerMemberConfig:
            return ServerMemberConfig(
                server_id=server.get("server_id", ""),
                server_name=server.get("server_name", ""),
                source_name=server.get("source_name", ""),
                logical_device_name=server.get("logical_device_name", ""),
                endpoints=[
                    ServerEndpointConfig(
                        endpoint_name=ep.get("endpoint_name", ""),
                        endpoint_id=ep.get("endpoint_id", ep.get("endpoint_name", "")),
                        protocol=ep.get("protocol", ""),
                        bind_host=ep.get("bind_host", "0.0.0.0"),
                        bind_port=ep.get("bind_port", 0),
                        host=ep.get("host", ep.get("bind_host", "")),
                        port=ep.get("port", ep.get("bind_port", 0)),
                    )
                    for ep in server.get("endpoints", [])
                ],
                points=[
                    ServerPointConfig(
                        point_id=pt.get("point_id", ""),
                        point_name=pt.get("point_name", ""),
                        data_type=pt.get("data_type", "FLOAT64"),
                        access_mode=pt.get("access_mode", "RO"),
                        associated_signal_id=pt.get("associated_signal_id", ""),
                        node_key=pt.get("node_key", ""),
                        variable_key=pt.get("variable_key", ""),
                        value_type=pt.get("value_type", ""),
                    )
                    for pt in server.get("points", [])
                ],
                capabilities=server.get("capabilities", []),
                update_policy=server.get("update_policy", {}),
                initial_values=server.get("initial_values", {}),
            )

        return ServerConfig(
            config_id=server_config_raw.get("config_id", ""),
            scenario_id=server_config_raw.get("scenario_id", ""),
            config_name=server_config_raw.get("config_name", ""),
            servers=[_server_member(server) for server in server_config_raw.get("servers", [])],
            synthetic=server_config_raw.get("synthetic", True),
            strategy_id=server_config_raw.get("strategy_id", ""),
        )

    def validate_server_config(self, server_config: ServerConfig) -> ValidationResult:
        """对 ServerConfig 执行 Starfish 契约兼容性校验。

        Args:
            server_config: Seahorse 生成的 ServerConfig。

        Returns:
            :class:`ValidationResult`。
        """
        return validate_server_config(server_config)

    def export_server_config_json(self, server_config: ServerConfig, *, indent: int = 2) -> str:
        """导出 ServerConfig handoff JSON 字符串。

        Args:
            server_config: Seahorse 生成的 ServerConfig。
            indent: JSON 缩进空格数，默认 2。

        Returns:
            UTF-8 JSON 字符串。
        """
        return export_server_config_to_json(server_config, indent=indent)

    def export_server_config_from_bundle(
        self,
        bundle: ScenarioBundle,
        *,
        indent: int = 2,
    ) -> str:
        """从 bundle 导出 ServerConfig handoff JSON 字符串。

        Args:
            bundle: 已生成的 ScenarioBundle。
            indent: JSON 缩进空格数，默认 2。

        Returns:
            UTF-8 JSON 字符串。

        Raises:
            ValueError: bundle.server_config 为 None。
        """
        return export_server_config_from_bundle(bundle, indent=indent)

    def save_server_config(
        self,
        server_config: ServerConfig,
        output_dir: str | Path,
    ) -> Path:
        """保存 ServerConfig handoff JSON。

        Args:
            server_config: Seahorse 生成的 ServerConfig。
            output_dir: 输出目录路径。

        Returns:
            已写入文件的 Path 对象。
        """
        return save_server_config(server_config, output_dir)

    def save_server_config_from_bundle(
        self,
        bundle: ScenarioBundle,
        output_dir: str | Path,
    ) -> Path:
        """从 bundle 保存 ServerConfig handoff JSON。

        Args:
            bundle: 已生成的 ScenarioBundle。
            output_dir: 输出目录路径。

        Returns:
            已写入文件的 Path 对象。

        Raises:
            ValueError: bundle.server_config 为 None。
        """
        return save_server_config_from_bundle(bundle, output_dir)

    def run_runtime_smoke(
        self,
        write_plan: WritePlan,
        *,
        runtime_id: str = "smoke-runtime",
        ticks: int = 1,
        now_ns: int = 0,
        workflow: RuntimeSmokeWorkflow | None = None,
    ) -> RuntimeSmokeReport:
        """执行内存 runtime smoke workflow。

        该入口只用于本地 smoke / in-memory runtime 验证，不接真实
        Starfish runtime、socket、subprocess、native runner 或
        ServerSimulatorFacade，也不启动真实 scheduler。

        Args:
            write_plan: 已构建的内存 WritePlan。
            runtime_id: smoke 运行实例标识。
            ticks: 调用 ``tick_and_dispatch`` 的次数；非正数时立即返回空报告。
            now_ns: 起始单调时钟纳秒值。
            workflow: 可选 :class:`RuntimeSmokeWorkflow`；未传入时由
                container 默认装配内存 backend / gateway / dispatch / executor。

        Returns:
            :class:`RuntimeSmokeReport`，包含 plan_id、tick_count、
            generated_batch_count、dispatch_count、success_count、
            failure_count、last_error、writer_history_count 等稳定字段。
        """
        # 延迟导入避免 facade 与 container 互相循环；container 依赖本
        # 模块的 SeahorseFacade。
        if workflow is None:
            from pacific.seahorse.container import build_runtime_smoke_workflow

            workflow = build_runtime_smoke_workflow(
                runtime_id=runtime_id,
                write_plan=write_plan,
            )
        return workflow.run(now_ns=now_ns, ticks=ticks)


def _scenario_config_snapshot(config: ScenarioConfig) -> dict[str, Any]:
    """将 ScenarioConfig 转为可序列化快照 dict。

    Args:
        config: 场景生成配置。

    Returns:
        字段快照 dict，便于 ``scenario_metadata.config_snapshot`` 持久化。
    """
    return {
        "scenario_id": config.scenario_id,
        "name": config.name,
        "deterministic_seed": config.deterministic_seed,
        "start_time": config.start_time.isoformat(),
        "duration_seconds": config.duration_seconds,
        "sample_interval_ms": config.sample_interval_ms,
        "asset_count": config.asset_count,
        "protocol_targets": list(config.protocol_targets),
    }


__all__ = ["SeahorseFacade"]
