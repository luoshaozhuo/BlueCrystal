"""采集任务与点位状态模块."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from whale.shared.persistence import Base


class AcquisitionTask(Base):
    """采集任务配置 — 以 LD 实例为核心的采集调度记录."""

    __tablename__ = "acq_task"
    __table_args__ = (
        CheckConstraint(
            "acquisition_mode IN ('READ_ONCE', 'POLLING', 'SUBSCRIBE', 'REPORT')",
            name="ck_acq_task_acquisition_mode",
        ),
        CheckConstraint(
            "task_status IN ('STARTED', 'RUNNING', 'STOPPING', 'ERROR', 'SUCCESS', 'STOPPED')",
            name="ck_acq_task_status",
        ),
        CheckConstraint(
            "polling_max_concurrent_connections > 0",
            name="ck_acq_task_polling_max_concurrent_connections",
        ),
        CheckConstraint(
            "polling_connection_start_interval_ms >= 0",
            name="ck_acq_task_polling_connection_start_interval_ms",
        ),
        CheckConstraint(
            "subscription_start_interval_ms >= 0",
            name="ck_acq_task_subscription_start_interval_ms",
        ),
        CheckConstraint(
            "subscription_notification_queue_size > 0",
            name="ck_acq_task_subscription_notification_queue_size",
        ),
        CheckConstraint(
            "subscription_notification_worker_count > 0",
            name="ck_acq_task_subscription_notification_worker_count",
        ),
        CheckConstraint(
            "subscription_notification_max_lag_ms > 0",
            name="ck_acq_task_subscription_notification_max_lag_ms",
        ),
        UniqueConstraint("ld_instance_id", "acquisition_mode", name="uq_acq_task_ld_mode"),
        {"comment": "采集任务配置"},
    )

    task_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="采集任务主键",
    )
    task_name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="采集任务名称，如 task_ZB-WTG-001",
    )
    ld_instance_id: Mapped[int] = mapped_column(
        ForeignKey("scada_ld_instance.ld_instance_id"),
        nullable=False,
        index=True,
        comment="LD 实例 ID，采集任务的核心对象；通过它可确定 endpoint、asset_instance、signal_profile",
    )
    acquisition_mode: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="采集模式：READ_ONCE / POLLING / SUBSCRIBE / REPORT",
    )
    task_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="STOPPED",
        comment="任务生命周期状态：STARTED / RUNNING / STOPPING / ERROR / SUCCESS / STOPPED",
    )
    request_timeout_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
        comment="单次 read 请求超时，单位毫秒",
    )
    poll_interval_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="采集轮询周期，单位毫秒",
    )

    polling_max_concurrent_connections: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        comment="POLLING/READ_ONCE 主动采集时允许同时读取的最大 connection 数；不拆分 items",
    )
    polling_connection_start_interval_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="POLLING/READ_ONCE 主动采集时不同 connection 的启动错峰间隔，单位毫秒；不改变单 connection 采样周期",
    )
    subscription_start_interval_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="SUBSCRIBE 模式下不同 connection 启动订阅的错峰间隔，单位毫秒",
    )
    subscription_notification_queue_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        comment="SUBSCRIBE 模式下客户端侧 notification 队列容量；队列满表示客户端过载",
    )
    subscription_notification_worker_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="SUBSCRIBE 模式下客户端侧 notification 固定消费 worker 数",
    )
    subscription_notification_max_lag_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5000,
        comment="SUBSCRIBE 模式下 notification 在客户端队列中的最大允许等待时间，单位毫秒；超限表示处理滞后",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="配置态启停标记，不表示运行状态",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        comment="任务优先级，数值越小优先级越高",
    )
    partition_key: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="多节点分区键，用于 dual_active_partitioned",
    )
    assignment_policy: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="AUTO",
        comment="任务分配策略：AUTO / PINNED / DISABLED",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="乐观并发控制版本号",
    )
    freshness_timeout_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30000,
        comment="数据新鲜度超时(ms)，用于判断 latest-state 是否 stale；polling/read 模式主要使用",
    )
    alive_timeout_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60000,
        comment="链路存活超时(ms)，subscribe 模式主要使用；polling 模式也可用于判断 source 是否连续失败导致 offline",
    )
    protocol_params: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="协议专属参数，避免 acq_task 被 OPC UA / Modbus / IEC 61850 字段污染",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


class AcqSignalState(Base):
    """点位最新状态 — 保存每个 LD 实例 + ProfileItem 解析后的最新值."""

    __tablename__ = "acq_signal_state"
    __table_args__ = (
        UniqueConstraint("ld_instance_id", "profile_item_id", name="uq_signal_state"),
        {"comment": "点位最新状态"},
    )

    signal_state_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="最新状态主键",
    )
    ld_instance_id: Mapped[int] = mapped_column(
        ForeignKey("scada_ld_instance.ld_instance_id"),
        nullable=False,
        comment="LD 实例 ID",
    )
    profile_item_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_profile_item.profile_item_id"),
        nullable=False,
        comment="点位方案明细 ID",
    )
    asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"),
        nullable=False,
        index=True,
        comment="所属资产实例 ID，通常冗余自 scada_ld_instance.asset_instance_id，便于查询",
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="采集任务 ID",
    )
    resolved_signal_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="实际解析后的采集路径，如 WTG_001/MMXU1.TotW.mag.f，可由 path_prefix + relative_path 生成",
    )
    value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="最新值（序列化）",
    )
    numeric_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="数值型冗余值，用于统计、告警、排序、聚合",
    )
    quality: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="质量位，可为空",
    )
    source_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="源端观测时间，可为空",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="平台接收时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="状态更新时间",
    )
    raw_payload_json: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        comment="原始采集载荷",
    )


class AcqSignalSample(Base):
    """点位历史样本 — 保存历史采集值."""

    __tablename__ = "acq_signal_sample"
    __table_args__ = {"comment": "点位历史样本"}

    sample_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="样本主键",
    )
    ld_instance_id: Mapped[int] = mapped_column(
        ForeignKey("scada_ld_instance.ld_instance_id"),
        nullable=False,
        comment="LD 实例 ID",
    )
    profile_item_id: Mapped[int] = mapped_column(
        ForeignKey("scada_signal_profile_item.profile_item_id"),
        nullable=False,
        comment="点位方案明细 ID",
    )
    asset_instance_id: Mapped[int] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"),
        nullable=False,
        index=True,
        comment="所属资产实例 ID",
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="采集任务 ID",
    )
    resolved_signal_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="实际采集路径",
    )
    value: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="样本值",
    )
    numeric_value: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="数值型冗余值",
    )
    quality: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="质量位",
    )
    source_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="源端观测时间",
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="平台接收时间",
    )
    raw_payload_json: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        comment="原始采集载荷",
    )
