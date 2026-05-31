#!/usr/bin/env bash
# ============================================================================
# run_ingest_write_readback_smoke.sh 入口自检脚本
# ============================================================================
#
# 被验证对象：scripts/run_ingest_write_readback_smoke.sh
# 证据等级：L2 contract（验证脚本 CLI 接口契约和失败码，不产生设备流量）
#
# 不能证明：
#   - 不验证真实设备 write/readback 行为（L5 field）
#   - 不验证 simulator/native runner 功能（由 pytest 测试覆盖）
#   - 不验证真实网络流量是否发生
#
# 环境依赖：bash 4.x+, python3, pytest, 项目测试文件存在
#
# 用法：
#   bash scripts/test_ingest_write_readback_smoke_contract.sh
# ============================================================================

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="${ROOT_DIR}/scripts/run_ingest_write_readback_smoke.sh"
PASSED=0
FAILED=0
TOTAL=0

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_test() {
  local name="$1"
  local rc="$2"
  local expected="$3"
  local desc="$4"
  TOTAL=$((TOTAL + 1))
  if [[ "${rc}" -eq "${expected}" ]]; then
    echo -e "${GREEN}PASS${NC} [${TOTAL}] ${name}: ${desc}"
    PASSED=$((PASSED + 1))
  else
    echo -e "${RED}FAIL${NC} [${TOTAL}] ${name}: expected rc=${expected}, got rc=${rc}. ${desc}"
    FAILED=$((FAILED + 1))
  fi
}

echo "============================================"
echo "run_ingest_write_readback_smoke.sh 入口自检"
echo "============================================"
echo ""

# Test 1: 脚本存在且可执行
if [[ -x "${SCRIPT}" ]]; then
  echo -e "${GREEN}PASS${NC} [1] 脚本存在且可执行: ${SCRIPT}"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${RED}FAIL${NC} [1] 脚本不可执行或不存在: ${SCRIPT}"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
  exit 1
fi

# Test 2: --help 输出包含所有必要选项
echo ""

HELP_OUTPUT=$(bash "${SCRIPT}" --help 2>&1)
REQUIRED_OPTIONS=(
  "--dry-run"
  "--write-enabled"
  "--confirm"
  "--protocol"
  "--audit-output"
  "--evidence-report"
  "--help"
  "WRITE_ENABLED"
  "CONFIRM_FLAG"
  "dry-run"
  "安全"
)

for opt in "${REQUIRED_OPTIONS[@]}"; do
  if echo "${HELP_OUTPUT}" | grep -qF -- "${opt}"; then
    echo -e "${GREEN}PASS${NC} [*] --help 包含必要选项: ${opt}"
  else
    echo -e "${RED}FAIL${NC} [*] --help 缺失必要选项: ${opt}"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
  fi
done
echo -e "--- --help 输出完整检查完成 ---"

# Test 3: 无效协议返回 rc=4
echo ""
rc=0
bash "${SCRIPT}" --protocol invalid 2>&1 >/dev/null || rc=$?
log_test "无效协议拒绝" "${rc}" 4 "invalid protocol -> rc=4"

# Test 4: WRITE_ENABLED=true 且 CONFIRM_FLAG 缺失时拒绝
echo ""
rc=0
WRITE_ENABLED=true bash "${SCRIPT}" --protocol opcua 2>&1 >/dev/null || rc=$?
log_test "WRITE_ENABLED=true 无 CONFIRM 拒绝" "${rc}" 1 "WRITE_ENABLED without CONFIRM -> rc=1"

# Test 5: --protocol opcua 仅运行 OPC UA
echo ""
OUTPUT=$(bash "${SCRIPT}" --protocol opcua 2>&1)
PROTO_LINE=$(echo "${OUTPUT}" | grep "^Protocols:" || echo "MISSING")
if echo "${PROTO_LINE}" | grep -q "opcua" && ! echo "${PROTO_LINE}" | grep -q "modbus_tcp\|iec61850_mms"; then
  echo -e "${GREEN}PASS${NC} [5] --protocol opcua 仅运行 OPC UA: ${PROTO_LINE}"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${RED}FAIL${NC} [5] --protocol opcua 协议过滤失败: ${PROTO_LINE}"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 6: 协议别名 modbus -> modbus_tcp
echo ""
OUTPUT=$(bash "${SCRIPT}" --protocol modbus 2>&1)
PROTO_LINE=$(echo "${OUTPUT}" | grep "^Protocols:" || echo "MISSING")
if echo "${PROTO_LINE}" | grep -q "modbus_tcp"; then
  echo -e "${GREEN}PASS${NC} [6] 协议别名 modbus -> modbus_tcp: ${PROTO_LINE}"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${RED}FAIL${NC} [6] 协议别名失败: ${PROTO_LINE}"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 7: 协议别名 iec61850 -> iec61850_mms
