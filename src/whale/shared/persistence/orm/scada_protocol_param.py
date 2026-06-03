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
    """协议端点参数定义 — 定义某个端点可填写哪些正式参数.

    这一层专门描述 endpoint 粒度的参数模板和值表，例如 OPC UA 会话参数、
    Modbus 超时、MQTT topic_filter、HTTP 基础路径、ADS AMS Net ID 等。
    端点主表只保留跨协议公共骨架；凡是会随协议变化的正式参数，都应通过
    `ScadaEndpointParamValue` 落库，而不是塞回 `scada_communication_endpoint`
    主表，也不是长期放在 `metadata_json`。
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
        String(64), nullable=False,
        comment=(
            "应用层协议族：OPC_UA / MODBUS / IEC101 / IEC104 / IEC61850 / MQTT / "
            "HTTP_REST / BECKHOFF_ADS。新增协议时继续扩此枚举，不为每个协议复制新表。"
        ),
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment=(
            "服务类型：READ / SUBSCRIBE / TCP_READ / RTU_READ / INTERROGATION / "
            "SPONTANEOUS / MMS_READ / REPORT / GOOSE / SV / REQUEST / "
            "ADS_READ_WRITE / ADS_NOTIFICATION 等；为 None 表示该参数适用于同协议全部服务。"
        ),
    )
    transport: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True,
        comment=(
            "传输层：TCP / SERIAL / ETHERNET_L2 / MQTT / HTTP / HTTPS；"
            "None 表示适用于同协议全部传输，避免为每种 transport 复制参数定义表。"
        ),
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
        String(1024), nullable=True, comment="允许值列表，逗号分隔；供 Navicat 下拉和值域核对"
    )
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="约束表达式，如 value > 0 / 0 <= value <= 100"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True,
        comment="参数说明；描述该定义在多协议矩阵中的语义和约束，不存具体 endpoint 值"
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
    """协议端点参数值 — endpoint 粒度的第一范式值表.

    每个 endpoint 的每个正式参数单独占一行，方便按协议视图、SQL 和 Navicat
    检索。该表承担正式参数主存储职责；`metadata_json` 只可放临时附注、
    导入痕迹和非结构化说明。
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
        nullable=False, index=True,
        comment="通信端点 ID；同一 endpoint 可按多协议服务模板写入多行 key-value 参数值"
    )
    param_def_id: Mapped[int] = mapped_column(
        ForeignKey("scada_protocol_param_def.param_def_id", ondelete="CASCADE"),
        nullable=False,
        comment="参数定义 ID；通过定义表表达协议/服务/transport 扩展，不在主表加专用列"
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
    """协议信号参数定义 — 定义单个点位如何被具体协议定位和解析.

    这一层专门描述 signal/profile item 粒度的正式参数，例如 Modbus
    寄存器地址、OPC UA NodeId、IEC104 IOA、MQTT payload_path、ADS
    symbol_name。它允许同一套共享点表在不同协议/服务下复用，只把寻址、
    订阅和解析差异放进参数定义和值表。禁止把这些协议地址字段塞回
    `scada_signal_profile_item` 主表，也禁止长期放在 `metadata_json`。
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
        String(64), nullable=False,
        comment=(
            "应用层协议族：与 endpoint 参数定义保持一致。通过协议+服务矩阵描述同一套共享点表"
            "在不同协议下的寻址方式。"
        ),
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment=(
            "服务类型；None 表示适用于同协议全部服务。可用来区分如 "
            "ADS_READ_WRITE 与 ADS_NOTIFICATION 的寻址/订阅参数差异。"
        ),
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
        String(1024), nullable=True, comment="允许值列表，逗号分隔；供 Navicat 查看可选枚举"
    )
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="约束表达式"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True,
        comment="参数说明；描述共享 signal_profile_item 在该协议/服务下如何被定位或订阅"
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
    """点位方案明细协议参数值 — signal profile item 粒度的第一范式值表.

    每个 profile_item 的每个协议参数单独占一行，这样同一套共享点表也能为
    不同协议保存各自的寻址与解析参数，而不污染主表列。
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
        nullable=False, index=True,
        comment="点位方案明细 ID；多个协议服务可复用同一 profile_item，并分别写参数值"
    )
    param_def_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_param_def.param_def_id", ondelete="CASCADE"),
        nullable=False,
        comment="信号参数定义 ID；通过定义表区分协议/服务，不复制多套 signal_profile_item"
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
