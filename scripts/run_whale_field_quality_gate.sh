#!/usr/bin/env bash
# =============================================================================
# Whale 现场质量门禁脚本
# =============================================================================
# 用途: 对 Whale 全链路执行质量门禁检查
#   - compileall 语法编译
#   - ruff lint
#   - mypy type check
#   - unit tests
#   - integration tests (message_pipeline + speed_layer + storage)
#   - e2e smoke
#   汇总输出 PASS/FAIL/ENVIRONMENT_PENDING
#
# 证据等级: L1 (syntax/type) + L2 (lint/contract) + L3 (unit/integration) + L4 (e2e)
# 环境依赖: Python 3.11+
# =============================================================================

set -euo pipefail

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ---- 默认值 ----
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="${REPO_ROOT}/ai_shared/field_readback"
FAIL_FAST="${FAIL_FAST:-false}"  # 默认不 fail-fast，跑全量
declare -A RESULTS
declare -a GATE_ORDER=(
    "compileall"
    "ruff_lint"
    "mypy_type"
    "unit_tests"
    "integration_tests"
    "e2e_smoke"
    "env_probe"
)

# ---- 帮助 ----
usage() {
    cat <<'EOF'
用法: run_whale_field_quality_gate.sh [OPTIONS]

选项:
  --fail-fast       首个失败即终止
  --skip-import-boundary  跳过 import 边界测试
  --skip-e2e        跳过 e2e smoke
  -h, --help        显示帮助

环境变量:
  FAIL_FAST=true      等同 --fail-fast
  PYTEST_ARGS="..."   额外 pytest 参数

示例:
  # 完整质量门禁
  bash scripts/run_whale_field_quality_gate.sh

  # fail-fast 模式
  FAIL_FAST=true bash scripts/run_whale_field_quality_gate.sh
EOF
    exit 0
}

SKIP_IMPORT_BOUNDARY=false
SKIP_E2E=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --fail-fast) FAIL_FAST=true; shift ;;
        --skip-import-boundary) SKIP_IMPORT_BOUNDARY=true; shift ;;
        --skip-e2e) SKIP_E2E=true; shift ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

# ---- 工具函数 ----
log_info()  { echo -e "${CYAN}[GATE]${NC}  $*"; }
log_pass()  { echo -e "${GREEN}[PASS]${NC}  $*"; }
log_fail()  { echo -e "${RED}[FAIL]${NC}  $*"; }
log_pend()  { echo -e "${YELLOW}[PENDING]${NC} $*"; }

record_result() {
    local gate="$1"
    local status="$2"
    local detail="${3:-}"
    RESULTS["$gate"]="$status"
    if [[ -n "$detail" ]]; then
        RESULTS["${gate}_detail"]="$detail"
    fi
}

