"""已废弃的共享持久化层模板导出边界。

本包不再承载真实实现。全部真实实现已迁移至 `seahorse.reference_data`。

本文件仅作为向后兼容的 re-export 包装器保留，
新代码请直接使用 `seahorse.reference_data`。

@deprecated: 新代码请使用 `seahorse.reference_data`。
  Round 11 背景：tools/source_lab/ 已物理删除，模板包装器是遗留桥接层。
"""
from __future__ import annotations

import warnings

warnings.warn(
    "whale.shared.persistence.template is deprecated. "
    "Use seahorse.reference_data instead.",
    DeprecationWarning,
    stacklevel=2,
)

from seahorse.reference_data import (  # noqa: E402, F401
    ENDPOINT_PARAM_DEFS,
    PROTOCOL_SAMPLE_SPECS,
    SIGNAL_PARAM_DEFS,
    _PROTOCOL_VIEW_DEFS,
    ParamDef,
    ProtocolSampleSpec,
    ensure_protocol_views,
    generate_all_sample_data,
    get_endpoint_params,
    get_signal_params,
)

__all__ = [
    "ENDPOINT_PARAM_DEFS",
    "SIGNAL_PARAM_DEFS",
    "_PROTOCOL_VIEW_DEFS",
    "ensure_protocol_views",
    "PROTOCOL_SAMPLE_SPECS",
    "generate_all_sample_data",
]
