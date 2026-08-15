"""Seahorse repository —— Whale 元数据只读映射与样例种子薄入口。

Seahorse 构建 WritePlan 所需的只读映射与样例种子入口；样例生成的实际
写入委托给 ``whale.shared.persistence.template.sample_data``，本文件
不持有生成实现。真实 Whale ORM 访问只在本 infrastructure 边界发生，
不进入 domain/application。
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from pacific.seahorse.domain.runtime_contract import (
    EndpointBinding,
    FieldBinding,
    ServerBinding,
    WritePlanId,
    WriteTarget,
)
from pacific.whale.shared.persistence.orm import (
    CommunicationEndpoint,
    IED,
    LDInstance,
    SignalProfile,
    SignalProfileItem,
)
from tools.sqlalchemy_session import session_scope

SessionScopeFactory = Callable[[], AbstractContextManager[Session]]


class WhaleMetadataMappingError(RuntimeError):
    """Whale 元数据无法映射为 Seahorse WritePlan。

    repository 在读取 Whale ORM 后，如果发现缺少 IED、Endpoint、LD、
    SignalProfile 或 SignalProfileItem 等构建计划必需字段，会抛出该稳定
    基础设施错误，避免继续产生 silent wrong result。
    """


class WhaleMetadataToWritePlanMapper:
    """将 Whale ORM 对象映射为 Seahorse runtime contract。

    该 mapper 只读取已加载的 ORM 对象字段和 relationship，不查询数据库；
    具体 session 生命周期由 repository 负责。
    """

    def map_endpoint(self, endpoint: CommunicationEndpoint) -> ServerBinding:
        """把单个 Whale CommunicationEndpoint 映射为 ServerBinding。

        Args:
            endpoint: 已加载 IED、LDInstance、SignalProfile.items 的 Whale ORM 对象。

        Returns:
            Seahorse 纯内存 server binding。

        Raises:
            WhaleMetadataMappingError: metadata 缺少构建 WritePlan 所需字段。
        """
        if endpoint.ied is None:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 缺少 IED 关系"
            )
        server_id = self._server_id(endpoint.ied)
        endpoint_id = self._endpoint_id(endpoint)
        fields = self._map_endpoint_fields(
            endpoint=endpoint,
            server_id=server_id,
            endpoint_id=endpoint_id,
        )
        if not fields:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 未配置可映射 point/field"
            )
        return ServerBinding(
            server_id=server_id,
            endpoints=(
                EndpointBinding(
                    endpoint_id=endpoint_id,
                    protocol=self._required_text(
                        endpoint.application_protocol,
                        f"endpoint {endpoint.endpoint_id}.application_protocol",
                    ),
                    fields=fields,
                ),
            ),
        )

    def _map_endpoint_fields(
        self,
        *,
        endpoint: CommunicationEndpoint,
        server_id: str,
        endpoint_id: str,
    ) -> tuple[FieldBinding, ...]:
        """从 endpoint 下的 LD/Profile items 展开字段 binding。"""
        if not endpoint.ld_instances:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 缺少 LDInstance 配置"
            )

        fields: list[FieldBinding] = []
        for ld_instance in sorted(
            endpoint.ld_instances,
            key=lambda item: item.ld_instance_id or 0,
        ):
            if ld_instance.signal_profile is None:
                raise WhaleMetadataMappingError(
                    f"LDInstance {ld_instance.ld_instance_id} 缺少 SignalProfile"
                )
            profile_items = ld_instance.signal_profile.items
            if not profile_items:
                raise WhaleMetadataMappingError(
                    f"SignalProfile {ld_instance.signal_profile_id} 未配置 SignalProfileItem"
                )
            for profile_item in sorted(
                profile_items,
                key=lambda item: item.profile_item_id or 0,
            ):
                fields.append(
                    self._map_profile_item(
                        server_id=server_id,
                        endpoint_id=endpoint_id,
                        ld_instance=ld_instance,
                        profile_item=profile_item,
                    )
                )
        return tuple(fields)

    def _map_profile_item(
        self,
        *,
        server_id: str,
        endpoint_id: str,
        ld_instance: LDInstance,
        profile_item: SignalProfileItem,
    ) -> FieldBinding:
        """将 LD + ProfileItem 映射为单个字段绑定。"""
        ld_name = self._required_text(
            ld_instance.ld_name,
            f"LDInstance {ld_instance.ld_instance_id}.ld_name",
        )
        relative_path = self._required_text(
            profile_item.relative_path,
            f"SignalProfileItem {profile_item.profile_item_id}.relative_path",
        )
        field_id = f"whale:ld:{ld_instance.ld_instance_id}:item:{profile_item.profile_item_id}:value"
        source_id = f"whale-source:profile-item:{profile_item.profile_item_id}:sample"
        return FieldBinding(
            field_id=field_id,
            target=WriteTarget(
                server_id=server_id,
                endpoint_id=endpoint_id,
                point_id=f"{ld_name}/{relative_path}",
                field_name="value",
            ),
            source_id=source_id,
        )

    def _server_id(self, ied: IED) -> str:
        """根据 IED 构造稳定 server_id。"""
        if ied.ied_name:
            return f"whale:ied:{ied.ied_name}"
        if ied.ied_id is not None:
            return f"whale:ied:{ied.ied_id}"
        raise WhaleMetadataMappingError("IED 缺少 ied_name/ied_id")

    def _endpoint_id(self, endpoint: CommunicationEndpoint) -> str:
        """根据 endpoint 主键和 AccessPoint 构造稳定 endpoint_id。"""
        if endpoint.endpoint_id is None:
            raise WhaleMetadataMappingError("CommunicationEndpoint 缺少 endpoint_id")
        access_point = self._required_text(
            endpoint.access_point_name,
            f"endpoint {endpoint.endpoint_id}.access_point_name",
        )
        return f"whale:endpoint:{endpoint.endpoint_id}:{access_point}"

    def _required_text(self, value: str | None, field_name: str) -> str:
        """校验 Whale 文本字段是可映射的非空值。"""
        if value is None or not value.strip():
            raise WhaleMetadataMappingError(f"{field_name} 不能为空")
        return value


class WhaleMetadataRepository:
    """Whale 元数据样例 seed 与 Seahorse WritePlan 读取 repository。

    seed 方法会修改 Whale 元数据库；读取方法只查询 Whale metadata 并映射
    为 Seahorse 纯内存 contract。session 可由测试显式注入，也可使用默认
    `session_scope`，repository 不把 ORM 对象泄漏给 application/domain。
    """

    def __init__(
        self,
        session: Session | None = None,
        *,
        session_factory: SessionScopeFactory | None = None,
        mapper: WhaleMetadataToWritePlanMapper | None = None,
    ) -> None:
        """初始化 repository。

        Args:
            session: 可选外部 session，主要用于单元测试或受控装配。
            session_factory: 可选 context-managed session 工厂。
            mapper: 可选 Whale ORM 到 Seahorse contract mapper。
        """
        self._session = session
        self._session_factory = session_factory or session_scope
        self._mapper = mapper or WhaleMetadataToWritePlanMapper()

    def seed_sample_metadata(self) -> None:
        """写入 Seahorse 协议样例元数据（薄包装，委托给 whale 侧的样例装配入口）。"""
        from pacific.whale.shared.persistence.sample_data import (
            generate_all_sample_data,
        )

        generate_all_sample_data()

    def clear_sample_metadata(self) -> None:
        """清理 Seahorse 协议样例元数据（薄包装，委托给 whale 侧的样例清理入口）。"""
        from pacific.whale.shared.persistence.sample_data import (
            clear_database_data,
        )

        clear_database_data()

    def load_servers(self, plan_id: WritePlanId) -> tuple[ServerBinding, ...]:
        """读取构建 WritePlan 所需的 server/endpoint/field 配置。

        Args:
            plan_id: 运行计划标识；当前 Whale schema 没有 plan 维度，本实现
                只用它保持端口契约，不据此过滤。

        Returns:
            Seahorse 纯内存 server binding 集合。

        Raises:
            WhaleMetadataMappingError: Whale metadata 不完整或无法映射。
        """
        _ = plan_id
        with self._session_scope() as session:
            endpoints = self._load_endpoints(session)
            servers = tuple(self._mapper.map_endpoint(endpoint) for endpoint in endpoints)
        if not servers:
            raise WhaleMetadataMappingError("Whale 未配置 CommunicationEndpoint")
        return servers

    def load_endpoints(self, server_id: str) -> tuple[EndpointBinding, ...]:
        """按 server_id 读取 endpoint binding。

        该方法用于满足 WhaleMetadataPort；主构建路径会通过 `load_servers`
        一次性读取，避免 runtime tick 期间增量查询。
        """
        return tuple(
            endpoint
            for server in self.load_servers(WritePlanId("adhoc"))
            if server.server_id == server_id
            for endpoint in server.endpoints
        )

    def load_fields(self, endpoint_id: str) -> tuple[FieldBinding, ...]:
        """按 endpoint_id 读取字段 binding。"""
        return tuple(
            field
            for server in self.load_servers(WritePlanId("adhoc"))
            for endpoint in server.endpoints
            if endpoint.endpoint_id == endpoint_id
            for field in endpoint.fields
        )

    def _session_scope(self) -> AbstractContextManager[Session]:
        """返回本次 repository 操作使用的 session context。"""
        if self._session is not None:
            return nullcontext(self._session)
        return self._session_factory()

    def _load_endpoints(self, session: Session) -> tuple[CommunicationEndpoint, ...]:
        """用 Whale ORM relationship 预加载 WritePlan 映射所需配置。"""
        statement = (
            select(CommunicationEndpoint)
            .options(
                selectinload(CommunicationEndpoint.ied),
                selectinload(CommunicationEndpoint.ld_instances)
                .selectinload(LDInstance.signal_profile)
                .selectinload(SignalProfile.items),
            )
            .order_by(CommunicationEndpoint.endpoint_id)
        )
        return tuple(session.scalars(statement).all())
