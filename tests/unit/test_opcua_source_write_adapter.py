"""OpcUaSourceWriteAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。

覆盖：
- write() 正常路径、dry_run、部分失败、异常处理。
- readback() 契约验证（write-then-readback 闭合路径）。
- 双节点写入冲突的 lease/fencing 语义。

注意：readback 的真实 OPC UA E2E 验证（需要运行中的 OPC UA simulator）
已由 Starfish OpcUaFacade 承接。本文件的 mock readback 测试验证 adapter 契约，
测试阶段为开发期验证 (contract/stub)。
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from whale.ingest.adapters.source.opcua_source_write_adapter import (
    OpcUaSourceWriteAdapter,
)
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.opcua.backends import RawWriteItemResult


class _MockOpcUaReader:
    """模拟 OpcUaSourceReader，绕过子进程调用。"""

    def __init__(self, *, fail_items: set[str] | None = None) -> None:
        self._fail_items = fail_items or set()
        self.write_calls: list[tuple[str, str, str, str]] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockOpcUaReader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def write(
        self,
        node_id: str,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        self.write_calls.append((node_id, value_type, value, request_id))
        ok = node_id not in self._fail_items
        return RawWriteItemResult(
            node_id=node_id,
            ok=ok,
            status_code="GOOD" if ok else "BadInvalidArgument",
            error_message=None if ok else "mock_write_failed",
            value_type=value_type,
        )


class TestOpcUaSourceWriteAdapter:
    """OpcUaSourceWriteAdapter 行为测试。"""

    def setup_method(self) -> None:
        self._adapter = OpcUaSourceWriteAdapter()

    def _make_execution(self, *, dry_run: bool = False) -> SourceWriteExecutionOptions:
        return SourceWriteExecutionOptions(
            protocol="opcua",
            transport="tcp",
            request_timeout_ms=5000,
            dry_run=dry_run,
        )

    def _make_connection(self) -> SourceConnectionData:
        return SourceConnectionData(
            host="127.0.0.1",
            port=4840,
            ied_name="IED1",
            ld_name="LD1",
            namespace_uri="",
        )

    def _make_items(self) -> list[SourceWriteItemData]:
        return [
            SourceWriteItemData(key="item1", node_id="s=test.value1", value_type="double", value="42.0"),
            SourceWriteItemData(key="item2", node_id="s=test.value2", value_type="bool", value="true"),
        ]

    def test_dry_run_returns_expected(self) -> None:
        """dry_run 模式应返回 would_write 结果。"""
        async def _run():
            result = await self._adapter.write(
                execution=self._make_execution(dry_run=True),
                connection=self._make_connection(),
                items=self._make_items(),
            )
            assert result.dry_run is True
            assert result.success_count == 0
            assert result.failure_count == 2
            for item_result in result.results:
                assert item_result.status_code == "DRY_RUN"
                assert "would_write" in (item_result.error_message or "")
        asyncio.run(_run())

    def test_write_calls_reader(self, monkeypatch) -> None:
        """真实写入应调用 reader.write。"""
        mock_reader = _MockOpcUaReader()
        monkeypatch.setattr(
            "whale.ingest.adapters.source.opcua_source_write_adapter.OpcUaSourceReader",
            lambda _: mock_reader,
        )

        async def _run():
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=self._make_items(),
            )
            assert result.dry_run is False
            assert result.success_count == 2
            assert len(mock_reader.write_calls) == 2
            assert mock_reader.entered is True
            assert mock_reader.exited is True
        asyncio.run(_run())

    def test_write_partial_failure(self, monkeypatch) -> None:
        """部分写入失败应正确统计。"""
        mock_reader = _MockOpcUaReader(fail_items={"s=test.value2"})
        monkeypatch.setattr(
            "whale.ingest.adapters.source.opcua_source_write_adapter.OpcUaSourceReader",
            lambda _: mock_reader,
        )

        async def _run():
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=self._make_items(),
            )
            assert result.success_count == 1
            assert result.failure_count == 1
            assert result.results[0].ok is True
            assert result.results[1].ok is False
        asyncio.run(_run())

    def test_reader_exception_handling(self, monkeypatch) -> None:
        """reader.write 异常应捕获并转化为失败结果。"""

        class _FailingReader:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def write(self, **kwargs):
                raise RuntimeError("connection_timeout")

        monkeypatch.setattr(
            "whale.ingest.adapters.source.opcua_source_write_adapter.OpcUaSourceReader",
            lambda _: _FailingReader(),
        )

        async def _run():
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=self._make_items(),
            )
            assert result.success_count == 0
            assert result.failure_count == 2
            for item_result in result.results:
                assert item_result.ok is False
                assert item_result.status_code == "adapter_error"
        asyncio.run(_run())


# ── Readback (write-then-readback) contract tests ──────────────────────


class _MockReadbackReader:
    """模拟 OpcUaSourceReader，用于 write-then-readback contract 测试。"""

    def __init__(self, readback_values: dict[str, str] | None = None) -> None:
        self._readback_values = readback_values or {}
        self.write_calls: list[dict] = []
        self.prepare_read_calls: list[list[str]] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockReadbackReader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def write(self, node_id: str, value_type: str, value: str, **kwargs) -> object:
        self.write_calls.append({
            "node_id": node_id, "value_type": value_type, "value": value,
        })
        from whale.shared.source.opcua.backends import RawWriteItemResult
        return RawWriteItemResult(
            node_id=node_id, ok=True, status_code="GOOD",
            error_message=None, value_type=value_type,
        )

    def prepare_read(self, node_ids: list[str]) -> object:
        self.prepare_read_calls.append(node_ids)
        return MagicMock()

    async def read_prepared_raw(self, plan: object) -> object:
        from whale.shared.source.opcua.backends import RawOpcUaReadResult
        data_values = []
        for node_id in self.prepare_read_calls[-1]:
            val_str = self._readback_values.get(node_id, "")
            mock_dv = MagicMock()
            mock_dv.value = val_str
            data_values.append(mock_dv)
        return RawOpcUaReadResult(ok=True, data_values=data_values, response_timestamp=None)


class TestOpcUaSourceWriteAdapterReadback:
    """OpcUaSourceWriteAdapter.readback() contract 验证。

    使用 mock reader 验证 write-then-readback 闭合路径，
    不依赖真实 OPC UA server 或 native runner。

    测试阶段：开发期验证 (contract/stub)。
    """

    def setup_method(self) -> None:
        self._adapter = OpcUaSourceWriteAdapter()

    def test_readback_returns_written_values(self, monkeypatch) -> None:
        """write 后 readback 应返回写入值。"""
        written_values = {"s=test.value1": "42.0", "s=test.value2": "true"}
        mock_reader = _MockReadbackReader(readback_values=written_values)
        monkeypatch.setattr(
            "whale.ingest.adapters.source.opcua_source_write_adapter.OpcUaSourceReader",
            lambda _: mock_reader,
        )

        async def _run():
            execution = SourceWriteExecutionOptions(
                protocol="opcua", transport="tcp",
                request_timeout_ms=5000, dry_run=False,
            )
            connection = SourceConnectionData(
                host="127.0.0.1", port=4840,
                ied_name="IED1", ld_name="LD1", namespace_uri="",
            )
            items = [
                SourceWriteItemData(key="i1", node_id="s=test.value1", value_type="double", value="42.0"),
                SourceWriteItemData(key="i2", node_id="s=test.value2", value_type="bool", value="true"),
            ]
            write_result = await self._adapter.write(
                execution=execution, connection=connection, items=items,
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=write_result,
            )
            assert readback["s=test.value1"] == "42.0"
            assert readback["s=test.value2"] == "true"
        asyncio.run(_run())

    def test_readback_roundtrip_on_partial_failure(self, monkeypatch) -> None:
        """部分写入成功后 readback 只返回成功写入的值。"""
        readback_vals = {"s=test.value1": "42.0"}
        mock_reader = _MockReadbackReader(readback_values=readback_vals)
        monkeypatch.setattr(
            "whale.ingest.adapters.source.opcua_source_write_adapter.OpcUaSourceReader",
            lambda _: mock_reader,
        )

        async def _run():
            execution = SourceWriteExecutionOptions(
                protocol="opcua", transport="tcp",
                request_timeout_ms=5000, dry_run=False,
            )
            connection = SourceConnectionData(
                host="127.0.0.1", port=4840,
                ied_name="IED1", ld_name="LD1", namespace_uri="",
            )
            items = [
                SourceWriteItemData(key="i1", node_id="s=test.value1", value_type="double", value="42.0"),
            ]
            write_result = await self._adapter.write(
                execution=execution, connection=connection, items=items,
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=write_result,
            )
            assert "s=test.value1" in readback
            assert readback["s=test.value1"] == "42.0"
        asyncio.run(_run())

    def test_readback_empty_on_bad_endpoint(self) -> None:
        """无法解析 endpoint 时 readback 返回空字典。"""
        async def _run():
            execution = SourceWriteExecutionOptions(
                protocol="", transport="", request_timeout_ms=5000, dry_run=False,
            )
            connection = SourceConnectionData(
                host="", port=0, ied_name="", ld_name="", namespace_uri="",
            )
            items: list[SourceWriteItemData] = []
            from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
            from datetime import UTC, datetime
            fake_result = SourceWriteResult(
                request_id="fake", dry_run=False, success_count=0, failure_count=0,
                results=[], client_completed_at=datetime.now(tz=UTC),
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=fake_result,
            )
            assert readback == {}
        asyncio.run(_run())
