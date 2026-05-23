"""Asset 资产模型 — 统一表达风场、风机、部件、通信设备等.

所有真实存在的设备、部件、通信设备都进入 asset_instance.
型号参数使用 asset_model.specifications JSON.
属性定义使用 asset_attribute.
"""

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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from whale.shared.persistence import Base

if TYPE_CHECKING:
    from whale.shared.persistence.orm.organization import Organization
    from whale.shared.persistence.orm.scada_ingest import IED


class AssetType(Base):
    """资产类型 — 定义资产分类.

    风场、集电线、风机、箱变、PCS、BMS、电池簇、SVG、气象站、
    通信管理机、网关、叶片、发电机、变流器等都可以是 asset_type.
    """

    __tablename__ = "asset_type"
    __table_args__ = (
        UniqueConstraint("type_code", name="uq_asset_type_code"),
        {"comment": "资产类型"},
    )

    asset_type_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="资产类型主键"
    )
    type_code: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="资产类型编码，如 WIND_FARM / COLLECTOR_LINE / WTG / BOX_TRANSFORMER / PCS / BMS / SVG / MET_STATION / GATEWAY / BLADE / GENERATOR / CONVERTER"
    )
    type_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="资产类型名称，如 风场 / 集电线 / 风力发电机组 / 箱变 / 储能PCS / 通信管理机 / 叶片"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="资产大类：SITE / ELECTRICAL_DEVICE / GENERATION_DEVICE / STORAGE_DEVICE / COMMUNICATION_DEVICE / COMPONENT"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="资产类型说明"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="扩展属性，如是否允许挂接部件、是否允许作为拓扑节点、默认图标、默认层级等"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class AssetModel(Base):
    """资产型号 — 统一保存所有资产型号.

    风机型号、PCS型号、箱变型号、网关型号、叶片型号、发电机型号都进入此表.
    类型特有参数保存到 specifications JSON.
    """

    __tablename__ = "asset_model"
    __table_args__ = (
        UniqueConstraint("asset_type_id", "model_code", name="uq_asset_model_type_code"),
        {"comment": "资产型号"},
    )

    model_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="资产型号主键"
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=False, comment="所属资产类型"
    )
    model_code: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="型号编码，如 WTG_5MW_VENDOR_A / PCS_2500KW_VENDOR_B / BLADE_85M_VENDOR_C"
    )
    model_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="型号名称"
    )
    manufacturer: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="制造商"
    )
    specifications: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="型号技术参数 JSON，如 {\"rated_power_kw\": 5000, \"hub_height_m\": 120, \"rotor_diameter_m\": 190}"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="型号说明"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="扩展信息，如资料来源、参数版本、厂家私有字段"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class AssetAttribute(Base):
    """资产型号属性定义 — 定义某类资产型号应该有哪些参数.

    用于解释 asset_model.specifications 中的 JSON key.
    例如风机类型定义 rated_power_kw / hub_height_m / rotor_diameter_m.
    """

    __tablename__ = "asset_attribute"
    __table_args__ = (
        UniqueConstraint("asset_type_id", "attribute_name", name="uq_asset_attribute_type_name"),
        {"comment": "资产型号属性定义"},
    )

    attribute_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="属性定义主键"
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=False, comment="所属资产类型"
    )
    attribute_name: Mapped[str] = mapped_column(
        String(128), nullable=False,
        comment="属性名，也是 asset_model.specifications 中的 JSON key，如 rated_power_kw / hub_height_m / rotor_diameter_m"
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="显示名称，如 额定功率 / 轮毂高度 / 叶轮直径"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="属性含义说明"
    )
    data_type_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("scada_data_type.data_type_id"), nullable=True, comment="数据类型 ID"
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="单位，如 kW / m / V / A / %"
    )
    constraint_expr: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="约束表达式，如 value > 0 / 0 <= value <= 100"
    )
    required: Mapped[bool] = mapped_column(
        Boolean, default=False, comment="该型号属性是否必填"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, comment="显示顺序"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="扩展信息"
    )


