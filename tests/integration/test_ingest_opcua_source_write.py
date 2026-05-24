"""Integration test for OPC UA source write via SourceCommandUseCase.

测试步骤：
1. 启动 OPC UA simulator。
2. 通过 SourceCommandUseCase 写入某个可写节点。
3. 再通过 OpcUaSourceAcquisitionAdapter 读取，验证值已变化。
4. dry_run 模式验证值不变化。
5. write disabled 模式验证真实写被拒绝。

依赖：
- open62541_client_runner 和 simulator 编译可用。
- 不需要外部 Redis 或 Kafka。
"""

from __future__ import annotations

import asyncio
import os
import socket
from contextlib import closing
from datetime import UTC, datetime

import pytest

from tests.support.source_lab_runtime import import_source_lab_module
from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
)
from whale.ingest.adapters.source.opcua_source_write_adapter import (
    OpcUaSourceWriteAdapter,
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
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
    SourceAcquisitionRequest,
)

_MODEL_MODULE = import_source_lab_module("tools.source_lab.model")
_ADDRESS_SPACE_MODULE = import_source_lab_module("tools.source_lab.opcua.address_space")
_SIMULATOR_MODULE = import_source_lab_module("tools.source_lab.opcua.open62541_source_simulator")

SimulatedPoint = _MODEL_MODULE.SimulatedPoint
SimulatedSource = _MODEL_MODULE.SimulatedSource
SourceConnection = _MODEL_MODULE.SourceConnection
logical_path = _ADDRESS_SPACE_MODULE.logical_path
Open62541SourceSimulator = _SIMULATOR_MODULE.Open62541SourceSimulator
resolve_runner_path = _SIMULATOR_MODULE.resolve_runner_path


def _require_runner() -> None:
    if not resolve_runner_path().exists():
        pytest.skip("open62541 runner executable does not exist")


def _choose_available_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _build_source(port: int) -> SimulatedSource:
    return SimulatedSource(
        connection=SourceConnection(
            name="write_test_source",
            ied_name="IED001",
            ld_name="LD0",
            host="127.0.0.1",
            port=port,
            transport="tcp",
            protocol="opcua",
            namespace_uri="urn:whale:ingest:write:e2e",
        ),
        points=(
            SimulatedPoint(
                ln_name="WPPD1",
                do_name="TotW",
                unit="kW",
                data_type="FLOAT64",
                initial_value=12.5,
            ),
        ),
    )


def _get_node_id(source: SimulatedSource, point_key: str) -> str:
    """获取 OPC UA 节点的 browse path。"""
    for point in source.points:
        if point.key == point_key:
            path = logical_path(source.connection, point)
            # logical_path 返回 nsu=...;s=... 格式
            return path
    raise ValueError(f"Point {point_key} not found")


