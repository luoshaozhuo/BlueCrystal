"""SCADA 协议参数模型 — 第一范式协议参数定义与值存储.

禁止使用 metadata_json 作为正式协议参数主存储。
禁止使用 param1 / param2 / param3。

每个参数定义一行，每个端点/点位的每个参数一行值。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from whale.shared.persistence import Base


class ScadaProtocolParamDef(Base):
    """协议端点参数定义 — 定义某个 (protocol, service_type, transport) 组合支持的参数.

    例如 Modbus TCP 需要 unit_id、connect_timeout_ms；
    GOOSE 需要 network_interface、vlan_id、app_id 等。
    不在 param_name 中编码协议信息。
    """

    __tablename__ = "scada_protocol_param_def"
    __table_args__ = (
        UniqueConstraint(
            "application_protocol", "service_type", "transport", "param_key",
            name="uq_protocol_param_def",
        ),
        {"comment": "协议端点参数定义"},
    )

    param_def_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="参数定义主键"
    )
    application_protocol: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="应用层协议：OPC_UA / MODBUS / IEC101 / IEC104 / IEC61850 / MQTT / HTTP_REST"
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="服务类型：TCP_READ / GOOSE / SV / MMS_READ / REPORT 等；为 None 表示该参数适用于协议所有服务类型"
    )
    transport: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True,
        comment="传输层：TCP / SERIAL / ETHERNET_L2 / MQTT / HTTP；None 表示适用于所有传输"
    )
    param_key: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="参数键，如 network_interface / vlan_id / app_id / unit_id / baudrate"
    )
    param_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="参数中文名称"
    )
    data_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="数据类型：STRING / INT / FLOAT / BOOL"
    )
    required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否必填"
    )
    default_value: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="默认值（字符串表示）"
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="单位，如 ms / bps / Hz"
    )
    allowed_values: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="允许值列表，逗号分隔"
    )
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="约束表达式，如 value > 0 / 0 <= value <= 100"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="参数说明"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="显示顺序"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class ScadaEndpointParamValue(Base):
    """协议端点参数值 — endpoint 粒度的参数值，第一范式.

    每个 endpoint 的每个参数值一行。
    """

    __tablename__ = "scada_endpoint_param_value"
    __table_args__ = (
        UniqueConstraint("endpoint_id", "param_def_id", name="uq_endpoint_param_value"),
        {"comment": "通信端点协议参数值"},
    )

    endpoint_param_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="端点参数值主键"
    )
    endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("scada_communication_endpoint.endpoint_id", ondelete="CASCADE"),
        nullable=False, index=True, comment="通信端点 ID"
    )
    param_def_id: Mapped[int] = mapped_column(
        ForeignKey("scada_protocol_param_def.param_def_id", ondelete="CASCADE"),
        nullable=False, comment="参数定义 ID"
    )
    value_text: Mapped[Optional[str]] = mapped_column(
        String(2048), nullable=True, comment="参数值（文本）"
    )
    value_int: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="参数值（整数）"
    )
    value_float: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="参数值（浮点数）"
    )
    value_bool: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="参数值（布尔）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class ScadaSignalParamDef(Base):
    """协议信号参发定义 — 某 (protocol, service_type) 下一个点位可配置的参数.

    例如 Modbus 信号需要 function_code / register_address；
    IEC104 信号需要 ioa / type_id。
    """

    __tablename__ = "scada_signal_param_def"
    __table_args__ = (
        UniqueConstraint(
            "application_protocol", "service_type", "param_key",
            name="uq_signal_param_def",
        ),
        {"comment": "协议信号参数定义"},
    )

    param_def_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="信号参数定义主键"
    )
    application_protocol: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="应用层协议"
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="服务类型；None 表示适用于所有类型"
    )
    param_key: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="参数键"
    )
    param_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="参数中文名称"
    )
    data_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="数据类型：STRING / INT / FLOAT / BOOL / ENUM"
    )
    required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否必填"
    )
    default_value: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="默认值"
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="单位"
    )
    allowed_values: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="允许值列表，逗号分隔"
    )
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="约束表达式"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="参数说明"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="显示顺序"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class ScadaSignalProfileItemParamValue(Base):
    """点位方案明细协议参数值 — signal profile item 粒度的参数值.

    每个 profile_item 的每个参数值一行。
    """

    __tablename__ = "scada_signal_profile_item_param_value"
    __table_args__ = (
        UniqueConstraint("profile_item_id", "param_def_id", name="uq_signal_param_value"),
        {"comment": "点位方案明细协议参数值"},
    )

    item_param_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="信号参数值主键"
    )
    profile_item_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_profile_item.profile_item_id", ondelete="CASCADE"),
        nullable=False, index=True, comment="点位方案明细 ID"
    )
    param_def_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_param_def.param_def_id", ondelete="CASCADE"),
        nullable=False, comment="信号参数定义 ID"
    )
    value_text: Mapped[Optional[str]] = mapped_column(
        String(2048), nullable=True, comment="参数值（文本）"
    )
    value_int: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="参数值（整数）"
    )
    value_float: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="参数值（浮点数）"
    )
    value_bool: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="参数值（布尔）"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
