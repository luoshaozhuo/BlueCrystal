"""SCADA server 汇总 view 的 SQLAlchemy Core 定义。

本模块只描述 `v_scada_server` 的 SELECT 查询，不创建数据库对象。
view 的实际创建和删除由 Alembic migration 通过 registry 管理。
"""

from __future__ import annotations

from sqlalchemy import column, join, select, table

from whale.shared.persistence.views.definition import ViewDefinition

scada_communication_endpoint = table(
    "scada_communication_endpoint",
    column("endpoint_id"),
    column("ied_id"),
    column("access_point_name"),
    column("application_protocol"),
    column("transport"),
    column("host"),
    column("port"),
    column("namespace_uri"),
    column("security_policy"),
    column("security_mode"),
    column("auth_type"),
    column("credential_ref"),
)
scada_ied = table(
    "scada_ied",
    column("ied_id"),
    column("ied_name"),
)
scada_ld_instance = table(
    "scada_ld_instance",
    column("ld_instance_id"),
    column("endpoint_id"),
    column("asset_instance_id"),
    column("signal_profile_id"),
    column("ld_name"),
    column("path_prefix"),
)
asset_instance = table(
    "asset_instance",
    column("asset_instance_id"),
    column("asset_code"),
    column("asset_name"),
)


def _build_scada_server_view() -> ViewDefinition:
    """构造 `v_scada_server` 的只读查询定义。"""

    ep = scada_communication_endpoint
    ied = scada_ied
    ld = scada_ld_instance
    asset = asset_instance
    from_clause = join(ep, ied, ied.c.ied_id == ep.c.ied_id).join(
        ld, ld.c.endpoint_id == ep.c.endpoint_id
    ).join(asset, asset.c.asset_instance_id == ld.c.asset_instance_id)

    selectable = select(
        ep.c.endpoint_id.label("endpoint_id"),
        ep.c.ied_id.label("ied_id"),
        ld.c.ld_instance_id.label("ld_instance_id"),
        ied.c.ied_name.label("ied_name"),
        asset.c.asset_code.label("asset_code"),
        asset.c.asset_name.label("asset_name"),
        ep.c.access_point_name.label("access_point_name"),
        ep.c.application_protocol.label("application_protocol"),
        ep.c.transport.label("transport"),
        ep.c.host.label("host"),
        ep.c.port.label("port"),
        ep.c.namespace_uri.label("namespace_uri"),
        ep.c.security_policy.label("security_policy"),
        ep.c.security_mode.label("security_mode"),
        ep.c.auth_type.label("auth_type"),
        ep.c.credential_ref.label("credential_ref"),
        ld.c.asset_instance_id.label("asset_instance_id"),
        ld.c.signal_profile_id.label("signal_profile_id"),
        ld.c.ld_name.label("ld_name"),
        ld.c.path_prefix.label("path_prefix"),
    ).select_from(from_clause)
    return ViewDefinition("v_scada_server", selectable)


SCADA_SERVER_VIEW = _build_scada_server_view()

__all__ = ["SCADA_SERVER_VIEW"]
