"""Iec61850MmsSourceAcquisitionAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。
"""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from whale.ingest.adapters.source.iec61850_source_acquisition_adapter import (
    Iec61850MmsSourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceBatchMismatchError,
    SourceReadError,
    SourceReadTimeoutError,
    SourceSubscriptionUnsupportedError,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec61850.backends import RawMmsReadResult


class _MockIec61850Reader:
    """模拟 Iec61850MmsSourceReader，绕过子进程调用。"""

    def __init__(self, results: list[RawMmsReadResult] | None = None, *, error: Exception | None = None) -> None:
        self._results = results or []
        self._error = error
        self.read_calls: list[tuple[str, str, str]] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockIec61850Reader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    async def read(self, obj_ref: str, fc: str = "NONE", *, request_id: str = "") -> RawMmsReadResult:
        self.read_calls.append((obj_ref, fc, request_id))
        if self._error is not None:
            raise self._error
        if self._results:
            return self._results.pop(0)
        return RawMmsReadResult(
            ok=True, obj_ref=obj_ref, value_type="BOOLEAN", value="true",
        )


class TestIec61850MmsSourceAcquisitionAdapter:
    """Iec61850MmsSourceAcquisitionAdapter 行为测试。"""

    def setup_method(self) -> None:
        self._adapter = Iec61850MmsSourceAcquisitionAdapter()

    def _make_execution(self) -> AcquisitionExecutionOptions:
        return AcquisitionExecutionOptions(
            protocol="iec61850_mms",
            transport="tcp",
            acquisition_mode="READ_ONCE",
            interval_ms=1000,
            max_iteration=1,
            request_timeout_ms=5000,
            freshness_timeout_ms=30_000,
            alive_timeout_ms=60_000,
        )

    def _make_connection(self, *, fc: str | None = None) -> SourceConnectionData:
        params: dict[str, object] = {}
        if fc is not None:
            params["fc"] = fc
        return SourceConnectionData(
            host="127.0.0.1",
            port=1102,
            ied_name="IED1",
            ld_name="LD1",
            namespace_uri="",
            params=params,
        )

    def _make_items(self) -> list[AcquisitionItemData]:
        return [
            AcquisitionItemData(key="ind1", profile_item_id=1, relative_path="Simulator/GGIO1.Ind1.stVal"),
            AcquisitionItemData(key="ind2", profile_item_id=2, relative_path="Simulator/GGIO1.Ind2.stVal"),
        ]

    def test_read_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """read 应成功返回 AcquiredNodeStateBatch。"""
        mock_reader = _MockIec61850Reader([
            RawMmsReadResult(ok=True, obj_ref="Simulator/GGIO1.Ind1.stVal", value_type="BOOLEAN", value="true"),
            RawMmsReadResult(ok=True, obj_ref="Simulator/GGIO1.Ind2.stVal", value_type="BOOLEAN", value="false"),
        ])
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            result = await self._adapter.read(
                execution=self._make_execution(),
                connection=self._make_connection(),
                items=self._make_items(),
            )
            assert result.availability_status == "VALID"
            assert len(result.values) == 2
            assert result.values[0].node_key == "ind1"
            assert result.values[0].value == "true"
            assert result.values[0].attributes.get("mms_value_type") == "BOOLEAN"
            assert result.values[1].node_key == "ind2"
            assert result.values[1].value == "false"
            assert mock_reader.entered is True
            assert mock_reader.exited is True
            assert len(mock_reader.read_calls) == 2
        asyncio.run(_run())

    def test_read_resolves_fc_from_connection_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """fc 应从 connection.params 获取。"""
        mock_reader = _MockIec61850Reader([
            RawMmsReadResult(ok=True, obj_ref="Simulator/GGIO1.SPCtrl1.setVal", value_type="BOOLEAN", value="true"),
        ])
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            await self._adapter.read(
                execution=self._make_execution(),
                connection=self._make_connection(fc="SP"),
                items=[AcquisitionItemData(key="sp1", profile_item_id=1, relative_path="Simulator/GGIO1.SPCtrl1.setVal")],
            )
            assert len(mock_reader.read_calls) == 1
            assert mock_reader.read_calls[0][1] == "SP"  # fc param
        asyncio.run(_run())

    def test_read_raw_failure_raises_source_read_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """raw result 失败应抛出 SourceReadError。"""
        mock_reader = _MockIec61850Reader([
            RawMmsReadResult(ok=False, obj_ref="Simulator/GGIO1.Ind1.stVal", value_type=None, value=None, error_reason="access-denied"),
        ])
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            with pytest.raises(SourceReadError, match="access-denied"):
                await self._adapter.read(
                    execution=self._make_execution(),
                    connection=self._make_connection(),
                    items=self._make_items()[:1],
                )
        asyncio.run(_run())

    def test_read_timeout_raises_source_read_timeout_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """TimeoutError 应转换为 SourceReadTimeoutError。"""
        mock_reader = _MockIec61850Reader(error=asyncio.TimeoutError())
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            with pytest.raises(SourceReadTimeoutError, match="timed out"):
                await self._adapter.read(
                    execution=self._make_execution(),
                    connection=self._make_connection(),
                    items=self._make_items()[:1],
                )
        asyncio.run(_run())

    def test_runner_not_available_raises_source_read_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """FileNotFoundError 应转换为 SourceReadError。"""
        mock_reader = _MockIec61850Reader(error=FileNotFoundError("runner not found"))
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        async def _run():
            with pytest.raises(SourceReadError, match="runner_not_available"):
                await self._adapter.read(
                    execution=self._make_execution(),
                    connection=self._make_connection(),
                    items=self._make_items()[:1],
                )
        asyncio.run(_run())

    def test_value_count_mismatch_raises_source_batch_mismatch_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """value 数量与 item 数量不匹配应抛出 SourceBatchMismatchError。"""
        mock_reader = _MockIec61850Reader([
            RawMmsReadResult(ok=True, obj_ref="Simulator/GGIO1.Ind1.stVal", value_type="BOOLEAN", value="true"),
        ])
        monkeypatch.setattr(
            "whale.ingest.adapters.source.iec61850_source_acquisition_adapter.Iec61850MmsSourceReader",
            lambda host, port, timeout_seconds: mock_reader,
        )

        # 直接测试 _to_acquired_batch_from_raw 的校验
        with pytest.raises(SourceBatchMismatchError, match="does not match item count"):
            Iec61850MmsSourceAcquisitionAdapter._to_acquired_batch_from_raw(
                connection=self._make_connection(),
                items=self._make_items(),
                addresses=["a", "b"],
                raw_results=[
                    RawMmsReadResult(ok=True, obj_ref="a", value_type="BOOLEAN", value="true"),
                ],
                client_received_at=datetime.now(tz=UTC),
                client_processed_at=datetime.now(tz=UTC),
            )

    def test_supports_subscription_returns_false(self) -> None:
        """IEC61850 MMS adapter 不应支持订阅。"""
        assert self._adapter.supports_subscription(
            self._make_execution(),
            self._make_connection(),
        ) is False

    def test_start_subscription_raises_unsupported_error(self) -> None:
        """start_subscription 应抛出 SourceSubscriptionUnsupportedError。"""
        with pytest.raises(
            SourceSubscriptionUnsupportedError,
            match="subscription acquisition is not supported",
        ):
            asyncio.run(
                self._adapter.start_subscription(
                    self._make_execution(),
                    self._make_connection(),
                    self._make_items(),
                    state_received=lambda batch: asyncio.sleep(0),
                )
            )

    def test_empty_obj_ref_raises_value_error(self) -> None:
        """空的 relative_path 应抛出 ValueError。"""
        with pytest.raises(ValueError, match="Empty relative_path"):
            Iec61850MmsSourceAcquisitionAdapter._resolve_obj_refs(
                self._make_connection(),
                [AcquisitionItemData(key="bad", profile_item_id=1, relative_path="")],
            )

    def test_empty_items_raises_value_error(self) -> None:
        """空 items 应抛出 ValueError。"""
        with pytest.raises(ValueError, match="Cannot resolve MMS object references"):
            Iec61850MmsSourceAcquisitionAdapter._resolve_obj_refs(
                self._make_connection(),
                [],
            )
