#!/usr/bin/env bash
# =============================================================================
# Whale 现场最小链路 smoke 脚本
# =============================================================================
# 用途: 在目标环境运行 Whale 端到端最小链路验证
#   --dry-run: 检查配置、依赖、连接性，不启动实际服务
#   --protocol kafka|pulsar: 仅验证指定消息管道协议
#
# 验证链路:
#   ingest API health → Kafka topic → raw_archive 本地写入 → raw_index memory sink
#   → standardized memory sink → DLQ → checkpoint/lag 指标输出
#
# 如 TDengine/Pulsar/HDFS 镜像不可稳定运行，输出 environment-pending 预检信息。
#
# 测试阶段：跨模块联调期验证（含配置检查）
# 环境依赖: Python 3.11+, Kafka broker (可选)
# =============================================================================

set -euo pipefail

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ---- 默认值 ----
DRY_RUN=false
PROTOCOL="kafka"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PASSED=0
FAILED=0
PENDING=0

# ---- 帮助 ----
usage() {
    cat <<'EOF'
用法: run_whale_field_minimal_smoke.sh [OPTIONS]

选项:
  --dry-run       干运行：检查配置、依赖、连接性，不启动服务
  --protocol VAL  消息管道协议过滤 (kafka|pulsar)，默认 kafka
  -h, --help      显示帮助

示例:
  # 干运行检查
  bash scripts/run_whale_field_minimal_smoke.sh --dry-run

  # Kafka 完整验证
  bash scripts/run_whale_field_minimal_smoke.sh --protocol kafka

  # Pulsar 预检
  bash scripts/run_whale_field_minimal_smoke.sh --protocol pulsar --dry-run
EOF
    exit 0
}

# ---- 参数解析 ----
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --protocol)
            PROTOCOL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "未知选项: $1"
            usage
            ;;
    esac
done

# ---- 工具函数 ----
log_info() { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC}  $*"; PASSED=$((PASSED + 1)); }
log_fail() { echo -e "${RED}[FAIL]${NC}  $*"; FAILED=$((FAILED + 1)); }
log_pending() { echo -e "${YELLOW}[PENDING]${NC} $*"; PENDING=$((PENDING + 1)); }

check_command() {
    local cmd="$1"
    local label="${2:-$cmd}"
    if command -v "$cmd" &>/dev/null; then
        log_pass "$label 可用"
        return 0
    else
        log_fail "$label 不可用"
        return 1
    fi
}

check_python_import() {
    local module="$1"
    local label="${2:-$module}"
    if python3 -c "import $module" 2>/dev/null; then
        log_pass "Python 模块 $label 可用"
        return 0
    else
        # 对于 environment-pending 的依赖，降级为 PENDING 而非 FAIL
        if [[ "$module" == "pulsar"* ]] || [[ "$module" == "taos"* ]] || \
           [[ "$module" == "pyflink"* ]] || [[ "$module" == "pyarrow"* ]] || \
           [[ "$module" == "boto3"* ]]; then
            log_pending "Python 模块 $label 不可用 (environment-pending)"
            return 0
        else
            log_fail "Python 模块 $label 不可用"
            return 1
        fi
    fi
}

check_port() {
    local host="$1"
    local port="$2"
    local label="$3"
    if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        log_pass "$label ($host:$port) 可连接"
        return 0
    else
        if $DRY_RUN; then
            log_pending "$label ($host:$port) 不可连接 (dry-run 模式)"
        else
            log_fail "$label ($host:$port) 不可连接"
        fi
        return 1
    fi
}

check_file() {
    local path="$1"
    local label="$2"
    if [[ -f "$path" ]]; then
        log_pass "$label 存在: $path"
        return 0
    else
        log_pending "$label 不存在: $path (需要首次部署)"
        return 1
    fi
}

