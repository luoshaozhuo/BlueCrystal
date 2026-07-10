from typing import Any, Optional
import datetime
import decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Column, Date, DateTime, ForeignKeyConstraint, Identity, Integer, Numeric, PrimaryKeyConstraint, Table, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class AstManufacturer(Base):
    __tablename__ = 'ast_manufacturer'
    __table_args__ = (
        PrimaryKeyConstraint('ast_manufacturer_id', name='ast_manufacturer_pkey'),
        UniqueConstraint('manufacturer_identifier', 'record_revision', name='ast_manufacturer_manufacturer_identifier_record_revision_key'),
        {'comment': '【主数据】制造商主数据。表示风机、逆变器、储能、箱变、通信设备等设备制造商。', 'schema': 'whale'}
    )

    ast_manufacturer_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    manufacturer_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='制造商业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='制造商中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='制造商英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='制造商中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='制造商英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    ast_asset_model: Mapped[list['AstAssetModel']] = relationship('AstAssetModel', back_populates='manufacturer')


class CfgAdsPointTable(Base):
    __tablename__ = 'cfg_ads_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_ads_point_table_id', name='cfg_ads_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_ads_point_table_point_table_identifier_record_revision_key'),
        {'comment': '【配置数据】ADS 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_ads_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_ads_point_item: Mapped[list['CfgAdsPointItem']] = relationship('CfgAdsPointItem', back_populates='cfg_ads_point_table')
    cfg_ads_conn: Mapped[list['CfgAdsConn']] = relationship('CfgAdsConn', back_populates='cfg_ads_point_table')


class CfgHttpRestPointTable(Base):
    __tablename__ = 'cfg_http_rest_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_http_rest_point_table_id', name='cfg_http_rest_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_http_rest_point_table_point_table_identifier_record_rev_key'),
        {'comment': '【配置数据】HTTP REST 设备能力点表。表示第三方系统或平台接口可提供的 REST 资源、指标、控制接口和响应字段全集快照。',
     'schema': 'whale'}
    )

    cfg_http_rest_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_http_rest_point_item: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', back_populates='cfg_http_rest_point_table')
    cfg_http_rest_conn: Mapped[list['CfgHttpRestConn']] = relationship('CfgHttpRestConn', back_populates='cfg_http_rest_point_table')


class CfgIec101PointTable(Base):
    __tablename__ = 'cfg_iec101_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_iec101_point_table_id', name='cfg_iec101_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_iec101_point_table_point_table_identifier_record_revisi_key'),
        {'comment': '【配置数据】IEC101 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_iec101_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_iec101_point_item: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', back_populates='cfg_iec101_point_table')
    cfg_iec101_conn: Mapped[list['CfgIec101Conn']] = relationship('CfgIec101Conn', back_populates='cfg_iec101_point_table')


class CfgIec104PointTable(Base):
    __tablename__ = 'cfg_iec104_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_iec104_point_table_id', name='cfg_iec104_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_iec104_point_table_point_table_identifier_record_revisi_key'),
        {'comment': '【配置数据】IEC104 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_iec104_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_iec104_point_item: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', back_populates='cfg_iec104_point_table')
    cfg_iec104_conn: Mapped[list['CfgIec104Conn']] = relationship('CfgIec104Conn', back_populates='cfg_iec104_point_table')


class CfgIec61850GoosePointTable(Base):
    __tablename__ = 'cfg_iec61850_goose_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_iec61850_goose_point_table_id', name='cfg_iec61850_goose_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_iec61850_goose_point_tabl_point_table_identifier_record_key'),
        {'comment': '【配置数据】IEC61850 GOOSE 设备能力点表。表示某协议连接可提供的接入量全集快照。',
     'schema': 'whale'}
    )

    cfg_iec61850_goose_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_iec61850_goose_point_item: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', back_populates='cfg_iec61850_goose_point_table')
    cfg_iec61850_goose_conn: Mapped[list['CfgIec61850GooseConn']] = relationship('CfgIec61850GooseConn', back_populates='cfg_iec61850_goose_point_table')


class CfgIec61850MmsPointTable(Base):
    __tablename__ = 'cfg_iec61850_mms_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_iec61850_mms_point_table_id', name='cfg_iec61850_mms_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_iec61850_mms_point_table_point_table_identifier_record__key'),
        {'comment': '【配置数据】IEC61850 MMS 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_iec61850_mms_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_iec61850_mms_point_item: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', back_populates='cfg_iec61850_mms_point_table')
    cfg_iec61850_mms_conn: Mapped[list['CfgIec61850MmsConn']] = relationship('CfgIec61850MmsConn', back_populates='cfg_iec61850_mms_point_table')


class CfgIec61850SvPointTable(Base):
    __tablename__ = 'cfg_iec61850_sv_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_iec61850_sv_point_table_id', name='cfg_iec61850_sv_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_iec61850_sv_point_table_point_table_identifier_record_r_key'),
        {'comment': '【配置数据】IEC61850 SV 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_iec61850_sv_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_iec61850_sv_point_item: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', back_populates='cfg_iec61850_sv_point_table')
    cfg_iec61850_sv_conn: Mapped[list['CfgIec61850SvConn']] = relationship('CfgIec61850SvConn', back_populates='cfg_iec61850_sv_point_table')


class CfgModbusPointTable(Base):
    __tablename__ = 'cfg_modbus_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_modbus_point_table_id', name='cfg_modbus_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_modbus_point_table_point_table_identifier_record_revisi_key'),
        {'comment': '【配置数据】Modbus 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_modbus_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_modbus_point_item: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', back_populates='cfg_modbus_point_table')
    cfg_modbus_conn: Mapped[list['CfgModbusConn']] = relationship('CfgModbusConn', back_populates='cfg_modbus_point_table')


