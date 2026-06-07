"""已废弃的 GB/T 30966 字段定义模块。

本模块不再承载真实实现。全部真实实现已迁移至
`seahorse.reference_data.gbt_30966_fields`。

本文件仅作为向后兼容的 re-export 包装器保留，
新代码请直接使用 `seahorse.reference_data.gbt_30966_fields`。

@deprecated: 使用 `seahorse.reference_data.gbt_30966_fields` 替代。
"""
from __future__ import annotations

import warnings

warnings.warn(
    "whale.shared.persistence.template.gbt_30966_fields is deprecated. "
    "Use seahorse.reference_data.gbt_30966_fields instead.",
    DeprecationWarning,
    stacklevel=2,
)

from seahorse.reference_data.gbt_30966_fields import (  # noqa: E402, F401
    ALL_LOGICAL_NODES,
    LogicalNodeDef,
    LogicalNodeField,
    LTIM,
    WALG,
    WALM,
    WAPC,
    WAVL,
    WCNV,
    WMET,
    WNAC,
    WPPD,
    WREP,
    WROT,
    WRPC,
    WSLG,
    WTOW,
    WTRF,
    WTRM,
    WTUR,
    WYAW,
    build_field_dict,
    total_field_count,
)

__all__ = [
    "LogicalNodeField",
    "LogicalNodeDef",
    "build_field_dict",
    "total_field_count",
    "ALL_LOGICAL_NODES",
    "WPPD",
    "WTUR",
    "WROT",
    "WTRM",
    "WGEN",
    "WCNV",
    "WTRF",
    "WNAC",
    "WYAW",
    "WTOW",
    "WMET",
    "WALM",
    "WSLG",
    "WALG",
    "WREP",
    "WAVL",
    "WAPC",
    "WRPC",
    "LTIM",
]