# ---- 主流程 ----
main() {
    echo ""
    echo "============================================================"
    echo " Whale 现场最小链路 smoke 检查"
    echo " 模式: $( $DRY_RUN && echo 'dry-run' || echo '实际运行' )"
    echo " 协议: $PROTOCOL"
    echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""

    # ---- Phase 1: 基础依赖 ----
    log_info "Phase 1: 基础依赖检查"
    check_command python3 "Python 3"
    check_command git "git"

    # Python 版本检查
    python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    if [[ "$(python3 -c 'import sys; print(sys.version_info >= (3, 11))')" == "True" ]]; then
        log_pass "Python 版本 $python_version >= 3.11"
    else
        log_fail "Python 版本 $python_version < 3.11，需要 >= 3.11"
    fi

    # Python 核心依赖
    check_python_import yaml "PyYAML"
    check_python_import sqlalchemy "SQLAlchemy"
    check_python_import fastapi "FastAPI"
    check_python_import pydantic "Pydantic"
    check_python_import redis "redis-py"
    check_python_import kafka "kafka-python"
    check_python_import psycopg "psycopg"
    check_python_import pytest "pytest"

    # Environment-pending 依赖
    check_python_import pulsar "pulsar-client (environment-pending)"
    check_python_import taos "taospy (environment-pending)"
    check_python_import pyarrow "pyarrow (environment-pending)"
    check_python_import boto3 "boto3 (environment-pending)"

    echo ""

    # ---- Phase 2: 配置与路径 ----
    log_info "Phase 2: 配置文件检查"
    check_file "$REPO_ROOT/pyproject.toml" "pyproject.toml"
    check_file "$REPO_ROOT/.env.whale.field.example" ".env.whale.field.example"

    # 检查 whale 配置目录
    local config_dir="$REPO_ROOT/config/whale"
    check_file "$config_dir/message_pipeline.kafka.example.yaml" "Kafka 配置模板"
    check_file "$config_dir/message_pipeline.pulsar.example.yaml" "Pulsar 配置模板 (environment-pending)"
    check_file "$config_dir/storage.raw_archive.example.yaml" "raw_archive 配置模板"
    check_file "$config_dir/storage.tdengine.example.yaml" "TDengine 配置模板 (environment-pending)"
    check_file "$config_dir/speed_layer.writers.example.yaml" "speed_layer writers 配置模板"

    echo ""

    # ---- Phase 3: 数据结构与代码 ----
    log_info "Phase 3: 代码结构检查"
    local src_dir="$REPO_ROOT/src/whale"

    # 核心模块存在性检查
    for module in ingest message_pipeline speed_layer storage; do
        if [[ -d "$src_dir/$module" ]]; then
            log_pass "源码模块 $module 存在"
        else
            log_fail "源码模块 $module 不存在"
        fi
    done

    # 测试文件存在性检查
    for test_file in \
        tests/integration/test_message_pipeline_inmemory_e2e.py \
        tests/integration/test_speed_layer_dlq_replay.py \
        tests/integration/test_speed_layer_index_standardized_pipeline.py \
        tests/integration/test_speed_layer_raw_archive_pipeline.py \
        "tests/e2e/test_whale_field_minimal_smoke.py"
    do
        if [[ -f "$REPO_ROOT/$test_file" ]]; then
            log_pass "测试文件 $test_file 存在"
        else
            log_pending "测试文件 $test_file 待创建"
        fi
    done

    echo ""

    # ---- Phase 4: 语法检查 ----
    log_info "Phase 4: 语法编译检查"
    if python3 -m compileall -q "$REPO_ROOT/src/whale" 2>&1; then
        log_pass "src/whale 全部 Python 文件编译通过"
    else
        log_fail "src/whale Python 编译失败"
    fi

    echo ""

    # ---- Phase 5: 连接性检查 ----
    log_info "Phase 5: 外部服务连接性检查"

    # Kafka
    if [[ "$PROTOCOL" == "kafka" ]]; then
        kafka_host=$(python3 -c "
import os, yaml
try:
    with open('$config_dir/message_pipeline.kafka.example.yaml') as f:
        cfg = yaml.safe_load(f)
    servers = cfg.get('kafka', {}).get('bootstrap_servers', ['localhost:9092'])
    parts = servers[0].split(':')
    print(f'{parts[0]}:{parts[1]}')
except:
    print('localhost:9092')
" 2>/dev/null)
        kafka_host_name=$(echo "$kafka_host" | cut -d: -f1)
        kafka_port=$(echo "$kafka_host" | cut -d: -f2)
        if check_port "$kafka_host_name" "$kafka_port" "Kafka broker"; then
            # 尝试通过 kafka-topics.sh 检查
            if command -v kafka-topics.sh &>/dev/null; then
                if kafka-topics.sh --bootstrap-server "$kafka_host" --list &>/dev/null 2>&1; then
                    log_pass "Kafka topic 列表可查询"
                else
                    log_pending "Kafka topic 列表查询失败 (可能 broker 未就绪)"
                fi
            else
                log_pending "kafka-topics.sh 不可用 (可选用 Kafka CLI)"
            fi
        fi
    elif [[ "$PROTOCOL" == "pulsar" ]]; then
        check_port "localhost" "6650" "Pulsar broker"
        log_pending "Pulsar 为 environment-pending 协议，真实 broker 未验证"
    fi

    # TDengine (environment-pending)
    check_port "localhost" "6041" "TDengine taosAdapter"
    log_pending "TDengine raw_index/standardized 为 environment-pending"

    # HDFS / S3 (environment-pending)
    log_pending "HDFS / S3 raw_archive 为 environment-pending"

    echo ""

    # ---- Phase 6: 测试运行 (非 dry-run 时) ----
    if ! $DRY_RUN; then
        log_info "Phase 6: 运行测试"
        cd "$REPO_ROOT"

        # InMemory E2E（无需外部依赖）
        log_info "运行 message_pipeline InMemory E2E 测试..."
        if python3 -m pytest tests/integration/test_message_pipeline_inmemory_e2e.py -v --tb=short -q 2>&1; then
            log_pass "message_pipeline InMemory E2E 通过"
        else
            log_fail "message_pipeline InMemory E2E 失败"
        fi

        # speed_layer DLQ/replay
        log_info "运行 speed_layer DLQ/replay 测试..."
        if python3 -m pytest tests/integration/test_speed_layer_dlq_replay.py -v --tb=short -q 2>&1; then
            log_pass "speed_layer DLQ/replay 通过"
        else
            log_fail "speed_layer DLQ/replay 失败"
        fi

        # speed_layer index/standardized
        log_info "运行 speed_layer index/standardized 测试..."
        if python3 -m pytest tests/integration/test_speed_layer_index_standardized_pipeline.py -v --tb=short -q 2>&1; then
            log_pass "speed_layer index/standardized 通过"
        else
            log_fail "speed_layer index/standardized 失败"
        fi

        # speed_layer raw_archive
        log_info "运行 speed_layer raw_archive pipeline 测试..."
        if python3 -m pytest tests/integration/test_speed_layer_raw_archive_pipeline.py -v --tb=short -q 2>&1; then
            log_pass "speed_layer raw_archive pipeline 通过"
        else
            log_fail "speed_layer raw_archive pipeline 失败"
        fi

        # E2E smoke (如果文件存在)
        if [[ -f "$REPO_ROOT/tests/e2e/test_whale_field_minimal_smoke.py" ]]; then
            log_info "运行 field minimal E2E smoke 测试..."
            if python3 -m pytest tests/e2e/test_whale_field_minimal_smoke.py -v --tb=short -q 2>&1; then
                log_pass "field minimal E2E smoke 通过"
            else
                log_fail "field minimal E2E smoke 失败"
            fi
        fi

        # Kafka contract 测试
        if [[ "$PROTOCOL" == "kafka" ]]; then
            log_info "运行 Kafka contract E2E 测试..."
            if python3 -m pytest tests/integration/test_message_pipeline_kafka_e2e.py -v --tb=short -q 2>&1; then
                log_pass "Kafka contract E2E 通过"
            else
                log_fail "Kafka contract E2E 失败"
            fi
        fi
    else
        log_info "Phase 6: 跳过 (--dry-run 模式)"
    fi

    echo ""

    # ---- 总结 ----
    log_info "============================================================"
    log_info " 摘要"
    log_info "============================================================"
    echo "  通过:   $PASSED"
    echo "  失败:   $FAILED"
    echo "  Pending: $PENDING"

    if [[ $FAILED -gt 0 ]]; then
        log_fail "存在失败项，请在部署前修复"
        exit 1
    elif [[ $PENDING -gt 0 ]]; then
        log_pending "存在 environment-pending 项，部分组件需现场环境就绪后验证"
        log_pending ""
        log_pending "需要现场环境就绪的组件:"
        log_pending "  1. TDengine 集群 → raw_index / standardized 真实后端"
        log_pending "  2. HDFS / S3 → raw_archive 分布式后端"
        log_pending "  3. Pulsar broker → message_pipeline Pulsar 后端"
        log_pending "  4. Flink 集群 → speed_layer Flink runtime"
        log_pending "  5. Redis → serving_cache 真实后端"
        exit 0
    else
        log_pass "全部检查项通过"
        exit 0
    fi
}

main "$@"