class CfgMqttPointTable(Base):
    __tablename__ = 'cfg_mqtt_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_mqtt_point_table_id', name='cfg_mqtt_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_mqtt_point_table_point_table_identifier_record_revision_key'),
        {'comment': '【配置数据】MQTT 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_mqtt_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_mqtt_point_item: Mapped[list['CfgMqttPointItem']] = relationship('CfgMqttPointItem', back_populates='cfg_mqtt_point_table')
    cfg_mqtt_conn: Mapped[list['CfgMqttConn']] = relationship('CfgMqttConn', back_populates='cfg_mqtt_point_table')


class CfgOpcuaPointTable(Base):
    __tablename__ = 'cfg_opcua_point_table'
    __table_args__ = (
        PrimaryKeyConstraint('cfg_opcua_point_table_id', name='cfg_opcua_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='cfg_opcua_point_table_point_table_identifier_record_revisio_key'),
        {'comment': '【配置数据】OPC UA 设备能力点表。表示某协议连接可提供的接入量全集快照。', 'schema': 'whale'}
    )

    cfg_opcua_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 点表业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_opcua_point_item: Mapped[list['CfgOpcuaPointItem']] = relationship('CfgOpcuaPointItem', back_populates='cfg_opcua_point_table')
    cfg_opcua_conn: Mapped[list['CfgOpcuaConn']] = relationship('CfgOpcuaConn', back_populates='cfg_opcua_point_table')


class RefCode(Base):
    __tablename__ = 'ref_code'
    __table_args__ = (
        PrimaryKeyConstraint('ref_code_id', name='ref_code_pkey'),
        UniqueConstraint('ref_type', 'code', name='ref_code_ref_type_code_key'),
        {'comment': '【参考数据】参考代码表。保存协议类型、表角色、组织性质、资产类型、任务类型、拓扑元素类型、状态和协议枚举码等小型稳定枚举。',
     'schema': 'whale'}
    )

    ref_code_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    ref_type: Mapped[str] = mapped_column(Text, nullable=False, comment='参考代码类型，例如 PROTOCOL、ASSET_TYPE、UNIT、DATA_TYPE；不是表名。')
    code: Mapped[str] = mapped_column(Text, nullable=False, comment='参考代码值；仅 ref_code 表使用 code 表示枚举码，同一 ref_type 下唯一。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='中文名称，用于中文界面、导入模板和运维查看。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='英文名称，用于英文界面、接口和导出文件。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='中文说明，不得为空。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='英文说明，不得为空。')
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='同一参考代码类型下的展示排序。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否启用该参考代码。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录最后更新时间。')
    updated_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录最后更新人或系统账号。')
    abbr_en: Mapped[Optional[str]] = mapped_column(Text, comment='英文缩写，可为空。')

    ast_asset_model: Mapped[list['AstAssetModel']] = relationship('AstAssetModel', back_populates='asset_type_ref')
    ast_asset_param_def_asset_type_ref: Mapped[list['AstAssetParamDef']] = relationship('AstAssetParamDef', foreign_keys='[AstAssetParamDef.asset_type_ref_id]', back_populates='asset_type_ref')
    ast_asset_param_def_data_type_ref: Mapped[list['AstAssetParamDef']] = relationship('AstAssetParamDef', foreign_keys='[AstAssetParamDef.data_type_ref_id]', back_populates='data_type_ref')
    ast_asset_param_def_unit_ref: Mapped[list['AstAssetParamDef']] = relationship('AstAssetParamDef', foreign_keys='[AstAssetParamDef.unit_ref_id]', back_populates='unit_ref')
    cfg_measurement_semantic_physical_quantity_category_ref: Mapped[list['CfgMeasurementSemantic']] = relationship('CfgMeasurementSemantic', foreign_keys='[CfgMeasurementSemantic.physical_quantity_category_ref_id]', back_populates='physical_quantity_category_ref')
    cfg_measurement_semantic_standard_data_type_ref: Mapped[list['CfgMeasurementSemantic']] = relationship('CfgMeasurementSemantic', foreign_keys='[CfgMeasurementSemantic.standard_data_type_ref_id]', back_populates='standard_data_type_ref')
    cfg_measurement_semantic_standard_unit_ref: Mapped[list['CfgMeasurementSemantic']] = relationship('CfgMeasurementSemantic', foreign_keys='[CfgMeasurementSemantic.standard_unit_ref_id]', back_populates='standard_unit_ref')
    cfg_protocol_operation_def_operation_direction_ref: Mapped[list['CfgProtocolOperationDef']] = relationship('CfgProtocolOperationDef', foreign_keys='[CfgProtocolOperationDef.operation_direction_ref_id]', back_populates='operation_direction_ref')
    cfg_protocol_operation_def_operation_semantic_ref: Mapped[list['CfgProtocolOperationDef']] = relationship('CfgProtocolOperationDef', foreign_keys='[CfgProtocolOperationDef.operation_semantic_ref_id]', back_populates='operation_semantic_ref')
    cfg_protocol_operation_def_protocol_ref: Mapped[list['CfgProtocolOperationDef']] = relationship('CfgProtocolOperationDef', foreign_keys='[CfgProtocolOperationDef.protocol_ref_id]', back_populates='protocol_ref')
    cfg_protocol_operation_def_request_response_mode_ref: Mapped[list['CfgProtocolOperationDef']] = relationship('CfgProtocolOperationDef', foreign_keys='[CfgProtocolOperationDef.request_response_mode_ref_id]', back_populates='request_response_mode_ref')
    cfg_protocol_table_registry_protocol_ref: Mapped[list['CfgProtocolTableRegistry']] = relationship('CfgProtocolTableRegistry', foreign_keys='[CfgProtocolTableRegistry.protocol_ref_id]', back_populates='protocol_ref')
    cfg_protocol_table_registry_table_role_ref: Mapped[list['CfgProtocolTableRegistry']] = relationship('CfgProtocolTableRegistry', foreign_keys='[CfgProtocolTableRegistry.table_role_ref_id]', back_populates='table_role_ref')
    org_unit: Mapped[list['OrgUnit']] = relationship('OrgUnit', back_populates='org_nature_ref')
    sec_permission_permission_code_ref: Mapped[list['SecPermission']] = relationship('SecPermission', foreign_keys='[SecPermission.permission_code_ref_id]', back_populates='permission_code_ref')
    sec_permission_permission_type_ref: Mapped[list['SecPermission']] = relationship('SecPermission', foreign_keys='[SecPermission.permission_type_ref_id]', back_populates='permission_type_ref')
    task: Mapped[list['Task']] = relationship('Task', back_populates='task_status_ref')
    task_param_def_data_type_ref: Mapped[list['TaskParamDef']] = relationship('TaskParamDef', foreign_keys='[TaskParamDef.data_type_ref_id]', back_populates='data_type_ref')
    task_param_def_task_type_ref: Mapped[list['TaskParamDef']] = relationship('TaskParamDef', foreign_keys='[TaskParamDef.task_type_ref_id]', back_populates='task_type_ref')
    task_point_table: Mapped[list['TaskPointTable']] = relationship('TaskPointTable', back_populates='point_table_usage_ref')
    cfg_ads_point_item_engineering_unit_ref: Mapped[list['CfgAdsPointItem']] = relationship('CfgAdsPointItem', foreign_keys='[CfgAdsPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_ads_point_item_protocol_data_type_ref: Mapped[list['CfgAdsPointItem']] = relationship('CfgAdsPointItem', foreign_keys='[CfgAdsPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_http_rest_point_item_engineering_unit_ref: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', foreign_keys='[CfgHttpRestPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_http_rest_point_item_http_method_ref: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', foreign_keys='[CfgHttpRestPointItem.http_method_ref_id]', back_populates='http_method_ref')
    cfg_http_rest_point_item_payload_format_ref: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', foreign_keys='[CfgHttpRestPointItem.payload_format_ref_id]', back_populates='payload_format_ref')
    cfg_http_rest_point_item_protocol_data_type_ref: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', foreign_keys='[CfgHttpRestPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec101_point_item_cause_of_transmission_ref: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', foreign_keys='[CfgIec101PointItem.cause_of_transmission_ref_id]', back_populates='cause_of_transmission_ref')
    cfg_iec101_point_item_engineering_unit_ref: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', foreign_keys='[CfgIec101PointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_iec101_point_item_protocol_data_type_ref: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', foreign_keys='[CfgIec101PointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec101_point_item_type_ref: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', foreign_keys='[CfgIec101PointItem.type_id_ref_id]', back_populates='type_ref')
    cfg_iec104_point_item_cause_of_transmission_ref: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', foreign_keys='[CfgIec104PointItem.cause_of_transmission_ref_id]', back_populates='cause_of_transmission_ref')
    cfg_iec104_point_item_engineering_unit_ref: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', foreign_keys='[CfgIec104PointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_iec104_point_item_protocol_data_type_ref: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', foreign_keys='[CfgIec104PointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec104_point_item_type_ref: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', foreign_keys='[CfgIec104PointItem.type_id_ref_id]', back_populates='type_ref')
    cfg_iec61850_goose_point_item_btype_ref: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', foreign_keys='[CfgIec61850GoosePointItem.btype_ref_id]', back_populates='btype_ref')
    cfg_iec61850_goose_point_item_cdc_ref: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', foreign_keys='[CfgIec61850GoosePointItem.cdc_ref_id]', back_populates='cdc_ref')
    cfg_iec61850_goose_point_item_engineering_unit_ref: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', foreign_keys='[CfgIec61850GoosePointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_iec61850_goose_point_item_protocol_data_type_ref: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', foreign_keys='[CfgIec61850GoosePointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec61850_mms_point_item_cdc_ref: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', foreign_keys='[CfgIec61850MmsPointItem.cdc_ref_id]', back_populates='cdc_ref')
    cfg_iec61850_mms_point_item_engineering_unit_ref: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', foreign_keys='[CfgIec61850MmsPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_iec61850_mms_point_item_fc_ref: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', foreign_keys='[CfgIec61850MmsPointItem.fc_ref_id]', back_populates='fc_ref')
    cfg_iec61850_mms_point_item_protocol_data_type_ref: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', foreign_keys='[CfgIec61850MmsPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec61850_sv_point_item_btype_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.btype_ref_id]', back_populates='btype_ref')
    cfg_iec61850_sv_point_item_cdc_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.cdc_ref_id]', back_populates='cdc_ref')
    cfg_iec61850_sv_point_item_engineering_unit_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_iec61850_sv_point_item_phase_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.phase_ref_id]', back_populates='phase_ref')
    cfg_iec61850_sv_point_item_protocol_data_type_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_iec61850_sv_point_item_quantity_ref: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', foreign_keys='[CfgIec61850SvPointItem.quantity_ref_id]', back_populates='quantity_ref')
    cfg_modbus_point_item_byte_order_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.byte_order_ref_id]', back_populates='byte_order_ref')
    cfg_modbus_point_item_engineering_unit_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_modbus_point_item_function_code_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.function_code_ref_id]', back_populates='function_code_ref')
    cfg_modbus_point_item_protocol_data_type_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_modbus_point_item_register_area_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.register_area_ref_id]', back_populates='register_area_ref')
    cfg_modbus_point_item_word_order_ref: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', foreign_keys='[CfgModbusPointItem.word_order_ref_id]', back_populates='word_order_ref')
    cfg_mqtt_point_item_engineering_unit_ref: Mapped[list['CfgMqttPointItem']] = relationship('CfgMqttPointItem', foreign_keys='[CfgMqttPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_mqtt_point_item_payload_format_ref: Mapped[list['CfgMqttPointItem']] = relationship('CfgMqttPointItem', foreign_keys='[CfgMqttPointItem.payload_format_ref_id]', back_populates='payload_format_ref')
    cfg_mqtt_point_item_protocol_data_type_ref: Mapped[list['CfgMqttPointItem']] = relationship('CfgMqttPointItem', foreign_keys='[CfgMqttPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_opcua_point_item_engineering_unit_ref: Mapped[list['CfgOpcuaPointItem']] = relationship('CfgOpcuaPointItem', foreign_keys='[CfgOpcuaPointItem.engineering_unit_ref_id]', back_populates='engineering_unit_ref')
    cfg_opcua_point_item_protocol_data_type_ref: Mapped[list['CfgOpcuaPointItem']] = relationship('CfgOpcuaPointItem', foreign_keys='[CfgOpcuaPointItem.protocol_data_type_ref_id]', back_populates='protocol_data_type_ref')
    cfg_protocol_task_type_mapping_point_table_usage_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.point_table_usage_ref_id]', back_populates='point_table_usage_ref')
    cfg_protocol_task_type_mapping_protocol_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.protocol_ref_id]', back_populates='protocol_ref')
    cfg_protocol_task_type_mapping_task_category_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.task_category_ref_id]', back_populates='task_category_ref')
    cfg_protocol_task_type_mapping_task_direction_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.task_direction_ref_id]', back_populates='task_direction_ref')
    cfg_protocol_task_type_mapping_task_protocol_role_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.task_protocol_role_ref_id]', back_populates='task_protocol_role_ref')
    cfg_protocol_task_type_mapping_task_type_ref: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', foreign_keys='[CfgProtocolTaskTypeMapping.task_type_ref_id]', back_populates='task_type_ref')
    org_power_plant: Mapped[list['OrgPowerPlant']] = relationship('OrgPowerPlant', back_populates='plant_type_ref')
    task_point_item_point_role_ref: Mapped[list['TaskPointItem']] = relationship('TaskPointItem', foreign_keys='[TaskPointItem.point_role_ref_id]', back_populates='point_role_ref')
    task_point_item_protocol_ref: Mapped[list['TaskPointItem']] = relationship('TaskPointItem', foreign_keys='[TaskPointItem.protocol_ref_id]', back_populates='protocol_ref')
    task_point_item_sample_mode_ref: Mapped[list['TaskPointItem']] = relationship('TaskPointItem', foreign_keys='[TaskPointItem.sample_mode_ref_id]', back_populates='sample_mode_ref')
    ast_asset_asset_lifecycle_status_ref: Mapped[list['AstAsset']] = relationship('AstAsset', foreign_keys='[AstAsset.asset_lifecycle_status_ref_id]', back_populates='asset_lifecycle_status_ref')
    ast_asset_asset_type_ref: Mapped[list['AstAsset']] = relationship('AstAsset', foreign_keys='[AstAsset.asset_type_ref_id]', back_populates='asset_type_ref')
    org_work_team: Mapped[list['OrgWorkTeam']] = relationship('OrgWorkTeam', back_populates='work_team_type_ref')
    ast_asset_maintenance_event_event_status_ref: Mapped[list['AstAssetMaintenanceEvent']] = relationship('AstAssetMaintenanceEvent', foreign_keys='[AstAssetMaintenanceEvent.event_status_ref_id]', back_populates='event_status_ref')
    ast_asset_maintenance_event_event_type_ref: Mapped[list['AstAssetMaintenanceEvent']] = relationship('AstAssetMaintenanceEvent', foreign_keys='[AstAssetMaintenanceEvent.event_type_ref_id]', back_populates='event_type_ref')
    cfg_connection: Mapped[list['CfgConnection']] = relationship('CfgConnection', back_populates='protocol_ref')
    geo_location: Mapped[list['GeoLocation']] = relationship('GeoLocation', back_populates='model_file_format_ref')
    topo_comm_element_element_kind_ref: Mapped[list['TopoCommElement']] = relationship('TopoCommElement', foreign_keys='[TopoCommElement.element_kind_ref_id]', back_populates='element_kind_ref')
    topo_comm_element_element_type_ref: Mapped[list['TopoCommElement']] = relationship('TopoCommElement', foreign_keys='[TopoCommElement.element_type_ref_id]', back_populates='element_type_ref')
    topo_elec_element_element_kind_ref: Mapped[list['TopoElecElement']] = relationship('TopoElecElement', foreign_keys='[TopoElecElement.element_kind_ref_id]', back_populates='element_kind_ref')
    topo_elec_element_element_type_ref: Mapped[list['TopoElecElement']] = relationship('TopoElecElement', foreign_keys='[TopoElecElement.element_type_ref_id]', back_populates='element_type_ref')
    cfg_connection_status_event: Mapped[list['CfgConnectionStatusEvent']] = relationship('CfgConnectionStatusEvent', back_populates='connection_status_ref')
    cfg_grid_dispatch_connection_channel_role_ref: Mapped[list['CfgGridDispatchConnection']] = relationship('CfgGridDispatchConnection', foreign_keys='[CfgGridDispatchConnection.channel_role_ref_id]', back_populates='channel_role_ref')
    cfg_grid_dispatch_connection_dispatch_level_ref: Mapped[list['CfgGridDispatchConnection']] = relationship('CfgGridDispatchConnection', foreign_keys='[CfgGridDispatchConnection.dispatch_level_ref_id]', back_populates='dispatch_level_ref')
    cfg_http_rest_conn: Mapped[list['CfgHttpRestConn']] = relationship('CfgHttpRestConn', back_populates='auth_type_ref')
    cfg_modbus_conn: Mapped[list['CfgModbusConn']] = relationship('CfgModbusConn', back_populates='transport_ref')
    cfg_opcua_conn_security_mode_ref: Mapped[list['CfgOpcuaConn']] = relationship('CfgOpcuaConn', foreign_keys='[CfgOpcuaConn.security_mode_ref_id]', back_populates='security_mode_ref')
    cfg_opcua_conn_security_policy_ref: Mapped[list['CfgOpcuaConn']] = relationship('CfgOpcuaConn', foreign_keys='[CfgOpcuaConn.security_policy_ref_id]', back_populates='security_policy_ref')
    task_config: Mapped[list['TaskConfig']] = relationship('TaskConfig', back_populates='trigger_mode_ref')
    task_run_run_scope_ref: Mapped[list['TaskRun']] = relationship('TaskRun', foreign_keys='[TaskRun.run_scope_ref_id]', back_populates='run_scope_ref')
    task_run_run_status_ref: Mapped[list['TaskRun']] = relationship('TaskRun', foreign_keys='[TaskRun.run_status_ref_id]', back_populates='run_status_ref')


class SecRole(Base):
    __tablename__ = 'sec_role'
    __table_args__ = (
        PrimaryKeyConstraint('sec_role_id', name='sec_role_pkey'),
        UniqueConstraint('role_identifier', 'record_revision', name='sec_role_role_identifier_record_revision_key'),
        {'comment': '【安全主数据】角色主数据。定义员工可被分配的角色集合，角色再关联权限。', 'schema': 'whale'}
    )

    sec_role_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    role_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='角色业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='角色中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='角色英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='角色中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='角色英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    sec_role_permission: Mapped[list['SecRolePermission']] = relationship('SecRolePermission', back_populates='role')
    sec_employee_role: Mapped[list['SecEmployeeRole']] = relationship('SecEmployeeRole', back_populates='role')


t_vw_ads_point_item = Table(
    'vw_ads_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('symbol_name', Text, comment='ADS 变量符号名，对应 pyads read_by_name/write_by_name 参数。'),
    Column('index_group', Integer, comment='ADS index group。'),
    Column('index_offset', Integer, comment='ADS index offset。'),
    Column('plc_datatype', Text, comment='pyads PLC datatype 参数。'),
    Column('array_length', Integer, comment='数组长度；标量可为空或 1。'),
    schema='whale',
    comment='【配置数据】ADS 点位执行视图。table_id 表示 cfg_ads_point_table_id；point_item_id 才是点位主键。plc_datatype 对应 pyads datatype 参数。'
)


t_vw_asset_full = Table(
    'vw_asset_full', Base.metadata,
    Column('asset_id', BigInteger, comment='资产主键，来自 ast_asset.ast_asset_id。'),
    Column('asset_identifier', Text, comment='场站或系统内部分配的资产唯一标识，来自 ast_asset.asset_identifier。'),
    Column('asset_name', Text, comment='资产中文名称，来自 ast_asset.name_zh。'),
    Column('asset_type_code', Text, comment='资产类型 code，来自 ref_code.ref_type=ASSET_TYPE。'),
    Column('asset_type_name', Text, comment='资产类型中文名，来自 ref_code.name_zh。'),
    Column('asset_model', Text, comment='资产型号标识，来自 ast_asset_model.model_identifier。'),
    Column('manufacturer_name', Text, comment='生产厂家中文名，来自 ast_manufacturer.name_zh。'),
    Column('production_date', Date, comment='生产日期，来自 ast_asset.production_date。'),
    Column('installation_date', Date, comment='现场安装日期，来自 ast_asset.installation_date。'),
    Column('commissioning_date', Date, comment='启用或投运日期，来自 ast_asset.commissioning_date。'),
    schema='whale',
    comment='【主数据】使用中资产视图。只展示当前使用中的真实资产核心台账字段。'
)


t_vw_asset_position_full = Table(
    'vw_asset_position_full', Base.metadata,
    Column('asset_id', BigInteger, comment='兼容字段，与 vw_geo_location.asset_id 含义一致。'),
    Column('asset_identifier', Text, comment='兼容字段，与 vw_geo_location.asset_identifier 含义一致。'),
    Column('asset_type_code', Text, comment='兼容字段，与 vw_geo_location.asset_type_code 含义一致。'),
    Column('asset_type_name', Text, comment='兼容字段，与 vw_geo_location.asset_type_name 含义一致。'),
    Column('coordinate_system', Text, comment='兼容字段，与 vw_geo_location.coordinate_system 含义一致。'),
    Column('longitude', Numeric(12, 8), comment='兼容字段，与 vw_geo_location.longitude 含义一致。'),
    Column('latitude', Numeric(12, 8), comment='兼容字段，与 vw_geo_location.latitude 含义一致。'),
    Column('altitude_m', Numeric(12, 3), comment='兼容字段，与 vw_geo_location.altitude_m 含义一致。'),
    Column('coordinate_x', Numeric(14, 4), comment='兼容字段，与 vw_geo_location.coordinate_x 含义一致。'),
    Column('coordinate_y', Numeric(14, 4), comment='兼容字段，与 vw_geo_location.coordinate_y 含义一致。'),
    Column('height_m', Numeric(12, 3), comment='兼容字段，与 vw_geo_location.height_m 含义一致。'),
    Column('rotation_x', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.rotation_x 含义一致。'),
    Column('rotation_y', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.rotation_y 含义一致。'),
    Column('rotation_z', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.rotation_z 含义一致。'),
    Column('scale_x', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.scale_x 含义一致。'),
    Column('scale_y', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.scale_y 含义一致。'),
    Column('scale_z', Numeric(10, 4), comment='兼容字段，与 vw_geo_location.scale_z 含义一致。'),
    Column('model_file_name', Text, comment='兼容字段，与 vw_geo_location.model_file_name 含义一致。'),
    schema='whale',
    comment='【主数据】资产三维位置兼容视图。字段与 vw_geo_location 相同，保留用于兼容旧命名。'
)


t_vw_connection_object_full = Table(
    'vw_connection_object_full', Base.metadata,
    Column('connection_id', BigInteger, comment='通用连接主键，来自 cfg_connection.cfg_connection_id；用于关联 vw_task_full.connection_id。'),
    Column('asset_id', BigInteger, comment='连接对象资产主键，来自 ast_asset.ast_asset_id。'),
    Column('asset_identifier', Text, comment='连接对象资产业务标识，来自 ast_asset.asset_identifier。'),
    Column('asset_name', Text, comment='连接对象资产中文名称，来自 ast_asset.name_zh。'),
    Column('asset_type_code', Text, comment='资产类型 code，来自 ref_code.ref_type=ASSET_TYPE。'),
    Column('asset_type_name', Text, comment='资产类型中文名，来自 ref_code.name_zh。'),
    Column('protocol', Text, comment='连接使用的协议 code，来自 ref_code.ref_type=PROTOCOL。'),
    Column('cfg_xxx_conn_table_name', Text, comment='协议专属连接参数表名，例如 cfg_modbus_conn。'),
    Column('cfg_xxx_conn_id', BigInteger, comment='协议专属连接表主键，同时等于 cfg_connection_id。'),
    Column('connection_params_json', JSONB, comment='协议连接参数 JSON，外部程序可直接用于建立协议连接。'),
    Column('point_item_view_name', Text, comment='该协议对应的点位执行视图名。'),
    schema='whale',
    comment='【配置数据】连接对象执行视图。外部程序通过 connection_id 获取资产、协议、协议连接表定位与 connection_params_json。'
)


t_vw_employee_full = Table(
    'vw_employee_full', Base.metadata,
    Column('employee_id', BigInteger, comment='员工主键，来自 emp_employee.emp_employee_id。'),
    Column('power_plant_id', BigInteger, comment='所属风光储电场主键，来自 emp_employee.power_plant_id。'),
    Column('employee_name', Text, comment='员工中文姓名，来自 emp_employee.name_zh。'),
    Column('role_name', Text, comment='系统角色标识，来自 sec_role.role_identifier。'),
    Column('permission_name', Text, comment='权限标识，来自 sec_permission.permission_identifier。'),
    Column('on_duty', Boolean, comment='是否当班，来自 emp_employee.on_duty；不同于 in_service。'),
    schema='whale',
    comment='【主数据】在职员工权限视图。只展示在职员工、角色和权限。'
)


t_vw_geo_location = Table(
    'vw_geo_location', Base.metadata,
    Column('asset_id', BigInteger, comment='资产主键，来自 geo_location.asset_id 关联 ast_asset.ast_asset_id。'),
    Column('asset_identifier', Text, comment='资产业务标识，来自 ast_asset.asset_identifier。'),
    Column('asset_type_code', Text, comment='资产类型 code，来自 ref_code.ref_type=ASSET_TYPE。'),
    Column('asset_type_name', Text, comment='资产类型中文名，来自 ref_code.name_zh。'),
    Column('coordinate_system', Text, comment='坐标系，来自 geo_location.coordinate_system。'),
    Column('longitude', Numeric(12, 8), comment='经度，来自 geo_location.longitude。'),
    Column('latitude', Numeric(12, 8), comment='纬度，来自 geo_location.latitude。'),
    Column('altitude_m', Numeric(12, 3), comment='海拔高程，单位米，来自 geo_location.altitude_m。'),
    Column('coordinate_x', Numeric(14, 4), comment='场站平面或投影坐标 X，来自 geo_location.coordinate_x。'),
    Column('coordinate_y', Numeric(14, 4), comment='场站平面或投影坐标 Y，来自 geo_location.coordinate_y。'),
    Column('height_m', Numeric(12, 3), comment='设备或模型高度，单位米，来自 geo_location.height_m。'),
    Column('rotation_x', Numeric(10, 4), comment='三维模型绕 X 轴旋转角，来自 geo_location.rotation_x。'),
    Column('rotation_y', Numeric(10, 4), comment='三维模型绕 Y 轴旋转角，来自 geo_location.rotation_y。'),
    Column('rotation_z', Numeric(10, 4), comment='三维模型绕 Z 轴旋转角，来自 geo_location.rotation_z。'),
    Column('scale_x', Numeric(10, 4), comment='三维模型 X 方向缩放比例，来自 geo_location.scale_x。'),
    Column('scale_y', Numeric(10, 4), comment='三维模型 Y 方向缩放比例，来自 geo_location.scale_y。'),
    Column('scale_z', Numeric(10, 4), comment='三维模型 Z 方向缩放比例，来自 geo_location.scale_z。'),
    Column('model_file_name', Text, comment='三维模型文件名，来自 geo_location.model_file_name。'),
    schema='whale',
    comment='【主数据】资产三维位置视图。只展示最新版本、需要在三维图显示的大型真实资产位置、模型、旋转和缩放参数。'
)


t_vw_http_rest_point_item = Table(
    'vw_http_rest_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('http_method', Text, comment='HTTP 方法 code。'),
    Column('resource_path', Text, comment='HTTP REST 资源路径。'),
    Column('params_path', Text, comment='HTTP 请求查询参数路径，对应 httpx/requests params。'),
    Column('json_body_path', Text, comment='HTTP 请求 JSON body 字段路径，对应 httpx/requests json。'),
    Column('response_json_path', Text, comment='HTTP 响应 JSON 字段解析路径。'),
    Column('payload_encoding', Text, comment='载荷编码格式 code。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    schema='whale',
    comment='【配置数据】HTTP REST 点位执行视图。table_id 表示 cfg_http_rest_point_table_id；params_path/json_body_path/response_json_path 分别对应请求查询参数、请求 JSON 体和响应 JSON 解析路径。'
)


t_vw_iec101_point_item = Table(
    'vw_iec101_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('type_id', Text, comment='IEC101/IEC104 ASDU Type ID code。'),
    Column('common_address', Integer, comment='IEC101/IEC104 common address。'),
    Column('io_address', Integer, comment='IEC101/IEC104 information object address。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    Column('quality_descriptor_enabled', Boolean, comment='是否解析或生成质量描述位。'),
    schema='whale',
    comment='【配置数据】IEC101 点位执行视图。table_id 表示 cfg_iec101_point_table_id；io_address 是 IEC101 信息对象地址。'
)


t_vw_iec104_point_item = Table(
    'vw_iec104_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('type_id', Text, comment='IEC101/IEC104 ASDU Type ID code。'),
    Column('common_address', Integer, comment='IEC101/IEC104 common address。'),
    Column('io_address', Integer, comment='IEC101/IEC104 information object address。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    Column('quality_descriptor_enabled', Boolean, comment='是否解析或生成质量描述位。'),
    Column('time_tag_enabled', Boolean, comment='IEC104 点是否带时标。'),
    schema='whale',
    comment='【配置数据】IEC104 点位执行视图。table_id 表示 cfg_iec104_point_table_id；io_address 是 IEC104 信息对象地址。'
)


t_vw_iec61850_goose_point_item = Table(
    'vw_iec61850_goose_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('go_cb_ref', Text, comment='IEC61850 GOOSE control block reference。'),
    Column('dataset_ref', Text, comment='IEC61850 dataset reference。'),
    Column('member_index', Integer, comment='IEC61850 dataset 成员序号。'),
    Column('object_reference', Text, comment='IEC61850 对象引用，供 libiec61850 read/write/operate 使用。'),
    Column('cdc', Text, comment='IEC61850 common data class code。'),
    Column('btype', Text, comment='IEC61850 basic type / 协议基础类型 code。'),
    schema='whale',
    comment='【配置数据】IEC61850 GOOSE 点位执行视图。table_id 表示 cfg_iec61850_goose_point_table_id；连接级 app_id/interface 在 connection_params_json。'
)


t_vw_iec61850_mms_point_item = Table(
    'vw_iec61850_mms_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('logical_device', Text, comment='IEC61850 logical device。'),
    Column('logical_node', Text, comment='IEC61850 logical node。'),
    Column('data_object', Text, comment='IEC61850 data object。'),
    Column('data_attribute', Text, comment='IEC61850 data attribute。'),
    Column('object_reference', Text, comment='IEC61850 对象引用，供 libiec61850 read/write/operate 使用。'),
    Column('functional_constraint', Text, comment='IEC61850 functional constraint code。'),
    Column('cdc', Text, comment='IEC61850 common data class code。'),
    Column('btype', Text, comment='IEC61850 basic type / 协议基础类型 code。'),
    Column('data_attribute_path', Text, comment='IEC61850 数据属性路径。'),
    schema='whale',
    comment='【配置数据】IEC61850 MMS 点位执行视图。table_id 表示 cfg_iec61850_mms_point_table_id；字段名称遵循 IEC61850 语义。'
)


t_vw_iec61850_sv_point_item = Table(
    'vw_iec61850_sv_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('sv_id', Text, comment='IEC61850 SV stream/control identifier。'),
    Column('dataset_ref', Text, comment='IEC61850 dataset reference。'),
    Column('sample_channel', Text, comment='IEC61850 SV 采样通道。'),
    Column('sample_index', Integer, comment='IEC61850 SV 采样序号。'),
    Column('phase', Text, comment='相别 code。'),
    Column('quantity', Text, comment='采样量类型 code。'),
    Column('cdc', Text, comment='IEC61850 common data class code。'),
    Column('btype', Text, comment='IEC61850 basic type / 协议基础类型 code。'),
    schema='whale',
    comment='【配置数据】IEC61850 SV 点位执行视图。table_id 表示 cfg_iec61850_sv_point_table_id；连接级 sample_rate/app_id/interface 在 connection_params_json。'
)


t_vw_modbus_point_item = Table(
    'vw_modbus_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('function_code', Text, comment='MODBUS 功能码 code，用于驱动 facade 分派 read_coils/read_discrete_inputs/read_holding_registers/read_input_registers/write_*。'),
    Column('register_area', Text, comment='MODBUS 地址区 code。'),
    Column('address', Integer, comment='MODBUS API address 参数，来自 register_address。'),
    Column('count', Integer, comment='MODBUS API count 参数，来自 register_count。'),
    Column('bit_offset', Integer, comment='寄存器内位偏移；不适用时为空。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    Column('byte_order', Text, comment='MODBUS 字节序 code。'),
    Column('word_order', Text, comment='MODBUS 字序 code。'),
    schema='whale',
    comment='【配置数据】MODBUS 点位执行视图。table_id 表示 cfg_modbus_point_table_id；point_item_id 才是点位主键。字段名称尽量贴近 pymodbus API 参数。'
)


t_vw_mqtt_point_item = Table(
    'vw_mqtt_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('topic', Text, comment='MQTT topic。'),
    Column('payload_path', Text, comment='MQTT payload 字段路径。'),
    Column('payload_encoding', Text, comment='载荷编码格式 code。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    schema='whale',
    comment='【配置数据】MQTT 点位执行视图。table_id 表示 cfg_mqtt_point_table_id；qos/retain 属于连接或任务参数。'
)


t_vw_opcua_point_item = Table(
    'vw_opcua_point_item', Base.metadata,
    Column('point_item_id', BigInteger, comment='协议点位主键，来自对应 cfg_xxx_point_item_id；外部程序应使用该字段匹配 vw_task_full.point_item_ids_json。'),
    Column('table_id', BigInteger, comment='协议点表主键，来自对应 cfg_xxx_point_table_id；注意它不是点位主键。'),
    Column('point_identifier', Text, comment='协议点业务稳定标识，来自对应 cfg_xxx_point_item.point_identifier。'),
    Column('semantic_identifier', Text, comment='业务测量、状态、控制或发布语义标识，来自 cfg_measurement_semantic.measurement_identifier。'),
    Column('semantic_name', Text, comment='业务语义中文名，来自 cfg_measurement_semantic.name_zh。'),
    Column('unit_code', Text, comment='工程单位 code，来自 ref_code.ref_type=UNIT。'),
    Column('scale', Numeric(18, 8), comment='原始值转换为工程值的比例系数，来自 scale_factor。'),
    Column('offset_value', Numeric(18, 8), comment='原始值转换为工程值的偏移量。'),
    Column('value_min', Numeric(24, 8), comment='工程值允许下限。'),
    Column('value_max', Numeric(24, 8), comment='工程值允许上限。'),
    Column('allowed_values', Text, comment='离散工程值允许集合，逗号分隔。'),
    Column('namespace_index', Integer, comment='OPC UA namespace index。'),
    Column('namespace_uri', Text, comment='OPC UA namespace URI。'),
    Column('node_id', Text, comment='OPC UA NodeId。'),
    Column('browse_path', Text, comment='OPC UA browse path。'),
    Column('attribute_id', Integer, comment='OPC UA attribute id。'),
    Column('data_type', Text, comment='协议原始数据类型 code。'),
    Column('variant_type', Text, comment='OPC UA Variant 类型；当前由协议数据类型映射。'),
    Column('value_rank', Integer, comment='OPC UA value rank。'),
    Column('array_length', Integer, comment='数组长度；标量可为空或 1。'),
    schema='whale',
    comment='【配置数据】OPC UA 点位执行视图。table_id 表示 cfg_opcua_point_table_id；point_item_id 才是点位主键。字段名称贴近 asyncua Node API 参数。'
)


t_vw_task_full = Table(
    'vw_task_full', Base.metadata,
    Column('task_id', BigInteger, comment='任务主键，来自 task.task_id。'),
    Column('task_identifier', Text, comment='任务业务标识，来自 task.task_identifier。'),
    Column('connection_id', BigInteger, comment='任务使用的通用连接主键，来自 cfg_connection.cfg_connection_id，可关联 vw_connection_object_full.connection_id。'),
    Column('asset_id', BigInteger, comment='任务连接对象资产主键，来自 ast_asset.ast_asset_id。'),
    Column('asset_identifier', Text, comment='任务连接对象资产业务标识。'),
    Column('asset_name', Text, comment='任务连接对象资产中文名称。'),
    Column('asset_type_code', Text, comment='任务连接对象资产类型 code。'),
    Column('asset_type_name', Text, comment='任务连接对象资产类型中文名。'),
    Column('protocol', Text, comment='任务使用协议 code，来自 ref_code.ref_type=PROTOCOL。'),
    Column('task_type', Text, comment='平台任务类型 code，来自 ref_code.ref_type=TASK_TYPE。'),
    Column('task_status', Text, comment='任务人为状态 code，来自 ref_code.ref_type=TASK_STATUS。'),
    Column('start_date', Date, comment='任务生效开始日期，来自 task.valid_from。'),
    Column('end_date', Date, comment='任务生效结束日期，来自 task.valid_to。'),
    Column('task_item_count', BigInteger, comment='任务绑定的协议 point_item 数量，由 task_point_item 聚合得到。'),
    Column('task_params_json', JSONB, comment='任务运行参数 JSON，来自 task_config 与 task_param_value 聚合。'),
    Column('point_item_ids_json', JSONB, comment='任务绑定的协议点主键列表；对应各 vw_xxx_point_item.point_item_id，而不是 table_id。'),
    Column('point_item_view_name', Text, comment='任务对应的协议点位执行视图名，外部程序据此查询 point_item_ids_json。'),
    schema='whale',
    comment='【配置数据】任务执行视图。外部程序通过 connection_id、task_params_json、point_item_view_name、point_item_ids_json 执行任务，不需要访问原始任务表。'
)


t_vw_topo_comm_full = Table(
    'vw_topo_comm_full', Base.metadata,
    Column('topo_comm_connection_id', BigInteger, comment='通信拓扑连接主键。'),
    Column('from_node_name', Text, comment='起点通信节点名称。'),
    Column('from_interface_name', Text, comment='起点通信接口名称。'),
    Column('edge_name', Text, comment='通信链路名称。'),
    Column('to_interface_name', Text, comment='终点通信接口名称。'),
    Column('to_node_name', Text, comment='终点通信节点名称。'),
    Column('from_node_asset_id', BigInteger, comment='起点节点关联资产主键；纯拓扑节点可为空。'),
    Column('to_node_asset_id', BigInteger, comment='终点节点关联资产主键；纯拓扑节点可为空。'),
    schema='whale',
    comment='【配置数据】通信拓扑执行视图。按 node-interface-edge-interface-node 展示，字段名与注释保持一致。'
)


t_vw_topo_elec_full = Table(
    'vw_topo_elec_full', Base.metadata,
    Column('topo_elec_connection_id', BigInteger, comment='电气拓扑连接主键。'),
    Column('from_node_name', Text, comment='起点电气节点名称。'),
    Column('from_interface_name', Text, comment='起点电气接口名称。'),
    Column('edge_name', Text, comment='电气连接边名称。'),
    Column('to_interface_name', Text, comment='终点电气接口名称。'),
    Column('to_node_name', Text, comment='终点电气节点名称。'),
    Column('from_node_asset_id', BigInteger, comment='起点节点关联资产主键；母线/PCC/外部电网等纯拓扑节点可为空。'),
    Column('to_node_asset_id', BigInteger, comment='终点节点关联资产主键；母线/PCC/外部电网等纯拓扑节点可为空。'),
    schema='whale',
    comment='【配置数据】电气拓扑执行视图。按 node-interface-edge-interface-node 展示，字段名与注释保持一致。'
)


class AstAssetModel(Base):
    __tablename__ = 'ast_asset_model'
    __table_args__ = (
        ForeignKeyConstraint(['asset_type_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_model_asset_type_ref_id_fkey'),
        ForeignKeyConstraint(['manufacturer_id'], ['whale.ast_manufacturer.ast_manufacturer_id'], name='ast_asset_model_manufacturer_id_fkey'),
        PrimaryKeyConstraint('ast_asset_model_id', name='ast_asset_model_pkey'),
        UniqueConstraint('model_identifier', 'record_revision', name='ast_asset_model_model_identifier_record_revision_key'),
        {'comment': '【主数据】资产型号主数据。只描述型号身份、厂家和资产类型，不存额定功率等特有产品参数。', 'schema': 'whale'}
    )

    ast_asset_model_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    manufacturer_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='制造商主键。')
    asset_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产类型，取值来自 ref_code.ref_type=ASSET_TYPE。')
    model_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='具体产品型号或工程产品系列标识，例如 GE_2_5_120、SG250HX；不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='型号中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='型号英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='型号中文说明。特定产品参数不进入本表。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='型号英文说明。Product-specific parameters are not stored in this table.')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset_type_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='ast_asset_model')
    manufacturer: Mapped['AstManufacturer'] = relationship('AstManufacturer', back_populates='ast_asset_model')
    ast_asset: Mapped[list['AstAsset']] = relationship('AstAsset', back_populates='model')


class AstAssetParamDef(Base):
    __tablename__ = 'ast_asset_param_def'
    __table_args__ = (
        ForeignKeyConstraint(['asset_type_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_param_def_asset_type_ref_id_fkey'),
        ForeignKeyConstraint(['data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_param_def_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['unit_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_param_def_unit_ref_id_fkey'),
        PrimaryKeyConstraint('ast_asset_param_def_id', name='ast_asset_param_def_pkey'),
        UniqueConstraint('asset_type_ref_id', 'param_identifier', 'record_revision', name='ast_asset_param_def_asset_type_ref_id_param_identifier_reco_key'),
        {'comment': '【元数据】资产参数定义。定义不同资产类型可配置的额定功率、叶轮直径、电压等级等参数。', 'schema': 'whale'}
    )

    ast_asset_param_def_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    asset_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产类型，取值来自 ref_code.ref_type=ASSET_TYPE。')
    param_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='资产参数业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='资产参数中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='资产参数英文名称。')
    data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='参数数据类型，取值来自 ref_code.ref_type=DATA_TYPE。')
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='该参数是否为该资产类型的必填参数。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='参数英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    unit_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='参数单位，取值来自 ref_code.ref_type=UNIT；无单位时可为空。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[asset_type_ref_id], back_populates='ast_asset_param_def_asset_type_ref')
    data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[data_type_ref_id], back_populates='ast_asset_param_def_data_type_ref')
    unit_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[unit_ref_id], back_populates='ast_asset_param_def_unit_ref')
    ast_asset_param_value: Mapped[list['AstAssetParamValue']] = relationship('AstAssetParamValue', back_populates='asset_param_def')


class CfgMeasurementSemantic(Base):
    __tablename__ = 'cfg_measurement_semantic'
    __table_args__ = (
        ForeignKeyConstraint(['physical_quantity_category_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_measurement_semantic_physical_quantity_category_ref_id_fkey'),
        ForeignKeyConstraint(['standard_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_measurement_semantic_standard_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['standard_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_measurement_semantic_standard_unit_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_measurement_semantic_id', name='cfg_measurement_semantic_pkey'),
        UniqueConstraint('measurement_identifier', 'record_revision', name='cfg_measurement_semantic_measurement_identifier_record_revi_key'),
        {'comment': '【主数据】采集量语义主数据。定义跨协议、跨资产、跨任务复用的业务采集量语义标准目录，例如有功功率、风速、转速、电压和温度。',
     'schema': 'whale'}
    )

    cfg_measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    measurement_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='采集量语义业务稳定标识，不引用 ref_code.code。')
    standard_source: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'PROJECT'::text"), comment='采集量语义来源标准或项目来源，例如 GB/T 30966.2-2022。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='采集量语义中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='采集量语义英文名称。')
    physical_quantity_category_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='物理量类别，取值来自 ref_code.ref_type=PHYSICAL_QUANTITY_CATEGORY。')
    standard_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='标准单位，取值来自 ref_code.ref_type=UNIT。')
    standard_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='标准数据类型，取值来自 ref_code.ref_type=DATA_TYPE。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='采集量语义中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='采集量语义英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    logical_node_code: Mapped[Optional[str]] = mapped_column(Text, comment='来源于 IEC 61400-25 / GB/T 30966.2 等标准时的逻辑节点代码；非该类标准语义可为空。')
    data_object_name: Mapped[Optional[str]] = mapped_column(Text, comment='来源标准中的数据对象名或本项目扩展语义名。')
    cdc_code: Mapped[Optional[str]] = mapped_column(Text, comment='公共数据类或数据类别代码；未知或不适用时可为空。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    physical_quantity_category_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[physical_quantity_category_ref_id], back_populates='cfg_measurement_semantic_physical_quantity_category_ref')
    standard_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[standard_data_type_ref_id], back_populates='cfg_measurement_semantic_standard_data_type_ref')
    standard_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[standard_unit_ref_id], back_populates='cfg_measurement_semantic_standard_unit_ref')
    cfg_ads_point_item: Mapped[list['CfgAdsPointItem']] = relationship('CfgAdsPointItem', back_populates='measurement_semantic')
    cfg_http_rest_point_item: Mapped[list['CfgHttpRestPointItem']] = relationship('CfgHttpRestPointItem', back_populates='measurement_semantic')
    cfg_iec101_point_item: Mapped[list['CfgIec101PointItem']] = relationship('CfgIec101PointItem', back_populates='measurement_semantic')
    cfg_iec104_point_item: Mapped[list['CfgIec104PointItem']] = relationship('CfgIec104PointItem', back_populates='measurement_semantic')
    cfg_iec61850_goose_point_item: Mapped[list['CfgIec61850GoosePointItem']] = relationship('CfgIec61850GoosePointItem', back_populates='measurement_semantic')
    cfg_iec61850_mms_point_item: Mapped[list['CfgIec61850MmsPointItem']] = relationship('CfgIec61850MmsPointItem', back_populates='measurement_semantic')
    cfg_iec61850_sv_point_item: Mapped[list['CfgIec61850SvPointItem']] = relationship('CfgIec61850SvPointItem', back_populates='measurement_semantic')
    cfg_modbus_point_item: Mapped[list['CfgModbusPointItem']] = relationship('CfgModbusPointItem', back_populates='measurement_semantic')
    cfg_mqtt_point_item: Mapped[list['CfgMqttPointItem']] = relationship('CfgMqttPointItem', back_populates='measurement_semantic')
    cfg_opcua_point_item: Mapped[list['CfgOpcuaPointItem']] = relationship('CfgOpcuaPointItem', back_populates='measurement_semantic')


class CfgProtocolOperationDef(Base):
    __tablename__ = 'cfg_protocol_operation_def'
    __table_args__ = (
        ForeignKeyConstraint(['operation_direction_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_operation_def_operation_direction_ref_id_fkey'),
        ForeignKeyConstraint(['operation_semantic_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_operation_def_operation_semantic_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_operation_def_protocol_ref_id_fkey'),
        ForeignKeyConstraint(['request_response_mode_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_operation_def_request_response_mode_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_protocol_operation_def_id', name='cfg_protocol_operation_def_pkey'),
        UniqueConstraint('protocol_ref_id', 'operation_identifier', 'record_revision', name='cfg_protocol_operation_def_protocol_ref_id_operation_identi_key'),
        {'comment': '【元数据】协议原生操作定义表。描述各通信协议的原生读、写、控制、发布、订阅、报告、通知、总召、时钟同步等操作语义，不直接作为平台任务类型。',
     'schema': 'whale'}
    )

    cfg_protocol_operation_def_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    protocol_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议类型，取值来自 ref_code.ref_type=PROTOCOL。')
    operation_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议原生操作业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议原生操作中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议原生操作英文名称。')
    native_operation_name: Mapped[str] = mapped_column(Text, nullable=False, comment='协议标准或工程语境中的原生操作名称。')
    operation_semantic_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议操作语义，取值来自 ref_code.ref_type=PROTOCOL_OPERATION_SEMANTIC。')
    operation_direction_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议原生操作方向，取值来自 ref_code.ref_type=PROTOCOL_OPERATION_DIRECTION。')
    request_response_mode_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议交互模式，取值来自 ref_code.ref_type=REQUEST_RESPONSE_MODE。')
    standard_ref: Mapped[str] = mapped_column(Text, nullable=False, comment='协议标准、规范条款或工程来源说明。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议原生操作中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议原生操作英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    native_operation_code: Mapped[Optional[str]] = mapped_column(Text, comment='协议标准中的原生操作码、功能码、ASDU 类型、COT、服务名或工程码；没有固定码值时可为空。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    operation_direction_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[operation_direction_ref_id], back_populates='cfg_protocol_operation_def_operation_direction_ref')
    operation_semantic_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[operation_semantic_ref_id], back_populates='cfg_protocol_operation_def_operation_semantic_ref')
    protocol_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_ref_id], back_populates='cfg_protocol_operation_def_protocol_ref')
    request_response_mode_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[request_response_mode_ref_id], back_populates='cfg_protocol_operation_def_request_response_mode_ref')
    cfg_protocol_task_type_mapping: Mapped[list['CfgProtocolTaskTypeMapping']] = relationship('CfgProtocolTaskTypeMapping', back_populates='protocol_operation_def')


class CfgProtocolTableRegistry(Base):
    __tablename__ = 'cfg_protocol_table_registry'
    __table_args__ = (
        ForeignKeyConstraint(['protocol_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_table_registry_protocol_ref_id_fkey'),
        ForeignKeyConstraint(['table_role_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_table_registry_table_role_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_protocol_table_registry_id', name='cfg_protocol_table_registry_pkey'),
        UniqueConstraint('protocol_ref_id', 'table_role_ref_id', 'record_revision', name='cfg_protocol_table_registry_protocol_ref_id_table_role_ref__key'),
        {'comment': '【元数据】协议物理表注册表。表达协议类型与连接参数表、点表表头、点表采集点表之间的映射关系。', 'schema': 'whale'}
    )

    cfg_protocol_table_registry_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    protocol_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议类型，取值来自 ref_code.ref_type=PROTOCOL。')
    table_role_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议表角色，取值来自 ref_code.ref_type=PROTOCOL_TABLE_ROLE。')
    table_schema: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'whale'::text"), comment='协议物理表所在 schema。')
    table_name: Mapped[str] = mapped_column(Text, nullable=False, comment='协议物理表名。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议表映射中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议表映射英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    protocol_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_ref_id], back_populates='cfg_protocol_table_registry_protocol_ref')
    table_role_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[table_role_ref_id], back_populates='cfg_protocol_table_registry_table_role_ref')


class OrgUnit(Base):
    __tablename__ = 'org_unit'
    __table_args__ = (
        ForeignKeyConstraint(['org_nature_ref_id'], ['whale.ref_code.ref_code_id'], name='org_unit_org_nature_ref_id_fkey'),
        ForeignKeyConstraint(['parent_org_unit_id'], ['whale.org_unit.org_unit_id'], name='org_unit_parent_org_unit_id_fkey'),
        PrimaryKeyConstraint('org_unit_id', name='org_unit_pkey'),
        UniqueConstraint('org_identifier', 'record_revision', name='org_unit_org_identifier_record_revision_key'),
        {'comment': '【主数据】组织单元主数据。表示集团、区域公司、分公司、子公司等组织层级，是权责与绩效分解底座的组织根。',
     'schema': 'whale'}
    )

    org_unit_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    org_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='组织业务稳定标识，不引用 ref_code.code。')
    org_nature_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='组织性质，取值来自 ref_code.ref_type=ORG_NATURE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='组织中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='组织英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='组织中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='组织英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    parent_org_unit_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='上级组织单元，引用本表主键；为空表示顶层组织。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    org_nature_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='org_unit')
    parent_org_unit: Mapped[Optional['OrgUnit']] = relationship('OrgUnit', remote_side=[org_unit_id], back_populates='parent_org_unit_reverse')
    parent_org_unit_reverse: Mapped[list['OrgUnit']] = relationship('OrgUnit', remote_side=[parent_org_unit_id], back_populates='parent_org_unit')
    org_power_plant: Mapped[list['OrgPowerPlant']] = relationship('OrgPowerPlant', back_populates='owning_org_unit')


class SecPermission(Base):
    __tablename__ = 'sec_permission'
    __table_args__ = (
        ForeignKeyConstraint(['permission_code_ref_id'], ['whale.ref_code.ref_code_id'], name='sec_permission_permission_code_ref_id_fkey'),
        ForeignKeyConstraint(['permission_type_ref_id'], ['whale.ref_code.ref_code_id'], name='sec_permission_permission_type_ref_id_fkey'),
        PrimaryKeyConstraint('sec_permission_id', name='sec_permission_pkey'),
        UniqueConstraint('permission_identifier', 'record_revision', name='sec_permission_permission_identifier_record_revision_key'),
        {'comment': '【安全主数据】权限主数据。定义系统访问权限、配置权限和运维操作权限。', 'schema': 'whale'}
    )

    sec_permission_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    permission_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='权限业务稳定标识，不引用 ref_code.code。')
    permission_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='权限类型，取值来自 ref_code.ref_type=PERMISSION_TYPE。')
    permission_code_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='权限枚举，取值来自 ref_code.ref_type=PERMISSION。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='权限中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='权限英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='权限中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='权限英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    permission_code_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[permission_code_ref_id], back_populates='sec_permission_permission_code_ref')
    permission_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[permission_type_ref_id], back_populates='sec_permission_permission_type_ref')
    sec_role_permission: Mapped[list['SecRolePermission']] = relationship('SecRolePermission', back_populates='permission')


class Task(Base):
    __tablename__ = 'task'
    __table_args__ = (
        ForeignKeyConstraint(['task_status_ref_id'], ['whale.ref_code.ref_code_id'], name='task_task_status_ref_id_fkey'),
        PrimaryKeyConstraint('task_id', name='task_pkey'),
        UniqueConstraint('task_identifier', 'record_revision', name='task_task_identifier_record_revision_key'),
        {'comment': '【配置数据】统一协议交互任务身份表。表示采集、订阅、写入、控制、发布、响应读取、上送报告、接收写入和接收控制等任务身份。',
     'schema': 'whale'}
    )

    task_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='任务业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    task_status_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务人工状态，取值来自 ref_code.ref_type=TASK_STATUS；用于表达安排运行、停止或删除，不再使用 task.enabled。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    task_status_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='task')
    task_config: Mapped[list['TaskConfig']] = relationship('TaskConfig', back_populates='task')


class TaskParamDef(Base):
    __tablename__ = 'task_param_def'
    __table_args__ = (
        ForeignKeyConstraint(['data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='task_param_def_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['task_type_ref_id'], ['whale.ref_code.ref_code_id'], name='task_param_def_task_type_ref_id_fkey'),
        PrimaryKeyConstraint('task_param_def_id', name='task_param_def_pkey'),
        UniqueConstraint('task_type_ref_id', 'param_identifier', 'record_revision', name='task_param_def_task_type_ref_id_param_identifier_record_rev_key'),
        {'comment': '【元数据】任务参数定义表。定义不同通用任务类型可用的周期、超时、重试、确认、发布、响应和写后校验等参数。',
     'schema': 'whale'}
    )

    task_param_def_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='平台通用任务类型，取值来自 ref_code.ref_type=TASK_TYPE。')
    param_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数英文名称。')
    data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='参数数据类型，取值来自 ref_code.ref_type=DATA_TYPE。')
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='该任务类型是否必须配置该参数。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    default_value: Mapped[Optional[str]] = mapped_column(Text, comment='参数默认值。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[data_type_ref_id], back_populates='task_param_def_data_type_ref')
    task_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[task_type_ref_id], back_populates='task_param_def_task_type_ref')
    task_param_value: Mapped[list['TaskParamValue']] = relationship('TaskParamValue', back_populates='task_param_def')


class TaskPointTable(Base):
    __tablename__ = 'task_point_table'
    __table_args__ = (
        ForeignKeyConstraint(['point_table_usage_ref_id'], ['whale.ref_code.ref_code_id'], name='task_point_table_point_table_usage_ref_id_fkey'),
        PrimaryKeyConstraint('task_point_table_id', name='task_point_table_pkey'),
        UniqueConstraint('point_table_identifier', 'record_revision', name='task_point_table_point_table_identifier_record_revision_key'),
        {'comment': '【配置数据】任务点表表头。表示协议交互任务实际使用的接入点、控制目标、发布字段、响应字段或上报数据集。',
     'schema': 'whale'}
    )

    task_point_table_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    point_table_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点表业务稳定标识，不引用 ref_code.code。')
    point_table_usage_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务点表用途，取值来自 ref_code.ref_type=POINT_TABLE_USAGE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点表中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点表英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点表中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点表英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    point_table_usage_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='task_point_table')
    task_point_item: Mapped[list['TaskPointItem']] = relationship('TaskPointItem', back_populates='task_point_table')
    task_config: Mapped[list['TaskConfig']] = relationship('TaskConfig', back_populates='task_point_table')


class CfgAdsPointItem(Base):
    __tablename__ = 'cfg_ads_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_ads_point_item_value_domain'),
        ForeignKeyConstraint(['cfg_ads_point_table_id'], ['whale.cfg_ads_point_table.cfg_ads_point_table_id'], name='cfg_ads_point_item_cfg_ads_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_ads_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_ads_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_ads_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_ads_point_item_id', name='cfg_ads_point_item_pkey'),
        UniqueConstraint('cfg_ads_point_table_id', 'point_identifier', 'record_revision', name='cfg_ads_point_item_cfg_ads_point_table_id_point_identifier__key'),
        {'comment': '【配置数据】ADS 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_ads_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_ads_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 ADS 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    symbol_name: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 符号变量名。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='ADS 原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    index_group: Mapped[Optional[int]] = mapped_column(Integer, comment='ADS Index Group。')
    index_offset: Mapped[Optional[int]] = mapped_column(Integer, comment='ADS Index Offset。')
    array_length: Mapped[Optional[int]] = mapped_column(Integer, comment='数组长度；标量为空。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_ads_point_table: Mapped['CfgAdsPointTable'] = relationship('CfgAdsPointTable', back_populates='cfg_ads_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_ads_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_ads_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_ads_point_item_protocol_data_type_ref')


class CfgHttpRestPointItem(Base):
    __tablename__ = 'cfg_http_rest_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_http_rest_point_item_value_domain'),
        ForeignKeyConstraint(['cfg_http_rest_point_table_id'], ['whale.cfg_http_rest_point_table.cfg_http_rest_point_table_id'], name='cfg_http_rest_point_item_cfg_http_rest_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_http_rest_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['http_method_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_http_rest_point_item_http_method_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_http_rest_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['payload_format_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_http_rest_point_item_payload_format_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_http_rest_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_http_rest_point_item_id', name='cfg_http_rest_point_item_pkey'),
        UniqueConstraint('cfg_http_rest_point_table_id', 'point_identifier', 'record_revision', name='cfg_http_rest_point_item_cfg_http_rest_point_table_id_point_key'),
        {'comment': '【配置数据】HTTP REST 设备能力点。直接隶属 HTTP REST 点表，记录资源路径、HTTP '
                '方法、载荷路径、语义、单位、访问模式和值域声明。',
     'schema': 'whale'}
    )

    cfg_http_rest_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_http_rest_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 HTTP REST 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    resource_path: Mapped[str] = mapped_column(Text, nullable=False, comment='REST 资源路径，不包含 base_url，例如 /api/v1/plant/overview。')
    http_method_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='HTTP 方法，取值来自 ref_code.ref_type=HTTP_METHOD。')
    response_body_path: Mapped[str] = mapped_column(Text, nullable=False, comment='响应体字段路径，例如 JSONPath。')
    payload_format_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='载荷格式，取值来自 ref_code.ref_type=PAYLOAD_FORMAT。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='响应字段或请求字段原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为工程值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为工程值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    request_body_path: Mapped[Optional[str]] = mapped_column(Text, comment='请求体字段路径；读类接口可为空。')
    query_param_path: Mapped[Optional[str]] = mapped_column(Text, comment='HTTP 查询参数路径；用于 GET 查询参数或分页、时间窗参数。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_http_rest_point_table: Mapped['CfgHttpRestPointTable'] = relationship('CfgHttpRestPointTable', back_populates='cfg_http_rest_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_http_rest_point_item_engineering_unit_ref')
    http_method_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[http_method_ref_id], back_populates='cfg_http_rest_point_item_http_method_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_http_rest_point_item')
    payload_format_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[payload_format_ref_id], back_populates='cfg_http_rest_point_item_payload_format_ref')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_http_rest_point_item_protocol_data_type_ref')


