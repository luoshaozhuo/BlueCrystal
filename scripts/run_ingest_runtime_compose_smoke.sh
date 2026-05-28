#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.ingest-dev.yaml}"
BASE_URL="${BASE_URL:-http://127.0.0.1:18000}"
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-whale-ingest-smoke}"
SERVICE_NAME="ingest-runtime"

# Unset proxy to avoid interference with localhost container requests
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

CURL="curl -fsS"

probe_url() {
  local path="$1"
  if $CURL "$BASE_URL$path" >/dev/null 2>&1; then
    $CURL "$BASE_URL$path"
    return 0
  fi

  local container_name
  container_name="$(docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps -q "$SERVICE_NAME")"
  if [[ -z "$container_name" ]]; then
    return 1
  fi

  docker exec "$container_name" sh -lc "python - <<'PY'
import urllib.request
with urllib.request.urlopen('http://127.0.0.1:8000$path') as response:
    print(response.read().decode())
PY"
}

cleanup() {
  docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
}

trap cleanup EXIT

docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" up -d --build "$SERVICE_NAME"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" ps
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" logs --tail=200 "$SERVICE_NAME"

for _ in $(seq 1 30); do
  if probe_url "/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

probe_url "/healthz"
probe_url "/readyz"
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" run --rm "$SERVICE_NAME" migrate
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" run --rm "$SERVICE_NAME" worker --smoke-exit
docker compose -p "$PROJECT_NAME" -f "$COMPOSE_FILE" run --rm "$SERVICE_NAME" api-worker --smoke-exit

# Host-port smoke: verify real CRUD via published port (not just healthcheck)
echo "--- Host-port CRUD smoke ---"
# 1. Create a scheduler job via host port
CREATE_RESP=$($CURL -X POST "$BASE_URL/api/v1/scheduler-jobs" \
  -H "Content-Type: application/json" \
  -H "x-actor: smoke-test" \
  -d '{"job_id":"smoke-host-port","job_type":"acquisition","priority":5}')
JOB_ID=$(echo "$CREATE_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)
if [ "$JOB_ID" != "smoke-host-port" ]; then
  echo "FAIL: host-port CREATE returned unexpected response: $CREATE_RESP"
  exit 1
fi
echo "OK: CREATE via host-port returned job_id=$JOB_ID"

# 2. Read the job back via host port
READ_RESP=$($CURL "$BASE_URL/api/v1/scheduler-jobs/smoke-host-port" -H "x-actor: smoke-test")
READ_JOB=$(echo "$READ_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('job_id',''))" 2>/dev/null)
if [ "$READ_JOB" != "smoke-host-port" ]; then
  echo "FAIL: host-port READ returned unexpected response: $READ_RESP"
  exit 1
fi
echo "OK: READ via host-port returned job_id=$READ_JOB"

# 3. List jobs via host port
LIST_RESP=$($CURL "$BASE_URL/api/v1/scheduler-jobs" -H "x-actor: smoke-test")
LIST_TOTAL=$(echo "$LIST_RESP" | python -c "import sys,json; print(json.load(sys.stdin).get('total',0))" 2>/dev/null)
if [ "$LIST_TOTAL" -lt 1 ]; then
  echo "FAIL: host-port LIST returned unexpected response: $LIST_RESP"
  exit 1
fi
echo "OK: LIST via host-port returned total=$LIST_TOTAL"

echo "--- Host-port smoke passed ---"
