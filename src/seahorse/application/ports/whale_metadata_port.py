"""Whale 元数据运行计划读取端口。

该端口只表达构建 WritePlan 所需的 server/point/field 配置读取契约；
真实 Whale ORM 访问必须隔离在 infrastructure/repositories，本轮不接
真实查询实现。
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from seahorse.domain.runtime_contract import EndpointBinding, FieldBinding, ServerBinding, WritePlanId


@runtime_checkable
class WhaleMetadataPort(Protocol):
    """Whale 元数据读取端口。

    实现方应一次性读取构建 WritePlan 所需配置；runtime tick 期间不应
    通过该端口查询 Whale DB。
    """

    def load_servers(self, plan_id: WritePlanId) -> tuple[ServerBinding, ...]:
        """读取 server binding 集合。"""
        ...

    def load_endpoints(self, server_id: str) -> tuple[EndpointBinding, ...]:
        """读取指定 server 的 endpoint binding 集合。"""
        ...

    def load_fields(self, endpoint_id: str) -> tuple[FieldBinding, ...]:
        """读取指定 endpoint 的字段绑定集合。"""
        ...
