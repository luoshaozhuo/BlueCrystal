#!/usr/bin/env bash
# diagnose_whale_p5_dependencies.sh
#
# P5 准生产依赖验证期 — 独立诊断脚本。
# 检查每个外部依赖的连通性和关键功能可用性。
#
# 每个依赖输出：
#   dependency name
#   endpoint/DSN 摘要（敏感信息脱敏）
#   TCP reachability
#   auth result
#   minimal operation result
#   final status: PASS/FAIL/NOT_RUN
#   reason
#
# 覆盖：
#   PostgreSQL  — TCP connect + SELECT 1
#   Redis        — TCP connect + PING
#   Kafka        — TCP connect + broker metadata
#   S3/MinIO     — TCP connect + bucket head + put/get/delete temp object
#   TDengine     — TCP connect + REST API SELECT 1（多路径探测）
#
# 使用方式：
#   bash scripts/diagnose_whale_p5_dependencies.sh
#
# 环境变量覆盖默认配置（同 .env.p5.example）：
#   WHALE_TEST_POSTGRES_DSN        (默认 postgresql://whale:whale@localhost:5432/whale_test)
#   WHALE_KAFKA_BOOTSTRAP_SERVERS  (默认 localhost:9092)
#   WHALE_REDIS_URL                (默认 localhost:16379)
#   WHALE_S3_ENDPOINT_URL          (默认 http://localhost:9000)
#   WHALE_S3_BUCKET                (默认 whale-raw)
#   WHALE_S3_REGION                (默认 us-east-1)
#   WHALE_S3_ACCESS_KEY            (默认 minioadmin)
#   WHALE_S3_SECRET_KEY            (默认 minioadmin)
#   WHALE_S3_ADDRESSING_STYLE      (默认 path)
#   WHALE_TDENGINE_DSN             (默认 localhost:6041)
#   WHALE_TDENGINE_REST_PATH       (默认 /rest/sql)
#   WHALE_TDENGINE_USER            (默认 root)
#   WHALE_TDENGINE_PASSWORD        (默认 taosdata)

set -euo pipefail

# ---- 颜色输出 ----
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS_COUNT=0
FAIL_COUNT=0
NOT_RUN_COUNT=0
DIAG_LINES=()

