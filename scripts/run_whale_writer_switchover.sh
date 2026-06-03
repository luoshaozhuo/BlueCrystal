#!/usr/bin/env bash
# =============================================================================
# Whale Writer 无缝切换脚本
# =============================================================================
# 用途: 对 Whale speed_layer writers 执行无缝切换（新 consumer group 启动、
#       追平、旧 consumer group 延迟停止），最小化数据采集中断。
#
# 切换步骤:
#   1. 新 writer group 启动，订阅同一 topic
#   2. 等待新 group 从 offset/timestamp 追平到旧 group 的位置
#   3. 监控 consumer lag，确认 lag = 0
#   4. 切换 active 标记到新 group
#   5. 延迟停止旧 writer group（保留 group 用于回滚）
#
# 回滚步骤:
#   1. 停止新 writer group
#   2. 重新激活旧 writer group
#   3. 旧 group 从未提交的 offset 继续消费
#
# 证据等级: L4 (integration switchover)
# 环境依赖: Kafka broker (验证 consumer lag 需要)
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
TOPIC="${WHALE_TOPIC:-whale.ingest.state}"
OLD_GROUP="${WHALE_OLD_CONSUMER_GROUP:-whale-speed-layer-v1}"
NEW_GROUP="${WHALE_NEW_CONSUMER_GROUP:-whale-speed-layer-v2}"
BOOTSTRAP_SERVERS="${WHALE_KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
LAG_CHECK_INTERVAL="${WHALE_SWITCHOVER_LAG_INTERVAL:-5}"
LAG_CHECK_MAX_RETRIES="${WHALE_SWITCHOVER_LAG_MAX_RETRIES:-60}"
ACTION="${1:-switchover}"

# ---- 帮助 ----
usage() {
    cat <<'EOF'
用法: run_whale_writer_switchover.sh [ACTION]

ACTION:
  switchover    执行无缝切换（默认）
  rollback      回滚到旧 writer group
  status        查看 consumer group 状态
  -h, --help    显示帮助

环境变量:
  WHALE_TOPIC                  topic 名称 (默认 whale.ingest.state)
  WHALE_OLD_CONSUMER_GROUP     旧 consumer group (默认 whale-speed-layer-v1)
  WHALE_NEW_CONSUMER_GROUP     新 consumer group (默认 whale-speed-layer-v2)
  WHALE_KAFKA_BOOTSTRAP_SERVERS Kafka broker 地址 (默认 localhost:9092)
  WHALE_SWITCHOVER_LAG_INTERVAL lag 检查间隔秒数 (默认 5)
  WHALE_SWITCHOVER_LAG_MAX_RETRIES lag 检查最大重试次数 (默认 60)

示例:
  # 执行切换
  bash scripts/run_whale_writer_switchover.sh switchover

  # 查看状态
  bash scripts/run_whale_writer_switchover.sh status

  # 回滚
  bash scripts/run_whale_writer_switchover.sh rollback
EOF
    exit 0
}

if [[ "$ACTION" == "-h" ]] || [[ "$ACTION" == "--help" ]]; then
    usage
fi

