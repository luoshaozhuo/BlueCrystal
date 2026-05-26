"""协议矩阵与 runner 类型测试。"""

from __future__ import annotations

from tools.source_lab.access.runners.registry import build_capacity_runner, build_subscription_runner


def test_polling_protocols_build_expected_runners() -> None:
    """polling 协议应可构建 capacity runner。"""

    names = {
        "opcua": build_capacity_runner("opcua").name,
        "modbus_tcp": build_capacity_runner("modbus_tcp").name,
        "modbus_rtu": build_capacity_runner("modbus_rtu").name,
        "iec101": build_capacity_runner("iec101").name,
        "iec104": build_capacity_runner("iec104").name,
        "iec61850_mms": build_capacity_runner("iec61850_mms").name,
        "http_rest": build_capacity_runner("http_rest").name,
    }

    # iec101/modbus_rtu 使用 native runner 需要串口设备；
    # 无串口环境下回退到 Python lightweight runner
    import glob
    _has_serial = len(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")) > 0
    modbus_rtu_expected = "modbus_rtu_native_runner" if _has_serial else "modbus_rtu_polling_runner"
    iec101_expected = "iec101_native_runner" if _has_serial else "iec101_polling_runner"

    assert names == {
        "opcua": "opcua_open62541_serial_runner",
        "modbus_tcp": "modbus_tcp_native_runner",
        "modbus_rtu": modbus_rtu_expected,
        "iec101": iec101_expected,
        "iec104": "iec104_native_runner",
        "iec61850_mms": "iec61850_mms_native_runner",
        "http_rest": "http_rest_polling_runner",
    }


def test_streaming_protocols_build_expected_runners() -> None:
    """streaming 协议应可构建 subscribe runner。"""

    names = {
        "opcua": build_subscription_runner("opcua").name,
        "iec101": build_subscription_runner("iec101").name,
        "iec104": build_subscription_runner("iec104").name,
        "iec61850_report": build_subscription_runner("iec61850_report").name,
        "mqtt": build_subscription_runner("mqtt").name,
    }

    assert names == {
        "opcua": "opcua_open62541_subscription_runner",
        "iec101": "iec101_event_runner",
        "iec104": "iec104_event_runner",
        "iec61850_report": "iec61850_report_runner",
        "mqtt": "mqtt_subscription_runner",
    }
