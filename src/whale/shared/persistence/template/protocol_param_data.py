"""SCADA 多协议端点/信号参数定义初始化数据.

本文件仅定义参数结构（哪些参数、数据类型、默认值、约束等），
不关联任何具体 endpoint 或 profile item。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParamDef:
    """单个参数定义."""
    key: str
    name: str
    data_type: str
    required: bool = False
    default: str | None = None
    unit: str | None = None
    allowed: str | None = None
    constraint: str | None = None
    desc: str | None = None
    sort: int = 0


# ── GOOSE Endpoint Parameters ─────────────────────────────────────────

GOOSE_ENDPOINT_PARAMS = [
    ParamDef("network_interface", "网络接口", "STRING", True, desc="如 eth0 / enp0s3"),
    ParamDef("vlan_id", "VLAN ID", "INT", default="0", constraint="0 <= value <= 4095", desc="802.1Q VLAN ID"),
    ParamDef("app_id", "APP ID", "INT", required=True, constraint="0 <= value <= 65535", desc="GOOSE APP ID"),
    ParamDef("multicast_mac", "组播 MAC", "STRING", required=True, desc="如 01:0C:CD:01:00:01"),
    ParamDef("go_cb_ref", "GO CB Ref", "STRING", required=True, desc="GOOSE Control Block 引用"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True, desc="数据集引用"),
    ParamDef("min_time_ms", "最小间隔(ms)", "INT", default="1", constraint="value > 0", unit="ms", desc="GOOSE 最小重发间隔"),
    ParamDef("max_time_ms", "最大间隔(ms)", "INT", default="1000", constraint="value > 0", unit="ms", desc="GOOSE 最大重发间隔"),
]

# ── SV Endpoint Parameters ────────────────────────────────────────────

SV_ENDPOINT_PARAMS = [
    ParamDef("network_interface", "网络接口", "STRING", True, desc="如 eth0 / enp0s3"),
    ParamDef("vlan_id", "VLAN ID", "INT", default="0", constraint="0 <= value <= 4095"),
    ParamDef("app_id", "APP ID", "INT", required=True, constraint="0 <= value <= 65535"),
    ParamDef("multicast_mac", "组播 MAC", "STRING", required=True, desc="如 01:0C:CD:04:00:01"),
    ParamDef("sv_cb_ref", "SV CB Ref", "STRING", required=True, desc="Sampled Value Control Block 引用"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("sample_rate_hz", "采样率(Hz)", "INT", default="4000", constraint="value > 0", unit="Hz"),
    ParamDef("asdu_count", "ASDU 数量", "INT", default="1", constraint="value > 0"),
]

# ── Modbus Endpoint Parameters ────────────────────────────────────────

MODBUS_TCP_ENDPOINT_PARAMS = [
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef("connect_timeout_ms", "连接超时(ms)", "INT", default="3000", constraint="value > 0", unit="ms"),
    ParamDef("request_timeout_ms", "请求超时(ms)", "INT", default="1000", constraint="value > 0", unit="ms"),
]

MODBUS_RTU_ENDPOINT_PARAMS = [
    ParamDef("serial_port", "串口设备", "STRING", True, desc="如 /dev/ttyUSB0"),
    ParamDef("baudrate", "波特率", "INT", default="19200", allowed="9600,19200,38400,57600,115200", unit="bps"),
    ParamDef("parity", "校验位", "STRING", default="N", allowed="N,E,O"),
    ParamDef("stop_bits", "停止位", "INT", default="1", allowed="1,2"),
    ParamDef("data_bits", "数据位", "INT", default="8", allowed="7,8"),
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef("response_timeout_ms", "响应超时(ms)", "INT", default="1000", constraint="value > 0", unit="ms"),
]

# ── IEC104 Endpoint Parameters ────────────────────────────────────────

IEC104_ENDPOINT_PARAMS = [
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("originator_address", "发起方地址", "INT", default="0", constraint="0 <= value <= 255"),
    ParamDef("interrogation_group", "总召组", "INT", default="20", constraint="value >= 0"),
    ParamDef("t0_ms", "T0 连接超时(ms)", "INT", default="30000", constraint="value > 0", unit="ms", desc="连接建立超时"),
    ParamDef("t1_ms", "T1 发送/确认超时(ms)", "INT", default="15000", constraint="value > 0", unit="ms"),
    ParamDef("t2_ms", "T2 接收确认超时(ms)", "INT", default="10000", constraint="value > 0", unit="ms"),
    ParamDef("t3_ms", "T3 测试帧超时(ms)", "INT", default="20000", constraint="value > 0", unit="ms"),
    ParamDef("k", "K 最大未确认发送", "INT", default="12", constraint="1 <= value <= 32767"),
    ParamDef("w", "W 最大未确认接收", "INT", default="8", constraint="1 <= value <= 32767"),
]

# ── IEC101 Endpoint Parameters ────────────────────────────────────────

IEC101_ENDPOINT_PARAMS = [
    ParamDef("serial_port", "串口设备", "STRING", True, desc="如 /dev/ttyUSB0"),
    ParamDef("baudrate", "波特率", "INT", default="9600", allowed="9600,19200,38400,57600,115200", unit="bps"),
    ParamDef("parity", "校验位", "STRING", default="E", allowed="N,E,O"),
    ParamDef("stop_bits", "停止位", "INT", default="1", allowed="1,2"),
    ParamDef("data_bits", "数据位", "INT", default="8", allowed="7,8"),
    ParamDef("link_address", "链路地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
]

# ── IEC61850 MMS/Report Endpoint Parameters ──────────────────────────

IEC61850_MMS_ENDPOINT_PARAMS = [
    ParamDef("scl_ref", "SCL 文件引用", "STRING", desc="ICD/CID/SCD 文件路径或引用"),
    ParamDef("access_point", "AccessPoint", "STRING", default="AP1"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", desc="MMS 数据集引用路径"),
    ParamDef("report_control_block", "Report Control Block", "STRING", desc="RCB 名称"),
    ParamDef("integrity_period_ms", "完整性周期(ms)", "INT", default="60000", constraint="value > 0", unit="ms"),
    ParamDef("buffered", "缓冲模式", "BOOL", default="true", desc="true=BRCB, false=URCB"),
]

# ── Signal Item Parameters (used per signal profile item) ─────────────

MODBUS_SIGNAL_PARAMS = [
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef("function_code", "功能码", "INT", required=True, allowed="1,2,3,4", desc="1=线圈,2=离散输入,3=保持寄存器,4=输入寄存器"),
    ParamDef("register_address", "寄存器地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("register_count", "寄存器数量", "INT", default="1", constraint="1 <= value <= 125"),
    ParamDef("byte_order", "字节序", "STRING", default="BIG_ENDIAN", allowed="BIG_ENDIAN,LITTLE_ENDIAN"),
    ParamDef("word_order", "词序", "STRING", default="BIG_ENDIAN", allowed="BIG_ENDIAN,LITTLE_ENDIAN"),
    ParamDef("signed", "有符号", "BOOL", default="false"),
]

IEC104_SIGNAL_PARAMS = [
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("ioa", "信息对象地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("type_id", "类型 ID", "INT", required=True, constraint="1 <= value <= 127"),
    ParamDef("cot", "传输原因", "INT", default="3", constraint="1 <= value <= 63"),
]

IEC101_SIGNAL_PARAMS = [
    ParamDef("link_address", "链路地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("ioa", "信息对象地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("type_id", "类型 ID", "INT", required=True, constraint="1 <= value <= 127"),
    ParamDef("cot", "传输原因", "INT", default="3", constraint="1 <= value <= 63"),
]

IEC61850_SIGNAL_PARAMS = [
    ParamDef("ied_name", "IED 名称", "STRING", required=True),
    ParamDef("ld_inst", "LD 实例", "STRING", required=True),
    ParamDef("ln_class", "LN 类", "STRING", required=True, desc="如 MMXU / WROT / WTUR"),
    ParamDef("ln_inst", "LN 实例", "INT", default="1"),
    ParamDef("do_name", "DO 名称", "STRING", required=True),
    ParamDef("da_name", "DA 名称", "STRING", default="mag.f"),
    ParamDef("fc", "功能约束", "STRING", default="MX", allowed="MX,ST,CF,DC,SV"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING"),
    ParamDef("dataset_index", "数据集索引", "INT", constraint="value >= 0"),
]

GOOSE_SIGNAL_PARAMS = [
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("dataset_index", "数据集索引", "INT", constraint="value >= 0"),
    ParamDef("goose_field_path", "GOOSE 字段路径", "STRING", desc="如 gooseData[0].value"),
]

SV_SIGNAL_PARAMS = [
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("asdu_index", "ASDU 索引", "INT", default="0", constraint="value >= 0"),
    ParamDef("sample_channel", "采样通道", "INT", default="0", constraint="value >= 0"),
    ParamDef("smp_index", "SMP 索引", "INT", default="0", constraint="value >= 0"),
]

# ── Registry: protocol → (endpoint params, signal params) ─────────────

ENDPOINT_PARAM_DEFS: dict[str, dict[str, list[ParamDef]]] = {
    "MODBUS": {
        "TCP_READ": MODBUS_TCP_ENDPOINT_PARAMS,
        "RTU_READ": MODBUS_RTU_ENDPOINT_PARAMS,
    },
    "IEC101": {
        "INTERROGATION": IEC101_ENDPOINT_PARAMS,
        "SPONTANEOUS": IEC101_ENDPOINT_PARAMS,
    },
    "IEC104": {
        "INTERROGATION": IEC104_ENDPOINT_PARAMS,
        "SPONTANEOUS": IEC104_ENDPOINT_PARAMS,
    },
    "IEC61850": {
        "MMS_READ": IEC61850_MMS_ENDPOINT_PARAMS,
        "REPORT": IEC61850_MMS_ENDPOINT_PARAMS,
        "GOOSE": GOOSE_ENDPOINT_PARAMS,
        "SV": SV_ENDPOINT_PARAMS,
    },
}

SIGNAL_PARAM_DEFS: dict[str, dict[str, list[ParamDef]]] = {
    "MODBUS": {"TCP_READ": MODBUS_SIGNAL_PARAMS, "RTU_READ": MODBUS_SIGNAL_PARAMS},
    "IEC101": {"INTERROGATION": IEC101_SIGNAL_PARAMS, "SPONTANEOUS": IEC101_SIGNAL_PARAMS},
    "IEC104": {"INTERROGATION": IEC104_SIGNAL_PARAMS, "SPONTANEOUS": IEC104_SIGNAL_PARAMS},
    "IEC61850": {
        "MMS_READ": IEC61850_SIGNAL_PARAMS,
        "REPORT": IEC61850_SIGNAL_PARAMS,
        "GOOSE": GOOSE_SIGNAL_PARAMS,
        "SV": SV_SIGNAL_PARAMS,
    },
}

# ── Helper to get params for a specific protocol+service ──────────────


def get_endpoint_params(protocol: str, service_type: str | None) -> list[ParamDef]:
    """Get endpoint parameter definitions for the given protocol and service type."""
    if protocol in ENDPOINT_PARAM_DEFS:
        proto_params = ENDPOINT_PARAM_DEFS[protocol]
        if service_type in proto_params:
            return list(proto_params[service_type])
        # Return combined if no specific service type match
        all_params: list[ParamDef] = []
        for sp in proto_params.values():
            all_params.extend(sp)
        return all_params
    return []


def get_signal_params(protocol: str, service_type: str | None) -> list[ParamDef]:
    """Get signal parameter definitions for the given protocol and service type."""
    if protocol in SIGNAL_PARAM_DEFS:
        proto_params = SIGNAL_PARAM_DEFS[protocol]
        if service_type in proto_params:
            return list(proto_params[service_type])
        all_params: list[ParamDef] = []
        for sp in proto_params.values():
            all_params.extend(sp)
        return all_params
    return []
