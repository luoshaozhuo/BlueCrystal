#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# ingest 三协议 field write-readback 验证入口（Task D，Round 12）
# ============================================================================
#
# 功能：对 OPC UA / Modbus TCP / IEC 61850 MMS 执行可配置、可审计、
# 默认 dry-run 安全的 write-readback 验证。
#
# 测试阶段：模块集成期验证（simulator/native）—— 无真实设备时为 validation-entry-ready，
# 有真实设备时为 L5 field。
#
# 重要安全警告：
#   - 写入功能**默认关闭**（WRITE_ENABLED=false）。必须显式设置
#     WRITE_ENABLED=true 才会执行实际写入。
#   - 生产环境必须设置 CONFIRM_FLAG=true 确认非 dry-run 安全。
#   - 无真实设备环境不得标 L5 passed。
#
# 用法示例：
#   # Dry-run（只验证脚本存在和配置解析，不写入）
#   ./scripts/run_ingest_write_readback_smoke.sh
#
#   # 执行 OPC UA simulator 验证
#   PROTOCOL=opcua CONFIRM_FLAG=true WRITE_ENABLED=true \
#     ./scripts/run_ingest_write_readback_smoke.sh
#
#   # 三协议全部执行
#   PROTOCOL=all CONFIRM_FLAG=true WRITE_ENABLED=true \
#     ./scripts/run_ingest_write_readback_smoke.sh
#
#   # 指定 audit 输出路径
#   AUDIT_OUTPUT=/var/log/ingest/field_readback_audit.jsonl \
#     PROTOCOL=modbus_tcp CONFIRM_FLAG=true WRITE_ENABLED=true \
#     ./scripts/run_ingest_write_readback_smoke.sh
# ============================================================================

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

# ── 命令行参数解析 ────────────────────────────────────────────────────────────

# 使用环境变量作为默认值，命令行参数可覆盖
PROTOCOL="${PROTOCOL:-all}"
WRITE_ENABLED="${WRITE_ENABLED:-false}"
CONFIRM_FLAG="${CONFIRM_FLAG:-false}"
AUDIT_OUTPUT="${AUDIT_OUTPUT:-}"
EVIDENCE_REPORT="${EVIDENCE_REPORT:-}"
PYTEST_MARKERS="${PYTEST_MARKERS:-}"
PYTEST_EXTRA_ARGS="${PYTEST_EXTRA_ARGS:-}"

print_usage() {
  cat << 'USAGE_EOF'
用法: bash scripts/run_ingest_write_readback_smoke.sh [选项]

ingest 三协议 field write-readback 验证入口。默认 dry-run 安全模式，不产生真实设备写入。

选项:
  --dry-run                 dry-run 模式（默认启用），仅验证脚本和配置，不真实写入设备。
                            此为默认行为，无需显式指定。
  --write-enabled           启用真实写入。必须同时指定 --confirm 才能执行。
                            警告：此选项会向真实设备发送写入命令。
  --confirm                 确认执行真实写入。仅在 --write-enabled 同时指定时生效。
                            此双重安全门防止意外生产写入。
  --protocol <协议>         指定协议：opcua | modbus | iec61850 | all（默认：all）
  --audit-output <路径>     审计日志输出文件路径
  --evidence-report <路径>  证据报告输出文件路径
  --pytest-markers <标记>   pytest 标记过滤
  --pytest-extra-args <参数> 额外 pytest 参数
  --help, -h                显示此帮助信息

环境变量（命令行参数优先级更高）:
  PROTOCOL, WRITE_ENABLED, CONFIRM_FLAG, AUDIT_OUTPUT, EVIDENCE_REPORT,
  PYTEST_MARKERS, PYTEST_EXTRA_ARGS

安全说明:
  - 默认 WRITE_ENABLED=false，不会向设备写入任何数据。
  - 启用真实写入需要同时设置 --write-enabled 和 --confirm。
  - 无真实设备环境不得标 L5 field passed。

示例:
  # Dry-run 模式（默认安全）
  bash scripts/run_ingest_write_readback_smoke.sh

  # 仅验证 OPC UA 协议
  bash scripts/run_ingest_write_readback_smoke.sh --protocol opcua

  # 真实设备写入（需要双重确认）
  bash scripts/run_ingest_write_readback_smoke.sh --protocol modbus --write-enabled --confirm
USAGE_EOF
}

