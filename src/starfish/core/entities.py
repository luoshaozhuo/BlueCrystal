"""Whale 运行视图的强类型行模型。

这些 dataclass 仅描述视图列契约，不负责查询、连接生命周期或协议运行时行为。
"""

from decimal import Decimal
from typing import ClassVar

from pydantic.dataclasses import dataclass

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

@dataclass
class EntityBase:
    """所有实体的基类。"""
    view_name: ClassVar[str] = ""

@dataclass
class BaseConnection(EntityBase):
    view_name: ClassVar[str] = "vw_comm_connection"
    connection_id: int
    protocol: str
    host: str
    port: int
    reconnect_enabled: bool
    reconnect_interval_ms: int
    src_point_table_id: int
    sink_point_table_id: int


@dataclass
class IEC104Connection(BaseConnection):
    view_name: ClassVar[str] = "vw_comm_iec104_connection"
    t0_ms: int
    t1_ms: int
    t2_ms: int
    t3_ms: int
    k_value: int
    w_value: int


@dataclass
class ADSConnection(BaseConnection):
    view_name: ClassVar[str] = "vw_comm_das_connection"
    protocol_role: str


@dataclass
class BasePointItem(EntityBase):
    view_name: ClassVar[str] = ""
    point_table_id: int
    point_item_id: int
    business_semantic_identifier: str
    business_semantic_name_zh: str
    physical_quantity_category: str
    data_type: str
    unit: str
    scale_factor: Decimal
    offset_value: Decimal
    value_min: Decimal | None
    value_max: Decimal | None
    allowed_values: JsonValue

@dataclass
class IEC104SrcPointItem(BasePointItem):
    """IEC104 Source 点项视图的完整行契约。"""

    view_name: ClassVar[str] = "vw_src_iec104_point_item"
    value_update_mode: str
    value_update_interval_ms: int | None
    iec104_type_id: int
    iec104_type: str
    common_address: int
    information_object_address: int
    general_interrogation_enabled: bool
    general_interrogation_group: int | None
    counter_interrogation_enabled: bool
    periodic_transmission_enabled: bool
    periodic_interval_ms: int | None
    spontaneous_transmission_enabled: bool
    deadband: Decimal | None
    background_transmission_enabled: bool
    quality_enabled: bool


@dataclass
class IEC104SinkPointItem(BasePointItem):
    """IEC104 Sink 点项视图的完整行契约。"""

    view_name: ClassVar[str] = "vw_sink_iec104_point_item"
    iec104_type_id: int
    iec104_type: str
    common_address: int
    information_object_address: int
    general_interrogation_enabled: bool
    general_interrogation_group: int | None
    counter_interrogation_enabled: bool
    periodic_transmission_enabled: bool
    periodic_interval_ms: int | None
    spontaneous_transmission_enabled: bool
    deadband: Decimal | None
    background_transmission_enabled: bool
    quality_enabled: bool


@dataclass
class ADSSrcPointItem(BasePointItem):
    """ADS Source 点项视图的完整行契约。

    类名保留现有 ``DAS`` 公开名称；其数据契约对应 Whale 的 ADS view。
    """

    view_name: ClassVar[str] = "vw_src_ads_point_item"
    value_update_mode: str
    value_update_interval_ms: int | None
    addressing_mode: str
    ads_data_type: str
    symbol_name: str | None
    index_group: int | None
    index_offset: int | None
    notification_mode: str
    cycle_time_ms: int | None
    max_delay_ms: int | None


@dataclass
class ADSSinkPointItem(BasePointItem):
    """ADS Sink 点项视图的完整行契约。

    类名保留现有 ``DAS`` 公开名称；其数据契约对应 Whale 的 ADS view。
    """

    view_name: ClassVar[str] = "vw_sink_ads_point_item"
    addressing_mode: str
    ads_data_type: str
    symbol_name: str | None
    index_group: int | None
    index_offset: int | None
