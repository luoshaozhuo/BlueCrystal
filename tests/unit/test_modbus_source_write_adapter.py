"""ModbusSourceWriteAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。
"""
from __future__ import annotations

import asyncio

from whale.ingest.adapters.source.modbus_source_write_adapter import (
    ModbusSourceWriteAdapter,
)
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.modbus.backends import RawWriteItemResult


class _MockModbusReader:
    """模拟 ModbusSourceReader，绕过子进程调用。"""

    def __init__(self, *, fail_addrs: set[int] | None = None) -> None:
        self._fail_addrs = fail_addrs or set()
        self.write_calls: list[tuple[int, str, str, str]] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockModbusReader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def write(
        self,
        reg_addr: int,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        self.write_calls.append((reg_addr, value_type, value, request_id))
        ok = reg_addr not in self._fail_addrs
        return RawWriteItemResult(
            reg_addr=reg_addr,
            ok=ok,
            status_code="OK" if ok else "BadInvalidArgument",
            error_message=None if ok else "mock_write_failed",
        )


class TestModbusSourceWriteAdapter:
    """ModbusSourceWriteAdapter 行为测试。"""

    def setup_method(self) -> None:
        self._adapter = ModbusSourceWriteAdapter()

    def _make_execution(self, *, dry_run: bool = False) -> SourceWriteExecutionOptions:
        return SourceWriteExecutionOptions(
            protocol="modbus_tcp",
            transport="tcp",
            request_timeout_ms=5000,
            dry_run=dry_run,
        )

    def _make_connection(self) -> SourceConnectionData:
        return SourceConnectionData(
            host="127.0.0.1",
            port=502,
            ied_name="IED1",
            ld_name="LD1",
            namespace_uri="",
        )

    def _make_items(self) -> list[SourceWriteItemData]:
        return [
            SourceWriteItemData(key="item1", node_id="0", value_type="uint16", value="42"),
            SourceWriteItemData(key="item2", node_id="1", value_type="uint16", value="100"),
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
        mock_reader = _MockModbusReader()
        monkeypatch.setattr(
            "whale.ingest.adapters.source.modbus_source_write_adapter.ModbusSourceReader",
            lambda **_: mock_reader,
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
        mock_reader = _MockModbusReader(fail_addrs={1})
        monkeypatch.setattr(
            "whale.ingest.adapters.source.modbus_source_write_adapter.ModbusSourceReader",
            lambda **_: mock_reader,
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
            "whale.ingest.adapters.source.modbus_source_write_adapter.ModbusSourceReader",
            lambda **_: _FailingReader(),
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

    def test_hex_node_id(self, monkeypatch) -> None:
        """0x 前缀的 node_id 应解析为十六进制寄存器地址。"""
        mock_reader = _MockModbusReader()
        monkeypatch.setattr(
            "whale.ingest.adapters.source.modbus_source_write_adapter.ModbusSourceReader",
            lambda **_: mock_reader,
        )

        async def _run():
            items = [
                SourceWriteItemData(key="hex_item", node_id="0x0A", value_type="uint16", value="255"),
            ]
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=items,
            )
            assert result.success_count == 1
            assert mock_reader.write_calls[0][0] == 10  # reg_addr = 10
        asyncio.run(_run())

    def test_invalid_node_id(self, monkeypatch) -> None:
        """无法解析的 node_id 应返回 adapter_error。"""
        mock_reader = _MockModbusReader()
        monkeypatch.setattr(
            "whale.ingest.adapters.source.modbus_source_write_adapter.ModbusSourceReader",
            lambda **_: mock_reader,
        )

        async def _run():
            items = [
                SourceWriteItemData(key="bad_item", node_id="not_a_number", value_type="uint16", value="42"),
            ]
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=items,
            )
            assert result.success_count == 0
            assert result.failure_count == 1
            assert "cannot parse" in (result.results[0].error_message or "").lower()
        asyncio.run(_run())