# 解析命令行参数
# 协议别名映射：modbus -> modbus_tcp, iec61850 -> iec61850_mms
DRY_RUN_EXPLICIT=true  # 默认 dry-run 模式
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN_EXPLICIT=true
      # dry-run 模式下确保 WRITE_ENABLED=false（除非已通过 --write-enabled 设置）
      if [[ "${WRITE_ENABLED}" != "true" ]]; then
        WRITE_ENABLED=false
      fi
      shift
      ;;
    --write-enabled)
      WRITE_ENABLED=true
      DRY_RUN_EXPLICIT=false
      shift
      ;;
    --confirm)
      CONFIRM_FLAG=true
      shift
      ;;
    --protocol)
      if [[ -z "${2:-}" ]]; then
        echo "错误：--protocol 需要参数（opcua | modbus | iec61850 | all）"
        exit 4
      fi
      PROTOCOL="$2"
      shift 2
      ;;
    --audit-output)
      if [[ -z "${2:-}" ]]; then
        echo "错误：--audit-output 需要参数（文件路径）"
        exit 4
      fi
      AUDIT_OUTPUT="$2"
      shift 2
      ;;
    --evidence-report)
      if [[ -z "${2:-}" ]]; then
        echo "错误：--evidence-report 需要参数（文件路径）"
        exit 4
      fi
      EVIDENCE_REPORT="$2"
      shift 2
      ;;
    --pytest-markers)
      if [[ -z "${2:-}" ]]; then
        echo "错误：--pytest-markers 需要参数"
        exit 4
      fi
      PYTEST_MARKERS="$2"
      shift 2
      ;;
    --pytest-extra-args)
      if [[ -z "${2:-}" ]]; then
        echo "错误：--pytest-extra-args 需要参数"
        exit 4
      fi
      PYTEST_EXTRA_ARGS="$2"
      shift 2
      ;;
    --help|-h)
      print_usage
      exit 0
      ;;
    *)
      echo "错误：未知选项 '$1'。使用 --help 查看帮助。"
      exit 4
      ;;
  esac
done

# ── 协议别名映射 ──────────────────────────────────────────────────────────────
# 将简写协议名映射到标准名
case "${PROTOCOL}" in
  modbus) PROTOCOL="modbus_tcp" ;;
  iec61850) PROTOCOL="iec61850_mms" ;;
esac

# ── 协议 → 测试文件映射 ──────────────────────────────────────────────────────

declare -A PROTOCOL_TESTS=(
  ["opcua"]="tests/integration/test_ingest_opcua_source_write.py"
  ["modbus_tcp"]="tests/integration/test_ingest_modbus_source_write.py"
  ["iec61850_mms"]="tests/integration/test_ingest_iec61850_mms_source_write.py"
)

# ── 失败代码分类 ──────────────────────────────────────────────────────────────

readonly RC_OK=0
readonly RC_DRY_RUN=0        # dry-run 安全通过
readonly RC_WRITE_DISABLED=0  # 写入被禁用——预期安全行为
readonly RC_CONFIRM_FAILED=1  # 缺少 CONFIRM_FLAG
readonly RC_TEST_FAILED=2     # 测试失败
readonly RC_ENV_MISSING=3     # 环境缺失
readonly RC_INVALID_PROTO=4   # 无效协议
readonly RC_INTERNAL_ERROR=5  # 内部错误

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

log_audit() {
  local level="$1" msg="$2"
  local timestamp
  timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local entry="{\"ts\":\"${timestamp}\",\"level\":\"${level}\",\"msg\":\"${msg}\",\"script\":\"run_ingest_write_readback_smoke\"}"
  echo "${entry}"
  if [[ -n "${AUDIT_OUTPUT}" ]]; then
    echo "${entry}" >> "${AUDIT_OUTPUT}"
  fi
}

