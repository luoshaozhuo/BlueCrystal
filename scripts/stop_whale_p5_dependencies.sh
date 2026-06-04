#!/usr/bin/env bash
# stop_whale_p5_dependencies.sh
#
# 停止并清理 Whale P5 准生产依赖验证期启动的全部外部依赖容器。
# 默认停止容器但不删除 volumes，加 --clean 参数时同时删除 volumes。
#
# 使用方式：
#   bash scripts/stop_whale_p5_dependencies.sh
#   bash scripts/stop_whale_p5_dependencies.sh --clean

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${WHALE_P5_COMPOSE_FILE:-docker-compose.p5.yml}"
COMPOSE_PATH="$REPO_ROOT/$COMPOSE_FILE"
CLEAN_VOLUMES=false

# 解析参数
for arg in "$@"; do
    case "$arg" in
        --clean|-c)
            CLEAN_VOLUMES=true
            ;;
    esac
done

echo "=========================================="
echo " Whale P5 外部依赖环境停止"
echo " 执行时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="
echo ""

# ---- 检查 Docker 是否可用 ----
if ! command -v docker &>/dev/null; then
    echo "Docker 不可用，无需停止。"
    exit 0
fi

if ! docker info &>/dev/null; then
    echo "Docker 守护进程未运行，无需停止。"
    exit 0
fi

# ---- 检查 compose 文件 ----
if [ ! -f "$COMPOSE_PATH" ]; then
    echo "Compose 文件不存在: ${COMPOSE_PATH}"
    echo "尝试直接停止已知容器名..."
    for container in whale-p5-postgres whale-p5-redis whale-p5-redpanda whale-p5-minio whale-p5-tdengine; do
        docker stop "$container" 2>/dev/null && docker rm "$container" 2>/dev/null || true
    done
    exit 0
fi

# ---- 检查 docker compose 子命令 ----
COMPOSE_CMD=""
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo "未找到 docker compose 或 docker-compose 命令，跳过。"
    exit 0
fi

echo "正在停止 P5 依赖容器..."
if $CLEAN_VOLUMES; then
    $COMPOSE_CMD -f "$COMPOSE_PATH" down -v
    echo "容器已停止，volumes 已删除。"
else
    $COMPOSE_CMD -f "$COMPOSE_PATH" down
    echo "容器已停止（volumes 保留）。"
    echo "如需删除 volumes，运行: bash scripts/stop_whale_p5_dependencies.sh --clean"
fi

echo ""
echo "P5 依赖环境已停止。"
