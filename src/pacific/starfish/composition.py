"""Starfish pandas-first 依赖装配与协议分派入口。

本模块以 connection DataFrame 分组调用协议 loader，再以 concat/merge/cardinality
检查组合一行一个 point 的公共配置帧。Engine 在配置物化后确定性释放；协议原生
对象只由 factory/worker 边界创建。
"""

from __future__ import annotations

from typing import Sequence

from pacific.starfish.adapters import PGViewLoader
from pacific.starfish.adapters import DbViewLoadError
from pacific.starfish.adapters import ProtocolServerFactory
from pacific.starfish.core import BaseConnection
from pacific.starfish.core import IEC104Connection, IEC104SrcPointItem, IEC104SinkPointItem
from pacific.starfish.core import ADSConnection, ADSSrcPointItem, ADSSinkPointItem
from pacific.starfish.core import StarfishServerManager
from pacific.starfish.core import ServerDefinition

VIEW_SELECTOR = {
    'IEC104': (IEC104Connection, IEC104SrcPointItem, IEC104SinkPointItem),
    'ADS': (ADSConnection, ADSSrcPointItem, ADSSinkPointItem),
}

def build_server_manager_from_db(connection_ids: Sequence[int] | None = None) -> StarfishServerManager:
    """以 pandas 配置主链路装配 server manager。

    Args:
        connection_ids: 选定 IDs；``None`` 表示从同一 Engine 枚举全部 connection。

    Returns:
        持有规范化配置帧和协议 workers、尚未启动且不再依赖数据库的 manager。

    Raises:
        DbViewLoadError: ID 为空、配置缺失/重复或 protocol 尚未注册。
    """
    if connection_ids is not None and len(connection_ids) == 0:
        raise DbViewLoadError("connection_ids 不能为空")

    conn_df = PGViewLoader().load(BaseConnection, _in={"connection_id": connection_ids} if connection_ids is not None else None)
    if conn_df.empty:
        raise DbViewLoadError("connection_ids 不存在或未注册协议")
    
    servers = []
    for row in conn_df.iterrows():
        view_cls = VIEW_SELECTOR[row['protocol']]
        _conn_sr = PGViewLoader().load(view_cls[0], _equ={"connection_id": row['connection_id']}).squeeze()
        _src_point_item_df = PGViewLoader().load(view_cls[1], _equ={"point_table_id": _conn_sr['src_point_table_id']})
        _sink_point_item_df = PGViewLoader().load(view_cls[2], _equ={"point_table_id": _conn_sr['sink_point_table_id']})
        servers.append(ProtocolServerFactory.create(ServerDefinition(_conn_sr, _src_point_item_df, _sink_point_item_df)))

    return StarfishServerManager(servers)

__all__ = ["build_server_manager_from_db"]
