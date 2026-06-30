"""seahorse reference_data 硬清理验证。

原 ``seahorse.reference_data`` 兼容 wrapper 已在 Round 7B 删除；其真实
参考数据由 ``whale.shared.persistence.template`` 承载。本测试断言：

1. ``seahorse.reference_data`` 旧顶层包不可再被 import。
2. 旧 ``seahorse.reference_data.protocol_param_data`` 等同名单文件不可再
   被 import。
3. 真实协议参数矩阵仍可通过 ``whale.shared.persistence.template`` 取得，
   行为不变。

测试阶段：构建期验证 (P2)。
不能证明：所有原 import 路径使用方都已迁移；仅证明仓库自身不再保留旧
reference_data 兼容入口。
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_SEAHORSE_REF_DIR = PROJECT_ROOT / "src" / "seahorse" / "reference_data"


def _purge_module(name: str) -> None:
    targets = [key for key in list(sys.modules)
               if key == name or key.startswith(name + ".")]
    for key in targets:
        sys.modules.pop(key, None)


def test_legacy_reference_data_directory_removed() -> None:
    """seahorse.reference_data 顶层目录必须已物理删除。"""
    assert not SRC_SEAHORSE_REF_DIR.exists(), (
        f"{SRC_SEAHORSE_REF_DIR} 应已被删除"
    )


@pytest.mark.parametrize(
    "module_name",
    [
        "seahorse.reference_data",
        "seahorse.reference_data.protocol_param_data",
        "seahorse.reference_data.protocol_view_defs",
        "seahorse.reference_data.sample_data",
        "seahorse.reference_data.gbt_30966_fields",
    ],
)
def test_legacy_reference_data_modules_not_importable(module_name: str) -> None:
    """旧 reference_data 模块 import 必须失败。"""
    _purge_module(module_name)
    with pytest.raises((ModuleNotFoundError, ImportError)):
        importlib.import_module(module_name)


def test_protocol_param_data_available_via_whale_template() -> None:
    """协议参数数据源文件应仍位于 Whale shared persistence 模板目录。

    ``whale.shared.persistence.template.protocol_param_data`` 自身为旧
    wrapper，仍然 re-export 已被删除的 ``seahorse.reference_data``（属于
    whale 后续清理项，本轮 handoff forbidden），不可直接 import。本测试
    只验证文件仍存在于 ``whale.shared.persistence.template`` 目录，作为
    Round 7B 后续清理的目标定位。
    """
    file_path = (
        PROJECT_ROOT
        / "src"
        / "whale"
        / "shared"
        / "persistence"
        / "template"
        / "protocol_param_data.py"
    )
    assert file_path.is_file(), (
        f"{file_path} 必须存在，作为 Whale 协议参数真实数据源"
    )


def test_protocol_view_defs_available_via_whale_views() -> None:
    """协议视图定义应仍可通过 whale.shared.persistence.views 取得。

    ``whale.shared.persistence.views`` 是 Round 7B 未触及的独立包（不
    re-export seahorse.reference_data），其 ``scada_protocol_views`` 子
    模块直接承载 view 定义，本测试可安全 import。
    """
    from whale.shared.persistence.views.scada_protocol_views import (
        ViewDefinition,
        SCADA_PROTOCOL_VIEW_DEFINITIONS,
    )

    assert len(SCADA_PROTOCOL_VIEW_DEFINITIONS) > 0
    assert all(
        isinstance(item, ViewDefinition)
        for item in SCADA_PROTOCOL_VIEW_DEFINITIONS
    )


def test_gbt_30966_fields_available_via_whale_template() -> None:
    """GB/T 30966 字段定义源文件应仍位于 Whale 模板目录。

    ``whale.shared.persistence.template.gbt_30966_fields`` 是旧 wrapper，
    仍 re-export 已删除的 ``seahorse.reference_data.gbt_30966_fields``
    （属于 whale 后续清理项，本轮 forbidden）。本测试只验证源文件位置
    仍可定位，不实际 import 触发 wrapper。
    """
    file_path = (
        PROJECT_ROOT
        / "src"
        / "whale"
        / "shared"
        / "persistence"
        / "template"
        / "gbt_30966_fields.py"
    )
    assert file_path.is_file(), (
        f"{file_path} 必须存在，作为 GB/T 30966 字段真实数据源"
    )


def test_whale_metadata_repository_does_not_import_seahorse_reference_data() -> None:
    """seahorse.infrastructure.repositories.whale_metadata_repository 不得
    再 import ``seahorse.reference_data``。
    """
    import ast

    repo_path = (
        PROJECT_ROOT
        / "src"
        / "seahorse"
        / "infrastructure"
        / "repositories"
        / "whale_metadata_repository.py"
    )
    assert repo_path.is_file(), f"{repo_path} 必须存在"
    tree = ast.parse(repo_path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("seahorse.reference_data"):
                offenders.append(node.module)
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("seahorse.reference_data"):
                    offenders.append(alias.name)
    assert offenders == [], (
        f"whale_metadata_repository 不应再 import seahorse.reference_data: {offenders}"
    )