"""共享持久化层 SCADA 元数据 repository —— seahorse 参考数据与读取。

本文件负责生成一套共享的 `SignalProfile/SignalProfileItem`，并为 16 组
协议-服务样例写入 IED、Endpoint、LD、采集任务以及第一范式参数值。
它还提供 Seahorse 构建 WritePlan 所需的只读映射。真实 Whale ORM 访问
只在本 infrastructure 边界发生，不进入 domain/application。
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from seahorse.domain.runtime_contract import (
    EndpointBinding,
    FieldBinding,
    ServerBinding,
    WritePlanId,
    WriteTarget,
)
from whale.shared.persistence import Base
from whale.shared.persistence.orm import (
    AcquisitionTask,
    AssetInstance,
    AssetModel,
    AssetType,
    CDCDict,
    CommunicationEndpoint,
    FCDict,
    IED,
    LDInstance,
    Organization,
    ScadaDataType,
    ScadaEndpointParamValue,
    ScadaProtocolParamDef,
    ScadaSignalParamDef,
    ScadaSignalProfileItemParamValue,
    SignalProfile,
    SignalProfileItem,
)
from whale.shared.persistence.session import session_scope

ScalarValue = str | int | float | bool
SessionScopeFactory = Callable[[], AbstractContextManager[Session]]
EndpointParamDefs = dict[str, dict[str, tuple]]
SignalParamDefs = dict[str, dict[str, tuple]]


def _load_protocol_param_defs() -> tuple[EndpointParamDefs, SignalParamDefs]:
    """延迟读取参考参数表，避免 repository/template 循环导入。

    ``seahorse.reference_data`` 兼容层已在 Round 7B 删除；现在直接读取
    ``whale.shared.persistence.template.protocol_param_data``，由 Alembic
    与 Whale 共享协议参数表统一管理。
    """
    from whale.shared.persistence.template.protocol_param_data import (
        ENDPOINT_PARAM_DEFS,
        SIGNAL_PARAM_DEFS,
    )

    return ENDPOINT_PARAM_DEFS, SIGNAL_PARAM_DEFS


class WhaleMetadataMappingError(RuntimeError):
    """Whale 元数据无法映射为 Seahorse WritePlan。

    repository 在读取 Whale ORM 后，如果发现缺少 IED、Endpoint、LD、
    SignalProfile 或 SignalProfileItem 等构建计划必需字段，会抛出该稳定
    基础设施错误，避免继续产生 silent wrong result。
    """


class WhaleMetadataToWritePlanMapper:
    """将 Whale ORM 对象映射为 Seahorse runtime contract。

    该 mapper 只读取已加载的 ORM 对象字段和 relationship，不查询数据库；
    具体 session 生命周期由 repository 负责。
    """

    def map_endpoint(self, endpoint: CommunicationEndpoint) -> ServerBinding:
        """把单个 Whale CommunicationEndpoint 映射为 ServerBinding。

        Args:
            endpoint: 已加载 IED、LDInstance、SignalProfile.items 的 Whale ORM 对象。

        Returns:
            Seahorse 纯内存 server binding。

        Raises:
            WhaleMetadataMappingError: metadata 缺少构建 WritePlan 所需字段。
        """
        if endpoint.ied is None:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 缺少 IED 关系"
            )
        server_id = self._server_id(endpoint.ied)
        endpoint_id = self._endpoint_id(endpoint)
        fields = self._map_endpoint_fields(
            endpoint=endpoint,
            server_id=server_id,
            endpoint_id=endpoint_id,
        )
        if not fields:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 未配置可映射 point/field"
            )
        return ServerBinding(
            server_id=server_id,
            endpoints=(
                EndpointBinding(
                    endpoint_id=endpoint_id,
                    protocol=self._required_text(
                        endpoint.application_protocol,
                        f"endpoint {endpoint.endpoint_id}.application_protocol",
                    ),
                    fields=fields,
                ),
            ),
        )

    def _map_endpoint_fields(
        self,
        *,
        endpoint: CommunicationEndpoint,
        server_id: str,
        endpoint_id: str,
    ) -> tuple[FieldBinding, ...]:
        """从 endpoint 下的 LD/Profile items 展开字段 binding。"""
        if not endpoint.ld_instances:
            raise WhaleMetadataMappingError(
                f"endpoint {endpoint.endpoint_id} 缺少 LDInstance 配置"
            )

        fields: list[FieldBinding] = []
        for ld_instance in sorted(
            endpoint.ld_instances,
            key=lambda item: item.ld_instance_id or 0,
        ):
            if ld_instance.signal_profile is None:
                raise WhaleMetadataMappingError(
                    f"LDInstance {ld_instance.ld_instance_id} 缺少 SignalProfile"
                )
            profile_items = ld_instance.signal_profile.items
            if not profile_items:
                raise WhaleMetadataMappingError(
                    f"SignalProfile {ld_instance.signal_profile_id} 未配置 SignalProfileItem"
                )
            for profile_item in sorted(
                profile_items,
                key=lambda item: item.profile_item_id or 0,
            ):
                fields.append(
                    self._map_profile_item(
                        server_id=server_id,
                        endpoint_id=endpoint_id,
                        ld_instance=ld_instance,
                        profile_item=profile_item,
                    )
                )
        return tuple(fields)

    def _map_profile_item(
        self,
        *,
        server_id: str,
        endpoint_id: str,
        ld_instance: LDInstance,
        profile_item: SignalProfileItem,
    ) -> FieldBinding:
        """将 LD + ProfileItem 映射为单个字段绑定。"""
        ld_name = self._required_text(
            ld_instance.ld_name,
            f"LDInstance {ld_instance.ld_instance_id}.ld_name",
        )
        relative_path = self._required_text(
            profile_item.relative_path,
            f"SignalProfileItem {profile_item.profile_item_id}.relative_path",
        )
        field_id = f"whale:ld:{ld_instance.ld_instance_id}:item:{profile_item.profile_item_id}:value"
        source_id = f"whale-source:profile-item:{profile_item.profile_item_id}:sample"
        return FieldBinding(
            field_id=field_id,
            target=WriteTarget(
                server_id=server_id,
                endpoint_id=endpoint_id,
                point_id=f"{ld_name}/{relative_path}",
                field_name="value",
            ),
            source_id=source_id,
        )

    def _server_id(self, ied: IED) -> str:
        """根据 IED 构造稳定 server_id。"""
        if ied.ied_name:
            return f"whale:ied:{ied.ied_name}"
        if ied.ied_id is not None:
            return f"whale:ied:{ied.ied_id}"
        raise WhaleMetadataMappingError("IED 缺少 ied_name/ied_id")

    def _endpoint_id(self, endpoint: CommunicationEndpoint) -> str:
        """根据 endpoint 主键和 AccessPoint 构造稳定 endpoint_id。"""
        if endpoint.endpoint_id is None:
            raise WhaleMetadataMappingError("CommunicationEndpoint 缺少 endpoint_id")
        access_point = self._required_text(
            endpoint.access_point_name,
            f"endpoint {endpoint.endpoint_id}.access_point_name",
        )
        return f"whale:endpoint:{endpoint.endpoint_id}:{access_point}"

    def _required_text(self, value: str | None, field_name: str) -> str:
        """校验 Whale 文本字段是可映射的非空值。"""
        if value is None or not value.strip():
            raise WhaleMetadataMappingError(f"{field_name} 不能为空")
        return value


class WhaleMetadataRepository:
    """Whale 元数据样例 seed 与 Seahorse WritePlan 读取 repository。

    seed 方法会修改 Whale 元数据库；读取方法只查询 Whale metadata 并映射
    为 Seahorse 纯内存 contract。session 可由测试显式注入，也可使用默认
    `session_scope`，repository 不把 ORM 对象泄漏给 application/domain。
    """

    def __init__(
        self,
        session: Session | None = None,
        *,
        session_factory: SessionScopeFactory | None = None,
        mapper: WhaleMetadataToWritePlanMapper | None = None,
    ) -> None:
        """初始化 repository。

        Args:
            session: 可选外部 session，主要用于单元测试或受控装配。
            session_factory: 可选 context-managed session 工厂。
            mapper: 可选 Whale ORM 到 Seahorse contract mapper。
        """
        self._session = session
        self._session_factory = session_factory or session_scope
        self._mapper = mapper or WhaleMetadataToWritePlanMapper()

    def seed_sample_metadata(self) -> None:
        """写入 Seahorse 协议样例元数据。"""
        generate_all_sample_data()

    def clear_sample_metadata(self) -> None:
        """清理 Seahorse 协议样例元数据。"""
        clear_database_data()

    def load_servers(self, plan_id: WritePlanId) -> tuple[ServerBinding, ...]:
        """读取构建 WritePlan 所需的 server/endpoint/field 配置。

        Args:
            plan_id: 运行计划标识；当前 Whale schema 没有 plan 维度，本实现
                只用它保持端口契约，不据此过滤。

        Returns:
            Seahorse 纯内存 server binding 集合。

        Raises:
            WhaleMetadataMappingError: Whale metadata 不完整或无法映射。
        """
        _ = plan_id
        with self._session_scope() as session:
            endpoints = self._load_endpoints(session)
            servers = tuple(self._mapper.map_endpoint(endpoint) for endpoint in endpoints)
        if not servers:
            raise WhaleMetadataMappingError("Whale 未配置 CommunicationEndpoint")
        return servers

    def load_endpoints(self, server_id: str) -> tuple[EndpointBinding, ...]:
        """按 server_id 读取 endpoint binding。

        该方法用于满足 WhaleMetadataPort；主构建路径会通过 `load_servers`
        一次性读取，避免 runtime tick 期间增量查询。
        """
        return tuple(
            endpoint
            for server in self.load_servers(WritePlanId("adhoc"))
            if server.server_id == server_id
            for endpoint in server.endpoints
        )

    def load_fields(self, endpoint_id: str) -> tuple[FieldBinding, ...]:
        """按 endpoint_id 读取字段 binding。"""
        return tuple(
            field
            for server in self.load_servers(WritePlanId("adhoc"))
            for endpoint in server.endpoints
            if endpoint.endpoint_id == endpoint_id
            for field in endpoint.fields
        )

    def _session_scope(self) -> AbstractContextManager[Session]:
        """返回本次 repository 操作使用的 session context。"""
        if self._session is not None:
            return nullcontext(self._session)
        return self._session_factory()

    def _load_endpoints(self, session: Session) -> tuple[CommunicationEndpoint, ...]:
        """用 Whale ORM relationship 预加载 WritePlan 映射所需配置。"""
        statement = (
            select(CommunicationEndpoint)
            .options(
                selectinload(CommunicationEndpoint.ied),
                selectinload(CommunicationEndpoint.ld_instances)
                .selectinload(LDInstance.signal_profile)
                .selectinload(SignalProfile.items),
            )
            .order_by(CommunicationEndpoint.endpoint_id)
        )
        return tuple(session.scalars(statement).all())


@dataclass(frozen=True)
class ProtocolSampleSpec:
    """单个协议样例端点定义."""

    asset_code: str
    asset_name: str
    access_point_name: str
    endpoint_name: str
    application_protocol: str
    service_type: str
    transport: str
    host: str | None
    port: int | None
    namespace_uri: str | None
    security_policy: str | None
    security_mode: str | None
    auth_type: str | None
    ld_name: str
    path_prefix: str
    endpoint_params: dict[str, ScalarValue]
    signal_params: dict[str, ScalarValue]


PROTOCOL_SAMPLE_SPECS: list[ProtocolSampleSpec] = [
    ProtocolSampleSpec(
        asset_code="WTG_OPCUA_001",
        asset_name="OPC UA 样例风机",
        access_point_name="OPCUA_AP",
        endpoint_name="OPC UA 读取端点",
        application_protocol="OPC_UA",
        service_type="READ",
        transport="TCP",
        host="127.0.0.1",
        port=4840,
        namespace_uri="urn:whale:windfarm:opcua",
        security_policy="Basic256Sha256",
        security_mode="SignAndEncrypt",
        auth_type="UsernamePassword",
        ld_name="LD_OPCUA_001",
        path_prefix="WTG_OPCUA_001",
        endpoint_params={
            "endpoint_url": "opc.tcp://127.0.0.1:4840",
            "application_uri": "urn:whale:client:opcua:read",
            "connect_timeout_ms": 5000,
            "request_timeout_ms": 3000,
            "security_policy_override": "Basic256Sha256",
        },
        signal_params={
            "namespace_index": 2,
            "node_id": "ns=2;s=WTG_OPCUA_001/MMXU1.TotW.mag.f",
            "browse_path": "2:WTG_OPCUA_001/2:MMXU1/2:TotW",
            "attribute_id": 13,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_OPCUA_SUB_001",
        asset_name="OPC UA 订阅样例风机",
        access_point_name="OPCUA_SUB_AP",
        endpoint_name="OPC UA 订阅端点",
        application_protocol="OPC_UA",
        service_type="SUBSCRIBE",
        transport="TCP",
        host="127.0.0.1",
        port=4841,
        namespace_uri="urn:whale:windfarm:opcua",
        security_policy="Basic256Sha256",
        security_mode="SignAndEncrypt",
        auth_type="UsernamePassword",
        ld_name="LD_OPCUA_SUB_001",
        path_prefix="WTG_OPCUA_SUB_001",
        endpoint_params={
            "endpoint_url": "opc.tcp://127.0.0.1:4841",
            "application_uri": "urn:whale:client:opcua:subscribe",
            "connect_timeout_ms": 5000,
            "request_timeout_ms": 3000,
            "security_policy_override": "Basic256Sha256",
        },
        signal_params={
            "namespace_index": 2,
            "node_id": "ns=2;s=WTG_OPCUA_SUB_001/MMXU1.TotW.mag.f",
            "browse_path": "2:WTG_OPCUA_SUB_001/2:MMXU1/2:TotW",
            "attribute_id": 13,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_MODBUS_TCP_001",
        asset_name="Modbus TCP 样例风机",
        access_point_name="MBTCP_AP",
        endpoint_name="Modbus TCP 端点",
        application_protocol="MODBUS",
        service_type="TCP_READ",
        transport="TCP",
        host="192.168.10.21",
        port=502,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_MODBUS_TCP_001",
        path_prefix="WTG_MODBUS_TCP_001",
        endpoint_params={
            "unit_id": 1,
            "connect_timeout_ms": 3000,
            "request_timeout_ms": 1000,
        },
        signal_params={
            "unit_id": 1,
            "function_code": 3,
            "register_address": 40001,
            "register_count": 2,
            "byte_order": "BIG_ENDIAN",
            "word_order": "BIG_ENDIAN",
            "signed": False,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_MODBUS_RTU_001",
        asset_name="Modbus RTU 样例风机",
        access_point_name="MBRTU_AP",
        endpoint_name="Modbus RTU 端点",
        application_protocol="MODBUS",
        service_type="RTU_READ",
        transport="SERIAL",
        host=None,
        port=None,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_MODBUS_RTU_001",
        path_prefix="WTG_MODBUS_RTU_001",
        endpoint_params={
            "serial_port": "/dev/ttyUSB0",
            "baudrate": 19200,
            "parity": "N",
            "stop_bits": 1,
            "data_bits": 8,
            "unit_id": 2,
            "response_timeout_ms": 1200,
        },
        signal_params={
            "unit_id": 2,
            "function_code": 4,
            "register_address": 30011,
            "register_count": 2,
            "byte_order": "LITTLE_ENDIAN",
            "word_order": "BIG_ENDIAN",
            "signed": False,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_IEC101_001",
        asset_name="IEC101 样例风机",
        access_point_name="IEC101_AP",
        endpoint_name="IEC101 总召端点",
        application_protocol="IEC101",
        service_type="INTERROGATION",
        transport="SERIAL",
        host=None,
        port=None,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_IEC101_001",
        path_prefix="WTG_IEC101_001",
        endpoint_params={
            "serial_port": "/dev/ttyS1",
            "baudrate": 9600,
            "parity": "E",
            "stop_bits": 1,
            "data_bits": 8,
            "link_address": 11,
            "common_address": 101,
        },
        signal_params={
            "link_address": 11,
            "common_address": 101,
            "ioa": 1001,
            "type_id": 13,
            "cot": 20,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_IEC101_SP_001",
        asset_name="IEC101 自发上送样例风机",
        access_point_name="IEC101_SP_AP",
        endpoint_name="IEC101 自发上送端点",
        application_protocol="IEC101",
        service_type="SPONTANEOUS",
        transport="SERIAL",
        host=None,
        port=None,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_IEC101_SP_001",
        path_prefix="WTG_IEC101_SP_001",
        endpoint_params={
            "serial_port": "/dev/ttyS2",
            "baudrate": 19200,
            "parity": "E",
            "stop_bits": 1,
            "data_bits": 8,
            "link_address": 12,
            "common_address": 102,
        },
        signal_params={
            "link_address": 12,
            "common_address": 102,
            "ioa": 1002,
            "type_id": 30,
            "cot": 3,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_IEC104_001",
        asset_name="IEC104 样例风机",
        access_point_name="IEC104_AP",
        endpoint_name="IEC104 总召端点",
        application_protocol="IEC104",
        service_type="INTERROGATION",
        transport="TCP",
        host="192.168.20.31",
        port=2404,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_IEC104_001",
        path_prefix="WTG_IEC104_001",
        endpoint_params={
            "common_address": 201,
            "originator_address": 1,
            "interrogation_group": 20,
            "t0_ms": 30000,
            "t1_ms": 15000,
            "t2_ms": 10000,
            "t3_ms": 20000,
            "k": 12,
            "w": 8,
        },
        signal_params={
            "common_address": 201,
            "ioa": 4001,
            "type_id": 13,
            "cot": 20,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_IEC104_SP_001",
        asset_name="IEC104 自发上送样例风机",
        access_point_name="IEC104_SP_AP",
        endpoint_name="IEC104 自发上送端点",
        application_protocol="IEC104",
        service_type="SPONTANEOUS",
        transport="TCP",
        host="192.168.20.32",
        port=2404,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_IEC104_SP_001",
        path_prefix="WTG_IEC104_SP_001",
        endpoint_params={
            "common_address": 202,
            "originator_address": 1,
            "interrogation_group": 20,
            "t0_ms": 30000,
            "t1_ms": 15000,
            "t2_ms": 10000,
            "t3_ms": 20000,
            "k": 12,
            "w": 8,
        },
        signal_params={
            "common_address": 202,
            "ioa": 4002,
            "type_id": 30,
            "cot": 3,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_61850_MMS_001",
        asset_name="IEC61850 MMS 样例风机",
        access_point_name="MMS_AP",
        endpoint_name="IEC61850 MMS 端点",
        application_protocol="IEC61850",
        service_type="MMS_READ",
        transport="TCP",
        host="192.168.30.41",
        port=102,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type="Certificate",
        ld_name="LD_61850_MMS_001",
        path_prefix="LD0",
        endpoint_params={
            "scl_ref": "configs/wtg_61850.icd",
            "access_point": "AP1",
            "dataset_ref": "WTG/MMXU$MX$TotW",
            "report_control_block": "BRep01",
            "integrity_period_ms": 60000,
            "buffered": True,
        },
        signal_params={
            "ied_name": "IED_WTG_61850_MMS_001",
            "ld_inst": "LD0",
            "ln_class": "MMXU",
            "ln_inst": 1,
            "do_name": "TotW",
            "da_name": "mag.f",
            "fc": "MX",
            "dataset_ref": "WTG/MMXU$MX$TotW",
            "dataset_index": 0,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_61850_RPT_001",
        asset_name="IEC61850 Report 样例风机",
        access_point_name="RPT_AP",
        endpoint_name="IEC61850 Report 端点",
        application_protocol="IEC61850",
        service_type="REPORT",
        transport="TCP",
        host="192.168.30.42",
        port=102,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type="Certificate",
        ld_name="LD_61850_RPT_001",
        path_prefix="LD0",
        endpoint_params={
            "scl_ref": "configs/wtg_61850_report.icd",
            "access_point": "AP1",
            "dataset_ref": "WTG/LLN0$RP$Status",
            "report_control_block": "BRep02",
            "integrity_period_ms": 30000,
            "buffered": True,
        },
        signal_params={
            "ied_name": "IED_WTG_61850_RPT_001",
            "ld_inst": "LD0",
            "ln_class": "WTUR",
            "ln_inst": 1,
            "do_name": "OpSt",
            "da_name": "stVal",
            "fc": "ST",
            "dataset_ref": "WTG/LLN0$RP$Status",
            "dataset_index": 0,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_61850_GOOSE_001",
        asset_name="IEC61850 GOOSE 样例风机",
        access_point_name="GOOSE_AP",
        endpoint_name="IEC61850 GOOSE 端点",
        application_protocol="IEC61850",
        service_type="GOOSE",
        transport="ETHERNET_L2",
        host=None,
        port=None,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_61850_GOOSE_001",
        path_prefix="LD0",
        endpoint_params={
            "network_interface": "eth0",
            "vlan_id": 100,
            "app_id": 4097,
            "multicast_mac": "01:0C:CD:01:00:01",
            "go_cb_ref": "IED1/LLN0$GO$gcb01",
            "dataset_ref": "IED1/LLN0$Dataset01",
            "min_time_ms": 1,
            "max_time_ms": 1000,
        },
        signal_params={
            "dataset_ref": "IED1/LLN0$Dataset01",
            "dataset_index": 0,
            "goose_field_path": "gooseData[0].value",
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_61850_SV_001",
        asset_name="IEC61850 SV 样例风机",
        access_point_name="SV_AP",
        endpoint_name="IEC61850 SV 端点",
        application_protocol="IEC61850",
        service_type="SV",
        transport="ETHERNET_L2",
        host=None,
        port=None,
        namespace_uri=None,
        security_policy=None,
        security_mode=None,
        auth_type=None,
        ld_name="LD_61850_SV_001",
        path_prefix="LD0",
        endpoint_params={
            "network_interface": "eth1",
            "vlan_id": 200,
            "app_id": 8193,
            "multicast_mac": "01:0C:CD:04:00:01",
            "sv_cb_ref": "IED1/LLN0$SV$svcb01",
            "dataset_ref": "IED1/LLN0$DatasetSV01",
            "sample_rate_hz": 4000,
            "asdu_count": 1,
        },
        signal_params={
            "dataset_ref": "IED1/LLN0$DatasetSV01",
            "asdu_index": 0,
            "sample_channel": 0,
            "smp_index": 0,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_MQTT_001",
        asset_name="MQTT 样例风机",
        access_point_name="MQTT_AP",
        endpoint_name="MQTT 订阅端点",
        application_protocol="MQTT",
        service_type="SUBSCRIBE",
        transport="MQTT",
        host="mqtt-broker.local",
        port=1883,
        namespace_uri=None,
        security_policy="TLS_OPTIONAL",
        security_mode="TLS",
        auth_type="Token",
        ld_name="LD_MQTT_001",
        path_prefix="telemetry/wtg_001",
        endpoint_params={
            "client_id": "whale-mqtt-wtg-001",
            "topic_prefix": "whale/wtg/001",
            "qos": 1,
            "clean_session": True,
            "keepalive_seconds": 60,
            "username_ref": "cred://mqtt/whale_user",
            "password_ref": "cred://mqtt/whale_password",
        },
        signal_params={
            "topic": "whale/wtg/001/telemetry",
            "payload_path": "measurements.active_power_kw",
            "payload_type": "JSON",
            "retain": False,
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_HTTP_001",
        asset_name="HTTP REST 样例风机",
        access_point_name="HTTP_AP",
        endpoint_name="HTTP REST 轮询端点",
        application_protocol="HTTP_REST",
        service_type="REQUEST",
        transport="HTTPS",
        host="api.windfarm.local",
        port=443,
        namespace_uri=None,
        security_policy="TLS",
        security_mode="TLS",
        auth_type="API_KEY",
        ld_name="LD_HTTP_001",
        path_prefix="devices/WTG_HTTP_001",
        endpoint_params={
            "base_path": "/api/v1",
            "method": "GET",
            "auth_header_ref": "cred://http/whale_api_key",
            "request_timeout_ms": 3000,
            "verify_tls": True,
        },
        signal_params={
            "resource_path": "/devices/WTG_HTTP_001/telemetry",
            "json_path": "telemetry.active_power_kw",
            "method": "GET",
            "value_field": "active_power_kw",
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_ADS_001",
        asset_name="Beckhoff ADS 样例风机",
        access_point_name="ADS_AP",
        endpoint_name="Beckhoff ADS 端点",
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_READ_WRITE",
        transport="TCP",
        host="192.168.40.51",
        port=48898,
        namespace_uri=None,
        security_policy="PLC_ROUTE",
        security_mode="ROUTE",
        auth_type="Certificate",
        ld_name="LD_ADS_001",
        path_prefix="MAIN.WTG_ADS_001",
        endpoint_params={
            "ams_net_id": "5.32.160.1.1.1",
            "ads_router_port": 48898,
            "ads_server_port": 851,
            "route_name": "whale-ads-route",
            "connect_timeout_ms": 3000,
            "request_timeout_ms": 1000,
        },
        signal_params={
            "symbol_name": "MAIN.WTG_ADS_001.ActivePower",
            "index_group": 16416,
            "index_offset": 32,
            "data_size": 8,
            "ads_data_type": "LREAL",
        },
    ),
    ProtocolSampleSpec(
        asset_code="WTG_ADS_SUB_001",
        asset_name="Beckhoff ADS 通知样例风机",
        access_point_name="ADS_SUB_AP",
        endpoint_name="Beckhoff ADS 通知端点",
        application_protocol="BECKHOFF_ADS",
        service_type="ADS_NOTIFICATION",
        transport="TCP",
        host="192.168.40.52",
        port=48898,
        namespace_uri=None,
        security_policy="PLC_ROUTE",
        security_mode="ROUTE",
        auth_type="Certificate",
        ld_name="LD_ADS_SUB_001",
        path_prefix="MAIN.WTG_ADS_SUB_001",
        endpoint_params={
            "ams_net_id": "5.32.160.1.1.2",
            "ads_router_port": 48898,
            "ads_server_port": 852,
            "route_name": "whale-ads-sub-route",
            "connect_timeout_ms": 3000,
            "request_timeout_ms": 1000,
        },
        signal_params={
            "symbol_name": "MAIN.WTG_ADS_SUB_001.ActivePower",
            "index_group": 16416,
            "index_offset": 64,
            "data_size": 8,
            "ads_data_type": "LREAL",
            "notification_mode": "CYCLIC",
            "cycle_time_ms": 1000,
            "max_delay_ms": 100,
        },
    ),
]


def generate_all_sample_data() -> None:
    """生成共享点表与多协议端点样例数据."""

    with session_scope() as session:
        print("=" * 60)
        print("  SCADA 多协议样本数据生成")
        print("=" * 60)

        org = _create_org(session)
        data_types = _create_data_types(session)
        wtg_type, model = _create_asset_types_and_models(session)
        _create_cdc_fc(session)
        session.flush()

        profile, profile_items = _create_signal_profile(session, wtg_type, data_types)
        session.flush()

        endpoint_param_defs, signal_param_defs = _seed_protocol_param_defs(session)
        session.flush()

        ld_instances = _create_protocol_samples(
            session,
            org=org,
            wtg_type=wtg_type,
            model=model,
            profile=profile,
            profile_items=profile_items[:3],
            endpoint_param_defs=endpoint_param_defs,
            signal_param_defs=signal_param_defs,
        )
        session.flush()

        tasks = _create_acquisition_tasks(session, ld_instances)
        session.flush()
        session.commit()

        print(f"✓ 共享点表: 1 套 / {len(profile_items)} 个点位")
        print(f"✓ 协议端点样例: {len(ld_instances)} 组")
        print(f"✓ 采集任务: {len(tasks)} 个")
        print("=" * 60)
        print("  样本数据生成完毕")
        print("=" * 60)


def clear_database_data() -> None:
    """清空 Alembic 已创建 schema 中的 ORM 表数据。

    本函数只删除业务表数据，不建表、不删表、不重建 view，也不修改
    Alembic 版本表；调用前要求目标数据库已经执行过 migration。
    """

    with session_scope() as session:
        print("=" * 60)
        print("  清空 shared persistence 数据表")
        print("=" * 60)
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        print("✓ 数据表已清空")
        print("=" * 60)


def reset_sample_data() -> None:
    """连接当前配置数据库，清空已有数据后重新写入样例数据。"""

    clear_database_data()
    generate_all_sample_data()


def _create_org(session: Session) -> Organization:
    """创建演示组织."""

    org = Organization(org_name="Whale 多协议样例场站")
    session.add(org)
    session.flush()
    return org


def _create_data_types(session: Session) -> dict[str, ScadaDataType]:
    """创建样例所需的 SCADA 基础数据类型."""

    types: dict[str, ScadaDataType] = {}
    for name, enc, bits, constraint in [
        ("BOOLEAN", "IEC61850_BASIC", 1, "CHECK(value IN (0,1))"),
        ("INT32", "IEC61850_BASIC", 32, "CHECK(value BETWEEN -2147483648 AND 2147483647)"),
        ("INT64", "IEC61850_BASIC", 64, "CHECK(value BETWEEN -9223372036854775808 AND 9223372036854775807)"),
        ("FLOAT32", "IEC61850_BASIC", 32, "CHECK(value BETWEEN -3.4E38 AND 3.4E38)"),
        ("FLOAT64", "IEC61850_BASIC", 64, "CHECK(value BETWEEN -1.7E308 AND 1.7E308)"),
        ("STRING", "IEC61850_BASIC", None, "CHECK(LENGTH(value) <= 255)"),
        ("DATETIME", "IEC61850_BASIC", None, ""),
        ("VisString255", "IEC61850_BASIC", None, "CHECK(LENGTH(value) <= 255)"),
    ]:
        data_type = ScadaDataType(
            type_name=name,
            encoding=enc,
            size_bits=bits,
            constraint_expr=constraint or None,
        )
        session.add(data_type)
        types[name] = data_type
    session.flush()
    return types


def _create_asset_types_and_models(session: Session) -> tuple[AssetType, AssetModel]:
    """创建协议样例共用的资产类型和型号."""

    wtg_type = AssetType(
        type_code="WTG",
        type_name="风力发电机组",
        category="GENERATION_DEVICE",
        description="协议样例共用风机资产类型",
    )
    session.add(wtg_type)
    session.flush()

    model = AssetModel(
        asset_type_id=wtg_type.asset_type_id,
        model_code="WTG_PROTOCOL_SAMPLE",
        model_name="多协议样例风机",
        manufacturer="Whale Sample",
        specifications={"rated_power_kw": 5000, "hub_height_m": 120, "rotor_diameter_m": 190},
    )
    session.add(model)
    session.flush()
    return wtg_type, model


def _create_cdc_fc(session: Session) -> None:
    """创建 GB/T 30966 点表依赖的 CDC / FC 字典."""

    cdc_list = [
        ("MV", "Measured Value", "测量值"),
        ("SPS", "Single Point Status", "单点状态"),
        ("INS", "Integer Status", "整数状态"),
        ("ENS", "Enabled State", "使能状态"),
        ("ACT", "Activation Info", "动作信息"),
        ("ACD", "Directional Protection Activation Info", "方向保护动作信息"),
        ("INC", "Integer Controlled Step Position Info", "整数控制阶位信息"),
        ("BCR", "Binary Counter Reading", "二进制计数器读数"),
        ("ENC", "Enumerated Status", "枚举状态"),
        ("ENG", "Enumerated Status Setting", "枚举状态定值"),
        ("DPL", "Double Point Status", "双点状态"),
        ("DPC", "Double Point Controllable Status", "双点可控状态"),
        ("SPC", "Single Point Controllable Status", "单点可控状态"),
        ("HMV", "Harmonic Value", "谐波值"),
        ("HST", "Harmonic Value Setting", "谐波定值"),
        ("CSD", "Curve Shape Description", "曲线形状描述"),
        ("CST", "Curve Shape Setting", "曲线形状定值"),
        ("ISC", "Integer Status Setting", "整数状态定值"),
        ("LPL", "Logical Node Name Plate", "逻辑节点铭牌"),
        ("LPC", "Logical Node Name Plate Setting", "逻辑节点铭牌定值"),
    ]
    for code, name, desc in cdc_list:
        session.add(CDCDict(cdc_code=code, cdc_name=name, description=desc))
    fc_list = [
        ("ST", "Status", "状态"),
        ("MX", "Measurand", "测量量"),
        ("SP", "Setpoint", "设定值"),
        ("SV", "Substitution Value", "替代值"),
        ("CF", "Configuration", "配置"),
        ("DC", "Description", "描述"),
        ("EX", "Extended Definition", "扩展定义"),
    ]
    for code, name, desc in fc_list:
        session.add(FCDict(fc_code=code, fc_name=name, description=desc))


def _create_signal_profile(
    session: Session,
    wtg_type: AssetType,
    data_types: dict[str, ScadaDataType],
) -> tuple[SignalProfile, list[SignalProfileItem]]:
    """创建供所有协议样例共用的一套 GB/T 30966 点表."""

    from whale.shared.persistence.template.gbt_30966_fields import ALL_LOGICAL_NODES

    profile = SignalProfile(
        profile_code="WTG_GB_T_30966_2_SHARED_V1",
        profile_name="风机 GB/T 30966.2 共享协议点位方案 V1",
        asset_type_id=wtg_type.asset_type_id,
        standard_family="GB_T_30966",
        vendor="STANDARD",
        version="1.0",
        description="一套共享点表，同时被 OPC UA、Modbus、IEC、MQTT、HTTP、ADS 样例端点复用",
        metadata_json={"sample_protocols": [spec.application_protocol for spec in PROTOCOL_SAMPLE_SPECS]},
    )
    session.add(profile)
    session.flush()

    created_items: list[SignalProfileItem] = []
    for node_def in ALL_LOGICAL_NODES:
        for field in node_def.fields:
            data_type = data_types.get(field.data_type) or data_types["FLOAT64"]
            ln_name = f"{node_def.name}1"
            da_name = _resolve_da_name(field.cdc)
            fc = _resolve_fc(field.cdc)
            item = SignalProfileItem(
                signal_profile_id=profile.signal_profile_id,
                ln_class=node_def.name,
                ln_name=ln_name,
                do_name=field.key,
                da_name=da_name,
                relative_path=f"{ln_name}.{field.key}.{da_name}",
                fc=fc,
                cdc=field.cdc,
                data_type_id=data_type.data_type_id,
                default_unit=field.unit if field.unit else None,
                display_name=field.desc,
                default_sample_mode="SUBSCRIPTION",
                default_sample_interval_ms=100,
                default_constraint_expr=_resolve_constraint(field.unit),
                quality_supported=True,
                timestamp_supported=True,
                description=f"{node_def.desc} — {field.desc}",
            )
            session.add(item)
            created_items.append(item)
    return profile, created_items


def _resolve_da_name(cdc: str) -> str:
    """根据 CDC 选择默认 DA 名称."""

    if cdc in {"SPS", "SPC", "ENS", "ACT", "ACD", "DPL", "DPC", "INS", "INC", "ENC", "ENG", "BCR", "ISC", "CSD", "CST", "LPL", "LPC"}:
        return "stVal"
    return "mag.f"


def _resolve_fc(cdc: str) -> str:
    """根据 CDC 选择默认 FC."""

    if cdc in {"SPS", "ENS", "ACT", "ACD", "DPL", "DPC", "SPC", "INS", "INC", "ENC", "ENG", "ISC"}:
        return "ST"
    if cdc in {"CSD", "CST", "LPL", "LPC", "BCR"}:
        return "CF"
    return "MX"


def _resolve_constraint(unit: str | None) -> str | None:
    """根据单位推导演示点位的默认约束表达式."""

    if unit in {"kW", "kWh", "kVAr", "kVArh", "A", "V"}:
        return ">= 0"
    if unit == "Hz":
        return "BETWEEN 45 AND 55"
    if unit == "deg C":
        return "BETWEEN -40 AND 80"
    if unit == "m/s":
        return "BETWEEN 0 AND 75"
    if unit == "deg":
        return "BETWEEN 0 AND 360"
    if unit == "%":
        return "BETWEEN 0 AND 100"
    return None


def _seed_protocol_param_defs(
    session: Session,
) -> tuple[dict[tuple[str, str, str], dict[str, ScadaProtocolParamDef]], dict[tuple[str, str], dict[str, ScadaSignalParamDef]]]:
    """写入协议参数定义，并返回按协议/服务索引的定义映射."""

    endpoint_defs: dict[tuple[str, str, str], dict[str, ScadaProtocolParamDef]] = {}
    signal_defs: dict[tuple[str, str], dict[str, ScadaSignalParamDef]] = {}
    endpoint_param_defs, signal_param_defs = _load_protocol_param_defs()

    for spec in PROTOCOL_SAMPLE_SPECS:
        endpoint_key = (spec.application_protocol, spec.service_type, spec.transport)
        if endpoint_key not in endpoint_defs:
            endpoint_defs[endpoint_key] = {}
            for param in endpoint_param_defs[spec.application_protocol][spec.service_type]:
                endpoint_definition = ScadaProtocolParamDef(
                    application_protocol=spec.application_protocol,
                    service_type=spec.service_type,
                    transport=spec.transport,
                    param_key=param.key,
                    param_name=param.name,
                    data_type=param.data_type,
                    required=param.required,
                    default_value=param.default,
                    unit=param.unit,
                    allowed_values=param.allowed,
                    constraint_expr=param.constraint,
                    description=param.desc,
                    sort_order=param.sort,
                )
                session.add(endpoint_definition)
                endpoint_defs[endpoint_key][param.key] = endpoint_definition

        signal_key = (spec.application_protocol, spec.service_type)
        if signal_key not in signal_defs:
            signal_defs[signal_key] = {}
            for param in signal_param_defs[spec.application_protocol][spec.service_type]:
                signal_definition = ScadaSignalParamDef(
                    application_protocol=spec.application_protocol,
                    service_type=spec.service_type,
                    param_key=param.key,
                    param_name=param.name,
                    data_type=param.data_type,
                    required=param.required,
                    default_value=param.default,
                    unit=param.unit,
                    allowed_values=param.allowed,
                    constraint_expr=param.constraint,
                    description=param.desc,
                    sort_order=param.sort,
                )
                session.add(signal_definition)
                signal_defs[signal_key][param.key] = signal_definition

    return endpoint_defs, signal_defs


def _create_protocol_samples(
    session: Session,
    *,
    org: Organization,
    wtg_type: AssetType,
    model: AssetModel,
    profile: SignalProfile,
    profile_items: list[SignalProfileItem],
    endpoint_param_defs: dict[tuple[str, str, str], dict[str, ScadaProtocolParamDef]],
    signal_param_defs: dict[tuple[str, str], dict[str, ScadaSignalParamDef]],
) -> list[LDInstance]:
    """创建 16 组协议样例资产、端点、LD 与参数值."""

    ld_instances: list[LDInstance] = []
    for spec in PROTOCOL_SAMPLE_SPECS:
        asset = AssetInstance(
            asset_code=spec.asset_code,
            asset_name=spec.asset_name,
            asset_type_id=wtg_type.asset_type_id,
            model_id=model.model_id,
            org_id=org.org_id,
            location=f"{spec.application_protocol} 样例区",
            status="ACTIVE",
        )
        session.add(asset)
        session.flush()

        ied = IED(
            asset_instance_id=asset.asset_instance_id,
            ied_name=f"IED_{spec.asset_code}",
            ied_code=f"{spec.asset_code}_IED",
            ied_type="WTG_CONTROLLER",
            standard_family="SCADA_SAMPLE",
            metadata_json={"sample_protocol": spec.application_protocol, "service_type": spec.service_type},
        )
        session.add(ied)
        session.flush()

        endpoint = CommunicationEndpoint(
            ied_id=ied.ied_id,
            access_point_name=spec.access_point_name,
            endpoint_name=spec.endpoint_name,
            application_protocol=spec.application_protocol,
            service_type=spec.service_type,
            transport=spec.transport,
            host=spec.host,
            port=spec.port,
            namespace_uri=spec.namespace_uri,
            security_policy=spec.security_policy,
            security_mode=spec.security_mode,
            auth_type=spec.auth_type,
            service_capabilities_json=_build_service_capabilities(spec),
            description=f"{spec.application_protocol} / {spec.service_type} 样例端点",
            metadata_json={"sample": True},
        )
        session.add(endpoint)
        session.flush()

        ld_instance = LDInstance(
            endpoint_id=endpoint.endpoint_id,
            asset_instance_id=asset.asset_instance_id,
            signal_profile_id=profile.signal_profile_id,
            ld_name=spec.ld_name,
            ld_type="WIND_TURBINE",
            path_prefix=spec.path_prefix,
            metadata_json={"sample_protocol": spec.application_protocol},
        )
        session.add(ld_instance)
        session.flush()
        ld_instances.append(ld_instance)

        _create_endpoint_param_values(
            session,
            endpoint=endpoint,
            definitions=endpoint_param_defs[(spec.application_protocol, spec.service_type, spec.transport)],
            values=spec.endpoint_params,
        )
        _create_signal_param_values(
            session,
            profile_items=profile_items,
            definitions=signal_param_defs[(spec.application_protocol, spec.service_type)],
            values=spec.signal_params,
        )

    return ld_instances


def _build_service_capabilities(spec: ProtocolSampleSpec) -> dict[str, bool]:
    """根据样例协议推导能力摘要."""

    supports_read = spec.service_type in {
        "READ",
        "TCP_READ",
        "RTU_READ",
        "INTERROGATION",
        "MMS_READ",
        "REQUEST",
        "ADS_READ_WRITE",
    }
    supports_subscription = spec.service_type in {
        "SUBSCRIBE",
        "SPONTANEOUS",
        "REPORT",
        "GOOSE",
        "SV",
        "ADS_NOTIFICATION",
    }
    return {
        "supports_read": supports_read,
        "supports_write": spec.application_protocol in {"OPC_UA", "MODBUS", "IEC61850", "BECKHOFF_ADS"},
        "supports_subscription": supports_subscription,
        "supports_report": spec.service_type == "REPORT",
    }


def _resolve_acquisition_mode(service_type: str) -> str:
    """把协议服务语义映射为共享采集任务模式.

    Args:
        service_type: `CommunicationEndpoint.service_type` 中登记的协议服务类型。

    Returns:
        `AcquisitionTask.acquisition_mode` 对应的标准值。

    Raises:
        ValueError: 当出现当前样例未声明的 service_type 时抛出，避免静默写错任务语义。
    """

    if service_type == "REPORT":
        return "REPORT"
    if service_type in {"SUBSCRIBE", "SPONTANEOUS", "GOOSE", "SV", "ADS_NOTIFICATION"}:
        return "SUBSCRIBE"
    if service_type in {
        "READ",
        "TCP_READ",
        "RTU_READ",
        "INTERROGATION",
        "MMS_READ",
        "REQUEST",
        "ADS_READ_WRITE",
    }:
        return "POLLING"
    raise ValueError(f"Unsupported service_type for acquisition mode mapping: {service_type}")


def _create_endpoint_param_values(
    session: Session,
    *,
    endpoint: CommunicationEndpoint,
    definitions: dict[str, ScadaProtocolParamDef],
    values: dict[str, ScalarValue],
) -> None:
    """写入单个 endpoint 的正式参数值."""

    for key, value in values.items():
        definition = definitions[key]
        value_kwargs = _build_param_value_kwargs(definition.data_type, value)
        session.add(
            ScadaEndpointParamValue(
                endpoint_id=endpoint.endpoint_id,
                param_def_id=definition.param_def_id,
                **value_kwargs,
            )
        )


def _create_signal_param_values(
    session: Session,
    *,
    profile_items: list[SignalProfileItem],
    definitions: dict[str, ScadaSignalParamDef],
    values: dict[str, ScalarValue],
) -> None:
    """把同一协议映射到共享点表中的前若干个语义点位."""

    for profile_item in profile_items:
        for key, value in values.items():
            definition = definitions[key]
            value_kwargs = _build_param_value_kwargs(definition.data_type, value)
            session.add(
                ScadaSignalProfileItemParamValue(
                    profile_item_id=profile_item.profile_item_id,
                    param_def_id=definition.param_def_id,
                    **value_kwargs,
                )
            )


def _build_param_value_kwargs(data_type: str, value: ScalarValue) -> dict[str, str | int | float | bool | None]:
    """把 Python 值映射到协议参数值表的单列存储结构."""

    if data_type == "BOOL":
        return {"value_text": None, "value_int": None, "value_float": None, "value_bool": bool(value)}
    if data_type == "INT":
        return {"value_text": None, "value_int": int(value), "value_float": None, "value_bool": None}
    if data_type == "FLOAT":
        return {"value_text": None, "value_int": None, "value_float": float(value), "value_bool": None}
    return {"value_text": str(value), "value_int": None, "value_float": None, "value_bool": None}


def _create_acquisition_tasks(session: Session, ld_instances: list[LDInstance]) -> list[AcquisitionTask]:
    """为每个 LD 样例创建一条采集任务.

    这里必须逐个创建任务；旧实现因缩进错误只会保留最后一个 LD 的任务。
    """

    tasks: list[AcquisitionTask] = []
    for ld in ld_instances:
        asset = session.get(AssetInstance, ld.asset_instance_id)
        if asset is None:
            raise LookupError(f"AssetInstance `{ld.asset_instance_id}` not found for LD `{ld.ld_name}`.")
        endpoint = session.get(CommunicationEndpoint, ld.endpoint_id)
        if endpoint is None:
            raise LookupError(f"CommunicationEndpoint `{ld.endpoint_id}` not found for LD `{ld.ld_name}`.")
        if endpoint.service_type is None:
            raise ValueError(f"Endpoint `{endpoint.endpoint_id}` missing service_type for LD `{ld.ld_name}`.")

        task = AcquisitionTask(
            task_name=f"task_{asset.asset_code}",
            ld_instance_id=ld.ld_instance_id,
            acquisition_mode=_resolve_acquisition_mode(endpoint.service_type),
            poll_interval_ms=100,
            request_timeout_ms=500,
            freshness_timeout_ms=30000,
            alive_timeout_ms=60000,
            polling_max_concurrent_connections=4,
            polling_connection_start_interval_ms=25,
            subscription_start_interval_ms=25,
            subscription_notification_queue_size=4096,
            subscription_notification_worker_count=1,
            subscription_notification_max_lag_ms=200,
            protocol_params={},
        )
        session.add(task)
        tasks.append(task)
    return tasks


if __name__ == "__main__":
    reset_sample_data()
