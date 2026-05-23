"""OPC UA source acquisition adapter 单元测试。

这些测试覆盖 open62541 raw reader 到 ingest batch 的转换边界。
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import pytest

from whale.ingest.adapters.source.opcua_source_acquisition_adapter import (
    OpcUaSourceAcquisitionAdapter,
    _build_endpoint,
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
from whale.shared.source.opcua.backends import RawDataValue, RawOpcUaReadResult


class FakeReader:
    """可注入的假 OPC UA reader。"""

    def __init__(self, raw: RawOpcUaReadResult | None = None, *, error: Exception | None = None) -> None:
        self.raw = raw
        self.error = error
        self.prepared_addresses: list[str] = []

    async def __aenter__(self) -> FakeReader:
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def prepare_read(self, addresses: list[str]) -> list[str]:
        self.prepared_addresses = list(addresses)
        return list(addresses)

    async def read_prepared_raw(self, plan: object) -> RawOpcUaReadResult:
        del plan
        if self.error is not None:
            raise self.error
        assert self.raw is not None
        return self.raw


def _build_execution() -> AcquisitionExecutionOptions:
    return AcquisitionExecutionOptions(
        protocol="opcua",
        transport="tcp",
        acquisition_mode="READ_ONCE",
        interval_ms=1000,
        max_iteration=1,
        request_timeout_ms=1500,
        freshness_timeout_ms=30_000,
        alive_timeout_ms=60_000,
    )


def _build_connection(*, namespace_uri: str = "urn:windfarm:2wtg") -> SourceConnectionData:
    return SourceConnectionData(
        host="127.0.0.1",
        port=4840,
        ied_name="IED_01",
        ld_name="LD_01",
        namespace_uri=namespace_uri,
    )


def _build_items() -> list[AcquisitionItemData]:
    return [
        AcquisitionItemData(
            key="TotW",
            profile_item_id=1,
            relative_path="WTG_001/MMXU1.TotW.mag.f",
        ),
        AcquisitionItemData(
            key="Custom",
            profile_item_id=2,
            relative_path="nsu=urn:custom;s=Custom.Node",
        ),
    ]


def test_read_prepared_raw_success_returns_acquired_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OpcUaSourceAcquisitionAdapter()
    response_timestamp = datetime(2026, 5, 22, 8, 0, tzinfo=UTC)
    fake_reader = FakeReader(
        RawOpcUaReadResult(
            ok=True,
            data_values=(
                RawDataValue(
                    value=123.4,
                    source_timestamp=datetime(2026, 5, 22, 7, 59, tzinfo=UTC),
                    server_timestamp=datetime(2026, 5, 22, 8, 0, tzinfo=UTC),
                    status_code="GOOD",
                ),
                RawDataValue(
                    value=True,
                    source_timestamp=None,
                    server_timestamp=None,
                    status_code=None,
                ),
            ),
            response_timestamp=response_timestamp,
        )
    )
    monkeypatch.setattr(
        OpcUaSourceAcquisitionAdapter,
        "_build_reader",
        classmethod(lambda cls, execution, connection: fake_reader),
    )

    batch = asyncio.run(adapter.read(_build_execution(), _build_connection(), _build_items()))

    assert fake_reader.prepared_addresses == [
        "nsu=urn:windfarm:2wtg;s=WTG_001/MMXU1.TotW.mag.f",
        "nsu=urn:custom;s=Custom.Node",
    ]
    assert batch.source_id == "LD_01"
    assert batch.batch_observed_at == response_timestamp
    assert batch.values[0].node_key == "TotW"
    assert batch.values[0].value == "123.4"
    assert batch.values[0].quality == "GOOD"
    assert batch.values[0].server_timestamp == datetime(2026, 5, 22, 8, 0, tzinfo=UTC)
    assert batch.values[0].attributes["relative_path"] == "WTG_001/MMXU1.TotW.mag.f"
    assert batch.values[1].node_key == "Custom"
    assert batch.values[1].value == "True"
    assert batch.values[1].quality == "GOOD"
    assert batch.values[1].server_timestamp == response_timestamp
    assert batch.values[1].attributes["protocol_address"] == "nsu=urn:custom;s=Custom.Node"


def test_build_endpoint_uses_opc_tcp_scheme() -> None:
    endpoint = _build_endpoint(_build_execution(), _build_connection())

    assert endpoint == "opc.tcp://127.0.0.1:4840"


def test_value_count_mismatch_raises_source_batch_mismatch_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = OpcUaSourceAcquisitionAdapter()
    fake_reader = FakeReader(
        RawOpcUaReadResult(
            ok=True,
            data_values=(RawDataValue(value=1),),
            response_timestamp=datetime.now(tz=UTC),
        )
    )
    monkeypatch.setattr(
        OpcUaSourceAcquisitionAdapter,
        "_build_reader",
        classmethod(lambda cls, execution, connection: fake_reader),
    )

    with pytest.raises(SourceBatchMismatchError, match="does not match item count"):
        asyncio.run(adapter.read(_build_execution(), _build_connection(), _build_items()))


def test_raw_error_raises_source_read_error(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OpcUaSourceAcquisitionAdapter()
    fake_reader = FakeReader(
        RawOpcUaReadResult(
            ok=False,
            data_values=(),
            response_timestamp=datetime.now(tz=UTC),
            error_reason="read_failed",
        )
    )
    monkeypatch.setattr(
        OpcUaSourceAcquisitionAdapter,
        "_build_reader",
        classmethod(lambda cls, execution, connection: fake_reader),
    )

    with pytest.raises(SourceReadError, match="read_failed"):
        asyncio.run(adapter.read(_build_execution(), _build_connection(), _build_items()))


def test_timeout_raises_source_read_timeout_error(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = OpcUaSourceAcquisitionAdapter()
    fake_reader = FakeReader(error=asyncio.TimeoutError())
    monkeypatch.setattr(
        OpcUaSourceAcquisitionAdapter,
        "_build_reader",
        classmethod(lambda cls, execution, connection: fake_reader),
    )

    with pytest.raises(SourceReadTimeoutError, match="timed out"):
        asyncio.run(adapter.read(_build_execution(), _build_connection(), _build_items()))


def test_start_subscription_raises_unsupported_error() -> None:
    adapter = OpcUaSourceAcquisitionAdapter()

    with pytest.raises(
        SourceSubscriptionUnsupportedError,
        match="subscription acquisition is not supported by current source reader",
    ):
        asyncio.run(
            adapter.start_subscription(
                _build_execution(),
                _build_connection(),
                _build_items(),
                state_received=lambda batch: asyncio.sleep(0),
            )
        )