class CfgIec101PointItem(Base):
    __tablename__ = 'cfg_iec101_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_iec101_point_item_value_domain'),
        ForeignKeyConstraint(['cause_of_transmission_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec101_point_item_cause_of_transmission_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_iec101_point_table_id'], ['whale.cfg_iec101_point_table.cfg_iec101_point_table_id'], name='cfg_iec101_point_item_cfg_iec101_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec101_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_iec101_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec101_point_item_protocol_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['type_id_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec101_point_item_type_id_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_iec101_point_item_id', name='cfg_iec101_point_item_pkey'),
        UniqueConstraint('cfg_iec101_point_table_id', 'point_identifier', 'record_revision', name='cfg_iec101_point_item_cfg_iec101_point_table_id_point_ident_key'),
        {'comment': '【配置数据】IEC101 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_iec101_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_iec101_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 IEC101 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    type_id_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC101 类型标识，取值来自 ref_code.ref_type=IEC104_TYPE_ID。')
    common_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='公共地址。')
    information_object_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='信息对象地址。')
    quality_descriptor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否包含 IEC101 质量描述符；用于驱动解析 IV、NT、SB、BL 等质量位。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    cause_of_transmission_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='IEC101 传送原因，取值来自 ref_code.ref_type=IEC101_COT；用于区分响应、周期、突发、命令等远动语义。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cause_of_transmission_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[cause_of_transmission_ref_id], back_populates='cfg_iec101_point_item_cause_of_transmission_ref')
    cfg_iec101_point_table: Mapped['CfgIec101PointTable'] = relationship('CfgIec101PointTable', back_populates='cfg_iec101_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_iec101_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_iec101_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_iec101_point_item_protocol_data_type_ref')
    type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[type_id_ref_id], back_populates='cfg_iec101_point_item_type_ref')


