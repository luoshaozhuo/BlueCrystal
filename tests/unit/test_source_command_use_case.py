"""SourceCommandUseCase 单元测试。"""

from __future__ import annotations

import asyncio
import os

from whale.ingest.usecases.source_command_use_case import SourceCommandUseCase
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
    SourceWriteRequest,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.ports.source.source_write_port import SourceWritePort
from whale.ingest.adapters.source.static_source_write_port_registry import (
    StaticSourceWritePortRegistry,
)


class _FakeWritePort(SourceWritePort):
    """记录最后一次调用参数的假写端口。"""

    def __init__(self) -> None:
        self.last_execution = None
        self.last_connection = None
        self.last_items = None

    async def write(self, execution, connection, items):
        self.last_execution = execution
        self.last_connection = connection
        self.last_items = items
        from whale.ingest.usecases.dtos.source_write_result import SourceWriteItemResult, SourceWriteResult
        from datetime import UTC, datetime
        item_results = [
            SourceWriteItemResult(key=item.key, node_id=item.node_id, ok=True, status_code="GOOD")
            for item in items
        ]
        return SourceWriteResult(
            request_id="fake_write",
            dry_run=False,
            success_count=len(item_results),
            failure_count=0,
            results=item_results,
            client_completed_at=datetime.now(tz=UTC),
        )


def _make_request(*, dry_run: bool = False, protocol: str = "opcua") -> SourceWriteRequest:
    return SourceWriteRequest(
        request_id="test-001",
        task_id=1,
        execution=SourceWriteExecutionOptions(
            protocol=protocol,
            transport="tcp",
            dry_run=dry_run,
            request_timeout_ms=5000,
        ),
        connections=[
            SourceConnectionData(
                host="127.0.0.1", port=4840,
                ied_name="IED1", ld_name="LD1",
                namespace_uri="",
            ),
        ],
        items=[
            SourceWriteItemData(key="item1", node_id="s=test.value", value_type="double", value="42.0"),
        ],
    )


class TestSourceCommandUseCase:
    """SourceCommandUseCase 行为测试。"""

    def setup_method(self) -> None:
        self._write_port = _FakeWritePort()
        self._registry = StaticSourceWritePortRegistry(
            ports_by_protocol={"opcua": self._write_port},
        )
        self._use_case = SourceCommandUseCase(write_port_registry=self._registry)
        self._saved_env = os.environ.get("WHALE_INGEST_SOURCE_WRITE_ENABLED")

    def teardown_method(self) -> None:
        if self._saved_env is not None:
            os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = self._saved_env
        elif "WHALE_INGEST_SOURCE_WRITE_ENABLED" in os.environ:
            del os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"]

    def _enable_write(self) -> None:
        os.environ["WHALE_INGEST_SOURCE_WRITE_ENABLED"] = "true"

    def test_dry_run_does_not_call_adapter(self) -> None:
        """dry_run 模式不应调用 write adapter。"""
        async def _run():
            request = _make_request(dry_run=True)
            result = await self._use_case.execute(request)
            assert result.dry_run is True
            assert result.success_count == 0
            assert result.failure_count == 1
            assert result.results[0].status_code == "DRY_RUN"
            assert self._write_port.last_execution is None  # adapter 未被调用
        asyncio.run(_run())

    def test_write_disabled_raises(self) -> None:
        """未启用真实写入时应拒绝。"""
        async def _run():
            request = _make_request(dry_run=False)
            try:
                await self._use_case.execute(request)
                assert False, "Expected RuntimeError"
            except RuntimeError as e:
                assert "Real device write is disabled" in str(e)
        asyncio.run(_run())

    def test_write_enabled_calls_adapter(self) -> None:
        """启用后应调用 write adapter。"""
        self._enable_write()
        async def _run():
            request = _make_request(dry_run=False)
            result = await self._use_case.execute(request)
            assert result.dry_run is False
            assert result.success_count == 1
            assert self._write_port.last_execution is not None
        asyncio.run(_run())

    def test_unknown_protocol_raises(self) -> None:
        """未知协议应抛出 ValueError。"""
        self._enable_write()
        async def _run():
            request = _make_request(dry_run=False, protocol="modbus_tcp")
            try:
                await self._use_case.execute(request)
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "Unsupported write protocol" in str(e)
        asyncio.run(_run())

    def test_validate_empty_request_id(self) -> None:
        """空的 request_id 应拒绝。"""
        async def _run():
            request = _make_request(dry_run=True)
            request.request_id = ""
            try:
                await self._use_case.execute(request)
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "request_id is required" in str(e)
        asyncio.run(_run())

    def test_validate_empty_protocol(self) -> None:
        """空的 protocol 应拒绝。"""
        async def _run():
            request = _make_request(dry_run=True)
            request.execution.protocol = ""
            try:
                await self._use_case.execute(request)
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "protocol is required" in str(e)
        asyncio.run(_run())

    def test_validate_empty_connections(self) -> None:
        """空的 connections 应拒绝。"""
        async def _run():
            request = _make_request(dry_run=True)
            request.connections = []
            try:
                await self._use_case.execute(request)
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "connections cannot be empty" in str(e)
        asyncio.run(_run())

    def test_validate_empty_items(self) -> None:
        """空的 items 应拒绝。"""
        async def _run():
            request = _make_request(dry_run=True)
            request.items = []
            try:
                await self._use_case.execute(request)
                assert False, "Expected ValueError"
            except ValueError as e:
                assert "items cannot be empty" in str(e)
        asyncio.run(_run())
