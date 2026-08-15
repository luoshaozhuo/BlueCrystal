"""Ingest 运行时 CRUD API 的 Pydantic schema 定义。

本模块定义 ingest runtime 所有 REST API 的请求/响应 schema。
包括采集任务、数据源、连接配置、信号配置、测点、调度任务、
安全分区、Bundle 元数据、节点状态、租约状态、审计事件的
创建、部分更新和查询响应模型。

所有 schema 通过 Pydantic BaseModel 提供请求验证和序列化支持。

不负责：业务逻辑、权限判断、租约守卫——这些由 use case 和
service 层处理。
"""

from __future__ import annotations

from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from pacific.whale.shared.persistence.orm import AcquisitionTask


AcquisitionModeLiteral = Literal["READ_ONCE", "POLLING", "SUBSCRIBE", "REPORT"]

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """通用的分页响应封装，用于列表类 API 的统一返回格式。

    Attributes:
        items: 当前页的数据列表。
        total: 符合条件的总数。
        limit: 每页最大条数。
        offset: 当前偏移量。
    """

    items: list[T]
    total: int
    limit: int
    offset: int


class AcquisitionTaskCreate(BaseModel):
    """采集任务创建请求。

    包含采集任务的全部初始配置，包括采集模式、轮询间隔、
    超时、优先级、分区键和协议参数。
    """

    task_name: str
    ld_instance_id: int
    acquisition_mode: AcquisitionModeLiteral = "POLLING"
    poll_interval_ms: int = 100
    request_timeout_ms: int = 500
    enabled: bool = True
    priority: int = 100
    partition_key: str | None = None
    assignment_policy: str = "AUTO"
    protocol_params: dict[str, Any] = Field(default_factory=dict)


class AcquisitionTaskPatch(BaseModel):
    """采集任务部分更新请求。

    仅包含需要修改的字段。expected_version 用于乐观并发控制。
    """

    expected_version: int
    task_name: str | None = None
    acquisition_mode: AcquisitionModeLiteral | None = None
    poll_interval_ms: int | None = None
    request_timeout_ms: int | None = None
    enabled: bool | None = None
    priority: int | None = None
    partition_key: str | None = None
    assignment_policy: str | None = None
    protocol_params: dict[str, Any] | None = None


class AcquisitionTaskResponse(BaseModel):
    """采集任务查询响应。

    返回采集任务的全部配置和当前版本号。
    版本号用于乐观并发控制——调用方在 PATCH 操作时需提供
    expected_version。
    """

    task_id: int
    task_name: str
    ld_instance_id: int
    acquisition_mode: str
    task_status: str
    poll_interval_ms: int
    request_timeout_ms: int
    enabled: bool
    priority: int
    partition_key: str | None
    assignment_policy: str
    protocol_params: dict[str, Any]
    version: int

    @classmethod
    def from_orm_row(cls, row: AcquisitionTask) -> "AcquisitionTaskResponse":
        """从 ORM 行对象构造响应实例。"""
        return cls(
            task_id=row.task_id,
            task_name=row.task_name,
            ld_instance_id=row.ld_instance_id,
            acquisition_mode=row.acquisition_mode,
            task_status=row.task_status,
            poll_interval_ms=row.poll_interval_ms,
            request_timeout_ms=row.request_timeout_ms,
            enabled=row.enabled,
            priority=row.priority,
            partition_key=row.partition_key,
            assignment_policy=row.assignment_policy,
            protocol_params=dict(row.protocol_params),
            version=row.version,
        )


class SourceCreate(BaseModel):
    """数据源（IED/设备）创建请求。"""

    ied_name: str
    asset_code: str
    asset_name: str
    ied_type: str | None = None
    standard_family: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SourcePatch(BaseModel):
    """数据源部分更新请求。"""

    expected_version: int
    ied_name: str | None = None
    asset_name: str | None = None
    ied_type: str | None = None
    standard_family: str | None = None
    metadata_json: dict[str, Any] | None = None


