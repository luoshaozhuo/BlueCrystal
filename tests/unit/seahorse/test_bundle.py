"""seahorse 场景包导出与校验测试。

验证：
1. ScenarioBundle 数据类创建与字段完整性。
2. _make_serializable 序列化转换正确性。
3. 确定性校验和计算（相同内容相同 hash，不同内容不同 hash）。
4. JSON bundle 导出与回读。
5. JSONL 时序导出格式正确。
6. Bundle 校验器（schema_version、scenario_id 一致性、seed_plan/server_config 存在性、
   synthetic 标记、checksum 可复算、server_config 结构检查）。
7. CLI 子命令（generate-scenario、export-bundle、validate-bundle）基本可用性。
8. SeahorseGenerator 集成：生成 bundle 并通过校验。

测试阶段：开发期验证 (P1)。
使用的替身：无 — 全部使用真实 SeahorseGenerator 生成。
不能证明：大文件性能、网络传输兼容性、跨语言 JSON 反序列化。
NOT_RUN 条件：无（纯内存测试，无外部依赖）。
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from seahorse.models.scenario import ScenarioConfig, ScenarioMetadata
from seahorse.models.plan import (
    SeedPlan,
    SeedEntity,
    ServerConfig,
    ServerEndpointConfig,
    ServerMemberConfig,
    ServerPointConfig,
    SignalProfileItemPlan,
    SignalProfilePlan,
    EndpointPlan,
    AcquisitionTaskPlan,
)
from seahorse.models.generation import (
    GeneratedSignalValue,
    GeneratedAlarmEvent,
    GeneratedControlResult,
)
from seahorse.models.bundle import ScenarioBundle, _make_serializable
from seahorse.exporters.serialization import compute_bundle_checksum, bundle_to_serializable
from seahorse.exporters.bundle_exporter import export_bundle_to_json, save_bundle
from seahorse.exporters.timeseries_exporter import (
    export_timeseries_to_jsonl,
    save_timeseries,
)
from seahorse.exporters.bundle_validator import (
    ValidationResult,
    validate_bundle,
    validate_bundle_from_dict,
)
from seahorse.orchestration import SeahorseGenerator


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_minimal_bundle(
    scenario_id: str = "test_scenario",
    seed: int = 42,
) -> ScenarioBundle:
    """构造最小有效场景包，供各测试用例使用。

    包含一个实体的完整种子计划、服务端计划和单条信号值。
    校验和已计算。

    Args:
        scenario_id: 场景标识。
        seed: 确定性种子。

    Returns:
        填充完毕且已计算校验和的 ScenarioBundle 实例。
    """
    config = ScenarioConfig(
        scenario_id=scenario_id,
        name="测试场景",
        deterministic_seed=seed,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=60.0,
        asset_count=1,
        protocol_targets=["OPC_UA"],
    )
    metadata = ScenarioMetadata(
        scenario_id=scenario_id,
        seahorse_version="0.2.0",
        config_snapshot={},
        stats={"entity_count": 1},
    )
    entity = SeedEntity(entity_id=f"{scenario_id}_entity_000", entity_type="WTG")
    seed_plan = SeedPlan(
        plan_id=f"plan_{scenario_id}",
        scenario_id=scenario_id,
        entities=[entity],
        signal_profiles=[
            SignalProfilePlan(
                profile_id=f"{scenario_id}_profile_000",
                items=[
                    SignalProfileItemPlan(
                        signal_id=f"{scenario_id}_profile_000_ActivePower",
                        signal_name="ActivePower",
                        unit="kW",
                    )
                ],
            )
        ],
        endpoints=[
            EndpointPlan(
                endpoint_id=f"{scenario_id}_entity_000_OPC_UA_ep",
                application_protocol="OPC_UA",
            )
        ],
        acquisition_tasks=[
            AcquisitionTaskPlan(
                task_id=f"{scenario_id}_entity_000_OPC_UA_ep_task",
                associated_endpoint_id=f"{scenario_id}_entity_000_OPC_UA_ep",
            )
        ],
    )
    server_config = ServerConfig(
        config_id=f"server_config_{scenario_id}",
        scenario_id=scenario_id,
        config_name=f"{scenario_id}_config",
        servers=[
            ServerMemberConfig(
                server_id=f"server_{scenario_id}",
                server_name=f"{scenario_id}_server",
                endpoints=[
                    ServerEndpointConfig(
                        endpoint_name="OPC_UA_server_ep",
                        protocol="OPC_UA",
                        bind_port=4840,
                    )
                ],
                points=[
                    ServerPointConfig(
                        point_id=f"{scenario_id}_entity_000_active_power",
                        point_name="ActivePower",
                        associated_signal_id=f"{scenario_id}_entity_000_ActivePower",
                    )
                ],
            )
        ],
    )
    signal = GeneratedSignalValue(
        signal_id="sig_1",
        scenario_id=scenario_id,
        device_id=entity.entity_id,
        timestamp=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        value=100.0,
        synthetic=True,
    )
    alarm = GeneratedAlarmEvent(
        alarm_id="alm_1",
        entity_id=entity.entity_id,
        alarm_type="THRESHOLD",
        severity="MAJOR",
        timestamp=datetime(2024, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
        message="测试告警",
    )
    control = GeneratedControlResult(
        control_id="ctrl_1",
        entity_id=entity.entity_id,
        control_type="START",
        status="ACCEPTED",
        timestamp=datetime(2024, 1, 1, 0, 2, 0, tzinfo=timezone.utc),
    )

    bundle = ScenarioBundle(
        schema_version="1.0.0",
        scenario_version="1.0.0",
        generator_version="0.2.0",
        created_at=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        scenario_id=scenario_id,
        name="测试场景",
        deterministic_seed=seed,
        synthetic=True,
        scenario_config=config,
        scenario_metadata=metadata,
        seed_plan=seed_plan,
        server_config=server_config,
        generated_timeseries_sample=[signal],
        alarm_events=[alarm],
        control_results=[control],
    )
    bundle.checksum = compute_bundle_checksum(bundle)
    return bundle


# ── ScenarioBundle 数据类 ──────────────────────────────────────────────────────


def test_scenario_bundle_defaults() -> None:
    """ScenarioBundle 应具有正确的默认值。"""
    bundle = ScenarioBundle()
    assert bundle.schema_version == "1.0.0"
    assert bundle.scenario_version == "1.0.0"
    assert bundle.generator_version == "0.2.0"
    assert bundle.synthetic is True
    assert bundle.checksum == ""
    assert bundle.seed_plan is None
    assert bundle.server_config is None
    assert bundle.generated_timeseries_sample == []
    assert bundle.alarm_events == []
    assert bundle.control_results == []


def test_scenario_bundle_field_assignment() -> None:
    """ScenarioBundle 字段应正确赋值。"""
    bundle = _make_minimal_bundle("field_test")
    assert bundle.scenario_id == "field_test"
    assert bundle.name == "测试场景"
    assert bundle.deterministic_seed == 42
    assert bundle.synthetic is True
    assert bundle.seed_plan is not None
    assert bundle.server_config is not None
    assert len(bundle.generated_timeseries_sample) == 1
    assert len(bundle.alarm_events) == 1
    assert len(bundle.control_results) == 1
    assert bundle.checksum != ""


def test_scenario_bundle_created_at_is_datetime() -> None:
    """created_at 应为 datetime 类型。"""
    bundle = ScenarioBundle()
    assert isinstance(bundle.created_at, datetime)


def test_scenario_bundle_replay_metadata_optional() -> None:
    """replay_metadata 默认应为 None。"""
    bundle = ScenarioBundle()
    assert bundle.replay_metadata is None

    bundle.replay_metadata = {"source": "replay.jsonl", "speed_factor": 2.0}
    assert bundle.replay_metadata["source"] == "replay.jsonl"


# ── _make_serializable ─────────────────────────────────────────────────────────


def test_make_serializable_dataclass() -> None:
    """_make_serializable 应正确转换 dataclass 为 dict。"""
    signal = GeneratedSignalValue(
        signal_id="sig_1",
        scenario_id="test",
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
        value=42.5,
        quality=0,
        synthetic=True,
    )
    result = _make_serializable(signal)
    assert isinstance(result, dict)
    assert result["signal_id"] == "sig_1"
    assert result["value"] == 42.5
    assert result["synthetic"] is True
    assert isinstance(result["timestamp"], str)
    assert "2024-01-01" in result["timestamp"]


def test_make_serializable_datetime() -> None:
    """_make_serializable 应将 datetime 转换为 ISO 字符串。"""
    dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = _make_serializable(dt)
    assert isinstance(result, str)
    assert "2024-06-01" in result
    assert "12:00:00" in result


def test_make_serializable_nested() -> None:
    """_make_serializable 应递归处理嵌套 dataclass。"""
    bundle = _make_minimal_bundle("nested_test")
    result = _make_serializable(bundle)
    assert isinstance(result, dict)
    assert result["schema_version"] == "1.0.0"
    assert isinstance(result["seed_plan"], dict)
    assert result["seed_plan"]["scenario_id"] == "nested_test"
    assert isinstance(result["generated_timeseries_sample"], list)
    assert len(result["generated_timeseries_sample"]) == 1


def test_make_serializable_list() -> None:
    """_make_serializable 应处理普通 list。"""
    result = _make_serializable([1, 2, 3])
    assert result == [1, 2, 3]


def test_make_serializable_bytes() -> None:
    """_make_serializable 应将 bytes 转换为 hex 字符串。"""
    result = _make_serializable(b"hello")
    assert result == "68656c6c6f"


# ── 校验和计算 ─────────────────────────────────────────────────────────────────


def test_checksum_is_deterministic() -> None:
    """相同内容的 bundle 应产生相同校验和。"""
    bundle1 = _make_minimal_bundle("cs_test", seed=42)
    bundle2 = _make_minimal_bundle("cs_test", seed=42)
    assert bundle1.checksum == bundle2.checksum
    assert len(bundle1.checksum) == 64  # SHA256 hex


def test_checksum_differs_for_different_content() -> None:
    """不同 seed 的 bundle 应产生不同校验和。"""
    bundle1 = _make_minimal_bundle("cs_diff", seed=42)
    bundle2 = _make_minimal_bundle("cs_diff", seed=99)
    assert bundle1.checksum != bundle2.checksum


def test_checksum_differs_for_different_scenario_id() -> None:
    """不同 scenario_id 的 bundle 应产生不同校验和。"""
    bundle1 = _make_minimal_bundle("id_a", seed=42)
    bundle2 = _make_minimal_bundle("id_b", seed=42)
    assert bundle1.checksum != bundle2.checksum


def test_checksum_excludes_created_at() -> None:
    """校验和应排除 created_at，不同生成时间的相同内容产生相同校验和。"""
    bundle1 = _make_minimal_bundle("no_ts")
    bundle1.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    bundle2 = _make_minimal_bundle("no_ts")
    bundle2.created_at = datetime(2025, 12, 31, tzinfo=timezone.utc)
    # 重新计算排除 created_at 后的校验和
    cs1 = compute_bundle_checksum(bundle1)
    cs2 = compute_bundle_checksum(bundle2)
    assert cs1 == cs2


def test_checksum_is_sha256_hex() -> None:
    """校验和应为 64 字符 SHA256 十六进制字符串。"""
    bundle = _make_minimal_bundle()
    assert len(bundle.checksum) == 64
    assert all(c in "0123456789abcdef" for c in bundle.checksum)


# ── JSON Bundle 导出 ───────────────────────────────────────────────────────────


def test_export_bundle_to_json_returns_string() -> None:
    """export_bundle_to_json 应返回有效 JSON 字符串。"""
    bundle = _make_minimal_bundle("json_export")
    result = export_bundle_to_json(bundle)
    assert isinstance(result, str)
    # 应可被 json.loads 解析
    parsed = json.loads(result)
    assert parsed["scenario_id"] == "json_export"


def test_export_bundle_to_json_contains_all_fields() -> None:
    """导出的 JSON 应包含所有必要字段。"""
    bundle = _make_minimal_bundle("full_export")
    result = export_bundle_to_json(bundle)
    parsed = json.loads(result)
    required_fields = [
        "schema_version", "scenario_version", "generator_version",
        "created_at", "scenario_id", "name", "deterministic_seed",
        "synthetic", "scenario_config", "scenario_metadata",
        "seed_plan", "server_config", "generated_timeseries_sample",
        "alarm_events", "control_results", "checksum",
    ]
    for field in required_fields:
        assert field in parsed, f"缺少字段: {field}"


def test_save_bundle_creates_file() -> None:
    """save_bundle 应在指定目录创建 JSON 文件。"""
    bundle = _make_minimal_bundle("save_test")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_bundle(bundle, tmpdir)
        assert path.exists()
        assert path.suffix == ".json"
        content = path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert parsed["scenario_id"] == "save_test"


def test_save_bundle_creates_parent_dirs() -> None:
    """save_bundle 在父目录不存在时应自动创建。"""
    bundle = _make_minimal_bundle("mkdir_test")
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "deep" / "nested"
        path = save_bundle(bundle, nested)
        assert path.exists()
        assert path.parent == nested


def test_bundle_json_round_trip() -> None:
    """Bundle JSON 导出后应可成功加载并校验。"""
    bundle = _make_minimal_bundle("roundtrip")
    json_str = export_bundle_to_json(bundle)
    loaded = json.loads(json_str)

    # 通过 validate_bundle_from_dict 重建并校验
    result = validate_bundle_from_dict(loaded)
    assert result.is_valid, f"校验失败: {result.errors}"
    assert len(result.errors) == 0


# ── JSONL 时序导出 ─────────────────────────────────────────────────────────────


def test_export_timeseries_to_jsonl() -> None:
    """export_timeseries_to_jsonl 应返回每行一个 JSON 对象的文本。"""
    signals = [
        GeneratedSignalValue(
            signal_id="sig_1",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=100.0,
            synthetic=True,
        ),
        GeneratedSignalValue(
            signal_id="sig_2",
            timestamp=datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            value=200.0,
            synthetic=True,
        ),
    ]
    result = export_timeseries_to_jsonl(signals)
    assert isinstance(result, str)
    lines = result.strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "signal_id" in obj
        assert "value" in obj
        assert obj["synthetic"] is True


def test_export_timeseries_to_jsonl_empty() -> None:
    """空信号值列表应只输出换行符。"""
    result = export_timeseries_to_jsonl([])
    assert result == "\n"


def test_save_timeseries_creates_file() -> None:
    """save_timeseries 应在指定目录创建 JSONL 文件。"""
    signals = [
        GeneratedSignalValue(
            signal_id="sig_save",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=50.0,
            synthetic=True,
        ),
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_timeseries(signals, tmpdir, scenario_id="ts_test")
        assert path.exists()
        assert path.suffix == ".jsonl"
        content = path.read_text(encoding="utf-8")
        assert "sig_save" in content


# ── Bundle 校验 ────────────────────────────────────────────────────────────────


def test_validate_bundle_all_pass() -> None:
    """正确构造的 bundle 应全部校验通过。"""
    bundle = _make_minimal_bundle("valid_test")
    result = validate_bundle(bundle)
    assert result.is_valid
    assert len(result.errors) == 0
    assert len(result.passed_checks) >= 6


def test_validate_bundle_missing_schema_version() -> None:
    """缺少 schema_version 应报错。"""
    bundle = _make_minimal_bundle("no_schema")
    bundle.schema_version = ""
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("schema_version" in e for e in result.errors)


def test_validate_bundle_inconsistent_scenario_id() -> None:
    """scenario_id 不一致应报错。"""
    bundle = _make_minimal_bundle("consistency_test")
    if bundle.seed_plan:
        bundle.seed_plan.scenario_id = "mismatched"
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("不一致" in e for e in result.errors)


def test_validate_bundle_missing_seed_plan() -> None:
    """缺少 seed_plan 应报错。"""
    bundle = _make_minimal_bundle("no_sp")
    bundle.seed_plan = None
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("seed_plan" in e for e in result.errors)


def test_validate_bundle_missing_server_config() -> None:
    """缺少 server_config 应报错。"""
    bundle = _make_minimal_bundle("no_srv")
    bundle.server_config = None
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("server_config" in e for e in result.errors)


def test_validate_bundle_non_synthetic_signal() -> None:
    """存在 synthetic=False 的信号应报错。"""
    bundle = _make_minimal_bundle("non_syn")
    bundle.generated_timeseries_sample = [
        GeneratedSignalValue(
            signal_id="bad_sig",
            timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
            value=0.0,
            synthetic=False,
        )
    ]
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("synthetic" in e for e in result.errors)


def test_validate_bundle_missing_checksum() -> None:
    """缺少 checksum 应报错。"""
    bundle = _make_minimal_bundle("no_cs")
    bundle.checksum = ""
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("checksum" in e for e in result.errors)


def test_validate_bundle_checksum_mismatch() -> None:
    """校验和不匹配应报错。"""
    bundle = _make_minimal_bundle("cs_mismatch")
    bundle.checksum = "0" * 64
    result = validate_bundle(bundle)
    assert not result.is_valid
    assert any("checksum" in e for e in result.errors)


def test_validate_bundle_server_config_structure() -> None:
    """server_config 缺少 endpoint_name 或 point_id 应产生警告（非错误）。"""
    bundle = _make_minimal_bundle("srv_struct")
    if bundle.server_config and bundle.server_config.servers:
        server = bundle.server_config.servers[0]
        if server.endpoints:
            server.endpoints[0].endpoint_name = ""
            server.endpoints[0].protocol = ""
        if server.points:
            server.points[0].point_id = ""
    result = validate_bundle(bundle)
    # endpoint_name/protocol 缺失是警告不是错误
    assert result.warnings, "应产生警告"
    # 但整体仍应视为有效（因 seed_plan、synthetic 等检查通过）
    # 注意：如果 checksum 也同时变化则需要重算
    bundle.checksum = compute_bundle_checksum(bundle)
    result2 = validate_bundle(bundle)
    assert result2.is_valid, f"校验失败: {result2.errors}"


def test_validation_result_defaults() -> None:
    """ValidationResult 默认值应为有效状态。"""
    vr = ValidationResult()
    assert vr.is_valid
    assert vr.errors == []
    assert vr.warnings == []
    assert vr.passed_checks == []


def test_validation_result_add_error() -> None:
    """add_error 应记录错误并将 is_valid 置为 False。"""
    vr = ValidationResult()
    vr.add_error("测试错误")
    assert not vr.is_valid
    assert len(vr.errors) == 1
    assert vr.errors[0] == "测试错误"


def test_validation_result_add_warning() -> None:
    """add_warning 应记录警告但不影响 is_valid。"""
    vr = ValidationResult()
    vr.add_warning("测试警告")
    assert vr.is_valid
    assert len(vr.warnings) == 1


def test_validate_bundle_from_dict_roundtrip() -> None:
    """从 dict 重建 bundle 并校验，结果应与原始校验一致。"""
    bundle = _make_minimal_bundle("dict_rt")
    serializable = bundle_to_serializable(bundle)
    json_str = json.dumps(serializable, ensure_ascii=False, default=str)
    loaded = json.loads(json_str)

    result = validate_bundle_from_dict(loaded)
    assert result.is_valid, f"从 dict 校验失败: {result.errors}"


# ── SeahorseGenerator 集成 ─────────────────────────────────────────────────────


def test_generator_to_bundle_integration() -> None:
    """SeahorseGenerator generate() 产出应可打包为有效 bundle。"""
    config = ScenarioConfig(
        scenario_id="integration_test",
        deterministic_seed=123,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=1.0,
        asset_count=1,
        protocol_targets=["OPC_UA"],
    )
    generator = SeahorseGenerator(config)
    seed_plan, server_config, signals, alarms, controls = generator.generate()

    bundle = ScenarioBundle(
        schema_version="1.0.0",
        scenario_id="integration_test",
        deterministic_seed=123,
        synthetic=True,
        scenario_config=config,
        scenario_metadata=generator.metadata,
        seed_plan=seed_plan,
        server_config=server_config,
        generated_timeseries_sample=signals,
        alarm_events=alarms,
        control_results=controls,
    )
    bundle.checksum = compute_bundle_checksum(bundle)

    # 应通过校验
    result = validate_bundle(bundle)
    assert result.is_valid, f"集成校验失败: {result.errors}"
    assert len(bundle.generated_timeseries_sample) > 0
    assert all(sv.synthetic for sv in bundle.generated_timeseries_sample)


def test_generator_bundle_deterministic() -> None:
    """相同 config 两次 generate 应产生校验和一致的 bundle。"""
    def _make_bundle() -> ScenarioBundle:
        config = ScenarioConfig(
            scenario_id="det_bundle",
            deterministic_seed=42,
            start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
            duration_seconds=0.5,
            asset_count=1,
            protocol_targets=["OPC_UA"],
        )
        generator = SeahorseGenerator(config)
        seed_plan, server_config, signals, alarms, controls = generator.generate()
        bundle = ScenarioBundle(
            schema_version="1.0.0",
            scenario_id="det_bundle",
            deterministic_seed=42,
            synthetic=True,
            scenario_config=config,
            scenario_metadata=generator.metadata,
            seed_plan=seed_plan,
            server_config=server_config,
            generated_timeseries_sample=signals,
            alarm_events=alarms,
            control_results=controls,
        )
        bundle.checksum = compute_bundle_checksum(bundle)
        return bundle

    bundle1 = _make_bundle()
    bundle2 = _make_bundle()
    assert bundle1.checksum == bundle2.checksum
    # 同时验证通过校验
    result1 = validate_bundle(bundle1)
    result2 = validate_bundle(bundle2)
    assert result1.is_valid
    assert result2.is_valid


# ── CLI smoke tests ────────────────────────────────────────────────────────────


def test_cli_generate_scenario_help() -> None:
    """generate-scenario --help 应正常输出用法。"""
    from seahorse.__main__ import main
    with pytest.raises(SystemExit) as exc_info:
        main(["generate-scenario", "--help"])
    assert exc_info.value.code == 0


def test_cli_export_bundle_help() -> None:
    """export-bundle --help 应正常输出用法。"""
    from seahorse.__main__ import main
    with pytest.raises(SystemExit) as exc_info:
        main(["export-bundle", "--help"])
    assert exc_info.value.code == 0


def test_cli_validate_bundle_help() -> None:
    """validate-bundle --help 应正常输出用法。"""
    from seahorse.__main__ import main
    with pytest.raises(SystemExit) as exc_info:
        main(["validate-bundle", "--help"])
    assert exc_info.value.code == 0


def test_cli_generate_and_validate_roundtrip() -> None:
    """CLI generate-scenario 产出应可通过 validate-bundle 校验。"""
    from seahorse.__main__ import main

    with tempfile.TemporaryDirectory() as tmpdir:
        # 生成场景
        rc = main([
            "generate-scenario",
            "--scenario-id", "cli_test",
            "--seed", "99",
            "--asset-count", "1",
            "--duration", "0.5",
            "--output-dir", tmpdir,
            "--start-time", "2024-01-01T00:00:00+00:00",
        ])
        assert rc == 0

        # 检查输出文件
        bundle_path = Path(tmpdir) / "cli_test_bundle.json"
        assert bundle_path.exists()

        ts_path = Path(tmpdir) / "cli_test_timeseries.jsonl"
        assert ts_path.exists()

        # 校验生成的 bundle
        rc2 = main([
            "validate-bundle",
            "--input", str(bundle_path),
        ])
        assert rc2 == 0


def test_cli_validate_missing_file() -> None:
    """校验不存在的文件应返回非零退出码。"""
    from seahorse.__main__ import main
    rc = main([
        "validate-bundle",
        "--input", "/nonexistent/path/bundle.json",
    ])
    assert rc != 0


def test_cli_export_missing_file() -> None:
    """导出不存在的文件应返回非零退出码。"""
    from seahorse.__main__ import main
    rc = main([
        "export-bundle",
        "--input", "/nonexistent/path/bundle.json",
    ])
    assert rc != 0


def test_cli_no_command_shows_help() -> None:
    """无子命令时 main() 应返回非零退出码（打印帮助后）。"""
    from seahorse.__main__ import main
    # 无子命令时 main() 打印帮助并返回 1（非 SystemExit）
    rc = main([])
    assert rc != 0, "无子命令时应返回非零退出码"