write_evidence_report() {
  local results_text="${1:-}"
  local report_file="${EVIDENCE_REPORT}"
  if [[ -z "${report_file}" ]]; then
    report_file="${ROOT_DIR}/ai_shared/reports/write_readback_evidence_$(date +%Y%m%d_%H%M%S).md"
  fi
  mkdir -p "$(dirname "${report_file}")"

  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  local hostname
  hostname="$(hostname 2>/dev/null || echo "unknown")"
  local evidence_level
  if [[ "${WRITE_ENABLED}" == "true" ]]; then
    evidence_level="模块集成期验证（simulator/native，写入已启用；如有真实设备则为准生产依赖验证期 field）"
  else
    evidence_level="模块集成期验证（simulator/native，写入已禁用，validation-entry-ready）"
  fi

  # 直接构造报告内容，避免 heredoc+sed 的分隔符冲突
  {
    printf '# ingest 写入回读现场验证证据报告\n\n'
    printf '## 验证环境\n\n'
    printf '| 参数 | 值 |\n'
    printf '|---|---|\n'
    printf '| 协议 | %s |\n' "${PROTOCOL}"
    printf '| 写入启用 | %s |\n' "${WRITE_ENABLED}"
    printf '| 确认标志 | %s |\n' "${CONFIRM_FLAG}"
    printf '| 执行时间 | %s |\n' "${ts}"
    printf '| 主机名 | %s |\n' "${hostname}"
    printf '\n## 测试阶段\n\n'
    printf '%s\n' "${evidence_level}"
    printf '\n## 验证结果\n\n'
    printf '| 协议 | 测试文件 | 状态 | 失败代码 | 说明 |\n'
    printf '|---|---|---|---|---|\n'
    printf '%s\n' "${results_text}"
    printf '\n## 注意事项\n\n'
    printf '- 若无真实设备环境，本报告测试阶段为 **模块集成期验证（simulator/native）**，不得标为准生产依赖验证期 field。\n'
    printf '- 写入功能默认关闭（WRITE_ENABLED=false），需显式启用。\n'
    printf '- 本验证入口为 **validation-entry-ready**，非 field-ready。\n'
  } > "${report_file}"

  echo "Evidence report written: ${report_file}"
}

classify_failure() {
  local pytest_rc="$1"
  case "${pytest_rc}" in
    0) echo "PASS" ;;
    1) echo "TEST_FAILURES" ;;
    2) echo "USER_INTERRUPT" ;;
    3) echo "INTERNAL_ERROR" ;;
    4) echo "USAGE_ERROR" ;;
    5) echo "NO_TESTS_COLLECTED" ;;
    *) echo "UNKNOWN_RC_${pytest_rc}" ;;
  esac
}

# ── 主流程 ────────────────────────────────────────────────────────────────────

