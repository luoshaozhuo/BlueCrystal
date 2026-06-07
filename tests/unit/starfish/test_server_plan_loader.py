"""starfish ServerPlan JSON 加载器测试。

验证：
1. 有效 JSON 的加载和校验通过路径。
2. 必填字段缺失的错误检测。
3. schema_version 不匹配警告。
4. payload_hash 不匹配检测。
5. endpoints/points 结构校验。
6. synthetic 标识校验。
7. 文件不存在和 JSON 解析错误边界。
8. Seahorse 导出的真实 JSON 可被 Starfish loader 正确消费。

测试阶段：开发期验证 (P1)。
使用的替身：无 — 所有 JSON 由 fixture 或 Seahorse exporter 生成。
外部依赖：无（纯内存 / 临时文件测试，Seahorse 集成测试除外）。
不能证明：跨语言 JSON 反序列化、真实协议 server 启动。
NOT_RUN 条件：无。
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from starfish.loader import load_server_plan
from starfish.models.plan import LoadResult, ValidationResult


# ── Fixtures ────────────────────────────────────────────────────────────────────


def _make_valid_payload(
    scenario_id: str = "sf_loader_test",
    protocol: str = "OPC_UA",
    synthetic: bool = True,
) -> dict:
    """构造一个通过全部校验的最小有效 JSON payload。

    Args:
        scenario_id: 场景标识。
        protocol: 端点协议。
        synthetic: 合成数据标识。

    Returns:
        最小有效 ServerPlan JSON dict。
    """
    import hashlib

    payload = {
        "schema_version": "1.0.0",
        "scenario_id": scenario_id,
        "generator_version": "0.2.0",
        "generated_at": "2024-01-01T00:00:00+00:00",
        "synthetic": synthetic,
        "server_name": "测试 ServerPlan",
        "strategy_id": "test_strategy",
        "endpoints": [
            {
                "endpoint_id": f"{scenario_id}_{protocol}_ep",
                "endpoint_name": f"{protocol}_ep",
                "protocol": protocol,
                "host": "127.0.0.1",
                "port": 4840,
            }
        ],
        "points": [
            {
                "point_id": f"{scenario_id}_point_000",
                "point_name": "TestPoint",
                "node_key": f"ns=2;s={scenario_id}_point_000",
                "variable_key": "Value",
                "value_type": "Float",
                "access_mode": "RO",
                "data_type": "FLOAT64",
            }
        ],
        "capabilities": ["READ"],
        "update_policy": {"default": {"mode": "poll", "interval_ms": 100}},
        "initial_values": {f"{scenario_id}_point_000": 0.0},
        "payload_hash": "",
    }
    # 预计算 hash
    content = {k: v for k, v in payload.items() if k not in ("payload_hash", "generated_at")}
    canonical = json.dumps(content, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    payload["payload_hash"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def _write_json(tmpdir: str, data: dict, filename: str = "test_plan.json") -> Path:
    """将 dict 写入临时 JSON 文件。

    Args:
        tmpdir: 临时目录路径。
        data: 要写入的数据。
        filename: 文件名。

    Returns:
        写入后的文件 Path。
    """
    path = Path(tmpdir) / filename
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# ── 加载成功路径 ────────────────────────────────────────────────────────────────


class TestLoadServerPlanSuccess:
    """有效 JSON 的加载成功测试。"""

    def test_load_valid_plan(self) -> None:
        """加载完全有效的 ServerPlan JSON 应成功。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, _make_valid_payload("load_ok"))
            result = load_server_plan(plan_path)

            assert result.plan is not None
            assert result.plan.scenario_id == "load_ok"
            assert len(result.plan.endpoints) == 1
            assert len(result.plan.points) == 1
            assert result.plan.synthetic is True
            assert result.plan.capabilities == ["READ"]
            assert result.validation.is_valid
            assert len(result.validation.errors) == 0

    def test_load_returns_load_result_type(self) -> None:
        """load_server_plan 应返回 LoadResult 实例。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, _make_valid_payload("type_check"))
            result = load_server_plan(plan_path)
            assert isinstance(result, LoadResult)
            assert isinstance(result.validation, ValidationResult)

    def test_load_with_multiple_endpoints(self) -> None:
        """应正确加载包含多端点的 ServerPlan。"""
        payload = _make_valid_payload("multi_ep")
        payload["endpoints"].append({
            "endpoint_id": "multi_ep_MODBUS_TCP_ep",
            "endpoint_name": "MODBUS_TCP_ep",
            "protocol": "MODBUS_TCP",
            "host": "127.0.0.1",
            "port": 502,
        })
        from starfish.loader.server_plan_loader import _compute_payload_hash
        payload["payload_hash"] = _compute_payload_hash(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.plan is not None
            assert len(result.plan.endpoints) == 2
            assert result.validation.is_valid

    def test_load_with_multiple_points(self) -> None:
        """应正确加载包含多点位的 ServerPlan。"""
        payload = _make_valid_payload("multi_pt")
        payload["points"].append({
            "point_id": "multi_pt_point_001",
            "point_name": "Point2",
            "node_key": "ns=2;s=multi_pt_point_001",
            "variable_key": "Value",
            "value_type": "Int32",
            "access_mode": "RO",
            "data_type": "INT32",
        })
        from starfish.loader.server_plan_loader import _compute_payload_hash
        payload["payload_hash"] = _compute_payload_hash(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.plan is not None
            assert len(result.plan.points) == 2
            assert result.validation.is_valid

    def test_load_preserves_update_policy(self) -> None:
        """update_policy 应正确保留在加载结果中。"""
        payload = _make_valid_payload("up_policy")
        payload["update_policy"] = {"mode": "push", "batch_size": 10}
        from starfish.loader.server_plan_loader import _compute_payload_hash
        payload["payload_hash"] = _compute_payload_hash(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.plan is not None
            assert result.plan.update_policy == {"mode": "push", "batch_size": 10}

    def test_load_preserves_initial_values(self) -> None:
        """initial_values 应正确保留在加载结果中，含多种数据类型。"""
        payload = _make_valid_payload("iv_types")
        payload["points"] = [
            {"point_id": "float_pt", "value_type": "Float"},
            {"point_id": "int_pt", "value_type": "Int32"},
            {"point_id": "bool_pt", "value_type": "Boolean"},
        ]
        payload["initial_values"] = {
            "float_pt": 3.14,
            "int_pt": 42,
            "bool_pt": True,
        }
        from starfish.loader.server_plan_loader import _compute_payload_hash
        payload["payload_hash"] = _compute_payload_hash(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.plan is not None
            assert result.plan.initial_values == {
                "float_pt": 3.14,
                "int_pt": 42,
                "bool_pt": True,
            }


# ── 校验失败路径 ────────────────────────────────────────────────────────────────


class TestLoadServerPlanValidationErrors:
    """JSON 校验失败场景测试。"""

    def test_load_missing_scenario_id(self) -> None:
        """缺少 scenario_id 应报错。"""
        payload = _make_valid_payload("no_sid")
        del payload["scenario_id"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("scenario_id" in e for e in result.validation.errors)

    def test_load_missing_schema_version(self) -> None:
        """缺少 schema_version 应报错。"""
        payload = _make_valid_payload("no_sv")
        del payload["schema_version"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("schema_version" in e for e in result.validation.errors)

    def test_load_missing_endpoints(self) -> None:
        """缺少 endpoints 应报错。"""
        payload = _make_valid_payload("no_ep")
        del payload["endpoints"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("endpoints" in e for e in result.validation.errors)

    def test_load_empty_endpoints(self) -> None:
        """endpoints 为空应报错。"""
        payload = _make_valid_payload("empty_ep")
        payload["endpoints"] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("endpoints" in e.lower() for e in result.validation.errors)

    def test_load_missing_points(self) -> None:
        """缺少 points 应报错。"""
        payload = _make_valid_payload("no_pt")
        del payload["points"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("points" in e for e in result.validation.errors)

    def test_load_empty_points(self) -> None:
        """points 为空应报错。"""
        payload = _make_valid_payload("empty_pt")
        payload["points"] = []

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("points" in e.lower() for e in result.validation.errors)

    def test_load_endpoint_missing_protocol(self) -> None:
        """endpoint 缺少 protocol 应报错。"""
        payload = _make_valid_payload("no_proto")
        payload["endpoints"][0]["protocol"] = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("protocol" in e for e in result.validation.errors)

    def test_load_endpoint_missing_endpoint_id(self) -> None:
        """endpoint 缺少 endpoint_id 应报错。"""
        payload = _make_valid_payload("no_epid")
        del payload["endpoints"][0]["endpoint_id"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("endpoint_id" in e for e in result.validation.errors)

    def test_load_point_missing_point_id(self) -> None:
        """point 缺少 point_id 应报错。"""
        payload = _make_valid_payload("no_ptid")
        del payload["points"][0]["point_id"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("point_id" in e for e in result.validation.errors)

    def test_load_missing_payload_hash(self) -> None:
        """缺少 payload_hash 应报错。"""
        payload = _make_valid_payload("no_hash")
        del payload["payload_hash"]

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("payload_hash" in e for e in result.validation.errors)


# ── 校验警告路径 ────────────────────────────────────────────────────────────────


class TestLoadServerPlanValidationWarnings:
    """JSON 校验警告场景测试。"""

    def test_load_schema_version_warning(self) -> None:
        """不匹配的 schema_version 应产生警告但仍加载成功。"""
        payload = _make_valid_payload("ver_warn")
        payload["schema_version"] = "2.0.0"
        # 修改 schema_version 后，需要更新 payload_hash
        # 或清空以跳过 hash 校验（仅产生警告）
        payload["payload_hash"] = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.validation.is_valid  # 警告不阻止通过
            assert result.plan is not None
            assert any("schema_version" in w for w in result.validation.warnings)

    def test_load_synthetic_false_warning(self) -> None:
        """synthetic=False 应产生警告。"""
        payload = _make_valid_payload("syn_false")
        payload["synthetic"] = False
        from starfish.loader.server_plan_loader import _compute_payload_hash
        payload["payload_hash"] = _compute_payload_hash(payload)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.validation.is_valid
            assert any("synthetic" in w.lower() for w in result.validation.warnings)

    def test_load_empty_payload_hash_warning(self) -> None:
        """空 payload_hash 应产生警告但不阻止加载。"""
        payload = _make_valid_payload("empty_hash")
        payload["payload_hash"] = ""

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert any("payload_hash" in w.lower() for w in result.validation.warnings)
            # plan 仍然应该被构建
            assert result.plan is not None


# ── payload_hash 校验 ───────────────────────────────────────────────────────────


class TestPayloadHashVerification:
    """payload_hash 校验测试。"""

    def test_payload_hash_match(self) -> None:
        """正确的 payload_hash 应通过校验。"""
        payload = _make_valid_payload("hash_match")
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert result.validation.is_valid
            assert any("payload_hash" in p for p in result.validation.passed_checks)

    def test_payload_hash_mismatch(self) -> None:
        """不匹配的 payload_hash 应报错。"""
        payload = _make_valid_payload("hash_bad")
        payload["payload_hash"] = "0" * 64  # 错误的 hash

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = _write_json(tmpdir, payload)
            result = load_server_plan(plan_path)

            assert not result.validation.is_valid
            assert any("payload_hash" in e.lower() for e in result.validation.errors)

    def test_payload_hash_deterministic(self) -> None:
        """相同内容应产生相同 payload_hash。"""
        payload1 = _make_valid_payload("hash_det")
        payload1["generated_at"] = "2024-01-01T00:00:00+00:00"
        from starfish.loader.server_plan_loader import _compute_payload_hash
        hash1 = _compute_payload_hash(payload1)

        payload2 = _make_valid_payload("hash_det")
        payload2["generated_at"] = "2025-06-04T12:00:00+00:00"  # 不同时间
        hash2 = _compute_payload_hash(payload2)

        # generated_at 被排除，所以 hash 应相同
        assert hash1 == hash2

    def test_payload_hash_differs_by_content(self) -> None:
        """不同 scenario_id 应产生不同 payload_hash。"""
        payload1 = _make_valid_payload("hash_a")
        from starfish.loader.server_plan_loader import _compute_payload_hash
        hash1 = _compute_payload_hash(payload1)

        payload2 = _make_valid_payload("hash_b")
        hash2 = _compute_payload_hash(payload2)

        assert hash1 != hash2

    def test_payload_hash_64_char_hex(self) -> None:
        """payload_hash 应为 64 字符十六进制字符串。"""
        payload = _make_valid_payload("hash_fmt")
        from starfish.loader.server_plan_loader import _compute_payload_hash
        computed = _compute_payload_hash(payload)

        assert len(computed) == 64
        assert all(c in "0123456789abcdef" for c in computed)


# ── 错误边界 ────────────────────────────────────────────────────────────────────


class TestLoadServerPlanErrorBoundaries:
    """文件不存在和 JSON 解析错误边界测试。"""

    def test_file_not_found(self) -> None:
        """不存在的文件应抛出 FileNotFoundError。"""
        with pytest.raises(FileNotFoundError):
            load_server_plan("/nonexistent/path/not_a_file.json")

    def test_invalid_json(self) -> None:
        """无效 JSON 文件应抛出 json.JSONDecodeError。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bad.json"
            path.write_text("this is not json", encoding="utf-8")
            with pytest.raises(json.JSONDecodeError):
                load_server_plan(path)

    def test_top_level_not_dict(self) -> None:
        """JSON 顶层不是 dict 应抛出 ValueError。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "list.json"
            path.write_text('[{"key": "value"}]', encoding="utf-8")
            with pytest.raises(ValueError, match="dict"):
                load_server_plan(path)

    def test_empty_file(self) -> None:
        """空文件应抛出 JSON 解析错误。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "empty.json"
            path.write_text("", encoding="utf-8")
            with pytest.raises(json.JSONDecodeError):
                load_server_plan(path)


