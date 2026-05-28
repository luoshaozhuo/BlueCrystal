"""SCADA 采集模型 — IED / Endpoint / LDInstance / SignalProfile."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from whale.shared.persistence import Base

if TYPE_CHECKING:
    from whale.shared.persistence.orm.asset import AssetInstance


class IED(Base):
    """IED 实例 — 表示一个真实 IED 通信身份，必须绑定 asset_instance.

    普通设备：IED 绑定该设备资产.
    网关设备：IED 绑定网关/通信管理机资产.
    """

    __tablename__ = "scada_ied"
    __table_args__ = (
        UniqueConstraint("ied_name", name="uq_ied_name"),
        {"comment": "IED 实例"},
    )

    ied_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="IED 主键")
    asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=False, index=True,
        comment="IED 所属资产实例，不能为空"
    )
    ied_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="IED 名称，如 IED_WTG_001 / IED_GATEWAY_001 / IED_PCS_001"
    )
    ied_code: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="IED 编码，如 WTG001_CTRL_IED / GATEWAY_A_IED"
    )
    ied_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="IED 类型：WTG_CONTROLLER / SUBSTATION_GATEWAY / PCS_CONTROLLER / MET_STATION / PROTECTION_DEVICE"
    )
    standard_family: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="标准体系：IEC61850 / IEC61400_25 / DLT860 / GB_T_30966 / VENDOR_PRIVATE"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="IED 扩展属性，如 SCL 来源文件、工程版本、厂家私有标识"
    )
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"), comment="乐观并发版本号")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    asset_instance: Mapped["AssetInstance"] = relationship(back_populates="ied")
    endpoints: Mapped[list["CommunicationEndpoint"]] = relationship(back_populates="ied")


class CommunicationEndpoint(Base):
    """通信端点 — 表示真实可连接的通信入口.

    合并 AccessPoint + endpoint + protocol 上下文.
    一个 IED 可以有多个 endpoint.
    """

    __tablename__ = "scada_communication_endpoint"
    __table_args__ = (
        UniqueConstraint("ied_id", "access_point_name", name="uq_endpoint_ied_ap"),
        {"comment": "通信端点"},
    )

    endpoint_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="通信端点主键")
    ied_id: Mapped[int] = mapped_column(ForeignKey("scada_ied.ied_id"), nullable=False, index=True, comment="所属 IED")
    access_point_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="AccessPoint 名称，如 AP1 / MMS_AP / OPCUA_AP / ETH1"
    )
    endpoint_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="端点显示名称，如 1号风机MMS端点 / 1号网关OPC UA端点"
    )
    application_protocol: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True,
        comment="应用层协议：OPC_UA / MODBUS / IEC101 / IEC104 / IEC61850 / MQTT / HTTP_REST"
    )
    service_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, index=True,
        comment="服务类型：READ / SUBSCRIBE / TCP_READ / RTU_READ / INTERROGATION / SPONTANEOUS / MMS_READ / REPORT / GOOSE / SV / REQUEST"
    )
    transport: Mapped[str] = mapped_column(
        String(32), nullable=False, default="TCP",
        comment="传输层协议：TCP / SERIAL / ETHERNET_L2 / MQTT / HTTP / HTTPS"
    )
    host: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="主机地址，如 192.168.10.21"
    )
    port: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="端口号，如 102 / 4840 / 502"
    )
    namespace_uri: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="命名空间 URI，适用 OPC UA 或厂家私有命名空间"
    )
    security_policy: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="安全策略：None / Basic256Sha256 / Basic256"
    )
    security_mode: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="安全模式：None / Sign / SignAndEncrypt"
    )
    auth_type: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="认证方式：Anonymous / UsernamePassword / Certificate / Token"
    )
    credential_ref: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="凭据引用，不直接存明文密码"
    )
    heartbeat_interval_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="心跳间隔，单位毫秒")
    service_capabilities_json: Mapped[dict] = mapped_column(
        JSON, default=dict,
        comment="服务能力，如 {\"supports_read\": true, \"supports_write\": false, \"supports_subscription\": true}"
    )
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="端点说明")
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="扩展属性，如 网络区域、冗余组、厂家私有连接字段"
    )
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"), comment="乐观并发版本号")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    ied: Mapped["IED"] = relationship(back_populates="endpoints")
    ld_instances: Mapped[list["LDInstance"]] = relationship(back_populates="endpoint")


class LDInstance(Base):
    """LD 实例 — 表示某个 endpoint 下真实暴露出来的 LD.

    每个 LDInstance 必须绑定 asset_instance_id.
    普通设备：LDInstance.asset_instance_id 通常等于 IED.asset_instance_id.
    网关代理：LDInstance.asset_instance_id 指向被代理的设备资产.
    """

    __tablename__ = "scada_ld_instance"
    __table_args__ = (
        UniqueConstraint("endpoint_id", "ld_name", name="uq_ld_instance_endpoint_name"),
        {"comment": "LD 实例"},
    )

    ld_instance_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="LD 实例主键")
    endpoint_id: Mapped[int] = mapped_column(
        ForeignKey("scada_communication_endpoint.endpoint_id"), nullable=False, index=True, comment="所属通信端点"
    )
    asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=False, index=True,
        comment="该 LD 实际代表的资产实例，不能为空"
    )
    signal_profile_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scada_signal_profile.signal_profile_id"), nullable=True, index=True,
        comment="该 LD 使用的点位方案"
    )
    ld_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="LD 名称，如 ZB-WTG-001 / PCS_001 / MET_001"
    )
    ld_type: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="LD 类型：WIND_TURBINE / PCS / BMS / MET_STATION / GATEWAY / SUBSTATION"
    )
    path_prefix: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="协议路径前缀，如 WTG_001 / Gateway/WTG_001"
    )
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, comment="实例扩展属性")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    endpoint: Mapped["CommunicationEndpoint"] = relationship(back_populates="ld_instances")
    signal_profile: Mapped[Optional["SignalProfile"]] = relationship(back_populates="ld_instances")


class SignalProfile(Base):
    """点位方案 — 表示一套可复用的 LN/DO/DA 采集方案.

    多个 LDInstance 可以引用同一个 SignalProfile.
    例如：风机基础点位方案 V1 / 厂家A风机点位方案 V2.
    """

    __tablename__ = "scada_signal_profile"
    __table_args__ = (
        UniqueConstraint("profile_code", name="uq_signal_profile_code"),
        {"comment": "点位方案"},
    )

    signal_profile_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="点位方案主键")
    profile_code: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False, comment="点位方案编码，如 WTG_IEC61400_25_BASIC_V1"
    )
    profile_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="点位方案名称，如 风机基础采集点位方案 V1"
    )
    asset_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=True, comment="适用资产类型"
    )
    standard_family: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="标准体系：IEC61400_25 / IEC61850 / GB_T_30966 / VENDOR_PRIVATE"
    )
    vendor: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="厂家：STANDARD / VendorA / VendorB"
    )
    version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="方案版本")
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="方案说明")
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="方案扩展信息，如 来源文件、适用机型、适用协议、点表版本"
    )
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"), comment="乐观并发版本号")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    ld_instances: Mapped[list["LDInstance"]] = relationship(back_populates="signal_profile")
    items: Mapped[list["SignalProfileItem"]] = relationship(back_populates="signal_profile")


class SignalProfileItem(Base):
    """点位方案明细 — 表示某个 SignalProfile 中的一个可采集点.

    LN / DO / DA 信息直接合并在一条记录中.
    """

    __tablename__ = "scada_signal_profile_item"
    __table_args__ = (
        UniqueConstraint("signal_profile_id", "relative_path", name="uq_profile_item_path"),
        {"comment": "点位方案明细"},
    )

    profile_item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="点位方案明细主键")
    signal_profile_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_profile.signal_profile_id"), nullable=False, index=True, comment="所属点位方案"
    )
    ln_class: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="LN 类：MMXU / WROT / WGEN / WTUR / GGIO 等"
    )
    ln_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="LN 完整名称，如 MMXU1 / WROT1 / WGEN1"
    )
    do_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="DO 名称，如 TotW / WSpd / Beh / Health / RotSpd"
    )
    da_name: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="DA 名称，如 mag.f / stVal / q / t"
    )
    relative_path: Mapped[str] = mapped_column(
        String(512), nullable=False,
        comment="相对于 LD 实例的点位路径，如 MMXU1.TotW.mag.f / WROT1.RotSpd.mag.f"
    )
    fc: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="功能约束：ST / MX / SP / CF / DC / EX"
    )
    cdc: Mapped[Optional[str]] = mapped_column(
        String(8), nullable=True, comment="公共数据类：MV / SPS / INS / ACT / DPC"
    )
    data_type_id: Mapped[int] = mapped_column(
        ForeignKey("scada_data_type.data_type_id"), nullable=False, comment="数据类型 ID"
    )
    default_unit: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="默认单位，如 kW / m/s / ℃ / % / rpm"
    )
    default_scale: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="默认倍率")
    default_offset: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="默认偏移量")
    default_precision: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="默认小数精度")
    default_constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="默认值域或约束表达式，如 0 <= value <= 100 / value >= 0 / NONE"
    )
    default_sample_mode: Mapped[str] = mapped_column(
        String(32), default="POLLING", comment="默认采样模式：POLLING / SUBSCRIPTION / REPORT"
    )
    default_sample_interval_ms: Mapped[int] = mapped_column(
        Integer, default=1000, comment="默认采样周期，单位毫秒"
    )
    default_deadband: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="默认死区")
    quality_supported: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="该点位是否支持质量位"
    )
    timestamp_supported: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="该点位是否支持源端时间戳"
    )
    writable: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否可写或可控")
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="显示名称，如 有功功率 / 风速 / 转速 / 运行状态"
    )
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="点位说明")
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"), comment="乐观并发版本号")

    signal_profile: Mapped["SignalProfile"] = relationship(back_populates="items")
    data_type: Mapped["ScadaDataType"] = relationship()


class ScadaDataType(Base):
    """SCADA 数据类型 — 统一管理 BOOLEAN / INT32 / FLOAT64 / STRING 等基本类型."""

    __tablename__ = "scada_data_type"
    __table_args__ = (
        UniqueConstraint("type_name", name="uq_data_type_name"),
        {"comment": "SCADA 数据类型"},
    )

    data_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="数据类型主键")
    type_name: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, comment="类型名称：BOOLEAN / INT32 / INT64 / FLOAT32 / FLOAT64 / STRING / DATETIME / JSON"
    )
    encoding: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="编码方式：IEC61850_BASIC / OPCUA_VARIANT / MODBUS_REGISTER"
    )
    size_bits: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="位宽")
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="值域约束 SQL 条件语句，如 CHECK(value BETWEEN -3.4E38 AND 3.4E38) / CHECK(value IN (0,1)) / CHECK(LENGTH(value) <= 255)"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="扩展信息，如 协议类型映射、序列化规则"
    )


class CDCDict(Base):
    """CDC 字典 — 解释 IEC 61850 公共数据类."""

    __tablename__ = "scada_cdc_dict"
    __table_args__ = (
        UniqueConstraint("cdc_code", name="uq_cdc_code"),
        {"comment": "CDC 字典"},
    )

    cdc_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="CDC 主键")
    cdc_code: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, comment="CDC 编码：MV / SPS / INS / ACT / DPC 等"
    )
    cdc_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="CDC 英文全称")
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="中文说明")


class FCDict(Base):
    """FC 字典 — 解释 IEC 61850 功能约束."""

    __tablename__ = "scada_fc_dict"
    __table_args__ = (
        UniqueConstraint("fc_code", name="uq_fc_code"),
        {"comment": "FC 字典"},
    )

    fc_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="FC 主键")
    fc_code: Mapped[str] = mapped_column(
        String(8), unique=True, nullable=False, comment="FC 编码：ST / MX / SP / SV / CF / DC / EX"
    )
    fc_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="FC 英文全称")
    description: Mapped[Optional[str]] = mapped_column(String(512), nullable=True, comment="中文说明")
