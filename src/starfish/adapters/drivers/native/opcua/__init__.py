"""OPC UA native-backed driver adapter。"""

from __future__ import annotations

from starfish.adapters.drivers.native.opcua.opcua_facade import OpcUaFacade, probe_opcua_binary

__all__ = ["OpcUaFacade", "probe_opcua_binary"]