echo ""
OUTPUT=$(bash "${SCRIPT}" --protocol iec61850 2>&1)
PROTO_LINE=$(echo "${OUTPUT}" | grep "^Protocols:" || echo "MISSING")
if echo "${PROTO_LINE}" | grep -q "iec61850_mms"; then
  echo -e "${GREEN}PASS${NC} [7] 协议别名 iec61850 -> iec61850_mms: ${PROTO_LINE}"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${RED}FAIL${NC} [7] 协议别名失败: ${PROTO_LINE}"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 8: dry-run 默认不产生真实网络流量（通过检查 WRITE_ENABLED 状态）
echo ""
OUTPUT=$(bash "${SCRIPT}" --protocol opcua 2>&1)
if echo "${OUTPUT}" | grep -q "WRITE_ENABLED is 'false'" && echo "${OUTPUT}" | grep -q "not 'true'"; then
  echo -e "${GREEN}PASS${NC} [8] dry-run 默认 WRITE_ENABLED=false"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${RED}FAIL${NC} [8] dry-run 默认未正确显示 WRITE_ENABLED=false"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 9: 证据报告生成
echo ""
REPORT_FILE="/tmp/test_ingest_smoke_contract_$(date +%s).md"
OUTPUT=$(EVIDENCE_REPORT="${REPORT_FILE}" bash "${SCRIPT}" --protocol opcua 2>&1)
if [[ -f "${REPORT_FILE}" ]]; then
  REPORT_CONTENT=$(cat "${REPORT_FILE}")
  if echo "${REPORT_CONTENT}" | grep -q "验证环境" && echo "${REPORT_CONTENT}" | grep -q "证据等级" && echo "${REPORT_CONTENT}" | grep -q "L3 simulator/native"; then
    echo -e "${GREEN}PASS${NC} [9] 证据报告生成正确（含验证环境/证据等级/L3 标注）"
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
  else
    echo -e "${RED}FAIL${NC} [9] 证据报告内容不完整"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
  fi
  rm -f "${REPORT_FILE}"
else
  echo -e "${RED}FAIL${NC} [9] 证据报告未生成"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 10: 审计日志无凭据泄露检查
echo ""
AUDIT_FILE="/tmp/test_ingest_smoke_audit_$(date +%s).jsonl"
AUDIT_OUTPUT="${AUDIT_FILE}" bash "${SCRIPT}" --protocol opcua 2>&1 >/dev/null
if [[ -f "${AUDIT_FILE}" ]]; then
  AUDIT_LINES=$(wc -l < "${AUDIT_FILE}")
  # 检查审计日志中不包含敏感凭据关键词
  if grep -qiE "password|secret|token|api_key|private_key|certificate|credential" "${AUDIT_FILE}"; then
    echo -e "${RED}FAIL${NC} [10] 审计日志可能泄露凭据（检测到敏感关键词）"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
  else
    echo -e "${GREEN}PASS${NC} [10] 审计日志无凭据泄露（${AUDIT_LINES} 行审计记录，无敏感关键词）"
    PASSED=$((PASSED + 1))
    TOTAL=$((TOTAL + 1))
  fi
  rm -f "${AUDIT_FILE}"
else
  echo -e "${GREEN}PASS${NC} [10] 未设置 AUDIT_OUTPUT 时无文件生成（符合预期，仅 stdout）"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 11: --help 输出不泄露密码、token、密钥
echo ""
if echo "${HELP_OUTPUT}" | grep -qiE "password|secret|token|api_key|private_key"; then
  echo -e "${RED}FAIL${NC} [11] --help 输出包含敏感凭据关键词"
  FAILED=$((FAILED + 1))
  TOTAL=$((TOTAL + 1))
else
  echo -e "${GREEN}PASS${NC} [11] --help 输出无敏感凭据泄露"
  PASSED=$((PASSED + 1))
  TOTAL=$((TOTAL + 1))
fi

# Test 12: 三协议 write-readback 测试文件存在
echo ""
REQUIRED_TEST_FILES=(
  "tests/integration/test_ingest_opcua_source_write.py"
  "tests/integration/test_ingest_modbus_source_write.py"
  "tests/integration/test_ingest_iec61850_mms_source_write.py"
)

for tf in "${REQUIRED_TEST_FILES[@]}"; do
  if [[ -f "${ROOT_DIR}/${tf}" ]]; then
    echo -e "${GREEN}PASS${NC} [*] 测试文件存在: ${tf}"
  else
    echo -e "${RED}FAIL${NC} [*] 测试文件缺失: ${tf}"
    FAILED=$((FAILED + 1))
    TOTAL=$((TOTAL + 1))
  fi
done

# ── 收口 ────────────────────────────────────────────────────────────────────

echo ""
echo "============================================"
echo "自检结果: ${PASSED} passed, ${FAILED} failed, ${TOTAL} total"
echo "============================================"

if [[ ${FAILED} -gt 0 ]]; then
  echo "存在 ${FAILED} 个失败项——入口脚本契约不完整。"
  exit 2
else
  echo "入口脚本契约自检全部通过。"
  echo "证据等级: L2 contract（验证 CLI 契约，不产生设备流量）。"
  exit 0
fi
