#!/usr/bin/env bash
# run_whale_p5_external_dependency_regression.sh
#
# P5 准生产依赖验证期 — 全链路回归执行脚本。
#
# 逐项运行以下测试组，输出：
#   test group, stage: P5, result: PASS/FAIL/NOT_RUN, reason, command
#
# 测试组：
#   1. TDengine waveform 集成测试
#   2. TDengine simulation_result 集成测试
#   3. PostgreSQL model_asset 集成测试
#   4. Storage E2E (S3 + TDengine + Redis)
#   5. Kafka pipeline E2E
#
# 退出码：
#   exit 1 — 任一测试组 FAIL
#   exit 0 — 无 FAIL（全 PASS 或部分 NOT_RUN）
#           SUMMARY 行写明环境缺失项
#
# 使用方式：
#   bash scripts/run_whale_p5_external_dependency_regression.sh
#
# 前置条件：
#   建议先运行诊断脚本确认依赖可用：
#     bash scripts/diagnose_whale_p5_dependencies.sh
#   如需启动本地依赖容器：
#     bash scripts/start_whale_p5_dependencies.sh

set -euo pipefail

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# ---- 计数器 ----
PASS_COUNT=0
FAIL_COUNT=0
NOT_RUN_COUNT=0

# ---- 结果记录 ----
declare -a GROUP_RESULTS=()

record_result() {
    local group="$1"
    local result="$2"
    local reason="$3"
    local command="$4"
    GROUP_RESULTS+=("${group}|${result}|${reason}|${command}")
    case "$result" in
        PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
        FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
        NOT_RUN) NOT_RUN_COUNT=$((NOT_RUN_COUNT + 1)) ;;
    esac
}

print_group_header() {
    echo ""
    echo "======================================================================"
    echo " 测试组: $1"
    echo " 阶段: P5 (准生产依赖验证期)"
    echo "======================================================================"
}

# ---- 辅助: 运行 pytest 并解析结果 ----
run_pytest_group() {
    local group_name="$1"
    local cmd="$2"
    local missing_env_reason="${3:-MISSING_ENVIRONMENT}"

    print_group_header "$group_name"
    echo " 命令: ${cmd}"
    echo ""

    # 执行 pytest
    local output
    local rc=0
    output=$(eval "$cmd" 2>&1) || rc=$?

    if [ $rc -eq 0 ]; then
        # pytest exit 0 = 全部通过（或全部 skip）
        if echo "$output" | grep -q "passed"; then
            local passed_count
            passed_count=$(echo "$output" | grep -oP '\d+(?= passed)' | head -1 || echo "?")
            echo -e "  结果: [${GREEN}PASS${NC}] — ${passed_count} 个测试通过"
            record_result "$group_name" "PASS" "全部通过" "$cmd"
        elif echo "$output" | grep -q "skipped" && ! echo "$output" | grep -q "failed"; then
            # 全部 skip → NOT_RUN
            echo -e "  结果: [${YELLOW}NOT_RUN${NC}] — 全部 skip"
            record_result "$group_name" "NOT_RUN" "$missing_env_reason: 全部测试 skip（外部依赖不可达）" "$cmd"
        else
            echo -e "  结果: [${GREEN}PASS${NC}] — 无失败"
            record_result "$group_name" "PASS" "测试通过" "$cmd"
        fi
    elif [ $rc -eq 1 ]; then
        # pytest exit 1 = 有测试失败
        local failed_count
        failed_count=$(echo "$output" | grep -oP '\d+(?= failed)' | head -1 || echo "?")
        echo -e "  结果: [${RED}FAIL${NC}] — ${failed_count} 个测试失败"
        record_result "$group_name" "FAIL" "测试失败 (${failed_count} failed)" "$cmd"
    elif [ $rc -eq 5 ]; then
        # pytest exit 5 = 未收集到测试
        echo -e "  结果: [${YELLOW}NOT_RUN${NC}] — 无可执行测试"
        record_result "$group_name" "NOT_RUN" "$missing_env_reason: 无可执行测试（全部被 skip）" "$cmd"
    else
        # 其他错误
        echo -e "  结果: [${RED}FAIL${NC}] — pytest 执行异常 (exit=${rc})"
        record_result "$group_name" "FAIL" "pytest 执行异常 (exit=${rc})" "$cmd"
    fi

    # 打印 pytest 摘要行
    echo ""
    local summary_line
    summary_line=$(echo "$output" | grep -E "^=?=.*(passed|failed|skipped|error)" | tail -1 || true)
    if [ -n "$summary_line" ]; then
        echo "  $summary_line"
    fi

    # 打印失败详情（如有）
    if [ $rc -eq 1 ]; then
        echo ""
        echo "  失败详情:"
        echo "$output" | grep -A 3 "FAILED\|AssertionError\|Error" | head -40 || true
    fi

    echo ""
}

