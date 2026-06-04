"""model_asset DTO 模型单元测试。

验证 ModelAssetImportRequest、ModelAssetImportResult、SimulationCaseImportRequest、
SimulationResultImportRequest、SimulationImportManifest、SimulationFileType 的
数据结构和枚举行为。

被验证对象：
- whale.model_asset.models: 所有 DTO 和枚举

测试阶段：开发期验证 (unit，无外部依赖)。
不能证明：DTO 在真实持久化和 API 序列化中的行为。
"""

from __future__ import annotations

from whale.model_asset.models import (
    ModelAssetImportRequest,
    ModelAssetImportResult,
    SimulationCaseImportRequest,
    SimulationFileType,
    SimulationImportManifest,
    SimulationResultImportRequest,
)


class TestSimulationFileType:
    """SimulationFileType 枚举测试。"""

    def test_all_expected_types_exist(self) -> None:
        """验证所有期望的文件类型都已定义。"""
        expected = {"FAST", "OPENFAST", "WINDFARM", "BLADED", "SIMULINK", "OTHER", "UNSUPPORTED"}
        actual = set(SimulationFileType._member_names_)
        assert expected.issubset(actual) or expected == actual, (
            f"缺少文件类型: {expected - actual}"
        )

    def test_enum_values_are_strings(self) -> None:
        """验证枚举值为字符串类型。"""
        for member in SimulationFileType:
            assert isinstance(member.value, str)


class TestModelAssetImportRequest:
    """ModelAssetImportRequest DTO 测试。"""

    def test_minimal_creation(self) -> None:
        """验证最小必需字段创建。"""
        req = ModelAssetImportRequest(
            model_code="WF001_FAST_v1",
            model_name="某风场FAST模型",
            model_type="FAST",
            asset_scope="WIND_FARM",
        )
        assert req.model_code == "WF001_FAST_v1"
        assert req.model_name == "某风场FAST模型"
        assert req.model_type == "FAST"
        assert req.asset_scope == "WIND_FARM"
        assert req.version == "1.0"
        assert req.files == []
        assert req.metadata == {}
        assert req.parent_model_code is None

    def test_full_creation(self) -> None:
        """验证全部字段创建。"""
        req = ModelAssetImportRequest(
            model_code="WTG_FAST_v2",
            model_name="风机FAST模型V2",
            model_type="FAST",
            asset_scope="WTG",
            version="2.1",
            parent_model_code="WTG_FAST_v1",
            owner_asset_code="WTG_001",
            files=["/tmp/test.fst", "/tmp/test.fast"],
            checksum_sha256="abc123def456",
            metadata={"rated_power_mw": 5.0},
        )
        assert req.version == "2.1"
        assert req.parent_model_code == "WTG_FAST_v1"
        assert req.owner_asset_code == "WTG_001"
        assert len(req.files) == 2
        assert req.checksum_sha256 == "abc123def456"
        assert req.metadata["rated_power_mw"] == 5.0


class TestModelAssetImportResult:
    """ModelAssetImportResult DTO 测试。"""

    def test_success_result(self) -> None:
        """验证成功导入结果。"""
        result = ModelAssetImportResult(
            success=True,
            model_code="WF001_FAST_v1",
            model_asset_id=1,
            parser_status="IMPORTED",
            artifact_ids=[101, 102],
        )
        assert result.success is True
        assert result.model_asset_id == 1
        assert result.parser_status == "IMPORTED"
        assert len(result.artifact_ids) == 2

    def test_failure_result(self) -> None:
        """验证失败导入结果。"""
        result = ModelAssetImportResult(
            success=False,
            model_code="WF001_BAD",
            error_message="文件格式不支持",
        )
        assert result.success is False
        assert result.model_asset_id is None
        assert result.error_message == "文件格式不支持"


class TestSimulationCaseImportRequest:
    """SimulationCaseImportRequest DTO 测试。"""

    def test_creation(self) -> None:
        """验证仿真案例导入请求创建。"""
        req = SimulationCaseImportRequest(
            case_code="CASE_001_DLC12",
            case_name="DLC 1.2 设计工况",
            model_code="WTG_FAST_v1",
            case_type="DESIGN",
            parameters={"wind_speed_mps": 12.0},
            scenario={"turbulence": "NTM", "shear": 0.2},
            created_by="engineer_01",
        )
        assert req.case_code == "CASE_001_DLC12"
        assert req.model_code == "WTG_FAST_v1"
        assert req.parameters["wind_speed_mps"] == 12.0
        assert req.scenario["turbulence"] == "NTM"

    def test_default_values(self) -> None:
        """验证默认值。"""
        req = SimulationCaseImportRequest(
            case_code="CASE_002",
            case_name="测试案例",
            model_code="M_01",
            case_type="OTHER",
        )
        assert req.parameters == {}
        assert req.scenario == {}
        assert req.created_by is None


class TestSimulationResultImportRequest:
    """SimulationResultImportRequest DTO 测试。"""

    def test_creation(self) -> None:
        """验证仿真结果导入请求创建。"""
        req = SimulationResultImportRequest(
            result_code="RES_001_TIMESERIES",
            case_code="CASE_001_DLC12",
            result_type="TIMESERIES",
            time_series_backend="FILE",
            time_series_ref="/data/res_001.csv",
            summary={"max_power_kw": 5200},
            metrics={"aep_gwh": 22.5},
        )
        assert req.result_code == "RES_001_TIMESERIES"
        assert req.case_code == "CASE_001_DLC12"
        assert req.result_type == "TIMESERIES"
        assert req.summary["max_power_kw"] == 5200
        assert req.metrics["aep_gwh"] == 22.5

    def test_defaults(self) -> None:
        """验证默认值。"""
        req = SimulationResultImportRequest(
            result_code="RES_002",
            case_code="CASE_002",
            result_type="SUMMARY",
        )
        assert req.status == "IMPORTED"
        assert req.files == []
        assert req.summary == {}
        assert req.metrics == {}


class TestSimulationImportManifest:
    """SimulationImportManifest 模型测试。"""

    def test_minimal_creation(self) -> None:
        """验证最小字段创建。"""
        m = SimulationImportManifest(
            model_code="FAST_v1",
            model_type="FAST",
        )
        assert m.model_code == "FAST_v1"
        assert m.version == "1.0"
        assert m.asset_scope == "WTG"
        assert m.files == []
        assert m.metadata == {}

    def test_manifest_fields_match_spec(self) -> None:
        """验证 manifest 字段与规格一致：包含 model_code、model_type、version、
        asset_scope、parent_model_code、files、checksum_sha256、metadata。"""
        m = SimulationImportManifest(
            model_code="WFP_001",
            model_type="WINDFARM",
            version="2.0",
            asset_scope="SITE",
            parent_model_code="WFP_BASE",
            files=["farm.wnd", "farm.wfp"],
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb924",
            metadata={"site_name": "达坂城"},
        )
        assert m.model_code == "WFP_001"
        assert m.model_type == "WINDFARM"
        assert m.version == "2.0"
        assert m.asset_scope == "SITE"
        assert m.parent_model_code == "WFP_BASE"
        assert len(m.files) == 2
        assert m.checksum_sha256 is not None
        assert m.metadata["site_name"] == "达坂城"
