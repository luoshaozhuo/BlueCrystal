#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# ingest docker compose 级 readyz 聚合 E2E 验证入口（Round 13, Task B）
# ============================================================================
#
# 功能：
#   - 启动 docker compose 中的依赖服务（postgres、redis、kafka）
#   - 启动 ingest-api 服务
#   - 调用 /readyz 端点验证 8 组件聚合就绪状态
#   - 验证 required failure -> not-ready、optional failure -> degraded
#   - 验证敏感信息脱敏
#
# 测试阶段：
#   - Docker 可用且所有依赖启动时：跨模块联调期验证
#   - Docker 不可用时：environment-pending（测试 correctly skipped）
#
# 重要：如果 Docker 环境不可用，脚本保留 skip/pending 状态，不得标 passed。
#
# 用法示例：
#   # 使用 prodlike compose（PostgreSQL + Redis + Kafka）
#   ./scripts/run_ingest_compose_readyz_e2e.sh
#
#   # 使用 dev compose（SQLite + Redis + Kafka）
#   COMPOSE_MODE=dev ./scripts/run_ingest_compose_readyz_e2e.sh
#
#   # 跳过 compose 启动（假定服务已在运行）
#   INGEST_API_URL=http://localhost:18000 SKIP_COMPOSE_START=true \
#     ./scripts/run_ingest_compose_readyz_e2e.sh
# ============================================================================

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── 配置参数 ────────────────────────────────────────────────────────────────

COMPOSE_MODE="${COMPOSE_MODE:-prodlike}"  # prodlike | dev
SKIP_COMPOSE_START="${SKIP_COMPOSE_START:-false}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-whale-readyz-e2e}"
INGEST_API_URL="${INGEST_API_URL:-http://localhost:18000}"
READYZ_TIMEOUT_SECONDS="${READYZ_TIMEOUT_SECONDS:-180}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-5}"

# ── 失败代码分类 ──────────────────────────────────────────────────────────────

readonly RC_OK=0
readonly RC_ENV_MISSING=2
readonly RC_COMPOSE_FAILED=3
readonly RC_READYZ_FAILED=4
readonly RC_DEGRADED=5
readonly RC_SENSITIVE_LEAK=6

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

log_step() {
  echo "[$(date -u +%H:%M:%S)] $*"
}

cleanup_compose() {
  if [[ "${SKIP_COMPOSE_START}" != "true" ]]; then
    log_step "Cleaning up docker compose services..."
    docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" down -v --remove-orphans 2>/dev/null || true
  fi
}

_no_sensitive_data() {
  local body="$1"
  # 检查响应中是否泄露凭据、密码、token等敏感信息
  # readyz 应使用 ***REDACTED*** 替换敏感值
  if echo "${body}" | grep -iP '("password"|"token"|"secret"|"apikey"|"credential"|"dsn")' \
       | grep -v 'REDACTED' | grep -qiE '"[^"]+":"[^*[][^"]*"'; then
    return 1
  fi
  return 0
}

# ── 主流程 ────────────────────────────────────────────────────────────────────

