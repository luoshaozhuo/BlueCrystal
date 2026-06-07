"""seahorse reference_data 新路径 import 测试。

验证：
1. seahorse.reference_data 包可正常导入。
2. 所有公开符号均可从 seahorse.reference_data 获取。
3. 协议参数矩阵与原来一致。

测试阶段：开发期验证 (P1)。
不能证明：数据库访问正确性、视图 SQL 方言兼容性。
"""
from __future__ import annotations


def test_import_seahorse_reference_data_package() -> None:
    """seahorse.reference_data 包可正常导入。"""
    import seahorse.reference_data  # noqa: F401


def test_protocol_param_data_accessible_from_reference_data() -> None:
    """协议参数数据可从 seahorse.reference_data 导入。"""
    from seahorse.reference_data import (
        ENDPOINT_PARAM_DEFS,
        SIGNAL_PARAM_DEFS,
        ParamDef,
        get_endpoint_params,
    )

    assert isinstance(ENDPOINT_PARAM_DEFS, dict)
    assert isinstance(SIGNAL_PARAM_DEFS, dict)
    assert "OPC_UA" in ENDPOINT_PARAM_DEFS
    assert "MODBUS" in ENDPOINT_PARAM_DEFS
    assert "BECKHOFF_ADS" in ENDPOINT_PARAM_DEFS

    params = get_endpoint_params("OPC_UA", "READ")
    assert len(params) > 0
    assert all(isinstance(p, ParamDef) for p in params)


def test_protocol_view_defs_accessible_from_reference_data() -> None:
    """协议视图定义可从 seahorse.reference_data 导入。"""
    from seahorse.reference_data import _PROTOCOL_VIEW_DEFS, ensure_protocol_views

    assert isinstance(_PROTOCOL_VIEW_DEFS, dict)
    assert "v_scada_endpoint_beckhoff_ads" in _PROTOCOL_VIEW_DEFS
    assert callable(ensure_protocol_views)


def test_sample_data_accessible_from_reference_data() -> None:
    """样例数据模块可从 seahorse.reference_data 导入。"""
    from seahorse.reference_data import (
        PROTOCOL_SAMPLE_SPECS,
        ProtocolSampleSpec,
        generate_all_sample_data,
    )

    assert isinstance(PROTOCOL_SAMPLE_SPECS, list)
    assert len(PROTOCOL_SAMPLE_SPECS) == 16
    assert all(isinstance(s, ProtocolSampleSpec) for s in PROTOCOL_SAMPLE_SPECS)
    assert callable(generate_all_sample_data)


def test_protocol_coverage_matches_expected_matrix() -> None:
    """参考数据中的协议覆盖矩阵与预期一致。"""
    from seahorse.reference_data.protocol_param_data import ENDPOINT_PARAM_DEFS, SIGNAL_PARAM_DEFS

    expected = {
        ("OPC_UA", "READ"),
        ("OPC_UA", "SUBSCRIBE"),
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
        ("MQTT", "SUBSCRIBE"),
        ("HTTP_REST", "REQUEST"),
        ("BECKHOFF_ADS", "ADS_READ_WRITE"),
        ("BECKHOFF_ADS", "ADS_NOTIFICATION"),
    }
    registered_ep = {(p, s) for p, svcs in ENDPOINT_PARAM_DEFS.items() for s in svcs}
    registered_sp = {(p, s) for p, svcs in SIGNAL_PARAM_DEFS.items() for s in svcs}
    assert registered_ep == expected
    assert registered_sp == expected


def test_gbt_30966_fields_accessible() -> None:
    """GB/T 30966 字段定义可从 seahorse 新路径导入。"""
    from seahorse.reference_data.gbt_30966_fields import ALL_LOGICAL_NODES, LogicalNodeDef

    assert isinstance(ALL_LOGICAL_NODES, list)
    assert len(ALL_LOGICAL_NODES) > 0
    assert all(isinstance(ln, LogicalNodeDef) for ln in ALL_LOGICAL_NODES)
