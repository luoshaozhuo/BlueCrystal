"""旧路径兼容包装器测试。

验证：
1. 旧路径 whale.shared.persistence.template 模块仍可导入。
2. 旧路径导出的对象与新路径 seahorse.reference_data 完全相同。
3. 旧路径导入触发 DeprecationWarning。

测试阶段：开发期验证 (P1)。
不能证明：生产环境集成正确性。
"""
from __future__ import annotations

import warnings
from typing import Any


def collect_public_names(module: Any) -> set[str]:
    """收集模块中不以 `_` 开头的公开名称。"""
    return {name for name in dir(module) if not name.startswith("_")}


def test_old_template_init_still_importable() -> None:
    """旧路径 __init__ 仍可导入。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import whale.shared.persistence.template

        assert hasattr(whale.shared.persistence.template, "ENDPOINT_PARAM_DEFS")
        assert hasattr(whale.shared.persistence.template, "PROTOCOL_SAMPLE_SPECS")
        assert hasattr(whale.shared.persistence.template, "generate_all_sample_data")


def test_old_protocol_param_data_still_importable() -> None:
    """旧路径 protocol_param_data 仍可导入。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from whale.shared.persistence.template.protocol_param_data import (
            ENDPOINT_PARAM_DEFS,
            ParamDef,
            get_endpoint_params,
        )

        assert isinstance(ENDPOINT_PARAM_DEFS, dict)
        assert "OPC_UA" in ENDPOINT_PARAM_DEFS
        result = get_endpoint_params("OPC_UA", "READ")
        assert len(result) > 0
        assert all(isinstance(p, ParamDef) for p in result)


def test_old_protocol_view_defs_still_importable() -> None:
    """旧路径 protocol_view_defs 仍可导入。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from whale.shared.persistence.template.protocol_view_defs import (
            _PROTOCOL_VIEW_DEFS,
            ensure_protocol_views,
        )

        assert isinstance(_PROTOCOL_VIEW_DEFS, dict)
        assert callable(ensure_protocol_views)


def test_old_sample_data_still_importable() -> None:
    """旧路径 sample_data 仍可导入。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from whale.shared.persistence.template.sample_data import (
            PROTOCOL_SAMPLE_SPECS,
            ProtocolSampleSpec,
            generate_all_sample_data,
        )

        assert len(PROTOCOL_SAMPLE_SPECS) == 16
        assert all(isinstance(s, ProtocolSampleSpec) for s in PROTOCOL_SAMPLE_SPECS)
        assert callable(generate_all_sample_data)


def test_old_path_triggers_deprecation_warning() -> None:
    """旧路径导入必须触发 DeprecationWarning。"""
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        # 需要清除已有模块缓存才能重新触发 warning
        import sys

        for mod_key in [
            "whale.shared.persistence.template",
            "whale.shared.persistence.template.protocol_param_data",
            "whale.shared.persistence.template.protocol_view_defs",
            "whale.shared.persistence.template.sample_data",
        ]:
            sys.modules.pop(mod_key, None)

        import whale.shared.persistence.template  # noqa: F401

        deprecations = [w for w in recorded if issubclass(w.category, DeprecationWarning)]
        assert len(deprecations) >= 1, "旧路径导入应触发 DeprecationWarning"


def test_new_and_old_path_objects_are_identical() -> None:
    """新路径和旧路径导出的核心对象应为同一对象（引用相等）。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from seahorse.reference_data import ENDPOINT_PARAM_DEFS as new_ep
        from whale.shared.persistence.template import ENDPOINT_PARAM_DEFS as old_ep

    assert new_ep is old_ep, "新旧路径导入的 ENDPOINT_PARAM_DEFS 不是同一对象"


def test_old_template_internal_imports_work() -> None:
    """旧路径内部导入仍可正常工作（测试 private helpers 兼容性）。"""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        from whale.shared.persistence.template.sample_data import (
            _create_org,
            _resolve_acquisition_mode,
            _resolve_da_name,
            _resolve_fc,
        )

        assert callable(_create_org)
        assert _resolve_da_name("MV") == "mag.f"
        assert _resolve_da_name("SPS") == "stVal"
        assert _resolve_fc("SPS") == "ST"
        assert _resolve_fc("MV") == "MX"
        assert _resolve_acquisition_mode("READ") == "POLLING"
        assert _resolve_acquisition_mode("SUBSCRIBE") == "SUBSCRIBE"
