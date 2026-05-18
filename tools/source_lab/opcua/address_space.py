"""OPC UA address-space model and renderers for source_lab.

本模块负责把协议无关的 SimulatedSource 转换为统一 OPC UA 地址空间描述，
再分别渲染为：

1. NodeSet XML：供 simulator address-space generation 使用；
2. TSV：供 open62541 C runner 使用。

本模块不负责：
- 读数据库；
- 启动 server；
- 管理进程；
- client 读取。
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
    """One OPC UA object node in the simulated address space."""

    node_id: str
    browse_name: str
    display_name: str
    parent_node_id: str | None


@dataclass(frozen=True, slots=True)
class OpcUaVariableSpec:
    """One OPC UA variable node in the simulated address space."""

    node_id: str
    browse_name: str
    display_name: str
    parent_node_id: str
    data_type: str
    initial_value: str
    point_key: str


@dataclass(frozen=True, slots=True)
class OpcUaAddressSpace:
    """Backend-neutral OPC UA address-space description."""

    endpoint: str
    namespace_uri: str
    objects: tuple[OpcUaObjectSpec, ...]
    variables: tuple[OpcUaVariableSpec, ...]


def build_endpoint(connection: SourceConnection) -> str:
    """Build an OPC UA endpoint from source connection settings.

    Args:
        connection: Source connection metadata.

    Returns:
        OPC UA endpoint string.
    """
    transport = connection.transport.strip().lower()
    scheme = "opc.tcp" if transport == "tcp" else f"opc.{transport}"
    return f"{scheme}://{connection.host}:{connection.port}"


def opcua_data_type(scada_type: str | None) -> str:
    """Map internal SCADA data type to OPC UA scalar data type name.

    Args:
        scada_type: Internal point data type.

    Returns:
        OPC UA scalar type name.
    """
    normalized = str(scada_type or "FLOAT64").strip().upper()
    return _SCADA_TO_OPCUA_TYPE.get(normalized, "Double")


def logical_path(connection: SourceConnection, point: SimulatedPoint) -> str:
    """Build stable logical NodeId path: IED.LD.LN.DO.

    Args:
        connection: Source connection metadata.
        point: Simulated point metadata.

    Returns:
        Logical string NodeId path.
    """
    return f"{connection.ied_name}.{connection.ld_name}.{point.ln_name}.{point.do_name}"


def ld_path(connection: SourceConnection) -> str:
    """Build LD object NodeId path.

    Args:
        connection: Source connection metadata.

    Returns:
        LD node path.
    """
    return f"{connection.ied_name}.{connection.ld_name}"


def ln_path(connection: SourceConnection, point: SimulatedPoint) -> str:
    """Build LN object NodeId path.

    Args:
        connection: Source connection metadata.
        point: Simulated point metadata.

    Returns:
        LN node path.
    """
    return f"{connection.ied_name}.{connection.ld_name}.{point.ln_name}"


def format_initial_value(point: SimulatedPoint) -> str:
    """Format initial value for OPC UA scalar variable.

    Args:
        point: Simulated point metadata.

    Returns:
        String representation of the initial value.
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
    """Build backend-neutral OPC UA address-space description.

    Args:
        source: One simulated source.

    Returns:
        OPC UA address-space description.

    Raises:
        ValueError: If required OPC UA source fields are missing.
    """
    connection = source.connection
    namespace_uri = str(connection.namespace_uri or "").strip()
    if not namespace_uri:
        raise ValueError("OPC UA source simulator requires connection.namespace_uri")

    if not connection.ied_name.strip():
        raise ValueError("OPC UA source simulator requires connection.ied_name")

    if not connection.ld_name.strip():
        raise ValueError("OPC UA source simulator requires connection.ld_name")

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
    """Render OPC UA address-space description as NodeSet XML.

    Args:
        address_space: Backend-neutral OPC UA address-space description.

    Returns:
        NodeSet XML content.
    """
    last_modified = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

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

    for obj in address_space.objects:
        if obj.node_id == "WindFarm":
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
    """Render OPC UA address-space description as runner TSV.

    Args:
        address_space: Backend-neutral OPC UA address-space description.
        extra_records: Optional extra runner configuration records.

    Returns:
        TSV content consumed by the open62541 C runner.

    Raises:
        ValueError: If a TSV field contains tab or newline.
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
    """Build one validated TSV line.

    Args:
        *fields: TSV fields.

    Returns:
        One TSV line.

    Raises:
        ValueError: If any field contains tab or newline.
    """
    for field in fields:
        if "\t" in field or "\n" in field or "\r" in field:
            raise ValueError(f"TSV field contains unsupported control character: {field!r}")
    return "\t".join(fields)