class SourceResponse(BaseModel):
    """数据源查询响应。"""

    source_id: int
    ied_name: str
    asset_instance_id: int
    asset_code: str
    asset_name: str
    ied_type: str | None
    standard_family: str | None
    version: int


class ConnectionCreate(BaseModel):
    """连接配置创建请求。

    描述一个采集连接的全部参数：协议、传输方式、主机地址、
    端口、命名空间、端点名称和凭证引用。
    """

    source_id: int
    access_point_name: str
    application_protocol: str
    transport: str
    service_type: str | None = None
    host: str | None = None
    port: int | None = None
    namespace_uri: str | None = None
    endpoint_name: str | None = None
    credential_ref: str | None = None
    service_capabilities_json: dict[str, Any] = Field(default_factory=dict)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ConnectionPatch(BaseModel):
    """连接配置部分更新请求。"""

    expected_version: int
    access_point_name: str | None = None
    application_protocol: str | None = None
    transport: str | None = None
    service_type: str | None = None
    host: str | None = None
    port: int | None = None
    namespace_uri: str | None = None
    endpoint_name: str | None = None
    credential_ref: str | None = None
    service_capabilities_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class ConnectionResponse(BaseModel):
    """连接配置查询响应。"""

    connection_id: int
    source_id: int
    access_point_name: str
    application_protocol: str
    transport: str
    service_type: str | None
    host: str | None
    port: int | None
    namespace_uri: str | None
    endpoint_name: str | None
    credential_ref: str | None
    service_capabilities_json: dict[str, Any]
    metadata_json: dict[str, Any]
    version: int


class SignalProfileCreate(BaseModel):
    """信号配置创建请求。"""

    profile_code: str
    profile_name: str
    standard_family: str | None = None
    vendor: str | None = None
    version_label: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class SignalProfilePatch(BaseModel):
    """信号配置部分更新请求。"""

    expected_version: int
    profile_code: str | None = None
    profile_name: str | None = None
    standard_family: str | None = None
    vendor: str | None = None
    version_label: str | None = None
    description: str | None = None
    metadata_json: dict[str, Any] | None = None


class SignalProfileResponse(BaseModel):
    """信号配置查询响应。"""

    signal_profile_id: int
    profile_code: str
    profile_name: str
    standard_family: str | None
    vendor: str | None
    version_label: str | None
    description: str | None
    metadata_json: dict[str, Any]
    version: int


class PointCreate(BaseModel):
    """测点（采集点位）创建请求。

    描述单个测点的完整信息：信号配置、相关路径、数据对象名称、
    数据类型、逻辑节点、功能约束（FC）、CDC 类型、可写性等。
    """

    signal_profile_id: int
    relative_path: str
    do_name: str
    data_type_name: str
    ln_class: str | None = None
    ln_name: str | None = None
    da_name: str | None = None
    fc: str | None = None
    cdc: str | None = None
    default_unit: str | None = None
    writable: bool = False
    display_name: str | None = None
    description: str | None = None


class PointPatch(BaseModel):
    """测点部分更新请求。"""

    expected_version: int
    relative_path: str | None = None
    do_name: str | None = None
    data_type_name: str | None = None
    ln_class: str | None = None
    ln_name: str | None = None
    da_name: str | None = None
    fc: str | None = None
    cdc: str | None = None
    default_unit: str | None = None
    writable: bool | None = None
    display_name: str | None = None
    description: str | None = None


class PointResponse(BaseModel):
    """测点查询响应。"""

    point_id: int
    signal_profile_id: int
    relative_path: str
    do_name: str
    data_type_name: str
    ln_class: str | None
    ln_name: str | None
    da_name: str | None
    fc: str | None
    cdc: str | None
    default_unit: str | None
    writable: bool
    display_name: str | None
    description: str | None
    version: int


# ── Scheduler Job ──────────────────────────────────────────────────────────

