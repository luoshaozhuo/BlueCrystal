"""已废弃的协议视图定义模块。

本模块不再承载真实实现。全部真实实现已迁移至
`seahorse.reference_data.protocol_view_defs`。

本文件仅作为向后兼容的 re-export 包装器保留，
新代码请直接使用 `seahorse.reference_data`。

@deprecated: 使用 `seahorse.reference_data.protocol_view_defs` 替代。
"""
from __future__ import annotations

import warnings

warnings.warn(
    "whale.shared.persistence.template.protocol_view_defs is deprecated. "
    "Use seahorse.reference_data.protocol_view_defs instead.",
    DeprecationWarning,
    stacklevel=2,
)

from seahorse.reference_data.protocol_view_defs import (  # noqa: E402, F401
    _PROTOCOL_VIEW_DEFS,
    ensure_protocol_views,
)
