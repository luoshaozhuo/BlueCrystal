"""ModbusSourceAcquisitionAdapter 单元测试。

使用 mock reader 绕过真实的 native runner 子进程。
"""
from __future__ import annotations

import asyncio

import pytest

from whale.ingest.adapters.source.modbus_source_acquisition_adapter import (
    ModbusSourceAcquisitionAdapter,
)
from whale.ingest.usecases.dtos.source_acquisition_request import (
    AcquisitionExecutionOptions,
    AcquisitionItemData,
)
from whale.ingest.usecases.dtos.source_connection_data import SourceConnectionData
from whale.shared.source.modbus.backends import RawModbusReadResult


class _MockModbusReader:
    """模拟 ModbusSourceReader。"""

    def __init__(self, values: list[int] | None = None) -> None:
        self._values = values or [42, 100]
        self.prepared: list[object] = []
        self.entered = False
        self.exited = False

    async def __aenter__(self) -> _MockModbusReader:
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.exited = True

    def prepare_read(self, reg_addrs):
        self.prepared.append(reg_addrs)
        return type("Plan", (), {"reg_addrs": reg_addrs})()

    async def read_prepared(self, plan):
        return RawModbusReadResult(
            ok=True,
            values=tuple(self._values),
        )


class TestModbusSourceAcquisitionAdapter:
    """ModbusSourceAcquisitionAdapter 行为测试。"""

    def setup_method(self) -> None:
        self._adapter = ModbusSourceAcquisitionAdapter()

    def test_read_calls_reader(self, monkeypatch) -> None:
        """read 应调用 reader 并返回正确结果。"""
        mock_reader = _MockModbusReader(values=[10, 20, 30])
        monkeypatch.setattr(
            "whale.ingest.adapters.source.modbus_source_acquisition_adapter.ModbusSourceReader",
            lambda host, port, unit_id: mock_reader,
        )

        connection = SourceConnectionData(
            host="127.0.0.1", port=502, ied_name="IED1", ld_name="LD1", namespace_uri="",
        )
        items = [
            AcquisitionItemData(key="item1", profile_item_id=1, relative_path="0"),
            AcquisitionItemData(key="item2", profile_item_id=2, relative_path="1"),
            AcquisitionItemData(key="item3", profile_item_id=3, relative_path="2"),
        ]
        execution = AcquisitionExecutionOptions(
            protocol="modbus_tcp", transport="tcp",
            acquisition_mode="READ_ONCE", interval_ms=100,
            max_iteration=1, request_timeout_ms=5000,
            freshness_timeout_ms=30000, alive_timeout_ms=60000,
        )

        async def _run():
            result = await self._adapter.read(
                execution=execution,
                connection=connection,
                items=items,
            )
            assert result.availability_status == "VALID"
            assert len(result.values) == 3
            assert result.values[0].value == "10"
            assert result.values[1].value == "20"
            assert result.values[2].value == "30"
            assert mock_reader.entered
            assert mock_reader.exited
        asyncio.run(_run())

    def test_supports_subscription_returns_false(self) -> None:
        """Modbus TCP adapter 不应支持订阅。"""
        assert self._adapter.supports_subscription(
            AcquisitionExecutionOptions(
                protocol="modbus_tcp", transport="tcp",
                acquisition_mode="READ_ONCE", interval_ms=100,
                max_iteration=1, request_timeout_ms=5000,
                freshness_timeout_ms=30000, alive_timeout_ms=60000,
            ),
            SourceConnectionData(host="", port=0, ied_name="", ld_name="", namespace_uri=""),
        ) is False

    def test_hex_relative_path(self) -> None:
        """0x 前缀的 relative_path 应解析为十六进制寄存器地址。"""
        addrs = ModbusSourceAcquisitionAdapter._resolve_reg_addrs(
            SourceConnectionData(host="", port=0, ied_name="", ld_name="", namespace_uri=""),
            [AcquisitionItemData(key="t1", profile_item_id=1, relative_path="0x0A")],
        )
        assert addrs == [10]

    def test_invalid_relative_path_raises(self) -> None:
        """无法解析的 relative_path 应抛出 ValueError。"""
        with pytest.raises(ValueError, match="Cannot resolve"):
            ModbusSourceAcquisitionAdapter._resolve_reg_addrs(
                SourceConnectionData(host="", port=0, ied_name="", ld_name="", namespace_uri=""),
                [AcquisitionItemData(key="t1", profile_item_id=1, relative_path="not_a_number")],
            )
