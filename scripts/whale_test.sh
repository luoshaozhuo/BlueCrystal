#!/usr/bin/env bash
# =============================================================================
# Whale 测试统一入口
#
# 支持两个模式：
#   1. dry-run（默认） — 输出测试计划，不执行任何测试。
#   2. execute（--execute） — 执行低风险评估期和 must-run 命令；
#      外部依赖、长测、人工条件测试仅列入 NOT_RUN 或 manual-or-expensive。
#
# 输出结果使用 PASS / FAIL / NOT_RUN。
#
# 参数:
#   --stage     生命周期阶段 (必选，除非指定 --suite)
#   --component 组件名 (可选，默认 whale)
#   --module    子模块名 (可选)
#   --suite     回归套件 (可选)
#   --execute   实际执行测试 (默认 dry-run)
#   --dry-run   显式 dry-run (默认已开启)
#
# 生命周期阶段取值:
#   开发期验证
#   构建期验证
#   模块集成期验证
#   跨模块联调期验证
#   准生产依赖验证期
#   部署前验收期
#   发布后运维验证期
#
# 组件取值: whale, platform_shared, turtle, octopus
#
# 模块取值 (仅 whale 组件): ingest, message_pipeline, speed_layer, storage, shared_source, batch_layer
#
# 回归套件取值: affected-regression, module-regression, chain-regression, release-regression
#
# 使用示例:
#   bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --dry-run
#   bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --execute
#   bash scripts/whale_test.sh --suite release-regression --component whale --dry-run
# =============================================================================

set -euo pipefail

# ---- 参数解析 ----
STAGE=""
COMPONENT="whale"
MODULE=""
SUITE=""
DRY_RUN="true"
EXECUTE="false"

usage() {
    cat <<'EOF'
用法:
  whale_test.sh --stage <阶段> [--component <组件>] [--module <模块>] [--suite <套件>] [--execute|--dry-run]

参数:
  --stage      生命周期阶段 (必选，除非指定 --suite)
  --component  组件: whale|platform_shared|turtle|octopus (默认 whale)
  --module     子模块: ingest|message_pipeline|speed_layer|storage|shared_source|batch_layer
  --suite      回归套件: affected-regression|module-regression|chain-regression|release-regression
  --execute    实际执行测试 (默认 dry-run 安全模式)
  --dry-run    dry-run 模式 (默认开启，输出测试计划)

示例:
  bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --dry-run
  bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --execute
  bash scripts/whale_test.sh --suite release-regression --component whale --dry-run
  bash scripts/whale_test.sh --suite release-regression --component whale --execute
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --stage)
            STAGE="$2"
            shift 2
            ;;
        --component)
            COMPONENT="$2"
            shift 2
            ;;
        --module)
            MODULE="$2"
            shift 2
            ;;
        --suite)
            SUITE="$2"
            shift 2
            ;;
        --execute)
            DRY_RUN="false"
            EXECUTE="true"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            EXECUTE="false"
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            echo "未知参数: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# ---- 输入验证 ----

VALID_STAGES=("开发期验证" "构建期验证" "模块集成期验证" "跨模块联调期验证" "准生产依赖验证期" "部署前验收期" "发布后运维验证期")
VALID_COMPONENTS=("whale" "platform_shared" "turtle" "octopus")
VALID_MODULES=("ingest" "message_pipeline" "speed_layer" "storage" "shared_source" "batch_layer")
VALID_SUITES=("affected-regression" "module-regression" "chain-regression" "release-regression")

if [[ -z "$STAGE" && -z "$SUITE" ]]; then
    echo "错误: 必须指定 --stage 或 --suite" >&2
    usage
    exit 1
fi

if [[ -n "$STAGE" ]]; then
    stage_valid=0
    for s in "${VALID_STAGES[@]}"; do
        if [[ "$STAGE" == "$s" ]]; then
            stage_valid=1
            break
        fi
    done
    if [[ $stage_valid -eq 0 ]]; then
        echo "错误: 无效的生命周期阶段 '$STAGE'" >&2
        echo "有效值: ${VALID_STAGES[*]}" >&2
        exit 1
    fi
