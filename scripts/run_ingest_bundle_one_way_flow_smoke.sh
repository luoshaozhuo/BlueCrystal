#!/usr/bin/env bash
# ── Ingest One-Way Bundle Flow Smoke ──────────────────────────────────
# Simulates management→collection zone offline bundle transfer:
#   1. Export raw bundle (management side)
#   2. Verify redacted bundle is rejected on import
#   3. Dry-run import raw bundle (collection side)
#   4. Import raw bundle
#   5. Verify checksum mismatch is rejected
#   6. Verify audit events were written
set -euo pipefail
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}:${PYTHONPATH:-}"

echo "=== Ingest One-Way Bundle Flow Smoke ==="

python - "$@" <<'PY'
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from whale.ingest.bundle.model import IngestBundle
from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory
from whale.shared.persistence import Base
from whale.shared.persistence.orm import IngestBundleMetadata
from sqlalchemy import create_engine, text

# ── Setup in-memory SQLite ──────────────────────────────────────────
engine = create_engine("sqlite://", echo=False)
Base.metadata.create_all(bind=engine)
session_factory = create_runtime_session_factory(engine)

# Audit collector
audit_events: list[dict] = []


class _MemoryAuditSink:
    def emit(self, event) -> None:
        audit_events.append(event)


service = BundleService(session_factory=session_factory, audit_sink=_MemoryAuditSink(), node_id="test-node")

failures = 0


def check(step: str, condition: bool, detail: str = "") -> None:
    global failures
    if condition:
        print(f"  ✅ {step}")
    else:
        print(f"  ❌ {step}: {detail}")
        failures += 1


# ── 1. Export raw bundle from management zone ───────────────────────
from datetime import UTC, datetime
ts1 = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S%f")
bundle = service.export_bundle(source="mgmt-zone", actor="admin", redacted=False, bundle_version=f"raw-{ts1}")
check("export raw bundle", bundle.bundle_version != "" and bundle.checksum != "")
check("bundle has schema_version", bundle.schema_version == "1.0")
check("bundle not redacted", not bundle.redacted)

# ── 2. Redacted bundle must be rejected ─────────────────────────────
ts2 = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S%f")
redacted = service.export_bundle(source="mgmt-zone", actor="admin", redacted=True, bundle_version=f"redacted-{ts2}")
try:
    service.import_bundle(redacted, actor="admin", dry_run=False)
    check("redacted bundle rejected", False, "should have raised ValueError")
except ValueError as e:
    check("redacted bundle rejected", "REDACTED" in str(e) or "redacted" in str(e).lower())

# ── 3. Dry-run import raw bundle ───────────────────────────────────
dry_result = service.import_bundle(bundle, actor="admin", dry_run=True)
check("dry-run import", dry_result.dry_run and dry_result.imported_count >= 0)

# ── 4. Import raw bundle (accept) ──────────────────────────────────
import_result = service.import_bundle(bundle, actor="admin", dry_run=False)
check("import accepted", not import_result.dry_run and import_result.imported_count >= 0)

# ── 5. Checksum mismatch must be rejected ──────────────────────────
corrupt = bundle.model_copy(update={"checksum": "badchecksum"})
try:
    service.import_bundle(corrupt, actor="admin", dry_run=False)
    check("checksum mismatch rejected", False, "should have raised ValueError")
except ValueError as e:
    check("checksum mismatch rejected", "checksum" in str(e).lower())

# ── 6. Verify audit events were written ────────────────────────────
audit_actions = [e.action for e in audit_events]
check("bundle.export audited", "bundle.export" in audit_actions)
check("bundle.import audited", "bundle.import" in audit_actions)
check("redacted bundle import denied audited", any("DENY" in str(e.decision) for e in audit_events))

print(f"\n--- Smoke result: {failures} failures ---")
sys.exit(failures)
PY
