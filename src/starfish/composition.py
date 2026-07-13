"""Starfish 依赖装配与协议分派入口。

本模块先通过通用 connection view 获取 protocol，再按 protocol registry 调用
对应 definition loader。core 不依赖数据库、registry 或具体协议 adapter。
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence

from starfish.adapters.db_views import ConnectionDbViewLoader, DbViewLoadError
from starfish.adapters.db_views.iec104 import Iec104DbViewLoader
from starfish.adapters.protocols import ProtocolServerFactory
from starfish.core import StarfishServerManager
from starfish.core.definitions import ServerDefinition
from starfish.core.ports.server_loader import ServerDefinitionLoaderPort

ProtocolLoaderFactory = Callable[[str], ServerDefinitionLoaderPort]


def list_connection_ids_from_db(db_url: str) -> list[int]:
    """列出 `vw_connection_object_full` 中的全部 connection IDs。"""
    return ConnectionDbViewLoader(db_url).list_connection_ids()


def build_server_manager_from_db(
    db_url: str,
    connection_ids: Sequence[int],
    *,
    loader_factories: dict[str, ProtocolLoaderFactory] | None = None,
) -> StarfishServerManager:
    """按 connection IDs 的实际 protocol 装配 server manager。

    Args:
        db_url: `WHALE_DB_URL` 提供的 SQLAlchemy 数据库 URL。
        connection_ids: CLI 或其他调用方选定的 connection IDs。
        loader_factories: protocol 到 loader factory 的可选注册表，主要用于测试
            或后续协议扩展；默认当前只注册 IEC104。

    Returns:
        已持有协议 server workers、尚未启动的 manager。

    Raises:
        DbViewLoadError: ID 为空、connection 不存在或 protocol 尚未注册。
    """
    # 去重并确保 connection IDs 为整数列表。
    normalized_ids = list(dict.fromkeys(int(value) for value in connection_ids))
    if not normalized_ids:
        raise DbViewLoadError("connection_ids 不能为空")

    protocols = ConnectionDbViewLoader(db_url).load_protocols(normalized_ids)
    grouped_ids: dict[str, list[int]] = defaultdict(list)
    for connection_id in normalized_ids:
        grouped_ids[protocols[connection_id]].append(connection_id)

    factories = loader_factories or {
        "IEC104": lambda url: Iec104DbViewLoader(url),
    }
    definitions: list[ServerDefinition] = []
    for protocol, protocol_connection_ids in grouped_ids.items():
        loader_factory = factories.get(protocol)
        if loader_factory is None:
            raise DbViewLoadError(
                f"未注册 protocol={protocol} 的 Starfish server loader，"
                f"connection_ids={protocol_connection_ids}"
            )
        definitions.extend(loader_factory(db_url).load(protocol_connection_ids))

    definitions_by_id = {
        definition.connection_id: definition for definition in definitions
    }
    missing_definitions = sorted(set(normalized_ids) - definitions_by_id.keys())
    if missing_definitions:
        raise DbViewLoadError(
            f"protocol loader 未返回 connection definitions: {missing_definitions}"
        )
    ordered_definitions = [definitions_by_id[value] for value in normalized_ids]
    return StarfishServerManager.from_definitions(
        ordered_definitions,
        ProtocolServerFactory(),
    )


__all__ = ["build_server_manager_from_db", "list_connection_ids_from_db"]
