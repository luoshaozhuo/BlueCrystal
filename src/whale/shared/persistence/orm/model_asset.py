"""仿真模型资产 ORM 模型。

定义模型资产、仿真案例、仿真结果和仿真制品的持久化模型。
模型资产（ModelAsset）表达风电仿真模型（FAST/OpenFAST/WINDFARM/BLADED/SIMULINK 等），
支持模型版本派生关系和资产实例绑定。

本文件包含四张表：
- ModelAsset: 模型资产主表。
- SimulationCase: 仿真案例定义。
- SimulationResult: 仿真结果记录。
- SimulationArtifact: 仿真制品（文件）记录。

约束：
- model_code / case_code / result_code 必须 unique。
- parent_model_asset_id 支持模型版本/派生关系。
- owner_asset_instance_id 允许为空，支持未绑定真实资产的设计模型。
- 文件本体不进 PostgreSQL，只保存 URI、checksum 和元数据。
- 解析状态明确为 IMPORTED / PARTIAL / UNSUPPORTED / FAILED。
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from whale.shared.persistence import Base


class ModelAsset(Base):
    """模型资产 — 表达风电仿真模型及其元数据。

    支持 FAST / OpenFAST / WINDFARM / BLADED / SIMULINK 等模型类型，
    通过 parent_model_asset_id 表达模型版本派生关系。
    owner_asset_instance_id 可空，支持未绑定真实资产的纯设计模型。
    """

    __tablename__ = "model_asset"
    __table_args__ = (
        UniqueConstraint("model_code", name="uq_model_asset_code"),
        {"comment": "模型资产"},
    )

    model_asset_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="模型资产主键"
    )
    model_code: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="模型编码，全局唯一，如 MY_FARM_FAST_v1"
    )
    model_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="模型名称，如 某风场FAST模型"
    )
    model_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="模型类型：FAST / OPENFAST / WINDFARM / BLADED / SIMULINK / OTHER"
    )
    asset_scope: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="资产范围：SITE / WIND_FARM / WTG / COMPONENT / STORAGE / GRID / OTHER"
    )
    owner_asset_instance_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("asset_instance.asset_instance_id"), nullable=True,
        comment="所属资产实例 ID，可空（纯设计模型）"
    )
    parent_model_asset_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("model_asset.model_asset_id"), nullable=True,
        comment="父模型资产 ID，支持模型版本/派生关系"
    )
    source_file_uri: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="源文件 URI（存储路径或对象存储 key）"
    )
    raw_archive_batch_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="原始归档批次 ID"
    )
    version: Mapped[str] = mapped_column(
        String(64), default="1.0", comment="模型版本号"
    )
    checksum_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="主文件 SHA256 校验和"
    )
    parser_status: Mapped[str] = mapped_column(
        String(32), default="IMPORTED",
        comment="解析状态：IMPORTED / PARTIAL / UNSUPPORTED / FAILED"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict,
        comment="扩展元数据，如模型描述、仿真参数、文件列表等"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SimulationCase(Base):
    """仿真案例 — 定义一次仿真运行的条件和参数。

    关联一个模型资产，携带输入参数和场景配置。
    案例类型包括设计工况、运行工况、故障工况、假设分析和回归测试。
    """

    __tablename__ = "simulation_case"
    __table_args__ = (
        UniqueConstraint("case_code", name="uq_simulation_case_code"),
        {"comment": "仿真案例"},
    )

    simulation_case_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="仿真案例主键"
    )
    case_code: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="案例编码，全局唯一"
    )
    case_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="案例名称"
    )
    model_asset_id: Mapped[int] = mapped_column(
        ForeignKey("model_asset.model_asset_id"), nullable=False, comment="关联模型资产 ID"
    )
    case_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="案例类型：DESIGN / OPERATION / FAULT / WHAT_IF / REGRESSION / OTHER"
    )
    input_file_uri: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="输入文件 URI"
    )
    raw_archive_batch_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="原始归档批次 ID"
    )
    parameter_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="输入参数 JSON，如 wind_speed_mps=12.0"
    )
    scenario_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="场景配置 JSON，如生成停机/偏航/变桨事件"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="CREATED",
        comment="案例状态：CREATED / IMPORTED / RUNNING / SUCCEEDED / FAILED / CANCELLED"
    )
    created_by: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="创建者标识"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SimulationResult(Base):
    """仿真结果 — 记录仿真案例的运行结果。

    一个案例可以产生多个结果（如时序数据、汇总报告、日志）。
    支持多种结果类型和时序后端（TDengine / FILE / NONE）。
    """

    __tablename__ = "simulation_result"
    __table_args__ = (
        UniqueConstraint("result_code", name="uq_simulation_result_code"),
        {"comment": "仿真结果"},
    )

    simulation_result_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="仿真结果主键"
    )
    simulation_case_id: Mapped[int] = mapped_column(
        ForeignKey("simulation_case.simulation_case_id"), nullable=False,
        comment="关联仿真案例 ID"
    )
    result_code: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="结果编码，全局唯一"
    )
    result_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="结果类型：TIMESERIES / SUMMARY / REPORT / ARTIFACT / LOG / OTHER"
    )
    result_file_uri: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True, comment="结果文件 URI"
    )
    raw_archive_batch_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="原始归档批次 ID"
    )
    time_series_backend: Mapped[Optional[str]] = mapped_column(
        String(32), nullable=True,
        comment="时序后端：TDENGINE / FILE / NONE"
    )
    time_series_ref: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True, comment="时序数据引用（表名或文件路径）"
    )
    summary_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="汇总结果 JSON，如统计指标"
    )
    metric_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="指标 JSON，如性能评估指标"
    )
    status: Mapped[str] = mapped_column(
        String(32), default="IMPORTED",
        comment="结果状态：IMPORTED / PARTIAL / FAILED"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SimulationArtifact(Base):
    """仿真制品 — 记录与模型资产、案例或结果关联的文件。

    通过 owner_type + owner_id 组合关联到三类父对象：
    MODEL_ASSET / SIMULATION_CASE / SIMULATION_RESULT。
    文件本体不进数据库，仅记录 URI、校验和和元数据。
    """

    __tablename__ = "simulation_artifact"
    __table_args__ = {"comment": "仿真制品"}

    simulation_artifact_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, comment="仿真制品主键"
    )
    owner_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="所属对象类型：MODEL_ASSET / SIMULATION_CASE / SIMULATION_RESULT"
    )
    owner_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="所属对象 ID"
    )
    artifact_type: Mapped[str] = mapped_column(
        String(32), nullable=False,
        comment="制品类型：SOURCE_FILE / INPUT_FILE / RESULT_FILE / REPORT / LOG / CONFIG / OTHER"
    )
    file_uri: Mapped[str] = mapped_column(
        String(1024), nullable=False, comment="文件 URI"
    )
    raw_archive_batch_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, comment="原始归档批次 ID"
    )
    checksum_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="文件 SHA256 校验和"
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict, comment="扩展元数据"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
