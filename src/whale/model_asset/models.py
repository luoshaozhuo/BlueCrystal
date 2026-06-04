"""模型资产 DTO 和数据模型。

定义模型资产导入请求、导入结果、仿真案例导入请求、仿真结果导入请求
以及仿真导入 manifest 的 data transfer object。

本文件包含：
- SimulationFileType: 仿真文件类型枚举。
- SimulationImportManifest: 导入 manifest 模型。
- ModelAssetImportRequest / ModelAssetImportResult: 模型资产导入 DTO。
- SimulationCaseImportRequest: 仿真案例导入请求 DTO。
- SimulationResultImportRequest: 仿真结果导入请求 DTO。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class SimulationFileType(str, Enum):
    """仿真文件类型枚举。

    根据文件扩展名、内容标记（magic bytes 或 YAML header）分类。
    不执行深度解析，仅基于表面特征判断。
    """

    FAST = "FAST"            # .fst .fast .fstf
    OPENFAST = "OPENFAST"    # .fst .yaml .fstproj with OpenFAST marker
    WINDFARM = "WINDFARM"    # .wnd .wfp
    BLADED = "BLADED"        # .prj .bld
    SIMULINK = "SIMULINK"    # .slx .mdl
    OTHER = "OTHER"          # 已知格式但非上述类型
    UNSUPPORTED = "UNSUPPORTED"  # 无法识别或不支持的格式


# model_type / asset_scope / case_type 等受限于 ORM 字段约束，
# 此处不重复定义枚举，直接在 DTO 中使用 str 并附带校验逻辑。


@dataclass
class ModelAssetImportRequest:
    """模型资产导入请求。

    包含模型编码、名称、类型、范围、版本、文件列表和 manifest 信息。
    文件路径列表中的文件由 SimulationArchiveService 归档后存储 URI。

    Attributes:
        model_code: 模型编码，全局唯一。
        model_name: 模型名称。
        model_type: 模型类型（FAST / OPENFAST / WINDFARM / BLADED / SIMULINK / OTHER）。
        asset_scope: 资产范围（SITE / WIND_FARM / WTG / COMPONENT / STORAGE / GRID / OTHER）。
        version: 版本号。
        parent_model_code: 父模型编码，用于表达版本派生关系。
        owner_asset_code: 所属资产实例编码，可空。
        files: 文件路径列表。
        checksum_sha256: 主文件 SHA256。
        metadata: 扩展元数据字典。
    """

    model_code: str
    model_name: str
    model_type: str
    asset_scope: str
    version: str = "1.0"
    parent_model_code: Optional[str] = None
    owner_asset_code: Optional[str] = None
    files: list[str] = field(default_factory=list)
    checksum_sha256: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class ModelAssetImportResult:
    """模型资产导入结果。

    表达单次导入操作的结果，包括成功/失败状态、模型编码和生成的制品列表。

    Attributes:
        success: 是否成功。
        model_code: 导入的模型编码。
        model_asset_id: 分配的模型资产 ID。
        parser_status: 解析状态（IMPORTED / PARTIAL / UNSUPPORTED / FAILED）。
        artifact_ids: 关联的制品 ID 列表。
        error_message: 失败时的错误信息。
    """

    success: bool
    model_code: str
    model_asset_id: Optional[int] = None
    parser_status: Optional[str] = None
    artifact_ids: list[int] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class SimulationCaseImportRequest:
    """仿真案例导入请求。

    关联一个模型资产，携带输入参数和场景配置。

    Attributes:
        case_code: 案例编码，全局唯一。
        case_name: 案例名称。
        model_code: 关联的模型编码。
        case_type: 案例类型（DESIGN / OPERATION / FAULT / WHAT_IF / REGRESSION / OTHER）。
        input_file_uri: 输入文件 URI。
        parameters: 输入参数字典。
        scenario: 场景配置字典。
        created_by: 创建者标识。
    """

    case_code: str
    case_name: str
    model_code: str
    case_type: str
    input_file_uri: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    scenario: dict = field(default_factory=dict)
    created_by: Optional[str] = None


@dataclass
class SimulationResultImportRequest:
    """仿真结果导入请求。

    关联一个仿真案例，携带结果类型、汇总数据和指标。

    Attributes:
        result_code: 结果编码，全局唯一。
        case_code: 关联的案例编码。
        result_type: 结果类型（TIMESERIES / SUMMARY / REPORT / ARTIFACT / LOG / OTHER）。
        result_file_uri: 结果文件 URI。
        time_series_backend: 时序后端（TDENGINE / FILE / NONE）。
        time_series_ref: 时序数据引用。
        summary: 汇总结果字典。
        metrics: 指标字典。
        status: 结果状态（IMPORTED / PARTIAL / FAILED）。
        files: 关联文件路径列表。
    """

    result_code: str
    case_code: str
    result_type: str
    result_file_uri: Optional[str] = None
    time_series_backend: Optional[str] = None
    time_series_ref: Optional[str] = None
    summary: dict = field(default_factory=dict)
    metrics: dict = field(default_factory=dict)
    status: str = "IMPORTED"
    files: list[str] = field(default_factory=list)


@dataclass
class SimulationImportManifest:
    """仿真导入 manifest — 描述单次导入操作的完整上下文。

    可同时包含模型资产、案例和结果的导入请求，用于批量导入场景。

    Attributes:
        model_code: 模型编码。
        model_type: 模型类型。
        version: 版本号。
        asset_scope: 资产范围。
        parent_model_code: 父模型编码。
        files: 文件路径列表。
        checksum_sha256: 校验和。
        metadata: 扩展元数据。
    """

    model_code: str
    model_type: str
    version: str = "1.0"
    asset_scope: str = "WTG"
    parent_model_code: Optional[str] = None
    files: list[str] = field(default_factory=list)
    checksum_sha256: Optional[str] = None
    metadata: dict = field(default_factory=dict)
