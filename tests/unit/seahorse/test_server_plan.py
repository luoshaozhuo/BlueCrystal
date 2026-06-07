"""seahorse ServerPlan 契约校验、handoff 导出与 CLI 测试。

验证：
1. ServerPlan 校验器成功路径。
2. ServerPlan 校验器：缺 protocol、endpoint 空、point 空等失败场景。
3. ServerPlan 校验器：initial_values 指向未知 point 的警告。
4. ServerPlan handoff JSON 导出结构完整性。
5. ServerPlan handoff payload_hash 稳定性与确定性。
6. ScenarioBundle -> ServerPlan handoff roundtrip。
7. CLI export-server-plan smoke 测试。

测试阶段：开发期验证 (P1)。
使用的替身：无 — 所有数据由 fixture 构造或 SeahorseGenerator 生成。
外部依赖：无（纯内存 / 临时文件测试）。
不能证明：Starfish runtime 实际启动、跨语言 JSON 反序列化。
NOT_RUN 条件：无。
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from seahorse.models.scenario import ScenarioConfig
from seahorse.models.plan import (
    ServerPlan,
    ServerEndpointPlan,
    ServerPointPlan,
)
from seahorse.models.bundle import ScenarioBundle
from seahorse.exporters.server_plan_validator import (
    validate_server_plan,
    validate_server_plan_from_dict,
)
from seahorse.exporters.server_plan_exporter import (
    build_server_plan_payload,
    export_server_plan_to_json,
    export_server_plan_from_bundle,
    save_server_plan,
    save_server_plan_from_bundle,
)
from seahorse.exporters.serialization import compute_bundle_checksum
from seahorse.orchestration import SeahorseGenerator


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_valid_server_plan(
    scenario_id: str = "sp_test",
    protocol: str = "OPC_UA",
) -> ServerPlan:
    """构造一个通过全部校验的最小有效 ServerPlan。

    包含一个端点、一个点位、合法 capabilities 和可追溯的 initial_values。

    Args:
        scenario_id: 场景标识。
        protocol: 端点协议。

    Returns:
        完全有效可通过校验的 ServerPlan 实例。
    """
    ep_id = f"{scenario_id}_{protocol}_ep"
    pt_id = f"{scenario_id}_point_000"
    return ServerPlan(
        server_id=f"server_{scenario_id}",
        scenario_id=scenario_id,
        server_name="测试 ServerPlan",
        endpoints=[
            ServerEndpointPlan(
                endpoint_name=f"{protocol}_ep",
                endpoint_id=ep_id,
                protocol=protocol,
                bind_host="0.0.0.0",
                bind_port=4840,
                host="127.0.0.1",
                port=4840,
            )
        ],
        points=[
            ServerPointPlan(
                point_id=pt_id,
                point_name="TestPoint",
                data_type="FLOAT64",
                access_mode="RO",
                node_key=f"ns=2;s={pt_id}",
                variable_key="Value",
                value_type="Float",
            )
        ],
        synthetic=True,
        strategy_id="test_strategy",
        capabilities=["READ"],
        update_policy={"default": {"mode": "poll", "interval_ms": 100}},
        initial_values={pt_id: 0.0},
    )


# ── 校验器：成功路径 ────────────────────────────────────────────────────────────


def test_validate_server_plan_all_pass() -> None:
    """完全合法的 ServerPlan 应全部校验通过。"""
    sp = _make_valid_server_plan("v_all_pass")
    result = validate_server_plan(sp)
    assert result.is_valid, f"校验失败: {result.errors}"
    assert len(result.errors) == 0
    assert len(result.passed_checks) >= 8


def test_validate_server_plan_minimal_fields() -> None:
    """最小字段的 ServerPlan（默认值）校验应根据结构判断。

    默认构造的 ServerPlan endpoints 和 points 为空，应校验失败。
    """
    sp = ServerPlan(server_id="minimal", scenario_id="min_test")
    result = validate_server_plan(sp)
    # endpoints 和 points 为空，应失败
    assert not result.is_valid
    assert any("endpoints" in e.lower() for e in result.errors)
    assert any("points" in e.lower() for e in result.errors)


# ── 校验器：失败场景 ────────────────────────────────────────────────────────────


def test_validate_server_plan_missing_scenario_id() -> None:
    """缺少 scenario_id 应报错。"""
    sp = _make_valid_server_plan("v_no_sid")
    sp.scenario_id = ""
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("scenario_id" in e for e in result.errors)


def test_validate_server_plan_missing_protocol() -> None:
    """endpoint 缺少 protocol 应报错。"""
    sp = _make_valid_server_plan("v_no_proto")
    sp.endpoints[0].protocol = ""
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("protocol" in e for e in result.errors)


def test_validate_server_plan_missing_endpoint_id() -> None:
    """endpoint 缺少 endpoint_id 应报错。"""
    sp = _make_valid_server_plan("v_no_epid")
    sp.endpoints[0].endpoint_id = ""
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("endpoint_id" in e for e in result.errors)


def test_validate_server_plan_empty_endpoints() -> None:
    """endpoints 为空应报错。"""
    sp = _make_valid_server_plan("v_empty_ep")
    sp.endpoints = []
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("endpoints" in e.lower() for e in result.errors)


def test_validate_server_plan_empty_points() -> None:
    """points 为空应报错。"""
    sp = _make_valid_server_plan("v_empty_pt")
    sp.points = []
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("points" in e.lower() for e in result.errors)


def test_validate_server_plan_tcp_invalid_port() -> None:
    """TCP 类协议 port 为 0 应报错。"""
    sp = _make_valid_server_plan("v_bad_port", protocol="MODBUS_TCP")
    sp.endpoints[0].port = 0
    sp.endpoints[0].bind_port = 0
    result = validate_server_plan(sp)
    assert not result.is_valid
    assert any("port" in e.lower() for e in result.errors)


def test_validate_server_plan_non_tcp_skips_port_check() -> None:
    """非 TCP 协议（如 SERIAL）应跳过 host/port 检查。

    使用自定义协议名，不在 TCP 类协议列表中。
    """
    sp = _make_valid_server_plan("v_serial", protocol="RTU_SERIAL")
    sp.endpoints[0].port = 0
    sp.endpoints[0].host = ""
    # 需要重新填充初始值以匹配新的 point_id
    pt_id = sp.points[0].point_id
    sp.initial_values = {pt_id: 0.0}
    result = validate_server_plan(sp)
    # 非 TCP 协议不检查 host/port，应通过
    assert result.is_valid, f"非 TCP 协议不应检查 port: {result.errors}"


def test_validate_server_plan_initial_values_orphan_warning() -> None:
    """initial_values 中 key 无法追溯到 points 中 point_id 时应产生警告。

    注意：不可追溯的 key 仅产生警告，不阻止校验通过。
    """
    sp = _make_valid_server_plan("v_orphan_iv")
    sp.initial_values = {"nonexistent_point": 42.0, sp.points[0].point_id: 0.0}
    result = validate_server_plan(sp)
    # 有孤儿 key，应有警告
    assert result.warnings, "应产生 initial_values 孤儿 key 警告"
    assert any("initial_values" in w.lower() for w in result.warnings)
    # 整体仍应通过（孤儿 key 不阻止校验）
    assert result.is_valid, f"校验应仍通过: {result.errors}"


def test_validate_server_plan_capability_write_conflict() -> None:
    """capabilities 未声明 WRITE 但 points 中有 WO/RW 点位时应产生警告。"""
    sp = _make_valid_server_plan("v_cap_conflict")
    sp.capabilities = ["READ"]  # 未声明 WRITE
    # 添加一个可写点位
    pt_id_w = f"{sp.scenario_id}_point_write"
    sp.points.append(
        ServerPointPlan(
            point_id=pt_id_w,
            point_name="WritePoint",
            access_mode="WO",
            node_key=f"ns=2;s={pt_id_w}",
            variable_key="Value",
            value_type="Float",
        )
    )
    sp.initial_values = {sp.points[0].point_id: 0.0}
    result = validate_server_plan(sp)
    # 应有警告
    assert result.warnings, "应产生 capabilities 冲突警告"
    assert any("WRITE" in w for w in result.warnings)


def test_validate_server_plan_missing_contract_fields_warning() -> None:
    """point 缺少 node_key/variable_key/value_type 时应产生警告。"""
    sp = _make_valid_server_plan("v_no_contract")
    sp.points[0].node_key = ""
    sp.points[0].variable_key = ""
    sp.points[0].value_type = ""
    sp.initial_values = {sp.points[0].point_id: 0.0}
    result = validate_server_plan(sp)
    assert any("node_key" in w.lower() or "variable_key" in w.lower()
               or "value_type" in w.lower() for w in result.warnings), \
        f"应产生契约字段缺失警告: {result.warnings}"


# ── ServerPlan handoff 导出 ─────────────────────────────────────────────────────


def test_export_server_plan_json_structure() -> None:
    """导出的 JSON 应包含 Starfish 契约必需字段。"""
    sp = _make_valid_server_plan("exp_struct")
    json_str = export_server_plan_to_json(sp)
    parsed = json.loads(json_str)

    required_fields = [
        "schema_version", "scenario_id", "generator_version",
        "generated_at", "synthetic", "server_name", "strategy_id",
        "endpoints", "points", "capabilities", "update_policy",
        "initial_values", "payload_hash",
    ]
    for field in required_fields:
        assert field in parsed, f"缺少字段: {field}"

    # 检查端点字段
    ep = parsed["endpoints"][0]
    for field in ("endpoint_id", "protocol", "host", "port"):
        assert field in ep, f"endpoint 缺少字段: {field}"

    # 检查点位字段
    pt = parsed["points"][0]
    for field in ("point_id", "node_key", "variable_key", "value_type", "access_mode"):
        assert field in pt, f"point 缺少字段: {field}"


def test_export_server_plan_payload_hash_stability() -> None:
    """相同 ServerPlan 的 payload_hash 应稳定一致。"""
    sp1 = _make_valid_server_plan("hash_stable")
    sp2 = _make_valid_server_plan("hash_stable")

    json_str1 = export_server_plan_to_json(sp1)
    json_str2 = export_server_plan_to_json(sp2)
    parsed1 = json.loads(json_str1)
    parsed2 = json.loads(json_str2)

    assert parsed1["payload_hash"] == parsed2["payload_hash"]
    assert len(parsed1["payload_hash"]) == 64  # SHA256 hex


def test_export_server_plan_payload_hash_differs() -> None:
    """不同内容的 ServerPlan 应产生不同 payload_hash。"""
    sp1 = _make_valid_server_plan("hash_diff_a")
    sp2 = _make_valid_server_plan("hash_diff_b")

    parsed1 = json.loads(export_server_plan_to_json(sp1))
    parsed2 = json.loads(export_server_plan_to_json(sp2))

    assert parsed1["payload_hash"] != parsed2["payload_hash"]


def test_build_server_plan_payload_has_empty_hash() -> None:
    """build_server_plan_payload 产出的 payload_hash 应为空字符串，
    由 export_server_plan_to_json 调用时填充。
    """
    sp = _make_valid_server_plan("payload_empty")
    payload = build_server_plan_payload(sp)
    assert payload["payload_hash"] == ""


def test_save_server_plan_atomic_write() -> None:
    """save_server_plan 应以原子方式创建 JSON 文件。"""
    sp = _make_valid_server_plan("atomic_save")
    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_server_plan(sp, tmpdir)
        assert path.exists()
        assert path.suffix == ".json"
        content = path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert parsed["scenario_id"] == "atomic_save"
        assert parsed["payload_hash"] != ""


def test_save_server_plan_creates_parent_dir() -> None:
    """save_server_plan 在父目录不存在时应自动创建。"""
    sp = _make_valid_server_plan("mkdir_sp")
    with tempfile.TemporaryDirectory() as tmpdir:
        nested = Path(tmpdir) / "deep" / "nested_sp"
        path = save_server_plan(sp, nested)
        assert path.exists()
        assert path.parent == nested


# ── ScenarioBundle -> ServerPlan handoff ────────────────────────────────────────


def test_bundle_to_server_plan_handoff_roundtrip() -> None:
    """从 ScenarioBundle 导出 ServerPlan 后应可反序列化并校验通过。"""
    config = ScenarioConfig(
        scenario_id="bundle_sp_rt",
        deterministic_seed=42,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=1.0,
        asset_count=1,
        protocol_targets=["OPC_UA"],
    )
    generator = SeahorseGenerator(config)
    seed_plan, server_plan, signals, alarms, controls = generator.generate()

    bundle = ScenarioBundle(
        schema_version="1.0.0",
        scenario_id="bundle_sp_rt",
        deterministic_seed=42,
        synthetic=True,
        scenario_config=config,
        scenario_metadata=generator.metadata,
        seed_plan=seed_plan,
        server_plan=server_plan,
        generated_timeseries_sample=signals,
        alarm_events=alarms,
        control_results=controls,
    )
    bundle.checksum = compute_bundle_checksum(bundle)

    # 从 bundle 导出 ServerPlan
    json_str = export_server_plan_from_bundle(bundle)
    parsed = json.loads(json_str)
    assert parsed["scenario_id"] == "bundle_sp_rt"
    assert parsed["payload_hash"] != ""

    # 从 dict 校验
    result = validate_server_plan_from_dict(parsed)
    assert result.is_valid, f"从 bundle 导出的 ServerPlan 校验失败: {result.errors}"


def test_save_server_plan_from_bundle() -> None:
    """save_server_plan_from_bundle 应正确保存文件。"""
    config = ScenarioConfig(
        scenario_id="save_bundle_sp",
        deterministic_seed=99,
        start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_seconds=1.0,
        asset_count=1,
        protocol_targets=["OPC_UA"],
    )
    generator = SeahorseGenerator(config)
    seed_plan, server_plan, signals, alarms, controls = generator.generate()

    bundle = ScenarioBundle(
        schema_version="1.0.0",
        scenario_id="save_bundle_sp",
        deterministic_seed=99,
        synthetic=True,
        scenario_config=config,
        scenario_metadata=generator.metadata,
        seed_plan=seed_plan,
        server_plan=server_plan,
        generated_timeseries_sample=signals,
        alarm_events=alarms,
        control_results=controls,
    )
    bundle.checksum = compute_bundle_checksum(bundle)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = save_server_plan_from_bundle(bundle, tmpdir)
        assert path.exists()
        assert "save_bundle_sp_server_plan.json" in str(path)


def test_export_from_bundle_none_server_plan_raises() -> None:
    """bundle.server_plan 为 None 时 export_server_plan_from_bundle 应抛出 ValueError。"""
    bundle = ScenarioBundle(scenario_id="no_sp_bundle")
    bundle.server_plan = None
    with pytest.raises(ValueError, match="server_plan"):
        export_server_plan_from_bundle(bundle)


# ── CLI export-server-plan smoke ────────────────────────────────────────────────


def test_cli_export_server_plan_help() -> None:
    """export-server-plan --help 应正常输出。"""
    from seahorse.__main__ import main
    with pytest.raises(SystemExit) as exc_info:
        main(["export-server-plan", "--help"])
    assert exc_info.value.code == 0


def test_cli_export_server_plan_from_bundle() -> None:
    """从已有 bundle 导出 ServerPlan 的 CLI 路径。"""
    from seahorse.__main__ import main

    with tempfile.TemporaryDirectory() as tmpdir:
        # 先生成 bundle
        rc = main([
            "generate-scenario",
            "--scenario-id", "cli_sp_bundle",
            "--seed", "42",
            "--asset-count", "1",
            "--duration", "0.5",
            "--output-dir", tmpdir,
            "--start-time", "2024-01-01T00:00:00+00:00",
        ])
        assert rc == 0

        bundle_path = Path(tmpdir) / "cli_sp_bundle_bundle.json"
        assert bundle_path.exists()

        # 从 bundle 导出 ServerPlan
        rc2 = main([
            "export-server-plan",
            "--input", str(bundle_path),
            "--output-dir", tmpdir,
        ])
        assert rc2 == 0, f"CLI export-server-plan 失败 (exit={rc2})"

        sp_path = Path(tmpdir) / "cli_sp_bundle_server_plan.json"
        assert sp_path.exists()
        content = json.loads(sp_path.read_text(encoding="utf-8"))
        assert content["scenario_id"] == "cli_sp_bundle"
        assert content["payload_hash"] != ""


def test_cli_export_server_plan_direct_generate() -> None:
    """直接通过参数生成 ServerPlan 的 CLI 路径。"""
    from seahorse.__main__ import main

    with tempfile.TemporaryDirectory() as tmpdir:
        rc = main([
            "export-server-plan",
            "--scenario-id", "cli_direct_sp",
            "--seed", "77",
            "--asset-count", "2",
            "--protocol-targets", "OPC_UA", "MODBUS_TCP",
            "--output-dir", tmpdir,
        ])
        assert rc == 0, f"CLI direct generate export-server-plan 失败 (exit={rc})"

        sp_path = Path(tmpdir) / "cli_direct_sp_server_plan.json"
        assert sp_path.exists()
        content = json.loads(sp_path.read_text(encoding="utf-8"))
        assert content["scenario_id"] == "cli_direct_sp"
        assert len(content["endpoints"]) == 2
        assert "payload_hash" in content


def test_cli_export_server_plan_no_input_no_scenario_id() -> None:
    """既未指定 --input 也未指定 --scenario-id 时应失败。"""
    from seahorse.__main__ import main
    rc = main([
        "export-server-plan",
        "--output-dir", "/tmp",
    ])
    assert rc != 0


def test_cli_export_server_plan_missing_input_file() -> None:
    """指定不存在的 --input 文件时应返回非零。"""
    from seahorse.__main__ import main
    rc = main([
        "export-server-plan",
        "--input", "/nonexistent/bundle.json",
        "--output-dir", "/tmp",
    ])
    assert rc != 0


# ── validate_server_plan_from_dict ─────────────────────────────────────────────


def test_validate_server_plan_from_dict_valid() -> None:
    """通过有效的 ServerPlan dict 应校验通过。"""
    sp = _make_valid_server_plan("vfd_valid")
    payload = build_server_plan_payload(sp)
    payload["payload_hash"] = ""  # hash 由 export 函数填充，validate 不检查
    result = validate_server_plan_from_dict(payload)
    assert result.is_valid, f"校验失败: {result.errors}"


def test_validate_server_plan_from_dict_missing_scenario_id() -> None:
    """dict 缺少 scenario_id 应报错。"""
    result = validate_server_plan_from_dict({"scenario_id": ""})
    assert not result.is_valid
    assert any("scenario_id" in e for e in result.errors)


def test_validate_server_plan_from_dict_empty_endpoints() -> None:
    """dict 中 endpoints 为空应报错。"""
    result = validate_server_plan_from_dict({
        "scenario_id": "test",
        "synthetic": True,
        "endpoints": [],
        "points": [{"point_id": "p1", "value_type": "Float"}],
    })
    assert not result.is_valid
    assert any("endpoints" in e.lower() for e in result.errors)


def test_validate_server_plan_from_dict_empty_points() -> None:
    """dict 中 points 为空应报错。"""
    result = validate_server_plan_from_dict({
        "scenario_id": "test",
        "synthetic": True,
        "endpoints": [{"endpoint_id": "ep1", "protocol": "OPC_UA"}],
        "points": [],
    })
    assert not result.is_valid
    assert any("points" in e.lower() for e in result.errors)


def test_validate_server_plan_from_dict_orphan_initial_values() -> None:
    """dict 中 initial_values 有孤儿 key 应产生警告。"""
    result = validate_server_plan_from_dict({
        "scenario_id": "test",
        "synthetic": True,
        "endpoints": [{
            "endpoint_id": "ep1",
            "protocol": "OPC_UA",
            "host": "127.0.0.1",
            "port": 4840,
        }],
        "points": [{"point_id": "p1", "value_type": "Float"}],
        "initial_values": {"p1": 0.0, "orphan": 99.0},
    })
    assert result.warnings
    assert any("initial_values" in w.lower() for w in result.warnings)