class CfgIec104PointItem(Base):
    __tablename__ = 'cfg_iec104_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_iec104_point_item_value_domain'),
        ForeignKeyConstraint(['cause_of_transmission_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec104_point_item_cause_of_transmission_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_iec104_point_table_id'], ['whale.cfg_iec104_point_table.cfg_iec104_point_table_id'], name='cfg_iec104_point_item_cfg_iec104_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec104_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_iec104_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec104_point_item_protocol_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['type_id_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec104_point_item_type_id_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_iec104_point_item_id', name='cfg_iec104_point_item_pkey'),
        UniqueConstraint('cfg_iec104_point_table_id', 'point_identifier', 'record_revision', name='cfg_iec104_point_item_cfg_iec104_point_table_id_point_ident_key'),
        {'comment': '【配置数据】IEC104 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_iec104_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_iec104_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 IEC104 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    type_id_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC104 类型标识，取值来自 ref_code.ref_type=IEC104_TYPE_ID。')
    common_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='公共地址。')
    information_object_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='信息对象地址。')
    quality_descriptor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否包含 IEC104 质量描述符；用于驱动解析无效、非当前、替代、闭锁等质量位。')
    time_tag_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否带 CP56Time2a 等时标；用于驱动解析带时标遥测、遥信或事件。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    cause_of_transmission_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='IEC104 传送原因，取值来自 ref_code.ref_type=IEC104_COT；用于区分总召响应、周期上送、突发上送、命令等远动语义。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cause_of_transmission_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[cause_of_transmission_ref_id], back_populates='cfg_iec104_point_item_cause_of_transmission_ref')
    cfg_iec104_point_table: Mapped['CfgIec104PointTable'] = relationship('CfgIec104PointTable', back_populates='cfg_iec104_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_iec104_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_iec104_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_iec104_point_item_protocol_data_type_ref')
    type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[type_id_ref_id], back_populates='cfg_iec104_point_item_type_ref')


class CfgIec61850GoosePointItem(Base):
    __tablename__ = 'cfg_iec61850_goose_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_iec61850_goose_point_item_value_domain'),
        ForeignKeyConstraint(['btype_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_goose_point_item_btype_ref_id_fkey'),
        ForeignKeyConstraint(['cdc_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_goose_point_item_cdc_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_goose_point_table_id'], ['whale.cfg_iec61850_goose_point_table.cfg_iec61850_goose_point_table_id'], name='cfg_iec61850_goose_point_item_cfg_iec61850_goose_point_tab_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_goose_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_iec61850_goose_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_goose_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_goose_point_item_id', name='cfg_iec61850_goose_point_item_pkey'),
        UniqueConstraint('cfg_iec61850_goose_point_table_id', 'point_identifier', 'record_revision', name='cfg_iec61850_goose_point_item_cfg_iec61850_goose_point_tabl_key'),
        {'comment': '【配置数据】IEC61850 GOOSE 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。',
     'schema': 'whale'}
    )

    cfg_iec61850_goose_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_iec61850_goose_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 IEC61850 GOOSE 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    goose_control_ref: Mapped[str] = mapped_column(Text, nullable=False, comment='GOOSE 控制块引用。')
    dataset_ref: Mapped[str] = mapped_column(Text, nullable=False, comment='数据集引用。')
    member_index: Mapped[int] = mapped_column(Integer, nullable=False, comment='数据集成员序号。')
    object_reference: Mapped[str] = mapped_column(Text, nullable=False, comment='成员对象引用。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='GOOSE 成员原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    cdc_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='GOOSE 数据成员的 CDC，取值来自 ref_code.ref_type=IEC61850_CDC。')
    btype_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='GOOSE 数据成员基础类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    btype_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[btype_ref_id], back_populates='cfg_iec61850_goose_point_item_btype_ref')
    cdc_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[cdc_ref_id], back_populates='cfg_iec61850_goose_point_item_cdc_ref')
    cfg_iec61850_goose_point_table: Mapped['CfgIec61850GoosePointTable'] = relationship('CfgIec61850GoosePointTable', back_populates='cfg_iec61850_goose_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_iec61850_goose_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_iec61850_goose_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_iec61850_goose_point_item_protocol_data_type_ref')


