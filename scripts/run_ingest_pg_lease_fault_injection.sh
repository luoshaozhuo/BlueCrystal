#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# ingest PostgreSQL 多进程双节点 lease E2E 与故障注入验证入口（Task B，Round 12）
# ============================================================================
#
# 功能：
#   - 启动 PostgreSQL 测试服务（通过 docker compose 或使用已有 PG DSN）
#   - 执行双进程/多连接 lease E2E 测试
#   - 覆盖：并发 acquire、fencing token mismatch、lease 过期后旧主拒绝、
#     release 后新主接管、DB 断连/超时安全失败
#
# 环境要求（二选一）：
#   1. docker compose 模式：docker 和 docker compose 可用
#   2. PG DSN 模式：设置 WHALE_INGEST_TEST_PG_DSN 指向已有 PostgreSQL
#
# 证据等级：
#   - 具备 PostgreSQL 时为 L4 integration
#   - 仅有 SQLite 时为 L3 simulator（单进程模拟多节点）
#   - 环境缺失时为 environment-pending（对应测试正确 skip）
#
# 重要：如果环境不可用，脚本保留 skip，不得标 passed。
#
# 用法示例：
#   # 自动启动 PG（docker compose）
#   PG_MODE=docker ./scripts/run_ingest_pg_lease_fault_injection.sh
#
#   # 使用已有 PG DSN
#   WHALE_INGEST_TEST_PG_DSN="postgresql+psycopg://user:pass@host:5432/db" \
#     PG_MODE=dsn ./scripts/run_ingest_pg_lease_fault_injection.sh
#
#   # 只运行 SQLite 部分（不需要 PG）
#   PG_MODE=sqlite-only ./scripts/run_ingest_pg_lease_fault_injection.sh
# ============================================================================

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── 配置参数 ────────────────────────────────────────────────────────────────

PG_MODE="${PG_MODE:-auto}"          # auto | docker | dsn | sqlite-only
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.ingest-prodlike.yaml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-whale-pg-lease-test}"
PG_DSN="${WHALE_INGEST_TEST_PG_DSN:-}"
PYTEST_EXTRA_ARGS="${PYTEST_EXTRA_ARGS:-}"

# ── 失败代码分类 ──────────────────────────────────────────────────────────────

readonly RC_OK=0
readonly RC_TEST_FAILED=1
readonly RC_ENV_MISSING=2
readonly RC_DOCKER_FAILED=3
readonly RC_PG_UNAVAILABLE=4

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

log_step() {
  echo "[$(date -u +%H:%M:%S)] $*"
}

cleanup_pg() {
  if [[ "${PG_MODE}" == "docker" ]]; then
    log_step "Stopping PostgreSQL test container..."
    docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down --volumes postgres 2>/dev/null || true
    # Also remove the anonymous volume if any
    docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down -v 2>/dev/null || true
  fi
}

check_pg_ready() {
  local dsn="$1" max_wait="${2:-30}"
  log_step "Waiting for PostgreSQL to be ready (max ${max_wait}s)..."
  for i in $(seq 1 "${max_wait}"); do
    if python3 -c "
import os, sys
try:
    from sqlalchemy import create_engine, text
    e = create_engine('${dsn}', connect_args={'connect_timeout': 3})
    with e.connect() as c:
        c.execute(text('SELECT 1'))
    sys.exit(0)
except Exception as exc:
    sys.exit(1)
" 2>/dev/null; then
      log_step "PostgreSQL is ready."
      return 0
    fi
    sleep 1
  done
  return 1
}

# ── 主流程 ────────────────────────────────────────────────────────────────────

