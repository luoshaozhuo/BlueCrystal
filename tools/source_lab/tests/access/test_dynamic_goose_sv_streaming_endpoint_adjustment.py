"""GOOSE/SV streaming endpoint 动态调整测试。

验证 GOOSE/SV endpoint 在 runtime 的创建、修改和移除行为。
测试阶段：开发期验证 (contract)。
"""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import cast

import pytest
from tools.source_lab.access.runtime import ContinuityMonitor, EndpointRuntimeRegistry
from tools.source_lab.fleet import SourceSimulatorFleet
from tools.source_lab.model import SimulatedSource, UpdateConfig
from tools.source_lab.tests.access._dynamic_runtime_test_utils import (
    build_goose_source,
    build_native_registry,
    build_sv_source,
    shutdown_registry,
    streaming_config,
)

pytestmark = [
    pytest.mark.requires_raw_socket,
    pytest.mark.requires_cap_net_raw,
    pytest.mark.requires_root_or_cap_net_raw,
]


def _l2_runtime_status(protocol: str) -> tuple[bool, str | None]:
    build_dir = Path(__file__).resolve().parents[2] / "native" / "build"
    names = {
        "iec61850_goose": ("iec61850_goose_publisher_simulator", "iec61850_goose_subscriber_runner"),
        "iec61850_sv": ("iec61850_sv_publisher_simulator", "iec61850_sv_subscriber_runner"),
    }[protocol]
    missing = [str(build_dir / name) for name in names if not (build_dir / name).exists()]
    if missing:
        return False, "dependency_missing: " + ",".join(missing)
    if os.geteuid() == 0:
        return True, None
    try:
        for line in Path("/proc/self/status").read_text(encoding="utf-8").splitlines():
            if line.startswith("CapEff:"):
                value = int(line.split(":", 1)[1].strip(), 16)
                if value & (1 << 13):
                    return True, None
                break
    except OSError:
        pass
    if _executables_have_cap_net_raw(tuple(build_dir / name for name in names)):
        return True, None
    interface = os.environ.get("SOURCE_LAB_L2_INTERFACE", "lo")
    return False, (
        "SKIPPED_ENV_PERMISSION: raw_socket_permission_missing: "
        f"protocol={protocol} interface={interface}"
    )


