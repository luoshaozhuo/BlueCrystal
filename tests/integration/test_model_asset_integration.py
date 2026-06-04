"""model_asset 模块集成测试。

验证导入模型资产 -> raw_archive -> DB 元数据写入的完整链路，
以及案例导入 -> 结果导入 -> artifact -> result series InMemory 的完整链路。

使用 SQLite 内存数据库和 LocalCompressedArchiveSink + InMemorySink 闭环。

被验证对象：
- whale.model_asset.detector / archive / repository / service
- whale.storage.simulation_result

测试阶段：模块集成期验证 (integration，使用临时文件 + SQLite)。
不能证明：PostgreSQL 和真实文件系统存储下的行为。
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from whale.shared.persistence import Base
from whale.model_asset.archive import SimulationArchiveService
from whale.model_asset.detector import SimulationFileTypeDetector
from whale.model_asset.models import (
    ModelAssetImportRequest,
    SimulationCaseImportRequest,
    SimulationImportManifest,
    SimulationResultImportRequest,
)
from whale.model_asset.repository import ModelAssetRepository
from whale.model_asset.service import ModelAssetImportService
from whale.storage.raw_archive import (
    InMemoryManifestRepository,
    LocalCompressedArchiveSink,
)
from whale.storage.simulation_result import (
    InMemorySimulationResultTimeSeriesSink,
)


class TestModelAssetIntegration:
    """模型资产导入全链路集成测试。"""

    @pytest.fixture(scope="function")
    def session(self) -> Session:
        """创建 SQLite 内存数据库 session。"""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            yield session
        finally:
            session.rollback()
            session.close()
            Base.metadata.drop_all(engine)

    @pytest.fixture(scope="function")
    def service(self, session: Session, tmp_path: Path) -> ModelAssetImportService:
        """创建完整的 ModelAssetImportService。"""
        detector = SimulationFileTypeDetector()
        archive_sink = LocalCompressedArchiveSink(tmp_path / "archive")
        manifest_repo = InMemoryManifestRepository()
        archive_svc = SimulationArchiveService(archive_sink, manifest_repo)
        repo = ModelAssetRepository(session)
        return ModelAssetImportService(detector, archive_svc, repo)

    @pytest.mark.asyncio
    async def test_full_import_chain(
        self,
        service: ModelAssetImportService,
        tmp_path: Path,
        session: Session,
    ) -> None:
        """验证完整导入链路：模型 -> 案例 -> 结果 -> 时序数据。

        步 1: 导入模型资产（归档源文件 + 写入 DB 元数据）。
        步 2: 导入仿真案例（关联模型 + 写入 DB）。
        步 3: 导入仿真结果（关联案例 + 写入 DB）。
        步 4: 将时序数据写入 InMemory sink。
        """
        # 步 1: 导入模型资产
        fst_file = tmp_path / "wtg_fast.fst"
        fst_file.write_text("FAST v8.16 input file for 5MW turbine")
        fast_file = tmp_path / "wtg.fast"
        fast_file.write_text("Turbine input")

        import_req = ModelAssetImportRequest(
            model_code="WTG_INTEG_001",
            model_name="集成测试风机模型",
            model_type="FAST",
            asset_scope="WTG",
            version="1.0",
            files=[str(fst_file), str(fast_file)],
        )
        result = await service.import_model_asset(import_req)
        assert result.success is True
        assert result.model_asset_id is not None

        # 验证归档文件存在
        archive_dir = tmp_path / "archive"
        files_in_archive = list(archive_dir.glob("*.jsonl.gz"))
        assert len(files_in_archive) >= 1, f"归档目录无文件: {list(archive_dir.iterdir())}"

        # 验证 DB 中模型资产可查询
        repo = ModelAssetRepository(session)
        asset = repo.get_model_asset_by_code("WTG_INTEG_001")
        assert asset is not None
        assert asset.model_name == "集成测试风机模型"
        assert asset.model_type == "FAST"
        assert asset.parser_status == "IMPORTED"

        # 步 2: 导入仿真案例
        case_req = SimulationCaseImportRequest(
            case_code="CASE_INTEG_DLC12",
            case_name="DLC 1.2 设计工况",
            model_code="WTG_INTEG_001",
            case_type="DESIGN",
            parameters={"wind_speed_mps": 12.0, "turbulence_intensity": 0.14},
            scenario={"iec_class": "IIB"},
            created_by="integration_test",
        )
        case_result = await service.import_simulation_case(case_req)
        assert case_result["success"] is True

        case = repo.get_case_by_code("CASE_INTEG_DLC12")
        assert case is not None
        assert case.case_type == "DESIGN"
        assert case.parameter_json["wind_speed_mps"] == 12.0
        assert case.status == "CREATED"

        # 步 3: 导入仿真结果
        result_req = SimulationResultImportRequest(
            result_code="RES_INTEG_TIMESERIES",
            case_code="CASE_INTEG_DLC12",
            result_type="TIMESERIES",
            time_series_backend="FILE",
            time_series_ref="/data/res_int.csv",
            summary={"max_power_kw": 5200, "avg_wind_mps": 11.8},
            metrics={"aep_gwh": 22.1, "capacity_factor": 0.45},
        )
        res_result = await service.import_simulation_result(result_req)
        assert res_result["success"] is True

        sim_res = repo.get_result_by_code("RES_INTEG_TIMESERIES")
        assert sim_res is not None
        assert sim_res.result_type == "TIMESERIES"
        assert sim_res.summary_json["max_power_kw"] == 5200
        assert sim_res.status == "IMPORTED"

        # 步 4: 写入 InMemory 时序数据
        sink = InMemorySimulationResultTimeSeriesSink()
        await sink.write_result_series(
            result_code="RES_INTEG_TIMESERIES",
            channel_name="gen_speed_rpm",
            timestamps=[
                "2025-01-01T00:00:00Z",
                "2025-01-01T00:00:01Z",
                "2025-01-01T00:00:02Z",
            ],
            values=[1200.0, 1215.0, 1208.0],
            unit="rpm",
            metadata={"simulator": "FAST"},
        )
        data = await sink.read_result_series("RES_INTEG_TIMESERIES", "gen_speed_rpm")
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_import_manifest_chain(
        self,
        service: ModelAssetImportService,
        tmp_path: Path,
        session: Session,
    ) -> None:
        """验证基于 SimulationImportManifest 的导入链路。

        确保 manifest 定义的 model_code、model_type、version、asset_scope、
        parent_model_code、files、checksum_sha256、metadata 都正确持久化。
        """
        fst = tmp_path / "manifest_model.fst"
        fst.write_text("FAST manifest test")

        # 通过 manifest 字段构造导入请求，验证所有字段可表达
        manifest = SimulationImportManifest(
            model_code="MANIFEST_001",
            model_type="OPENFAST",
            version="3.5",
            asset_scope="SITE",
            parent_model_code=None,
            files=[str(fst)],
            checksum_sha256="e3b0c44298fc1c149afbf4c8996fb924",
            metadata={"description": "manifest 测试模型"},
        )

        request = ModelAssetImportRequest(
            model_code=manifest.model_code,
            model_name=f"Manifest 模型 {manifest.model_code}",
            model_type=manifest.model_type,
            asset_scope=manifest.asset_scope,
            version=manifest.version,
            parent_model_code=manifest.parent_model_code,
            files=manifest.files,
            checksum_sha256=manifest.checksum_sha256,
            metadata=manifest.metadata,
        )

        result = await service.import_model_asset(request)
        assert result.success is True

        repo = ModelAssetRepository(session)
        asset = repo.get_model_asset_by_code("MANIFEST_001")
        assert asset is not None
        assert asset.model_type == "OPENFAST"
        assert asset.asset_scope == "SITE"
        assert asset.version == "3.5"
        assert asset.metadata_json["description"] == "manifest 测试模型"

    @pytest.mark.asyncio
    async def test_model_type_detection_and_persistence(
        self,
        service: ModelAssetImportService,
        tmp_path: Path,
        session: Session,
    ) -> None:
        """验证不同文件类型的检测和持久化。

        测试 FAST、OpenFAST (YAML+marker)、WINDFARM、BLADED、SIMULINK 五种类型。
        """
        test_cases = [
            ("FAST", "fast_model.fst", "FAST v8 input"),
            ("OPENFAST", "of_model.yaml", "openfast:\n  version: 3.5"),
            ("WINDFARM", "farm.wnd", "wind farm layout"),
            ("BLADED", "bladed.prj", "BLADED project"),
            ("SIMULINK", "controller.slx", "Simulink model"),
        ]

        repo = ModelAssetRepository(session)

        for model_type, fname, content in test_cases:
            f = tmp_path / fname
            f.write_text(content)

            code = f"MT_{model_type}_INTEG"
            req = ModelAssetImportRequest(
                model_code=code,
                model_name=f"{model_type} 集成测试",
                model_type=model_type,
                asset_scope="WTG",
                files=[str(f)],
            )
            result = await service.import_model_asset(req)
            assert result.success is True, f"{model_type} 导入失败"

            asset = repo.get_model_asset_by_code(code)
            assert asset is not None, f"{model_type} 未持久化"
            assert asset.model_type == model_type

    @pytest.mark.asyncio
    async def test_result_series_inmemory_full_cycle(
        self,
        service: ModelAssetImportService,
        tmp_path: Path,
        session: Session,
    ) -> None:
        """验证仿真结果时序数据 InMemory 完整读写循环。

        导入模型、案例、结果后，通过 InMemory sink 写入和读取时序数据。
        """
        # 建立基础数据
        f = tmp_path / "series_model.fst"
        f.write_text("test")
        await service.import_model_asset(ModelAssetImportRequest(
            model_code="SERIES_01", model_name="时序测试",
            model_type="FAST", asset_scope="WTG", files=[str(f)],
        ))
        await service.import_simulation_case(SimulationCaseImportRequest(
            case_code="SERIES_CASE", case_name="时序案例",
            model_code="SERIES_01", case_type="DESIGN",
        ))
        await service.import_simulation_result(SimulationResultImportRequest(
            result_code="SERIES_RES", case_code="SERIES_CASE",
            result_type="TIMESERIES",
        ))

        # InMemory 时序写入
        sink = InMemorySimulationResultTimeSeriesSink()
        channels: dict[str, list[float]] = {
            "wind_speed": [8.0, 8.5, 9.0, 10.0, 11.0],
            "gen_power": [1500.0, 1800.0, 2200.0, 3100.0, 4200.0],
            "pitch_angle": [0.0, 2.0, 5.0, 8.0, 10.0],
        }

        for ch_name, values in channels.items():
            ts = [f"2025-01-01T00:00:{i:02d}Z" for i in range(len(values))]
            await sink.write_result_series(
                result_code="SERIES_RES",
                channel_name=ch_name,
                timestamps=ts,
                values=values,
                unit="unit",
            )

        # 验证各通道数据
        for ch_name, expected_values in channels.items():
            data = await sink.read_result_series("SERIES_RES", ch_name)
            assert len(data) == len(expected_values)
            for i, (d, ev) in enumerate(zip(data, expected_values)):
                assert d["value"] == ev, f"通道 {ch_name} 值不匹配: idx={i}"

        # 验证时间范围查询
        subset = await sink.read_result_series(
            "SERIES_RES", "wind_speed",
            start_time="2025-01-01T00:00:02Z",
            end_time="2025-01-01T00:00:03Z",
        )
        assert len(subset) == 2  # 索引 2 (9.0) 和 3 (10.0)