# ---- 工具函数 ----
log_info() { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_pass() { echo -e "${GREEN}[PASS]${NC}  $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---- 检查 Kafka CLI 可用性 ----
check_kafka_cli() {
    if ! command -v kafka-consumer-groups.sh &>/dev/null; then
        log_warn "kafka-consumer-groups.sh 不可用，consumer lag 检查将被跳过"
        log_info "继续执行切换流程（不验证 lag = 0）"
        return 1
    fi
    return 0
}

# ---- 获取 consumer group 信息 ----
get_consumer_group_info() {
    local group="$1"
    if check_kafka_cli; then
        kafka-consumer-groups.sh \
            --bootstrap-server "$BOOTSTRAP_SERVERS" \
            --group "$group" \
            --describe 2>/dev/null || true
    else
        echo "  (Kafka CLI 不可用，无法获取 consumer group 信息)"
    fi
}

# ---- 检查 consumer lag ----
check_consumer_lag() {
    local group="$1"
    local total_lag=0

    if ! check_kafka_cli; then
        echo "0"
        return 0
    fi

    local lag_info
    lag_info=$(kafka-consumer-groups.sh \
        --bootstrap-server "$BOOTSTRAP_SERVERS" \
        --group "$group" \
        --describe 2>/dev/null || true)

    if [[ -z "$lag_info" ]] || echo "$lag_info" | grep -q "does not exist"; then
        echo "-1"
        return 0
    fi

    # 提取 LAG 列并求和
    while IFS= read -r line; do
        if echo "$line" | grep -qv "GROUP\|^$"; then
            local lag
            lag=$(echo "$line" | awk '{print $NF}' 2>/dev/null || echo "0")
            lag=${lag:-0}
            total_lag=$((total_lag + lag))
        fi
    done <<< "$lag_info"

    echo "$total_lag"
}

# ---- 确认操作 ----
confirm_action() {
    local msg="$1"
    echo ""
    log_warn "$msg"
    read -r -p "确认继续? (yes/no): " response
    if [[ "$response" != "yes" ]]; then
        log_info "操作取消"
        exit 0
    fi
}

# ---- 检查 producer 活跃性 ----
check_producer_active() {
    # 检查 topic 是否有最近的数据（确认 ingest 仍在发布）
    if check_kafka_cli; then
        local latest_offset
        latest_offset=$(kafka-run-class.sh kafka.tools.GetOffsetShell \
            --broker-list "$BOOTSTRAP_SERVERS" \
            --topic "$TOPIC" \
            --time -1 2>/dev/null | head -1) || true
        if [[ -n "$latest_offset" ]]; then
            log_info "topic $TOPIC 最新 offset: $latest_offset"
            return 0
        fi
    fi
    log_warn "无法确认 producer 活跃性，请手动确认 ingest 正在发布消息"
    return 1
}

# ---- 主流程 ----
main() {
    echo ""
    echo "============================================================"
    echo " Whale Writer 无缝切换"
    echo " 操作: $ACTION"
    echo " Topic: $TOPIC"
    echo " 旧 Group: $OLD_GROUP"
    echo " 新 Group: $NEW_GROUP"
    echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""

    case "$ACTION" in

    status)
        log_info "=== Consumer Group 状态 ==="
        echo ""
        log_info "旧 consumer group: $OLD_GROUP"
        get_consumer_group_info "$OLD_GROUP"
        echo ""
        log_info "新 consumer group: $NEW_GROUP"
        get_consumer_group_info "$NEW_GROUP"
        echo ""
        log_info "状态查询完成"
        ;;

    switchover)
        # ---- 步骤 1: 记录当前状态 ----
        log_info "步骤 1/6: 记录旧 consumer group 当前状态"
        get_consumer_group_info "$OLD_GROUP"
        local old_lag
        old_lag=$(check_consumer_lag "$OLD_GROUP")
        log_info "旧 group 当前 lag: $old_lag"

        # ---- 步骤 2: 确认 producer 活跃 ----
        log_info "步骤 2/6: 确认 ingest producer 活跃"
        check_producer_active || true

        # ---- 步骤 3: 启动新 writer group ----
        log_info "步骤 3/6: 启动新 writer group ($NEW_GROUP)"
        log_info "新 consumer group 开始消费 topic $TOPIC"
        log_info ""
        log_info "手动启动命令参考:"
        log_info "  WHALE_KAFKA_CONSUMER_GROUP=$NEW_GROUP \\"
        log_info "  whale speed-layer run --mode prodlike \\"
        log_info "    --config config/whale/speed_layer.writers.example.yaml"
        log_info ""
        confirm_action "请确认新 writer group 已成功启动?"

        # ---- 步骤 4: 等待追平 ----
        log_info "步骤 4/6: 等待新 consumer group 追平"
        local retry=0
        local new_lag=-1

        if check_kafka_cli; then
            while [[ $retry -lt $LAG_CHECK_MAX_RETRIES ]]; do
                sleep "$LAG_CHECK_INTERVAL"
                retry=$((retry + 1))
                new_lag=$(check_consumer_lag "$NEW_GROUP")
                log_info "轮次 $retry/$LAG_CHECK_MAX_RETRIES: 新 group lag = $new_lag"

                if [[ "$new_lag" == "-1" ]]; then
                    log_info "新 consumer group 尚未创建，等待中..."
                    continue
                fi

                if [[ "$new_lag" -le 0 ]]; then
                    log_pass "新 consumer group lag = 0，已追平"
                    break
                fi
            done

            if [[ "$new_lag" -gt 0 ]] || [[ "$new_lag" == "-1" ]]; then
                log_warn "新 consumer group 未能在 ${LAG_CHECK_MAX_RETRIES}x${LAG_CHECK_INTERVAL}s 内追平"
                log_warn "当前 lag = $new_lag，请手动检查"
                confirm_action "仍然继续切换?"
            fi
        else
            log_info "无法检查 lag (Kafka CLI 不可用)，等待 ${LAG_CHECK_INTERVAL}s 后继续..."
            sleep "$LAG_CHECK_INTERVAL"
        fi

        # ---- 步骤 5: 切换 active ----
        log_info "步骤 5/6: 切换 active 到新 writer group"
        log_info "新 consumer group ($NEW_GROUP) 现已成为 active"
        log_info ""
        log_info "负载均衡/路由切换:"
        log_info "  如使用 Nginx/K8s Service, 更新 upstream 指向新 pod"
        log_info "  如使用 DNS, 更新 CNAME 记录"
        log_info ""
        confirm_action "请确认流量已切换到新 writer group?"

        # ---- 步骤 6: 延迟停止旧 writer group ----
        log_info "步骤 6/6: 延迟停止旧 writer group ($OLD_GROUP)"
        log_info "等待 30 秒以确保新 group 稳定处理..."
        sleep 30

        local final_old_lag
        final_old_lag=$(check_consumer_lag "$OLD_GROUP")
        log_info "旧 group 最终 lag: $final_old_lag"

        log_info ""
        log_info "手动停止旧 writer group 命令参考:"
        log_info "  1. 发送 SIGTERM 信号"
        log_info "     kill -TERM \$(pgrep -f 'whale speed-layer.*$OLD_GROUP')"
        log_info ""
        log_info "  2. 或通过 whale CLI 优雅关闭"
        log_info "     whale speed-layer stop --group $OLD_GROUP"
        log_info ""

        log_warn "保留旧 consumer group ($OLD_GROUP) 用于回滚!"
        log_warn "不要删除 consumer group 或重置 offset"
        log_info ""

        log_pass "无缝切换完成"
        log_info ""
        log_info "=== 切换后状态 ==="
        get_consumer_group_info "$NEW_GROUP"
        ;;

    rollback)
        log_info "=== 回滚到旧 writer group ==="
        echo ""
        confirm_action "确认回滚到 $OLD_GROUP?"

        # ---- 步骤 1: 停止新 group ----
        log_info "步骤 1/3: 停止新 writer group ($NEW_GROUP)"
        log_info "手动停止命令:"
        log_info "  kill -TERM \$(pgrep -f 'whale speed-layer.*$NEW_GROUP')"
        confirm_action "请确认新 writer group 已停止?"

        # ---- 步骤 2: 重新激活旧 group ----
        log_info "步骤 2/3: 重新激活旧 writer group ($OLD_GROUP)"
        log_info "旧 consumer group 从未提交的 offset 继续消费"
        log_info ""
        log_info "手动启动命令:"
        log_info "  WHALE_KAFKA_CONSUMER_GROUP=$OLD_GROUP \\"
        log_info "  whale speed-layer run --mode prodlike"
        log_info ""
        confirm_action "请确认旧 writer group 已重新启动?"

        # ---- 步骤 3: 验证 ----
        log_info "步骤 3/3: 验证旧 group 运行状态"
        sleep 10
        get_consumer_group_info "$OLD_GROUP"
        log_info ""
        log_pass "回滚完成"
        ;;

    *)
        log_error "未知操作: $ACTION"
        usage
        ;;
    esac
}

main "$@"
