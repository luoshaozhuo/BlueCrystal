"""IEC104 server worker 与 protocol factory 测试。"""

from __future__ import annotations

from typing import Any

import pytest

from starfish.adapters.protocols import ProtocolServerFactory
from starfish.adapters.protocols.iec104 import Iec104Server
from starfish.core.definitions import PointItemDefinition, ServerDefinition


class _FakeBackend:
    """记录 IEC104 worker 生命周期调用。"""

    def __init__(self) -> None:
        self.calls: list[object] = []

    def load_points(self, definition: ServerDefinition) -> None:
        self.calls.append(("load_points", definition))

    def connect(self) -> None:
        self.calls.append("connect")

    def start(self) -> None:
        self.calls.append("start")

    def stop(self) -> None:
        self.calls.append("stop")

    def health(self) -> dict[str, Any]:
        return {"status": "started", "mode": "fake", "running": True}


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
    )


def test_iec104_server_owns_definition_and_backend_lifecycle() -> None:
    definition = _definition()
    backend = _FakeBackend()
    server = Iec104Server(definition, backend=backend)

    server.start()

    assert backend.calls == [("load_points", definition), "connect", "start"]
    assert server.status().point_count == 1
    assert not hasattr(server, "read")
    assert not hasattr(server, "write")

    server.stop()
    assert backend.calls[-1] == "stop"


def test_protocol_factory_only_supports_iec104() -> None:
    factory = ProtocolServerFactory()

    assert isinstance(factory.create(_definition()), Iec104Server)
    with pytest.raises(ValueError, match="只支持 IEC104"):
        factory.create(_definition("MODBUS_TCP"))