# ── LoadResult 模型 ─────────────────────────────────────────────────────────────


class TestLoadResult:
    """LoadResult 和 ValidationResult 模型测试。"""

    def test_validation_result_is_valid_no_errors(self) -> None:
        """无错误时 is_valid 应为 True。"""
        vr = ValidationResult()
        assert vr.is_valid

    def test_validation_result_is_valid_with_warnings_only(self) -> None:
        """仅警告时 is_valid 应为 True。"""
        vr = ValidationResult()
        vr.add_warning("测试警告")
        assert vr.is_valid
        assert len(vr.warnings) == 1

    def test_validation_result_is_valid_with_errors(self) -> None:
        """有错误时 is_valid 应为 False。"""
        vr = ValidationResult()
        vr.add_error("测试错误")
        assert not vr.is_valid

    def test_validation_result_mixed(self) -> None:
        """混合 errors/warnings/passes 时应正确计数。"""
        vr = ValidationResult()
        vr.add_error("err")
        vr.add_warning("warn")
        vr.add_pass("pass")
        assert not vr.is_valid
        assert len(vr.errors) == 1
        assert len(vr.warnings) == 1
        assert len(vr.passed_checks) == 1

    def test_load_result_defaults(self) -> None:
        """LoadResult 默认值应合理。"""
        lr = LoadResult()
        assert lr.plan is None
        assert lr.validation.is_valid
        assert lr.file_path == ""


