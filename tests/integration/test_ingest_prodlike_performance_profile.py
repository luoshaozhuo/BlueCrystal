"""Performance profile conformance tests for ingest runtime."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from whale.ingest.runtime.scheduler_settings import SchedulerSettings


@pytest.fixture
def perf_config() -> dict:
    path = Path("config/ingest/performance.prodlike.yaml")
    if not path.exists():
        path = Path(__file__).parents[2] / "config" / "ingest" / "performance.prodlike.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "performance config must be a YAML dict"
    return data


class TestPerformanceProfileConformance:

    @pytest.mark.integration
    def test_config_has_required_sections(self, perf_config: dict) -> None:
        assert "baseline" in perf_config, "Missing 'baseline' section"
        assert "limits" in perf_config, "Missing 'limits' section"
        assert "scheduler" in perf_config, "Missing 'scheduler' section"

    @pytest.mark.integration
    def test_baseline_throughput_targets_positive(self, perf_config: dict) -> None:
        bt = perf_config["baseline"]["throughput"]
        for key in ("jobs_per_second", "events_per_second", "bundle_imports_per_second"):
            val = bt[key]
            assert isinstance(val, (int, float)) and val > 0, f"{key} must be positive, got {val}"

    @pytest.mark.integration
    def test_baseline_latency_thresholds_positive(self, perf_config: dict) -> None:
        lat = perf_config["baseline"]["latency"]
        for key in ("assignment_lag_p95_ms", "lease_renewal_p99_ms", "api_p99_response_ms"):
            val = lat[key]
            assert isinstance(val, (int, float)) and val > 0, f"{key} must be positive, got {val}"

    @pytest.mark.integration
    def test_baseline_resources_positive(self, perf_config: dict) -> None:
        res = perf_config["baseline"]["resources"]
        for key in ("max_memory_mb", "max_open_fds", "max_db_connections"):
            val = res[key]
            assert isinstance(val, (int, float)) and val > 0, f"{key} must be positive, got {val}"

    @pytest.mark.integration
    def test_limits_threadpool_sensible(self, perf_config: dict) -> None:
        tp = perf_config["limits"]["threadpool"]
        assert 1 <= tp["scheduler_max_workers"] <= 64, "scheduler_max_workers out of range"
        assert 1 <= tp["worker_max_workers"] <= 32, "worker_max_workers out of range"
        assert 1 <= tp["db_pool_size"] <= 100, "db_pool_size out of range"

    @pytest.mark.integration
    def test_timeouts_sensible(self, perf_config: dict) -> None:
        to = perf_config["limits"]["timeouts"]
        for key in ("api_read_timeout_seconds", "api_write_timeout_seconds"):
            val = to[key]
            assert isinstance(val, (int, float)) and 1 <= val <= 300, f"{key} out of range [1, 300]"

    @pytest.mark.integration
    def test_scheduler_params_sensible(self, perf_config: dict) -> None:
        sched = perf_config["scheduler"]
        assert 1 <= sched["heartbeat_interval_seconds"] <= 60
        assert sched["heartbeat_timeout_seconds"] >= sched["heartbeat_interval_seconds"] * 2
        assert sched["lease_ttl_seconds"] >= sched["heartbeat_timeout_seconds"]
        assert 1 <= sched["pull_max_in_flight"] <= 64

    @pytest.mark.integration
    def test_scheduler_defaults_conform_to_limits(self) -> None:
        """SchedulerSettings defaults must be within production limits."""
        settings = SchedulerSettings()
        assert settings.executors.threadpool_max_workers >= 2
        assert settings.heartbeat_interval_seconds >= 5
        assert settings.lease_ttl_seconds >= settings.heartbeat_timeout_seconds

    @pytest.mark.integration
    def test_error_budget_sensible(self, perf_config: dict) -> None:
        eb = perf_config["baseline"]["error_budget"]
        assert 0.0 <= eb["max_rejected_bundles_pct"] <= 100
        assert 0.0 <= eb["max_lease_conflict_rate"] <= 1.0
        assert 0.0 <= eb["max_timeout_rate"] <= 1.0
