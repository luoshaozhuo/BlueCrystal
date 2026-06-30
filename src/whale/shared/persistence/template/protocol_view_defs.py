"""共享持久化层协议视图定义入口。

本模块只 re-export ``whale.shared.persistence.views.scada_protocol_views``
中已经定义并由 Alembic 管理的 SCADA 协议视图，作为 ``whale.shared.persistence.template``
包内对 view 维度的统一访问入口。

真实视图定义与 ``CreateView``/``DropView`` DDL 渲染由
``whale.shared.persistence.views`` 承载；本模块不重新维护 view 元数据，
也不再保留对 ``seahorse.reference_data`` 的兼容 wrapper。
"""
from __future__ import annotations

from whale.shared.persistence.views.definition import ViewDefinition
from whale.shared.persistence.views.scada_protocol_views import (
    SCADA_PROTOCOL_VIEW_DEFINITIONS,
    SCADA_PROTOCOL_VIEW_SQL,
)

# 历史 ``_PROTOCOL_VIEW_DEFS`` 形态是 ``dict[str, str]``（view name →
# SELECT SQL 字符串）；现有真实数据 ``SCADA_PROTOCOL_VIEW_SQL`` 已使用同
# 样的 ``dict[str, str]`` 形态，因此保持同名字面导出，避免调用方形态
# 变化。
_PROTOCOL_VIEW_DEFS: dict[str, str] = dict(SCADA_PROTOCOL_VIEW_SQL)


__all__ = [
    "ViewDefinition",
    "SCADA_PROTOCOL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_SQL",
    "_PROTOCOL_VIEW_DEFS",
]