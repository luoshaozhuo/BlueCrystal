"""已废弃的协议参数定义模块。

本模块不再承载真实实现。全部真实实现已迁移至
`seahorse.reference_data.protocol_param_data`。

本文件仅作为向后兼容的 re-export 包装器保留，
新代码请直接使用 `seahorse.reference_data`。

@deprecated: 使用 `seahorse.reference_data.protocol_param_data` 替代。
"""
from __future__ import annotations

import warnings

warnings.warn(
    "whale.shared.persistence.template.protocol_param_data is deprecated. "
    "Use seahorse.reference_data.protocol_param_data instead.",
    DeprecationWarning,
    stacklevel=2,
)

from seahorse.reference_data.protocol_param_data import (  # noqa: E402, F401
    ENDPOINT_PARAM_DEFS,
    SIGNAL_PARAM_DEFS,
    ParamDef,
    get_endpoint_params,
    get_signal_params,
)