@pytest.mark.integration
def test_opcua_write_then_read_verify_value_changed() -> None:
    """写入后通过读取验证值已变化。"""
    _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    write_port = OpcUaSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"opcua": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)
    os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

    node_path = _get_node_id(source, "WPPD1.TotW")
    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
    )

    try:
        with Open62541SourceSimulator(source):
            # 先读取初始值确认 baseline
            read_adapter = OpcUaSourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="pre-write-read",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="opcua",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=5_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection_data],
                items=[
                    AcquisitionItemData(
                        key=point.key,
                        profile_item_id=idx + 1,
                        relative_path=logical_path(source.connection, point),
                    )
                    for idx, point in enumerate(source.points)
                ],
            )

            async def _read() -> str | None:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=read_request.connections[0],
                    items=read_request.items,
                )
                for value in result.values:
                    if value.node_key == "WPPD1.TotW":
                        return value.value
                return None

            initial_value = asyncio.run(_read())
            assert initial_value is not None
            assert float(initial_value) == 12.5 or initial_value == "12.5"

            # 执行写入（double 类型）
            write_request = SourceWriteRequest(
                request_id="write-test-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="opcua",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=False,
                    actor="test",
                ),
                connections=[connection_data],
                items=[
                    SourceWriteItemData(
                        key="WPPD1.TotW",
                        node_id=node_path,
                        value_type="double",
                        value="99.9",
                    ),
                ],
                client_requested_at=datetime.now(tz=UTC),
            )

            write_result = asyncio.run(use_case.execute(write_request))
            assert write_result.success_count == 1, (
                f"Write failed: {write_result.results}"
            )

            # 再次读取验证值已变化
            final_value = asyncio.run(_read())
            assert final_value is not None
            assert final_value is not None and float(final_value) == pytest.approx(99.9, abs=1e-6), (
                f"Expected ~99.9 after write, got {final_value}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]


@pytest.mark.integration
def test_opcua_write_dry_run_does_not_change_value() -> None:
    """dry_run 模式不应改变实际值。"""
    _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    node_path = _get_node_id(source, "WPPD1.TotW")
    write_port = OpcUaSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"opcua": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)

    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
    )

    try:
        with Open62541SourceSimulator(source):
            # 读取 baseline
            read_adapter = OpcUaSourceAcquisitionAdapter()
            read_request = SourceAcquisitionRequest(
                request_id="dry-run-baseline",
                task_id=1,
                execution=AcquisitionExecutionOptions(
                    protocol="opcua",
                    transport="tcp",
                    acquisition_mode="READ_ONCE",
                    interval_ms=100,
                    max_iteration=1,
                    request_timeout_ms=5_000,
                    freshness_timeout_ms=30_000,
                    alive_timeout_ms=60_000,
                ),
                connections=[connection_data],
                items=[
                    AcquisitionItemData(
                        key=point.key,
                        profile_item_id=idx + 1,
                        relative_path=logical_path(source.connection, point),
                    )
                    for idx, point in enumerate(source.points)
                ],
            )

            async def _read() -> str | None:
                result = await read_adapter.read(
                    execution=read_request.execution,
                    connection=read_request.connections[0],
                    items=read_request.items,
                )
                for value in result.values:
                    if value.node_key == "WPPD1.TotW":
                        return value.value
                return None

            initial_value = asyncio.run(_read())

            # dry_run 写入
            dry_run_request = SourceWriteRequest(
                request_id="dry-run-001",
                task_id=1,
                execution=SourceWriteExecutionOptions(
                    protocol="opcua",
                    transport="tcp",
                    request_timeout_ms=5_000,
                    dry_run=True,
                    actor="test",
                ),
                connections=[connection_data],
                items=[
                    SourceWriteItemData(
                        key="WPPD1.TotW",
                        node_id=node_path,
                        value_type="double",
                        value="99.9",
                    ),
                ],
            )

            result = asyncio.run(use_case.execute(dry_run_request))
            assert result.dry_run is True
            assert result.success_count == 0

            # 再次读取，值应不变
            final_value = asyncio.run(_read())
            assert final_value == initial_value, (
                f"dry_run should not change value. Before: {initial_value}, After: {final_value}"
            )
    finally:
        if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]


@pytest.mark.integration
def test_opcua_write_disabled_refuses_real_write() -> None:
    """未启用写入时，真实写请求应被拒绝。"""
    _require_runner()

    port = _choose_available_port()
    source = _build_source(port)
    write_port = OpcUaSourceWriteAdapter()
    registry = StaticSourceWritePortRegistry(ports_by_protocol={"opcua": write_port})
    use_case = SourceCommandUseCase(write_port_registry=registry)

    # 确保未设置启用标记
    if "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
        del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]

    connection_data = SourceConnectionData(
        host=source.connection.host,
        port=source.connection.port,
        ied_name=source.connection.ied_name,
        ld_name=source.connection.ld_name,
        namespace_uri=source.connection.namespace_uri or "",
    )

    write_request = SourceWriteRequest(
        request_id="write-disabled-test",
        task_id=1,
        execution=SourceWriteExecutionOptions(
            protocol="opcua",
            transport="tcp",
            request_timeout_ms=5_000,
            dry_run=False,
        ),
        connections=[connection_data],
        items=[
            SourceWriteItemData(
                key="WPPD1.TotW",
                node_id=f"s={source.points[0].do_name}",
                value_type="double",
                value="99.9",
            ),
        ],
    )

    with pytest.raises(RuntimeError, match="Real device write is disabled"):
        asyncio.run(use_case.execute(write_request))