run_gate() {
    local gate="$1"
    local label="$2"
    shift 2
    local cmd=("$@")

    echo ""
    log_info "===== $label ====="

    local start_ts
    start_ts=$(date +%s)

    local output
    local exit_code=0

    if output=$("${cmd[@]}" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi

    local end_ts
    end_ts=$(date +%s)
    local elapsed=$((end_ts - start_ts))

    if [[ $exit_code -eq 0 ]]; then
        log_pass "$label (${elapsed}s)"
        record_result "$gate" "PASS"
        # 显示最后 5 行输出
        echo "$output" | tail -5
    else
        log_fail "$label (${elapsed}s, exit=$exit_code)"
        record_result "$gate" "FAIL" "exit_code=$exit_code"
        # 显示最后 20 行输出
        echo "$output" | tail -20
        if [[ "$FAIL_FAST" == "true" ]]; then
            return 1
        fi
    fi
    return 0
}

# ---- 主流程 ----
main() {
    mkdir -p "$OUTPUT_DIR"

    echo ""
    echo "============================================================"
    echo " Whale 现场质量门禁"
    echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo " 仓库: $REPO_ROOT"
    echo " Fail-Fast: $FAIL_FAST"
    echo "============================================================"

    cd "$REPO_ROOT"

    # ---- Gate 1: compileall ----
    run_gate "compileall" "语法编译 (compileall)" \
        python3 -m compileall -q src tests scripts || $FAIL_FAST && return 1

    # ---- Gate 2: ruff lint ----
    run_gate "ruff_lint" "Lint (ruff)" \
        python3 -m ruff check src tests scripts --output-format concise || $FAIL_FAST && return 1

    # ---- Gate 3: mypy type check ----
    run_gate "mypy_type" "类型检查 (mypy)" \
        python3 -m mypy src/whale --no-error-summary 2>&1 || $FAIL_FAST && return 1

    # ---- Gate 4: unit tests ----
    run_gate "unit_tests" "单元测试 (pytest tests/unit)" \
        python3 -m pytest tests/unit/ -v --tb=short -q \
            --no-header ${PYTEST_ARGS:-} 2>&1 || $FAIL_FAST && return 1

    # ---- Gate 5: integration tests ----
    run_gate "integration_tests" "集成测试 (message_pipeline + speed_layer + storage)" \
        python3 -m pytest \
            tests/integration/ \
            -k "ingest or message_pipeline or speed_layer or storage or raw_archive or tdengine or kafka" \
            -v --tb=short -q --no-header ${PYTEST_ARGS:-} 2>&1 || $FAIL_FAST && return 1

    # Import boundary tests
    if ! $SKIP_IMPORT_BOUNDARY; then
        if [[ -f "$REPO_ROOT/tests/unit/test_turtle_octopus_import_boundary.py" ]]; then
            run_gate "import_boundary" "Import 边界测试" \
                python3 -m pytest tests/unit/test_turtle_octopus_import_boundary.py \
                    -v --tb=short -q --no-header ${PYTEST_ARGS:-} 2>&1 || $FAIL_FAST && return 1
        fi
    fi

    # ---- Gate 6: e2e smoke ----
    if ! $SKIP_E2E; then
        if [[ -f "$REPO_ROOT/tests/e2e/test_whale_field_minimal_smoke.py" ]]; then
            run_gate "e2e_smoke" "E2E Smoke 测试" \
                python3 -m pytest tests/e2e/ -v --tb=short -q --no-header \
                    ${PYTEST_ARGS:-} 2>&1 || $FAIL_FAST && return 1
        else
            log_pend "E2E smoke 测试文件不存在，跳过"
            record_result "e2e_smoke" "SKIP" "file_not_found"
        fi
    else
        log_pend "E2E smoke 跳过 (--skip-e2e)"
        record_result "e2e_smoke" "SKIP" "user_requested"
    fi

    # ---- Gate 7: 环境探针 ----
    log_info "===== 环境探针 ====="

    # TDengine 检查
    if timeout 3 bash -c "echo >/dev/tcp/localhost/6041" 2>/dev/null; then
        log_info "TDengine (localhost:6041): 可连接"
        record_result "env_probe_tdengine" "AVAILABLE"
    else
        log_pend "TDengine (localhost:6041): 不可连接 (environment-pending)"
        record_result "env_probe_tdengine" "ENVIRONMENT_PENDING"
    fi

    # Pulsar 检查
    if timeout 3 bash -c "echo >/dev/tcp/localhost/6650" 2>/dev/null; then
        log_info "Pulsar (localhost:6650): 可连接"
        record_result "env_probe_pulsar" "AVAILABLE"
    else
        log_pend "Pulsar (localhost:6650): 不可连接 (environment-pending)"
        record_result "env_probe_pulsar" "ENVIRONMENT_PENDING"
    fi

    # HDFS 检查
    if timeout 3 bash -c "echo >/dev/tcp/localhost/9870" 2>/dev/null; then
        log_info "HDFS NameNode (localhost:9870): 可连接"
        record_result "env_probe_hdfs" "AVAILABLE"
    else
        log_pend "HDFS NameNode (localhost:9870): 不可连接 (environment-pending)"
        record_result "env_probe_hdfs" "ENVIRONMENT_PENDING"
    fi

    # S3/MinIO 检查
    if timeout 3 bash -c "echo >/dev/tcp/localhost/9000" 2>/dev/null; then
        log_info "S3/MinIO (localhost:9000): 可连接"
        record_result "env_probe_s3" "AVAILABLE"
    else
        log_pend "S3/MinIO (localhost:9000): 不可连接 (environment-pending)"
        record_result "env_probe_s3" "ENVIRONMENT_PENDING"
    fi

    echo ""

    # ---- 汇总 ----
    local all_passed=true
    local has_failure=false
    local has_pending=false

    echo "============================================================"
    log_info "质量门禁汇总"
    echo "============================================================"

    for gate in "${GATE_ORDER[@]}"; do
        local status="${RESULTS[$gate]:-UNKNOWN}"
        local detail="${RESULTS[${gate}_detail]:-}"
        case "$status" in
            PASS)
                echo -e "  ${GREEN}[PASS]${NC}  $gate $detail"
                ;;
            FAIL)
                echo -e "  ${RED}[FAIL]${NC}  $gate $detail"
                has_failure=true
                all_passed=false
                ;;
            SKIP)
                echo -e "  ${YELLOW}[SKIP]${NC}  $gate $detail"
                has_pending=true
                ;;
            *)
                echo -e "  ${YELLOW}[??]${NC}   $gate $status $detail"
                has_pending=true
                all_passed=false
                ;;
        esac
    done

    echo ""
    log_info "环境探针:"
    for probe in tdengine pulsar hdfs s3; do
        local pstatus="${RESULTS[env_probe_${probe}]:-UNKNOWN}"
        case "$pstatus" in
            AVAILABLE)
                echo -e "  ${GREEN}[OK]${NC}    $probe: 可用"
                ;;
            ENVIRONMENT_PENDING)
                echo -e "  ${YELLOW}[PENDING]${NC} $probe: environment-pending"
                has_pending=true
                ;;
            *)
                echo -e "  ${YELLOW}[??]${NC}    $probe: $pstatus"
                ;;
        esac
    done

    echo ""
    echo "============================================================"
    if $has_failure; then
        echo -e "  总体结果: ${RED}FAIL${NC}"
        echo "============================================================"
        echo ""
        log_info "失败项需在部署前修复"
        exit 1
    elif $has_pending; then
        echo -e "  总体结果: ${YELLOW}ENVIRONMENT_PENDING${NC}"
        echo "============================================================"
        echo ""
        log_info "存在 environment-pending 项，需现场环境就绪后补验证"
        exit 0
    else
        echo -e "  总体结果: ${GREEN}PASS${NC}"
        echo "============================================================"
        echo ""
        log_pass "全部质量门禁通过"
        exit 0
    fi
}

main "$@"
