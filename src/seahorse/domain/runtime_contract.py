"""Seahorse runtime contract 领域模型。

本模块只定义运行计划、数据源、调度和写入 batch 的强类型内存契约。
它不读取 Whale DB、不连接 Starfish、不调度线程，也不保证 50Hz 性能；
50Hz 只在 ``PeriodicScheduleSpec`` 中表达为可校验的配置语义。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


ScalarValue = str | int | float | bool
"""可写入 Starfish handoff/runtime contract 的标量值类型。"""

PointFieldValue = ScalarValue | None
"""单个点位字段值；None 表示当前 batch 明确不携带值。"""


class DataSourceKind(StrEnum):
    """运行时值来源类型。"""

    RANDOM = "random"
    SAMPLE = "sample"
    FUNCTION = "function"
    REPLAY = "replay"


class DataSourceValueKind(StrEnum):
    """数据源输出值类型提示。

    该提示只服务 Seahorse 内存 data source runtime 的最小取值策略，不表达
    Starfish 协议字段 schema，也不触发真实 driver 类型转换。
    """

    NUMERIC = "numeric"
    BOOL = "bool"
    STRING = "string"
    NOMINAL = "nominal"


class ScheduleKind(StrEnum):
    """写入调度类型。"""

    PERIODIC = "periodic"
    RANDOM_TIME = "random_time"
    MANUAL_TRIGGER = "manual_trigger"
    EVENT_TRIGGER = "event_trigger"


@dataclass(frozen=True, slots=True)
class WritePlanId:
    """运行计划稳定标识。

    Attributes:
        value: 非空计划标识，供日志、快照和 batch 关联使用。
    """

    value: str

    def __post_init__(self) -> None:
        """校验计划标识。"""
        if not self.value:
            raise ValueError("WritePlanId.value 不能为空")


@dataclass(frozen=True, slots=True)
class WriteTarget:
    """单个可写入目标。

    Attributes:
        server_id: Starfish server member 标识。
        endpoint_id: endpoint 标识。
        point_id: point 标识。
        field_name: point 下的字段名，例如 value、quality。
    """

    server_id: str
    endpoint_id: str
    point_id: str
    field_name: str = "value"

    def stable_key(self) -> str:
        """返回可用于拓扑和诊断输出的稳定 key。"""
        return f"{self.server_id}:{self.endpoint_id}:{self.point_id}:{self.field_name}"


@dataclass(frozen=True, slots=True)
class FieldBinding:
    """WritePlan 中字段与值来源的绑定关系。

    Attributes:
        field_id: 绑定标识，要求在计划内稳定。
        target: 写入目标。
        source_id: 对应 ``DataSourceSpec.source_id``。
    """

    field_id: str
    target: WriteTarget
    source_id: str


@dataclass(frozen=True, slots=True)
class EndpointBinding:
    """endpoint 与字段绑定集合。

    Attributes:
        endpoint_id: endpoint 标识。
        protocol: 协议名，仅作契约描述，不创建 driver。
        fields: 该 endpoint 下的字段绑定。
    """

    endpoint_id: str
    protocol: str
    fields: tuple[FieldBinding, ...] = ()


@dataclass(frozen=True, slots=True)
class ServerBinding:
    """server member 与 endpoint 绑定集合。"""

    server_id: str
    endpoints: tuple[EndpointBinding, ...] = ()


@dataclass(frozen=True, slots=True)
class DataSourceSpec:
    """运行时值来源契约。

    ``REPLAY`` 只表达来源类型和引用名，本轮不读取文件、不执行真实 replay。

    Attributes:
        source_id: 来源标识。
        kind: 来源类型。
        reference: 样例名、函数名或 replay 逻辑引用；不是文件读取承诺。
        seed: 可选确定性 seed。
        value_type: 输出值类型提示；默认 numeric，保持旧调用兼容。
    """

    source_id: str
    kind: DataSourceKind
    reference: str = ""
    seed: int | None = None
    value_type: DataSourceValueKind = DataSourceValueKind.NUMERIC


@dataclass(frozen=True, slots=True)
class PeriodicScheduleSpec:
    """周期调度契约。

    Attributes:
        period_ns: 周期纳秒值。50Hz 目标对应不大于 20ms，即
            ``period_ns <= 20_000_000``。该判断只说明配置满足目标周期，
            不代表真实性能已验证。
    """

    period_ns: int

    @classmethod
    def from_period_ms(cls, period_ms: float) -> "PeriodicScheduleSpec":
        """从毫秒构建周期调度配置。

        Args:
            period_ms: 周期毫秒，必须大于 0。

        Returns:
            周期调度配置。
        """
        if period_ms <= 0:
            raise ValueError("period_ms 必须大于 0")
        return cls(period_ns=int(period_ms * 1_000_000))

    @property
    def period_ms(self) -> float:
        """返回周期毫秒值。"""
        return self.period_ns / 1_000_000

    def supports_50hz_target(self) -> bool:
        """判断配置周期是否满足 50Hz 目标周期。

        Returns:
            True 表示配置周期不大于 20ms；不代表 runtime 性能达标。
        """
        return self.period_ns <= 20_000_000

    def __post_init__(self) -> None:
        """校验周期必须为正。"""
        if self.period_ns <= 0:
            raise ValueError("period_ns 必须大于 0")


@dataclass(frozen=True, slots=True)
class RandomTimeScheduleSpec:
    """随机时刻调度契约。

    只表达随机窗口和 seed，不创建随机执行器。
    """

    window_start_ns: int
    window_end_ns: int
    seed: int | None = None

    def __post_init__(self) -> None:
        """校验随机窗口。"""
        if self.window_end_ns <= self.window_start_ns:
            raise ValueError("window_end_ns 必须大于 window_start_ns")


@dataclass(frozen=True, slots=True)
class ManualTriggerSpec:
    """手动触发调度契约。"""

    trigger_name: str


@dataclass(frozen=True, slots=True)
class EventTriggerSpec:
    """事件触发调度契约。"""

    event_type: str


ScheduleDetail = (
    PeriodicScheduleSpec | RandomTimeScheduleSpec | ManualTriggerSpec | EventTriggerSpec
)
"""ScheduleSpec.detail 可接受的强类型调度详情。"""


@dataclass(frozen=True, slots=True)
class ScheduleSpec:
    """运行计划调度契约。"""

    kind: ScheduleKind
    detail: ScheduleDetail

    @classmethod
    def periodic(cls, period: PeriodicScheduleSpec) -> "ScheduleSpec":
        """构建周期调度契约。"""
        return cls(kind=ScheduleKind.PERIODIC, detail=period)

    @classmethod
    def random_time(cls, detail: RandomTimeScheduleSpec) -> "ScheduleSpec":
        """构建随机时刻调度契约。"""
        return cls(kind=ScheduleKind.RANDOM_TIME, detail=detail)

    @classmethod
    def manual(cls, detail: ManualTriggerSpec) -> "ScheduleSpec":
        """构建手动触发调度契约。"""
        return cls(kind=ScheduleKind.MANUAL_TRIGGER, detail=detail)

    @classmethod
    def event(cls, detail: EventTriggerSpec) -> "ScheduleSpec":
        """构建事件触发调度契约。"""
        return cls(kind=ScheduleKind.EVENT_TRIGGER, detail=detail)

    def __post_init__(self) -> None:
        """校验 kind 与 detail 类型一致。"""
        expected: dict[ScheduleKind, type[ScheduleDetail]] = {
            ScheduleKind.PERIODIC: PeriodicScheduleSpec,
            ScheduleKind.RANDOM_TIME: RandomTimeScheduleSpec,
            ScheduleKind.MANUAL_TRIGGER: ManualTriggerSpec,
            ScheduleKind.EVENT_TRIGGER: EventTriggerSpec,
        }
        if not isinstance(self.detail, expected[self.kind]):
            raise TypeError(f"{self.kind.value} 调度详情类型不匹配")


@dataclass(frozen=True, slots=True)
class WritePlan:
    """Seahorse 内存运行计划。

    计划必须在 runtime tick 前构建完成，tick 期间不得依赖 Whale DB 查询。
    """

    plan_id: WritePlanId
    servers: tuple[ServerBinding, ...]
    data_sources: tuple[DataSourceSpec, ...]
    schedule: ScheduleSpec

    def field_bindings(self) -> tuple[FieldBinding, ...]:
        """展开计划中的全部字段绑定。"""
        fields: list[FieldBinding] = []
        for server in self.servers:
            for endpoint in server.endpoints:
                fields.extend(endpoint.fields)
        return tuple(fields)


@dataclass(frozen=True, slots=True)
class WriteItem:
    """单个写入项。"""

    target: WriteTarget
    value: PointFieldValue
    source_id: str
    timestamp_ns: int


@dataclass(frozen=True, slots=True)
class WriteBatch:
    """批量写入契约。

    Starfish writer hot path 应接受 batch。
    """

    plan_id: WritePlanId
    batch_id: str
    items: tuple[WriteItem, ...]

    def __post_init__(self) -> None:
        """校验 batch 标识。"""
        if not self.batch_id:
            raise ValueError("batch_id 不能为空")


@dataclass(frozen=True, slots=True)
class WriteFailure:
    """单项写入失败。"""

    target: WriteTarget
    reason: str
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class WriteBatchResult:
    """批量写入结果。"""

    batch_id: str
    accepted_count: int
    failures: tuple[WriteFailure, ...] = ()

    @property
    def success(self) -> bool:
        """返回 batch 是否完全成功。"""
        return not self.failures

    def __post_init__(self) -> None:
        """校验接受数量不能为负。"""
        if self.accepted_count < 0:
            raise ValueError("accepted_count 不能为负数")


def validate_write_plan(plan: WritePlan) -> tuple[str, ...]:
    """校验运行计划的纯内存一致性。

    Args:
        plan: 待校验运行计划。

    Returns:
        错误消息元组；空元组表示校验通过。
    """
    errors: list[str] = []
    source_ids = {source.source_id for source in plan.data_sources}
    field_ids: set[str] = set()
    for field_binding in plan.field_bindings():
        if field_binding.field_id in field_ids:
            errors.append(f"重复 field_id: {field_binding.field_id}")
        field_ids.add(field_binding.field_id)
        if field_binding.source_id not in source_ids:
            errors.append(
                f"字段 {field_binding.field_id} 引用未知 source_id: {field_binding.source_id}"
            )
    if not plan.servers:
        errors.append("WritePlan.servers 不能为空")
    if not plan.data_sources:
        errors.append("WritePlan.data_sources 不能为空")
    return tuple(errors)


__all__ = [
    "DataSourceKind",
    "DataSourceSpec",
    "DataSourceValueKind",
    "EndpointBinding",
    "EventTriggerSpec",
    "FieldBinding",
    "ManualTriggerSpec",
    "PeriodicScheduleSpec",
    "PointFieldValue",
    "RandomTimeScheduleSpec",
    "ScalarValue",
    "ScheduleDetail",
    "ScheduleKind",
    "ScheduleSpec",
    "ServerBinding",
    "WriteBatch",
    "WriteBatchResult",
    "WriteFailure",
    "WriteItem",
    "WritePlan",
    "WritePlanId",
    "WriteTarget",
    "validate_write_plan",
]
