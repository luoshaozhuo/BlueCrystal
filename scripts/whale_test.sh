#!/usr/bin/env bash
# =============================================================================
# Whale 测试统一入口 (dry-run)
#
# 第一轮只支持 dry-run 输出测试计划，不执行实际测试命令。
# 不启动外部环境，不执行危险命令。
#
# 参数:
#   --stage     生命周期阶段 (必选)
#   --component 组件名 (可选，默认 whale)
#   --module    子模块名 (可选)
#   --suite     回归套件 (可选)
#   --dry-run   输出测试计划 (默认开启)
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
# 组件取值: whale, source_lab, platform_shared, turtle, octopus
#
# 模块取值 (仅 whale 组件): ingest, message_pipeline, speed_layer, storage, shared_source, batch_layer
#
# 回归套件取值: affected-regression, module-regression, chain-regression, release-regression
#
# 使用示例:
#   bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --dry-run
#   bash scripts/whale_test.sh --suite release-regression --component whale --dry-run
# =============================================================================

set -euo pipefail

# ---- 参数解析 ----
STAGE=""
COMPONENT="whale"
MODULE=""
SUITE=""
DRY_RUN="true"

usage() {
    cat <<'EOF'
用法:
  whale_test.sh --stage <阶段> [--component <组件>] [--module <模块>] [--suite <套件>] [--dry-run]

参数:
  --stage      生命周期阶段 (必选，除非指定 --suite)
  --component  组件: whale|source_lab|platform_shared|turtle|octopus (默认 whale)
  --module     子模块: ingest|message_pipeline|speed_layer|storage|shared_source|batch_layer
  --suite      回归套件: affected-regression|module-regression|chain-regression|release-regression
  --dry-run    dry-run 模式 (默认开启)

示例:
  bash scripts/whale_test.sh --stage 开发期验证 --component whale --module storage --dry-run
  bash scripts/whale_test.sh --suite release-regression --component whale --dry-run
  bash scripts/whale_test.sh --stage 准生产依赖验证期 --component whale --dry-run
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
        --dry-run)
            DRY_RUN="true"
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
VALID_COMPONENTS=("whale" "source_lab" "platform_shared" "turtle" "octopus")
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

# ---- 确认 dry-run 模式 ----
echo "============================================"
echo "  Whale 测试计划 (dry-run)"
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
echo "模式:          dry-run (不执行实际测试)"
echo ""

# ---- 根据 stage 和 suite 生成测试计划 ----