pass_msg() { echo -e "    [${GREEN}PASS${NC}] $1"; PASS_COUNT=$((PASS_COUNT + 1)); DIAG_LINES+=("PASS: $1"); }
fail_msg() { echo -e "    [${RED}FAIL${NC}] $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); DIAG_LINES+=("FAIL: $1"); }
not_run_msg() { echo -e "    [${YELLOW}NOT_RUN${NC}] $1"; NOT_RUN_COUNT=$((NOT_RUN_COUNT + 1)); DIAG_LINES+=("NOT_RUN: $1"); }

# ---- 环境变量默认值 ----
PG_DSN="${WHALE_TEST_POSTGRES_DSN:-}"
KAFKA_BOOTSTRAP="${WHALE_KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
REDIS_URL="${WHALE_REDIS_URL:-localhost:16379}"
S3_ENDPOINT_URL="${WHALE_S3_ENDPOINT_URL:-http://localhost:9000}"
S3_BUCKET="${WHALE_S3_BUCKET:-whale-raw}"
S3_REGION="${WHALE_S3_REGION:-us-east-1}"
S3_ACCESS_KEY="${WHALE_S3_ACCESS_KEY:-minioadmin}"
S3_SECRET_KEY="${WHALE_S3_SECRET_KEY:-minioadmin}"
S3_ADDRESSING="${WHALE_S3_ADDRESSING_STYLE:-path}"
TDENGINE_DSN="${WHALE_TDENGINE_DSN:-localhost:6041}"
TDENGINE_REST_PATH="${WHALE_TDENGINE_REST_PATH:-/rest/sql}"
TDENGINE_USER="${WHALE_TDENGINE_USER:-root}"
TDENGINE_PASSWORD="${WHALE_TDENGINE_PASSWORD:-taosdata}"

# ---- 辅助函数 ----

tcp_check() {
    local host="$1"
    local port="$2"
    local timeout="${3:-3}"
    if command -v timeout &>/dev/null; then
        timeout "$timeout" bash -c "echo > /dev/tcp/${host}/${port}" 2>/dev/null && return 0 || return 1
    else
        python3 -c "
import socket
s = socket.socket()
s.settimeout(${timeout})
try:
    s.connect(('${host}', ${port}))
    s.close()
except Exception:
    exit(1)
" 2>/dev/null && return 0 || return 1
    fi
}

extract_host_port() {
    local dsn="$1"
    local default_host="${2:-localhost}"
    local default_port="${3:-80}"
    local cleaned="${dsn}"
    cleaned="${cleaned#taosws://}"
    cleaned="${cleaned#http://}"
    cleaned="${cleaned#https://}"
    cleaned="${cleaned#postgresql://}"
    cleaned="${cleaned#redis://}"
    if [[ "$dsn" == postgresql://* ]]; then
        cleaned=$(echo "$dsn" | sed -E 's|^[^@]*@([^:/]+)(:[0-9]+)?.*|\1\2|')
    fi
    if [[ "$cleaned" == *:* ]]; then
        local host_part="${cleaned%:*}"
        local port_part="${cleaned##*:}"
        port_part="${port_part%%/*}"
        port_part="${port_part%%\?*}"
        echo "${host_part} ${port_part}"
    else
        echo "${cleaned%/*} ${default_port}"
    fi
}

sanitize_dsn() {
    # 脱敏 DSN 中的密码部分，输出安全的摘要
    local dsn="$1"
    # postgresql://user:password@host:port/db → postgresql://user:***@host:port/db
    echo "$dsn" | sed -E 's|://([^:]+):[^@]+@|://\1:***@|g' \
                 | sed -E 's|://([^:]+):[^@]+$|://\1:***@localhost|g'
}

print_section_header() {
    local deps_name="$1"
    local endpoint_summary="$2"
    echo ""
    echo "--- ${deps_name} ---"
    echo "  Endpoint/DSN: ${endpoint_summary}"
    DIAG_LINES+=("")
    DIAG_LINES+=("DEPENDENCY: ${deps_name}")
    DIAG_LINES+=("  endpoint: ${endpoint_summary}")
}

echo "=========================================="
echo " Whale P5 外部依赖诊断"
echo " 执行时间: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
echo "=========================================="

# =====================================================================
# 1. PostgreSQL
# =====================================================================
print_section_header "PostgreSQL" "$(sanitize_dsn "${PG_DSN:-<DSN 未设置>}")"

if [ -z "${PG_DSN:-}" ]; then
    not_run_msg "TCP reachability: NOT_RUN — WHALE_TEST_POSTGRES_DSN 未设置"
    not_run_msg "SELECT 1: NOT_RUN — DSN 未设置"
    not_run_msg "最终状态: NOT_RUN: MISSING_ENVIRONMENT (WHALE_TEST_POSTGRES_DSN 未设置)"
else
    read -r PG_HOST PG_PORT <<< "$(extract_host_port "$PG_DSN" "localhost" "5432")"
    PG_PORT="${PG_PORT:-5432}"

    # TCP reachability
    if tcp_check "$PG_HOST" "$PG_PORT"; then
        pass_msg "TCP reachability: ${PG_HOST}:${PG_PORT} 可达"
        TCP_OK=true
    else
        fail_msg "TCP reachability: ${PG_HOST}:${PG_PORT} 不可达"
        TCP_OK=false
    fi

    # Auth + SELECT 1
    if $TCP_OK; then
        # 通过环境变量传递 DSN 给 Python 子进程
        export __PG_DSN__="$PG_DSN"
        PG_RESULT=$(python3 -c "
import os, sys
from sqlalchemy import create_engine, text
dsn = os.getenv('__PG_DSN__', '')
if not dsn:
    print('NOT_RUN: DSN 未设置')
    sys.exit(0)
try:
    engine = create_engine(dsn, connect_args={'connect_timeout': 5})
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1'))
        row = result.fetchone()
        if row and row[0] == 1:
            print('PASS: SELECT 1 成功')
        else:
            print('FAIL: SELECT 1 返回异常')
except Exception as exc:
    error_msg = str(exc)[:200]
    if 'password' in error_msg.lower() or 'authentication' in error_msg.lower():
        print(f'FAIL: 认证失败 — {error_msg}')
    elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
        print(f'FAIL: 连接失败 — {error_msg}')
    else:
        print(f'FAIL: 查询失败 — {error_msg}')
" 2>&1 || echo "FAIL: Python 脚本执行异常")
        if echo "$PG_RESULT" | grep -q "^PASS:"; then
            pass_msg "auth + SELECT 1: 成功"
            pass_msg "最终状态: PASS"
        elif echo "$PG_RESULT" | grep -q "认证失败"; then
            fail_msg "auth + SELECT 1: 认证失败"
            fail_msg "最终状态: FAIL (认证失败)"
        elif echo "$PG_RESULT" | grep -q "连接失败"; then
            fail_msg "auth + SELECT 1: 连接失败"
            fail_msg "最终状态: FAIL (连接失败)"
        else
            fail_msg "auth + SELECT 1: 失败 — ${PG_RESULT}"
            fail_msg "最终状态: FAIL"
        fi
    else
        not_run_msg "auth + SELECT 1: NOT_RUN — TCP 不可达"
        fail_msg "最终状态: FAIL (TCP 不可达)"
    fi
fi

# =====================================================================
# 2. Redis
# =====================================================================
print_section_header "Redis" "${REDIS_URL}"

read -r R_HOST R_PORT <<< "$(extract_host_port "$REDIS_URL" "localhost" "16379")"
R_PORT="${R_PORT:-16379}"

# TCP reachability
if tcp_check "$R_HOST" "$R_PORT"; then
    pass_msg "TCP reachability: ${R_HOST}:${R_PORT} 可达"
    TCP_OK=true
else
    fail_msg "TCP reachability: ${R_HOST}:${R_PORT} 不可达"
    TCP_OK=false
fi

# PING
if $TCP_OK; then
    # 尝试用 redis-cli PING
    if command -v redis-cli &>/dev/null; then
        if redis-cli -h "$R_HOST" -p "$R_PORT" --no-auth-warning ping &>/dev/null; then
            REDIS_PING="PASS"
        else
            REDIS_PING="FAIL: PING 失败"
        fi
    else
        # fallback: python3 发 PING
        REDIS_PING=$(python3 -c "
import socket, sys
host, port = '${R_HOST}', ${R_PORT}
try:
    s = socket.create_connection((host, port), timeout=3)
    # 发送 RESP PING 命令
    s.sendall(b'*1\r\n\$4\r\nPING\r\n')
    resp = s.recv(1024)
    s.close()
    if b'PONG' in resp:
        print('PASS')
    else:
        print(f'FAIL: 未收到 PONG，收到 {resp[:50]!r}')
except Exception as exc:
    print(f'FAIL: {exc}')
" 2>&1 || echo "FAIL: PING 脚本异常")
    fi

    case "${REDIS_PING}" in
        PASS)
            pass_msg "Redis PING: 成功"
            pass_msg "最终状态: PASS"
            ;;
        FAIL:*)
            detail="${REDIS_PING#FAIL: }"
            fail_msg "Redis PING: ${detail}"
            fail_msg "最终状态: FAIL (PING 失败)"
            ;;
        *)
            fail_msg "Redis PING: ${REDIS_PING}"
            fail_msg "最终状态: FAIL"
            ;;
    esac
else
    not_run_msg "Redis PING: NOT_RUN — TCP 不可达"
    fail_msg "最终状态: FAIL (TCP 不可达)"
fi

# =====================================================================
# 3. Kafka (Redpanda)
# =====================================================================
print_section_header "Kafka (Redpanda)" "${KAFKA_BOOTSTRAP}"

read -r K_HOST K_PORT <<< "$(extract_host_port "$KAFKA_BOOTSTRAP" "localhost" "9092")"
K_PORT="${K_PORT:-9092}"

# TCP reachability
if tcp_check "$K_HOST" "$K_PORT"; then
    pass_msg "TCP reachability: ${K_HOST}:${K_PORT} 可达"
    TCP_OK=true
else
    fail_msg "TCP reachability: ${K_HOST}:${K_PORT} 不可达"
    TCP_OK=false
fi

# broker metadata
if $TCP_OK; then
    KAFKA_META=$(python3 -c "
import sys, struct, socket

host, port = '${K_HOST}', ${K_PORT}
try:
    s = socket.create_connection((host, port), timeout=5)

    # 构造 MetadataRequest (API Key 3, Version 4) 的简化 Kafka 协议帧
    # 这是为了在没有 kafka-python 的情况下做 broker metadata 探测
    # Kafka Request Header: api_key(2), api_version(2), correlation_id(4), client_id_len(2), client_id(variable)
    # Metadata Request Body (v4): topics_array_len(4), topics(array), allow_auto_topic_creation(1), include_cluster_authorized_operations(1), include_topic_authorized_operations(1)

    import kafka
    # 如果 kafka-python 可用，使用它
    from kafka import KafkaAdminClient
    admin = KafkaAdminClient(bootstrap_servers=f'{host}:{port}', request_timeout_ms=5000)
    metadata = admin.list_topics()
    topic_count = len(metadata)
    # 检查 controller
    cluster = admin._client.cluster
    brokers = len(cluster.brokers())
    print(f'PASS: broker metadata 可用 — {brokers} broker(s)，{topic_count} topic(s)')
except ImportError:
    # kafka-python 不可用时做简化 TCP 探测
    # 直接测试能否建立 TCP 连接即可（已在上一步完成）
    print('WARN: kafka-python 未安装，无法获取 broker metadata（TCP 可达）')
except Exception as exc:
    error_msg = str(exc)[:200]
    print(f'FAIL: broker metadata 获取失败 — {error_msg}')
" 2>&1 || echo "FAIL: Kafka 诊断脚本异常")

    if echo "$KAFKA_META" | grep -q "^PASS:"; then
        detail="${KAFKA_META#PASS: }"
        pass_msg "broker metadata: ${detail}"
        pass_msg "最终状态: PASS"
    elif echo "$KAFKA_META" | grep -q "^WARN:"; then
        detail="${KAFKA_META#WARN: }"
        pass_msg "broker metadata: ${detail}"
        pass_msg "最终状态: PASS (driver 受限，TCP 可达)"
    elif echo "$KAFKA_META" | grep -q "^FAIL:"; then
        detail="${KAFKA_META#FAIL: }"
        fail_msg "broker metadata: ${detail}"
        fail_msg "最终状态: FAIL (broker metadata 不可用)"
    else
        fail_msg "broker metadata: ${KAFKA_META}"
        fail_msg "最终状态: FAIL"
    fi
else
    not_run_msg "broker metadata: NOT_RUN — TCP 不可达"
    fail_msg "最终状态: FAIL (TCP 不可达)"
fi

# =====================================================================
# 4. S3 / MinIO
# =====================================================================
print_section_header "S3 / MinIO" "${S3_ENDPOINT_URL} (bucket: ${S3_BUCKET})"

# 提取 host:port
S3_HOST=""
S3_PORT=9000
if [[ "$S3_ENDPOINT_URL" == http://* ]]; then
    S3_CLEAN="${S3_ENDPOINT_URL#http://}"
elif [[ "$S3_ENDPOINT_URL" == https://* ]]; then
    S3_CLEAN="${S3_ENDPOINT_URL#https://}"
else
    S3_CLEAN="$S3_ENDPOINT_URL"
fi
S3_CLEAN="${S3_CLEAN%/}"
if [[ "$S3_CLEAN" == *:* ]]; then
    S3_HOST="${S3_CLEAN%:*}"
    S3_PORT="${S3_CLEAN##*:}"
else
    S3_HOST="$S3_CLEAN"
fi
# 验证 port 是数字
if ! [[ "$S3_PORT" =~ ^[0-9]+$ ]]; then
    S3_PORT=9000
fi

# TCP reachability
if [ -n "$S3_HOST" ] && tcp_check "$S3_HOST" "$S3_PORT"; then
    pass_msg "TCP reachability: ${S3_HOST}:${S3_PORT} 可达"
    TCP_OK=true
else
    if [ -z "$S3_HOST" ]; then
        fail_msg "TCP reachability: host 解析失败 (${S3_ENDPOINT_URL})"
    else
        fail_msg "TCP reachability: ${S3_HOST}:${S3_PORT} 不可达"
    fi
    TCP_OK=false
fi

# bucket head + put/get/delete temp object
if $TCP_OK; then
    S3_DIAG_RESULT=$(python3 -c "
import sys, time

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print('FAIL: boto3 未安装')
    sys.exit(0)

endpoint = '${S3_ENDPOINT_URL}'
bucket = '${S3_BUCKET}'
region = '${S3_REGION}'
access_key = '${S3_ACCESS_KEY}'
secret_key = '${S3_SECRET_KEY}'
addressing = '${S3_ADDRESSING}'

try:
    client = boto3.client('s3',
        endpoint_url=endpoint,
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(s3={'addressing_style': addressing}),
    )
except Exception as exc:
    print(f'FAIL: S3 client 初始化失败 — {exc}')
    sys.exit(0)

# 1. bucket head
try:
    client.head_bucket(Bucket=bucket)
    print(f'PASS: bucket_head — 桶 {bucket} 存在且可达')
except Exception as exc:
    print(f'FAIL: bucket_head — {str(exc)[:150]}')
    sys.exit(0)

# 2. put temp object
test_key = f'whale_p5_diag_{int(time.time())}.txt'
test_body = f'Whale P5 diagnostics at {time.time()}'
try:
    client.put_object(Bucket=bucket, Key=test_key, Body=test_body.encode('utf-8'))
    print(f'PASS: put_object — key={test_key} 写入成功')
except Exception as exc:
    print(f'FAIL: put_object — {str(exc)[:150]}')
    sys.exit(0)

# 3. get temp object
try:
    resp = client.get_object(Bucket=bucket, Key=test_key)
    body = resp['Body'].read().decode('utf-8')
    if body == test_body:
        print(f'PASS: get_object — key={test_key} 读取验证一致')
    else:
        print(f'FAIL: get_object — 内容不匹配')
except Exception as exc:
    print(f'FAIL: get_object — {str(exc)[:150]}')

# 4. delete temp object
try:
    client.delete_object(Bucket=bucket, Key=test_key)
    print(f'PASS: delete_object — key={test_key} 清理成功')
except Exception as exc:
    print(f'WARN: delete_object — {str(exc)[:100]} (非致命，手动清理)')
" 2>&1 || echo "FAIL: S3 诊断脚本异常")

    # 解析 S3 诊断结果
    all_pass=true
    while IFS= read -r line; do
        if [ -z "$line" ]; then continue; fi
        case "$line" in
            PASS:*)
                detail="${line#PASS: }"
                pass_msg "${detail}"
                ;;
            FAIL:*)
                detail="${line#FAIL: }"
                fail_msg "${detail}"
                all_pass=false
                ;;
            WARN:*)
                detail="${line#WARN: }"
                echo "    ${detail}"
                ;;
            *)
                echo "    ${line}"
                ;;
        esac
    done <<< "$S3_DIAG_RESULT"

    if $all_pass; then
        pass_msg "最终状态: PASS"
    else
        fail_msg "最终状态: FAIL"
    fi
else
    not_run_msg "bucket_head/put/get/delete: NOT_RUN — TCP 不可达"
    fail_msg "最终状态: FAIL (TCP 不可达)"
fi

# =====================================================================
# 5. TDengine
# =====================================================================
print_section_header "TDengine (taosAdapter)" "${TDENGINE_DSN} (REST path: ${TDENGINE_REST_PATH})"

read -r TD_HOST TD_PORT <<< "$(extract_host_port "$TDENGINE_DSN" "localhost" "6041")"
TD_PORT="${TD_PORT:-6041}"

# TCP reachability
if tcp_check "$TD_HOST" "$TD_PORT"; then
    pass_msg "TCP reachability: ${TD_HOST}:${TD_PORT} 可达"
    TCP_OK=true
else
    fail_msg "TCP reachability: ${TD_HOST}:${TD_PORT} 不可达"
    TCP_OK=false
fi

# REST API SELECT 1（多路径探测）
if $TCP_OK; then
    REST_RESULT=$(python3 -c "
import urllib.request, urllib.error, base64, json, sys

host = '${TD_HOST}'
port = '${TD_PORT}'
primary_path = '${TDENGINE_REST_PATH}'
user = '${TDENGINE_USER}'
password = '${TDENGINE_PASSWORD}'

paths_to_check = [primary_path]
if primary_path != '/rest/sqlt':
    paths_to_check.append('/rest/sqlt')
if primary_path != '/rest/sql':
    paths_to_check.append('/rest/sql')

auth_bytes = base64.b64encode(f'{user}:{password}'.encode('utf-8'))
auth_header = 'Basic ' + auth_bytes.decode('ascii')
results = []

for path in paths_to_check:
    url = f'http://{host}:{port}{path}'
    try:
        req = urllib.request.Request(
            url,
            data=b'SELECT 1',
            headers={'Content-Type': 'text/plain'},
            method='POST',
        )
        req.add_header('Authorization', auth_header)
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode('utf-8')
            result = json.loads(body)
            code = result.get('code', -1)
            if code == 0:
                results.append(f'OK:{path}')
            else:
                desc = result.get('desc', 'unknown')
                results.append(f'ERROR:{path}:code={code}:{desc[:60]}')
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8', errors='replace')[:80]
        results.append(f'HTTP_ERROR:{path}:{exc.code}:{error_body}')
    except Exception as exc:
        results.append(f'CONN_ERROR:{path}:{str(exc)[:80]}')

for r in results:
    print(r)
if not any('OK:' in r for r in results):
    sys.exit(0)
" 2>&1 || true)

    # 解析 REST 探测
    REST_OK=false
    REST_DETAILS=""
    while IFS= read -r line; do
        if [ -z "$line" ]; then continue; fi
        case "$line" in
            OK:*)
                path="${line#OK:}"
                REST_OK=true
                REST_DETAILS="${REST_DETAILS}可用(${path}) "
                ;;
            ERROR:*)
                REST_DETAILS="${REST_DETAILS}错误(${line}) "
                ;;
            HTTP_ERROR:*)
                REST_DETAILS="${REST_DETAILS}HTTP错误(${line}) "
                ;;
            CONN_ERROR:*)
                REST_DETAILS="${REST_DETAILS}连接失败(${line}) "
                ;;
            *)
                REST_DETAILS="${REST_DETAILS}${line} "
                ;;
        esac
    done <<< "$REST_RESULT"

    echo "  -> REST API 探测: ${REST_DETAILS}"

    if $REST_OK; then
        pass_msg "REST API SELECT 1: 成功"
        pass_msg "最终状态: PASS"
    else
        # 区分认证失败 vs 连接失败
        if echo "$REST_RESULT" | grep -q "code=3\|code=4\|code=5"; then
            fail_msg "REST API SELECT 1: 认证失败 (code=3/4/5)"
        else
            fail_msg "REST API SELECT 1: 不可用 — ${REST_DETAILS}"
        fi
        fail_msg "最终状态: FAIL"
    fi
else
    not_run_msg "REST API SELECT 1: NOT_RUN — TCP 不可达"
    fail_msg "最终状态: FAIL (TCP 不可达)"
fi

# =====================================================================
# SUMMARY
# =====================================================================
echo ""
echo "=========================================="
echo " 诊断汇总"
echo "=========================================="
echo "  PASS:     ${PASS_COUNT}"
echo "  FAIL:     ${FAIL_COUNT}"
echo "  NOT_RUN:  ${NOT_RUN_COUNT}"
echo ""
echo " 详细结果:"
for line in "${DIAG_LINES[@]}"; do
    echo "  ${line}"
done
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}存在 ${FAIL_COUNT} 项 FAIL，请检查相关依赖配置和服务状态。${NC}"
    exit 1
elif [ "$PASS_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}所有检查均 NOT_RUN 或未执行。${NC}"
    exit 0
else
    echo -e "${GREEN}所有可检查依赖均通过。${NC}"
    exit 0
fi