def _executables_have_cap_net_raw(paths: tuple[Path, ...]) -> bool:
    for path in paths:
        try:
            result = subprocess.run(
                ["getcap", str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
        except OSError:
            return False
        if result.returncode != 0 or "cap_net_raw=ep" not in result.stdout:
            return False
    return True


def _require_l2_runtime(protocol: str) -> None:
    allowed, reason = _l2_runtime_status(protocol)
    if not allowed:
        pytest.skip(reason or "SKIPPED_ENV_PERMISSION: raw_socket_permission_missing")


def _run_streaming_isolation_test(
    tmp_path: Path, protocol: str
) -> tuple[EndpointRuntimeRegistry, ContinuityMonitor, SourceSimulatorFleet, tuple[SimulatedSource, ...]]:
    if protocol == "iec61850_goose":
        sources = tuple(build_goose_source(index, 1000 + index) for index in range(3))
    else:
        sources = tuple(build_sv_source(index, 4000 + index) for index in range(3))
    registry, monitor = build_native_registry(tmp_path)
    fleet = SourceSimulatorFleet.create(sources, update_config=UpdateConfig(enabled=True, interval_seconds=0.1))
    return registry, monitor, fleet, sources


def _wait_for_event_growth(monitor: ContinuityMonitor, endpoint_id: str, *, baseline_events: int, timeout_s: float = 6.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        current = monitor.snapshot()[endpoint_id]
        if current.endpoint_event_count > baseline_events or current.endpoint_sample_count > baseline_events:
            return
        time.sleep(0.1)
    raise AssertionError(f"event/sample did not grow for {endpoint_id}")


def test_dynamic_goose_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_goose")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_goose")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=before[source.connection.name].endpoint_event_count,
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            metrics = after[source.connection.name]
            prev = before[source.connection.name]
            assert metrics.endpoint_event_count > prev.endpoint_event_count
            assert metrics.endpoint_stream_restart_count == prev.endpoint_stream_restart_count
            assert metrics.endpoint_callback_gap_count <= prev.endpoint_callback_gap_count + 1
            assert metrics.endpoint_callback_max_gap_ms <= 2500.0
            assert metrics.stagger_offset_changed is False
        journal = registry._state_store.load_journal_entries()
        assert any(
            entry.get("action") == "STOP_ENDPOINT"
            and sources[0].connection.name in cast(list[str], entry.get("affected_endpoints", []))
            and sources[1].connection.name in cast(list[str], entry.get("unaffected_endpoints", []))
            for entry in journal
        )
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_goose_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_goose")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_goose")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(1.0)
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=before[source.connection.name].endpoint_event_count,
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_goose_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_goose")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_goose")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        target = sources[0].connection.name
        config = registry.get_config(target)
        assert config is not None, f"config not found for {target}"
        expected_version = config.config_version
        assert registry.update_endpoint(
            target,
            {"params": {"publish_interval_ms": 1200}},
            expected_version,
        ).result == "SUCCESS"
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=before[source.connection.name].endpoint_event_count,
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            assert after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
            assert after[source.connection.name].endpoint_stream_restart_count == before[source.connection.name].endpoint_stream_restart_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_sv_stop_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_sv")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_sv")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        assert registry.stop_endpoint(sources[0].connection.name).result == "SUCCESS"
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=max(
                    before[source.connection.name].endpoint_event_count,
                    before[source.connection.name].endpoint_sample_count,
                ),
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            metrics = after[source.connection.name]
            prev = before[source.connection.name]
            assert metrics.endpoint_sample_count > prev.endpoint_sample_count or metrics.endpoint_event_count > prev.endpoint_event_count
            assert metrics.endpoint_stream_restart_count == prev.endpoint_stream_restart_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_sv_pause_one_app_id_keeps_other_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_sv")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_sv")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        assert registry.pause_endpoint(sources[0].connection.name).result == "SUCCESS"
        time.sleep(1.0)
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=max(
                    before[source.connection.name].endpoint_event_count,
                    before[source.connection.name].endpoint_sample_count,
                ),
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            assert after[source.connection.name].endpoint_sample_count > before[source.connection.name].endpoint_sample_count or after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_sv_replace_params_keeps_unaffected_app_id_receiving_when_raw_socket_allowed(tmp_path: Path) -> None:
    _require_l2_runtime("iec61850_sv")
    registry, monitor, fleet, sources = _run_streaming_isolation_test(tmp_path, "iec61850_sv")
    try:
        fleet.start()
        for source in sources:
            assert registry.add_endpoint(streaming_config(source)).result == "SUCCESS"
        time.sleep(3.0)
        before = monitor.snapshot()
        target = sources[0].connection.name
        config = registry.get_config(target)
        assert config is not None, f"config not found for {target}"
        expected_version = config.config_version
        assert registry.update_endpoint(
            target,
            {"params": {"sample_rate_hz": 2}},
            expected_version,
        ).result == "SUCCESS"
        for source in sources[1:]:
            _wait_for_event_growth(
                monitor,
                source.connection.name,
                baseline_events=max(
                    before[source.connection.name].endpoint_event_count,
                    before[source.connection.name].endpoint_sample_count,
                ),
            )
        after = monitor.snapshot()
        for source in sources[1:]:
            assert after[source.connection.name].endpoint_sample_count > before[source.connection.name].endpoint_sample_count or after[source.connection.name].endpoint_event_count > before[source.connection.name].endpoint_event_count
    finally:
        shutdown_registry(registry)
        fleet.stop()


def test_dynamic_goose_sv_permission_skip_reason_is_explicit() -> None:
    for protocol in ("iec61850_goose", "iec61850_sv"):
        allowed, reason = _l2_runtime_status(protocol)
        if allowed:
            assert reason is None
            continue
        assert reason is not None
        assert "raw_socket_permission_missing" in reason or "dependency_missing" in reason
        assert reason.startswith(("SKIPPED_ENV_PERMISSION:", "dependency_missing:"))
