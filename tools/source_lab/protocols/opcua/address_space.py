"""OPC UA 地址空间模型与渲染器。

负责：将协议无关的 SimulatedSource 转换为统一 OPC UA 地址空间描述，
再分别渲染为两种格式：
1. NodeSet XML：供 simulator address-space generation 使用；
2. TSV：供 open62541 C runner 使用。
不负责：读数据库、启动 server、管理进程、client 读取。
数据流：SimulatedSource -> build_address_space() -> OpcUaAddressSpace
         -> render_nodeset_xml() -> XML 字符串
         -> render_open62541_tsv() -> TSV 字符串
设计边界：类型映射使用全局字典 _SCADA_TO_OPCUA_TYPE，不匹配时回退到 Double。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from tools.source_lab.model import SimulatedPoint, SimulatedSource, SourceConnection


_SCADA_TO_OPCUA_TYPE: dict[str, str] = {
    "FLOAT64": "Double",
    "FLOAT32": "Double",
    "DOUBLE": "Double",
    "FLOAT": "Double",
    "INT8": "Int32",
    "INT16": "Int32",
    "INT32": "Int32",
    "INT64": "Int32",
    "INT8U": "Int32",
    "INT16U": "Int32",
    "INT32U": "Int32",
    "UINT8": "Int32",
    "UINT16": "Int32",
    "UINT32": "Int32",
    "BOOLEAN": "Boolean",
    "BOOL": "Boolean",
    "VISSTRING255": "String",
    "STRING": "String",
    "CODED_ENUM": "Int32",
    "TIMESTAMP": "String",
    "DATETIME": "String",
    "OCTET_STRING": "String",
}


@dataclass(frozen=True, slots=True)
class OpcUaObjectSpec:
    """OPC UA 地址空间中的单个对象节点描述。

    Attributes:
        node_id: 节点标识符（逻辑路径）。
        browse_name: 浏览名称。
        display_name: 显示名称。
        parent_node_id: 父节点标识符，根节点为 None。
    """

    node_id: str
    browse_name: str
    display_name: str
    parent_node_id: str | None


@dataclass(frozen=True, slots=True)
class OpcUaVariableSpec:
    """OPC UA 地址空间中的单个变量节点描述。

    Attributes:
        node_id: 变量节点标识符（完整逻辑路径）。
        browse_name: 浏览名称。
        display_name: 显示名称（可选含单位后缀）。
        parent_node_id: 所属 LN 对象节点标识符。
        data_type: OPC UA 数据类型名称。
        initial_value: 初始值字符串。
        point_key: 关联的 SimulatedPoint.key，用于写入映射。
    """

    node_id: str
    browse_name: str
    display_name: str
    parent_node_id: str
    data_type: str
    initial_value: str
    point_key: str


@dataclass(frozen=True, slots=True)
class OpcUaAddressSpace:
    """后端无关的 OPC UA 地址空间描述。

    Attributes:
        endpoint: OPC UA 端点 URL。
        namespace_uri: 应用的命名空间 URI。
        objects: 对象节点元组。
        variables: 变量节点元组。
    """

    endpoint: str
    namespace_uri: str
    objects: tuple[OpcUaObjectSpec, ...]
    variables: tuple[OpcUaVariableSpec, ...]


def build_endpoint(connection: SourceConnection) -> str:
    """从连接配置构建 OPC UA 端点 URL。

    Args:
        connection: 源连接配置，包含传输协议、主机和端口。

    Returns:
        OPC UA 端点字符串，如 opc.tcp://host:port。
    """
    transport = connection.transport.strip().lower()
    scheme = "opc.tcp" if transport == "tcp" else f"opc.{transport}"
    return f"{scheme}://{connection.host}:{connection.port}"


def opcua_data_type(scada_type: str | None) -> str:
    """将内部 SCADA 数据类型映射为 OPC UA 标量数据类型名。

    Args:
        scada_type: 内部点位数据类型字符串。

    Returns:
        OPC UA 标量类型名，无匹配时回退到 Double。
    """
    normalized = str(scada_type or "FLOAT64").strip().upper()
    return _SCADA_TO_OPCUA_TYPE.get(normalized, "Double")


def logical_path(connection: SourceConnection, point: SimulatedPoint) -> str:
    """构建稳定逻辑 NodeId 路径：IED.LD.LN.DO。

    Args:
        connection: 源连接配置，包含 IED 和 LD 名称。
        point: 模拟点位定义，包含 LN 和 DO 名称。

    Returns:
        逻辑字符串 NodeId 路径。
    """
    return f"{connection.ied_name}.{connection.ld_name}.{point.ln_name}.{point.do_name}"


def ld_path(connection: SourceConnection) -> str:
    """构建 LD 对象节点的 NodeId 路径。

    Args:
        connection: 源连接配置。

    Returns:
        LD 节点路径：IED.LD。
    """
    return f"{connection.ied_name}.{connection.ld_name}"


def ln_path(connection: SourceConnection, point: SimulatedPoint) -> str:
    """构建 LN 对象节点的 NodeId 路径。

    Args:
        connection: 源连接配置。
        point: 模拟点位定义。

    Returns:
        LN 节点路径：IED.LD.LN。
    """
    return f"{connection.ied_name}.{connection.ld_name}.{point.ln_name}"


def format_initial_value(point: SimulatedPoint) -> str:
    """格式化初始值为 OPC UA 标量变量字符串表示。

    Args:
        point: 模拟点位定义。

    Returns:
        初始值的字符串表示，按数据类型转换格式。
    """
    data_type = opcua_data_type(point.data_type)
    initial = point.initial_value

    if data_type == "Boolean":
        return "true" if bool(initial) else "false"

    if data_type == "Int32":
        return str(int(float(initial or 0)))

    if data_type == "String":
        return str(initial or "")

    return str(float(initial or 0.0))


def build_address_space(source: SimulatedSource) -> OpcUaAddressSpace:
    """构建后端无关的 OPC UA 地址空间描述。

    Args:
        source: 一个模拟源定义。

    Returns:
        OPC UA 地址空间描述。

    Raises:
        ValueError: 缺少 OPC UA 必需的源字段（namespace_uri / ied_name / ld_name）。
    """
    connection = source.connection

    # ---------- 阶段 1: 校验输入参数 ----------
    # 缺少 namespace_uri/ied_name/ld_name 会导致渲染产物不可用，提前止损。
    namespace_uri = str(connection.namespace_uri or "").strip()
    if not namespace_uri:
        raise ValueError("OPC UA source simulator requires connection.namespace_uri")

    if not connection.ied_name.strip():
        raise ValueError("OPC UA source simulator requires connection.ied_name")

    if not connection.ld_name.strip():
        raise ValueError("OPC UA source simulator requires connection.ld_name")

    # ---------- 阶段 2: 构建对象节点层次（WindFarm -> IED -> LD -> LN） ----------
    objects: list[OpcUaObjectSpec] = [
        OpcUaObjectSpec(
            node_id="WindFarm",
            browse_name="WindFarm",
            display_name="WindFarm",
            parent_node_id=None,
        ),
        OpcUaObjectSpec(
            node_id=connection.ied_name,
            browse_name=connection.ied_name,
            display_name=connection.ied_name,
            parent_node_id="WindFarm",
        ),
        OpcUaObjectSpec(
            node_id=ld_path(connection),
            browse_name=connection.ld_name,
            display_name=connection.ld_name,
            parent_node_id=connection.ied_name,
        ),
    ]

    # ---------- 阶段 3: 遍历点位构建变量节点 ----------
    # 相同 LN 下的点位共享一个 LN 对象节点，不重复创建。
    seen_lns: set[str] = set()
    seen_variables: set[str] = set()
    variables: list[OpcUaVariableSpec] = []

    for point in source.points:
        ln_node_id = ln_path(connection, point)
        if ln_node_id not in seen_lns:
            seen_lns.add(ln_node_id)
            objects.append(
                OpcUaObjectSpec(
                    node_id=ln_node_id,
                    browse_name=point.ln_name,
                    display_name=point.ln_name,
                    parent_node_id=ld_path(connection),
                )
            )

        variable_node_id = logical_path(connection, point)
        if variable_node_id in seen_variables:
            continue

        seen_variables.add(variable_node_id)

        display_name = point.display_name or point.do_name
        if point.unit:
            display_name = f"{display_name} ({point.unit})"

        variables.append(
            OpcUaVariableSpec(
                node_id=variable_node_id,
                browse_name=point.do_name,
                display_name=display_name,
                parent_node_id=ln_node_id,
                data_type=opcua_data_type(point.data_type),
                initial_value=format_initial_value(point),
                point_key=point.key,
            )
        )

    return OpcUaAddressSpace(
        endpoint=build_endpoint(connection),
        namespace_uri=namespace_uri,
        objects=tuple(objects),
        variables=tuple(variables),
    )


def render_nodeset_xml(address_space: OpcUaAddressSpace) -> str:
    """将 OPC UA 地址空间描述渲染为 NodeSet XML。

    Args:
        address_space: 后端无关的 OPC UA 地址空间描述。

    Returns:
        NodeSet XML 内容字符串。

    Raises:
        ValueError: 对象节点缺少 parent_node_id。
    """
    last_modified = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---------- 阶段 1: XML 文档头与命名空间定义 ----------
    parts: list[str] = [
        f"""<?xml version="1.0" encoding="utf-8"?>
