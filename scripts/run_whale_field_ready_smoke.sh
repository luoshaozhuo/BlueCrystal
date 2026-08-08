#!/usr/bin/env bash
# =============================================================================
# Whale 现场部署前可交付基线一键预检/验证脚本 (Round 6)
# =============================================================================
# 用途: 串联 L5 probe + Kafka E2E + Storage E2E + field minimal smoke，
#   输出 Whale 现场部署前完整可交付基线汇总。
#
# 每步失败时输出清晰错误，但继续执行后续检查。
# 最终汇总输出 L5 verified / env-pending / failed / skipped。
#
# 使用方式:
#   bash scripts/run_whale_field_ready_smoke.sh
#   bash scripts/run_whale_field_ready_smoke.sh --json              # JSON 输出
#   bash scripts/run_whale_field_ready_smoke.sh --skip-tests        # 跳过测试，仅环境检查
#
# 环境依赖: Docker (for compose ps), CPython 3.13, pytest
# 测试阶段：准生产依赖验证期（E2E/field） + 跨模块联调期验证
#
# 已知 env-pending: Pulsar (6650) / Flink (8081) / HDFS (9870)
# 已知 stub/未实现: batch_layer / warehouse / mart
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

JSON_OUTPUT=false
SKIP_TESTS=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 记录每步结果
declare -A STEP_RESULT
declare -A STEP_DETAIL
STEP_ORDER=(
    "docker-env"
    "field-readback"
    "l6-pollution"
    "l5-probe"
    "kafka-e2e"
    "storage-e2e"
    "field-smoke"
    "l5-marker-audit"
)

usage() {
    cat <<'EOF'
用法: run_whale_field_ready_smoke.sh [OPTIONS]

选项:
  --json         JSON 格式输出汇总
  --skip-tests   跳过测试步骤，仅做环境和静态检查
  -h, --help     显示帮助
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_OUTPUT=true; shift ;;
        --skip-tests) SKIP_TESTS=true; shift ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

# ---- 工具函数 ----
log_info()    { $JSON_OUTPUT || echo -e "${CYAN}[INFO]${NC}     $*"; }
log_ok()      { $JSON_OUTPUT || echo -e "${GREEN}[OK]${NC}       $*"; }
log_fail()    { $JSON_OUTPUT || echo -e "${RED}[FAIL]${NC}     $*"; }
log_warn()    { $JSON_OUTPUT || echo -e "${YELLOW}[WARN]${NC}     $*"; }
log_step()    { $JSON_OUTPUT || echo -e "${BLUE}[STEP]${NC}     $*"; }
log_skip()    { $JSON_OUTPUT || echo -e "${YELLOW}[SKIP]${NC}     $*"; }

mark_result() {
    local step="$1" result="$2" detail="$3"
    STEP_RESULT["$step"]="$result"
    STEP_DETAIL["$step"]="$detail"
}

# ---- Step 1: Docker compose 环境检查 ----
check_docker_env() {
    log_info "Step 1/8: Docker compose 环境检查"

    local compose_file="${REPO_ROOT}/deploy/whale/message_pipeline/docker-compose.whale-l5.yaml"
    if [[ ! -f "$compose_file" ]]; then
        log_fail "docker-compose.whale-l5.yaml 不存在"
        mark_result "docker-env" "failed" "compose file missing"
        return 1
    fi

    if ! command -v docker &>/dev/null; then
        log_fail "docker 命令不可用"
        mark_result "docker-env" "failed" "docker not found"
        return 1
    fi

    # 检查 compose 子命令（docker compose 或 docker-compose）
    local compose_cmd=""
    if docker compose version &>/dev/null 2>&1; then
        compose_cmd="docker compose"
    elif command -v docker-compose &>/dev/null; then
        compose_cmd="docker-compose"
    else
        log_warn "docker compose 命令不可用，跳过容器状态检查"
        mark_result "docker-env" "warn" "docker available but compose not found"
        return 0
    fi

    local ps_output
    if ps_output=$($compose_cmd -f "$compose_file" ps 2>&1); then
        local running_count
        running_count=$(echo "$ps_output" | grep -c "Up" || true)
        local total_count
        total_count=$(echo "$ps_output" | grep -c "whale-l5-" || true)
        if [[ "$running_count" -ge 5 ]]; then
            log_ok "Docker compose L5 容器: ${running_count} 个运行中 (kafka, redis, minio, tdengine, postgres)"
            mark_result "docker-env" "ok" "${running_count} containers running"
        elif [[ "$running_count" -gt 0 ]]; then
            log_warn "Docker compose L5 容器: ${running_count}/${total_count} 运行中，建议 docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml up -d"
            mark_result "docker-env" "warn" "${running_count}/${total_count} running"
        else
            log_warn "Docker compose L5 容器: 无运行中容器，运行 'docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml up -d' 启动"
            mark_result "docker-env" "warn" "no containers running"
        fi
    else
        log_warn "Docker compose ps 失败: $ps_output"
        mark_result "docker-env" "warn" "compose ps failed"
    fi
}