fi

comp_valid=0
for c in "${VALID_COMPONENTS[@]}"; do
    if [[ "$COMPONENT" == "$c" ]]; then
        comp_valid=1
        break
    fi
done
if [[ $comp_valid -eq 0 ]]; then
    echo "错误: 无效的组件 '$COMPONENT'" >&2
    echo "有效值: ${VALID_COMPONENTS[*]}" >&2
    exit 1
fi

if [[ -n "$MODULE" ]]; then
    if [[ "$COMPONENT" != "whale" ]]; then
        echo "错误: --module 仅在 --component whale 时有效" >&2
        exit 1
    fi
    mod_valid=0
    for m in "${VALID_MODULES[@]}"; do
        if [[ "$MODULE" == "$m" ]]; then
            mod_valid=1
            break
        fi
    done
    if [[ $mod_valid -eq 0 ]]; then
        echo "错误: 无效的模块 '$MODULE'" >&2
        echo "有效值: ${VALID_MODULES[*]}" >&2
        exit 1
    fi
fi

if [[ -n "$SUITE" ]]; then
    suite_valid=0
    for s in "${VALID_SUITES[@]}"; do
        if [[ "$SUITE" == "$s" ]]; then
            suite_valid=1
            break
        fi
    done
    if [[ $suite_valid -eq 0 ]]; then
        echo "错误: 无效的回归套件 '$SUITE'" >&2
        echo "有效值: ${VALID_SUITES[*]}" >&2
        exit 1
    fi
fi

# ---- 全局计数器 ----
PASS_COUNT=0
FAIL_COUNT=0
NOT_RUN_COUNT=0
declare -a NOT_RUN_ITEMS=()

# ---- 执行/输出辅助 ----

run_or_dry() {
    local desc="$1"
    local cmd="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "  [dry-run] $cmd"
        return 0
    else
        echo "  [execute] $cmd"
        if eval "$cmd" 2>&1; then
            echo "  · PASS: $desc"
            PASS_COUNT=$((PASS_COUNT + 1))
            return 0
        else
            echo "  · FAIL: $desc"
            FAIL_COUNT=$((FAIL_COUNT + 1))
            return 1
        fi
    fi
}

not_run() {
    local desc="$1"
    local reason="$2"
    echo "  · NOT_RUN: $reason — $desc"
    NOT_RUN_COUNT=$((NOT_RUN_COUNT + 1))
    NOT_RUN_ITEMS+=("[$reason] $desc")
}

# ---- 确认模式 ----
echo "============================================"
if [[ "$DRY_RUN" == "true" ]]; then
    echo "  Whale 测试计划 (dry-run)"
else
    echo "  Whale 测试执行 (execute)"
fi
echo "============================================"
echo ""
if [[ -n "$STAGE" ]]; then
    echo "生命周期阶段: $STAGE"
fi
echo "组件:          $COMPONENT"
if [[ -n "$MODULE" ]]; then
    echo "子模块:        $MODULE"
fi
if [[ -n "$SUITE" ]]; then
    echo "回归套件:      $SUITE"
fi
if [[ "$DRY_RUN" == "true" ]]; then
    echo "模式:          dry-run (不执行实际测试)"
else
    echo "模式:          execute (仅 must-run 低风险命令)"
fi
echo ""

# ---- 阶段函数 ----

# 构建期验证命令
print_build_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 构建期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        if [[ -z "$mod" ]]; then
            not_run "全量编译检查（未指定模块）" "OUT_OF_SCOPE"
        else
            run_or_dry "py_compile $mod" "python -m compileall src/whale/$mod/ -q"
            run_or_dry "ruff $mod" "python -m ruff check src/whale/$mod/"
            not_run "mypy $mod" "TOO_EXPENSIVE_FOR_THIS_RUN"
        fi
    elif [[ "$comp" == "platform_shared" ]]; then
        run_or_dry "ruff platform_shared" "python -m ruff check src/platform_shared/"
        not_run "mypy platform_shared" "TOO_EXPENSIVE_FOR_THIS_RUN"
    elif [[ "$comp" == "turtle" ]]; then
        run_or_dry "ruff turtle" "python -m ruff check src/turtle/"
    elif [[ "$comp" == "octopus" ]]; then
        run_or_dry "ruff octopus" "python -m ruff check src/octopus/"
    fi
    echo ""
}

