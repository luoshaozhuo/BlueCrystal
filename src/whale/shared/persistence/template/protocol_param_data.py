"""SCADA 多协议端点/信号参数模板.

本文件只定义“某协议某服务需要哪些参数”，不绑定具体 endpoint 或 signal。
正式参数应进入第一范式参数表；禁止把协议地址字段塞回主表，也禁止把
`metadata_json` 当作正式参数主存储。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamDef:
    """单个协议参数定义模板."""

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


OPC_UA_ENDPOINT_PARAMS = [
    ParamDef("endpoint_url", "Endpoint URL", "STRING", required=True, desc="如 opc.tcp://127.0.0.1:4840"),
    ParamDef("application_uri", "应用 URI", "STRING", default="urn:whale:client:opcua"),
    ParamDef("connect_timeout_ms", "连接超时(ms)", "INT", default="5000", unit="ms", constraint="value > 0"),
    ParamDef("request_timeout_ms", "请求超时(ms)", "INT", default="3000", unit="ms", constraint="value > 0"),
    ParamDef("security_policy_override", "安全策略覆盖", "STRING", default="Basic256Sha256"),
]

OPC_UA_SIGNAL_PARAMS = [
    ParamDef("namespace_index", "命名空间索引", "INT", default="2", constraint="value >= 0"),
    ParamDef("node_id", "NodeId", "STRING", required=True, desc="如 ns=2;s=WTG001/MMXU1.TotW.mag.f"),
    ParamDef("browse_path", "BrowsePath", "STRING", desc="如 2:WTG001/2:MMXU1/2:TotW"),
    ParamDef("attribute_id", "属性 ID", "INT", default="13", desc="默认读取 Value 属性"),
]

MODBUS_TCP_ENDPOINT_PARAMS = [
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef("connect_timeout_ms", "连接超时(ms)", "INT", default="3000", unit="ms", constraint="value > 0"),
    ParamDef("request_timeout_ms", "请求超时(ms)", "INT", default="1000", unit="ms", constraint="value > 0"),
]

MODBUS_RTU_ENDPOINT_PARAMS = [
    ParamDef("serial_port", "串口设备", "STRING", True, desc="如 /dev/ttyUSB0"),
    ParamDef("baudrate", "波特率", "INT", default="19200", allowed="9600,19200,38400,57600,115200", unit="bps"),
    ParamDef("parity", "校验位", "STRING", default="N", allowed="N,E,O"),
    ParamDef("stop_bits", "停止位", "INT", default="1", allowed="1,2"),
    ParamDef("data_bits", "数据位", "INT", default="8", allowed="7,8"),
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef("response_timeout_ms", "响应超时(ms)", "INT", default="1000", unit="ms", constraint="value > 0"),
]

MODBUS_SIGNAL_PARAMS = [
    ParamDef("unit_id", "单元 ID", "INT", default="1", constraint="1 <= value <= 247"),
    ParamDef(
        "function_code",
        "功能码",
        "INT",
        required=True,
        allowed="1,2,3,4",
        desc="1=线圈,2=离散输入,3=保持寄存器,4=输入寄存器",
    ),
    ParamDef("register_address", "寄存器地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("register_count", "寄存器数量", "INT", default="1", constraint="1 <= value <= 125"),
    ParamDef("byte_order", "字节序", "STRING", default="BIG_ENDIAN", allowed="BIG_ENDIAN,LITTLE_ENDIAN"),
    ParamDef("word_order", "词序", "STRING", default="BIG_ENDIAN", allowed="BIG_ENDIAN,LITTLE_ENDIAN"),
    ParamDef("signed", "有符号", "BOOL", default="false"),
]

IEC104_ENDPOINT_PARAMS = [
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("originator_address", "发起方地址", "INT", default="0", constraint="0 <= value <= 255"),
    ParamDef("interrogation_group", "总召组", "INT", default="20", constraint="value >= 0"),
    ParamDef("t0_ms", "T0 连接超时(ms)", "INT", default="30000", unit="ms", constraint="value > 0", desc="连接建立超时"),
    ParamDef("t1_ms", "T1 发送/确认超时(ms)", "INT", default="15000", unit="ms", constraint="value > 0"),
    ParamDef("t2_ms", "T2 接收确认超时(ms)", "INT", default="10000", unit="ms", constraint="value > 0"),
    ParamDef("t3_ms", "T3 测试帧超时(ms)", "INT", default="20000", unit="ms", constraint="value > 0"),
    ParamDef("k", "K 最大未确认发送", "INT", default="12", constraint="1 <= value <= 32767"),
    ParamDef("w", "W 最大未确认接收", "INT", default="8", constraint="1 <= value <= 32767"),
]

IEC104_SIGNAL_PARAMS = [
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("ioa", "信息对象地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("type_id", "类型 ID", "INT", required=True, constraint="1 <= value <= 127"),
    ParamDef("cot", "传输原因", "INT", default="3", constraint="1 <= value <= 63"),
]

IEC101_ENDPOINT_PARAMS = [
    ParamDef("serial_port", "串口设备", "STRING", True, desc="如 /dev/ttyUSB0"),
    ParamDef("baudrate", "波特率", "INT", default="9600", allowed="9600,19200,38400,57600,115200", unit="bps"),
    ParamDef("parity", "校验位", "STRING", default="E", allowed="N,E,O"),
    ParamDef("stop_bits", "停止位", "INT", default="1", allowed="1,2"),
    ParamDef("data_bits", "数据位", "INT", default="8", allowed="7,8"),
    ParamDef("link_address", "链路地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
]

IEC101_SIGNAL_PARAMS = [
    ParamDef("link_address", "链路地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("common_address", "公共地址", "INT", default="1", constraint="1 <= value <= 65535"),
    ParamDef("ioa", "信息对象地址", "INT", required=True, constraint="value >= 0"),
    ParamDef("type_id", "类型 ID", "INT", required=True, constraint="1 <= value <= 127"),
    ParamDef("cot", "传输原因", "INT", default="3", constraint="1 <= value <= 63"),
]

IEC61850_MMS_ENDPOINT_PARAMS = [
    ParamDef("scl_ref", "SCL 文件引用", "STRING", desc="ICD/CID/SCD 文件路径或引用"),
    ParamDef("access_point", "AccessPoint", "STRING", default="AP1"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", desc="MMS 数据集引用路径"),
    ParamDef("report_control_block", "Report Control Block", "STRING", desc="RCB 名称"),
    ParamDef("integrity_period_ms", "完整性周期(ms)", "INT", default="60000", unit="ms", constraint="value > 0"),
    ParamDef("buffered", "缓冲模式", "BOOL", default="true", desc="true=BRCB, false=URCB"),
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

GOOSE_ENDPOINT_PARAMS = [
    ParamDef("network_interface", "网络接口", "STRING", True, desc="如 eth0 / enp0s3"),
    ParamDef("vlan_id", "VLAN ID", "INT", default="0", constraint="0 <= value <= 4095", desc="802.1Q VLAN ID"),
    ParamDef("app_id", "APP ID", "INT", required=True, constraint="0 <= value <= 65535", desc="GOOSE APP ID"),
    ParamDef("multicast_mac", "组播 MAC", "STRING", required=True, desc="如 01:0C:CD:01:00:01"),
    ParamDef("go_cb_ref", "GO CB Ref", "STRING", required=True, desc="GOOSE Control Block 引用"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True, desc="数据集引用"),
    ParamDef("min_time_ms", "最小间隔(ms)", "INT", default="1", unit="ms", constraint="value > 0", desc="GOOSE 最小重发间隔"),
    ParamDef("max_time_ms", "最大间隔(ms)", "INT", default="1000", unit="ms", constraint="value > 0", desc="GOOSE 最大重发间隔"),
]

GOOSE_SIGNAL_PARAMS = [
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("dataset_index", "数据集索引", "INT", constraint="value >= 0"),
    ParamDef("goose_field_path", "GOOSE 字段路径", "STRING", desc="如 gooseData[0].value"),
]

SV_ENDPOINT_PARAMS = [
    ParamDef("network_interface", "网络接口", "STRING", True, desc="如 eth0 / enp0s3"),
    ParamDef("vlan_id", "VLAN ID", "INT", default="0", constraint="0 <= value <= 4095"),
    ParamDef("app_id", "APP ID", "INT", required=True, constraint="0 <= value <= 65535"),
    ParamDef("multicast_mac", "组播 MAC", "STRING", required=True, desc="如 01:0C:CD:04:00:01"),
    ParamDef("sv_cb_ref", "SV CB Ref", "STRING", required=True, desc="Sampled Value Control Block 引用"),
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("sample_rate_hz", "采样率(Hz)", "INT", default="4000", unit="Hz", constraint="value > 0"),
    ParamDef("asdu_count", "ASDU 数量", "INT", default="1", constraint="value > 0"),
]

SV_SIGNAL_PARAMS = [
    ParamDef("dataset_ref", "Dataset Ref", "STRING", required=True),
    ParamDef("asdu_index", "ASDU 索引", "INT", default="0", constraint="value >= 0"),
    ParamDef("sample_channel", "采样通道", "INT", default="0", constraint="value >= 0"),
    ParamDef("smp_index", "SMP 索引", "INT", default="0", constraint="value >= 0"),
]

MQTT_ENDPOINT_PARAMS = [
    ParamDef("client_id", "客户端 ID", "STRING", required=True),
    ParamDef("topic_prefix", "主题前缀", "STRING", default="whale/wtg"),
    ParamDef("qos", "默认 QoS", "INT", default="1", allowed="0,1,2"),
    ParamDef("clean_session", "清理会话", "BOOL", default="true"),
    ParamDef("keepalive_seconds", "KeepAlive(秒)", "INT", default="60", unit="s", constraint="value > 0"),
    ParamDef("username_ref", "用户名引用", "STRING", desc="引用凭据系统中的用户名键"),
    ParamDef("password_ref", "密码引用", "STRING", desc="引用凭据系统中的密码键"),
]

MQTT_SIGNAL_PARAMS = [
    ParamDef("topic", "主题", "STRING", required=True),
    ParamDef("payload_path", "报文字段路径", "STRING", required=True, desc="如 telemetry.power_kw"),
    ParamDef("payload_type", "报文类型", "STRING", default="JSON", allowed="JSON,RAW,PROTOBUF"),
    ParamDef("retain", "Retain 标记", "BOOL", default="false"),
]

HTTP_REST_ENDPOINT_PARAMS = [
    ParamDef("base_path", "基础路径", "STRING", default="/api/v1"),
    ParamDef("method", "HTTP 方法", "STRING", default="GET", allowed="GET,POST"),
    ParamDef("auth_header_ref", "认证头引用", "STRING", desc="引用凭据或 header 模板"),
    ParamDef("request_timeout_ms", "请求超时(ms)", "INT", default="3000", unit="ms", constraint="value > 0"),
    ParamDef("verify_tls", "校验 TLS", "BOOL", default="true"),
]

HTTP_REST_SIGNAL_PARAMS = [
    ParamDef("resource_path", "资源路径", "STRING", required=True, desc="如 /devices/WTG001/telemetry"),
    ParamDef("json_path", "JSONPath", "STRING", required=True, desc="JSONPath 或字段路径"),
    ParamDef("method", "点位方法", "STRING", default="GET", allowed="GET,POST"),
    ParamDef("value_field", "值字段", "STRING", default="value"),
]

BECKHOFF_ADS_ENDPOINT_PARAMS = [
    ParamDef("ams_net_id", "AMS Net ID", "STRING", required=True, desc="如 5.32.160.1.1.1"),
    ParamDef("ads_router_port", "ADS Router Port", "INT", default="48898", constraint="value > 0"),
    ParamDef("ads_server_port", "ADS Server Port", "INT", default="851", constraint="value > 0"),
    ParamDef("route_name", "路由名称", "STRING", default="whale-ads-route"),
    ParamDef("connect_timeout_ms", "连接超时(ms)", "INT", default="3000", unit="ms", constraint="value > 0"),
    ParamDef("request_timeout_ms", "请求超时(ms)", "INT", default="1000", unit="ms", constraint="value > 0"),
]

BECKHOFF_ADS_READ_WRITE_SIGNAL_PARAMS = [
    ParamDef("symbol_name", "符号名称", "STRING", required=True, desc="如 MAIN.WTG001.ActivePower"),
    ParamDef("index_group", "IndexGroup", "INT", constraint="value >= 0"),
    ParamDef("index_offset", "IndexOffset", "INT", constraint="value >= 0"),
    ParamDef("data_size", "数据长度", "INT", default="8", constraint="value > 0"),
    ParamDef("ads_data_type", "ADS 数据类型", "STRING", default="LREAL", allowed="BOOL,INT,DINT,REAL,LREAL,STRING"),
]

BECKHOFF_ADS_NOTIFICATION_SIGNAL_PARAMS = [
    *BECKHOFF_ADS_READ_WRITE_SIGNAL_PARAMS,
    ParamDef(
        "notification_mode",
        "通知模式",
        "STRING",
        default="CYCLIC",
        allowed="CYCLIC,ON_CHANGE",
        desc="ADS Notification 触发模式",
    ),
    ParamDef("cycle_time_ms", "采样周期(ms)", "INT", default="1000", unit="ms", constraint="value > 0"),
    ParamDef("max_delay_ms", "最大聚合延迟(ms)", "INT", default="100", unit="ms", constraint="value >= 0"),
]

ENDPOINT_PARAM_DEFS: dict[str, dict[str, list[ParamDef]]] = {
    "OPC_UA": {
        "READ": OPC_UA_ENDPOINT_PARAMS,
        "SUBSCRIBE": OPC_UA_ENDPOINT_PARAMS,
    },
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
    "MQTT": {
        "SUBSCRIBE": MQTT_ENDPOINT_PARAMS,
    },
    "HTTP_REST": {
        "REQUEST": HTTP_REST_ENDPOINT_PARAMS,
    },
    "BECKHOFF_ADS": {
        "ADS_READ_WRITE": BECKHOFF_ADS_ENDPOINT_PARAMS,
        "ADS_NOTIFICATION": BECKHOFF_ADS_ENDPOINT_PARAMS,
    },
}

SIGNAL_PARAM_DEFS: dict[str, dict[str, list[ParamDef]]] = {
    "OPC_UA": {
        "READ": OPC_UA_SIGNAL_PARAMS,
        "SUBSCRIBE": OPC_UA_SIGNAL_PARAMS,
    },
    "MODBUS": {
        "TCP_READ": MODBUS_SIGNAL_PARAMS,
        "RTU_READ": MODBUS_SIGNAL_PARAMS,
    },
    "IEC101": {
        "INTERROGATION": IEC101_SIGNAL_PARAMS,
        "SPONTANEOUS": IEC101_SIGNAL_PARAMS,
    },
    "IEC104": {
        "INTERROGATION": IEC104_SIGNAL_PARAMS,
        "SPONTANEOUS": IEC104_SIGNAL_PARAMS,
    },
    "IEC61850": {
        "MMS_READ": IEC61850_SIGNAL_PARAMS,
        "REPORT": IEC61850_SIGNAL_PARAMS,
        "GOOSE": GOOSE_SIGNAL_PARAMS,
        "SV": SV_SIGNAL_PARAMS,
    },
    "MQTT": {
        "SUBSCRIBE": MQTT_SIGNAL_PARAMS,
    },
    "HTTP_REST": {
        "REQUEST": HTTP_REST_SIGNAL_PARAMS,
    },
    "BECKHOFF_ADS": {
        "ADS_READ_WRITE": BECKHOFF_ADS_READ_WRITE_SIGNAL_PARAMS,
        "ADS_NOTIFICATION": BECKHOFF_ADS_NOTIFICATION_SIGNAL_PARAMS,
    },
}


def _merge_param_defs(param_defs: dict[str, list[ParamDef]]) -> list[ParamDef]:
    """按 `param_key` 去重合并服务级参数定义."""

    merged: dict[str, ParamDef] = {}
    for params in param_defs.values():
        for param in params:
            merged[param.key] = param
    return list(merged.values())


def get_endpoint_params(protocol: str, service_type: str | None) -> list[ParamDef]:
    """返回指定协议/服务的端点参数模板."""

    proto_params = ENDPOINT_PARAM_DEFS.get(protocol)
    if proto_params is None:
        return []
    if service_type in proto_params:
        return list(proto_params[service_type])
    return _merge_param_defs(proto_params)


def get_signal_params(protocol: str, service_type: str | None) -> list[ParamDef]:
    """返回指定协议/服务的点位参数模板."""

    proto_params = SIGNAL_PARAM_DEFS.get(protocol)
    if proto_params is None:
        return []
    if service_type in proto_params:
        return list(proto_params[service_type])
    return _merge_param_defs(proto_params)