class CfgIec61850MmsPointItem(Base):
    __tablename__ = 'cfg_iec61850_mms_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_iec61850_mms_point_item_value_domain'),
        ForeignKeyConstraint(['cdc_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_mms_point_item_cdc_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_mms_point_table_id'], ['whale.cfg_iec61850_mms_point_table.cfg_iec61850_mms_point_table_id'], name='cfg_iec61850_mms_point_item_cfg_iec61850_mms_point_table_i_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_mms_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['fc_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_mms_point_item_fc_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_iec61850_mms_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_mms_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_mms_point_item_id', name='cfg_iec61850_mms_point_item_pkey'),
        UniqueConstraint('cfg_iec61850_mms_point_table_id', 'point_identifier', 'record_revision', name='cfg_iec61850_mms_point_item_cfg_iec61850_mms_point_table_id_key'),
        {'comment': '【配置数据】IEC61850 MMS 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。',
     'schema': 'whale'}
    )

    cfg_iec61850_mms_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_iec61850_mms_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 IEC61850 MMS 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    object_reference: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 对象引用，例如 LD/LN.DO.DA。')
    fc_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='功能约束，取值来自 ref_code.ref_type=IEC61850_FC。')
    cdc_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='公共数据类，取值来自 ref_code.ref_type=IEC61850_CDC。')
    data_attribute_path: Mapped[str] = mapped_column(Text, nullable=False, comment='数据属性路径。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='MMS 原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    logical_device: Mapped[Optional[str]] = mapped_column(Text, comment='IEC 61850 逻辑设备名，用于从 object_reference 中拆分出驱动寻址层级。')
    logical_node: Mapped[Optional[str]] = mapped_column(Text, comment='IEC 61850 逻辑节点名，例如 WTUR、WGEN、MMXU、XCBR。')
    data_object: Mapped[Optional[str]] = mapped_column(Text, comment='IEC 61850 数据对象名，例如 TotW、Pos、PhV。')
    data_attribute: Mapped[Optional[str]] = mapped_column(Text, comment='IEC 61850 数据属性名，例如 mag.f、stVal、q、t。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cdc_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[cdc_ref_id], back_populates='cfg_iec61850_mms_point_item_cdc_ref')
    cfg_iec61850_mms_point_table: Mapped['CfgIec61850MmsPointTable'] = relationship('CfgIec61850MmsPointTable', back_populates='cfg_iec61850_mms_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_iec61850_mms_point_item_engineering_unit_ref')
    fc_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[fc_ref_id], back_populates='cfg_iec61850_mms_point_item_fc_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_iec61850_mms_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_iec61850_mms_point_item_protocol_data_type_ref')


class CfgIec61850SvPointItem(Base):
    __tablename__ = 'cfg_iec61850_sv_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_iec61850_sv_point_item_value_domain'),
        ForeignKeyConstraint(['btype_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_btype_ref_id_fkey'),
        ForeignKeyConstraint(['cdc_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_cdc_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_sv_point_table_id'], ['whale.cfg_iec61850_sv_point_table.cfg_iec61850_sv_point_table_id'], name='cfg_iec61850_sv_point_item_cfg_iec61850_sv_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_iec61850_sv_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['phase_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_phase_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_protocol_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['quantity_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_iec61850_sv_point_item_quantity_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_sv_point_item_id', name='cfg_iec61850_sv_point_item_pkey'),
        UniqueConstraint('cfg_iec61850_sv_point_table_id', 'point_identifier', 'record_revision', name='cfg_iec61850_sv_point_item_cfg_iec61850_sv_point_table_id_p_key'),
        {'comment': '【配置数据】IEC61850 SV 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。',
     'schema': 'whale'}
    )

    cfg_iec61850_sv_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_iec61850_sv_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 IEC61850 SV 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    sv_control_ref: Mapped[str] = mapped_column(Text, nullable=False, comment='SV 控制块引用。')
    dataset_ref: Mapped[str] = mapped_column(Text, nullable=False, comment='数据集引用。')
    sample_channel: Mapped[str] = mapped_column(Text, nullable=False, comment='采样通道名称。')
    sample_index: Mapped[int] = mapped_column(Integer, nullable=False, comment='采样通道序号。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='SV 原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    phase_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='采样通道相别，取值来自 ref_code.ref_type=PHASE。')
    quantity_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='采样量类型，取值来自 ref_code.ref_type=SV_QUANTITY。')
    cdc_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='SV 数据成员 CDC，取值来自 ref_code.ref_type=IEC61850_CDC。')
    btype_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='SV 数据成员基础类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    btype_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[btype_ref_id], back_populates='cfg_iec61850_sv_point_item_btype_ref')
    cdc_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[cdc_ref_id], back_populates='cfg_iec61850_sv_point_item_cdc_ref')
    cfg_iec61850_sv_point_table: Mapped['CfgIec61850SvPointTable'] = relationship('CfgIec61850SvPointTable', back_populates='cfg_iec61850_sv_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_iec61850_sv_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_iec61850_sv_point_item')
    phase_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[phase_ref_id], back_populates='cfg_iec61850_sv_point_item_phase_ref')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_iec61850_sv_point_item_protocol_data_type_ref')
    quantity_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[quantity_ref_id], back_populates='cfg_iec61850_sv_point_item_quantity_ref')


class CfgModbusPointItem(Base):
    __tablename__ = 'cfg_modbus_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_modbus_point_item_value_domain'),
        ForeignKeyConstraint(['byte_order_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_byte_order_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_modbus_point_table_id'], ['whale.cfg_modbus_point_table.cfg_modbus_point_table_id'], name='cfg_modbus_point_item_cfg_modbus_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['function_code_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_function_code_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_modbus_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_protocol_data_type_ref_id_fkey'),
        ForeignKeyConstraint(['register_area_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_register_area_ref_id_fkey'),
        ForeignKeyConstraint(['word_order_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_point_item_word_order_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_modbus_point_item_id', name='cfg_modbus_point_item_pkey'),
        UniqueConstraint('cfg_modbus_point_table_id', 'point_identifier', 'record_revision', name='cfg_modbus_point_item_cfg_modbus_point_table_id_point_ident_key'),
        {'comment': '【配置数据】Modbus 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_modbus_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_modbus_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 Modbus 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    function_code_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='Modbus 功能码，取值来自 ref_code.ref_type=MODBUS_FUNCTION_CODE。')
    register_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='Modbus 寄存器或线圈起始地址。')
    register_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='Modbus 连续寄存器或线圈数量。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='Modbus 原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    byte_order_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='字节序，取值来自 ref_code.ref_type=BYTE_ORDER。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    register_area_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='Modbus 地址区分类，取值来自 ref_code.ref_type=MODBUS_REGISTER_AREA；与 function_code_ref_id 一起帮助驱动 facade 分派到 coils、discrete inputs、holding registers 或 input registers。')
    bit_offset: Mapped[Optional[int]] = mapped_column(Integer, comment='寄存器内位偏移；当一个寄存器内拆分多个布尔量时填写。')
    word_order_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='字序，取值来自 ref_code.ref_type=WORD_ORDER；单寄存器值可为空。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    byte_order_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[byte_order_ref_id], back_populates='cfg_modbus_point_item_byte_order_ref')
    cfg_modbus_point_table: Mapped['CfgModbusPointTable'] = relationship('CfgModbusPointTable', back_populates='cfg_modbus_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_modbus_point_item_engineering_unit_ref')
    function_code_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[function_code_ref_id], back_populates='cfg_modbus_point_item_function_code_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_modbus_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_modbus_point_item_protocol_data_type_ref')
    register_area_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[register_area_ref_id], back_populates='cfg_modbus_point_item_register_area_ref')
    word_order_ref: Mapped[Optional['RefCode']] = relationship('RefCode', foreign_keys=[word_order_ref_id], back_populates='cfg_modbus_point_item_word_order_ref')


class CfgMqttPointItem(Base):
    __tablename__ = 'cfg_mqtt_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_mqtt_point_item_value_domain'),
        ForeignKeyConstraint(['cfg_mqtt_point_table_id'], ['whale.cfg_mqtt_point_table.cfg_mqtt_point_table_id'], name='cfg_mqtt_point_item_cfg_mqtt_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_mqtt_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_mqtt_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['payload_format_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_mqtt_point_item_payload_format_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_mqtt_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_mqtt_point_item_id', name='cfg_mqtt_point_item_pkey'),
        UniqueConstraint('cfg_mqtt_point_table_id', 'point_identifier', 'record_revision', name='cfg_mqtt_point_item_cfg_mqtt_point_table_id_point_identifie_key'),
        {'comment': '【配置数据】MQTT 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_mqtt_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_mqtt_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 MQTT 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    topic: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT Topic。')
    payload_format_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='载荷格式，取值来自 ref_code.ref_type=PAYLOAD_FORMAT。')
    payload_path: Mapped[str] = mapped_column(Text, nullable=False, comment='载荷内字段路径，例如 JSONPath。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='载荷字段原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_mqtt_point_table: Mapped['CfgMqttPointTable'] = relationship('CfgMqttPointTable', back_populates='cfg_mqtt_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_mqtt_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_mqtt_point_item')
    payload_format_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[payload_format_ref_id], back_populates='cfg_mqtt_point_item_payload_format_ref')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_mqtt_point_item_protocol_data_type_ref')


class CfgOpcuaPointItem(Base):
    __tablename__ = 'cfg_opcua_point_item'
    __table_args__ = (
        CheckConstraint('value_min IS NOT NULL AND value_max IS NOT NULL OR allowed_values IS NOT NULL', name='chk_cfg_opcua_point_item_value_domain'),
        ForeignKeyConstraint(['cfg_opcua_point_table_id'], ['whale.cfg_opcua_point_table.cfg_opcua_point_table_id'], name='cfg_opcua_point_item_cfg_opcua_point_table_id_fkey'),
        ForeignKeyConstraint(['engineering_unit_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_opcua_point_item_engineering_unit_ref_id_fkey'),
        ForeignKeyConstraint(['measurement_semantic_id'], ['whale.cfg_measurement_semantic.cfg_measurement_semantic_id'], name='cfg_opcua_point_item_measurement_semantic_id_fkey'),
        ForeignKeyConstraint(['protocol_data_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_opcua_point_item_protocol_data_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_opcua_point_item_id', name='cfg_opcua_point_item_pkey'),
        UniqueConstraint('cfg_opcua_point_table_id', 'point_identifier', 'record_revision', name='cfg_opcua_point_item_cfg_opcua_point_table_id_point_identif_key'),
        {'comment': '【配置数据】OPC UA 设备能力点。直接隶属协议点表，记录协议地址、解析参数和语义映射。', 'schema': 'whale'}
    )

    cfg_opcua_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_opcua_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属 OPC UA 设备能力点表。')
    measurement_semantic_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点对应的业务测量、状态、控制或发布语义。')
    point_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文名称。')
    namespace_uri: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 命名空间 URI。')
    node_id: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA NodeId。')
    attribute_id: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('13'), comment='属性 ID，默认 13 表示 Value。')
    value_rank: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'-1'::integer"), comment='值秩；-1 表示标量。')
    protocol_data_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='OPC UA 原始数据类型，取值来自 ref_code.ref_type=PROTOCOL_DATA_TYPE。')
    engineering_unit_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议点工程值单位，取值来自 ref_code.ref_type=UNIT；value_min、value_max 与 allowed_values 均按该单位解释。')
    scale_factor: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('1'), comment='协议原始值转换为统一值的比例系数。')
    offset_value: Mapped[decimal.Decimal] = mapped_column(Numeric(18, 8), nullable=False, server_default=text('0'), comment='协议原始值转换为统一值的偏移量。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='协议点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    namespace_index: Mapped[Optional[int]] = mapped_column(Integer, comment='OPC UA namespace index；当驱动包以 ns 索引寻址时使用。')
    browse_path: Mapped[Optional[str]] = mapped_column(Text, comment='浏览路径。')
    array_length: Mapped[Optional[int]] = mapped_column(Integer, comment='数组长度；标量为空。')
    value_min: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text("'-1000000'::integer"), comment='该协议点工程值允许下限；为空表示不声明下限。复杂质量规则由模块代码处理。')
    value_max: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(24, 8), server_default=text('1000000'), comment='该协议点工程值允许上限；为空表示不声明上限。复杂质量规则由模块代码处理。')
    allowed_values: Mapped[Optional[str]] = mapped_column(Text, comment='该协议点离散工程值允许集合，使用逗号分割字符串表达；为空表示不声明离散值集合。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_opcua_point_table: Mapped['CfgOpcuaPointTable'] = relationship('CfgOpcuaPointTable', back_populates='cfg_opcua_point_item')
    engineering_unit_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[engineering_unit_ref_id], back_populates='cfg_opcua_point_item_engineering_unit_ref')
    measurement_semantic: Mapped['CfgMeasurementSemantic'] = relationship('CfgMeasurementSemantic', back_populates='cfg_opcua_point_item')
    protocol_data_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_data_type_ref_id], back_populates='cfg_opcua_point_item_protocol_data_type_ref')


class CfgProtocolTaskTypeMapping(Base):
    __tablename__ = 'cfg_protocol_task_type_mapping'
    __table_args__ = (
        ForeignKeyConstraint(['point_table_usage_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_point_table_usage_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_operation_def_id'], ['whale.cfg_protocol_operation_def.cfg_protocol_operation_def_id'], name='cfg_protocol_task_type_mapping_protocol_operation_def_id_fkey'),
        ForeignKeyConstraint(['protocol_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_protocol_ref_id_fkey'),
        ForeignKeyConstraint(['task_category_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_task_category_ref_id_fkey'),
        ForeignKeyConstraint(['task_direction_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_task_direction_ref_id_fkey'),
        ForeignKeyConstraint(['task_protocol_role_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_task_protocol_role_ref_id_fkey'),
        ForeignKeyConstraint(['task_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_protocol_task_type_mapping_task_type_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_protocol_task_type_mapping_id', name='cfg_protocol_task_type_mapping_pkey'),
        UniqueConstraint('protocol_operation_def_id', 'task_type_ref_id', 'task_protocol_role_ref_id', 'record_revision', name='cfg_protocol_task_type_mappin_protocol_operation_def_id_tas_key'),
        {'comment': '【元数据】协议操作与平台任务类型映射表。定义某协议原生操作允许映射到哪些通用任务类型，并给出任务大类、方向、协议角色和点表用途。',
     'schema': 'whale'}
    )

    cfg_protocol_task_type_mapping_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    protocol_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议类型，取值来自 ref_code.ref_type=PROTOCOL；与协议操作定义保持一致，便于查询和约束检查。')
    protocol_operation_def_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议原生操作定义，指向 cfg_protocol_operation_def。')
    task_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='平台通用任务类型，取值来自 ref_code.ref_type=TASK_TYPE。')
    task_category_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务大类，取值来自 ref_code.ref_type=TASK_CATEGORY。')
    task_direction_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务数据流向，取值来自 ref_code.ref_type=TASK_DIRECTION。')
    task_protocol_role_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='本系统在该任务中的协议角色，取值来自 ref_code.ref_type=TASK_PROTOCOL_ROLE。')
    point_table_usage_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='该任务映射下任务点表的用途，取值来自 ref_code.ref_type=POINT_TABLE_USAGE。')
    allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='该协议操作与任务类型组合是否允许。')
    default_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='该协议操作与任务类型组合是否默认启用。')
    requires_point_table: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='该任务配置是否必须绑定 task_point_table。')
    requires_write_value: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='该任务是否需要写入值、控制值、命令载荷或方法入参。')
    requires_response_mapping: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='该任务是否需要响应字段、回读字段或上送字段映射。')
    requires_confirm: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='该任务是否需要协议确认、业务确认或写后校验。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='映射关系中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='映射关系英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一映射关系变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    point_table_usage_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[point_table_usage_ref_id], back_populates='cfg_protocol_task_type_mapping_point_table_usage_ref')
    protocol_operation_def: Mapped['CfgProtocolOperationDef'] = relationship('CfgProtocolOperationDef', back_populates='cfg_protocol_task_type_mapping')
    protocol_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_ref_id], back_populates='cfg_protocol_task_type_mapping_protocol_ref')
    task_category_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[task_category_ref_id], back_populates='cfg_protocol_task_type_mapping_task_category_ref')
    task_direction_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[task_direction_ref_id], back_populates='cfg_protocol_task_type_mapping_task_direction_ref')
    task_protocol_role_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[task_protocol_role_ref_id], back_populates='cfg_protocol_task_type_mapping_task_protocol_role_ref')
    task_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[task_type_ref_id], back_populates='cfg_protocol_task_type_mapping_task_type_ref')
    task_config: Mapped[list['TaskConfig']] = relationship('TaskConfig', back_populates='cfg_protocol_task_type_mapping')


class OrgPowerPlant(Base):
    __tablename__ = 'org_power_plant'
    __table_args__ = (
        ForeignKeyConstraint(['owning_org_unit_id'], ['whale.org_unit.org_unit_id'], name='org_power_plant_owning_org_unit_id_fkey'),
        ForeignKeyConstraint(['plant_type_ref_id'], ['whale.ref_code.ref_code_id'], name='org_power_plant_plant_type_ref_id_fkey'),
        PrimaryKeyConstraint('org_power_plant_id', name='org_power_plant_pkey'),
        UniqueConstraint('plant_identifier', 'record_revision', name='org_power_plant_plant_identifier_record_revision_key'),
        {'comment': '【主数据】并网型电场主数据。表示风电、光伏、储能或混合并网场站，是现场工作班组、员工、资产和拓扑的场站上下文。',
     'schema': 'whale'}
    )

    org_power_plant_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    owning_org_unit_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属组织单元，表示该并网型电场隶属的公司或管理组织。')
    plant_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='并网型电场业务稳定标识，不引用 ref_code.code。')
    plant_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='电场类型，取值来自 ref_code.ref_type=POWER_PLANT_TYPE；统一表示并网型电场，不刻意拆风电场、光伏电场或风光储电场。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='电场中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='电场英文名称。')
    wind_installed_capacity_mw: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default=text('0'), comment='风机装机容量，单位 MW。')
    pv_installed_capacity_mw: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default=text('0'), comment='光伏装机容量，单位 MW。')
    storage_power_mw: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default=text('0'), comment='储能额定功率，单位 MW。')
    storage_capacity_mwh: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 3), nullable=False, server_default=text('0'), comment='储能额定容量，单位 MWh。')
    grid_voltage_kv: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 3), nullable=False, comment='并网电压等级，单位 kV。')
    grid_capacity_mva: Mapped[decimal.Decimal] = mapped_column(Numeric(12, 3), nullable=False, comment='并网容量，单位 MVA。')
    dispatch_center: Mapped[str] = mapped_column(Text, nullable=False, comment='调度机构或调度中心名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='电场中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='电场英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    grid_connection_date: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='并网日期。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    owning_org_unit: Mapped['OrgUnit'] = relationship('OrgUnit', back_populates='org_power_plant')
    plant_type_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='org_power_plant')
    ast_asset: Mapped[list['AstAsset']] = relationship('AstAsset', back_populates='power_plant')
    org_work_team: Mapped[list['OrgWorkTeam']] = relationship('OrgWorkTeam', back_populates='power_plant')
    emp_employee: Mapped[list['EmpEmployee']] = relationship('EmpEmployee', back_populates='power_plant')
    cfg_grid_dispatch_connection: Mapped[list['CfgGridDispatchConnection']] = relationship('CfgGridDispatchConnection', back_populates='power_plant')


