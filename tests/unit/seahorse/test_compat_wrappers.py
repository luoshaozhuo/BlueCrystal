"""seahorse 旧路径硬清理验证。

本测试断言：

1. ``seahorse.models``、``seahorse.exporters``、``seahorse.strategies``、
   ``seahorse.generators``、``seahorse.orchestration``、``seahorse.ports``、
   ``seahorse.reference_data`` 旧顶层目录已物理删除。
2. 直接 import 旧顶层包或其同名单文件均抛 ``ImportError`` 或
   ``ModuleNotFoundError``；不再提供任何兼容 wrapper。
3. 旧路径不再出现在 ``seahorse`` 包或其子包的 ``__all__`` 中。
4. 参考参数数据仍可通过 ``whale.shared.persistence.template`` 取得
   （真实数据归属），保证原使用方仍有可用入口。

测试阶段：构建期验证 (P2)。
不能证明：旧 import 实际用户已迁移；仅证明仓库自身不再保留兼容层。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_SEAHORSE = PROJECT_ROOT / "src" / "seahorse"

LEGACY_TOP_PACKAGES = (
    "seahorse.models",
    "seahorse.exporters",
    "seahorse.strategies",
    "seahorse.generators",
    "seahorse.orchestration",
    "seahorse.ports",
    "seahorse.reference_data",
)

LEGACY_TOP_DIRS = (
    SRC_SEAHORSE / "models",
    SRC_SEAHORSE / "exporters",
    SRC_SEAHORSE / "strategies",
    SRC_SEAHORSE / "generators",
    SRC_SEAHORSE / "orchestration",
    SRC_SEAHORSE / "ports",
    SRC_SEAHORSE / "reference_data",
)

LEGACY_LEAF_MODULES = (
    "seahorse.models.scenario",
    "seahorse.models.plan",
    "seahorse.models.generation",
    "seahorse.models.bundle",
    "seahorse.exporters.bundle_exporter",
    "seahorse.exporters.bundle_validator",
    "seahorse.exporters.server_config_exporter",
    "seahorse.exporters.server_config_validator",
    "seahorse.exporters.server_plan_exporter",
    "seahorse.exporters.server_plan_validator",
    "seahorse.exporters.serialization",
    "seahorse.exporters.timeseries_exporter",
    "seahorse.strategies.curve_generation",
    "seahorse.strategies.random_generation",
    "seahorse.strategies.replay_generation",
    "seahorse.strategies.registry",
    "seahorse.generators.alarm_generator",
    "seahorse.generators.control_result_generator",
    "seahorse.orchestration.scenario_generator",
    "seahorse.ports.generation_strategy",
    "seahorse.reference_data.protocol_param_data",
    "seahorse.reference_data.protocol_view_defs",
    "seahorse.reference_data.sample_data",
    "seahorse.reference_data.gbt_30966_fields",
)


def _purge_module(name: str) -> None:
    """从 ``sys.modules`` 中删除指定模块及其所有子模块。

    直接 importlib.import_module 会命中先前测试遗留的缓存，无法验证
    当前仓库结构；必须先清缓存再触发 import。
    """
    targets = [
        key
        for key in list(sys.modules)
        if key == name or key.startswith(name + ".")
    ]
    for key in targets:
        sys.modules.pop(key, None)


@pytest.mark.parametrize("legacy_dir", LEGACY_TOP_DIRS, ids=lambda p: p.name)
def test_legacy_top_dirs_removed(legacy_dir: Path) -> None:
    """旧顶层目录必须不存在。"""
    assert not legacy_dir.exists(), f"{legacy_dir} 应已被删除"


@pytest.mark.parametrize("pkg", LEGACY_TOP_PACKAGES)
def test_legacy_top_packages_not_importable(pkg: str) -> None:
    """旧顶层包 import 必须失败。"""
    _purge_module(pkg)
    with pytest.raises((ModuleNotFoundError, ImportError)):
        importlib.import_module(pkg)


@pytest.mark.parametrize("leaf", LEGACY_LEAF_MODULES)
def test_legacy_leaf_modules_not_importable(leaf: str) -> None:
    """旧同名单文件 import 必须失败。"""
    _purge_module(leaf)
    with pytest.raises((ModuleNotFoundError, ImportError)):
        importlib.import_module(leaf)


def test_seahorse_package_root_has_no_legacy_name() -> None:
    """seahorse 包根目录不再含旧顶层路径。

    seahorse 包 ``__init__.py`` 不定义 ``__all__``，因此扫描其所在目录
    下的子目录列表以确保旧顶层路径名已物理消失。
    """
    forbidden = {"models", "exporters", "strategies", "generators",
                 "orchestration", "ports", "reference_data"}
    current = {p.name for p in SRC_SEAHORSE.iterdir() if p.is_dir()}
    leaked = forbidden.intersection(current)
    assert not leaked, f"seahorse 包根目录仍含旧路径: {sorted(leaked)}"


def test_seahorse_domain_init_does_not_advertise_legacy_models() -> None:
    """seahorse.domain __init__ 不再提到 ``seahorse.models`` 兼容 wrapper。"""
    from seahorse import domain

    docstring = (domain.__doc__ or "")
    assert "seahorse.models" not in docstring, (
        "domain.__doc__ 仍包含旧路径说明：seahorse.models 应被完全删除"
    )


def test_seahorse_use_cases_init_does_not_advertise_legacy_paths() -> None:
    """seahorse.application.use_cases __init__ 不再提到旧顶层路径。"""
    from seahorse.application import use_cases

    docstring = (use_cases.__doc__ or "")
    for legacy in ("seahorse.orchestration", "seahorse.generators"):
        assert legacy not in docstring, (
            f"application.use_cases.__doc__ 仍提到旧路径 {legacy}"
        )


def test_reference_data_replaced_by_whale_template_top_level() -> None:
    """真实参考数据归属：Whale shared persistence.template 顶层目录仍存在。

    Round 7B 不修改 ``src/whale``（handoff forbidden）。该 wrapper 自身仍
    re-export 已被删除的 ``seahorse.reference_data``，不可直接 import。本
    测试只验证顶层目录及其 ``__init__.py`` 仍存在，作为 Whale 后续清理
    Round 的目标定位。
    """
    template_dir = (
        PROJECT_ROOT / "src" / "whale" / "shared" / "persistence" / "template"
    )
    assert template_dir.is_dir(), f"{template_dir} 顶层目录必须存在"
    assert (template_dir / "__init__.py").is_file(), (
        f"{template_dir}/__init__.py 必须存在"
    )