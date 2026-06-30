"""构建 WritePlan 的最小用例。

用例只依赖 WhaleMetadataPort 的抽象读取契约，不接真实 Whale ORM，也
不在 runtime tick 中查询数据库。数据源和调度允许由调用方显式传入；
未传入时使用应用层默认策略，并在返回前做纯内存一致性校验。
"""

from __future__ import annotations

from dataclasses import dataclass

from seahorse.application.exceptions import WritePlanBuildError
from seahorse.application.ports.whale_metadata_port import WhaleMetadataPort
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    ServerBinding,
    PeriodicScheduleSpec,
    ScheduleSpec,
    WritePlan,
    WritePlanId,
    validate_write_plan,
)

DEFAULT_WRITE_PLAN_PERIOD_MS = 1000
"""未显式传入 schedule 时采用的保守周期，单位毫秒。"""


@dataclass(slots=True)
class BuildWritePlanUseCase:
    """从 metadata port 构建内存 WritePlan。

    Attributes:
        metadata_port: Whale metadata 抽象读取端口。
    """

    metadata_port: WhaleMetadataPort

    def execute(
        self,
        *,
        plan_id: WritePlanId,
        data_sources: tuple[DataSourceSpec, ...] | None = None,
        schedule: ScheduleSpec | None = None,
    ) -> WritePlan:
        """构建 WritePlan。

        runtime tick 前一次性读取 metadata port；本用例不保留数据库 session，
        也不触发真实 Starfish 写入或调度执行器。未传入数据源时，会按字段
        binding 的 ``source_id`` 生成 ``SAMPLE`` 类型默认数据源；未传入
        schedule 时，采用 1000ms periodic 配置，避免把本轮建模误写为
        50Hz runtime 能力。

        Args:
            plan_id: 运行计划标识。
            data_sources: 可选计划数据源契约；None 表示使用默认样例来源。
            schedule: 可选写入调度契约；None 表示使用保守周期默认值。

        Returns:
            纯内存 WritePlan。

        Raises:
            WritePlanBuildError: Whale 元数据或计划契约不完整。
        """
        servers = self.metadata_port.load_servers(plan_id)
        resolved_data_sources = (
            self._build_default_data_sources(servers)
            if data_sources is None
            else data_sources
        )
        resolved_schedule = schedule or ScheduleSpec.periodic(
            PeriodicScheduleSpec.from_period_ms(DEFAULT_WRITE_PLAN_PERIOD_MS)
        )
        plan = WritePlan(
            plan_id=plan_id,
            servers=servers,
            data_sources=resolved_data_sources,
            schedule=resolved_schedule,
        )
        errors = validate_write_plan(plan)
        if errors:
            raise WritePlanBuildError("; ".join(errors))
        if not plan.field_bindings():
            raise WritePlanBuildError("WritePlan.fields 不能为空")
        return plan

    def _build_default_data_sources(
        self,
        servers: tuple[ServerBinding, ...],
    ) -> tuple[DataSourceSpec, ...]:
        """按字段绑定生成默认 SAMPLE 数据源。

        Args:
            servers: metadata port 返回的 server binding 集合。

        Returns:
            根据字段 ``source_id`` 去重后的默认数据源。
        """
        source_ids = {
            field.source_id
            for server in servers
            for endpoint in server.endpoints
            for field in endpoint.fields
        }
        return tuple(
            DataSourceSpec(
                source_id=source_id,
                kind=DataSourceKind.SAMPLE,
                reference=source_id,
            )
            for source_id in sorted(source_ids)
        )