class AssetInstance(Base):
    """资产实例 — 表示真实存在的资产或部件.

    风场、集电线、风机、箱变、PCS、BMS、电池簇、网关、通信管理机、
    叶片、发电机、变流器都进入此表.
    parent_asset_instance_id 统一表达资产层级和部件归属.
    """

    __tablename__ = "asset_instance"
    __table_args__ = (
        UniqueConstraint("asset_code", name="uq_asset_instance_code"),
        {"comment": "资产实例"},
    )

    asset_instance_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="资产实例主键"
    )
    asset_code: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False,
        comment="资产编码，如 WF_001 / LINE_A / WTG_001 / PCS_001 / GATEWAY_001 / WTG_001_BLADE_A"
    )
    asset_name: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="资产名称，如 一号风场 / A集电线 / 1号风机 / 1号通信管理机 / 1号风机A叶片"
    )
    asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=False, index=True,
        comment="资产类型 ID"
    )
    model_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset_model.model_id"), nullable=True,
        comment="资产型号 ID，可为空；场站层级、线路层级、虚拟资产可能没有具体型号"
    )
    org_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("org_unit.org_id"), nullable=True, comment="所属组织 ID"
    )
    parent_asset_instance_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=True, index=True,
        comment="父资产实例 ID，支持资产树查询，如 风场→集电线→风机→叶片"
    )
    installation_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="安装日期"
    )
    commissioning_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="投运日期"
    )
    location: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="安装位置文本，如 A区3号机位"
    )
    longitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="经度"
    )
    latitude: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="纬度"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE",
        comment="资产状态：ACTIVE / INACTIVE / RETIRED / MAINTENANCE"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="资产实例扩展属性"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    ied: Mapped[Optional["IED"]] = relationship(back_populates="asset_instance")
    org: Mapped[Optional["Organization"]] = relationship(back_populates="asset_instances")


class AssetBOM(Base):
    """资产型号 BOM — 表示某个资产型号由哪些子资产型号组成.

    由于部件也统一进入 asset_type / asset_model，因此 BOM 引用资产类型和型号.
    """

    __tablename__ = "asset_bom"
    __table_args__ = (
        UniqueConstraint("parent_model_id", "child_asset_type_id", "child_model_id",
                         "position_rule", name="uq_asset_bom"),
        {"comment": "资产型号 BOM"},
    )

    bom_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="BOM 主键"
    )
    parent_asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=False, comment="父资产类型 ID"
    )
    parent_model_id: Mapped[int] = mapped_column(
        ForeignKey("asset_model.model_id"), nullable=False, comment="父资产型号 ID"
    )
    child_asset_type_id: Mapped[int] = mapped_column(
        ForeignKey("asset_type.asset_type_id"), nullable=False, comment="子资产类型 ID"
    )
    child_model_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset_model.model_id"), nullable=True, comment="子资产型号 ID，可为空"
    )
    quantity: Mapped[int] = mapped_column(
        Integer, default=1, comment="数量"
    )
    required: Mapped[bool] = mapped_column(
        Boolean, default=True, comment="是否必选部件"
    )
    position_rule: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="部件位置规则，如 BLADE_A / BLADE_B / BLADE_C"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="扩展属性"
    )


class AssetRelation(Base):
    """资产关系 — 用于表达非树形关系.

    例如：网关代理风机、测风塔服务某风机、箱变连接风机、PCS属于某储能单元.
    parent_asset_instance_id 适合表达从属层级，但不适合表达电气连接、通信代理等.
    """

    __tablename__ = "asset_relation"
    __table_args__ = (
        UniqueConstraint("source_asset_instance_id", "target_asset_instance_id",
                         "relation_type", "valid_from", name="uq_asset_relation"),
        {"comment": "资产关系"},
    )

    relation_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="资产关系主键"
    )
    source_asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=False, comment="源资产实例 ID"
    )
    target_asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=False, comment="目标资产实例 ID"
    )
    relation_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="关系类型：PARENT_CHILD / ELECTRICAL_CONNECTED_TO / COMMUNICATION_PROXY_FOR / MEASURES / INSTALLED_IN / CONTROLS / PROTECTS"
    )
    direction: Mapped[str] = mapped_column(
        String(16), default="DIRECTED",
        comment="关系方向：DIRECTED / UNDIRECTED"
    )
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="关系生效时间"
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="关系失效时间"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="扩展信息，如连接端子、线路编号、代理协议、测量范围"
    )


