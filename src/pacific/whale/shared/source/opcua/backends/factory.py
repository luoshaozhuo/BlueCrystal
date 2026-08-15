"""OPC UA 客户端后端工厂。

提供后端名称规范化和实例化逻辑，
将配置中的后端名称映射到具体后端类。
"""
from __future__ import annotations

from pacific.whale.shared.source.models import SourceConnectionProfile
from pacific.whale.shared.source.opcua.backends.base import OpcUaClientBackend
from pacific.whale.shared.source.opcua.backends.open62541_backend import Open62541OpcUaClientBackend


def normalize_client_backend_name(name: str) -> str:
    """Normalize one raw client-backend label to a supported canonical name."""

    normalized = name.strip().lower().replace("_", "").replace("-", "")
    if normalized in {"open62541", "open"}:
        return "open62541"
    raise ValueError("source_lab OPC UA only supports open62541")


def resolve_client_backend_name(connection: SourceConnectionProfile) -> str:
    """Resolve OPC UA client backend name from connection params or default."""

    params_backend = connection.params.get("client_backend")
    if isinstance(params_backend, str) and params_backend.strip():
        return normalize_client_backend_name(params_backend)

    return "open62541"


def build_client_backend(connection: SourceConnectionProfile) -> OpcUaClientBackend:
    """Build one concrete OPC UA client backend for the given connection."""

    backend_name = resolve_client_backend_name(connection)
    if backend_name == "open62541":
        return Open62541OpcUaClientBackend(connection)
    raise AssertionError(f"Unhandled OPC UA client backend: {backend_name}")