<UANodeSet xmlns="http://opcfoundation.org/UA/2011/03/UANodeSet.xsd"
           LastModified="{last_modified}">
  <NamespaceUris>
    <Uri>http://opcfoundation.org/UA/</Uri>
    <Uri>{escape(address_space.namespace_uri)}</Uri>
  </NamespaceUris>
  <Aliases>
    <Alias Alias="BaseObjectType">i=58</Alias>
    <Alias Alias="FolderType">i=61</Alias>
    <Alias Alias="BaseDataVariableType">i=63</Alias>
    <Alias Alias="ObjectsFolder">i=85</Alias>
    <Alias Alias="HasTypeDefinition">i=40</Alias>
    <Alias Alias="Organizes">i=35</Alias>
    <Alias Alias="HasComponent">i=47</Alias>
    <Alias Alias="Double">i=11</Alias>
    <Alias Alias="Int32">i=6</Alias>
    <Alias Alias="Boolean">i=1</Alias>
    <Alias Alias="String">i=12</Alias>
  </Aliases>

"""
    ]

    # ---------- 阶段 2: 对象节点渲染 ----------
    for obj in address_space.objects:
        if obj.node_id == "WindFarm":
            # WindFarm 是根对象，parent 为 ObjectsFolder，使用 Organizes 引用
            parts.append(
                f"""  <UAObject NodeId="ns=1;s={escape(obj.node_id)}"
            BrowseName="1:{escape(obj.browse_name)}">
    <DisplayName>{escape(obj.display_name)}</DisplayName>
    <References>
      <Reference ReferenceType="Organizes" IsForward="false">ObjectsFolder</Reference>
      <Reference ReferenceType="HasTypeDefinition">FolderType</Reference>
    </References>
  </UAObject>
