#!/usr/bin/env bash
# start_whale_p5_dependencies.sh
#
# 启动 Whale P5 准生产依赖验证期所需的全部外部依赖容器。
# 包含：PostgreSQL、Redis、Redpanda（Kafka API）、MinIO（S3）、TDengine。
#
# 健康等待：脚本会等待所有容器 healthy 后再退出。
# Docker 不可用时输出 NOT_RUN: MISSING_ENVIRONMENT 并退出 0。
#
# 使用方式：
#   bash scripts/start_whale_p5_dependencies.sh
#
# 自定义 compose 文件：
#   export WHALE_P5_COMPOSE_FILE=deploy/whale/speed_layer/docker-compose.p5.yml   # 仓库迁移后真实路径，脚本默认 COMPOSE_FILE 已是此值
#
# 注意：
#   - 此脚本仅用于本地 P5 集成测试，不是生产部署工具。
#   - 不与用户本地 .env 冲突。

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="${WHALE_P5_COMPOSE_FILE:-deploy/whale/speed_layer/docker-compose.p5.yml}"
COMPOSE_PATH="$REPO_ROOT/$COMPOSE_FILE"

echo "=========================================="
echo " Whale P5 外部依赖环境启动"
echo " 执行时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo " Compose 文件: ${COMPOSE_PATH}"
echo "=========================================="
echo ""

# ---- 检查 Docker 是否可用 ----
if ! command -v docker &>/dev/null; then
    echo -e "[${YELLOW}NOT_RUN${NC}] MISSING_ENVIRONMENT: Docker 未安装或不在 PATH 中"
    echo "  P5 外部依赖需要 Docker 运行容器。请安装 Docker 后重试。"
    exit 0
fi

if ! docker info &>/dev/null; then
    echo -e "[${YELLOW}NOT_RUN${NC}] MISSING_ENVIRONMENT: Docker 守护进程未运行"
    echo "  请启动 Docker Desktop 或 dockerd 后重试。"
    exit 0
fi

# ---- 检查 compose 文件 ----
if [ ! -f "$COMPOSE_PATH" ]; then
    echo -e "[${RED}FAIL${NC}] Compose 文件不存在: ${COMPOSE_PATH}"
    exit 1
fi

# ---- 检查 docker compose 子命令 ----
COMPOSE_CMD=""
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    echo -e "[${RED}FAIL${NC}] 未找到 docker compose 或 docker-compose 命令"
    exit 1
fi

echo "正在启动 P5 依赖容器..."
$COMPOSE_CMD -f "$COMPOSE_PATH" up -d

echo ""
echo "等待所有服务就绪 (healthy)..."
echo ""

# ---- 逐个服务等待 healthy ----
SERVICES=("postgres" "redis" "redpanda" "minio" "tdengine")
MAX_WAIT=120
ALL_HEALTHY=true

for svc in "${SERVICES[@]}"; do
    echo -n "  等待 ${svc} healthy..."
    waited=0
    svc_healthy=false
    while [ $waited -lt $MAX_WAIT ]; do
        state=$($COMPOSE_CMD -f "$COMPOSE_PATH" ps -q "$svc" 2>/dev/null | xargs -r docker inspect --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
        if [ "$state" = "healthy" ]; then
            echo -e " ${GREEN}OK${NC} (${waited}s)"
            svc_healthy=true
            break
        fi
        sleep 2
        waited=$((waited + 2))
    done
    if [ "$svc_healthy" != "true" ]; then
        echo -e " ${RED}TIMEOUT${NC} (${waited}s)"
        ALL_HEALTHY=false
    fi
done

echo ""
if $ALL_HEALTHY; then
    echo -e "[${GREEN}PASS${NC}] 所有 P5 依赖服务已就绪"
else
    echo -e "[${RED}FAIL${NC}] 部分服务未能在 ${MAX_WAIT}s 内就绪，请检查容器状态"
    echo "  运行诊断: bash scripts/diagnose_whale_p5_dependencies.sh"
    exit 1
fi

# ---- 确保 MinIO bucket 已创建 ----
echo ""
echo "正在创建 MinIO bucket (whale-raw)..."
if command -v python3 &>/dev/null; then
    python3 -c "
import sys
try:
    import boto3
    from botocore.config import Config
    client = boto3.client('s3',
        endpoint_url='http://localhost:9000',
        region_name='us-east-1',
        aws_access_key_id='minioadmin',
        aws_secret_access_key='minioadmin',
        config=Config(s3={'addressing_style': 'path'}),
    )
    try:
        client.head_bucket(Bucket='whale-raw')
        print('bucket whale-raw 已存在')
    except Exception:
        client.create_bucket(Bucket='whale-raw')
        print('bucket whale-raw 已创建')
except ImportError:
    print('[WARN] boto3 未安装，跳过 MinIO bucket 创建')
except Exception as exc:
    print(f'[WARN] MinIO bucket 创建失败: {exc} (非致命，稍后可手动创建)')
" 2>&1 || true
fi

echo ""
echo "=========================================="
echo " P5 依赖环境启动完成"
echo ""
echo " 连接信息:"
echo "   PostgreSQL:  postgresql://whale:whale@localhost:5432/whale_test"
echo "   Redis:       localhost:16379"
echo "   Kafka:       localhost:9092 (Redpanda)"
echo "   S3/MinIO:    http://localhost:9000 (minioadmin:minioadmin)"
echo "   TDengine:    localhost:6041 (root:taosdata, REST: /rest/sql)"
echo ""
echo " 下一步:"
echo "   bash scripts/diagnose_whale_p5_dependencies.sh"
echo "   bash scripts/run_whale_p5_external_dependency_regression.sh"
echo "=========================================="