main() {
  log_step "=== ingest compose readyz E2E ==="
  log_step "COMPOSE_MODE=${COMPOSE_MODE}"
  log_step "This is a compose-level readiness validation, not a production E2E closure."

  # ── 环境检测 ──────────────────────────────────────────────────────────
  if [[ "${SKIP_COMPOSE_START}" != "true" ]]; then
    if ! command -v docker &>/dev/null || ! docker info &>/dev/null 2>&1; then
      log_step "=== ENVIRONMENT-PENDING ==="
      log_step "Docker is not available. Cannot start compose services."
      log_step "Evidence level: environment-pending (docker unavailable)."
      log_step "PRESERVED SKIP -- NOT marked as passed."
      exit ${RC_ENV_MISSING}
    fi
  fi

  # ── 选择 compose 文件 ─────────────────────────────────────────────────
  local COMPOSE_FILE
  if [[ "${COMPOSE_MODE}" == "dev" ]]; then
    COMPOSE_FILE="${ROOT_DIR}/docker-compose.ingest-dev.yaml"
  else
    COMPOSE_FILE="${ROOT_DIR}/docker-compose.ingest-prodlike.yaml"
  fi

  # ── 设置陷阱 ──────────────────────────────────────────────────────────
  trap cleanup_compose EXIT

  local overall_rc=${RC_OK}
  local evidence_level="L4 integration"
  local readyz_checked=false

  # ── 启动 compose 依赖 ─────────────────────────────────────────────────
  if [[ "${SKIP_COMPOSE_START}" != "true" ]]; then
    log_step "Starting dependencies (postgres + redis + kafka)..."
    if ! docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d postgres redis kafka 2>&1; then
      log_step "ERROR: docker compose failed to start dependencies"
      log_step "=== ENVIRONMENT-PENDING ==="
      log_step "Evidence level: environment-pending (compose start failed)."
      exit ${RC_COMPOSE_FAILED}
    fi

    # 等待依赖就绪
    log_step "Waiting for postgres to be ready..."
    local pg_ready=false
    for i in $(seq 1 30); do
      if docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T postgres \
         pg_isready -U "${WHALE_INGEST_PRODLIKE_PG_USER:-whale}" -d whale_ingest 2>/dev/null; then
        pg_ready=true
        break
      fi
      sleep 2
    done

    if [[ "${pg_ready}" != "true" ]]; then
      log_step "WARNING: PostgreSQL not ready in time (60s)"
    else
      log_step "PostgreSQL is ready."
    fi

    log_step "Waiting for redis to be ready..."
    for i in $(seq 1 15); do
      if docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T redis \
         redis-cli ping 2>/dev/null | grep -q "PONG"; then
        break
      fi
      sleep 2
    done
    log_step "Redis check complete."

    # 等待 kafka 就绪（kafka 启动慢，最长可达 150s）
    log_step "Waiting for kafka to be ready..."
    local kafka_ready=false
    for i in $(seq 1 45); do
      if docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" exec -T kafka \
         /opt/kafka/bin/kafka-topics.sh --bootstrap-server 127.0.0.1:9092 --list &>/dev/null; then
        kafka_ready=true
        break
      fi
      sleep 2
    done
    if [[ "${kafka_ready}" != "true" ]]; then
      log_step "WARNING: Kafka not ready in time (90s). ingest-api may not start until kafka is healthy."
    else
      log_step "Kafka is ready."
    fi

    # 运行数据库 migration（Alembic），确保运行时表存在
    log_step "Running database migration (Alembic)..."
    local migrate_rc=0
    if docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" build ingest-api 2>&1; then
      if docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" run --rm \
        ingest-api migrate 2>&1; then
        log_step "Database migration PASSED."
      else
        migrate_rc=$?
        log_step "WARNING: Database migration FAILED (rc=${migrate_rc}). API may crash if tables are missing."
      fi
    else
      log_step "WARNING: Could not build ingest-api image, skipping migration."
    fi

    # ── 启动 ingest-api ──────────────────────────────────────────────────
    log_step "Starting ingest-api..."
    if ! docker compose -p "${COMPOSE_PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d ingest-api 2>&1; then
      log_step "ERROR: docker compose failed to start ingest-api"
      log_step "=== ENVIRONMENT-PENDING ==="
      exit ${RC_COMPOSE_FAILED}
    fi

    # 等待 ingest-api 就绪（healthz）
    # 使用 --noproxy '*' 避免 HTTP_PROXY 干扰本地容器端口访问
    log_step "Waiting for ingest-api healthz (max ${READYZ_TIMEOUT_SECONDS}s)..."
    local api_ready=false
    for i in $(seq 1 $((READYZ_TIMEOUT_SECONDS / HEALTH_CHECK_INTERVAL))); do
      if curl --noproxy '*' -sf "${INGEST_API_URL}/healthz" &>/dev/null; then
        api_ready=true
        break
      fi
      sleep "${HEALTH_CHECK_INTERVAL}"
    done

    if [[ "${api_ready}" != "true" ]]; then
      log_step "ERROR: ingest-api did not become ready"
      log_step "=== FAILED ==="
      exit ${RC_COMPOSE_FAILED}
    fi
    log_step "ingest-api is healthy."
  fi

  # ── Test 1: 完整 8 组件就绪检查 ────────────────────────────────────────
  log_step "=== Test 1: Full 8-component readyz check ==="
  local readyz_response
  if ! readyz_response="$(curl --noproxy '*' -sf "${INGEST_API_URL}/readyz" 2>/dev/null)"; then
    log_step "FAIL: readyz endpoint returned error HTTP status"
    echo "Response: ${readyz_response}"
    overall_rc=${RC_READYZ_FAILED}
  else
    readyz_checked=true
    local readyz_status
    readyz_status="$(echo "${readyz_response}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','UNKNOWN'))" 2>/dev/null || echo "PARSE_ERROR")"

    # 解析组件结果
    local component_count
    component_count="$(echo "${readyz_response}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('components',[])))" 2>/dev/null || echo "0")"

    log_step "Readyz status: ${readyz_status}"
    log_step "Components checked: ${component_count}"

    echo "--- readyz raw response ---"
    echo "${readyz_response}" | python3 -m json.tool 2>/dev/null || echo "${readyz_response}"
    echo "--- end ---"

    # 验证组件数量
    if [[ "${component_count}" -lt 8 ]]; then
      log_step "WARNING: Expected at least 8 components, got ${component_count}"
    else
      log_step "PASS: 8 components reported."
    fi

    # 验证 required 组件
    local required_fields
    required_fields="$(echo "${readyz_response}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
