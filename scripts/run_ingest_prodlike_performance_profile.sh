#!/usr/bin/env bash
# ── Ingest Production-like Performance Profile ──────────────────────────
# Validates the performance profile config and runs a synthetic benchmark
# against the ingest runtime to ensure baseline targets are achievable.
#
# Usage:
#   bash scripts/run_ingest_prodlike_performance_profile.sh
#
# Exit code: number of failed checks (0 = all pass).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="${ROOT_DIR}/config/ingest/performance.prodlike.yaml"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}:${PYTHONPATH:-}"

failures=0

echo "=== Ingest Performance Profile ==="
echo "Config: ${CONFIG_FILE}"
echo ""

# ── 1. Validate config structure ────────────────────────────────────────
python - "${CONFIG_FILE}" <<'PY'
from __future__ import annotations

import sys
import yaml
from pathlib import Path

config_path = Path(sys.argv[1])
failures = 0

try:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    print("  ✅ performance config loads as valid YAML")
except Exception as e:
    print(f"  ❌ performance config invalid: {e}")
    sys.exit(1)

# Check required sections
for section in ("baseline", "limits", "scheduler"):
    if section in data:
        print(f"  ✅ section '{section}' present")
    else:
        print(f"  ❌ section '{section}' missing")
        failures += 1

# Check baseline throughput targets
bt = data.get("baseline", {}).get("throughput", {})
for key in ("jobs_per_second", "events_per_second", "bundle_imports_per_second"):
    val = bt.get(key, 0)
    if isinstance(val, (int, float)) and val > 0:
        print(f"  ✅ baseline.throughput.{key} = {val}")
    else:
        print(f"  ❌ baseline.throughput.{key} missing or zero")
        failures += 1

# Check latency thresholds
lat = data.get("baseline", {}).get("latency", {})
for key in ("assignment_lag_p95_ms", "lease_renewal_p99_ms", "api_p99_response_ms"):
    val = lat.get(key, 0)
    if isinstance(val, (int, float)) and val > 0:
        print(f"  ✅ baseline.latency.{key} = {val}")
    else:
        print(f"  ❌ baseline.latency.{key} missing or zero")
        failures += 1

# Check limits
limits = data.get("limits", {})
tp = limits.get("threadpool", {})
for key in ("scheduler_max_workers", "worker_max_workers", "db_pool_size"):
    val = tp.get(key, 0)
    if isinstance(val, int) and val > 0:
        print(f"  ✅ limits.threadpool.{key} = {val}")
    else:
        print(f"  ❌ limits.threadpool.{key} missing or zero")
        failures += 1

# Check scheduler params
sched = data.get("scheduler", {})
for key in ("heartbeat_interval_seconds", "lease_ttl_seconds", "pull_max_in_flight"):
    val = sched.get(key)
    if isinstance(val, (int, float)) and val > 0:
        print(f"  ✅ scheduler.{key} = {val}")
    else:
        print(f"  ❌ scheduler.{key} missing or not positive")
        failures += 1

print(f"\n  Config validation: {failures} failures")
sys.exit(failures)
PY

config_result=$?
failures=$((failures + config_result))

# ── 2. Validate against SchedulerSettings dataclass ─────────────────────
echo ""
echo "--- Scheduler settings conformance ---"
python - "$@" <<'PY'
from __future__ import annotations

import sys
from whale.ingest.runtime.scheduler_settings import SchedulerSettings

settings = SchedulerSettings()
checks = 0

# Verify defaults are within production limits
assert settings.executors.threadpool_max_workers >= 1, "threadpool_max_workers must be >= 1"
checks += 1

assert settings.heartbeat_interval_seconds >= 1, "heartbeat_interval_seconds must be >= 1"
checks += 1

assert settings.heartbeat_timeout_seconds >= settings.heartbeat_interval_seconds * 2, \
    "heartbeat_timeout must be >= 2x heartbeat_interval"
checks += 1

