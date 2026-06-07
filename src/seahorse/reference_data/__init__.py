"""seahorse 参考数据层。

本包包含协议参数模板、样例数据规格、30966 字段定义和协议查询视图。
这些数据供样例数据库初始化、Navicat 浏览、本地演示和单测使用，
不依赖 whale ingest runtime。
"""

from __future__ import annotations

from seahorse.reference_data.protocol_param_data import (
    ENDPOINT_PARAM_DEFS,
    SIGNAL_PARAM_DEFS,
    ParamDef,
    get_endpoint_params,
    get_signal_params,
)
from seahorse.reference_data.protocol_view_defs import (
    _PROTOCOL_VIEW_DEFS,
    ensure_protocol_views,
)
from seahorse.reference_data.sample_data import (
    PROTOCOL_SAMPLE_SPECS,
    ProtocolSampleSpec,
    generate_all_sample_data,
)

__all__ = [
    "ParamDef",
    "ENDPOINT_PARAM_DEFS",
    "SIGNAL_PARAM_DEFS",
    "get_endpoint_params",
    "get_signal_params",
    "_PROTOCOL_VIEW_DEFS",
    "ensure_protocol_views",
    "ProtocolSampleSpec",
    "PROTOCOL_SAMPLE_SPECS",
    "generate_all_sample_data",
]