"""
            )
            continue

        if obj.parent_node_id is None:
            raise ValueError(f"Object node requires parent_node_id: {obj.node_id}")

        parts.append(
            f"""  <UAObject NodeId="ns=1;s={escape(obj.node_id)}"
            BrowseName="1:{escape(obj.browse_name)}"
            ParentNodeId="ns=1;s={escape(obj.parent_node_id)}">
    <DisplayName>{escape(obj.display_name)}</DisplayName>
    <References>
      <Reference ReferenceType="HasTypeDefinition">BaseObjectType</Reference>
      <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s={escape(obj.parent_node_id)}</Reference>
    </References>
  </UAObject>
"""
        )

    # ---------- 阶段 3: 变量节点渲染 ----------
    for variable in address_space.variables:
        xml_value = escape(variable.initial_value)
        parts.append(
            f"""  <UAVariable NodeId="ns=1;s={escape(variable.node_id)}"
              BrowseName="1:{escape(variable.browse_name)}"
              ParentNodeId="ns=1;s={escape(variable.parent_node_id)}"
              DataType="{escape(variable.data_type)}"
              ValueRank="-1">
    <DisplayName>{escape(variable.display_name)}</DisplayName>
    <References>
      <Reference ReferenceType="HasTypeDefinition">BaseDataVariableType</Reference>
      <Reference ReferenceType="HasComponent" IsForward="false">ns=1;s={escape(variable.parent_node_id)}</Reference>
    </References>
    <Value>
      <{escape(variable.data_type)}>{xml_value}</{escape(variable.data_type)}>
    </Value>
  </UAVariable>
"""
        )

    parts.append("</UANodeSet>\n")
    return "".join(parts)


def render_open62541_tsv(
    address_space: OpcUaAddressSpace,
    extra_records: dict[str, str] | None = None,
) -> str:
    """将 OPC UA 地址空间描述渲染为 open62541 C runner 的 TSV 格式。

    Args:
        address_space: 后端无关的 OPC UA 地址空间描述。
        extra_records: 可选的附加 runner 配置键值对。

    Returns:
        TSV 格式字符串，由 open62541 C runner 消费。

    Raises:
        ValueError: TSV 字段包含制表符或换行符时抛出。
    """
    lines = [
        _tsv_line("endpoint", address_space.endpoint),
        _tsv_line("namespace_uri", address_space.namespace_uri),
    ]

    if extra_records:
        for key, value in extra_records.items():
            lines.append(_tsv_line(key, value))

    for variable in address_space.variables:
        lines.append(
            _tsv_line(
                "node",
                variable.node_id,
                variable.browse_name,
                variable.display_name,
                variable.data_type,
                variable.initial_value,
            )
        )

    return "\n".join(lines) + "\n"


def _tsv_line(*fields: str) -> str:
    """构建一条经过校验的 TSV 行。

    Args:
        *fields: TSV 字段字符串。

    Returns:
        一条制表符分隔的 TSV 行。

    Raises:
        ValueError: 任一字段包含制表符或换行符时抛出，防止破坏 TSV 结构。
    """
    for field in fields:
        if "\t" in field or "\n" in field or "\r" in field:
            raise ValueError(f"TSV field contains unsupported control character: {field!r}")
    return "\t".join(fields)