main() {
  log_audit "INFO" "write-readback smoke started: PROTOCOL=${PROTOCOL} WRITE_ENABLED=${WRITE_ENABLED} CONFIRM_FLAG=${CONFIRM_FLAG}"

  # ── 安全门禁 ──────────────────────────────────────────────────────────
  if [[ "${WRITE_ENABLED}" != "true" ]]; then
    echo "=== ingest write-readback smoke (DRY-RUN safe) ==="
    echo "Evidence level: L3 simulator/native (validation-entry-ready)."
    echo "This script is NOT field validation."
    echo ""
    echo "WRITE_ENABLED is '${WRITE_ENABLED}' (not 'true')."
    echo "Running pytest write-readback tests (write adapters are tested via"
    echo "simulator/native runners; no real device writes are sent)."
    echo ""
    echo "To enable real writes against live devices, set:"
    echo "  WRITE_ENABLED=true CONFIRM_FLAG=true PROTOCOL=<protocol> \\"
    echo "  ENDPOINT=<endpoint> NODE=<node> EXPECTED_VALUE=<value> \\"
    echo "  ./scripts/run_ingest_write_readback_smoke.sh"
    echo ""
  fi

  if [[ "${WRITE_ENABLED}" == "true" ]] && [[ "${CONFIRM_FLAG}" != "true" ]]; then
    log_audit "ERROR" "WRITE_ENABLED=true but CONFIRM_FLAG is not 'true'; aborting"
    echo "ERROR: WRITE_ENABLED is 'true' but CONFIRM_FLAG is not 'true'."
    echo "Set CONFIRM_FLAG=true to confirm you intend to send real writes."
    echo "This is a safety gate to prevent accidental production writes."
    exit ${RC_CONFIRM_FAILED}
  fi

  # ── 协议选择 ──────────────────────────────────────────────────────────
  local protocols_to_run=()
  if [[ "${PROTOCOL}" == "all" ]]; then
    protocols_to_run=("opcua" "modbus_tcp" "iec61850_mms")
  elif [[ -n "${PROTOCOL_TESTS[${PROTOCOL}]:-}" ]]; then
    protocols_to_run=("${PROTOCOL}")
  else
    log_audit "ERROR" "Unsupported protocol: ${PROTOCOL}"
    echo "ERROR: Unsupported protocol '${PROTOCOL}'."
    echo "Supported: opcua | modbus_tcp | iec61850_mms | all"
    exit ${RC_INVALID_PROTO}
  fi

  # ── 构建测试文件列表 ──────────────────────────────────────────────────
  local test_files=()
  for proto in "${protocols_to_run[@]}"; do
    test_files+=("${PROTOCOL_TESTS[${proto}]}")
  done

  # ── 构建 pytest 参数 ──────────────────────────────────────────────────
  local pytest_args=(-q --tb=short)
  if [[ -n "${PYTEST_MARKERS}" ]]; then
    pytest_args+=(-m "${PYTEST_MARKERS}")
  fi
  if [[ -n "${PYTEST_EXTRA_ARGS}" ]]; then
    # shellcheck disable=SC2206
    pytest_args+=(${PYTEST_EXTRA_ARGS})
  fi
  pytest_args+=("${test_files[@]}")

  # ── 写入启用时的环境变量 ──────────────────────────────────────────────
  if [[ "${WRITE_ENABLED}" == "true" ]]; then
    export WHALE_INGEST_SOURCE_WRITE_ENABLED=1
    log_audit "WARN" "Write enabled for protocols: ${protocols_to_run[*]}"
  fi

  # ── 执行测试 ──────────────────────────────────────────────────────────
  echo "=== Executing write-readback smoke tests ==="
  echo "Protocols: ${protocols_to_run[*]}"
  echo "Wrapper write_enabled: ${WRITE_ENABLED}"
  echo ""
  local overall_rc=0
  local results_summary=""
  for proto in "${protocols_to_run[@]}"; do
    local test_file="${PROTOCOL_TESTS[${proto}]}"
    local proto_rc=0
    log_audit "INFO" "Running tests for ${proto}: ${test_file}"
    python -m pytest "${test_file}" -q --tb=short ${PYTEST_MARKERS:+-m "${PYTEST_MARKERS}"} ${PYTEST_EXTRA_ARGS:+${PYTEST_EXTRA_ARGS}} || proto_rc=$?
    local failure_class
    failure_class="$(classify_failure "${proto_rc}")"
    results_summary+="| ${proto} | ${test_file} | $([[ ${proto_rc} -eq 0 ]] && echo "PASS" || echo "FAIL (rc=${proto_rc})") | ${failure_class} | |"$'\n'
    if [[ ${proto_rc} -ne 0 ]]; then
      log_audit "ERROR" "Tests for ${proto} failed: rc=${proto_rc} classification=${failure_class}"
      overall_rc=1
    fi
  done

  # ── 生成证据报告 ──────────────────────────────────────────────────────
  if [[ "${WRITE_ENABLED}" == "true" ]] || [[ -n "${EVIDENCE_REPORT}" ]]; then
    write_evidence_report "${results_summary}"

  fi

  # ── 收口 ──────────────────────────────────────────────────────────────
  if [[ ${overall_rc} -eq 0 ]]; then
    if [[ "${WRITE_ENABLED}" != "true" ]]; then
      echo ""
      echo "=== PASS (validation-entry-ready) ==="
      echo "Tests passed. Evidence level: L3 simulator/native."
      echo "This is NOT L5 field validation without real devices."
    else
      echo ""
      echo "=== PASS (write enabled) ==="
      echo "Tests passed with writes enabled."
      echo "If real devices/endpoints were configured, evidence level: L5 field."
      echo "Otherwise: L3 simulator/native."
    fi
    exit ${RC_OK}
  else
    log_audit "ERROR" "Write-readback smoke tests failed"
    echo ""
    echo "=== FAILED ==="
    exit ${RC_TEST_FAILED}
  fi
}

main "$@"
