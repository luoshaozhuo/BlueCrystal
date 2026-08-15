"""IEC104 server worker 与 protocol factory 测试。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import pytest

from pacific.starfish.adapters.protocols import ProtocolServerFactory
from pacific.starfish.adapters.protocols.ads import AdsServer
from pacific.starfish.adapters.protocols.iec104 import Iec104Server
from pacific.starfish.core.definitions import PointItemDefinition, ServerDefinition
from starfish.core.config_frames import normalize_server_config_frame


class _FakeBackend:
    """记录 IEC104 worker 生命周期调用。"""

    def __init__(self) -> None:
        self.calls: list[object] = []

    def load_points(self, definition: ServerDefinition) -> None:
        """记录 definition 装载。"""
        self.calls.append(("load_points", definition))

    def connect(self) -> None:
        """记录连接装配。"""
        self.calls.append("connect")

    def start(self) -> None:
        """记录 runtime 启动。"""
        self.calls.append("start")

    def stop(self) -> None:
        """记录 runtime 停止。"""
        self.calls.append("stop")

    def health(self) -> dict[str, Any]:
        """返回固定健康快照。"""
        return {"status": "started", "mode": "fake", "running": True}

    def update_point(
        self,
        point: int | str,
        value: Any,
        *,
        transmit_spontaneous: bool = True,
        quality: Any = None,
        recorded_at: datetime | None = None,
    ) -> dict[str, Any]:
        """记录数据源值更新。"""
        self.calls.append(
            (
                "update_point",
                point,
                value,
                transmit_spontaneous,
                quality,
                recorded_at,
            )
        )
        return {"point_item_id": point, "value": value}

    def point_state(self, point: int | str) -> dict[str, Any]:
        """返回固定 Point 状态。"""
        self.calls.append(("point_state", point))
        return {"point_item_id": point, "value": 3}


def _definition(protocol: str = "IEC104") -> ServerDefinition:
    return ServerDefinition(
        connection_id=1001,
        name="IEC104 server",
        protocol=protocol,
        bind_host="0.0.0.0",
        bind_port=2404,
        point_items=(
            PointItemDefinition(11, "p11", "point 11", "FLOAT64", "M_ME_NC_1", 10001),
        ),
        station_role="CONTROLLED_STATION",
    )


def _configuration(protocol: str) -> pd.DataFrame:
    """生成 factory 使用的一行一个 point 公共配置帧。"""
    return normalize_server_config_frame(
        pd.DataFrame(
            [
                {
                    "connection_id": 1001,
                    "name": f"{protocol} server",
                    "protocol": protocol,
                    "bind_host": "127.0.0.1",
                    "bind_port": 2404 if protocol == "IEC104" else 48898,
                    "station_role": (
                        "CONTROLLED_STATION" if protocol == "IEC104" else "SERVER"
                    ),
                    "reconnect_enabled": True,
                    "reconnect_interval_ms": 1000,
                    "t0_ms": 30000,
                    "t1_ms": 15000,
                    "t2_ms": 10000,
                    "t3_ms": 20000,
                    "k_value": 12,
                    "w_value": 8,
                    "ams_net_id": "127.0.0.1.1.1",
                    "ams_port": 851,
                    "point_table_id": 10,
                    "point_item_id": 11,
                    "sort_order": 1,
                    "point_identifier": (
                        "p11" if protocol == "IEC104" else "MAIN.ActivePower"
                    ),
                    "semantic_name": "point 11",
                    "data_type": "FLOAT64",
                    "type_id": "M_ME_NC_1" if protocol == "IEC104" else "LREAL",
                    "io_address": 10001 if protocol == "IEC104" else "MAIN.ActivePower",
                    "initial_value": 0.0,
                    "iec104_type_id": 13,
                    "common_address": 1,
                    "information_object_address": 10001,
                    "general_interrogation_enabled": True,
                    "periodic_transmission_enabled": False,
                    "spontaneous_transmission_enabled": False,
                    "counter_interrogation_enabled": False,
                    "background_transmission_enabled": False,
                    "quality_enabled": True,
                    "addressing_mode": "SYMBOL",
                    "symbol_name": "MAIN.ActivePower",
                    "notification_mode": "NONE",
                }
            ]
        )
    )


def test_iec104_server_owns_definition_and_backend_lifecycle() -> None:
    """worker 管理 backend 生命周期并委托稳定的 point API。"""
    definition = _definition()
    backend = _FakeBackend()
    server = Iec104Server(definition, backend=backend)

    server.start()

    assert backend.calls == [("load_points", definition), "connect", "start"]
    assert server.status().point_count == 1
    assert server.update_point(11, 2)["value"] == 2
    assert server.point_state("p11")["value"] == 3
    server.stop()
    assert backend.calls[-1] == "stop"


def test_protocol_factory_rejects_unregistered_protocol() -> None:
    """协议 factory 对未注册协议返回稳定错误。"""
    factory = ProtocolServerFactory()

    assert isinstance(factory.create(_configuration("IEC104")), Iec104Server)
    assert isinstance(factory.create(_configuration("ADS")), AdsServer)
    with pytest.raises(ValueError, match="未注册 protocol=MODBUS_TCP"):
        factory.create(_configuration("MODBUS_TCP"))