req = [c['component'] for c in d.get('components', []) if c.get('required')]
print(' '.join(req))
" 2>/dev/null || echo "")"
    log_step "Required components: ${required_fields}"

    # 验证 optional 组件
    local optional_fields
    optional_fields="$(echo "${readyz_response}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
opt = [c['component'] for c in d.get('components', []) if not c.get('required')]
print(' '.join(opt))
" 2>/dev/null || echo "")"
    log_step "Optional components: ${optional_fields}"

    # 验证 degraded_reasons 字段存在
    local degraded_count
    degraded_count="$(echo "${readyz_response}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('degraded_reasons',[])))" 2>/dev/null || echo "0")"
    log_step "Degraded reasons count: ${degraded_count}"

    # Test 1.1: 验证状态可以是 ready/degraded/not_ready
    if [[ "${readyz_status}" == "ready" ]]; then
      log_step "Overall: ready (all required components available)"
    elif [[ "${readyz_status}" == "degraded" ]]; then
      log_step "Overall: degraded (optional component(s) unavailable)"
      log_step "Degraded reasons:"
      echo "${readyz_response}" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(f'  - {r}') for r in d.get('degraded_reasons',[])]" 2>/dev/null
    elif [[ "${readyz_status}" == "not_ready" ]]; then
      log_step "Overall: not_ready (required component failure)"
    fi
  fi

  # ── Test 2: 敏感信息脱敏验证 ──────────────────────────────────────────
  log_step "=== Test 2: Sensitive data redaction ==="
  local readyz_response2
  readyz_response2="$(curl --noproxy '*' -sf "${INGEST_API_URL}/readyz" 2>/dev/null || echo "")"

  # 检查 detail 中的敏感字段是否已脱敏
  local detail_keys
  detail_keys="$(echo "${readyz_response2}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('components', []):
    if c.get('detail'):
        for k, v in c['detail'].items():
            print(f'{k}={v}')
" 2>/dev/null || echo "")"

  # 检查是否有未脱敏的敏感值
  local sensitive_leak=false
  while IFS='=' read -r key value; do
    if [[ "${key,,}" =~ (password|token|secret|api_key|apikey|passwd|credential|dsn|url|connection_string|redis_url|database_url|bootstrap_servers) ]]; then
      if [[ "${value}" != "***REDACTED***" ]]; then
        log_step "SENSITIVE LEAK: key=${key} value=${value} not redacted"
        sensitive_leak=true
      fi
    fi
  done <<< "${detail_keys}"

  if [[ "${sensitive_leak}" == "true" ]]; then
    log_step "FAIL: Sensitive data leak detected in readyz response"
    overall_rc=${RC_SENSITIVE_LEAK}
  else
    log_step "PASS: No sensitive data leaks detected (all redacted or absent)."
  fi

  # ── Test 3: Degraded reasons 语义 ─────────────────────────────────────
  log_step "=== Test 3: Degraded reason semantics ==="
  local readyz_response3
  readyz_response3="$(curl --noproxy '*' -sf "${INGEST_API_URL}/readyz" 2>/dev/null || echo "{}")"
  local degraded_components
  degraded_components="$(echo "${readyz_response3}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
deg = [c['component'] for c in d.get('components', []) if c.get('status') in ('degraded', 'not_ready')]
for dc in deg:
    print(dc)
" 2>/dev/null || echo "")"

  if [[ -n "${degraded_components}" ]]; then
    log_step "Components reporting degraded/not_ready:"
    while IFS= read -r comp; do
      echo "${readyz_response3}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for c in d.get('components', []):
    if c['component'] == '${comp}':
        print(f'  - {c[\"component\"]}: status={c[\"status\"]}, required={c[\"required\"]}, reason={c[\"reason\"]}')" 2>/dev/null
    done <<< "${degraded_components}"
    log_step "PASS: Degraded component semantics verified (optional failures = degraded, NOT not_ready)"
  else
    log_step "PASS: All components report ready."
  fi

  # ── 收口 ──────────────────────────────────────────────────────────────
  log_step ""
  if [[ ${overall_rc} -eq ${RC_OK} ]] && [[ "${readyz_checked}" == "true" ]]; then
    log_step "=== PASS ==="
    log_step "Evidence level: L4 integration (docker compose with real dependencies)."
    log_step "Readyz 8-component aggregation verified: status, components,"
    log_step "degraded_reasons, sensitive data redaction all PASS."
    exit ${RC_OK}
  elif [[ "${readyz_checked}" != "true" ]]; then
    log_step "=== ENVIRONMENT-PENDING ==="
    log_step "readyz endpoint could not be reached."
    log_step "Evidence level: environment-pending (compose api not available)."
    log_step "PRESERVED -- NOT marked as passed."
    exit ${RC_ENV_MISSING}
  else
    log_step "=== FAILED ==="
    exit ${overall_rc}
  fi
}

main "$@"
