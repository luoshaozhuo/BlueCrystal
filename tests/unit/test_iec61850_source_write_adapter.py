"""Iec61850MmsSourceWriteAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。

覆盖：
- write() 正常路径、dry_run、部分失败、异常处理、无效连接。
- readback() 契约验证（write-then-readback 闭合路径）。

测试阶段：开发期验证 (contract/stub)。
真实 IEC 61850 MMS E2E readback 需要运行中的 IEC 61850 simulator。
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
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult
from whale.shared.source.iec61850.backends import RawMmsReadResult, RawWriteItemResult


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


# ── Readback (write-then-readback) contract tests ──────────────────────


class _MockIec61850ReadbackReader:
    """模拟 Iec61850MmsSourceReader，用于 write-then-readback contract 测试。

    同时实现 write 和 read 方法，支持完整的 write+readback 闭合路径。
    """

    def __init__(self, readback_values: dict[str, str] | None = None) -> None:
        self._readback_values = readback_values or {}
        self.write_calls: list[dict] = []
        self.read_calls: list[dict] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockIec61850ReadbackReader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def write(
        self, obj_ref: str, fc: str, value_type: str, value: str, *, request_id: str = "",
    ) -> RawWriteItemResult:
        self.write_calls.append({"obj_ref": obj_ref, "fc": fc, "value_type": value_type, "value": value})
        return RawWriteItemResult(
            obj_ref=obj_ref, ok=True, status_code="OK", error_message=None, value_type=value_type,
        )

    async def read(
        self, obj_ref: str, fc: str, *, request_id: str = "",
    ) -> RawMmsReadResult:
        self.read_calls.append({"obj_ref": obj_ref, "fc": fc})
        val = self._readback_values.get(obj_ref, "")
        return RawMmsReadResult(ok=True, obj_ref=obj_ref, value=val, value_type="STRING")


class TestIec61850MmsSourceWriteAdapterReadback:
    """Iec61850MmsSourceWriteAdapter.readback() contract 验证。

    使用 mock reader 验证 write-then-readback 闭合路径，
    不依赖真实 IEC 61850 MMS server 或 native runner。

    测试阶段：开发期验证 (contract/stub)。
    真实 IEC 61850 MMS E2E readback 需要运行中的 IEC 61850 simulator。
    """

    def setup_method(self) -> None:
        self._adapter = Iec61850MmsSourceWriteAdapter()

    def _make_execution(self, *, dry_run: bool = False) -> SourceWriteExecutionOptions:
        return SourceWriteExecutionOptions(
            protocol="iec61850_mms", transport="tcp",
            request_timeout_ms=5000, dry_run=dry_run,
        )

    def _make_connection(self) -> SourceConnectionData:
        return SourceConnectionData(
            host="127.0.0.1", port=1102,
            ied_name="IED1", ld_name="LD1", namespace_uri="",
        )

    def test_readback_returns_written_values(self, monkeypatch) -> None:
        """write 后 readback 应返回写入的 MMS 值。"""
        readback_vals = {
            "Simulator/GGIO1.SPCtrl1.setVal": "true",
            "Simulator/GGIO1.SPCtrl2.setVal": "42",
        }
        mock_reader = _MockIec61850ReadbackReader(readback_values=readback_vals)
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_write_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            execution = self._make_execution()
            connection = self._make_connection()
            items = [
                SourceWriteItemData(key="sp1", node_id="Simulator/GGIO1.SPCtrl1.setVal", value_type="BOOLEAN", value="true"),
                SourceWriteItemData(key="sp2", node_id="Simulator/GGIO1.SPCtrl2.setVal", value_type="INT32", value="42"),
            ]
            write_result = await self._adapter.write(
                execution=execution, connection=connection, items=items,
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=write_result,
            )
            assert readback["Simulator/GGIO1.SPCtrl1.setVal"] == "true"
            assert readback["Simulator/GGIO1.SPCtrl2.setVal"] == "42"
        asyncio.run(_run())

    def test_readback_empty_on_invalid_host(self) -> None:
        """无效 host/port 时 readback 返回空字典。"""
        async def _run():
            execution = self._make_execution()
            connection = SourceConnectionData(
                host="", port=0, ied_name="", ld_name="", namespace_uri="",
            )
            items = [
                SourceWriteItemData(key="sp1", node_id="Simulator/GGIO1.SPCtrl1.setVal", value_type="BOOLEAN", value="true"),
            ]
            fake_result = SourceWriteResult(
                request_id="fake", dry_run=False, success_count=0, failure_count=0,
                results=[],
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=fake_result,
            )
            assert readback == {}
        asyncio.run(_run())

    def test_readback_handles_read_failure_gracefully(self, monkeypatch) -> None:
        """单个点回读失败不影响其他点的回读。"""

        class _PartialReadReader:
            def __init__(self):
                self.entered = False
                self.exited = False

            async def __aenter__(self):
                self.entered = True
                return self

            async def __aexit__(self, *args):
                self.exited = True

            async def write(self, obj_ref, fc, value_type, value, *, request_id=""):
                return RawWriteItemResult(obj_ref=obj_ref, ok=True, status_code="OK", error_message=None, value_type=value_type)

            async def read(self, obj_ref, fc, *, request_id=""):
                if "SPCtrl2" in obj_ref:
                    raise RuntimeError("MMS read timeout")
                return RawMmsReadResult(ok=True, obj_ref=obj_ref, value="42", value_type="INT32")

        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_write_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: _PartialReadReader(),
        )

        async def _run():
            execution = self._make_execution()
            connection = self._make_connection()
            items = [
                SourceWriteItemData(key="sp1", node_id="Simulator/GGIO1.SPCtrl1.setVal", value_type="INT32", value="42"),
                SourceWriteItemData(key="sp2", node_id="Simulator/GGIO1.SPCtrl2.setVal", value_type="INT32", value="42"),
            ]
            write_result = await self._adapter.write(
                execution=execution, connection=connection, items=items,
            )
            readback = await self._adapter.readback(
                execution=execution, connection=connection,
                items=items, write_result=write_result,
            )
            # sp1 回读成功
            assert "Simulator/GGIO1.SPCtrl1.setVal" in readback
            # sp2 回读失败，不包含在结果中
            assert "Simulator/GGIO1.SPCtrl2.setVal" not in readback
        asyncio.run(_run())
