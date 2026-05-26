"""Tests for Iec61850ReportSourceAcquisitionAdapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest

from whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter import (
    Iec61850ReportSourceAcquisitionAdapter,
    _report_event_to_batch,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceReadError,
    SourceSubscriptionUnsupportedError,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec61850.backends.report_base import RawReportEvent


def _make_adapter() -> Iec61850ReportSourceAcquisitionAdapter:
    return Iec61850ReportSourceAcquisitionAdapter()


def _make_connection(**kwargs) -> SourceConnectionData:
    defaults = {
        "host": "127.0.0.1",
        "port": 1102,
        "ied_name": "Simulator",
        "ld_name": "Simulator",
        "namespace_uri": "",
        "params": {"rcb_ref": "EventsRCB01"},
    }
    defaults.update(kwargs)
    return SourceConnectionData(**defaults)


def _make_execution(**kwargs) -> AcquisitionExecutionOptions:
    defaults = {
        "protocol": "iec61850",
        "transport": "tcp",
        "acquisition_mode": "subscription",
        "interval_ms": 0,
        "max_iteration": None,
        "request_timeout_ms": 10000,
        "freshness_timeout_ms": 5000,
        "alive_timeout_ms": 15000,
        "subscription_start_interval_ms": 0,
        "params": {},
    }
    defaults.update(kwargs)
    return AcquisitionExecutionOptions(**defaults)


def _make_items(count: int = 3) -> list[AcquisitionItemData]:
    return [
        AcquisitionItemData(
            key=f"key_{i}",
            profile_item_id=i,
            relative_path=f"item_{i}",
        )
        for i in range(count)
    ]


class TestReportAdapterSupportsSubscription:
    def test_supports_subscription_returns_true(self) -> None:
        adapter = _make_adapter()
        assert adapter.supports_subscription(_make_execution(), _make_connection()) is True


class TestReportAdapterRead:
    @pytest.mark.asyncio
    async def test_read_returns_empty_batch(self) -> None:
        adapter = _make_adapter()
        batch = await adapter.read(_make_execution(), _make_connection(), _make_items())
        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.is_empty()

    @pytest.mark.asyncio
    async def test_read_batch_source_id_is_dash(self) -> None:
        adapter = _make_adapter()
        batch = await adapter.read(_make_execution(), _make_connection(), _make_items())
        assert batch.source_id == "-"


class TestReportAdapterStartSubscription:
    @pytest.mark.asyncio
    async def test_start_subscription_calls_reader_subscribe(self) -> None:
        adapter = _make_adapter()
        connection = _make_connection()
        execution = _make_execution()

        callbacks: list[AcquiredNodeStateBatch] = []

        async def on_batch(batch: AcquiredNodeStateBatch) -> None:
            callbacks.append(batch)

        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            # is_active returns True by default (subscription active)
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                execution, connection, _make_items(),
                state_received=on_batch,
            )
            assert handle is not None
            mock_reader.subscribe.assert_awaited_once()
            # Verify error_callback and reconnect args are passed
            _, kwargs = mock_reader.subscribe.await_args
            assert "error_callback" in kwargs
            assert kwargs.get("max_reconnect_attempts") == 1  # default from params
            await handle.close()
            mock_reader.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_subscription_invalid_connection(self) -> None:
        adapter = _make_adapter()
        connection = _make_connection(host="", port=0)

        with pytest.raises(Exception):
            await adapter.start_subscription(
                _make_execution(), connection, _make_items(),
                state_received=AsyncMock(),
            )

    @pytest.mark.asyncio
    async def test_start_subscription_runner_not_available(self) -> None:
        adapter = _make_adapter()
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            mock_reader.subscribe.side_effect = RuntimeError("executable does not exist")
            mock_reader_cls.return_value = mock_reader

            with pytest.raises(SourceReadError, match="runner_not_available"):
                await adapter.start_subscription(
                    _make_execution(), _make_connection(), _make_items(),
                    state_received=AsyncMock(),
                )

    @pytest.mark.asyncio
    async def test_handle_close_releases_resources(self) -> None:
        adapter = _make_adapter()
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                _make_execution(), _make_connection(), _make_items(),
                state_received=AsyncMock(),
            )
            await handle.close()
            mock_reader.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_handle_closed_property_active(self) -> None:
        """订阅正常时 handle.closed 返回 False。"""
        adapter = _make_adapter()
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                _make_execution(), _make_connection(), _make_items(),
                state_received=AsyncMock(),
            )
            assert not handle.closed
            assert handle.error is None
            await handle.close()

    @pytest.mark.asyncio
    async def test_handle_closed_after_close(self) -> None:
        """close() 后 handle.closed 返回 True。"""
        adapter = _make_adapter()
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                _make_execution(), _make_connection(), _make_items(),
                state_received=AsyncMock(),
            )
            await handle.close()
            assert handle.closed

    @pytest.mark.asyncio
    async def test_reconnect_config_from_execution_params(self) -> None:
        """execution.params 中的 max_reconnect_attempts 传递给 reader。"""
        adapter = _make_adapter()
        execution = _make_execution(params={"max_reconnect_attempts": 3})
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                execution, _make_connection(), _make_items(),
                state_received=AsyncMock(),
            )
            _, kwargs = mock_reader.subscribe.await_args
            assert kwargs.get("max_reconnect_attempts") == 3
            await handle.close()

    @pytest.mark.asyncio
    async def test_error_callback_passed_to_reader(self) -> None:
        """adapter 将 error_callback 传递给 reader。"""
        adapter = _make_adapter()
        with patch(
            "whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter.Iec61850ReportSourceReader",
        ) as mock_reader_cls:
            mock_reader = MagicMock(spec=["subscribe", "close"])
            mock_reader.subscribe = AsyncMock()
            mock_reader.close = AsyncMock()
            type(mock_reader).is_active = PropertyMock(return_value=True)
            mock_reader_cls.return_value = mock_reader

            handle = await adapter.start_subscription(
                _make_execution(), _make_connection(), _make_items(),
                state_received=AsyncMock(),
            )
            _, kwargs = mock_reader.subscribe.await_args
            assert "error_callback" in kwargs
            assert callable(kwargs["error_callback"])
            await handle.close()

    @pytest.mark.asyncio
    async def test_does_not_import_source_lab(self) -> None:
        """验证 adapter 源码不 import source_lab。"""
        import ast
        import inspect
        source = inspect.getsource(Iec61850ReportSourceAcquisitionAdapter)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import) and any(
                alias.name.startswith("tools.source_lab") for alias in node.names
            ):
                pytest.fail(f"adapter imports tools.source_lab: {node.names}")
            if isinstance(node, ast.ImportFrom) and (
                node.module or ""
            ).startswith("tools.source_lab"):
                pytest.fail(f"adapter imports tools.source_lab: {node.module}")


class TestReportEventToBatch:
    def test_report_event_maps_to_batch(self) -> None:
        connection = _make_connection()
        items = _make_items(3)
        event = RawReportEvent(
            ok=True,
            rcb_ref="Simulator/LLN0.RP.EventsRCB01",
            timestamp_ms=5000,
            seq_num=1,
            values=("true", "false", "42"),
        )

        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert not batch.is_empty()
        assert len(batch.values) == 3

        # Check value content
        assert batch.values[0].value == "true"
        assert batch.values[1].value == "false"
        assert batch.values[2].value == "42"

    def test_report_event_maps_attributes(self) -> None:
        connection = _make_connection()
        items = _make_items(1)
        event = RawReportEvent(
            ok=True,
            rcb_ref="Simulator/LLN0.RP.EventsRCB01",
            timestamp_ms=5000,
            seq_num=42,
            values=("true",),
        )

        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert batch.values[0].client_sequence == 42
        assert batch.values[0].attributes["rcb_ref"] == "Simulator/LLN0.RP.EventsRCB01"
        assert batch.values[0].attributes["seq_num"] == "42"

    def test_report_event_failed_returns_none(self) -> None:
        event = RawReportEvent(
            ok=False,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=0,
            values=(),
            error_reason="parse_error",
        )
        batch = _report_event_to_batch(
            connection=_make_connection(),
            items=_make_items(1),
            event=event,
        )
        assert batch is None

    def test_report_event_no_values_returns_none(self) -> None:
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=0,
            values=(),
        )
        batch = _report_event_to_batch(
            connection=_make_connection(),
            items=_make_items(1),
            event=event,
        )
        assert batch is None

    def test_report_event_fewer_values_than_items(self) -> None:
        connection = _make_connection()
        items = _make_items(5)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("v1", "v2", "v3"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 3  # Only maps available values

    def test_report_event_more_values_than_items(self) -> None:
        """values 数量多于 items 时截断多余 values。"""
        connection = _make_connection()
        items = _make_items(2)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("v1", "v2", "v3", "v4"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 2  # Truncated to items count

    def test_report_event_values_equal_items(self) -> None:
        """values 数量等于 items 数量时正常映射。"""
        connection = _make_connection()
        items = _make_items(3)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("a", "b", "c"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 3

    def test_report_event_single_value(self) -> None:
        """单个 value 也能正常映射。"""
        connection = _make_connection()
        items = _make_items(1)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("only_one",),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 1
        assert batch.values[0].value == "only_one"

    def test_report_event_mapping_quality_and_timestamp(self) -> None:
        """映射后的 quality/timestamp/node_key 稳定。"""
        connection = _make_connection()
        items = _make_items(2)
        event = RawReportEvent(
            ok=True,
            rcb_ref="Simulator/LLN0.RP.EventsRCB01",
            timestamp_ms=5000,
            seq_num=42,
            values=("val_a", "val_b"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert batch.values[0].node_key == "key_0"
        assert batch.values[0].quality == "GOOD"
        assert batch.values[0].client_sequence == 42
        assert batch.values[0].attributes["rcb_ref"] == "Simulator/LLN0.RP.EventsRCB01"
        assert batch.source_id == "Simulator"

    def test_report_event_mapping_values_less_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """values 少于 items 时 log warning。"""
        import logging
        caplog.set_level(logging.WARNING)
        connection = _make_connection()
        items = _make_items(5)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("v1", "v2"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 2
        assert any("report event has" in msg and "items requested" in msg for msg in caplog.messages), (
            f"expected warning about fewer values, got: {caplog.messages}"
        )

    def test_report_event_mapping_values_more_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """values 多于 items 时 log warning。"""
        import logging
        caplog.set_level(logging.WARNING)
        connection = _make_connection()
        items = _make_items(2)
        event = RawReportEvent(
            ok=True,
            rcb_ref="-",
            timestamp_ms=0,
            seq_num=1,
            values=("v1", "v2", "v3", "v4"),
        )
        batch = _report_event_to_batch(
            connection=connection,
            items=items,
            event=event,
        )
        assert batch is not None
        assert len(batch.values) == 2  # Truncated
        assert any("truncating" in msg for msg in caplog.messages), (
            f"expected warning about truncating, got: {caplog.messages}"
        )


class TestReportAdapterComposition:
    """Composition 注册验证。"""

    def test_report_adapter_resolvable_from_acquisition_registry(self) -> None:
        """composition 的 acquisition registry 能解析 iec61850_report。"""
        from whale.ingest.composition import build_source_write_composition

        comp = build_source_write_composition()
        reg = comp.acquisition_port_registry

        port = reg.get("iec61850_report")
        assert port is not None
        from whale.ingest.adapters.source.iec61850_report_source_acquisition_adapter import (
            Iec61850ReportSourceAcquisitionAdapter,
        )
        assert isinstance(port, Iec61850ReportSourceAcquisitionAdapter)

    def test_report_adapter_alias_resolves(self) -> None:
        """别名 iec61850report 也能解析。"""
        from whale.ingest.composition import build_source_write_composition

        comp = build_source_write_composition()
        reg = comp.acquisition_port_registry
        port = reg.get("iec61850report")
        assert port is not None

    def test_report_not_in_write_registry(self) -> None:
        """Report 不在 write registry 中。"""
        from whale.ingest.composition import build_source_write_composition

        comp = build_source_write_composition()
        write_reg = comp.write_port_registry
        with pytest.raises((KeyError, ValueError)):
            write_reg.get("iec61850_report")