class TopologyGraph(Base):
    """拓扑图定义 — 用于区分不同类型拓扑.

    电气拓扑、通信拓扑、物理层级拓扑、控制拓扑可以并存.
    """

    __tablename__ = "topology_graph"
    __table_args__ = {"comment": "拓扑图定义"}

    topology_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="拓扑图主键"
    )
    topology_code: Mapped[str] = mapped_column(
        String(128), unique=True, nullable=False,
        comment="拓扑编码，如 ELECTRICAL_TOPOLOGY / NETWORK_TOPOLOGY / ASSET_TREE / CONTROL_TOPOLOGY"
    )
    topology_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="拓扑名称，如 电气拓扑 / 通信网络拓扑 / 资产层级拓扑"
    )
    topology_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="拓扑类型：ELECTRICAL / NETWORK / PHYSICAL / CONTROL"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="拓扑说明"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="拓扑扩展信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class TopologyNode(Base):
    """拓扑节点 — 表示某张拓扑图中的节点.

    节点通常关联 asset_instance.
    一个资产可以同时出现在电气拓扑和通信拓扑中.
    """

    __tablename__ = "topology_node"
    __table_args__ = (
        UniqueConstraint("topology_id", "asset_instance_id", name="uq_topology_node"),
        {"comment": "拓扑节点"},
    )

    node_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="拓扑节点主键"
    )
    topology_id: Mapped[int] = mapped_column(
        ForeignKey("topology_graph.topology_id"), nullable=False, comment="所属拓扑图 ID"
    )
    asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=False, comment="关联资产实例 ID"
    )
    node_code: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
        comment="拓扑节点编码，如 WTG_001_NODE / BOX_001_NODE / SWITCH_A_NODE"
    )
    node_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="拓扑节点名称"
    )
    node_role: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True,
        comment="节点角色：SOURCE / LOAD / SWITCH / TRANSFORMER / ROUTER / GATEWAY / TERMINAL"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict, comment="节点扩展信息，如 图形坐标、电压等级、网络区域"
    )


class TopologyEdge(Base):
    """拓扑边 — 表示拓扑图中两个节点之间的连接.

    电气拓扑中表示线路、开关、变压器连接.
    通信拓扑中表示网线、交换机链路、光纤链路.
    """

    __tablename__ = "topology_edge"
    __table_args__ = {"comment": "拓扑边"}

    edge_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="拓扑边主键"
    )
    topology_id: Mapped[int] = mapped_column(
        ForeignKey("topology_graph.topology_id"), nullable=False, comment="所属拓扑图 ID"
    )
    source_node_id: Mapped[int] = mapped_column(
        ForeignKey("topology_node.node_id"), nullable=False, comment="起点节点 ID"
    )
    target_node_id: Mapped[int] = mapped_column(
        ForeignKey("topology_node.node_id"), nullable=False, comment="终点节点 ID"
    )
    edge_type: Mapped[str] = mapped_column(
        String(64), nullable=False,
        comment="边类型：ELECTRICAL_CABLE / FIBER_LINK / ETHERNET_LINK / TRANSFORMER_CONNECTION / SWITCH_CONNECTION"
    )
    direction: Mapped[str] = mapped_column(
        String(16), default="UNDIRECTED",
        comment="方向：DIRECTED / UNDIRECTED"
    )
    voltage_level: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True, comment="电压等级，如 35kV / 10kV / 690V，适用电气拓扑"
    )
    bandwidth_mbps: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="链路带宽 (Mbps)，适用通信拓扑"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE",
        comment="边状态：ACTIVE / DISCONNECTED / MAINTENANCE"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, default=dict,
        comment="扩展信息，如 线路长度、光纤芯号、开关编号、端口号"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
