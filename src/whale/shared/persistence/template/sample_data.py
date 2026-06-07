"""已废弃的 SCADA 样例数据模块。

本模块不再承载真实实现。全部真实实现已迁移至
`seahorse.reference_data.sample_data`。

本文件仅作为向后兼容的 re-export 包装器保留，
新代码请直接使用 `seahorse.reference_data`。

@deprecated: 使用 `seahorse.reference_data.sample_data` 替代。
"""
from __future__ import annotations

import warnings

warnings.warn(
    "whale.shared.persistence.template.sample_data is deprecated. "
    "Use seahorse.reference_data.sample_data instead.",
    DeprecationWarning,
    stacklevel=2,
)

# ── 从 seahorse re-export 所有公开和内部符号 ──────────────────────────────────
from seahorse.reference_data.sample_data import (  # noqa: E402, F401
    PROTOCOL_SAMPLE_SPECS,
    ProtocolSampleSpec,
    ScalarValue,
    generate_all_sample_data,
    # 以下为测试所需的 internal helpers
    _build_param_value_kwargs,
    _build_service_capabilities,
    _create_acquisition_tasks,
    _create_asset_types_and_models,
    _create_cdc_fc,
    _create_data_types,
    _create_endpoint_param_values,
    _create_org,
    _create_protocol_samples,
    _create_signal_param_values,
    _create_signal_profile,
    _resolve_acquisition_mode,
    _resolve_constraint,
    _resolve_da_name,
    _resolve_fc,
    _seed_protocol_param_defs,
)


if __name__ == "__main__":
    from whale.shared.persistence.init_db import init_db as _init_db

    _init_db(force=True)
    generate_all_sample_data()