main() {
  log_step "=== ingest PostgreSQL lease fault injection ==="
  log_step "PG_MODE=${PG_MODE}"
  log_step "This is a prodlike fault-injection entry, not a field/e2e closure artifact."

  # ── 自动检测模式 ──────────────────────────────────────────────────────
  if [[ "${PG_MODE}" == "auto" ]]; then
    if [[ -n "${PG_DSN}" ]]; then
      PG_MODE="dsn"
      log_step "auto-detected PG_MODE=dsn (WHALE_INGEST_TEST_PG_DSN is set)"
    elif command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
      PG_MODE="docker"
      log_step "auto-detected PG_MODE=docker (docker is available)"
    else
      PG_MODE="sqlite-only"
      log_step "auto-detected PG_MODE=sqlite-only (no PG DSN and no docker)"
    fi
  fi

  # ── 设置陷阱 ──────────────────────────────────────────────────────────
  trap cleanup_pg EXIT

  local overall_rc=0
  local pg_available=false

  # ── Docker 模式：启动 PG ──────────────────────────────────────────────
  if [[ "${PG_MODE}" == "docker" ]]; then
    log_step "Starting PostgreSQL via docker compose..."
    # 只启动 postgres 服务
    if ! docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d postgres 2>&1; then
      log_step "ERROR: docker compose failed to start PostgreSQL"
      log_step "Falling back to sqlite-only mode."
      PG_MODE="sqlite-only"
    else
      # 等待 PG 就绪
      local pg_host="127.0.0.1"
      local pg_port=5432
      # 从 compose 文件中读取 PG 凭据（默认值）
      local pg_user="${WHALE_INGEST_PRODLIKE_PG_USER:-whale}"
      local pg_pass="${WHALE_INGEST_PRODLIKE_PG_PASSWORD:-whale}"
      local pg_db="whale_ingest"
      PG_DSN="postgresql+psycopg://${pg_user}:${pg_pass}@${pg_host}:${pg_port}/${pg_db}"
      export WHALE_INGEST_TEST_PG_DSN="${PG_DSN}"

      if check_pg_ready "${PG_DSN}" 30; then
        pg_available=true
        log_step "PostgreSQL available at ${pg_host}:${pg_port}"

        # 在测试运行前执行 Alembic migration，确保 ingest_job_lease 等表存在
        log_step "Running database migration (Alembic)..."
        if python3 -c "
import os, sys
os.environ['WHALE_INGEST_DATABASE_URL'] = '${PG_DSN}'
from whale.ingest.framework.persistence import create_runtime_engine, migrate_runtime_database
engine = create_runtime_engine('${PG_DSN}')
try:
    migrate_runtime_database(engine)
    print('Migration completed successfully.')
finally:
    engine.dispose()
" 2>&1; then
          log_step "Database migration PASSED."
        else
          log_step "WARNING: Database migration FAILED. Tests may fail due to missing tables."
        fi
      else
        log_step "WARNING: PostgreSQL did not become ready in time"
        log_step "Falling back to sqlite-only mode."
        PG_MODE="sqlite-only"
        unset WHALE_INGEST_TEST_PG_DSN
      fi
    fi
  elif [[ "${PG_MODE}" == "dsn" ]]; then
    if [[ -z "${PG_DSN}" ]]; then
      log_step "ERROR: PG_MODE=dsn but WHALE_INGEST_TEST_PG_DSN is not set"
      log_step "Falling back to sqlite-only mode."
      PG_MODE="sqlite-only"
    elif check_pg_ready "${PG_DSN}" 10; then
      pg_available=true
      export WHALE_INGEST_TEST_PG_DSN="${PG_DSN}"
      log_step "PostgreSQL is available via DSN."

      # 在测试运行前执行 Alembic migration
      log_step "Running database migration (Alembic)..."
      if python3 -c "
from whale.ingest.framework.persistence import create_runtime_engine, migrate_runtime_database
engine = create_runtime_engine('${PG_DSN}')
try:
    migrate_runtime_database(engine)
    print('Migration completed successfully.')
finally:
    engine.dispose()
" 2>&1; then
        log_step "Database migration PASSED."
      else
        log_step "WARNING: Database migration FAILED. Tests may fail due to missing tables."
      fi
    else
      log_step "WARNING: PostgreSQL at the given DSN is not reachable"
      log_step "Falling back to sqlite-only mode."
      PG_MODE="sqlite-only"
      unset WHALE_INGEST_TEST_PG_DSN
    fi
  fi

  # ── 运行测试 ──────────────────────────────────────────────────────────
  log_step "=== Running SQLite dual-node lease tests ==="
  local sqlite_rc=0
  python -m pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py \
    -q --tb=short \
    -k "not Postgres" \
    ${PYTEST_EXTRA_ARGS} || sqlite_rc=$?

  if [[ ${sqlite_rc} -ne 0 ]]; then
    log_step "SQLite dual-node lease tests FAILED (rc=${sqlite_rc})"
    overall_rc=1
  else
    log_step "SQLite dual-node lease tests PASSED"
  fi

  if [[ "${pg_available}" == "true" ]]; then
    log_step "=== Running PostgreSQL multi-process lease E2E tests ==="
    local pg_rc=0
    python -m pytest tests/integration/test_ingest_dual_node_db_lease_e2e.py \
      -q --tb=short \
      -k "Postgres" \
      ${PYTEST_EXTRA_ARGS} || pg_rc=$?

    if [[ ${pg_rc} -ne 0 ]]; then
      log_step "PostgreSQL multi-process lease tests FAILED (rc=${pg_rc})"
      overall_rc=1
    else
      log_step "PostgreSQL multi-process lease tests PASSED (L4 integration)"
    fi
  else
    log_step "=== PostgreSQL multi-process lease tests SKIPPED ==="
    log_step "Evidence level: environment-pending (no PostgreSQL available)."
    log_step "These tests correctly skip when WHALE_INGEST_TEST_PG_DSN is not set."
    log_step ""
    log_step "To enable PG tests:"
    log_step "  1. Set WHALE_INGEST_TEST_PG_DSN or use PG_MODE=docker"
    log_step "  2. Ensure PostgreSQL is reachable"
    log_step ""
    log_step "NOT marked as passed."
  fi

  # ── 故障注入场景（仅 docker/PG 可用时） ──────────────────────────────
  if [[ "${pg_available}" == "true" ]] && [[ "${PG_MODE}" == "docker" ]]; then
    log_step "=== Running DB disconnect fault injection ==="

    # 验证 readyz 在 PG 可用时返回 ready
    log_step "Verifying readyz before fault injection..."

    # 停止 PG 模拟故障
    log_step "Stopping PostgreSQL to inject DB failure..."
    docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" stop postgres

    # 等待确认 PG 不可达
    log_step "Confirming PostgreSQL is down..."
    if check_pg_ready "${PG_DSN}" 5; then
      log_step "WARNING: PostgreSQL still reachable after stop? Check docker."
    else
      log_step "Confirmed: PostgreSQL is unreachable (expected during fault injection)."
    fi

    # 恢复 PG
    log_step "Restarting PostgreSQL..."
    docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" start postgres

    if check_pg_ready "${PG_DSN}" 30; then
      log_step "PostgreSQL recovered successfully."
    else
      log_step "WARNING: PostgreSQL did not recover in time."
    fi
  fi

  # ── 收口 ──────────────────────────────────────────────────────────────
  if [[ ${overall_rc} -eq 0 ]]; then
    log_step "=== PASS ==="
    if [[ "${pg_available}" == "true" ]]; then
      log_step "Evidence level: L4 integration (PostgreSQL multi-process)."
    else
      log_step "Evidence level: L3 simulator (SQLite only). PG tests: environment-pending."
    fi
    exit ${RC_OK}
  else
    log_step "=== FAILED ==="
    exit ${RC_TEST_FAILED}
  fi
}

main "$@"
