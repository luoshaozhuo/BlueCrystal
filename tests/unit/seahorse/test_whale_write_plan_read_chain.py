"""Seahorse Whale metadata 到 WritePlan 读取链路单元测试。

验证对象：application 用例的默认调度/数据源策略，以及 infrastructure
mapper 对 Whale ORM server/endpoint/point/field 配置的只读映射。
测试阶段：P1/P2。这里直接构造 ORM 对象和 fake port，不连接真实 Whale DB，
不能证明真实数据库内容完整、50Hz runtime 可用或 Starfish 写入闭环可用。
"""

from __future__ import annotations

import pytest

from seahorse.application.exceptions import WritePlanBuildError
from seahorse.application.use_cases.atomic import BuildWritePlanUseCase
from seahorse.domain.runtime_contract import (
    DataSourceKind,
    DataSourceSpec,
    EndpointBinding,
    FieldBinding,
    PeriodicScheduleSpec,
    ScheduleKind,
    ScheduleSpec,
    ServerBinding,
    WritePlan,
    WritePlanId,
    WriteTarget,
)
from seahorse.infrastructure.repositories import (
    WhaleMetadataMappingError,
    WhaleMetadataToWritePlanMapper,
)
from whale.shared.persistence.orm import (
    CommunicationEndpoint,
    IED,
    LDInstance,
    SignalProfile,
    SignalProfileItem,
)


class _StaticMetadataPort:
    """返回内存 server binding 的 WhaleMetadataPort 测试替身。"""

    def __init__(self, servers: tuple[ServerBinding, ...]) -> None:
        """保存 server binding 集合。"""
        self._servers = servers

    def load_servers(self, plan_id: WritePlanId) -> tuple[ServerBinding, ...]:
        """返回预置 server binding。"""
        _ = plan_id
        return self._servers

    def load_endpoints(self, server_id: str) -> tuple[EndpointBinding, ...]:
        """按 server_id 返回 endpoint binding。"""
        return tuple(
            endpoint
            for server in self._servers
            if server.server_id == server_id
            for endpoint in server.endpoints
        )

    def load_fields(self, endpoint_id: str) -> tuple[FieldBinding, ...]:
        """按 endpoint_id 返回 field binding。"""
        return tuple(
            field
            for server in self._servers
            for endpoint in server.endpoints
            if endpoint.endpoint_id == endpoint_id
            for field in endpoint.fields
        )


def _server_with_one_field(source_id: str = "src-1") -> ServerBinding:
    """构造一个最小 server/endpoint/field 配置。"""
    field = FieldBinding(
        field_id="field-1",
        target=WriteTarget("server-1", "endpoint-1", "point-1"),
        source_id=source_id,
    )
    return ServerBinding(
        server_id="server-1",
        endpoints=(
            EndpointBinding(
                endpoint_id="endpoint-1",
                protocol="OPC_UA",
                fields=(field,),
            ),
        ),
    )


def _whale_endpoint() -> CommunicationEndpoint:
    """构造 mapper 测试所需的 Whale ORM 对象图。"""
    ied = IED(
        ied_id=11,
        asset_instance_id=100,
        ied_name="IED_WTG_001",
    )
    endpoint = CommunicationEndpoint(
        endpoint_id=21,
        ied_id=11,
        access_point_name="AP1",
        application_protocol="OPC_UA",
        service_type="READ",
        transport="TCP",
    )
    profile = SignalProfile(
        signal_profile_id=31,
        profile_code="PROFILE_BASIC",
        profile_name="基础点表",
    )
    item = SignalProfileItem(
        profile_item_id=41,
        signal_profile_id=31,
        do_name="TotW",
        relative_path="MMXU1.TotW.mag.f",
        data_type_id=1,
    )
    ld_instance = LDInstance(
        ld_instance_id=51,
        endpoint_id=21,
        asset_instance_id=100,
        signal_profile_id=31,
        ld_name="LD_WTG_001",
    )

    endpoint.ied = ied
    endpoint.ld_instances = [ld_instance]
    ld_instance.endpoint = endpoint
    ld_instance.signal_profile = profile
    profile.items = [item]
    item.signal_profile = profile
    return endpoint


