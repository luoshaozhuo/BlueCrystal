"""共享持久化层模板包导出边界。

本包只承载 ``whale.shared.persistence.template`` 自身的真实参考数据：

- ``protocol_param_data``：多协议端点/信号参数模板。
- ``gbt_30966_fields``：GB/T 30966.2-2022 逻辑节点与字段定义。
- ``protocol_view_defs``：从 ``whale.shared.persistence.views`` 转发
  SCADA 协议视图定义。
- ``sample_data``：16 组协议-服务样例 + whale 元数据种子入口
  （``generate_all_sample_data`` / ``clear_database_data`` /
  ``reset_sample_data``）；样例数据种子入口见
  ``whale.shared.persistence.template.sample_data``。

本包不再 re-export ``seahorse.reference_data``，也未保留任何兼容
wrapper 或 ``DeprecationWarning``。
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
from whale.shared.persistence.sample_data import (
    PROTOCOL_SAMPLE_SPECS,
    ProtocolSampleSpec,
    clear_database_data,
    generate_all_sample_data,
    reset_sample_data,
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
    "PROTOCOL_SAMPLE_SPECS",
    "ProtocolSampleSpec",
    "clear_database_data",
    "generate_all_sample_data",
    "reset_sample_data",
    "SCADA_PROTOCOL_VIEW_DEFINITIONS",
    "SCADA_PROTOCOL_VIEW_SQL",
    "ViewDefinition",
]