echo "=========================================="
echo " Whale P5 外部依赖全链路回归验证"
echo " 执行时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="

# =====================================================================
# 1. TDengine waveform 集成测试
# =====================================================================
run_pytest_group \
    "TDengine waveform 集成测试" \
    "python -m pytest tests/integration/test_storage_waveform_tdengine_integration.py -q --no-header --tb=short" \
    "MISSING_ENVIRONMENT: TDengine taosAdapter 不可达"

# =====================================================================
# 2. TDengine simulation_result 集成测试
# =====================================================================
run_pytest_group \
    "TDengine simulation_result 集成测试" \
    "python -m pytest tests/integration/test_storage_simulation_result_tdengine_integration.py -q --no-header --tb=short" \
    "MISSING_ENVIRONMENT: TDengine taosAdapter 不可达"

# =====================================================================
# 3. PostgreSQL model_asset 集成测试
# =====================================================================
run_pytest_group \
    "PostgreSQL model_asset 集成测试" \
    "python -m pytest tests/integration/test_model_asset_postgres_integration.py -q --no-header --tb=short" \
    "MISSING_ENVIRONMENT: WHALE_TEST_POSTGRES_DSN 未设置或 PostgreSQL 不可达"

# =====================================================================
# 4. Storage E2E (S3/MinIO + TDengine + Redis)
# =====================================================================
run_pytest_group \
    "Storage E2E (S3/MinIO + TDengine + Redis)" \
    "python -m pytest tests/e2e/test_whale_l5_storage_e2e.py -q --no-header --tb=short" \
    "MISSING_ENVIRONMENT: S3/MinIO 或 TDengine 或 Redis 不可达"

# =====================================================================
# 5. Kafka pipeline E2E
# =====================================================================
run_pytest_group \
    "Kafka pipeline E2E" \
    "python -m pytest tests/e2e/test_whale_l5_kafka_pipeline_e2e.py -q --no-header --tb=short" \
    "MISSING_ENVIRONMENT: Kafka broker 不可达"

# =====================================================================
# SUMMARY
# =====================================================================
echo ""
echo "=========================================="
echo " P5 外部依赖全链路回归验证 — 汇总"
echo "=========================================="
echo ""
echo "SUMMARY: PASS=${PASS_COUNT}, FAIL=${FAIL_COUNT}, NOT_RUN=${NOT_RUN_COUNT}"
echo ""
echo "逐项明细:"
for entry in "${GROUP_RESULTS[@]}"; do
    IFS='|' read -r grp res reason cmd <<< "$entry"
    case "$res" in
        PASS)  echo -e "  [${GREEN}PASS${NC}]    ${grp}" ;;
        FAIL)  echo -e "  [${RED}FAIL${NC}]    ${grp} — ${reason}" ;;
        NOT_RUN) echo -e "  [${YELLOW}NOT_RUN${NC}] ${grp} — ${reason}" ;;
    esac
    echo "         命令: ${cmd}"
done
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}结果: 存在 ${FAIL_COUNT} 项 FAIL，退出码 1。${NC}"
    echo "  请检查失败详情并修复后重试。"
    exit 1
elif [ "$PASS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}结果: 所有已执行测试通过 (${PASS_COUNT} PASS)。退出码 0。${NC}"
    if [ "$NOT_RUN_COUNT" -gt 0 ]; then
        echo -e "${YELLOW}注意: ${NOT_RUN_COUNT} 项因环境缺失未执行 (NOT_RUN: MISSING_ENVIRONMENT)。${NC}"
    fi
    exit 0
else
    echo -e "${YELLOW}结果: 无可执行测试（${NOT_RUN_COUNT} 项 NOT_RUN: MISSING_ENVIRONMENT）。退出码 0。${NC}"
    echo ""
    echo "环境缺失说明:"
    echo "  - 如需启动本地 P5 依赖容器:"
    echo "      bash scripts/start_whale_p5_dependencies.sh"
    echo "  - 如需诊断外部依赖状态:"
    echo "      bash scripts/diagnose_whale_p5_dependencies.sh"
    echo "  - 环境变量参考:"
    echo "      cat .env.p5.example"
    exit 0
fi