# 开发期验证命令
print_dev_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 开发期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        if [[ -z "$mod" ]]; then
            not_run "全量 unit 测试" "TOO_EXPENSIVE_FOR_THIS_RUN"
        else
            run_or_dry "pytest unit -k '$mod'" "python -m pytest tests/unit/ -k '$mod' -q"
        fi
    elif [[ "$comp" == "platform_shared" ]]; then
        run_or_dry "platform_shared unit" "python -m pytest tests/unit/ -k 'platform_shared' -q"
    elif [[ "$comp" == "turtle" ]]; then
        run_or_dry "turtle import boundary" "python -m pytest tests/unit/test_turtle_octopus_import_boundary.py -q"
    elif [[ "$comp" == "octopus" ]]; then
        run_or_dry "octopus import boundary" "python -m pytest tests/unit/test_turtle_octopus_import_boundary.py -q"
    fi
    echo ""
}

# 模块集成期验证
print_module_integration_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 模块集成期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        if [[ -z "$mod" ]]; then
            not_run "全量集成测试" "TOO_EXPENSIVE_FOR_THIS_RUN"
        else
            run_or_dry "pytest integration -k '$mod'" "python -m pytest tests/integration/ -k '$mod' -q"
        fi
    elif [[ "$comp" == "platform_shared" ]]; then
        not_run "无独立集成测试" "OUT_OF_SCOPE"
    elif [[ "$comp" == "turtle" ]]; then
        not_run "turtle 当前多为空壳模块" "OUT_OF_SCOPE"
    elif [[ "$comp" == "octopus" ]]; then
        not_run "octopus 当前为空壳模块" "OUT_OF_SCOPE"
    fi
    echo ""
}

# 跨模块联调期验证
print_cross_module_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 跨模块联调期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        if [[ -z "$mod" || "$mod" == "ingest" ]]; then
            not_run "prodlike kafka/redis/pg" "MISSING_ENVIRONMENT"
        fi
        if [[ -z "$mod" || "$mod" == "message_pipeline" ]]; then
            not_run "Kafka message_pipeline E2E" "MISSING_ENVIRONMENT"
        fi
        if [[ -z "$mod" || "$mod" == "speed_layer" || "$mod" == "storage" ]]; then
            not_run "speed_layer pipeline" "MISSING_ENVIRONMENT"
        fi
    else
        not_run "无跨模块联调" "OUT_OF_SCOPE"
    fi
    echo ""
}

# 准生产依赖验证期
print_prodlike_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 准生产依赖验证期 ---"
    if [[ "$comp" == "whale" ]]; then
        not_run "l5 marker 测试" "MISSING_ENVIRONMENT"
        not_run "准生产依赖验证期 外部依赖探测" "MISSING_ENVIRONMENT"
    else
        not_run "无准生产依赖" "OUT_OF_SCOPE"
    fi
    echo ""
}

# 部署前验收期
print_deploy_commands() {
    local comp="$1"
    echo "--- 部署前验收期 ---"
    if [[ "$comp" == "whale" ]]; then
        not_run "field minimal smoke" "MISSING_ENVIRONMENT"
        not_run "field ready smoke 脚本" "MISSING_ENVIRONMENT"
    else
        not_run "无部署前验收" "OUT_OF_SCOPE"
    fi
    echo ""
}

# 发布后运维验证期
print_ops_commands() {
    local comp="$1"
    echo "--- 发布后运维验证期 ---"
    if [[ "$comp" == "whale" ]]; then
        not_run "健康检查 endpoint" "MANUAL_REQUIRED"
        not_run "监控告警验证" "MANUAL_REQUIRED"
    else
        not_run "无运维验证" "OUT_OF_SCOPE"
    fi
    echo ""
}