class SchedulerJobCreate(BaseModel):
    """调度任务创建请求。

    用于向 WorkerRuntime 调度器注册一个可调度 job。
    job_type 决定 dispatch 到哪个 handler。
    """

    job_id: str
    job_type: str = "acquisition"
    task_id: int | None = None
    partition_key: str | None = None
    enabled: bool = True
    priority: int = 100
    schedule_kind: str = "manual"
    schedule_expr: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    stagger_offset_ms: int | None = None


class SchedulerJobPatch(BaseModel):
    """调度任务部分更新请求。"""

    expected_version: int
    job_type: str | None = None
    enabled: bool | None = None
    priority: int | None = None
    partition_key: str | None = None
    schedule_kind: str | None = None
    schedule_expr: str | None = None
    config: dict[str, Any] | None = None
    stagger_offset_ms: int | None = None


class SchedulerJobResponse(BaseModel):
    """调度任务查询响应。"""

    job_id: str
    job_type: str
    task_id: int | None
    partition_key: str | None
    enabled: bool
    priority: int
    schedule_kind: str
    schedule_expr: str | None
    version: int
    config: dict[str, Any]
    stagger_offset_ms: int | None = None


# ── Security Partition ─────────────────────────────────────────────────────

class SecurityPartitionCreate(BaseModel):
    """安全分区创建请求。

    安全分区用于定义数据隔离边界、安全区域和访问方向。
    """

    partition_code: str
    partition_name: str
    security_zone: str = "UNCLASSIFIED"
    direction: str = "READ_ONLY"
    description: str | None = None
    rules_json: dict[str, Any] = Field(default_factory=dict)


class SecurityPartitionPatch(BaseModel):
    """安全分区部分更新请求。"""

    expected_version: int
    partition_name: str | None = None
    security_zone: str | None = None
    direction: str | None = None
    description: str | None = None
    rules_json: dict[str, Any] | None = None


class SecurityPartitionResponse(BaseModel):
    """安全分区查询响应。"""

    partition_id: int
    partition_code: str
    partition_name: str
    security_zone: str
    direction: str
    description: str | None
    rules_json: dict[str, Any]
    version: int


# ── Bundle Metadata ────────────────────────────────────────────────────────

class BundleMetadataResponse(BaseModel):
    """Bundle 元数据查询响应。

    Bundle 是一组采集配置的导出/导入单元，包含版本、校验和、
    签名状态和导入时间。
    """

    bundle_id: int
    bundle_version: str
    schema_version: str
    checksum: str
    signature_status: str
    source: str
    redacted: bool
    status: str
    created_at: str
    imported_at: str | None


# ── Node ───────────────────────────────────────────────────────────────────

class NodeResponse(BaseModel):
    """节点状态查询响应。

    描述一个 WorkerRuntime 节点的注册信息、运行模式和心跳状态。
    """

    node_key: str
    runtime_mode: str
    status: str
    hostname: str | None
    heartbeat_at: str
    last_seen_at: str
    created_at: str
    updated_at: str


# ── Lease ──────────────────────────────────────────────────────────────────

class LeaseResponse(BaseModel):
    """租约状态查询响应。

    描述一次租约的完整生命周期：持有者、状态、fencing token、
    获取/续期/过期/释放时间。
    """

    lease_id: int
    lease_name: str
    lease_scope: str
    resource_id: str
    holder_key: str
    status: str
    fencing_token: int
    acquired_at: str
    renewed_at: str
    expires_at: str
    released_at: str | None
    version: int


# ── Audit Event ────────────────────────────────────────────────────────────

class AuditEventResponse(BaseModel):
    """审计事件查询响应。

    记录一次操作的完整审计追踪信息：请求方、操作类型、
    决策结果、原因码和来源节点。
    """

    audit_id: int
    request_id: str
    actor: str | None
    action: str
    resource_type: str
    resource_id: str | None
    decision: str
    result: str
    reason_code: str | None
    http_status: int | None
    trace_id: str | None
    client_ip: str | None
    node_id: str | None
    event_timestamp: str
