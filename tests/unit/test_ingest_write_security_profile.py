"""Unit tests for WriteSecurityProfile domain model."""

from __future__ import annotations

from whale.ingest.domain.write_security_profile import (
    ProtocolWriteProfile,
    ReadbackStrategy,
    WriteSecurityProfile,
)


def test_default_profile_denies_all_protocols():
    profile = WriteSecurityProfile()
    assert profile.is_write_allowed("opcua") is False
    assert profile.is_write_allowed("modbus_tcp") is False
    assert profile.is_write_allowed("iec61850_mms") is False
    assert profile.is_write_allowed("unknown_protocol") is False


def test_explicitly_allowed_protocol_is_allowed():
    profile = WriteSecurityProfile(
        protocols={
            "opcua": ProtocolWriteProfile(allowed=True),
        }
    )
    assert profile.is_write_allowed("opcua") is True
    assert profile.is_write_allowed("modbus_tcp") is False


def test_profile_for_normalizes_protocol_name():
    profile = WriteSecurityProfile(
        protocols={
            "opcua": ProtocolWriteProfile(allowed=True),
        }
    )
    assert profile.profile_for("OPCUA").allowed is True
    assert profile.profile_for(" OpcUa ").allowed is True
    assert profile.profile_for("opcua").allowed is True


def test_profile_for_returns_default_for_unknown_protocol():
    profile = WriteSecurityProfile()
    resolved = profile.profile_for("nonexistent")
    assert resolved.allowed is False
    assert resolved.readback_strategy == ReadbackStrategy.DISABLED
    assert resolved.required_roles == ("admin",)
    assert resolved.max_items_per_write == 100


def test_protocol_write_profile_readback_strategy():
    profile = WriteSecurityProfile(
        protocols={
            "opcua": ProtocolWriteProfile(
                allowed=True,
                readback_strategy=ReadbackStrategy.IMMEDIATE_READBACK,
            ),
            "modbus_tcp": ProtocolWriteProfile(
                allowed=True,
                readback_strategy=ReadbackStrategy.ASYNC_CONFIRMATION,
            ),
        }
    )
    assert profile.profile_for("opcua").readback_strategy == ReadbackStrategy.IMMEDIATE_READBACK
    assert profile.profile_for("modbus_tcp").readback_strategy == ReadbackStrategy.ASYNC_CONFIRMATION
    assert profile.profile_for("iec61850_mms").readback_strategy == ReadbackStrategy.DISABLED


def test_protocol_write_profile_custom_roles():
    profile = WriteSecurityProfile(
        protocols={
            "opcua": ProtocolWriteProfile(
                allowed=True,
                required_roles=("supervisor", "engineer"),
                max_items_per_write=10,
            ),
        }
    )
    resolved = profile.profile_for("opcua")
    assert resolved.required_roles == ("supervisor", "engineer")
    assert resolved.max_items_per_write == 10


def test_write_security_profile_immutable_by_default():
    profile = WriteSecurityProfile(protocols={"opcua": ProtocolWriteProfile(allowed=True)})
    assert profile.is_write_allowed("modbus_tcp") is False
    assert profile.is_write_allowed("opcua") is True


def test_readback_strategy_enum_values():
    assert ReadbackStrategy.DISABLED.value == "disabled"
    assert ReadbackStrategy.IMMEDIATE_READBACK.value == "immediate_readback"
    assert ReadbackStrategy.ASYNC_CONFIRMATION.value == "async_confirmation"