# 构建期验证命令
print_build_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 构建期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        if [[ -z "$mod" ]]; then
            echo "  NOT_RUN: OUT_OF_SCOPE (未指定模块，不进行全量编译检查)"
        else
            echo "  1. python -m py_compile src/whale/$mod/ (dry-run)"
            echo "  2. ruff check src/whale/$mod/ (dry-run)"
            echo "  3. mypy src/whale/$mod/ (dry-run)"
        fi
    elif [[ "$comp" == "source_lab" ]]; then
        echo "  1. cmake -S tools/source_lab/native -B tools/source_lab/native/build (dry-run)"
        echo "  2. cmake --build tools/source_lab/native/build (dry-run)"
        echo "  3. ruff check tools/source_lab/ (dry-run)"
        echo "  4. mypy tools/source_lab/access tools/source_lab/field_*.py (dry-run)"
    elif [[ "$comp" == "platform_shared" ]]; then
        echo "  1. ruff check src/platform_shared/ (dry-run)"
        echo "  2. mypy src/platform_shared/ (dry-run)"
    elif [[ "$comp" == "turtle" ]]; then
        echo "  1. ruff check src/turtle/ (dry-run)"
    elif [[ "$comp" == "octopus" ]]; then
        echo "  1. ruff check src/octopus/ (dry-run)"
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
            echo "  MUST_RUN: pytest tests/unit/ -q (dry-run)"
            echo "  NOT_RUN: TOO_EXPENSIVE_FOR_THIS_ROUND (全量 unit 测试可能过多，建议指定 --module)"
        else
            echo "  MUST_RUN: pytest tests/unit/ -k '$mod' -q (dry-run)"
        fi
    elif [[ "$comp" == "source_lab" ]]; then
        echo "  MUST_RUN: pytest tools/source_lab/tests/ -q --timeout=120 (dry-run)"
    elif [[ "$comp" == "platform_shared" ]]; then
        echo "  MUST_RUN: pytest tests/unit/ -k 'platform_shared' -q (dry-run)"
    elif [[ "$comp" == "turtle" ]]; then
        echo "  MUST_RUN: pytest tests/unit/test_turtle_octopus_import_boundary.py -q (dry-run)"
    elif [[ "$comp" == "octopus" ]]; then
        echo "  MUST_RUN: pytest tests/unit/test_turtle_octopus_import_boundary.py -q (dry-run)"
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
            echo "  SHOULD_RUN: pytest tests/integration/ -q (dry-run)"
            echo "  NOT_RUN: TOO_EXPENSIVE_FOR_THIS_ROUND (全量集成测试可能过多)"
        else
            echo "  SHOULD_RUN: pytest tests/integration/ -k '$mod' -q (dry-run)"
        fi
    elif [[ "$comp" == "source_lab" ]]; then
        echo "  SHOULD_RUN: pytest tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py -q (dry-run)"
        echo "  SHOULD_RUN: pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py -q -s (dry-run)"
        echo "  SHOULD_RUN: pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py -q -s (dry-run)"
    elif [[ "$comp" == "platform_shared" ]]; then
        echo "  SHOULD_RUN: 无独立集成测试"
    elif [[ "$comp" == "turtle" ]]; then
        echo "  NOT_RUN: OUT_OF_SCOPE (turtle 当前多为空壳模块，暂不触发模块集成验证)"
    elif [[ "$comp" == "octopus" ]]; then
        echo "  NOT_RUN: OUT_OF_SCOPE (octopus 当前为空壳模块，暂不触发模块集成验证)"
    fi
    echo ""
}

# 跨模块联调期验证
print_cross_module_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 跨模块联调期验证 ---"
    if [[ "$comp" == "whale" ]]; then
        echo "  MANUAL: 需要 docker-compose 环境"
        if [[ -z "$mod" || "$mod" == "ingest" ]]; then
            echo "  MANUAL: pytest tests/integration/test_ingest_prodlike_*.py -k 'kafka_publish or redis_cache or postgres_runtime' -q (dry-run)"
        fi
        if [[ -z "$mod" || "$mod" == "message_pipeline" ]]; then
            echo "  MANUAL: pytest tests/integration/test_message_pipeline_kafka_e2e.py -q (dry-run)"
        fi
        if [[ -z "$mod" || "$mod" == "speed_layer" || "$mod" == "storage" ]]; then
            echo "  MANUAL: pytest tests/integration/test_speed_layer_*_pipeline.py -q (dry-run)"
        fi
    elif [[ "$comp" == "source_lab" ]]; then
        echo "  NOT_RUN: OUT_OF_SCOPE (source_lab 无跨模块联调阶段)"
    else
        echo "  NOT_RUN: OUT_OF_SCOPE"
    fi
    echo ""
}

# 准生产依赖验证期
print_prodlike_commands() {
    local comp="$1"
    local mod="${2:-}"
    echo "--- 准生产依赖验证期 ---"
    if [[ "$comp" == "whale" ]]; then
        echo "  MANUAL: 需要真实外部服务或 testcontainers"
        echo "  marker: l5"
        echo "  MANUAL: pytest -m l5 -q (dry-run)"
        echo "  MANUAL: bash scripts/run_whale_l5_external_dependency_probe.sh (dry-run)"
    elif [[ "$comp" == "source_lab" ]]; then
        echo "  MANUAL: 需要真实设备和协议"
        echo "  MANUAL: pytest tools/source_lab/tests/access/test_beckhoff_ads_real_protocol_readback.py -q (dry-run)"
    else
        echo "  NOT_RUN: OUT_OF_SCOPE"
    fi
    echo ""
}

