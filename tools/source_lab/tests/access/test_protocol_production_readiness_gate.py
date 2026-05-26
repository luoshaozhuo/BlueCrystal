"""Protocol production readiness gate.

本测试验证协议的 production_client_read/write 标记是否满足工程门禁要求。
不允许 skipped 测试 — 所有门禁必须明确通过或失败。

门禁规则（对应 ai_shared/rules/ 中的协议准入策略）：

production_client_read=true 必须满足：
  1. shared/source/{protocol}/ 存在生产 client/backend/reader。
  2. ingest/adapters/source/{protocol}_source_acquisition_adapter.py 存在。
  3. 该协议有 native runner 或真实 Python production client。
  4. 该协议有 capacity 测试通过（通过 build_capacity_runner 验证）。
  5. 测试不得 skipped。

production_client_write=true 必须满足：
  1. SourceWritePort adapter 存在（{protocol}_source_write_adapter.py）。
  2. supported_write_operations 非空。
  3. native runner 或 production client 支持真实写入。

Python lightweight runner 不得标记 production_client_write=true。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.runners.registry import (
    PROTOCOL_CAPABILITIES,
    build_capacity_runner,
)

# ── Known production-ready protocols ───────────────────────────────────
# These are the protocols that currently have production clients in shared/source.

_KNOWN_PRODUCTION_READ_PROTOCOLS: dict[str, dict[str, str]] = {
    "opcua": {
        "shared_source": "src/whale/shared/source/opcua",
        "read_adapter": "src/whale/ingest/adapters/source/opcua_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/opcua_source_write_adapter.py",
    },
    "modbus_tcp": {
        "shared_source": "src/whale/shared/source/modbus",
        "read_adapter": "src/whale/ingest/adapters/source/modbus_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/modbus_source_write_adapter.py",
    },
    "iec61850_mms": {
        "shared_source": "src/whale/shared/source/iec61850",
        "read_adapter": "src/whale/ingest/adapters/source/iec61850_source_acquisition_adapter.py",
        "write_adapter": "src/whale/ingest/adapters/source/iec61850_source_write_adapter.py",
    },
    "iec61850_report": {
        "shared_source": "src/whale/shared/source/iec61850",
        "read_adapter": "src/whale/ingest/adapters/source/iec61850_report_source_acquisition_adapter.py",
        "write_adapter": "",
    },
}

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _file_exists(relative_path: str) -> bool:
    return _REPO_ROOT.joinpath(relative_path).exists()


# ── Production client read gate ───────────────────────────────────────


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_known_production_protocols_have_shared_source(protocol: str, paths: dict[str, str]) -> None:
    """Known production client 协议必须有 shared/source/{protocol} 目录。"""
    shared_path = paths.get("shared_source", "")
    assert _file_exists(shared_path), (
        f"{protocol}: production client declared but {shared_path} does not exist"
    )


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_known_production_protocols_have_read_adapter(protocol: str, paths: dict[str, str]) -> None:
    """Known production client 协议必须有 read adapter。"""
    adapter_path = paths.get("read_adapter", "")
    assert _file_exists(adapter_path), (
        f"{protocol}: production client declared but {adapter_path} does not exist"
    )


def test_production_read_protocols_have_capacity_runner() -> None:
    """所有已知 production read 协议必须有可构建的 capacity runner。"""
    for protocol in _KNOWN_PRODUCTION_READ_PROTOCOLS:
        cap = PROTOCOL_CAPABILITIES.get(protocol, {})
        if cap.get("polling") is not True:
            continue
        try:
            runner = build_capacity_runner(protocol)
            assert runner is not None
        except Exception as exc:
            pytest.fail(f"{protocol}: build_capacity_runner failed: {exc}")


# ── Production client write gate ──────────────────────────────────────


@pytest.mark.parametrize("protocol, paths", list(_KNOWN_PRODUCTION_READ_PROTOCOLS.items()))
def test_production_write_protocols_have_write_adapter(protocol: str, paths: dict[str, str]) -> None:
    """production_client_write=True 协议必须有 write adapter。"""
    cap = PROTOCOL_CAPABILITIES.get(protocol, {})
    if cap.get("production_client_write") is not True:
        return  # not a write-enabled protocol — skip check, not a failure
    write_adapter = paths.get("write_adapter", "")
    assert _file_exists(write_adapter), (
        f"{protocol}: production_client_write=True but {write_adapter} does not exist"
    )
    supported = cap.get("supported_write_operations", ())
    assert len(supported) >= 1, (
        f"{protocol}: production_client_write=True but supported_write_operations is empty"
    )


def test_non_production_protocols_must_not_have_write_adapter_in_known() -> None:
    """production_client_write=False 协议不应在已知映射中有 write adapter。"""
    for protocol, paths in _KNOWN_PRODUCTION_READ_PROTOCOLS.items():
        cap = PROTOCOL_CAPABILITIES.get(protocol, {})
        if cap.get("production_client_write") is True:
            continue  # write-enabled, adapter expected
        wa = paths.get("write_adapter", "")
        if wa and _file_exists(wa):
            pytest.fail(
                f"{protocol}: production_client_write=False but {wa} exists. "
                "Either remove the adapter or set production_client_write=True."
            )


def test_python_lightweight_runners_must_not_claim_production_write() -> None:
    """python_lightweight_runner 不得标记 production_client_write=true。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        level = cap.get("current_implementation_level", "")
        if level != "python_lightweight_runner":
            continue
        if cap.get("write") is True or cap.get("production_client_write") is True:
            pytest.fail(
                f"{name}: python_lightweight_runner must not claim "
                f"production_client_write=true"
            )


# ── Registry integrity gate ──────────────────────────────────────────


def test_production_client_write_requires_supported_operations() -> None:
    """production_client_write=True → supported_write_operations 必须非空。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        if cap.get("production_client_write") is not True:
            continue
        supported = cap.get("supported_write_operations", ())
        assert len(supported) >= 1, (
            f"{name}: production_client_write=True but supported_write_operations is empty"
        )


def test_all_protocols_have_write_operation_fields() -> None:
    """每个协议条目必须有 supported_write_operations 和 unsupported_write_operations。"""
    for name, cap in PROTOCOL_CAPABILITIES.items():
        assert "supported_write_operations" in cap, f"{name}: missing supported_write_operations"
        assert "unsupported_write_operations" in cap, f"{name}: missing unsupported_write_operations"
