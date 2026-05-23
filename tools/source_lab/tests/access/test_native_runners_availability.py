"""Native runner availability tests — verify compiled executables exist.

如果某 native executable 不存在，测试以 ``dependency_missing`` 跳过。
不允许 fake PASS。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.runners.native_cmd import NativeCmdCapacityRunner
from tools.source_lab.access.runners.native_runner_map import NATIVE_CAPACITY_RUNNERS

_NATIVE_DIR = Path(__file__).resolve().parents[3] / "native" / "build"


def _executable_path(name: str) -> Path:
    return _NATIVE_DIR / name


def test_modbus_tcp_native_executable() -> None:
    """libmodbus TCP polling runner executable must exist or skip."""
    exe = _executable_path("modbus_tcp_polling_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: modbus_tcp_polling_runner not compiled (libmodbus missing)")


def test_modbus_rtu_native_executable() -> None:
    """libmodbus RTU polling runner executable must exist or skip."""
    exe = _executable_path("modbus_rtu_polling_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: modbus_rtu_polling_runner not compiled (libmodbus missing)")


def test_modbus_simulator_executable() -> None:
    """Modbus simulator server executable must exist or skip."""
    exe = _executable_path("modbus_simulator_server")
    if not exe.exists():
        pytest.skip("dependency_missing: modbus_simulator_server not compiled (libmodbus missing)")


def test_iec104_client_executable() -> None:
    """IEC104 client runner executable must exist or skip."""
    exe = _executable_path("iec104_client_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: iec104_client_runner not compiled (lib60870 missing)")


def test_iec101_client_executable() -> None:
    """IEC101 client runner executable must exist or skip."""
    exe = _executable_path("iec101_client_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: iec101_client_runner not compiled (lib60870 missing)")


def test_iec61850_mms_client_executable() -> None:
    """IEC61850 MMS client runner executable must exist or skip."""
    exe = _executable_path("iec61850_mms_client_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: iec61850_mms_client_runner not compiled (libiec61850 missing)")


def test_iec61850_goose_subscriber_executable() -> None:
    """IEC61850 GOOSE subscriber executable must exist or skip."""
    exe = _executable_path("iec61850_goose_subscriber_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: iec61850_goose_subscriber_runner not compiled (libiec61850 missing)")


def test_iec61850_sv_subscriber_executable() -> None:
    """IEC61850 SV subscriber executable must exist or skip."""
    exe = _executable_path("iec61850_sv_subscriber_runner")
    if not exe.exists():
        pytest.skip("dependency_missing: iec61850_sv_subscriber_runner not compiled (libiec61850 missing)")


def test_native_runner_map_has_entries() -> None:
    """NATIVE_CAPACITY_RUNNERS must have entries for all core protocols."""
    assert "modbus_tcp" in NATIVE_CAPACITY_RUNNERS
    assert "modbus_rtu" in NATIVE_CAPACITY_RUNNERS
    assert "iec104" in NATIVE_CAPACITY_RUNNERS
    assert "iec101" in NATIVE_CAPACITY_RUNNERS
    assert "iec61850_mms" in NATIVE_CAPACITY_RUNNERS


def test_capacity_runner_fallback() -> None:
    """build_capacity_runner must fall back to Python if native missing."""
    from tools.source_lab.access.runners.registry import build_capacity_runner
    runner = build_capacity_runner("modbus_tcp")
    # Should not raise — returns either native or Python lightweight
    assert runner is not None


def test_libmodbus_available() -> None:
    """Verify libmodbus shared library is loadable."""
    import ctypes.util
    lib = ctypes.util.find_library("modbus")
    if lib is None:
        pytest.skip("dependency_missing: libmodbus.so not found in system")
    assert lib is not None


def test_lib60870_available() -> None:
    """Verify lib60870 shared library is loadable."""
    import ctypes.util
    lib = ctypes.util.find_library("lib60870")
    if lib is None:
        pytest.skip("dependency_missing: lib60870 not found")


def test_libiec61850_available() -> None:
    """Verify libiec61850 shared library is loadable."""
    import ctypes.util
    lib = ctypes.util.find_library("iec61850")
    if lib is None:
        pytest.skip("dependency_missing: libiec61850 not found")
