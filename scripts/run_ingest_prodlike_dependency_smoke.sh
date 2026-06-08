#!/usr/bin/env bash
# Production-like dependency smoke script.
# Validates ingest runtime with real PostgreSQL / Redis / Kafka via Docker Compose.
#
# Usage:
#   bash scripts/run_ingest_prodlike_dependency_smoke.sh
#
# Exits non-zero if any check fails.

set -euo pipefail

# Unset proxy to avoid intercepting localhost Docker port checks
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-deploy/whale/ingest/docker-compose.ingest-prodlike.yaml}"
COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-whale-prodlike-smoke}"
export WHALE_INGEST_PRODLIKE_PG_USER="${WHALE_INGEST_PRODLIKE_PG_USER:-whale}"
export WHALE_INGEST_PRODLIKE_PG_PASSWORD="${WHALE_INGEST_PRODLIKE_PG_PASSWORD:-$(python - <<'PY'
import secrets
print(secrets.token_urlsafe(18))
PY
)}"
FAILURES=()

cleanup() {
  echo "--- Cleaning up ---"
  docker compose -p "$COMPOSE_PROJECT_NAME" -f "$ROOT_DIR/$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT

cd "$ROOT_DIR"

echo "=== 1. docker compose config ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" config >/dev/null
echo "OK: compose config valid"

echo "=== 2. docker build ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" build 2>&1 | tail -3
echo "OK: image built"

echo "=== 3. Start services ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" up -d postgres redis kafka
for _ in $(seq 1 30); do
  READY=true
  for svc in postgres redis kafka; do
    if ! docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" exec -T "$svc" sh -c "exit 0" 2>/dev/null; then
      READY=false
      break
    fi
  done
  $READY && break
  sleep 2
done
echo "OK: data services ready"

# Create isolated test database
echo "=== 3b. Create test database ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$WHALE_INGEST_PRODLIKE_PG_USER" -d whale_ingest -c "SELECT 1 FROM pg_database WHERE datname='whale_ingest_test'" 2>/dev/null \
  | grep -q 1 \
  || docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" exec -T postgres \
       psql -U "$WHALE_INGEST_PRODLIKE_PG_USER" -d whale_ingest -c "CREATE DATABASE whale_ingest_test OWNER \"$WHALE_INGEST_PRODLIKE_PG_USER\"" 2>/dev/null
echo "OK: test database ready"

# Set DSN for tests
export WHALE_INGEST_TEST_PG_DSN="postgresql+psycopg://${WHALE_INGEST_PRODLIKE_PG_USER}:${WHALE_INGEST_PRODLIKE_PG_PASSWORD}@127.0.0.1:5432/whale_ingest_test"
export WHALE_INGEST_REDIS_HOST="127.0.0.1"
export WHALE_INGEST_REDIS_PORT="16379"
export WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS="127.0.0.1:9092"
export WHALE_INGEST_KAFKA_TOPIC="whale.ingest.prodlike.smoke"

echo "=== 4. Migrate runtime DB ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" run --rm ingest-api migrate
echo "OK: migrate entrypoint succeeded"

echo "=== 5. Start api ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" up -d ingest-api
for _ in $(seq 1 30); do
  HEALTH=$(curl -fsS --noproxy '*' http://127.0.0.1:18000/healthz 2>/dev/null || true)
  if [ "$HEALTH" = '{"status":"ok"}' ]; then
    break
  fi
  sleep 2
done
echo "OK: api healthz=200"

echo "=== 6. Start workers ==="
docker compose -p "$COMPOSE_PROJECT_NAME" -f "$COMPOSE_FILE" up -d ingest-worker-a ingest-worker-b
sleep 5
echo "OK: workers started"

echo "=== 7. PostgreSQL runtime DB test ==="
WHALE_INGEST_TEST_PG_DSN="$WHALE_INGEST_TEST_PG_DSN" \
python -m pytest tests/integration/test_ingest_prodlike_postgres_runtime_db.py -v --tb=short -q 2>&1
echo "OK: PG runtime DB tests passed"

echo "=== 8. Redis cache test ==="
WHALE_INGEST_REDIS_HOST="$WHALE_INGEST_REDIS_HOST" \
WHALE_INGEST_REDIS_PORT="$WHALE_INGEST_REDIS_PORT" \
python -m pytest tests/integration/test_ingest_prodlike_redis_cache.py -v --tb=short -q 2>&1
echo "OK: Redis cache tests passed"

echo "=== 9. Kafka publish test ==="
WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS="$WHALE_INGEST_KAFKA_BOOTSTRAP_SERVERS" \
WHALE_INGEST_KAFKA_TOPIC="$WHALE_INGEST_KAFKA_TOPIC" \
python -m pytest tests/integration/test_ingest_prodlike_kafka_publish.py -v --tb=short -q 2>&1
echo "OK: Kafka publish tests passed"

echo "=== 10. Audit sink test ==="
WHALE_INGEST_TEST_PG_DSN="$WHALE_INGEST_TEST_PG_DSN" \
python -m pytest tests/integration/test_ingest_prodlike_audit_sink.py -v --tb=short -q 2>&1
echo "OK: Audit sink tests passed"

echo "=== 11. Access policy test ==="
python -m pytest tests/integration/test_ingest_prodlike_access_policy.py -v --tb=short -q 2>&1
echo "OK: Access policy tests passed"

echo ""
echo "=== All prodlike dependency smoke checks passed ==="
