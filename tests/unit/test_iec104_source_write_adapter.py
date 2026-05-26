"""Unit tests for IEC 104 source write adapter."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from whale.ingest.adapters.source.iec104_source_write_adapter import (
    Iec104SourceWriteAdapter,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.ingest.usecases.dtos.source_write_request import (
    SourceWriteExecutionOptions,
    SourceWriteItemData,
)
from whale.ingest.usecases.dtos.source_write_result import SourceWriteResult


class TestIec104WriteAdapterDTO:
    """Test IEC 104 write adapter DTO mapping and dry_run."""

    @pytest.mark.asyncio
    async def test_dry_run_returns_no_writes(self) -> None:
        adapter = Iec104SourceWriteAdapter()
        result = await adapter.write(
            execution=SourceWriteExecutionOptions(
                protocol="iec104", transport="tcp", dry_run=True,
            ),
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
            items=[
                SourceWriteItemData(key="sp1", node_id="101", value_type="BOOL", value="1"),
            ],
        )
        assert result.dry_run is True
        assert result.success_count == 0
        for r in result.results:
            assert r.status_code == "DRY_RUN"

    @pytest.mark.asyncio
    async def test_dry_run_all_items(self) -> None:
        adapter = Iec104SourceWriteAdapter()
        result = await adapter.write(
            execution=SourceWriteExecutionOptions(
                protocol="iec104", transport="tcp", dry_run=True,
            ),
            connection=SourceConnectionData(host="127.0.0.1", port=2404, ied_name="", ld_name="", namespace_uri=""),
            items=[
                SourceWriteItemData(key="sp1", node_id="101", value_type="BOOL", value="1"),
                SourceWriteItemData(key="sp2", node_id="102", value_type="BOOL", value="0"),
            ],
        )
        assert result.dry_run is True
        assert len(result.results) == 2

    def test_resolve_ioa_valid(self) -> None:
        item = SourceWriteItemData(key="sp1", node_id="101", value_type="BOOL", value="1")
        assert Iec104SourceWriteAdapter._resolve_ioa(item) == 101

    def test_resolve_ioa_invalid(self) -> None:
        item = SourceWriteItemData(key="sp1", node_id="not_a_number", value_type="BOOL", value="1")
        assert Iec104SourceWriteAdapter._resolve_ioa(item) is None

    def test_resolve_command_type_bool(self) -> None:
        item = SourceWriteItemData(key="sp1", node_id="101", value_type="BOOL", value="1")
        assert Iec104SourceWriteAdapter._resolve_command_type(item) == "C_SC_NA_1"

    def test_resolve_command_type_float(self) -> None:
        item = SourceWriteItemData(key="mv1", node_id="1", value_type="FLOAT", value="42.5")
        assert Iec104SourceWriteAdapter._resolve_command_type(item) == "C_SE_NC_1"

    def test_resolve_command_type_explicit(self) -> None:
        item = SourceWriteItemData(key="cmd1", node_id="101", value_type="C_SC_NA_1", value="1")
        assert Iec104SourceWriteAdapter._resolve_command_type(item) == "C_SC_NA_1"

    def test_resolve_command_type_unknown(self) -> None:
        item = SourceWriteItemData(key="cmd1", node_id="101", value_type="UNKNOWN", value="1")
        assert Iec104SourceWriteAdapter._resolve_command_type(item) is None

    def test_host_resolution_failure(self) -> None:
        adapter = Iec104SourceWriteAdapter()
        ts = datetime.now(tz=timezone.utc)
        result = adapter._error_result(
            execution=SourceWriteExecutionOptions(protocol="iec104", transport="tcp"),
            items=[SourceWriteItemData(key="sp1", node_id="101", value_type="BOOL", value="1")],
            error_code="host_resolution_failed",
            error_message="connection.host is required",
            client_requested_at=ts,
        )
        assert isinstance(result, SourceWriteResult)
        assert result.success_count == 0
        assert result.failure_count == 1
