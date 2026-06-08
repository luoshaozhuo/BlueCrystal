#!/usr/bin/env bash
# Run PostgreSQL migration matrix tests via docker compose PG.
# Usage: scripts/run_pg_migration_matrix.sh [--no-teardown]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-deploy/whale/ingest/docker-compose.ingest-dev.yaml}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-whale-pg-matrix}"
PG_DSN="${WHALE_INGEST_TEST_PG_DSN:-postgresql+psycopg://whale:whale@127.0.0.1:5432/whale_ingest}"
TEARDOWN=true

if [ "${1:-}" = "--no-teardown" ]; then
  TEARDOWN=false
fi

cleanup() {
  if [ "$TEARDOWN" = true ]; then
    echo "--- Tearing down PG container ---"
    docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" rm -sf postgres 2>/dev/null || true
  else
    echo "--- Keeping PG container running (--no-teardown) ---"
  fi
}

trap cleanup EXIT

echo "=== PG Migration Matrix ==="
echo "Compose file: $COMPOSE_FILE"
echo "PG DSN: $PG_DSN"

# Start postgres via compose
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d postgres

# Wait for PG to be healthy
for _ in $(seq 1 30); do
  if docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" exec -T postgres \
    pg_isready -U whale -d whale_ingest >/dev/null 2>&1; then
    echo "PostgreSQL is ready"
    break
  fi
  sleep 2
done

# Run the PG matrix tests
export WHALE_INGEST_TEST_PG_DSN="$PG_DSN"

cd "$ROOT_DIR"
python -m pytest tests/integration/test_ingest_runtime_alembic_postgres_matrix.py -v \
  -o "testpaths=tests/integration/test_ingest_runtime_alembic_postgres_matrix.py"

echo "=== PG Migration Matrix passed ==="