class SecRolePermission(Base):
    __tablename__ = 'sec_role_permission'
    __table_args__ = (
        ForeignKeyConstraint(['permission_id'], ['whale.sec_permission.sec_permission_id'], name='sec_role_permission_permission_id_fkey'),
        ForeignKeyConstraint(['role_id'], ['whale.sec_role.sec_role_id'], name='sec_role_permission_role_id_fkey'),
        PrimaryKeyConstraint('sec_role_permission_id', name='sec_role_permission_pkey'),
        UniqueConstraint('role_id', 'permission_id', 'record_revision', name='sec_role_permission_role_id_permission_id_record_revision_key'),
        {'comment': '【安全主数据】角色权限关系。表示某角色拥有哪些系统权限。', 'schema': 'whale'}
    )

    sec_role_permission_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='角色主键。')
    permission_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='权限主键。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    permission: Mapped['SecPermission'] = relationship('SecPermission', back_populates='sec_role_permission')
    role: Mapped['SecRole'] = relationship('SecRole', back_populates='sec_role_permission')


class TaskPointItem(Base):
    __tablename__ = 'task_point_item'
    __table_args__ = (
        ForeignKeyConstraint(['point_role_ref_id'], ['whale.ref_code.ref_code_id'], name='task_point_item_point_role_ref_id_fkey'),
        ForeignKeyConstraint(['protocol_ref_id'], ['whale.ref_code.ref_code_id'], name='task_point_item_protocol_ref_id_fkey'),
        ForeignKeyConstraint(['sample_mode_ref_id'], ['whale.ref_code.ref_code_id'], name='task_point_item_sample_mode_ref_id_fkey'),
        ForeignKeyConstraint(['task_point_table_id'], ['whale.task_point_table.task_point_table_id'], name='task_point_item_task_point_table_id_fkey'),
        PrimaryKeyConstraint('task_point_item_id', name='task_point_item_pkey'),
        UniqueConstraint('task_point_table_id', 'protocol_ref_id', 'protocol_point_table_id', 'protocol_point_item_id', 'point_role_ref_id', 'record_revision', name='task_point_item_task_point_table_id_protocol_ref_id_protoco_key'),
        {'comment': '【配置数据】任务点表明细。直接引用协议能力点表中的点项，表达任务实际使用的采集点、写入目标、控制目标、发布字段、响应字段或上报字段。',
     'schema': 'whale'}
    )

    task_point_item_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属任务点表。')
    protocol_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务点所属协议，取值来自 ref_code.ref_type=PROTOCOL；用于解释 protocol_point_table_id 与 protocol_point_item_id 所对应的协议物理表。')
    protocol_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议能力点表主键值；需结合 protocol_ref_id 和 cfg_protocol_table_registry 定位对应 cfg_<protocol>_point_table 物理表。')
    protocol_point_item_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议能力点表明细主键值；需结合 protocol_ref_id 和 cfg_protocol_table_registry 定位对应 cfg_<protocol>_point_item 物理表。')
    point_role_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='点在任务中的角色，取值来自 ref_code.ref_type=TASK_POINT_ROLE。')
    scan_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='任务内点位处理顺序。')
    sample_mode_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务点采样或触发模式，取值来自 ref_code.ref_type=SAMPLE_MODE。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务点英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    point_role_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[point_role_ref_id], back_populates='task_point_item_point_role_ref')
    protocol_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[protocol_ref_id], back_populates='task_point_item_protocol_ref')
    sample_mode_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[sample_mode_ref_id], back_populates='task_point_item_sample_mode_ref')
    task_point_table: Mapped['TaskPointTable'] = relationship('TaskPointTable', back_populates='task_point_item')


class AstAsset(Base):
    __tablename__ = 'ast_asset'
    __table_args__ = (
        ForeignKeyConstraint(['asset_lifecycle_status_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_asset_lifecycle_status_ref_id_fkey'),
        ForeignKeyConstraint(['asset_type_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_asset_type_ref_id_fkey'),
        ForeignKeyConstraint(['model_id'], ['whale.ast_asset_model.ast_asset_model_id'], name='ast_asset_model_id_fkey'),
        ForeignKeyConstraint(['parent_asset_id'], ['whale.ast_asset.ast_asset_id'], name='ast_asset_parent_asset_id_fkey'),
        ForeignKeyConstraint(['power_plant_id'], ['whale.org_power_plant.org_power_plant_id'], name='ast_asset_power_plant_id_fkey'),
        PrimaryKeyConstraint('ast_asset_id', name='ast_asset_pkey'),
        UniqueConstraint('asset_identifier', 'record_revision', name='ast_asset_asset_identifier_record_revision_key'),
        {'comment': '【主数据】资产主数据。只表示真实设备、系统和部件；拓扑接口和边不进入资产表，通过 parent_asset_id '
                '表达资产台账层级。',
     'schema': 'whale'}
    )

    ast_asset_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    power_plant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产所属并网型电场。')
    model_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产型号主键，不能为空。')
    asset_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='资产业务稳定标识，不引用 ref_code.code。')
    asset_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产类型，取值来自 ref_code.ref_type=ASSET_TYPE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='资产中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='资产英文名称。')
    asset_lifecycle_status_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产生命周期状态，取值来自 ref_code.ref_type=ASSET_LIFECYCLE_STATUS。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='资产中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='资产英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    parent_asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='上级资产主键，仅表达资产台账层级，不表达电气、通信或机械连接关系；无上级资产时为空。')
    serial_number: Mapped[Optional[str]] = mapped_column(Text, comment='厂家序列号。')
    production_date: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='生产日期；资料未知时可为空。')
    installation_date: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='现场安装日期；资料未知时可为空。')
    commissioning_date: Mapped[Optional[datetime.date]] = mapped_column(Date, comment='投运日期；未投运或资料未知时可为空。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset_lifecycle_status_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[asset_lifecycle_status_ref_id], back_populates='ast_asset_asset_lifecycle_status_ref')
    asset_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[asset_type_ref_id], back_populates='ast_asset_asset_type_ref')
    model: Mapped['AstAssetModel'] = relationship('AstAssetModel', back_populates='ast_asset')
    parent_asset: Mapped[Optional['AstAsset']] = relationship('AstAsset', remote_side=[ast_asset_id], back_populates='parent_asset_reverse')
    parent_asset_reverse: Mapped[list['AstAsset']] = relationship('AstAsset', remote_side=[parent_asset_id], back_populates='parent_asset')
    power_plant: Mapped['OrgPowerPlant'] = relationship('OrgPowerPlant', back_populates='ast_asset')
    ast_asset_maintenance_event_asset: Mapped[list['AstAssetMaintenanceEvent']] = relationship('AstAssetMaintenanceEvent', foreign_keys='[AstAssetMaintenanceEvent.asset_id]', back_populates='asset')
    ast_asset_maintenance_event_new_asset: Mapped[list['AstAssetMaintenanceEvent']] = relationship('AstAssetMaintenanceEvent', foreign_keys='[AstAssetMaintenanceEvent.new_asset_id]', back_populates='new_asset')
    ast_asset_maintenance_event_old_asset: Mapped[list['AstAssetMaintenanceEvent']] = relationship('AstAssetMaintenanceEvent', foreign_keys='[AstAssetMaintenanceEvent.old_asset_id]', back_populates='old_asset')
    ast_asset_param_value: Mapped[list['AstAssetParamValue']] = relationship('AstAssetParamValue', back_populates='asset')
    cfg_connection: Mapped[list['CfgConnection']] = relationship('CfgConnection', back_populates='asset')
    geo_location: Mapped[list['GeoLocation']] = relationship('GeoLocation', back_populates='asset')
    topo_comm_element: Mapped[list['TopoCommElement']] = relationship('TopoCommElement', back_populates='asset')
    topo_elec_element: Mapped[list['TopoElecElement']] = relationship('TopoElecElement', back_populates='asset')


class OrgWorkTeam(Base):
    __tablename__ = 'org_work_team'
    __table_args__ = (
        ForeignKeyConstraint(['power_plant_id'], ['whale.org_power_plant.org_power_plant_id'], name='org_work_team_power_plant_id_fkey'),
        ForeignKeyConstraint(['work_team_type_ref_id'], ['whale.ref_code.ref_code_id'], name='org_work_team_work_team_type_ref_id_fkey'),
        PrimaryKeyConstraint('org_work_team_id', name='org_work_team_pkey'),
        UniqueConstraint('work_team_identifier', 'record_revision', name='org_work_team_work_team_identifier_record_revision_key'),
        {'comment': '【主数据】现场工作班组主数据。表示运行班组、检修班组、值班组等现场组织单元。', 'schema': 'whale'}
    )

    org_work_team_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    power_plant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='所属并网型电场。')
    work_team_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='现场工作班组业务稳定标识，不引用 ref_code.code。')
    work_team_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='现场工作班组类型，取值来自 ref_code.ref_type=WORK_TEAM_TYPE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='现场工作班组中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='现场工作班组英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='现场工作班组中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='现场工作班组英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    power_plant: Mapped['OrgPowerPlant'] = relationship('OrgPowerPlant', back_populates='org_work_team')
    work_team_type_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='org_work_team')
    emp_employee: Mapped[list['EmpEmployee']] = relationship('EmpEmployee', back_populates='work_team')


class AstAssetMaintenanceEvent(Base):
    __tablename__ = 'ast_asset_maintenance_event'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='ast_asset_maintenance_event_asset_id_fkey'),
        ForeignKeyConstraint(['event_status_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_maintenance_event_event_status_ref_id_fkey'),
        ForeignKeyConstraint(['event_type_ref_id'], ['whale.ref_code.ref_code_id'], name='ast_asset_maintenance_event_event_type_ref_id_fkey'),
        ForeignKeyConstraint(['new_asset_id'], ['whale.ast_asset.ast_asset_id'], name='ast_asset_maintenance_event_new_asset_id_fkey'),
        ForeignKeyConstraint(['old_asset_id'], ['whale.ast_asset.ast_asset_id'], name='ast_asset_maintenance_event_old_asset_id_fkey'),
        PrimaryKeyConstraint('ast_asset_maintenance_event_id', name='ast_asset_maintenance_event_pkey'),
        {'comment': '【事件数据】资产维修更换保养退役记录。记录资产巡检、保养、维修、更换、退役和报废事件。', 'schema': 'whale'}
    )

    ast_asset_maintenance_event_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='发生事件的资产。')
    event_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='事件类型，取值来自 ref_code.ref_type=ASSET_MAINTENANCE_EVENT_TYPE。')
    event_status_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='事件状态，取值来自 ref_code.ref_type=EVENT_STATUS。')
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, comment='事件发生时间。')
    title_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='事件中文标题。')
    title_en: Mapped[str] = mapped_column(Text, nullable=False, comment='事件英文标题。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='事件中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='事件英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='事件完成时间；未完成时为空。')
    old_asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='更换事件中的旧资产。')
    new_asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='更换事件中的新资产。')
    work_order_identifier: Mapped[Optional[str]] = mapped_column(Text, comment='外部工单业务标识。')

    asset: Mapped['AstAsset'] = relationship('AstAsset', foreign_keys=[asset_id], back_populates='ast_asset_maintenance_event_asset')
    event_status_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[event_status_ref_id], back_populates='ast_asset_maintenance_event_event_status_ref')
    event_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[event_type_ref_id], back_populates='ast_asset_maintenance_event_event_type_ref')
    new_asset: Mapped[Optional['AstAsset']] = relationship('AstAsset', foreign_keys=[new_asset_id], back_populates='ast_asset_maintenance_event_new_asset')
    old_asset: Mapped[Optional['AstAsset']] = relationship('AstAsset', foreign_keys=[old_asset_id], back_populates='ast_asset_maintenance_event_old_asset')


class AstAssetParamValue(Base):
    __tablename__ = 'ast_asset_param_value'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='ast_asset_param_value_asset_id_fkey'),
        ForeignKeyConstraint(['asset_param_def_id'], ['whale.ast_asset_param_def.ast_asset_param_def_id'], name='ast_asset_param_value_asset_param_def_id_fkey'),
        PrimaryKeyConstraint('ast_asset_param_value_id', name='ast_asset_param_value_pkey'),
        UniqueConstraint('asset_id', 'asset_param_def_id', 'record_revision', name='ast_asset_param_value_asset_id_asset_param_def_id_record_re_key'),
        {'comment': '【主数据】资产参数值。保存具体资产的产品参数或现场参数。', 'schema': 'whale'}
    )

    ast_asset_param_value_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产主键。')
    asset_param_def_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='资产参数定义主键。')
    value_text: Mapped[str] = mapped_column(Text, nullable=False, comment='参数值文本。应用层按参数定义数据类型解释。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'资产参数值。'::text"), comment='参数值中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'Asset parameter value.'::text"), comment='参数值英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset: Mapped['AstAsset'] = relationship('AstAsset', back_populates='ast_asset_param_value')
    asset_param_def: Mapped['AstAssetParamDef'] = relationship('AstAssetParamDef', back_populates='ast_asset_param_value')


class CfgConnection(Base):
    __tablename__ = 'cfg_connection'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='cfg_connection_asset_id_fkey'),
        ForeignKeyConstraint(['protocol_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_connection_protocol_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_connection_id', name='cfg_connection_pkey'),
        UniqueConstraint('connection_identifier', 'record_revision', name='cfg_connection_connection_identifier_record_revision_key'),
        {'comment': '【配置数据】通用连接配置父表。统一连接身份、资产归属和协议类型；具体协议参数存放在对应 cfg_<protocol>_conn '
                '子表。',
     'schema': 'whale'}
    )

    cfg_connection_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='连接归属资产。连接配置是追加式记录，资产变化时新增连接记录，不更新旧记录。')
    protocol_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议类型，取值来自 ref_code.ref_type=PROTOCOL。')
    connection_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='连接业务稳定标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='连接中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='连接英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='连接中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='连接英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset: Mapped['AstAsset'] = relationship('AstAsset', back_populates='cfg_connection')
    protocol_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='cfg_connection')
    cfg_connection_status_event: Mapped[list['CfgConnectionStatusEvent']] = relationship('CfgConnectionStatusEvent', back_populates='cfg_connection')
    cfg_grid_dispatch_connection: Mapped[list['CfgGridDispatchConnection']] = relationship('CfgGridDispatchConnection', back_populates='cfg_connection')
    task_config: Mapped[list['TaskConfig']] = relationship('TaskConfig', back_populates='cfg_connection')


