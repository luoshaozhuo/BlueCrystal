"""dynamic endpoint PATCH 操作矩阵测试。

验证 endpoint 各属性组合的 PATCH 请求结果。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path

from tools.source_lab.access.runtime.continuity_model import EndpointContinuityMetrics
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import UpdateConfig
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_http_source,
    build_native_registry,
    build_opcua_source,
    build_registry,
    choose_port,
    polling_config,
    runtime_spec,
    shutdown_registry,
    subscribe_config,
)


def _assert_unaffected_stable(
    before: Mapping[str, EndpointContinuityMetrics],
    after: Mapping[str, EndpointContinuityMetrics],
    endpoint_id: str,
) -> None:
    before_metrics = before[endpoint_id]
    after_metrics = after[endpoint_id]
    assert after_metrics.endpoint_restart_count == before_metrics.endpoint_restart_count
    assert after_metrics.endpoint_config_version == before_metrics.endpoint_config_version
    assert after_metrics.stagger_offset_ns == before_metrics.stagger_offset_ns
    assert after_metrics.stagger_offset_changed is False
    assert after_metrics.unaffected_endpoint_continuity_breaks == 0


def test_dynamic_patch_points_only_replaces_target_endpoint(tmp_path: Path) -> None:
    sources = tuple(build_http_source(index, choose_port()) for index in range(3))
    registry, monitor = build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=6.0)).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        updated_points = runtime_spec(sources[0]).points[:1]
        result = registry.replace_points(sources[0].connection.name, updated_points, expected_version=1)
        assert result.result == "SUCCESS"
        time.sleep(0.6)
        after = monitor.snapshot()

        assert after[sources[0].connection.name].endpoint_config_version == 2
        for source in sources[1:]:
            _assert_unaffected_stable(before, after, source.connection.name)
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_patch_host_port_replaces_target_endpoint(tmp_path: Path) -> None:
    sources = tuple(build_http_source(index, choose_port()) for index in range(3))
    registry, monitor = build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=6.0)).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        replacement_port = choose_port()
        replacement_source = build_http_source(99, replacement_port)
        replacement_fleet = SourceSimulatorFleet.create((replacement_source,), update_config=UpdateConfig(enabled=False))
        replacement_fleet.start_source(0)
        try:
            result = registry.update_endpoint(
                sources[0].connection.name,
                {"host": "127.0.0.1", "port": replacement_port},
                expected_version=1,
            )
            assert result.result == "SUCCESS"
            entries = registry._state_store.load_journal_entries()
            assert entries[-1]["changed_fields"] == ["host", "port"]
            time.sleep(0.6)
            after = monitor.snapshot()

            assert after[sources[0].connection.name].endpoint_config_version == 2
            for source in sources[1:]:
                _assert_unaffected_stable(before, after, source.connection.name)
                assert after[source.connection.name].endpoint_actual_samples > before[source.connection.name].endpoint_actual_samples
        finally:
            replacement_fleet.stop()
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_patch_protocol_params_replaces_target_endpoint(tmp_path: Path) -> None:
    sources = tuple(build_http_source(index, choose_port()) for index in range(3))
    registry, monitor = build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=6.0)).result == "SUCCESS"
        time.sleep(0.8)
        before = monitor.snapshot()

        result = registry.update_endpoint(
            sources[0].connection.name,
            {"params": {"http_path": "/points", "batch_size": 4}},
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        entries = registry._state_store.load_journal_entries()
        assert entries[-1]["changed_fields"] == ["protocol_params"]
        time.sleep(0.6)
        after = monitor.snapshot()

        assert after[sources[0].connection.name].endpoint_config_version == 2
        for source in sources[1:]:
            _assert_unaffected_stable(before, after, source.connection.name)
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_patch_mode_change_replaces_target_endpoint(tmp_path: Path) -> None:
    sources = tuple(build_opcua_source(index, choose_port(45001, 47000)) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(polling_config(source, hz=2.0)).result == "SUCCESS"
        time.sleep(1.2)
        before = monitor.snapshot()

        result = registry.update_endpoint(
            sources[0].connection.name,
            {"mode": "subscribe", "publishing_interval_ms": 200.0},
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        entries = registry._state_store.load_journal_entries()
        assert entries[-1]["changed_fields"] == ["mode", "publishing_interval_ms"]
        time.sleep(1.0)
        after = monitor.snapshot()

        assert after[sources[0].connection.name].endpoint_config_version == 2
        for source in sources[1:]:
            _assert_unaffected_stable(before, after, source.connection.name)
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_patch_protocol_change_replaces_target_endpoint_or_returns_validation_error(
    tmp_path: Path,
) -> None:
    source = build_http_source(10, choose_port())
    registry, _monitor = build_registry(tmp_path)
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=False))
    try:
        fleet.start()
        assert registry.add_endpoint(polling_config(source)).result == "SUCCESS"
        result = registry.update_endpoint(source.connection.name, {"protocol": "mqtt"}, expected_version=1)
        assert result.result == "VALIDATION_ERROR"
        assert result.reason_code == "unsupported_protocol_change"
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_patch_security_params_redacts_sensitive_values_in_journal(tmp_path: Path) -> None:
    source = build_opcua_source(11, choose_port(47001, 48000))
    registry, _monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create((source,), update_config=UpdateConfig(enabled=True, interval_seconds=0.2))
    try:
        fleet.start()
        assert registry.add_endpoint(subscribe_config(source)).result == "SUCCESS"
        result = registry.update_endpoint(
            source.connection.name,
            {
                "params": {"security_policy": "Basic256Sha256"},
                "security_params": {"username": "alice", "password": "secret-pass", "token": "abc"},
            },
            expected_version=1,
        )
        assert result.result == "SUCCESS"
        entry = registry._state_store.load_journal_entries()[-1]
        assert entry["changed_fields"] == ["protocol_params", "security_params"]
        journal_text = (tmp_path / "runtime" / "operation_journal.jsonl").read_text(encoding="utf-8")
        assert "secret-pass" not in journal_text
        assert "\"alice\"" not in journal_text
        assert "\"abc\"" not in journal_text
        accepted_text = (tmp_path / "runtime" / "accepted_endpoints.json").read_text(encoding="utf-8")
        assert "***REDACTED***" in accepted_text
    finally:
        shutdown_registry(registry)
        fleet.stop()