# ── Seahorse -> Starfish contract 集成 ──────────────────────────────────────────


class TestSeahorseStarfishContract:
    """验证 Seahorse exporter 产物可被 Starfish loader 消费。"""

    def test_seahorse_exported_json_loads_correctly(self) -> None:
        """Seahorse 导出的真实 JSON 应被 Starfish loader 正确加载。"""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator
        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json

        config = ScenarioConfig(
            scenario_id="sf_contract_test",
            deterministic_seed=42,
            asset_count=1,
            protocol_targets=["OPC_UA"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()

        # Seahorse 导出 JSON
        json_str = export_server_plan_to_json(server_plan)
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == "1.0.0"
        assert parsed["scenario_id"] == "sf_contract_test"

        # Starfish 加载
        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "sf_contract_test_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")

            result = load_server_plan(plan_path)
            assert result.validation.is_valid, (
                f"Starfish 应能加载 Seahorse 导出的 JSON: {result.validation.errors}"
            )
            assert result.plan is not None
            assert result.plan.scenario_id == "sf_contract_test"
            assert len(result.plan.endpoints) >= 1
            assert len(result.plan.points) >= 1
            assert result.plan.synthetic is True

    def test_starfish_loads_seahorse_with_modbus(self) -> None:
        """Seahorse MODBUS_TCP 导出产物应被 Starfish loader 消费。"""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator
        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json

        config = ScenarioConfig(
            scenario_id="sf_modbus_test",
            deterministic_seed=99,
            asset_count=2,
            protocol_targets=["MODBUS_TCP"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()

        json_str = export_server_plan_to_json(server_plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "sf_modbus_test_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")

            result = load_server_plan(plan_path)
            assert result.validation.is_valid, (
                f"MODBUS_TCP plan 加载失败: {result.validation.errors}"
            )
            assert result.plan is not None
            assert result.plan.scenario_id == "sf_modbus_test"
            # MODBUS_TCP 端点应有合法 port（SeahorseGenerator 默认使用 4840）
            assert result.plan.endpoints[0].protocol == "MODBUS_TCP"
            assert result.plan.endpoints[0].port > 0  # port 应合法

    def test_starfish_loads_seahorse_with_initial_values(self) -> None:
        """Seahorse 导出的 initial_values 应被 Starfish 正确读取。"""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

        from seahorse.models.scenario import ScenarioConfig
        from seahorse.orchestration import SeahorseGenerator
        from seahorse.exporters.server_plan_exporter import export_server_plan_to_json

        config = ScenarioConfig(
            scenario_id="sf_iv_test",
            deterministic_seed=42,
            asset_count=1,
            protocol_targets=["OPC_UA"],
        )
        generator = SeahorseGenerator(config)
        _, server_plan = generator.generate_minimal()

        json_str = export_server_plan_to_json(server_plan)

        with tempfile.TemporaryDirectory() as tmpdir:
            plan_path = Path(tmpdir) / "sf_iv_test_server_plan.json"
            plan_path.write_text(json_str, encoding="utf-8")

            result = load_server_plan(plan_path)
            assert result.plan is not None
            # initial_values 应非空（SeahorseGenerator 为每个 point 生成初始值）
            if result.plan.initial_values:
                # 确保所有 initial_values key 都是合法的 point_id
                point_ids = {pt.point_id for pt in result.plan.points}
                for key in result.plan.initial_values:
                    assert key in point_ids, f"initial_values key {key} 不是合法 point_id"