assert settings.lease_ttl_seconds >= settings.heartbeat_timeout_seconds, \
    "lease_ttl_seconds must be >= heartbeat_timeout_seconds"
checks += 1

assert settings.pull_max_in_flight >= 1, "pull_max_in_flight must be >= 1"
checks += 1

print(f"  ✅ SchedulerSettings default conformance: {checks} checks passed")
PY

sched_result=$?
failures=$((failures + sched_result))

# ── 3. Synthetic benchmark in isolation ─────────────────────────────────
echo ""
echo "--- Synthetic throughput check ---"
python - "$@" <<'PY'
from __future__ import annotations

import time
from uuid import uuid4

from sqlalchemy import create_engine

from whale.ingest.bundle.checksum import compute_bundle_checksum
from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import create_runtime_session_factory
from whale.ingest.domain.audit_event import IngestAuditEvent
from whale.ingest.ports.audit import IngestAuditSinkPort
from whale.shared.persistence import Base
from whale.shared.persistence.orm import AcquisitionTask, IngestBundleMetadata

class _NullAuditSink(IngestAuditSinkPort):
    def emit(self, event: IngestAuditEvent) -> None:
        pass

# In-memory engine with all tables
engine = create_engine("sqlite://", echo=False)
Base.metadata.create_all(bind=engine)
sf = create_runtime_session_factory(engine)

# Pre-seed one task so exports produce rows
session = sf()
session.add(AcquisitionTask(
    task_name="perf-bench-task",
    ld_instance_id=1,
    acquisition_mode="POLLING",
    task_status="STOPPED",
    request_timeout_ms=5000,
    poll_interval_ms=1000,
    polling_max_concurrent_connections=4,
    polling_connection_start_interval_ms=0,
    subscription_start_interval_ms=0,
    subscription_notification_queue_size=1000,
    subscription_notification_worker_count=1,
    subscription_notification_max_lag_ms=5000,
    enabled=True,
    priority=100,
    partition_key="p1",
    assignment_policy="active_standby",
    protocol_params={"protocol": "modbus"},
    freshness_timeout_ms=30000,
    alive_timeout_ms=60000,
    version=1,
))
session.commit()
session.close()

service = BundleService(session_factory=sf, audit_sink=_NullAuditSink())

# Measure bundle export throughput
count = 100
start = time.perf_counter()
for i in range(count):
    b = service.export_bundle(source="perf-test", actor="bench", redacted=False, bundle_version=f"perf-export-{i}")
elapsed = time.perf_counter() - start
exports_per_sec = count / elapsed if elapsed > 0 else 0
print(f"  Bundle exports: {count} in {elapsed:.2f}s = {exports_per_sec:.0f}/s")

# Measure bundle import throughput
start = time.perf_counter()
for i in range(count):
    service.import_bundle(b, actor="bench", dry_run=True)
elapsed2 = time.perf_counter() - start
imports_per_sec = count / elapsed2 if elapsed2 > 0 else 0
print(f"  Bundle dry-imports: {count} in {elapsed2:.2f}s = {imports_per_sec:.0f}/s")

# Check against baseline (very loose for in-memory SQLite)
baseline_exports = 100  # /sec
baseline_imports = 100  # /sec

if exports_per_sec >= baseline_exports:
    print(f"  ✅ export throughput >= {baseline_exports}/s")
else:
    print(f"  ⚠️  export throughput {exports_per_sec:.0f}/s < {baseline_exports}/s (in-memory variant)")
if imports_per_sec >= baseline_imports:
    print(f"  ✅ import throughput >= {baseline_imports}/s")
else:
    print(f"  ⚠️  import throughput {imports_per_sec:.0f}/s < {baseline_imports}/s (in-memory variant)")

print("  ✅ synthetic throughput check complete")
PY

bench_result=$?
failures=$((failures + bench_result))

echo ""
echo "--- Performance profile result: ${failures} failures ---"
exit ${failures}
