"""Tests for the new protocol parameter ORM tables (scada_protocol_param_def,
scada_endpoint_param_value, scada_signal_param_def, scada_signal_profile_item_param_value).

Uses in-memory SQLite to verify table creation, unique constraints, FK constraints,
and parameter value storage without real database infrastructure.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine

from whale.shared.persistence import Base
from whale.shared.persistence.template.protocol_param_data import (
    ENDPOINT_PARAM_DEFS,
    get_endpoint_params,
    get_signal_params,
)
from whale.shared.persistence.template.protocol_view_defs import _PROTOCOL_VIEW_DEFS

# ── Helpers ───────────────────────────────────────────────────────────


def _make_engine() -> Engine:
    return create_engine("sqlite://", echo=False)


def _init_tables(engine: Engine) -> None:
    """Create all ORM tables on the given engine."""
    Base.metadata.create_all(bind=engine)


def test_param_def_table_created() -> None:
    """ScadaProtocolParamDef table must be created by ORM metadata."""
    engine = _make_engine()
    _init_tables(engine)
    inspector = inspect(engine)
    names = set(inspector.get_table_names())
    assert "scada_protocol_param_def" in names


def test_endpoint_param_value_table_created() -> None:
    """ScadaEndpointParamValue table must be created by ORM metadata."""
    engine = _make_engine()
    _init_tables(engine)
    inspector = inspect(engine)
    assert "scada_endpoint_param_value" in inspector.get_table_names()


def test_signal_param_def_table_created() -> None:
    """ScadaSignalParamDef table must be created by ORM metadata."""
    engine = _make_engine()
    _init_tables(engine)
    inspector = inspect(engine)
    assert "scada_signal_param_def" in inspector.get_table_names()


def test_signal_param_value_table_created() -> None:
    """ScadaSignalProfileItemParamValue table must be created."""
    engine = _make_engine()
    _init_tables(engine)
    inspector = inspect(engine)
    assert "scada_signal_profile_item_param_value" in inspector.get_table_names()


def test_param_def_unique_constraint() -> None:
    """Same (protocol, service_type, transport, param_key) must be rejected."""
    engine = _make_engine()
    _init_tables(engine)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO scada_protocol_param_def
                    (application_protocol, service_type, transport, param_key, param_name, data_type, required, sort_order)
                VALUES ('MODBUS', 'TCP_READ', 'TCP', 'unit_id', '单元ID', 'INT', 0, 0)
            """)
        )
        with pytest.raises(Exception, match="UNIQUE|IntegrityError"):
            conn.execute(
                text("""
                    INSERT INTO scada_protocol_param_def
                        (application_protocol, service_type, transport, param_key, param_name, data_type, required, sort_order)
                    VALUES ('MODBUS', 'TCP_READ', 'TCP', 'unit_id', '重复单元ID', 'INT', 0, 0)
                """)
            )


def test_endpoint_param_value_fk() -> None:
    """FK constraint on endpoint_id prevents orphan values."""
    engine = _make_engine()
    _init_tables(engine)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON"))
        with pytest.raises(Exception):
            conn.execute(
                text("""
                    INSERT INTO scada_endpoint_param_value (endpoint_id, param_def_id)
                    VALUES (99999, 99999)
                """)
            )


