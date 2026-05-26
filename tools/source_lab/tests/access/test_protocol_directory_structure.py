"""协议目录结构合规性测试。

验证：
1. ADR-20260524-006: 旧 tools/source_lab/opcua/ 已被删除。
2. 所有协议目录有非空 __init__.py。
3. 所需协议目录存在。
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROTOCOLS_DIR = Path(__file__).resolve().parents[2] / "protocols"
SOURCE_LAB_DIR = Path(__file__).resolve().parents[3]


class TestProtocolDirectoryDeleted:
    """ADR-20260524-006: 旧 opcua/ 目录已被删除。"""

    def test_old_opcua_directory_does_not_exist(self) -> None:
        old_dir = SOURCE_LAB_DIR / "opcua"
        assert not old_dir.exists(), (
            f"Old directory {old_dir} still exists. "
            "ADR-20260524-006 mandated deletion. "
            "All content has been moved to protocols/opcua/."
        )


class TestProtocolDirectoriesExist:
    """所需协议目录必须存在。"""

    REQUIRED_PROTOCOL_DIRS = [
        "opcua",
        "modbus",
        "iec104",
        "iec61850",
        "iec101",
        "mqtt",
        "http_rest",
    ]

    @pytest.fixture(params=REQUIRED_PROTOCOL_DIRS)
    def protocol_dir(self, request: pytest.FixtureRequest) -> Path:
        return PROTOCOLS_DIR / request.param

    def test_protocol_directory_exists(self, protocol_dir: Path) -> None:
        assert protocol_dir.is_dir(), f"Required protocol directory {protocol_dir} does not exist"

    def test_protocol_init_py_exists_and_non_empty(self, protocol_dir: Path) -> None:
        init_file = protocol_dir / "__init__.py"
        assert init_file.exists(), f"{init_file} does not exist"
        content = init_file.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"{init_file} is empty"


class TestSimulatorFileExists:
    """各协议目录必须有 simulator.py（占位或实现）。"""

    REQUIRED_SIMULATOR_DIRS = [
        "opcua",
        "modbus",
        "iec104",
        "iec61850",
        "iec101",
        "mqtt",
        "http_rest",
    ]

    @pytest.fixture(params=REQUIRED_SIMULATOR_DIRS)
    def protocol_dir(self, request: pytest.FixtureRequest) -> Path:
        return PROTOCOLS_DIR / request.param

    def test_simulator_file_exists(self, protocol_dir: Path) -> None:
        sim_file = protocol_dir / "simulator.py"
        assert sim_file.exists(), f"{sim_file} does not exist"


class TestCommonModulesExist:
    """common/ 目录必须包含必要模块。"""

    REQUIRED_COMMON_MODULES = [
        "simulator_models.py",
        "simulator_facade.py",
        "_base_facade.py",
        "simulators.py",
    ]

    def test_common_modules_exist(self) -> None:
        common_dir = PROTOCOLS_DIR / "common"
        assert common_dir.is_dir()
        for module in self.REQUIRED_COMMON_MODULES:
            assert (common_dir / module).exists(), f"{common_dir / module} does not exist"

    def test_no_old_opcua_in_common(self) -> None:
        """验证 common/ 下没有意外残留。"""
        common_dir = PROTOCOLS_DIR / "common"
        for entry in common_dir.iterdir():
            assert not entry.name.endswith(".pyc")


class TestRegistryModule:
    """registry.py 存在且包含新工厂函数。"""

    def test_registry_has_factory_functions(self) -> None:
        import inspect
        from tools.source_lab.protocols import registry

        assert hasattr(registry, "create_server_simulator")
        assert hasattr(registry, "get_server_simulator_capabilities")
        assert hasattr(registry, "list_server_simulator_protocols")
        assert hasattr(registry, "get_simulator_factory")  # backward compat

    def test_old_simulator_factory_still_works(self) -> None:
        """向后兼容的 get_simulator_factory 仍然可用。"""
        from tools.source_lab.protocols.registry import get_simulator_factory

        factory = get_simulator_factory("opcua")
        assert factory is not None
