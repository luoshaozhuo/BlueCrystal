#!/usr/bin/env bash
# CI gate script for ingest runtime — run all non-source_lab validation tests.
#
# Usage:
#   scripts/ci_ingest_runtime_gate.sh                # run all gates
#   scripts/ci_ingest_runtime_gate.sh --skip-smoke    # skip compose smoke (no Docker)
#   scripts/ci_ingest_runtime_gate.sh --skip-pg       # skip PG migration matrix
#
# Exits non-zero if any gate fails.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKIP_SMOKE=false
SKIP_PG=false
FAILURES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-smoke) SKIP_SMOKE=true; shift ;;
    --skip-pg)    SKIP_PG=true;    shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

cd "$ROOT_DIR"

# ── Helper ────────────────────────────────────────────────────────────────────

PASS=0
FAIL=0

run_gate() {
  local name="$1"
  shift
  echo ""
  echo "═══ Gate: $name ═══"
  if python -m pytest "$@" -x --tb=line -q; then
    echo "✅ PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "❌ FAIL: $name"
    FAIL=$((FAIL + 1))
    FAILURES+=("$name")
  fi
}

# ── 1. No source_lab imports in ingest production path ────────────────────────
run_gate "no-source-lab-imports" \
  tests/unit/test_iec61850_report_acquisition_adapter.py::TestReportAdapterNoSourceLabImport \
  tests/unit/test_iec61850_mms_backend.py

# ── 2. Idempotency tests ──────────────────────────────────────────────────────
run_gate "idempotency" \
  tests/integration/test_ingest_api_idempotency_all_mutating_routes.py

# ── 3. Dry-run tests ─────────────────────────────────────────────────────────
run_gate "dry-run" \
  tests/integration/test_ingest_api_dry_run_all_mutating_routes.py

# ── 4. Idempotency + dry_run interaction tests ───────────────────────────────
run_gate "idempotency-dry-run-interaction" \
  tests/integration/test_ingest_api_idempotency_dry_run_interaction.py

# ── 5. Full idempotency + dry_run combined suite ─────────────────────────────
run_gate "idempotency-dry-run-full" \
  tests/integration/test_ingest_api_idempotency_dry_run.py

# ── 6. PG migration matrix ───────────────────────────────────────────────────
if [ "$SKIP_PG" = false ]; then
  echo ""
  echo "═══ Gate: pg-migration-matrix ═══"
  if bash scripts/run_pg_migration_matrix.sh; then
    echo "✅ PASS: pg-migration-matrix"
    PASS=$((PASS + 1))
  else
    echo "❌ FAIL: pg-migration-matrix"
    FAIL=$((FAIL + 1))
    FAILURES+=("pg-migration-matrix")
  fi
else
  echo "═══ Gate: pg-migration-matrix (skipped) ═══"
fi

# ── 7. Compose host-port smoke ───────────────────────────────────────────────
if [ "$SKIP_SMOKE" = false ]; then
  echo ""
  echo "═══ Gate: compose-smoke ═══"
  if bash scripts/run_ingest_runtime_compose_smoke.sh; then
    echo "✅ PASS: compose-smoke"
    PASS=$((PASS + 1))
  else
    echo "❌ FAIL: compose-smoke"
    FAIL=$((FAIL + 1))
    FAILURES+=("compose-smoke")
  fi
else
  echo "═══ Gate: compose-smoke (skipped) ═══"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  CI Gate Summary: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════════════════════"
if [ "$FAIL" -gt 0 ]; then
  for f in "${FAILURES[@]}"; do
    echo "  ❌ $f"
  done
  exit 1
fi
echo "  ✅ All gates passed"