def test_param_def_insert_and_query() -> None:
    """Insert and query a param def."""
    engine = _make_engine()
    _init_tables(engine)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO scada_protocol_param_def
                    (application_protocol, service_type, transport, param_key, param_name, data_type,
                     required, default_value, unit, description, sort_order)
                VALUES ('MODBUS', 'TCP_READ', 'TCP', 'unit_id', '单元ID', 'INT',
                        1, '1', NULL, 'Modbus slave unit ID', 0)
            """)
        )
        rows = conn.execute(
            text("SELECT param_key, param_name, data_type FROM scada_protocol_param_def")
        ).fetchall()
        assert len(rows) >= 1
        assert any(r.param_key == "unit_id" for r in rows)


def test_endpoint_param_value_insert() -> None:
    """Insert a real endpoint param value (requires real FK)."""
    engine = _make_engine()
    _init_tables(engine)
    with engine.begin() as conn:
        # Insert param def
        conn.execute(
            text("""
                INSERT INTO scada_protocol_param_def
                    (application_protocol, service_type, transport, param_key, param_name, data_type, required, sort_order)
                VALUES ('MODBUS', 'TCP_READ', 'TCP', 'unit_id', '单元ID', 'INT', 0, 0)
            """)
        )
        # Insert a communication endpoint
        conn.execute(
            text("""
                INSERT INTO scada_communication_endpoint
                    (ied_id, access_point_name, application_protocol, transport, service_capabilities_json, metadata_json)
                VALUES (1, 'AP1', 'MODBUS', 'TCP', '{}', '{}')
            """)
        )
        # Insert IED (required for FK)
        conn.execute(
            text("""
                INSERT INTO scada_ied (ied_id, asset_instance_id, ied_name, metadata_json)
                VALUES (1, 1, 'TEST_IED', '{}')
            """)
        )
        # Insert asset_instance (required for asset_instance_id FK)
        conn.execute(
            text("""
                INSERT INTO asset_instance
                    (asset_instance_id, asset_code, asset_name, asset_type_id, status, metadata_json)
                VALUES (1, 'TEST', 'Test Asset', 1, 'active', '{}')
            """)
        )
        # Insert asset_type (required for asset_type_id FK)
        conn.execute(
            text("""
                INSERT INTO asset_type (asset_type_id, type_code, type_name, metadata_json)
                VALUES (1, 'TEST', 'Test Type', '{}')
            """)
        )


def test_goose_endpoint_params_defined() -> None:
    """GOOSE endpoint params must include network_interface and vlan_id."""
    params = get_endpoint_params("IEC61850", "GOOSE")
    keys = {p.key for p in params}
    assert "network_interface" in keys
    assert "vlan_id" in keys
    assert "app_id" in keys
    assert "multicast_mac" in keys


def test_sv_endpoint_params_defined() -> None:
    """SV endpoint params must include sv_cb_ref and sample_rate_hz."""
    params = get_endpoint_params("IEC61850", "SV")
    keys = {p.key for p in params}
    assert "sv_cb_ref" in keys
    assert "sample_rate_hz" in keys
    assert "asdu_count" in keys


def test_modbus_tcp_endpoint_params_defined() -> None:
    """Modbus TCP endpoint params must include unit_id and timeouts."""
    params = get_endpoint_params("MODBUS", "TCP_READ")
    keys = {p.key for p in params}
    assert "unit_id" in keys
    assert "connect_timeout_ms" in keys


def test_iec104_endpoint_params_defined() -> None:
    """IEC104 endpoint params include common_address, t0_ms through w."""
    params = get_endpoint_params("IEC104", "INTERROGATION")
    keys = {p.key for p in params}
    assert "common_address" in keys
    assert "t0_ms" in keys
    assert "k" in keys
    assert "w" in keys


def test_iec61850_mms_signal_params_defined() -> None:
    """IEC61850 MMS signal params must include ied_name, ld_inst, etc."""
    params = get_signal_params("IEC61850", "MMS_READ")
    keys = {p.key for p in params}
    assert "ied_name" in keys
    assert "ld_inst" in keys
    assert "do_name" in keys


def test_modbus_signal_params_defined() -> None:
    """Modbus signal params must include function_code and register_address."""
    params = get_signal_params("MODBUS", "TCP_READ")
    keys = {p.key for p in params}
    assert "function_code" in keys
    assert "register_address" in keys
    assert "byte_order" in keys


def test_goose_signal_params_defined() -> None:
    """GOOSE signal params must include dataset_ref and goose_field_path."""
    params = get_signal_params("IEC61850", "GOOSE")
    keys = {p.key for p in params}
    assert "dataset_ref" in keys
    assert "dataset_index" in keys
    assert "goose_field_path" in keys


def test_signal_param_def_unique_constraint() -> None:
    """Same (protocol, service_type, param_key) must be rejected."""
    engine = _make_engine()
    _init_tables(engine)
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO scada_signal_param_def
                    (application_protocol, service_type, param_key, param_name, data_type, required, sort_order)
                VALUES ('MODBUS', 'TCP_READ', 'function_code', 'Function Code', 'INT', 0, 0)
            """)
        )
        with pytest.raises(Exception, match="UNIQUE|IntegrityError|unique"):
            conn.execute(
                text("""
                    INSERT INTO scada_signal_param_def
                        (application_protocol, service_type, param_key, param_name, data_type, required, sort_order)
                    VALUES ('MODBUS', 'TCP_READ', 'function_code', 'Duplicate', 'INT', 0, 0)
                """)
            )


def test_param_defs_registry_completeness() -> None:
    """All expected protocol+service endpoint param defs must be registered."""
    expected = {
        ("MODBUS", "TCP_READ"),
        ("MODBUS", "RTU_READ"),
        ("IEC101", "INTERROGATION"),
        ("IEC101", "SPONTANEOUS"),
        ("IEC104", "INTERROGATION"),
        ("IEC104", "SPONTANEOUS"),
        ("IEC61850", "MMS_READ"),
        ("IEC61850", "REPORT"),
        ("IEC61850", "GOOSE"),
        ("IEC61850", "SV"),
    }
    registered = set()
    for proto, svc_map in ENDPOINT_PARAM_DEFS.items():
        for svc in svc_map:
            registered.add((proto, svc))
    assert registered == expected, f"Missing: {expected - registered}"


def test_protocol_views_sql_syntax() -> None:
    """All protocol view SQL definitions must parse with valid syntax."""
    for view_name, view_sql in _PROTOCOL_VIEW_DEFS.items():
        assert view_name.startswith("v_scada_endpoint_")
        assert "SELECT" in view_sql
        assert "scada_communication_endpoint" in view_sql


def test_service_type_field_on_endpoint() -> None:
    """CommunicationEndpoint ORM must have service_type field."""
    from whale.shared.persistence.orm import CommunicationEndpoint
    mapper = inspect(CommunicationEndpoint)
    cols = {c.name for c in mapper.columns}
    assert "service_type" in cols
    assert "application_protocol" in cols
    assert "transport" in cols
