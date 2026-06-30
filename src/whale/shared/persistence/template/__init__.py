"""共享持久化层模板包导出边界。

本包只承载 ``whale.shared.persistence.template`` 自身的真实参考数据：

- ``protocol_param_data``：多协议端点/信号参数模板。
- ``gbt_30966_fields``：GB/T 30966.2-2022 逻辑节点与字段定义。
- ``protocol_view_defs``：从 ``whale.shared.persistence.views`` 转发
  SCADA 协议视图定义。

本包不再 re-export ``seahorse.reference_data``，也未保留任何兼容
wrapper 或 ``DeprecationWarning``。Round 7B 旧 ``sample_data`` 已物理
删除，本包不导出 sample_data 任何符号；``seahorse.infrastructure.
repositories.whale_metadata_repository`` 自身仍承载样例装配入口。
"""
from __future__ import annotations

from whale.shared.persistence.template.gbt_30966_fields import (
    ALL_LOGICAL_NODES,
    LogicalNodeDef,
    LogicalNodeField,
    build_field_dict,
    total_field_count,
)
from whale.shared.persistence.template.protocol_param_data import (
    ENDPOINT_PARAM_DEFS,
    ParamDef,
    SIGNAL_PARAM_DEFS,
    get_endpoint_params,
    get_signal_params,
)
from whale.shared.persistence.template.protocol_view_defs import (
    SCADA_PROTOCOL_VIEW_DEFINITIONS,
    SCADA_PROTOCOL_VIEW_SQL,
    ViewDefinition,
)


__all__ = [
    "ALL_LOGICAL_NODES",
    "LogicalNodeDef",
    "LogicalNodeField",
    "build_field_dict",
    "total_field_count",
    "ENDPOINT_PARAM_DEFS",
    "SIGNAL_PARAM_DEFS",
    "ParamDef",
    "get_endpoint_params",
    "get_signal_params",
    "SCADA_PROTOCOL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_SQL",
    "ViewDefinition",
]