# 部署前验收期
print_deploy_commands() {
    local comp="$1"
    echo "--- 部署前验收期 ---"
    if [[ "$comp" == "whale" ]]; then
        echo "  MANUAL: 需要 docker-compose 或目标环境"
        echo "  SHOULD_RUN: pytest tests/e2e/test_whale_field_minimal_smoke.py -q (dry-run)"
        echo "  SHOULD_RUN: bash scripts/run_whale_field_ready_smoke.sh (dry-run)"
    else
        echo "  NOT_RUN: OUT_OF_SCOPE"
    fi
    echo ""
}

# 发布后运维验证期
print_ops_commands() {
    local comp="$1"
    echo "--- 发布后运维验证期 ---"
    if [[ "$comp" == "whale" ]]; then
        echo "  MANUAL: 需要生产或 staging 环境"
        echo "  MANUAL: 健康检查 endpoint 验证"
        echo "  MANUAL: 监控告警验证"
    else
        echo "  NOT_RUN: OUT_OF_SCOPE"
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
            echo "  MUST_RUN: 本轮变更影响的测试 (需 code-implementer 根据变更范围确定)"
            if [[ -n "$mod" ]]; then
                echo "  建议: pytest tests/unit/ -k '$mod' -q (dry-run)"
            else
                echo "  建议: 先确定变更范围，再选择测试"
            fi
            ;;
        module-regression)
            if [[ "$comp" == "whale" && -n "$mod" ]]; then
                echo "  MUST_RUN: pytest tests/unit/ -k '$mod' -q (dry-run)"
                echo "  SHOULD_RUN: pytest tests/integration/ -k '$mod' -q (dry-run)"
            elif [[ "$comp" == "source_lab" ]]; then
                echo "  MUST_RUN: pytest tools/source_lab/tests/ -q --timeout=120 (dry-run)"
            else
                echo "  MUST_RUN: pytest tests/unit/ -q (dry-run)"
                echo "  SHOULD_RUN: pytest tests/integration/ -q (dry-run)"
            fi
            ;;
        chain-regression)
            echo "  上下游链路测试:"
            if [[ "$comp" == "whale" ]]; then
                if [[ "$mod" == "ingest" || -z "$mod" ]]; then
                    echo "  SHOULD_RUN: pytest tests/integration/test_ingest_source_acquisition_to_redis.py -q (dry-run)"
                    echo "  SHOULD_RUN: pytest tests/integration/test_ingest_source_cache_message_e2e.py -q (dry-run)"
                fi
                if [[ "$mod" == "message_pipeline" || -z "$mod" ]]; then
                    echo "  SHOULD_RUN: pytest tests/integration/test_message_pipeline_kafka_e2e.py -q (dry-run)"
                fi
                if [[ "$mod" == "speed_layer" || "$mod" == "storage" || -z "$mod" ]]; then
                    echo "  SHOULD_RUN: pytest tests/integration/test_speed_layer_*_pipeline.py -q (dry-run)"
                fi
            fi
            ;;
        release-regression)
            echo "  全量回归 (除 slow/load/stress):"
            if [[ "$comp" == "whale" ]]; then
                echo "  MUST_RUN: pytest -m 'not slow and not load and not stress' -q (dry-run)"
            elif [[ "$comp" == "source_lab" ]]; then
                echo "  MUST_RUN: pytest tools/source_lab/tests/ -q --timeout=120 (dry-run)"
            fi
            ;;
    esac
    echo ""
}

# ---- 输出测试计划 ----
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

echo "============================================"
echo "  dry-run 完成。以上命令均未实际执行。"
echo "  如需执行，请直接运行对应的 pytest/脚本命令。"
echo "============================================"

exit 0
