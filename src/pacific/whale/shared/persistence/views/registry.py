"""shared persistence 数据库 view 注册表。

本模块只汇总 Alembic migration 需要管理的 view 定义，不注册 ORM metadata，
也不执行任何数据库 DDL。
"""

from __future__ import annotations

from pacific.whale.shared.persistence.views.definition import ViewDefinition
from pacific.whale.shared.persistence.views.scada_protocol_views import SCADA_PROTOCOL_VIEW_DEFINITIONS
from pacific.whale.shared.persistence.views.scada_server_view import SCADA_SERVER_VIEW

ALL_VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = (
    SCADA_SERVER_VIEW,
    *SCADA_PROTOCOL_VIEW_DEFINITIONS,
)

__all__ = ["ALL_VIEW_DEFINITIONS"]
