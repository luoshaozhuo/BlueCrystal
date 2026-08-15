"""共享持久化层数据库视图定义导出边界。

本包只集中表达只读 view 的 SELECT 定义和可渲染 DDL 片段，不创建 engine、
不连接数据库、不调用 create_all，也不把 view 注册进 ORM metadata。
数据库生命周期由 Alembic migration 手动管理。
"""

from __future__ import annotations

from pacific.whale.shared.persistence.views.definition import ViewDefinition
from pacific.whale.shared.persistence.views.registry import ALL_VIEW_DEFINITIONS
from pacific.whale.shared.persistence.views.scada_protocol_views import (
    SCADA_PROTOCOL_VIEW_DEFINITIONS,
    SCADA_PROTOCOL_VIEW_SQL,
)
from pacific.whale.shared.persistence.views.scada_server_view import SCADA_SERVER_VIEW


__all__ = [
    "ALL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_SQL",
    "SCADA_SERVER_VIEW",
    "ViewDefinition",
]