class EmpEmployee(Base):
    __tablename__ = 'emp_employee'
    __table_args__ = (
        ForeignKeyConstraint(['power_plant_id'], ['whale.org_power_plant.org_power_plant_id'], name='emp_employee_power_plant_id_fkey'),
        ForeignKeyConstraint(['work_team_id'], ['whale.org_work_team.org_work_team_id'], name='emp_employee_work_team_id_fkey'),
        PrimaryKeyConstraint('emp_employee_id', name='emp_employee_pkey'),
        UniqueConstraint('employee_identifier', 'record_revision', name='emp_employee_employee_identifier_record_revision_key'),
        {'comment': '【主数据】员工主数据。表示场站员工和系统用户，承担权限、任务分配、职责追责和绩效分解。', 'schema': 'whale'}
    )

    emp_employee_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    power_plant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='员工所属并网型电场。')
    work_team_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='员工所属现场工作班组。')
    employee_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='员工业务稳定标识，可作为系统用户标识，不引用 ref_code.code。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='员工中文姓名。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='员工英文姓名。')
    on_duty: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否当班/在岗值守，表示当前是否处于值班或现场值守状态；不同于是否在职。')
    in_service: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否在职，表示员工尚未离职或退出场站人员范围；不同于 on_duty。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='员工中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='员工英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    mobile_phone: Mapped[Optional[str]] = mapped_column(Text, comment='移动电话。')
    email: Mapped[Optional[str]] = mapped_column(Text, comment='电子邮箱。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    power_plant: Mapped['OrgPowerPlant'] = relationship('OrgPowerPlant', back_populates='emp_employee')
    work_team: Mapped['OrgWorkTeam'] = relationship('OrgWorkTeam', back_populates='emp_employee')
    sec_employee_role: Mapped[list['SecEmployeeRole']] = relationship('SecEmployeeRole', back_populates='employee')


class GeoLocation(Base):
    __tablename__ = 'geo_location'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='geo_location_asset_id_fkey'),
        ForeignKeyConstraint(['model_file_format_ref_id'], ['whale.ref_code.ref_code_id'], name='geo_location_model_file_format_ref_id_fkey'),
        PrimaryKeyConstraint('geo_location_id', name='geo_location_pkey'),
        UniqueConstraint('location_identifier', 'record_revision', name='geo_location_location_identifier_record_revision_key'),
        {'comment': '【主数据】三维场景资产位置主数据。只保存需要在三维图上显示的大型真实资产位置，不保存接口、拓扑边或普通小部件位置。',
     'schema': 'whale'}
    )

    geo_location_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='三维场景位置对应的真实资产，不能为空。')
    location_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='位置业务稳定标识，不引用 ref_code.code。')
    coordinate_system: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'WGS84'::text"), comment='坐标系名称，例如 WGS84、CGCS2000、LOCAL_SITE。')
    rotation_x: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('0'), comment='三维模型绕 X 轴旋转角，单位度。')
    rotation_y: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('0'), comment='三维模型绕 Y 轴旋转角，单位度。')
    rotation_z: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('0'), comment='三维模型绕 Z 轴旋转角，单位度。')
    scale_x: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('1'), comment='三维模型 X 方向缩放系数。')
    scale_y: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('1'), comment='三维模型 Y 方向缩放系数。')
    scale_z: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 4), nullable=False, server_default=text('1'), comment='三维模型 Z 方向缩放系数。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='位置中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='位置英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    longitude: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 8), comment='经度，适用于地理坐标系。')
    latitude: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 8), comment='纬度，适用于地理坐标系。')
    altitude_m: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 3), comment='高程或海拔，单位米。')
    coordinate_x: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 4), comment='场站平面坐标或投影坐标 X。')
    coordinate_y: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(14, 4), comment='场站平面坐标或投影坐标 Y。')
    height_m: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(12, 3), comment='设备本体高度，单位米，例如风机轮毂高度、测风塔高度、主变外形高度。')
    model_file_name: Mapped[Optional[str]] = mapped_column(Text, comment='三维模型文件名，例如 glTF、FBX、OBJ 模型文件。')
    model_file_format_ref_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='模型文件格式，取值来自 ref_code.ref_type=MODEL_FILE_FORMAT。')
    model_object_identifier: Mapped[Optional[str]] = mapped_column(Text, comment='模型文件内部对象标识，用于定位模型内子对象。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset: Mapped['AstAsset'] = relationship('AstAsset', back_populates='geo_location')
    model_file_format_ref: Mapped[Optional['RefCode']] = relationship('RefCode', back_populates='geo_location')


class TopoCommElement(Base):
    __tablename__ = 'topo_comm_element'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='topo_comm_element_asset_id_fkey'),
        ForeignKeyConstraint(['element_kind_ref_id'], ['whale.ref_code.ref_code_id'], name='topo_comm_element_element_kind_ref_id_fkey'),
        ForeignKeyConstraint(['element_type_ref_id'], ['whale.ref_code.ref_code_id'], name='topo_comm_element_element_type_ref_id_fkey'),
        PrimaryKeyConstraint('topo_comm_element_id', name='topo_comm_element_pkey'),
        UniqueConstraint('element_identifier', 'record_revision', name='topo_comm_element_element_identifier_record_revision_key'),
        {'comment': '【配置数据】通信拓扑元素。统一描述通信拓扑中的节点、链路和接口。', 'schema': 'whale'}
    )

    topo_comm_element_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    element_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='通信拓扑元素业务稳定标识，不引用 ref_code.code。')
    element_kind_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='元素种类，取值来自 ref_code.ref_type=TOPO_ELEMENT_KIND。')
    element_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='通信元素类型，取值来自 ref_code.ref_type=COMM_TOPO_ELEMENT_TYPE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='通信拓扑元素中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='通信拓扑元素英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='通信拓扑元素中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='通信拓扑元素英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='通信拓扑元素关联资产；仅当 NODE 表示真实 ast_asset 时填写，INTERFACE 与 EDGE 通常为空。')
    ip_address: Mapped[Optional[Any]] = mapped_column(INET, comment='通信节点或接口的 IP 地址；无 IP 时为空。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset: Mapped[Optional['AstAsset']] = relationship('AstAsset', back_populates='topo_comm_element')
    element_kind_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[element_kind_ref_id], back_populates='topo_comm_element_element_kind_ref')
    element_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[element_type_ref_id], back_populates='topo_comm_element_element_type_ref')
    topo_comm_connection_edge: Mapped[list['TopoCommConnection']] = relationship('TopoCommConnection', foreign_keys='[TopoCommConnection.edge_id]', back_populates='edge')
    topo_comm_connection_from_interface: Mapped[list['TopoCommConnection']] = relationship('TopoCommConnection', foreign_keys='[TopoCommConnection.from_interface_id]', back_populates='from_interface')
    topo_comm_connection_from_node: Mapped[list['TopoCommConnection']] = relationship('TopoCommConnection', foreign_keys='[TopoCommConnection.from_node_id]', back_populates='from_node')
    topo_comm_connection_to_interface: Mapped[list['TopoCommConnection']] = relationship('TopoCommConnection', foreign_keys='[TopoCommConnection.to_interface_id]', back_populates='to_interface')
    topo_comm_connection_to_node: Mapped[list['TopoCommConnection']] = relationship('TopoCommConnection', foreign_keys='[TopoCommConnection.to_node_id]', back_populates='to_node')


class TopoElecElement(Base):
    __tablename__ = 'topo_elec_element'
    __table_args__ = (
        ForeignKeyConstraint(['asset_id'], ['whale.ast_asset.ast_asset_id'], name='topo_elec_element_asset_id_fkey'),
        ForeignKeyConstraint(['element_kind_ref_id'], ['whale.ref_code.ref_code_id'], name='topo_elec_element_element_kind_ref_id_fkey'),
        ForeignKeyConstraint(['element_type_ref_id'], ['whale.ref_code.ref_code_id'], name='topo_elec_element_element_type_ref_id_fkey'),
        PrimaryKeyConstraint('topo_elec_element_id', name='topo_elec_element_pkey'),
        UniqueConstraint('element_identifier', 'record_revision', name='topo_elec_element_element_identifier_record_revision_key'),
        {'comment': '【配置数据】电气拓扑元素。统一描述电气原理图中的节点、边和接口，用于从发电到并网的全场电气图绘制。',
     'schema': 'whale'}
    )

    topo_elec_element_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    element_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='电气拓扑元素业务稳定标识，不引用 ref_code.code。')
    element_kind_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='元素种类，取值来自 ref_code.ref_type=TOPO_ELEMENT_KIND。')
    element_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='电气元素类型，取值来自 ref_code.ref_type=ELEC_TOPO_ELEMENT_TYPE。')
    name_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='电气拓扑元素中文名称。')
    name_en: Mapped[str] = mapped_column(Text, nullable=False, comment='电气拓扑元素英文名称。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='电气拓扑元素中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='电气拓扑元素英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    asset_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='电气拓扑元素关联资产；仅当 NODE 表示真实 ast_asset 时填写，INTERFACE 与 EDGE 通常为空。')
    rated_voltage_kv: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric(10, 3), comment='额定电压，单位 kV。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    asset: Mapped[Optional['AstAsset']] = relationship('AstAsset', back_populates='topo_elec_element')
    element_kind_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[element_kind_ref_id], back_populates='topo_elec_element_element_kind_ref')
    element_type_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[element_type_ref_id], back_populates='topo_elec_element_element_type_ref')
    topo_elec_connection_edge: Mapped[list['TopoElecConnection']] = relationship('TopoElecConnection', foreign_keys='[TopoElecConnection.edge_id]', back_populates='edge')
    topo_elec_connection_from_interface: Mapped[list['TopoElecConnection']] = relationship('TopoElecConnection', foreign_keys='[TopoElecConnection.from_interface_id]', back_populates='from_interface')
    topo_elec_connection_from_node: Mapped[list['TopoElecConnection']] = relationship('TopoElecConnection', foreign_keys='[TopoElecConnection.from_node_id]', back_populates='from_node')
    topo_elec_connection_to_interface: Mapped[list['TopoElecConnection']] = relationship('TopoElecConnection', foreign_keys='[TopoElecConnection.to_interface_id]', back_populates='to_interface')
    topo_elec_connection_to_node: Mapped[list['TopoElecConnection']] = relationship('TopoElecConnection', foreign_keys='[TopoElecConnection.to_node_id]', back_populates='to_node')


class CfgAdsConn(CfgConnection):
    __tablename__ = 'cfg_ads_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_ads_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_ads_conn_cfg_ads_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_ads_point_table_id'], ['whale.cfg_ads_point_table.cfg_ads_point_table_id'], name='cfg_ads_conn_cfg_ads_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_ads_conn_id', name='cfg_ads_conn_pkey'),
        {'comment': '【配置数据】ADS 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_ads_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_ads_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='ADS 设备能力点表。')
    host: Mapped[Any] = mapped_column(INET, nullable=False, comment='ADS 设备 IP。')
    ams_net_id: Mapped[str] = mapped_column(Text, nullable=False, comment='AMS Net ID。')
    ams_port: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('851'), comment='AMS 端口。')
    route_name: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 路由名称。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='ADS 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_ads_point_table: Mapped['CfgAdsPointTable'] = relationship('CfgAdsPointTable', back_populates='cfg_ads_conn')


class CfgConnectionStatusEvent(Base):
    __tablename__ = 'cfg_connection_status_event'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_connection_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_connection_status_event_cfg_connection_id_fkey'),
        ForeignKeyConstraint(['connection_status_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_connection_status_event_connection_status_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_connection_status_event_id', name='cfg_connection_status_event_pkey'),
        {'comment': '【事件数据】连接运行状态事件。记录在线、离线、超时、异常、恢复等运行状态，不表达配置生命周期。',
     'schema': 'whale'}
    )

    cfg_connection_status_event_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    cfg_connection_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='通用连接主键。')
    connection_status_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='连接运行状态，取值来自 ref_code.ref_type=CONNECTION_STATUS。')
    occurred_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='状态事件发生时间。')
    message_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='状态事件中文说明。')
    message_en: Mapped[str] = mapped_column(Text, nullable=False, comment='状态事件英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_connection: Mapped['CfgConnection'] = relationship('CfgConnection', back_populates='cfg_connection_status_event')
    connection_status_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='cfg_connection_status_event')


class CfgGridDispatchConnection(Base):
    __tablename__ = 'cfg_grid_dispatch_connection'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_connection_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_grid_dispatch_connection_cfg_connection_id_fkey'),
        ForeignKeyConstraint(['channel_role_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_grid_dispatch_connection_channel_role_ref_id_fkey'),
        ForeignKeyConstraint(['dispatch_level_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_grid_dispatch_connection_dispatch_level_ref_id_fkey'),
        ForeignKeyConstraint(['power_plant_id'], ['whale.org_power_plant.org_power_plant_id'], name='cfg_grid_dispatch_connection_power_plant_id_fkey'),
        PrimaryKeyConstraint('cfg_grid_dispatch_connection_id', name='cfg_grid_dispatch_connection_pkey'),
        UniqueConstraint('dispatch_connection_identifier', 'record_revision', name='cfg_grid_dispatch_connection_dispatch_connection_identifier_key'),
        {'comment': '【配置数据】电网调度连接信息。记录并网型电场与调度主站、集控或省地调之间的调度通信连接，并强制关联电场。',
     'schema': 'whale'}
    )

    cfg_grid_dispatch_connection_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    power_plant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='调度连接所属并网型电场。')
    cfg_connection_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='对应通用协议连接配置。')
    dispatch_connection_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='调度连接业务稳定标识，不引用 ref_code.code。')
    dispatch_center_name: Mapped[str] = mapped_column(Text, nullable=False, comment='调度机构或调度中心名称。')
    dispatch_level_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='调度层级，取值来自 ref_code.ref_type=DISPATCH_LEVEL。')
    channel_role_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='调度通道角色，取值来自 ref_code.ref_type=DISPATCH_CHANNEL_ROLE。')
    channel_name: Mapped[str] = mapped_column(Text, nullable=False, comment='调度通信通道名称，例如省调 IEC104 主通道。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='调度连接中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='调度连接英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    local_address: Mapped[Optional[str]] = mapped_column(Text, comment='本场站侧调度通信地址、ASDU 公共地址或链路地址。')
    remote_address: Mapped[Optional[str]] = mapped_column(Text, comment='调度主站侧通信地址或链路地址。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_connection: Mapped['CfgConnection'] = relationship('CfgConnection', back_populates='cfg_grid_dispatch_connection')
    channel_role_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[channel_role_ref_id], back_populates='cfg_grid_dispatch_connection_channel_role_ref')
    dispatch_level_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[dispatch_level_ref_id], back_populates='cfg_grid_dispatch_connection_dispatch_level_ref')
    power_plant: Mapped['OrgPowerPlant'] = relationship('OrgPowerPlant', back_populates='cfg_grid_dispatch_connection')


class CfgHttpRestConn(CfgConnection):
    __tablename__ = 'cfg_http_rest_conn'
    __table_args__ = (
        ForeignKeyConstraint(['auth_type_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_http_rest_conn_auth_type_ref_id_fkey'),
        ForeignKeyConstraint(['cfg_http_rest_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_http_rest_conn_cfg_http_rest_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_http_rest_point_table_id'], ['whale.cfg_http_rest_point_table.cfg_http_rest_point_table_id'], name='cfg_http_rest_conn_cfg_http_rest_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_http_rest_conn_id', name='cfg_http_rest_conn_pkey'),
        {'comment': '【配置数据】HTTP REST 连接参数。保存第三方系统或平台 REST API 连接参数，通用身份、资产归属和协议类型由 '
                'cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_http_rest_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_http_rest_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='HTTP REST 设备能力点表。')
    base_url: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST Base URL，样例统一使用 127.0.0.1 和本地 simulator 端口。')
    host_address: Mapped[Any] = mapped_column(INET, nullable=False, comment='HTTP REST 服务地址。')
    port: Mapped[int] = mapped_column(Integer, nullable=False, comment='HTTP REST 服务端口。')
    auth_type_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='认证类型，取值来自 ref_code.ref_type=HTTP_AUTH_TYPE。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='HTTP 请求超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='HTTP REST 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    username: Mapped[Optional[str]] = mapped_column(Text, comment='用户名；无认证或 token 认证时可为空。')

    auth_type_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='cfg_http_rest_conn')
    cfg_http_rest_point_table: Mapped['CfgHttpRestPointTable'] = relationship('CfgHttpRestPointTable', back_populates='cfg_http_rest_conn')


class CfgIec101Conn(CfgConnection):
    __tablename__ = 'cfg_iec101_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_iec101_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_iec101_conn_cfg_iec101_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_iec101_point_table_id'], ['whale.cfg_iec101_point_table.cfg_iec101_point_table_id'], name='cfg_iec101_conn_cfg_iec101_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_iec101_conn_id', name='cfg_iec101_conn_pkey'),
        {'comment': '【配置数据】IEC101 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_iec101_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_iec101_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC101 设备能力点表。')
    serial_port: Mapped[str] = mapped_column(Text, nullable=False, comment='串口名称。')
    baud_rate: Mapped[int] = mapped_column(Integer, nullable=False, comment='串口波特率。')
    link_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='链路地址。')
    common_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='默认公共地址。')
    balanced_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'), comment='是否平衡式传输。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC101 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_iec101_point_table: Mapped['CfgIec101PointTable'] = relationship('CfgIec101PointTable', back_populates='cfg_iec101_conn')


class CfgIec104Conn(CfgConnection):
    __tablename__ = 'cfg_iec104_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_iec104_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_iec104_conn_cfg_iec104_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_iec104_point_table_id'], ['whale.cfg_iec104_point_table.cfg_iec104_point_table_id'], name='cfg_iec104_conn_cfg_iec104_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_iec104_conn_id', name='cfg_iec104_conn_pkey'),
        {'comment': '【配置数据】IEC104 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_iec104_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_iec104_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC104 设备能力点表。')
    host: Mapped[Any] = mapped_column(INET, nullable=False, comment='IEC104 主站连接的远端 IP。')
    port: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('2404'), comment='IEC104 TCP 端口。')
    common_address: Mapped[int] = mapped_column(Integer, nullable=False, comment='默认公共地址。')
    t0_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('30000'), comment='建立连接超时时间。')
    t1_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('15000'), comment='发送或测试确认超时时间。')
    t2_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('10000'), comment='无数据确认超时时间。')
    t3_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('20000'), comment='空闲测试间隔。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC104 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_iec104_point_table: Mapped['CfgIec104PointTable'] = relationship('CfgIec104PointTable', back_populates='cfg_iec104_conn')


class CfgIec61850GooseConn(CfgConnection):
    __tablename__ = 'cfg_iec61850_goose_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_iec61850_goose_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_iec61850_goose_conn_cfg_iec61850_goose_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_goose_point_table_id'], ['whale.cfg_iec61850_goose_point_table.cfg_iec61850_goose_point_table_id'], name='cfg_iec61850_goose_conn_cfg_iec61850_goose_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_goose_conn_id', name='cfg_iec61850_goose_conn_pkey'),
        {'comment': '【配置数据】IEC61850 GOOSE 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 '
                'cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_iec61850_goose_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_iec61850_goose_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC61850 GOOSE 设备能力点表。')
    network_interface: Mapped[str] = mapped_column(Text, nullable=False, comment='接收 GOOSE 的网络接口名称。')
    appid: Mapped[int] = mapped_column(Integer, nullable=False, comment='GOOSE APPID。')
    multicast_mac: Mapped[str] = mapped_column(Text, nullable=False, comment='GOOSE 目的组播 MAC。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 GOOSE 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    vlan_id: Mapped[Optional[int]] = mapped_column(Integer, comment='VLAN ID。')

    cfg_iec61850_goose_point_table: Mapped['CfgIec61850GoosePointTable'] = relationship('CfgIec61850GoosePointTable', back_populates='cfg_iec61850_goose_conn')


class CfgIec61850MmsConn(CfgConnection):
    __tablename__ = 'cfg_iec61850_mms_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_iec61850_mms_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_iec61850_mms_conn_cfg_iec61850_mms_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_mms_point_table_id'], ['whale.cfg_iec61850_mms_point_table.cfg_iec61850_mms_point_table_id'], name='cfg_iec61850_mms_conn_cfg_iec61850_mms_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_mms_conn_id', name='cfg_iec61850_mms_conn_pkey'),
        {'comment': '【配置数据】IEC61850 MMS 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection '
                '表表达。',
     'schema': 'whale'}
    )

    cfg_iec61850_mms_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_iec61850_mms_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC61850 MMS 设备能力点表。')
    host: Mapped[Any] = mapped_column(INET, nullable=False, comment='IED 或网关 IP。')
    port: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('102'), comment='MMS TCP 端口。')
    ied_name: Mapped[str] = mapped_column(Text, nullable=False, comment='IED 名称。')
    access_point: Mapped[str] = mapped_column(Text, nullable=False, comment='访问点名称。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 MMS 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_iec61850_mms_point_table: Mapped['CfgIec61850MmsPointTable'] = relationship('CfgIec61850MmsPointTable', back_populates='cfg_iec61850_mms_conn')


class CfgIec61850SvConn(CfgConnection):
    __tablename__ = 'cfg_iec61850_sv_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_iec61850_sv_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_iec61850_sv_conn_cfg_iec61850_sv_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_iec61850_sv_point_table_id'], ['whale.cfg_iec61850_sv_point_table.cfg_iec61850_sv_point_table_id'], name='cfg_iec61850_sv_conn_cfg_iec61850_sv_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_iec61850_sv_conn_id', name='cfg_iec61850_sv_conn_pkey'),
        {'comment': '【配置数据】IEC61850 SV 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection '
                '表表达。',
     'schema': 'whale'}
    )

    cfg_iec61850_sv_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_iec61850_sv_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='IEC61850 SV 设备能力点表。')
    network_interface: Mapped[str] = mapped_column(Text, nullable=False, comment='接收 SV 的网络接口名称。')
    sv_id: Mapped[str] = mapped_column(Text, nullable=False, comment='采样值 SV ID。')
    appid: Mapped[int] = mapped_column(Integer, nullable=False, comment='SV APPID。')
    sample_rate_hz: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('4000'), comment='SV 采样率，属于连接/流配置，用于 SVSubscriber/SVPublisher 初始化，不属于单个变量描述。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='IEC61850 SV 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    vlan_id: Mapped[Optional[int]] = mapped_column(Integer, comment='VLAN ID。')

    cfg_iec61850_sv_point_table: Mapped['CfgIec61850SvPointTable'] = relationship('CfgIec61850SvPointTable', back_populates='cfg_iec61850_sv_conn')