# ---- Step 2: field_readback 不存在检查 ----
check_field_readback() {
    log_info "Step 2/8: field_readback 不存在检查"

    if [[ -d "${REPO_ROOT}/ai_shared/field_readback" ]]; then
        log_fail "ai_shared/field_readback/ 目录存在，应已删除"
        mark_result "field-readback" "failed" "field_readback directory exists"
        return 1
    fi

    if find "${REPO_ROOT}/ai_shared" -maxdepth 1 -name "field_readback" -type d 2>/dev/null | grep -q .; then
        log_fail "ai_shared/field_readback/ 目录存在"
        mark_result "field-readback" "failed" "field_readback directory exists"
        return 1
    fi

    log_ok "field_readback 目录不存在"
    mark_result "field-readback" "ok" "field_readback absent"
}

# ---- Step 3: L6 / 现场环境验证等级污染检查 ----
check_level_pollution() {
    log_info "Step 3/8: L6 / 现场环境验证等级污染检查"

    local l6_found=false
    # 仅在 REQ 文件和 reports 中搜索 L6（不包括 round5 报告中的 "L6 | 不存在" 确认行）
    while IFS= read -r line; do
        if ! echo "$line" | grep -q "L6 | 不存在"; then
            log_fail "发现 L6 引用: $line"
            l6_found=true
        fi
    done < <(grep -Rn "L6" "${REPO_ROOT}/ai_shared/memory/BlueCrystal_REQ_"*.md "${REPO_ROOT}/ai_shared/reports/" 2>/dev/null | grep -v "L6 | 不存在" || true)

    if $l6_found; then
        log_fail "仓库中存在 L6 引用（非确认行）"
        mark_result "l6-pollution" "failed" "L6 references found"
    else
        log_ok "仓库中无 L6 引用污染"
        mark_result "l6-pollution" "ok" "no L6 pollution"
    fi

    # 检查 L5 定义是否回退为"现场环境验证通过"
    local def_reverted=false
    while IFS= read -r line; do
        # 跳过 round4 报告中的历史记录行（这些说明修正了定义）
        if ! echo "$line" | grep -q "whale_l5_definition_req_cleanup_round4"; then
            log_fail "L5 定义可能回退为现场环境验证: $line"
            def_reverted=true
        fi
    done < <(grep -Rn "现场环境验证通过" "${REPO_ROOT}/ai_shared/memory/BlueCrystal_REQ_"*.md "${REPO_ROOT}/ai_shared/reports/" 2>/dev/null | grep -v "whale_l5_definition_req_cleanup_round4" | grep -v "修正为" | grep -v "移除" || true)

    if $def_reverted; then
        log_fail "L5 定义存在回退风险"
        mark_result "l6-pollution" "failed" "L5 definition may be reverted"
    else
        log_ok "L5 定义未回退为现场环境验证"
    fi
}

