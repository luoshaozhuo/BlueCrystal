"""Unit tests for IEC 104 source acquisition adapter."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from whale.ingest.adapters.source.iec104_source_acquisition_adapter import (
    Iec104SourceAcquisitionAdapter,
)
from whale.ingest.ports.source.source_acquisition_port import (
    SourceBatchMismatchError,
    SourceReadError,
    SourceSubscriptionUnsupportedError,
)
from whale.ingest.usecases.dtos.acquired_node_state import AcquiredNodeStateBatch
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.iec104.backends import RawIec104ReadResult


class TestIec104AcquisitionAdapterDTO:
    """Test IEC 104 acquisition adapter DTO mapping."""

    def test_supports_subscription_returns_false(self) -> None:
        adapter = Iec104SourceAcquisitionAdapter()
        assert adapter.supports_subscription(
            execution=AcquisitionExecutionOptions(
                protocol="iec104", transport="tcp", acquisition_mode="polling",
                interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
            ),
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
        ) is False

    def test_start_subscription_raises(self) -> None:
        adapter = Iec104SourceAcquisitionAdapter()
        async def _do_start() -> None:
            await adapter.start_subscription(
                execution=AcquisitionExecutionOptions(
                    protocol="iec104", transport="tcp", acquisition_mode="polling",
                    interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
                ),
                connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
                items=[],
                state_received=lambda _batch: None,
            )

        with pytest.raises(SourceSubscriptionUnsupportedError):
            asyncio.run(_do_start())

    def test_resolve_ioa_list_from_items(self) -> None:
        items = [
            AcquisitionItemData(key="sp1", profile_item_id=1, relative_path="101"),
            AcquisitionItemData(key="sp2", profile_item_id=2, relative_path="102"),
        ]
        result = Iec104SourceAcquisitionAdapter._resolve_ioa_list(
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
            items=items,
        )
        assert result == [101, 102]

    def test_resolve_ioa_invalid_path_raises(self) -> None:
        items = [
            AcquisitionItemData(key="bad", profile_item_id=99, relative_path="not_a_number"),
        ]
        with pytest.raises(ValueError, match="Cannot resolve IEC 104 IOA"):
            Iec104SourceAcquisitionAdapter._resolve_ioa_list(
                connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
                items=items,
            )

    def test_to_acquired_batch_with_valid_data(self) -> None:
        items = [
            AcquisitionItemData(key="sp1", relative_path="101", profile_item_id="p1"),
        ]
        raw = RawIec104ReadResult(
            ok=True,
            values={101: ("SP", "1")},
            response_timestamp=datetime.now(tz=timezone.utc),
        )
        batch = Iec104SourceAcquisitionAdapter._to_acquired_batch_from_raw(
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="IED001", ld_name="iec104_test", namespace_uri=""),
            items=items,
            ioa_list=[101],
            raw=raw,
            client_received_at=datetime.now(tz=timezone.utc),
            client_processed_at=datetime.now(tz=timezone.utc),
        )
        assert isinstance(batch, AcquiredNodeStateBatch)
        assert batch.source_id == "iec104_test"
        assert len(batch.values) == 1
        assert batch.values[0].node_key == "sp1"
        assert batch.values[0].value == "1"

    def test_to_acquired_batch_with_unmatched_ioa(self) -> None:
        """IOA not in response should produce UNKNOWN quality."""
        items = [
            AcquisitionItemData(key="sp1", profile_item_id=1, relative_path="999"),
        ]
        raw = RawIec104ReadResult(
            ok=True,
            values={},
            response_timestamp=datetime.now(tz=timezone.utc),
        )
        batch = Iec104SourceAcquisitionAdapter._to_acquired_batch_from_raw(
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="test", namespace_uri=""),
            items=items,
            ioa_list=[999],
            raw=raw,
            client_received_at=datetime.now(tz=timezone.utc),
            client_processed_at=datetime.now(tz=timezone.utc),
        )
        assert batch.values[0].quality == "UNKNOWN"
        assert "ioa_not_found_in_response" in batch.values[0].attributes.get("warning", "")

    def test_to_acquired_batch_with_failed_raw(self) -> None:
        items = [AcquisitionItemData(key="sp1", profile_item_id=1, relative_path="101")]
        raw = RawIec104ReadResult(ok=False, values={}, error_reason="timeout")
        with pytest.raises(SourceReadError, match="raw read failed"):
            Iec104SourceAcquisitionAdapter._to_acquired_batch_from_raw(
                connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="test", namespace_uri=""),
                items=items,
                ioa_list=[101],
                raw=raw,
                client_received_at=datetime.now(tz=timezone.utc),
                client_processed_at=datetime.now(tz=timezone.utc),
            )

    def test_build_reader_validates_host(self) -> None:
        with pytest.raises(ValueError, match="connection.host is required"):
            Iec104SourceAcquisitionAdapter._build_reader(
                execution=AcquisitionExecutionOptions(
                    protocol="iec104", transport="tcp", acquisition_mode="polling",
                    interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
                ),
                connection=SourceConnectionData(host="", port=2404, ied_name="", ld_name="", namespace_uri=""),
            )

    def test_build_reader_validates_port(self) -> None:
        with pytest.raises(ValueError, match="connection.port must be > 0"):
            Iec104SourceAcquisitionAdapter._build_reader(
                execution=AcquisitionExecutionOptions(
                    protocol="iec104", transport="tcp", acquisition_mode="polling",
                    interval_ms=100, max_iteration=1, request_timeout_ms=10_000,
                    freshness_timeout_ms=30_000, alive_timeout_ms=60_000,
                ),
                connection=SourceConnectionData(host="127.0.0.1", port=0, ied_name="", ld_name="", namespace_uri=""),
            )
