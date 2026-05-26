"""Iec61850MmsSourceWriteAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。
"""
from __future__ import annotations

import asyncio

from whale.ingest.adapters.source.iec61850_source_write_adapter import (
    Iec61850MmsSourceWriteAdapter,
)
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec61850.backends import RawWriteItemResult


class _MockIec61850Reader:
    """模拟 Iec61850MmsSourceReader，绕过子进程调用。"""

    def __init__(self, *, fail_items: set[str] | None = None) -> None:
        self._fail_items = fail_items or set()
        self.write_calls: list[tuple[str, str, str, str, str]] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockIec61850Reader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def write(
        self,
        obj_ref: str,
        fc: str,
        value_type: str,
        value: str,
        *,
        request_id: str = "",
    ) -> RawWriteItemResult:
        self.write_calls.append((obj_ref, fc, value_type, value, request_id))
        ok = obj_ref not in self._fail_items
        return RawWriteItemResult(
            obj_ref=obj_ref,
            ok=ok,
            status_code="OK" if ok else "access-denied",
            error_message=None if ok else "mock_write_failed",
            value_type=value_type,
        )


class TestIec61850MmsSourceWriteAdapter:
    """Iec61850MmsSourceWriteAdapter 行为测试。"""

    def setup_method(self) -> None:
        self._adapter = Iec61850MmsSourceWriteAdapter()

    def _make_execution(self, *, dry_run: bool = False) -> SourceWriteExecutionOptions:
        return SourceWriteExecutionOptions(
            protocol="iec61850_mms",
            transport="tcp",
            request_timeout_ms=5000,
            dry_run=dry_run,
        )

    def _make_connection(self) -> SourceConnectionData:
        return SourceConnectionData(
            host="127.0.0.1",
            port=1102,
            ied_name="IED1",
            ld_name="LD1",
            namespace_uri="",
        )

    def _make_items(self) -> list[SourceWriteItemData]:
        return [
            SourceWriteItemData(key="sp1", node_id="Simulator/GGIO1.SPCtrl1.setVal", value_type="BOOLEAN", value="true"),
            SourceWriteItemData(key="sp2", node_id="Simulator/GGIO1.SPCtrl2.setVal", value_type="INT32", value="42"),
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
        mock_reader = _MockIec61850Reader()
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_write_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
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
            # 验证写入参数
            assert mock_reader.write_calls[0][0] == "Simulator/GGIO1.SPCtrl1.setVal"
            assert mock_reader.write_calls[0][2] == "BOOLEAN"
            assert mock_reader.write_calls[0][3] == "true"
            assert mock_reader.write_calls[1][0] == "Simulator/GGIO1.SPCtrl2.setVal"
            assert mock_reader.write_calls[1][2] == "INT32"
            assert mock_reader.write_calls[1][3] == "42"
        asyncio.run(_run())

    def test_write_partial_failure(self, monkeypatch) -> None:
        """部分写入失败应正确统计。"""
        mock_reader = _MockIec61850Reader(fail_items={"Simulator/GGIO1.SPCtrl2.setVal"})
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_write_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
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
            assert result.results[1].status_code == "access-denied"
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
            "whale.ingest.adapters.source.iec61850_source_write_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: _FailingReader(),
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

    def test_invalid_connection_returns_error(self) -> None:
        """无效连接参数应返回错误结果而非崩溃。"""
        bad_connection = SourceConnectionData(
            host="", port=0, ied_name="", ld_name="", namespace_uri="",
        )

        async def _run():
            result = await self._adapter.write(
                execution=self._make_execution(),
                connection=bad_connection,
                items=self._make_items(),
            )
            assert result.success_count == 0
            assert result.failure_count == 2
            for item_result in result.results:
                assert item_result.status_code == "connection_invalid"
        asyncio.run(_run())
