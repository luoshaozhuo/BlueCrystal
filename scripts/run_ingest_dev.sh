#!/usr/bin/env bash
#
# run_ingest_dev.sh — 本地开发环境下的 Ingest 服务一键启动脚本
#
# 用途：
#   在本地开发环境中，完整地启动 Whale Ingest 服务所依赖的基础设施
#   并运行 Ingest 运行时。整个流程按以下步骤执行：
#
#   1. 确定环境变量文件：优先使用 deploy/whale/ingest/.env.ingest.local，
#      若不存在则回退到 deploy/whale/ingest/.env.ingest.example；两者均缺失时报错退出。
#   2. 加载环境变量文件，并根据 database/state_cache/message 三个
#      backend 选择计算需要的容器集合。
#   3. 执行统一 recreate：删除旧容器与卷。
#   4. 按 backend 组合启动对应容器（sqlite 仅使用本地文件，不起容器）。
#   5. 设置 PYTHONPATH，将 src/ 目录加入 Python 模块搜索路径。
#   6. 初始化数据库并加载示例数据（非交互式）。
#   7. 启动 whale.ingest 运行时主进程。
#
# 用法：
#   bash scripts/run_ingest_dev.sh
#
# 依赖：
#   - Docker（含 Compose 插件）
#   - Python 环境已激活（conda 或 venv）
#   - deploy/whale/ingest/ 下存在 .env.ingest.local 或 .env.ingest.example

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${ROOT_DIR}/deploy/whale/ingest/docker-compose.ingest-dev.yaml"
ENV_DIR="${ROOT_DIR}/deploy/whale/ingest"
LOCAL_ENV_FILE="${ENV_DIR}/.env.ingest.local"
EXAMPLE_ENV_FILE="${ENV_DIR}/.env.ingest.example"
ENV_FILE="${LOCAL_ENV_FILE}"

if [[ ! -f "${ENV_FILE}" ]]; then
  ENV_FILE="${EXAMPLE_ENV_FILE}"
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ingest environment file: ${ENV_FILE}" >&2
  exit 1
fi

cd "${ROOT_DIR}"

echo "[ingest-dev] loading environment from ${ENV_FILE##${ROOT_DIR}/}..."
set -a
source "${ENV_FILE}"
set +a

DB_BACKEND="${WHALE_INGEST_DATABASE_BACKEND:-sqlite}"
STATE_CACHE_BACKEND="${WHALE_INGEST_STATE_CACHE_BACKEND:-relational}"
MESSAGE_BACKEND="${WHALE_INGEST_MESSAGE_BACKEND:-relational_outbox}"

case "${DB_BACKEND}" in
  sqlite|postgresql) ;;
  *)
    echo "Unsupported WHALE_INGEST_DATABASE_BACKEND: ${DB_BACKEND}" >&2
    exit 1
    ;;
esac

case "${STATE_CACHE_BACKEND}" in
  relational|redis) ;;
  *)
    echo "Unsupported WHALE_INGEST_STATE_CACHE_BACKEND: ${STATE_CACHE_BACKEND}" >&2
    exit 1
    ;;
esac

case "${MESSAGE_BACKEND}" in
  relational_outbox|redis_streams|kafka) ;;
  *)
    echo "Unsupported WHALE_INGEST_MESSAGE_BACKEND: ${MESSAGE_BACKEND}" >&2
    exit 1
    ;;
esac

if [[ "${STATE_CACHE_BACKEND}" == "relational" && "${DB_BACKEND}" != "sqlite" ]]; then
  echo "The relational state-cache backend currently requires the sqlite database backend." >&2
  exit 1
fi

declare -a REQUIRED_SERVICES=()
if [[ "${DB_BACKEND}" == "postgresql" ]]; then
  REQUIRED_SERVICES+=("postgres")
fi
if [[ "${STATE_CACHE_BACKEND}" == "redis" ]]; then
  REQUIRED_SERVICES+=("redis")
fi
if [[ "${MESSAGE_BACKEND}" == "redis_streams" ]]; then
  REQUIRED_SERVICES+=("redis")
fi
if [[ "${MESSAGE_BACKEND}" == "kafka" ]]; then
  REQUIRED_SERVICES+=("kafka")
fi

if [[ "${DB_BACKEND}" == "sqlite" ]]; then
  SQLITE_DB_PATH="${WHALE_INGEST_DB_PATH:-${ROOT_DIR}/.data/ingest/whale.ingest.db}"
  export WHALE_INGEST_DB_PATH="${SQLITE_DB_PATH}"
  mkdir -p "$(dirname "${SQLITE_DB_PATH}")"
  echo "[ingest-dev] sqlite database path: ${WHALE_INGEST_DB_PATH}"
fi

echo "[ingest-dev] removing old containers and volumes..."
docker compose -f "${COMPOSE_FILE}" down --remove-orphans --volumes

if [[ ${#REQUIRED_SERVICES[@]} -gt 0 ]]; then
  SERVICES_TO_START="$(printf "%s\n" "${REQUIRED_SERVICES[@]}" | sort -u | tr '\n' ' ')"
  echo "[ingest-dev] selected backends: database=${DB_BACKEND}, state_cache=${STATE_CACHE_BACKEND}, message=${MESSAGE_BACKEND}"
  echo "[ingest-dev] starting selected services: ${SERVICES_TO_START}"
  # shellcheck disable=SC2206
  UNIQUE_SERVICES=( ${SERVICES_TO_START} )
  docker compose -f "${COMPOSE_FILE}" up -d --wait "${UNIQUE_SERVICES[@]}"
else
  echo "[ingest-dev] selected backends: database=${DB_BACKEND}, state_cache=${STATE_CACHE_BACKEND}, message=${MESSAGE_BACKEND}"
  echo "[ingest-dev] selected backends need no containers (sqlite/local-only)."
fi

export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

echo "[ingest-dev] initializing database and loading sample data..."
python -m whale.ingest.framework.persistence.init_db --sample-data --non-interactive

echo "[ingest-dev] starting ingest runtime..."
python -m whale.ingest