class CfgModbusConn(CfgConnection):
    __tablename__ = 'cfg_modbus_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_modbus_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_modbus_conn_cfg_modbus_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_modbus_point_table_id'], ['whale.cfg_modbus_point_table.cfg_modbus_point_table_id'], name='cfg_modbus_conn_cfg_modbus_point_table_id_fkey'),
        ForeignKeyConstraint(['transport_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_modbus_conn_transport_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_modbus_conn_id', name='cfg_modbus_conn_pkey'),
        {'comment': '【配置数据】Modbus 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_modbus_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_modbus_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='Modbus 设备能力点表。')
    host: Mapped[Any] = mapped_column(INET, nullable=False, comment='Modbus TCP 主机 IP。')
    port: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('502'), comment='Modbus TCP 端口。')
    slave_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='Modbus 从站地址。')
    transport_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='传输方式，取值来自 ref_code.ref_type=TRANSPORT。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='Modbus 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')

    cfg_modbus_point_table: Mapped['CfgModbusPointTable'] = relationship('CfgModbusPointTable', back_populates='cfg_modbus_conn')
    transport_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='cfg_modbus_conn')


class CfgMqttConn(CfgConnection):
    __tablename__ = 'cfg_mqtt_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_mqtt_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_mqtt_conn_cfg_mqtt_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_mqtt_point_table_id'], ['whale.cfg_mqtt_point_table.cfg_mqtt_point_table_id'], name='cfg_mqtt_conn_cfg_mqtt_point_table_id_fkey'),
        PrimaryKeyConstraint('cfg_mqtt_conn_id', name='cfg_mqtt_conn_pkey'),
        {'comment': '【配置数据】MQTT 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_mqtt_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_mqtt_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='MQTT 设备能力点表。')
    broker_url: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT Broker URL。')
    client_id: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT Client ID。')
    qos: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='默认 QoS。')
    clean_session: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否清理会话。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='MQTT 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    username: Mapped[Optional[str]] = mapped_column(Text, comment='用户名；匿名连接时为空。')

    cfg_mqtt_point_table: Mapped['CfgMqttPointTable'] = relationship('CfgMqttPointTable', back_populates='cfg_mqtt_conn')


class CfgOpcuaConn(CfgConnection):
    __tablename__ = 'cfg_opcua_conn'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_opcua_conn_id'], ['whale.cfg_connection.cfg_connection_id'], name='cfg_opcua_conn_cfg_opcua_conn_id_fkey'),
        ForeignKeyConstraint(['cfg_opcua_point_table_id'], ['whale.cfg_opcua_point_table.cfg_opcua_point_table_id'], name='cfg_opcua_conn_cfg_opcua_point_table_id_fkey'),
        ForeignKeyConstraint(['security_mode_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_opcua_conn_security_mode_ref_id_fkey'),
        ForeignKeyConstraint(['security_policy_ref_id'], ['whale.ref_code.ref_code_id'], name='cfg_opcua_conn_security_policy_ref_id_fkey'),
        PrimaryKeyConstraint('cfg_opcua_conn_id', name='cfg_opcua_conn_pkey'),
        {'comment': '【配置数据】OPC UA 连接参数。保存协议专属连接参数，通用身份、资产归属和协议类型由 cfg_connection 表表达。',
     'schema': 'whale'}
    )

    cfg_opcua_conn_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment='协议连接参数表主键，同时外键引用通用连接父表 cfg_connection。')
    cfg_opcua_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='OPC UA 设备能力点表。')
    endpoint_url: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA Endpoint URL。')
    security_policy_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='安全策略，取值来自 ref_code.ref_type=OPCUA_SECURITY_POLICY。')
    security_mode_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='安全模式，取值来自 ref_code.ref_type=OPCUA_SECURITY_MODE。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='协议请求或会话超时时间，单位毫秒。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 连接参数中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='OPC UA 连接参数英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    username: Mapped[Optional[str]] = mapped_column(Text, comment='用户名；匿名连接时为空。')

    cfg_opcua_point_table: Mapped['CfgOpcuaPointTable'] = relationship('CfgOpcuaPointTable', back_populates='cfg_opcua_conn')
    security_mode_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[security_mode_ref_id], back_populates='cfg_opcua_conn_security_mode_ref')
    security_policy_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[security_policy_ref_id], back_populates='cfg_opcua_conn_security_policy_ref')


class SecEmployeeRole(Base):
    __tablename__ = 'sec_employee_role'
    __table_args__ = (
        ForeignKeyConstraint(['employee_id'], ['whale.emp_employee.emp_employee_id'], name='sec_employee_role_employee_id_fkey'),
        ForeignKeyConstraint(['role_id'], ['whale.sec_role.sec_role_id'], name='sec_employee_role_role_id_fkey'),
        PrimaryKeyConstraint('sec_employee_role_id', name='sec_employee_role_pkey'),
        UniqueConstraint('employee_id', 'role_id', 'record_revision', name='sec_employee_role_employee_id_role_id_record_revision_key'),
        {'comment': '【安全主数据】员工角色分配。表示员工被赋予哪些系统角色。', 'schema': 'whale'}
    )

    sec_employee_role_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    employee_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='员工主键。')
    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='角色主键。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    employee: Mapped['EmpEmployee'] = relationship('EmpEmployee', back_populates='sec_employee_role')
    role: Mapped['SecRole'] = relationship('SecRole', back_populates='sec_employee_role')


class TaskConfig(Base):
    __tablename__ = 'task_config'
    __table_args__ = (
        ForeignKeyConstraint(['cfg_connection_id'], ['whale.cfg_connection.cfg_connection_id'], name='task_config_cfg_connection_id_fkey'),
        ForeignKeyConstraint(['cfg_protocol_task_type_mapping_id'], ['whale.cfg_protocol_task_type_mapping.cfg_protocol_task_type_mapping_id'], name='task_config_cfg_protocol_task_type_mapping_id_fkey'),
        ForeignKeyConstraint(['task_id'], ['whale.task.task_id'], name='task_config_task_id_fkey'),
        ForeignKeyConstraint(['task_point_table_id'], ['whale.task_point_table.task_point_table_id'], name='task_config_task_point_table_id_fkey'),
        ForeignKeyConstraint(['trigger_mode_ref_id'], ['whale.ref_code.ref_code_id'], name='task_config_trigger_mode_ref_id_fkey'),
        PrimaryKeyConstraint('task_config_id', name='task_config_pkey'),
        {'comment': '【配置数据】统一协议交互任务配置快照。绑定任务身份、连接、协议操作与任务类型映射、任务点表和调度参数。',
     'schema': 'whale'}
    )

    task_config_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务身份主键。')
    cfg_connection_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务绑定的通用连接。')
    cfg_protocol_task_type_mapping_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='协议原生操作与平台任务类型映射，用于确定协议、原生操作、任务类型、大类、方向、角色和点表用途。')
    task_point_table_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务实际使用的点表。')
    trigger_mode_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务触发方式，取值来自 ref_code.ref_type=TASK_TRIGGER_MODE。')
    timeout_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5000'), comment='任务级默认超时时间，单位毫秒。')
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('3'), comment='任务级默认重试次数。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='任务配置中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='任务配置英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一任务配置变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    cfg_connection: Mapped['CfgConnection'] = relationship('CfgConnection', back_populates='task_config')
    cfg_protocol_task_type_mapping: Mapped['CfgProtocolTaskTypeMapping'] = relationship('CfgProtocolTaskTypeMapping', back_populates='task_config')
    task: Mapped['Task'] = relationship('Task', back_populates='task_config')
    task_point_table: Mapped['TaskPointTable'] = relationship('TaskPointTable', back_populates='task_config')
    trigger_mode_ref: Mapped['RefCode'] = relationship('RefCode', back_populates='task_config')
    task_param_value: Mapped[list['TaskParamValue']] = relationship('TaskParamValue', back_populates='task_config')
    task_run: Mapped[list['TaskRun']] = relationship('TaskRun', back_populates='task_config')


class TopoCommConnection(Base):
    __tablename__ = 'topo_comm_connection'
    __table_args__ = (
        ForeignKeyConstraint(['edge_id'], ['whale.topo_comm_element.topo_comm_element_id'], name='topo_comm_connection_edge_id_fkey'),
        ForeignKeyConstraint(['from_interface_id'], ['whale.topo_comm_element.topo_comm_element_id'], name='topo_comm_connection_from_interface_id_fkey'),
        ForeignKeyConstraint(['from_node_id'], ['whale.topo_comm_element.topo_comm_element_id'], name='topo_comm_connection_from_node_id_fkey'),
        ForeignKeyConstraint(['to_interface_id'], ['whale.topo_comm_element.topo_comm_element_id'], name='topo_comm_connection_to_interface_id_fkey'),
        ForeignKeyConstraint(['to_node_id'], ['whale.topo_comm_element.topo_comm_element_id'], name='topo_comm_connection_to_node_id_fkey'),
        PrimaryKeyConstraint('topo_comm_connection_id', name='topo_comm_connection_pkey'),
        {'comment': '【配置数据】通信拓扑连接关系。按 '
                'from_node、from_interface、edge、to_node、to_interface 描述通信连接。',
     'schema': 'whale'}
    )

    topo_comm_connection_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    from_node_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='起点通信节点元素。')
    from_interface_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='起点通信接口元素，样例与正式建模要求必须填写。')
    edge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='通信链路元素，例如光纤、铜缆、串口链路。')
    to_node_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='终点通信节点元素。')
    to_interface_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='终点通信接口元素，样例与正式建模要求必须填写。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='通信连接中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='通信连接英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    edge: Mapped['TopoCommElement'] = relationship('TopoCommElement', foreign_keys=[edge_id], back_populates='topo_comm_connection_edge')
    from_interface: Mapped['TopoCommElement'] = relationship('TopoCommElement', foreign_keys=[from_interface_id], back_populates='topo_comm_connection_from_interface')
    from_node: Mapped['TopoCommElement'] = relationship('TopoCommElement', foreign_keys=[from_node_id], back_populates='topo_comm_connection_from_node')
    to_interface: Mapped['TopoCommElement'] = relationship('TopoCommElement', foreign_keys=[to_interface_id], back_populates='topo_comm_connection_to_interface')
    to_node: Mapped['TopoCommElement'] = relationship('TopoCommElement', foreign_keys=[to_node_id], back_populates='topo_comm_connection_to_node')


class TopoElecConnection(Base):
    __tablename__ = 'topo_elec_connection'
    __table_args__ = (
        ForeignKeyConstraint(['edge_id'], ['whale.topo_elec_element.topo_elec_element_id'], name='topo_elec_connection_edge_id_fkey'),
        ForeignKeyConstraint(['from_interface_id'], ['whale.topo_elec_element.topo_elec_element_id'], name='topo_elec_connection_from_interface_id_fkey'),
        ForeignKeyConstraint(['from_node_id'], ['whale.topo_elec_element.topo_elec_element_id'], name='topo_elec_connection_from_node_id_fkey'),
        ForeignKeyConstraint(['to_interface_id'], ['whale.topo_elec_element.topo_elec_element_id'], name='topo_elec_connection_to_interface_id_fkey'),
        ForeignKeyConstraint(['to_node_id'], ['whale.topo_elec_element.topo_elec_element_id'], name='topo_elec_connection_to_node_id_fkey'),
        PrimaryKeyConstraint('topo_elec_connection_id', name='topo_elec_connection_pkey'),
        {'comment': '【配置数据】电气拓扑连接关系。按 '
                'from_node、from_interface、edge、to_node、to_interface 描述电气原理图连接。',
     'schema': 'whale'}
    )

    topo_elec_connection_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    from_node_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='起点电气节点元素。')
    from_interface_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='起点电气接口元素，样例与正式建模要求必须填写。')
    edge_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='连接边元素，例如线路、电缆、变压器连接段。')
    to_node_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='终点电气节点元素。')
    to_interface_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='终点电气接口元素，样例与正式建模要求必须填写。')
    description_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='电气连接中文说明。')
    description_en: Mapped[str] = mapped_column(Text, nullable=False, comment='电气连接英文说明。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    edge: Mapped['TopoElecElement'] = relationship('TopoElecElement', foreign_keys=[edge_id], back_populates='topo_elec_connection_edge')
    from_interface: Mapped['TopoElecElement'] = relationship('TopoElecElement', foreign_keys=[from_interface_id], back_populates='topo_elec_connection_from_interface')
    from_node: Mapped['TopoElecElement'] = relationship('TopoElecElement', foreign_keys=[from_node_id], back_populates='topo_elec_connection_from_node')
    to_interface: Mapped['TopoElecElement'] = relationship('TopoElecElement', foreign_keys=[to_interface_id], back_populates='topo_elec_connection_to_interface')
    to_node: Mapped['TopoElecElement'] = relationship('TopoElecElement', foreign_keys=[to_node_id], back_populates='topo_elec_connection_to_node')


class TaskParamValue(Base):
    __tablename__ = 'task_param_value'
    __table_args__ = (
        ForeignKeyConstraint(['task_config_id'], ['whale.task_config.task_config_id'], name='task_param_value_task_config_id_fkey'),
        ForeignKeyConstraint(['task_param_def_id'], ['whale.task_param_def.task_param_def_id'], name='task_param_value_task_param_def_id_fkey'),
        PrimaryKeyConstraint('task_param_value_id', name='task_param_value_pkey'),
        UniqueConstraint('task_config_id', 'task_param_def_id', 'record_revision', name='task_param_value_task_config_id_task_param_def_id_record_re_key'),
        {'comment': '【配置数据】任务参数值表。保存某个任务配置快照的实际参数值。', 'schema': 'whale'}
    )

    task_param_value_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_config_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务配置快照主键。')
    task_param_def_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务参数定义主键。')
    param_value: Mapped[str] = mapped_column(Text, nullable=False, comment='任务参数值文本。应用层按参数定义数据类型解释。')
    record_revision: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'), comment='追加式不可变快照修订号。同一业务稳定标识变更时新增记录并递增修订号，不更新旧记录。')
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'), comment='是否为当前启用记录。修改状态时应新增记录，不更新旧记录。')
    valid_from: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录业务生效开始时间。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    supersedes_id: Mapped[Optional[int]] = mapped_column(BigInteger, comment='被本记录替代的上一版记录主键；为空表示初始版本。')
    valid_to: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='记录业务生效结束时间；为空表示仍然有效。')

    task_config: Mapped['TaskConfig'] = relationship('TaskConfig', back_populates='task_param_value')
    task_param_def: Mapped['TaskParamDef'] = relationship('TaskParamDef', back_populates='task_param_value')


class TaskRun(Base):
    __tablename__ = 'task_run'
    __table_args__ = (
        ForeignKeyConstraint(['run_scope_ref_id'], ['whale.ref_code.ref_code_id'], name='task_run_run_scope_ref_id_fkey'),
        ForeignKeyConstraint(['run_status_ref_id'], ['whale.ref_code.ref_code_id'], name='task_run_run_status_ref_id_fkey'),
        ForeignKeyConstraint(['task_config_id'], ['whale.task_config.task_config_id'], name='task_run_task_config_id_fkey'),
        PrimaryKeyConstraint('task_run_id', name='task_run_pkey'),
        UniqueConstraint('run_identifier', name='task_run_run_identifier_key'),
        {'comment': '【过程数据】任务运行记录表。记录协议交互任务的一次运行、一次会话、一次命令、一次发布或一次响应服务窗口，不记录高频轮询每一轮明细。',
     'schema': 'whale'}
    )

    task_run_id: Mapped[int] = mapped_column(BigInteger, Identity(start=1, increment=1, minvalue=1, maxvalue=9223372036854775807, cycle=False, cache=1), primary_key=True, autoincrement=True, comment='自增代理主键，列名统一为表名_id，满足 SQLAlchemy ORM 映射要求。')
    task_config_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务配置快照主键。')
    run_identifier: Mapped[str] = mapped_column(Text, nullable=False, comment='任务运行记录业务稳定标识，不引用 ref_code.code。')
    run_scope_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='任务运行记录粒度，取值来自 ref_code.ref_type=RUN_SCOPE。')
    run_status_ref_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment='运行状态，取值来自 ref_code.ref_type=RUN_STATUS。')
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, comment='运行开始时间。')
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='成功采集、写入、控制、发布、上报或响应数量。')
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'), comment='失败采集、写入、控制、发布、上报或响应数量。')
    message_zh: Mapped[str] = mapped_column(Text, nullable=False, comment='运行记录中文说明。')
    message_en: Mapped[str] = mapped_column(Text, nullable=False, comment='运行记录英文说明。')
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'), comment='记录创建时间。')
    created_by: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'system'::text"), comment='记录创建人或系统账号。')
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), comment='运行完成时间；未完成时为空。')

    run_scope_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[run_scope_ref_id], back_populates='task_run_run_scope_ref')
    run_status_ref: Mapped['RefCode'] = relationship('RefCode', foreign_keys=[run_status_ref_id], back_populates='task_run_run_status_ref')
    task_config: Mapped['TaskConfig'] = relationship('TaskConfig', back_populates='task_run')