def test_build_write_plan_uses_explicit_sources_and_schedule() -> None:
    """显式 data_sources/schedule 会原样进入 WritePlan。"""
    server = _server_with_one_field()
    schedule = ScheduleSpec.periodic(PeriodicScheduleSpec.from_period_ms(20))
    data_sources = (DataSourceSpec("src-1", DataSourceKind.RANDOM, seed=7),)
    builder = BuildWritePlanUseCase(metadata_port=_StaticMetadataPort((server,)))

    plan = builder.execute(
        plan_id=WritePlanId("plan-explicit"),
        data_sources=data_sources,
        schedule=schedule,
    )

    assert plan == WritePlan(
        plan_id=WritePlanId("plan-explicit"),
        servers=(server,),
        data_sources=data_sources,
        schedule=schedule,
    )


def test_build_write_plan_defaults_to_sample_sources_and_safe_schedule() -> None:
    """未传入策略时，用字段 source_id 生成 SAMPLE 数据源并采用 1000ms 周期。"""
    server = _server_with_one_field(source_id="src-default")
    builder = BuildWritePlanUseCase(metadata_port=_StaticMetadataPort((server,)))

    plan = builder.execute(plan_id=WritePlanId("plan-default"))

    assert plan.data_sources == (
        DataSourceSpec(
            source_id="src-default",
            kind=DataSourceKind.SAMPLE,
            reference="src-default",
        ),
    )
    assert plan.schedule.kind is ScheduleKind.PERIODIC
    assert isinstance(plan.schedule.detail, PeriodicScheduleSpec)
    assert plan.schedule.detail.period_ms == 1000


def test_build_write_plan_rejects_empty_server_config() -> None:
    """无 server 配置时返回应用层稳定错误。"""
    builder = BuildWritePlanUseCase(metadata_port=_StaticMetadataPort(()))

    with pytest.raises(WritePlanBuildError, match="servers 不能为空"):
        builder.execute(plan_id=WritePlanId("plan-empty"))


def test_build_write_plan_rejects_incomplete_source_config() -> None:
    """显式传入空数据源时，不用默认策略掩盖缺失配置。"""
    server = _server_with_one_field(source_id="missing-source")
    builder = BuildWritePlanUseCase(metadata_port=_StaticMetadataPort((server,)))

    with pytest.raises(WritePlanBuildError, match="未知 source_id"):
        builder.execute(plan_id=WritePlanId("plan-missing-source"), data_sources=())


def test_whale_mapper_maps_endpoint_profile_items_to_write_plan_bindings() -> None:
    """Whale IED/Endpoint/LD/ProfileItem 会映射成 server/endpoint/field。"""
    mapper = WhaleMetadataToWritePlanMapper()

    server = mapper.map_endpoint(_whale_endpoint())

    endpoint = server.endpoints[0]
    field = endpoint.fields[0]
    assert server.server_id == "whale:ied:IED_WTG_001"
    assert endpoint.endpoint_id == "whale:endpoint:21:AP1"
    assert endpoint.protocol == "OPC_UA"
    assert field.field_id == "whale:ld:51:item:41:value"
    assert field.target.point_id == "LD_WTG_001/MMXU1.TotW.mag.f"
    assert field.source_id == "whale-source:profile-item:41:sample"


def test_whale_mapper_rejects_endpoint_without_point_config() -> None:
    """缺少 LD/point 配置时，mapper 不猜测默认点位。"""
    endpoint = _whale_endpoint()
    endpoint.ld_instances = []

    with pytest.raises(WhaleMetadataMappingError, match="LDInstance"):
        WhaleMetadataToWritePlanMapper().map_endpoint(endpoint)


def test_whale_mapper_rejects_empty_profile_item_path() -> None:
    """缺少 relative_path 时，mapper 显式失败而不是拼接不稳定 point_id。"""
    endpoint = _whale_endpoint()
    endpoint.ld_instances[0].signal_profile.items[0].relative_path = ""

    with pytest.raises(WhaleMetadataMappingError, match="relative_path"):
        WhaleMetadataToWritePlanMapper().map_endpoint(endpoint)