# 回归套件
print_suite_plan() {
    local suite="$1"
    local comp="$2"
    local mod="${3:-}"
    echo "--- 回归套件: $suite ---"
    case "$suite" in
        affected-regression)
            if [[ -n "$mod" ]]; then
                run_or_dry "affected unit -k '$mod'" "python -m pytest tests/unit/ -k '$mod' -q"
            else
                not_run "请指定 --module 以确定影响范围" "OUT_OF_SCOPE"
            fi
            ;;
        module-regression)
            if [[ "$comp" == "whale" && -n "$mod" ]]; then
                run_or_dry "module unit -k '$mod'" "python -m pytest tests/unit/ -k '$mod' -q"
                run_or_dry "module integration -k '$mod'" "python -m pytest tests/integration/ -k '$mod' -q"
            else
                run_or_dry "full unit" "python -m pytest tests/unit/ -q"
                not_run "full integration" "TOO_EXPENSIVE_FOR_THIS_RUN"
            fi
            ;;
        chain-regression)
            if [[ "$comp" == "whale" ]]; then
                if [[ "$mod" == "ingest" || -z "$mod" ]]; then
                    not_run "acquisition to Redis" "MISSING_ENVIRONMENT"
                    not_run "cache message E2E" "MISSING_ENVIRONMENT"
                fi
                if [[ "$mod" == "message_pipeline" || -z "$mod" ]]; then
                    not_run "Kafka E2E" "MISSING_ENVIRONMENT"
                fi
                if [[ "$mod" == "speed_layer" || "$mod" == "storage" || -z "$mod" ]]; then
                    run_or_dry "speed_layer pipeline" "python -m pytest tests/integration/test_speed_layer_*_pipeline.py -q"
                fi
            fi
            ;;
        release-regression)
            if [[ "$comp" == "whale" ]]; then
                run_or_dry "release (no slow/load/stress)" "python -m pytest -m 'not slow and not load and not stress' -q"
            fi
            ;;
    esac
    echo ""
}

# ---- 输出测试计划/执行 ----
echo "============================================"
echo "  测试计划"
echo "============================================"
echo ""

if [[ -n "$STAGE" ]]; then
    case "$STAGE" in
        开发期验证)
            print_dev_commands "$COMPONENT" "$MODULE"
            ;;
        构建期验证)
            print_build_commands "$COMPONENT" "$MODULE"
            ;;
        模块集成期验证)
            print_module_integration_commands "$COMPONENT" "$MODULE"
            ;;
        跨模块联调期验证)
            print_cross_module_commands "$COMPONENT" "$MODULE"
            ;;
        准生产依赖验证期)
            print_prodlike_commands "$COMPONENT" "$MODULE"
            ;;
        部署前验收期)
            print_deploy_commands "$COMPONENT"
            ;;
        发布后运维验证期)
            print_ops_commands "$COMPONENT"
            ;;
    esac
fi

if [[ -n "$SUITE" ]]; then
    print_suite_plan "$SUITE" "$COMPONENT" "$MODULE"
fi

# ---- 总结 ----
echo "============================================"
if [[ "$DRY_RUN" == "true" ]]; then
    echo "  dry-run 完成。以上命令均未实际执行。"
    echo "  如需执行，请添加 --execute 参数。"
else
    echo "  执行结果"
    echo "============================================"
    echo "  PASS:     $PASS_COUNT"
    echo "  FAIL:     $FAIL_COUNT"
    echo "  NOT_RUN:  $NOT_RUN_COUNT"
    if [[ $NOT_RUN_COUNT -gt 0 ]]; then
        echo ""
        echo "  NOT_RUN 详情:"
        for item in "${NOT_RUN_ITEMS[@]}"; do
            echo "    $item"
        done
    fi
fi
echo "============================================"

if [[ "$EXECUTE" == "true" && $FAIL_COUNT -gt 0 ]]; then
    exit 1
fi

exit 0
