"""Seahorse facade。

该 facade 汇总当前已存在的离线场景生成、bundle 导出/校验、
ServerConfig/ServerPlan JSON handoff 和内存 runtime smoke 链路能力。
它不实现 50Hz runtime、真实 Starfish writer 或 Whale->WritePlan 读取
链路；smoke workflow 仅在内存中串联已注入的端口与原子用例。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

from seahorse.adapters.gateways.server_plan_handoff_gateway import (
    export_server_config_from_bundle,
    export_server_config_to_json,
    save_server_config,
    save_server_config_from_bundle,
)
from seahorse.adapters.serializers.bundle_json_serializer import (
    export_bundle_to_json,
    save_bundle,
)
from seahorse.application.use_cases import SeahorseGenerator
from seahorse.application.use_cases.atomic import RuntimeSmokeReport, RuntimeSmokeWorkflow
from seahorse.application.use_cases.bundle_validator import (
    ValidationResult,
    validate_bundle,
    validate_bundle_from_dict,
)
from seahorse.domain.bundle import ScenarioBundle
from seahorse.domain.bundle_checksum import compute_bundle_checksum
from seahorse.domain.plan import ServerConfig
from seahorse.domain.runtime_contract import WritePlan
from seahorse.domain.scenario import ScenarioConfig

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
            scenario_metadata=generator.metadata,
            seed_plan=seed_plan,
            server_config=server_config,
            generated_timeseries_sample=signals,
            alarm_events=alarms,
            control_results=controls,
        )
        bundle.checksum = compute_bundle_checksum(bundle)
        return bundle

    def export_bundle_json(self, bundle: ScenarioBundle, *, indent: int = 2) -> str:
        """导出 bundle JSON 字符串。"""
        return export_bundle_to_json(bundle, indent=indent)

    def save_bundle(self, bundle: ScenarioBundle, output_dir: str | Path) -> Path:
        """保存 bundle JSON 文件。"""
        return save_bundle(bundle, output_dir)

    def validate_bundle(self, bundle: ScenarioBundle) -> ValidationResult:
        """校验内存中的 ScenarioBundle。"""
        return validate_bundle(bundle)

    def validate_bundle_dict(self, data: dict[str, Any]) -> ValidationResult:
        """校验从 JSON 反序列化得到的 bundle dict。"""
        return validate_bundle_from_dict(data)

    def load_and_validate_bundle(self, input_path: str | Path) -> ValidationResult:
        """读取 bundle JSON 并执行校验。"""
        data = json.loads(Path(input_path).read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise TypeError("bundle JSON 顶层必须是 object")
        return validate_bundle_from_dict(data)

    def export_server_config_json(self, server_config: ServerConfig, *, indent: int = 2) -> str:
        """导出 ServerConfig handoff JSON 字符串。"""
        return export_server_config_to_json(server_config, indent=indent)

    def export_server_config_from_bundle(self, bundle: ScenarioBundle, *, indent: int = 2) -> str:
        """从 bundle 导出 ServerConfig handoff JSON 字符串。"""
        return export_server_config_from_bundle(bundle, indent=indent)

    def save_server_config(self, server_config: ServerConfig, output_dir: str | Path) -> Path:
        """保存 ServerConfig handoff JSON。"""
        return save_server_config(server_config, output_dir)

    def save_server_config_from_bundle(self, bundle: ScenarioBundle, output_dir: str | Path) -> Path:
        """从 bundle 保存 ServerConfig handoff JSON。"""
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
            from seahorse.container import build_runtime_smoke_workflow

            workflow = build_runtime_smoke_workflow(
                runtime_id=runtime_id,
                write_plan=write_plan,
            )
        return workflow.run(now_ns=now_ns, ticks=ticks)