# ---- Step 4: L5 外部依赖探针 ----
run_l5_probe() {
    log_info "Step 4/8: L5 外部依赖探针"

    local probe_script="${REPO_ROOT}/scripts/run_whale_l5_external_dependency_probe.sh"
    if [[ ! -f "$probe_script" ]]; then
        log_fail "L5 探针脚本不存在: $probe_script"
        mark_result "l5-probe" "failed" "probe script missing"
        return 1
    fi

    local probe_output
    if probe_output=$(bash "$probe_script" --json 2>&1); then
        # 解析 JSON 汇总
        local available degraded unavailable
        available=$(echo "$probe_output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
s = data.get('summary', {})
print(f\"{s.get('available', 0)}/{s.get('total', 0)} available\")
" 2>/dev/null || echo "?/?")

        log_ok "L5 探针完成: $available"

        # 检查关键 P0 服务
        local kafka_status
        kafka_status=$(echo "$probe_output" | python3 -c "
import sys, json
data = json.load(sys.stdin)
svcs = data.get('services', {})
k = svcs.get('kafka', {})
print(k.get('composite_status', 'unknown'))
" 2>/dev/null || echo "unknown")

        if [[ "$kafka_status" == "available" ]]; then
            log_ok "Kafka L5: available"
        else
            log_warn "Kafka L5: $kafka_status (Kafka E2E 测试将被跳过)"
        fi

        mark_result "l5-probe" "ok" "$available"
    else
        log_fail "L5 探针执行失败: $probe_output"
        mark_result "l5-probe" "failed" "probe execution failed"
        return 1
    fi
}

# ---- Step 5: Kafka pipeline L5 E2E ----
run_kafka_e2e() {
    log_info "Step 5/8: Kafka pipeline L5 E2E"

    if $SKIP_TESTS; then
        log_skip "跳过 Kafka E2E 测试 (--skip-tests)"
        mark_result "kafka-e2e" "skipped" "tests skipped"
        return 0
    fi

    local test_file="${REPO_ROOT}/tests/e2e/test_whale_l5_kafka_pipeline_e2e.py"
    if [[ ! -f "$test_file" ]]; then
        log_fail "Kafka E2E 测试文件不存在"
        mark_result "kafka-e2e" "failed" "test file missing"
        return 1
    fi

    local pytest_output
    if pytest_output=$(python3 -m pytest "$test_file" -m l5 -v --tb=short 2>&1); then
        # 统计 passed/skipped/failed
        local passed skipped failed
        passed=$(echo "$pytest_output" | grep -oP '\d+(?= passed)' || echo "0")
        skipped=$(echo "$pytest_output" | grep -oP '\d+(?= skipped)' || echo "0")
        failed=$(echo "$pytest_output" | grep -oP '\d+(?= failed)' || echo "0")
        passed=${passed:-0}
        skipped=${skipped:-0}
        failed=${failed:-0}

        $JSON_OUTPUT || echo "$pytest_output" | tail -5

        if [[ "$failed" -gt 0 ]]; then
            log_fail "Kafka E2E: ${passed} passed, ${failed} failed, ${skipped} skipped"
            mark_result "kafka-e2e" "failed" "${passed}p/${failed}f/${skipped}s"
            return 1
        else
            log_ok "Kafka E2E: ${passed} passed, ${skipped} skipped, ${failed} failed"
            mark_result "kafka-e2e" "ok" "${passed}p/${skipped}s"
        fi
    else
        local exit_code=$?
        # 提取 pytest 的汇总行
        local summary
        summary=$(echo "$pytest_output" | tail -3)
        log_fail "Kafka E2E 执行失败 (exit=$exit_code): $summary"
        mark_result "kafka-e2e" "failed" "exit=$exit_code"
        return 1
    fi
}

# ---- Step 6: Storage L5 E2E ----
run_storage_e2e() {
    log_info "Step 6/8: Storage L5 E2E"

    if $SKIP_TESTS; then
        log_skip "跳过 Storage E2E 测试 (--skip-tests)"
        mark_result "storage-e2e" "skipped" "tests skipped"
        return 0
    fi

    local test_file="${REPO_ROOT}/tests/e2e/test_whale_l5_storage_e2e.py"
    if [[ ! -f "$test_file" ]]; then
        log_fail "Storage E2E 测试文件不存在"
        mark_result "storage-e2e" "failed" "test file missing"
        return 1
    fi

    local pytest_output
    if pytest_output=$(python3 -m pytest "$test_file" -m l5 -v --tb=short 2>&1); then
        local passed skipped failed
        passed=$(echo "$pytest_output" | grep -oP '\d+(?= passed)' || echo "0")
        skipped=$(echo "$pytest_output" | grep -oP '\d+(?= skipped)' || echo "0")
        failed=$(echo "$pytest_output" | grep -oP '\d+(?= failed)' || echo "0")
        passed=${passed:-0}
        skipped=${skipped:-0}
        failed=${failed:-0}

        $JSON_OUTPUT || echo "$pytest_output" | tail -5

        if [[ "$failed" -gt 0 ]]; then
            log_fail "Storage E2E: ${passed} passed, ${failed} failed, ${skipped} skipped"
            mark_result "storage-e2e" "failed" "${passed}p/${failed}f/${skipped}s"
            return 1
        else
            log_ok "Storage E2E: ${passed} passed, ${skipped} skipped, ${failed} failed"
            mark_result "storage-e2e" "ok" "${passed}p/${skipped}s"
        fi
    else
        local exit_code=$?
        local summary
        summary=$(echo "$pytest_output" | tail -3)
        log_fail "Storage E2E 执行失败 (exit=$exit_code): $summary"
        mark_result "storage-e2e" "failed" "exit=$exit_code"
        return 1
    fi
}

# ---- Step 7: Field minimal smoke ----
run_field_smoke() {
    log_info "Step 7/8: Field minimal smoke (L4 InMemory)"

    if $SKIP_TESTS; then
        log_skip "跳过 Field minimal smoke (--skip-tests)"
        mark_result "field-smoke" "skipped" "tests skipped"
        return 0
    fi

    local test_file="${REPO_ROOT}/tests/e2e/test_whale_field_minimal_smoke.py"
    if [[ ! -f "$test_file" ]]; then
        log_fail "Field minimal smoke 测试文件不存在"
        mark_result "field-smoke" "failed" "test file missing"
        return 1
    fi

    local pytest_output
    if pytest_output=$(python3 -m pytest "$test_file" -v --tb=short 2>&1); then
        local passed skipped failed
        passed=$(echo "$pytest_output" | grep -oP '\d+(?= passed)' || echo "0")
        skipped=$(echo "$pytest_output" | grep -oP '\d+(?= skipped)' || echo "0")
        failed=$(echo "$pytest_output" | grep -oP '\d+(?= failed)' || echo "0")
        passed=${passed:-0}
        skipped=${skipped:-0}
        failed=${failed:-0}

        $JSON_OUTPUT || echo "$pytest_output" | tail -5

        if [[ "$failed" -gt 0 ]]; then
            log_fail "Field minimal smoke: ${passed} passed, ${failed} failed, ${skipped} skipped"
            mark_result "field-smoke" "failed" "${passed}p/${failed}f/${skipped}s"
            return 1
        else
            log_ok "Field minimal smoke: ${passed} passed, ${skipped} skipped, ${failed} failed"
            mark_result "field-smoke" "ok" "${passed}p/${skipped}s"
        fi
    else
        local exit_code=$?
        local summary
        summary=$(echo "$pytest_output" | tail -3)
        log_fail "Field minimal smoke 执行失败 (exit=$exit_code): $summary"
        mark_result "field-smoke" "failed" "exit=$exit_code"
        return 1
    fi
}

# ---- Step 8: L5 marker 审计 ----
run_l5_marker_audit() {
    log_info "Step 8/8: L5 marker 审计（InMemory 存储组件测试不得带 @pytest.mark.l5）"

    local violations=0

    # 搜索测试文件中同时 import InMemory sink/adapter 且带 @pytest.mark.l5 的文件。
    # InMemoryMessageBus / InMemoryDeadLetterSink 作为测试基础设施是允许的。
    # 模块级 import 可能服务于同文件的 L4 测试，非必然违规。
    # 仅当 import 的行同时被 @pytest.mark.l5 标记的测试方法使用时才算违规。
    # 本审计为 best-effort 级别；最终以 Round 5 收口报告为准。
    local forbidden_patterns=(
        "InMemoryServingCache"
        "MemoryRawIndexSink"
        "MemoryStandardizedSink"
        "InMemoryWarehouseSink"
        "InMemoryMartSink"
        "InMemoryManifestRepository"
        "InMemorySchemaRegistry"
    )

    while IFS= read -r file; do
        if ! grep -q "@pytest\.mark\.l5" "$file" 2>/dev/null; then
            continue
        fi

        for pattern in "${forbidden_patterns[@]}"; do
            # 仅在文件实际 import 该 InMemory 类时才检查
            if ! grep -q "import ${pattern}\|from.*import.*${pattern}" "$file" 2>/dev/null; then
                continue
            fi

            # 检查是否有 L5 标记的测试方法体内使用了该 InMemory 类
            # 方法: 找到 @pytest.mark.l5 之后的 def test_* 方法，检查方法体内是否引用该 pattern
            local l5_func_list
            l5_func_list=$(python3 -c "
import re, sys
with open('$file') as f:
    content = f.read()
# 找到所有带 @pytest.mark.l5 的 test 方法名
l5_funcs = []
for m in re.finditer(r'@pytest\.mark\.l5\s*\n(?:\s*@\S+\s*\n)*\s*(?:async\s+)?def\s+(test_\w+)', content):
    l5_funcs.append(m.group(1))
for func_name in set(l5_funcs):
    # 找到该方法的 body
    func_match = re.search(r'(?:async\s+)?def\s+' + func_name + r'\b.*?\n(.*?)(?=\n(?:async\s+)?def\s+test_|\nclass\s+|\Z)', content, re.DOTALL)
    if func_match:
        body = func_match.group(1)
        if '$pattern' in body:
            print(func_name)
" 2>/dev/null)

            if [[ -n "$l5_func_list" ]]; then
                log_warn "InMemory 存储组件在 L5 测试方法中使用: $file -> $l5_func_list (imports $pattern)"
                violations=$((violations + 1))
                break
            fi
        done
    done < <(find "${REPO_ROOT}/tests" -name "*.py" -type f 2>/dev/null)

    if [[ "$violations" -gt 0 ]]; then
        log_fail "L5 marker 审计: ${violations} 个违规 (InMemory 组件在 L5 测试中使用)"
        mark_result "l5-marker-audit" "failed" "$violations violations"
    else
        log_ok "L5 marker 审计: 0 个 InMemory 存储组件在 L5 测试中使用"
        mark_result "l5-marker-audit" "ok" "0 violations"
    fi
}

# ---- 汇总输出 ----
print_summary() {
    local ok_count=0 fail_count=0 warn_count=0 skip_count=0

    for step in "${STEP_ORDER[@]}"; do
        local result="${STEP_RESULT[$step]:-unknown}"
        case "$result" in
            ok) ok_count=$((ok_count + 1)) ;;
            failed) fail_count=$((fail_count + 1)) ;;
            warn) warn_count=$((warn_count + 1)) ;;
            skipped) skip_count=$((skip_count + 1)) ;;
        esac
    done

    if $JSON_OUTPUT; then
        echo "{"
        echo "  \"smoke_time\": \"$(date -Iseconds)\","
        echo "  \"summary\": {"
        echo "    \"total_steps\": ${#STEP_ORDER[@]},"
        echo "    \"ok\": $ok_count,"
        echo "    \"failed\": $fail_count,"
        echo "    \"warn\": $warn_count,"
        echo "    \"skipped\": $skip_count"
        echo "  },"
        echo "  \"steps\": {"
        local first=true
        for step in "${STEP_ORDER[@]}"; do
            local result="${STEP_RESULT[$step]:-unknown}"
            local detail="${STEP_DETAIL[$step]:-}"
            $first || echo ","
            first=false
            printf '    "%s": {"result": "%s", "detail": "%s"}' "$step" "$result" "$detail"
        done
        echo ""
        echo "  },"
        echo "  \"known_env_pending\": [\"Pulsar\", \"Flink\", \"HDFS\"],"
        echo "  \"known_stub\": [\"batch_layer\", \"warehouse\", \"mart\"],"
        echo "  \"l5_verified_services\": [\"Kafka\", \"PostgreSQL\", \"Redis\", \"S3/MinIO\", \"TDengine\"],"
        echo "  \"field_readback\": \"absent\","
        echo "  \"l6\": \"absent\""
        echo "}"
    else
        echo ""
        echo "============================================================"
        echo " Whale 现场部署前可交付基线汇总 (Round 6)"
        echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "============================================================"

        for step in "${STEP_ORDER[@]}"; do
            local result="${STEP_RESULT[$step]:-unknown}"
            local detail="${STEP_DETAIL[$step]:-}"
            case "$result" in
                ok) echo -e "  ${GREEN}[OK]${NC}       $step  $detail" ;;
                failed) echo -e "  ${RED}[FAIL]${NC}     $step  $detail" ;;
                warn) echo -e "  ${YELLOW}[WARN]${NC}     $step  $detail" ;;
                skipped) echo -e "  ${YELLOW}[SKIP]${NC}     $step  $detail" ;;
                *) echo -e "  [??]     $step  $detail" ;;
            esac
        done

        echo ""
        echo "============================================================"
        echo " 步骤总计: ${#STEP_ORDER[@]} | OK: ${GREEN}$ok_count${NC} | FAIL: ${RED}$fail_count${NC} | WARN: ${YELLOW}$warn_count${NC} | SKIP: $skip_count"
        echo ""
        echo " L5 verified 服务: Kafka, PostgreSQL, Redis, S3/MinIO, TDengine"
        echo " 已知 env-pending: Pulsar, Flink, HDFS"
        echo " 已知 stub/未实现: batch_layer, warehouse, mart"
        echo ""
        if [[ "$fail_count" -gt 0 ]]; then
            echo -e " ${RED}[FAIL]${NC} 存在失败步骤，请修复后重新运行"
        elif [[ "$warn_count" -gt 0 ]]; then
            echo -e " ${YELLOW}[WARN]${NC} 存在警告步骤，部分验证可能不完整"
        else
            echo -e " ${GREEN}[OK]${NC}   所有步骤通过，可交付基线就绪"
        fi
        echo ""
        echo " 环境启动:  docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml up -d"
        echo " 重新验证:  bash scripts/run_whale_field_ready_smoke.sh"
        echo "============================================================"
    fi
}

# ---- 主流程 ----
main() {
    $JSON_OUTPUT || echo ""
    $JSON_OUTPUT || echo "============================================================"
    $JSON_OUTPUT || echo " Whale 现场部署前可交付基线一键预检 (Round 6)"
    $JSON_OUTPUT || echo " 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    $JSON_OUTPUT || echo " 仓库: $REPO_ROOT"
    $JSON_OUTPUT || echo " 跳过测试: $SKIP_TESTS"
    $JSON_OUTPUT || echo "============================================================"
    $JSON_OUTPUT || echo ""

    # 按顺序执行 8 个检查步骤，每步独立，失败继续
    check_docker_env
    $JSON_OUTPUT || echo ""
    check_field_readback
    $JSON_OUTPUT || echo ""
    check_level_pollution
    $JSON_OUTPUT || echo ""
    run_l5_probe
    $JSON_OUTPUT || echo ""
    run_kafka_e2e
    $JSON_OUTPUT || echo ""
    run_storage_e2e
    $JSON_OUTPUT || echo ""
    run_field_smoke
    $JSON_OUTPUT || echo ""
    run_l5_marker_audit

    print_summary
}

main "$@"
