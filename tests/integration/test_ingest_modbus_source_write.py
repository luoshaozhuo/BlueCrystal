"""Integration test for Modbus TCP source write via SourceCommandUseCase.

测试步骤：
1. 启动 Modbus TCP simulator (Python lightweight)。
2. 通过 SourceCommandUseCase 写入某个可写寄存器。
3. 再通过 ModbusSourceAcquisitionAdapter 读取，验证值已变化。
4. dry_run 模式验证值不变化。
5. write disabled 模式验证真实写被拒绝。

依赖：
- modbus_tcp_polling_runner 编译可用。
- 不需要外部 Redis 或 Kafka。
"""
from __future__ import annotations

import asyncio
import os
import socket
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import pytest

# import_source_lab_module 已移除，source_lab 目录已物理删除
from whale.ingest.adapters.source.modbus_source_acquisition_adapter import (
    ModbusSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.modbus_source_write_adapter import (
    ModbusSourceWriteAdapter,
)
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)
from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
pytestmark = pytest.mark.skip(reason="source_lab 已删除，需迁移到 Starfish facade 或 standalone simulator")


def _resolve_dev_runner_path() -> Path | None:
    build_dir = Path(__file__).resolve().parents[2] / "tools" / "source_lab" / "native" / "build"
    for candidate in (
        build_dir / "modbus_tcp_polling_runner",
        build_dir / "modbus_tcp_polling_runner.exe",
    ):
        if candidate.exists():
            return candidate.resolve()
    return None


def _require_runner() -> Path:
    runner_path = _resolve_dev_runner_path()
    if runner_path is None:
        pytest.skip("modbus TCP runner executable does not exist")
    return runner_path


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _build_source(port: int) -> SimulatedSource:
    """Build a test source with register addresses matching point keys."""
    return SimulatedSource(
        connection=SourceConnection(
            name="write_test_source",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="modbus_tcp",
        ),
        points=(
            SimulatedPoint(ln_name="", do_name="0", unit="", data_type="UINT16", initial_value=12),
            SimulatedPoint(ln_name="", do_name="1", unit="", data_type="UINT16", initial_value=34),
        ),
    )


@pytest.mark.integration
def test_modbus_write_then_read_verify_value_changed() -> None:
    """写入后通过读取验证值已变化。"""
    runner_path = _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    write_port = ModbusSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"modbus_tcp": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"
    os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"] = str(runner_path)

    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
        params={"modbus_unit_id": 1},
    )

    try:
        with ModbusTcpSimulator(source):
            # Read baseline
            read_adapter = ModbusSourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="pre-write-read",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="modbus_tcp",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection_data],
                items=[
                    AcquisitionItemData(
                        key=point.key,
                        profile_item_id=idx + 1,
                        relative_path=str(idx),
                    )
                    for idx, point in enumerate(source.points)
                ],
            )

            async def _read() -> dict[str, str]:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=read_request.connections[0],
                    items=read_request.items,
                )
                return {v.node_key: v.value for v in result.values}

            initial_values = asyncio.run(_read())
            assert initial_values.get("0") == "12"
            assert initial_values.get("1") == "34"

            # Execute write (register 0 → 99)
            write_request = SourceWriteRequest(
                request_id="write-test-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="modbus_tcp",
                    transport="tcp",
                    request_timeout_ms=10_000,
                    dry_run=False,
                    actor="test",
                ),
                connections=[connection_data],
                items=[
                    SourceWriteItemData(
                        key="reg0",
                        node_id="0",
                        value_type="uint16",
                        value="99",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, f"Write failed: {write_result.results}"

            # Read again to verify change
            final_values = asyncio.run(_read())
            assert final_values.get("0") == "99", (
                f"Expected register 0 to be 99 after write, got {final_values.get('0')}"
            )
            # register 1 should remain unchanged
            assert final_values.get("1") == "34", (
                f"Expected register 1 to remain 34, got {final_values.get('1')}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]
        if "WHALE_MODBUS_CLIENT_RUNNER_PATH" in os.environ:
            del os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"]


@pytest.mark.integration
def test_modbus_write_dry_run_does_not_change_value() -> None:
    """dry_run 模式不应改变实际值。"""
    runner_path = _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    write_port = ModbusSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"modbus_tcp": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)
    os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"] = str(runner_path)

    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
        params={"modbus_unit_id": 1},
    )

    try:
        with ModbusTcpSimulator(source):
            read_adapter = ModbusSourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="dry-run-baseline",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="modbus_tcp",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection_data],
                items=[
                    AcquisitionItemData(
                        key=point.key,
                        profile_item_id=idx + 1,
                        relative_path=str(idx),
                    )
                    for idx, point in enumerate(source.points)
                ],
            )

            async def _read() -> dict[str, str]:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=read_request.connections[0],
                    items=read_request.items,
                )
                return {v.node_key: v.value for v in result.values}

            initial_values = asyncio.run(_read())

            # dry_run write
            dry_run_request = SourceWriteRequest(
                request_id="dry-run-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="modbus_tcp",
                    transport="tcp",
                    request_timeout_ms=10_000,
                    dry_run=True,
                    actor="test",
                ),
                connections=[connection_data],
                items=[
                    SourceWriteItemData(
                        key="reg0",
                        node_id="0",
                        value_type="uint16",
                        value="99",
                    ),
                ],
            )

            result = asyncio.run(use_case.execute(dry_run_request))
            assert result.dry_run is True
            assert result.success_count == 0

            # Value should be unchanged
            final_values = asyncio.run(_read())
            assert final_values == initial_values, (
                f"dry_run should not change value. Before: {initial_values}, After: {final_values}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]
        if "WHALE_MODBUS_CLIENT_RUNNER_PATH" in os.environ:
            del os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"]


@pytest.mark.integration
def test_modbus_write_disabled_refuses_real_write() -> None:
    """未启用写入时，真实写请求应被拒绝。"""
    runner_path = _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    write_port = ModbusSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"modbus_tcp": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)
    os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"] = str(runner_path)

    if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
        del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]

    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
        params={"modbus_unit_id": 1},
    )

    write_request = SourceWriteRequest(
        request_id="write-disabled-test",
        task_id=1,
        execution=SourceWriteExecutionOptions(
            protocol="modbus_tcp",
            transport="tcp",
            request_timeout_ms=5_000,
            dry_run=False,
        ),
        connections=[connection_data],
        items=[
            SourceWriteItemData(
                key="reg0",
                node_id="0",
                value_type="uint16",
                value="99",
            ),
        ],
    )

    try:
        with pytest.raises(RuntimeError, match="Real device write is disabled"):
            asyncio.run(use_case.execute(write_request))
    finally:
        if "WHALE_MODBUS_CLIENT_RUNNER_PATH" in os.environ:
            del os.environ["WHALE_MODBUS_CLIENT_RUNNER_PATH"]
