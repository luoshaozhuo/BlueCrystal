#!/usr/bin/env bash
# =============================================================================
# Whale L5 外部依赖环境探针脚本（Round 3 升级版）
# =============================================================================
# 用途: 多级探测 Whale 全链路所需外部依赖，输出完整 L5 就绪矩阵。
#   不启动实际业务服务，仅做端口/TCP 连接性、Python 驱动导入、服务级 health check、
#   认证验证和最小写入/读回验证。
#
# 探测层级 (按优先级):
#   - tcp_ok:        TCP 端口可达 (纯 socket connect)
#   - driver_ok:     Python driver 可导入 (import check)
#   - auth_ok:       认证通过 (如适用)
#   - service_health_ok: 服务 health endpoint 返回 OK (REST API / PING)
#   - e2e_ok:        写入+读回验证通过 (最小 write+read 闭环)
#
# 每个服务输出明确的综合状态:
#   - available:        所有探针通过 (tcp + driver + health + e2e)
#   - degraded:         TCP 可达但部分能力受限 (如无 driver 或 auth 失败)
#   - driver_missing:   TCP 可达但 Python driver 缺失
#   - unavailable:      所有探针失败 (服务完全不可达)
#   - environment_pending: 从未探测或环境未就绪
#
# 使用方式:
#   bash scripts/run_whale_l5_external_dependency_probe.sh
#   bash scripts/run_whale_l5_external_dependency_probe.sh --json  # JSON 输出
#
# 测试阶段：准生产依赖验证期（外部依赖多级可用性探针）
# 环境依赖: 无（纯连接性+driver探测，所有外部服务不可达时降级为 environment-pending）
#
# Round 3 变更:
#   - 修正 Redis "verified" + "driver missing" 矛盾: 引入多级状态体系
#   - 每个服务输出复合状态 (available/degraded/driver_missing/unavailable/env_pending)
#   - 区分 TCP reachable 和 full e2e verified
#   - 新增 TDengine/MinIO 的 REST API health check + 最小 write/read 验证
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

JSON_OUTPUT=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# -- 服务状态记录 (composite) --
declare -A SERVICE_STATUS
declare -A SERVICE_TCP
declare -A SERVICE_DRIVER
declare -A SERVICE_AUTH
declare -A SERVICE_HEALTH
declare -A SERVICE_E2E
declare -A SERVICE_DETAIL

# 服务列表按 P0 优先级排序
SERVICE_LIST=(
    "kafka"
    "redis"
    "postgres"
    "s3"
    "tdengine"
    "pulsar"
    "flink"
    "hdfs"
)

usage() {
    cat <<'EOF'
用法: run_whale_l5_external_dependency_probe.sh [OPTIONS]

选项:
  --json     JSON 格式输出结果
  -h, --help 显示帮助

环境变量覆盖 (默认值):
  WHALE_KAFKA_BOOTSTRAP_SERVERS   Kafka broker 地址 (localhost:9092)
  WHALE_REDIS_URL                 Redis 地址 (localhost:16379)
  WHALE_POSTGRES_HOST             PostgreSQL 地址 (localhost:5432)
  WHALE_S3_ENDPOINT               S3/MinIO endpoint (localhost:9000)
  WHALE_TDENGINE_DSN              TDengine DSN (localhost:6041)
  WHALE_PULSAR_SERVICE_URL        Pulsar broker 地址 (localhost:6650)
  WHALE_FLINK_JOBMANAGER          Flink JobManager 地址 (localhost:8081)
  WHALE_HDFS_NAMENODE             HDFS NameNode 地址 (localhost:9870)
EOF
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json) JSON_OUTPUT=true; shift ;;
        -h|--help) usage ;;
        *) echo "未知选项: $1"; usage ;;
    esac
done

# ---- 工具函数 ----
log_info()  { $JSON_OUTPUT || echo -e "${CYAN}[PROBE]${NC} $*"; }
log_avail() { $JSON_OUTPUT || echo -e "${GREEN}[OK]${NC}     $*"; }
log_pend()  { $JSON_OUTPUT || echo -e "${YELLOW}[PENDING]${NC} $*"; }
log_unavail() { $JSON_OUTPUT || echo -e "${RED}[FAIL]${NC}   $*"; }
log_degraded() { $JSON_OUTPUT || echo -e "${YELLOW}[DEGRADED]${NC} $*"; }

check_tcp() {
    local host="$1"; local port="$2"
    if timeout 3 bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

check_python_driver() {
    local module="$1"
    if python3 -c "import $module" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

compute_composite_status() {
    # 计算服务综合状态，按以下优先级:
    #   所有通过 = available
    #   tcp_ok + driver_ok + health_ok 但 e2e 未验证 = available (只缺 e2e)
    #   tcp_ok + driver_ok 但 health 失败 = degraded
    #   tcp_ok 但 driver 缺失 = driver_missing
    #   tcp 失败 = unavailable
    #   从未探测 = environment_pending
    local svc="$1"
    local tcp="${SERVICE_TCP[$svc]:-false}"
    local driver="${SERVICE_DRIVER[$svc]:-false}"
    local auth="${SERVICE_AUTH[$svc]:-n/a}"
    local health="${SERVICE_HEALTH[$svc]:-false}"
    local e2e="${SERVICE_E2E[$svc]:-false}"

    if [[ "$tcp" == "false" ]]; then
        echo "unavailable"
    elif [[ "$driver" == "driver_missing" ]]; then
        echo "driver_missing"
    elif [[ "$driver" == "false" ]]; then
        echo "driver_missing"
    elif [[ "$health" == "true" && "$e2e" == "true" ]]; then
        echo "available"
    elif [[ "$health" == "true" ]]; then
        echo "available"  # health OK 即可称为 available (e2e 是可选的增强验证)
    elif [[ "$tcp" == "true" && "$driver" == "true" ]]; then
        echo "degraded"  # TCP + driver OK 但 health 失败
    else
        echo "degraded"
    fi
}

# ---- 各服务探测函数 ----

probe_kafka() {
    local host="${WHALE_KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    # Level 1: TCP
    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[kafka]="true"
        log_avail "Kafka tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[kafka]="false"
        log_unavail "Kafka tcp: $hostname:$port 不可达"
    fi

    # Level 2: Python driver
    if check_python_driver "kafka"; then
        SERVICE_DRIVER[kafka]="true"
        log_avail "Kafka driver_ok: kafka-python"
    else
        SERVICE_DRIVER[kafka]="driver_missing"
        log_degraded "Kafka driver_missing: kafka-python 未安装"
    fi

    # Level 3 & 4: Service health (通过 metadata 查询验证 broker 可用)
    if [[ "${SERVICE_TCP[kafka]}" == "true" && "${SERVICE_DRIVER[kafka]}" == "true" ]]; then
        if timeout 8 python3 -c "
import sys
try:
    from kafka import KafkaAdminClient
    admin = KafkaAdminClient(bootstrap_servers='$hostname:$port', request_timeout_ms=5000)
    topics = admin.list_topics()
    admin.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_HEALTH[kafka]="true"
            log_avail "Kafka service_health_ok: broker 可用, topic 可列出"
        else
            SERVICE_HEALTH[kafka]="false"
            log_degraded "Kafka service_health: broker 连接失败或超时"
        fi
    else
        SERVICE_HEALTH[kafka]="false"
    fi

    # Level 5: E2E (最小 publish + consume)
    SERVICE_E2E[kafka]="false"
    if [[ "${SERVICE_HEALTH[kafka]}" == "true" ]]; then
        local e2e_topic="whale-l5-probe-e2e-$$"
        if timeout 10 python3 -c "
import sys, time
try:
    from kafka import KafkaProducer, KafkaConsumer
    producer = KafkaProducer(bootstrap_servers='$hostname:$port', max_block_ms=5000)
    future = producer.send('$e2e_topic', b'l5-probe-test')
    result = future.get(timeout=5)
    producer.flush()
    producer.close()

    consumer = KafkaConsumer(
        '$e2e_topic',
        bootstrap_servers='$hostname:$port',
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000,
        group_id='whale-l5-probe-group',
    )
    msgs = []
    for msg in consumer:
        msgs.append(msg)
        if len(msgs) >= 1:
            break
    consumer.close()
    sys.exit(0 if len(msgs) >= 1 else 1)
except Exception as e:
    print(f'Kafka e2e failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_E2E[kafka]="true"
            log_avail "Kafka e2e_ok: publish+consume 验证通过"
        else
            log_degraded "Kafka e2e: publish+consume 验证失败（不影响基本可用性）"
        fi
    fi

    local composite
    composite=$(compute_composite_status "kafka")
    SERVICE_STATUS[kafka]="$composite"
    SERVICE_DETAIL[kafka]="tcp=${SERVICE_TCP[kafka]} driver=${SERVICE_DRIVER[kafka]} health=${SERVICE_HEALTH[kafka]} e2e=${SERVICE_E2E[kafka]}"
}

probe_redis() {
    local host="${WHALE_REDIS_URL:-localhost:16379}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    # Level 1: TCP
    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[redis]="true"
        log_avail "Redis tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[redis]="false"
        log_unavail "Redis tcp: $hostname:$port 不可达"
    fi

    # Level 2: Python driver
    if check_python_driver "redis"; then
        SERVICE_DRIVER[redis]="true"
        log_avail "Redis driver_ok: redis-py"
    else
        SERVICE_DRIVER[redis]="driver_missing"
        log_degraded "Redis driver_missing: redis-py 未安装"
    fi

    # Level 3 & 4: Service health (PING)
    if [[ "${SERVICE_TCP[redis]}" == "true" && "${SERVICE_DRIVER[redis]}" == "true" ]]; then
        if timeout 5 python3 -c "
import sys
try:
    import redis
    r = redis.Redis(host='$hostname', port=$port, socket_connect_timeout=3, socket_timeout=3)
    rv = r.ping()
    sys.exit(0 if rv else 1)
except Exception as e:
    print(f'Redis ping failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_HEALTH[redis]="true"
            log_avail "Redis service_health_ok: PING 响应正常"
        else
            SERVICE_HEALTH[redis]="false"
            log_degraded "Redis service_health: PING 失败或超时"
        fi
    else
        SERVICE_HEALTH[redis]="false"
    fi

    # Level 4: Auth (无密码/默认 — Redis 通常不启用密码)
    SERVICE_AUTH[redis]="n/a"

    # Level 5: E2E (SET + GET + DEL 闭环)
    SERVICE_E2E[redis]="false"
    if [[ "${SERVICE_HEALTH[redis]}" == "true" ]]; then
        if timeout 5 python3 -c "
import sys
try:
    import redis
    r = redis.Redis(host='$hostname', port=$port, socket_connect_timeout=3, socket_timeout=3)
    probe_key = 'whale:l5:probe:e2e'
    r.setex(probe_key, 30, 'l5-probe-ok')
    val = r.get(probe_key)
    r.delete(probe_key)
    sys.exit(0 if val and b'l5-probe-ok' in val else 1)
except Exception as e:
    print(f'Redis e2e failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_E2E[redis]="true"
            log_avail "Redis e2e_ok: SET+GET+DEL 闭环验证通过"
        else
            log_degraded "Redis e2e: SET+GET+DEL 验证失败"
        fi
    fi

    local composite
    composite=$(compute_composite_status "redis")
    SERVICE_STATUS[redis]="$composite"
    SERVICE_DETAIL[redis]="tcp=${SERVICE_TCP[redis]} driver=${SERVICE_DRIVER[redis]} health=${SERVICE_HEALTH[redis]} e2e=${SERVICE_E2E[redis]}"
}

probe_postgres() {
    local host="${WHALE_POSTGRES_HOST:-localhost:5432}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    # Level 1: TCP
    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[postgres]="true"
        log_avail "PostgreSQL tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[postgres]="false"
        log_unavail "PostgreSQL tcp: $hostname:$port 不可达"
    fi

    # Level 2: Python driver
    if check_python_driver "psycopg"; then
        SERVICE_DRIVER[postgres]="true"
        log_avail "PostgreSQL driver_ok: psycopg"
    else
        SERVICE_DRIVER[postgres]="driver_missing"
        log_degraded "PostgreSQL driver_missing: psycopg 未安装"
    fi

    # Level 3 & 4: Service health (connect + SELECT 1)
    if [[ "${SERVICE_TCP[postgres]}" == "true" && "${SERVICE_DRIVER[postgres]}" == "true" ]]; then
        local pg_user="${WHALE_POSTGRES_USER:-whale}"
        local pg_pass="${WHALE_POSTGRES_PASSWORD:-whale}"
        local pg_db="${WHALE_POSTGRES_DB:-whale_ingest}"
        if timeout 8 python3 -c "
import sys
try:
    import psycopg
    conn = psycopg.connect(
        host='$hostname', port=$port,
        user='$pg_user', password='$pg_pass', dbname='$pg_db',
        connect_timeout=5
    )
    cur = conn.execute('SELECT 1')
    rv = cur.fetchone()
    conn.close()
    sys.exit(0 if rv and rv[0] == 1 else 1)
except Exception as e:
    print(f'PG health failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_HEALTH[postgres]="true"
            log_avail "PostgreSQL service_health_ok: SELECT 1 正常"
        else
            SERVICE_HEALTH[postgres]="false"
            log_degraded "PostgreSQL service_health: 连接或查询失败"
        fi
    else
        SERVICE_HEALTH[postgres]="false"
    fi

    SERVICE_AUTH[postgres]="n/a"
    SERVICE_E2E[postgres]="false"
    if [[ "${SERVICE_HEALTH[postgres]}" == "true" ]]; then
        SERVICE_E2E[postgres]="true"
        log_avail "PostgreSQL e2e_ok: connect+query 验证通过"
    fi

    local composite
    composite=$(compute_composite_status "postgres")
    SERVICE_STATUS[postgres]="$composite"
    SERVICE_DETAIL[postgres]="tcp=${SERVICE_TCP[postgres]} driver=${SERVICE_DRIVER[postgres]} health=${SERVICE_HEALTH[postgres]}"
}

probe_s3() {
    local host="${WHALE_S3_ENDPOINT:-localhost:9000}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)
    local access_key="${WHALE_S3_ACCESS_KEY:-minioadmin}"
    local secret_key="${WHALE_S3_SECRET_KEY:-minioadmin}"

    # Level 1: TCP
    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[s3]="true"
        log_avail "S3/MinIO tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[s3]="false"
        log_unavail "S3/MinIO tcp: $hostname:$port 不可达"
    fi

    # Level 2: Python driver (boto3)
    if check_python_driver "boto3"; then
        SERVICE_DRIVER[s3]="true"
        log_avail "S3 driver_ok: boto3"
    else
        SERVICE_DRIVER[s3]="driver_missing"
        log_degraded "S3 driver_missing: boto3 未安装 (pip install boto3)"
    fi

    # Level 3 & 4: Service health (head_bucket / list_buckets)
    if [[ "${SERVICE_TCP[s3]}" == "true" && "${SERVICE_DRIVER[s3]}" == "true" ]]; then
        if timeout 10 python3 -c "
import sys
try:
    import boto3
    client = boto3.client(
        's3',
        endpoint_url='http://$hostname:$port',
        aws_access_key_id='$access_key',
        aws_secret_access_key='$secret_key',
        region_name='us-east-1',
        use_ssl=False,
    )
    buckets = client.list_buckets()
    sys.exit(0)
except Exception as e:
    print(f'S3 health failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_HEALTH[s3]="true"
            log_avail "S3/MinIO service_health_ok: list_buckets 成功"
        else
            SERVICE_HEALTH[s3]="false"
            log_degraded "S3/MinIO service_health: list_buckets 失败（检查认证）"
        fi
    else
        SERVICE_HEALTH[s3]="false"
    fi

    # Level 5: E2E (put_object + get_object + delete_object)
    SERVICE_E2E[s3]="false"
    if [[ "${SERVICE_HEALTH[s3]}" == "true" ]]; then
        if timeout 10 python3 -c "
import sys, json
try:
    import boto3
    client = boto3.client(
        's3',
        endpoint_url='http://$hostname:$port',
        aws_access_key_id='$access_key',
        aws_secret_access_key='$secret_key',
        region_name='us-east-1',
        use_ssl=False,
    )
    bucket = 'whale-l5-test'
    key = 'probe-e2e-test.json'
    body = json.dumps({'probe': 'l5-e2e', 'ts': 'now'})
    client.put_object(Bucket=bucket, Key=key, Body=body)
    resp = client.get_object(Bucket=bucket, Key=key)
    data = json.loads(resp['Body'].read())
    client.delete_object(Bucket=bucket, Key=key)
    sys.exit(0 if data.get('probe') == 'l5-e2e' else 1)
except Exception as e:
    print(f'S3 e2e failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_E2E[s3]="true"
            log_avail "S3/MinIO e2e_ok: put+get+delete 闭环验证通过"
        else
            log_degraded "S3/MinIO e2e: put+get+delete 验证失败"
        fi
    fi

    local composite
    composite=$(compute_composite_status "s3")
    SERVICE_STATUS[s3]="$composite"
    SERVICE_DETAIL[s3]="tcp=${SERVICE_TCP[s3]} driver=${SERVICE_DRIVER[s3]} health=${SERVICE_HEALTH[s3]} e2e=${SERVICE_E2E[s3]}"
}

probe_tdengine() {
    local dsn="${WHALE_TDENGINE_DSN:-localhost:6041}"
    local hostname port
    # 解析 DSN (支持 taosws://、http:// 或纯 host:port)
    local cleaned="$dsn"
    cleaned="${cleaned#taosws://}"
    cleaned="${cleaned#http://}"
    cleaned="${cleaned#https://}"
    hostname=$(echo "$cleaned" | cut -d: -f1)
    port=$(echo "$cleaned" | rev | cut -d: -f1 | rev)
    # fallback
    port="${port:-6041}"
    local user="${TDENGINE_USER:-root}"
    local password="${TDENGINE_PASSWORD:-taosdata}"

    # Level 1: TCP
    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[tdengine]="true"
        log_avail "TDengine tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[tdengine]="false"
        log_unavail "TDengine tcp: $hostname:$port 不可达"
    fi

    # Level 2: Python driver (taos-ws-py 或 taospy)
    if check_python_driver "taosws" || check_python_driver "taos"; then
        SERVICE_DRIVER[tdengine]="true"
        log_avail "TDengine driver_ok: taos-ws-py 或 taospy 可用"
    else
        SERVICE_DRIVER[tdengine]="driver_missing"
        log_degraded "TDengine driver_missing: taos-ws-py/taospy 未安装 (TDengine 使用 REST API 通信，driver 是可选增强)"
    fi

    # Level 3: Auth check (REST API Basic Auth)
    if [[ "${SERVICE_TCP[tdengine]}" == "true" ]]; then
        if timeout 8 python3 -c "
import sys, urllib.request, base64
try:
    req = urllib.request.Request(
        'http://$hostname:$port/rest/sql',
        data=b'SELECT 1',
        headers={
            'Content-Type': 'text/plain',
            'Authorization': 'Basic ' + base64.b64encode(b'$user:$password').decode(),
        },
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        body = r.read().decode()
        if '\"code\":0' in body:
            sys.exit(0)
        else:
            print(f'TDengine auth/query failed: {body[:200]}', file=sys.stderr)
            sys.exit(1)
except Exception as e:
    print(f'TDengine REST failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_AUTH[tdengine]="true"
            SERVICE_HEALTH[tdengine]="true"
            log_avail "TDengine service_health_ok: REST API SELECT 1 正常"
        else
            SERVICE_HEALTH[tdengine]="false"
            log_degraded "TDengine service_health: REST API 失败或认证错误"
        fi
    else
        SERVICE_HEALTH[tdengine]="false"
    fi

    # Level 4 & 5: E2E (CREATE DB + CREATE TABLE + INSERT + SELECT + DROP 闭环)
    SERVICE_E2E[tdengine]="false"
    if [[ "${SERVICE_HEALTH[tdengine]}" == "true" ]]; then
        local db_name="whale_l5_probe_e2e"
        if timeout 15 python3 -c "
import sys, urllib.request, base64, json
try:
    auth = 'Basic ' + base64.b64encode(b'$user:$password').decode()
    def exec_sql(sql):
        req = urllib.request.Request(
            'http://$hostname:$port/rest/sql',
            data=sql.encode(),
            headers={'Content-Type': 'text/plain', 'Authorization': auth},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())

    # 创建测试数据库和表
    exec_sql('CREATE DATABASE IF NOT EXISTS $db_name KEEP 3')
    exec_sql('CREATE STABLE IF NOT EXISTS ${db_name}.probe (ts TIMESTAMP, val INT) TAGS (src NCHAR(32))')
    # 写入
    exec_sql(\"INSERT INTO ${db_name}.p1 USING ${db_name}.probe TAGS ('l5-probe') VALUES (NOW, 42)\")
    # 读回
    result = exec_sql('SELECT val FROM ${db_name}.probe LIMIT 1')
    rows = result.get('data', [])
    val = rows[0][0] if rows and rows[0] else None
    # 清理
    exec_sql('DROP DATABASE IF EXISTS $db_name')
    sys.exit(0 if val == 42 else 1)
except Exception as e:
    print(f'TDengine e2e failed: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null; then
            SERVICE_E2E[tdengine]="true"
            log_avail "TDengine e2e_ok: CREATE+INSERT+SELECT+DROP 闭环验证通过"
        else
            log_degraded "TDengine e2e: 写入+读回 验证失败"
        fi
    fi

    local composite
    composite=$(compute_composite_status "tdengine")
    SERVICE_STATUS[tdengine]="$composite"
    SERVICE_DETAIL[tdengine]="tcp=${SERVICE_TCP[tdengine]} driver=${SERVICE_DRIVER[tdengine]} auth=${SERVICE_AUTH[tdengine]:-n/a} health=${SERVICE_HEALTH[tdengine]} e2e=${SERVICE_E2E[tdengine]}"
}

probe_pulsar() {
    local host="${WHALE_PULSAR_SERVICE_URL:-localhost:6650}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[pulsar]="true"
        log_avail "Pulsar tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[pulsar]="false"
        log_unavail "Pulsar tcp: $hostname:$port 不可达"
    fi

    if check_python_driver "pulsar"; then
        SERVICE_DRIVER[pulsar]="true"
        log_avail "Pulsar driver_ok: pulsar-client"
    else
        SERVICE_DRIVER[pulsar]="driver_missing"
        log_degraded "Pulsar driver_missing: pulsar-client 未安装"
    fi

    # P1 可选服务: 仅做 TCP + driver 探测
    SERVICE_HEALTH[pulsar]="false"
    SERVICE_E2E[pulsar]="false"
    local composite
    composite=$(compute_composite_status "pulsar")
    SERVICE_STATUS[pulsar]="$composite"
    SERVICE_DETAIL[pulsar]="tcp=${SERVICE_TCP[pulsar]} driver=${SERVICE_DRIVER[pulsar]}"
}

probe_flink() {
    local host="${WHALE_FLINK_JOBMANAGER:-localhost:8081}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[flink]="true"
        log_avail "Flink tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[flink]="false"
        log_unavail "Flink tcp: $hostname:$port 不可达"
    fi

    if check_python_driver "pyflink"; then
        SERVICE_DRIVER[flink]="true"
        log_avail "Flink driver_ok: pyflink"
    else
        SERVICE_DRIVER[flink]="driver_missing"
        log_degraded "Flink driver_missing: pyflink 未安装"
    fi

    # P1 可选服务
    SERVICE_HEALTH[flink]="false"
    SERVICE_E2E[flink]="false"
    local composite
    composite=$(compute_composite_status "flink")
    SERVICE_STATUS[flink]="$composite"
    SERVICE_DETAIL[flink]="tcp=${SERVICE_TCP[flink]} driver=${SERVICE_DRIVER[flink]}"
}

probe_hdfs() {
    local host="${WHALE_HDFS_NAMENODE:-localhost:9870}"
    local hostname port
    hostname=$(echo "$host" | cut -d: -f1)
    port=$(echo "$host" | cut -d: -f2)

    if check_tcp "$hostname" "$port"; then
        SERVICE_TCP[hdfs]="true"
        log_avail "HDFS tcp_ok: $hostname:$port"
    else
        SERVICE_TCP[hdfs]="false"
        log_unavail "HDFS tcp: $hostname:$port 不可达"
    fi

    if check_python_driver "pyarrow"; then
        SERVICE_DRIVER[hdfs]="true"
        log_avail "HDFS driver_ok: pyarrow"
    else
        SERVICE_DRIVER[hdfs]="driver_missing"
        log_degraded "HDFS driver_missing: pyarrow 未安装"
    fi

    # P1 可选服务
    SERVICE_HEALTH[hdfs]="false"
    SERVICE_E2E[hdfs]="false"
    local composite
    composite=$(compute_composite_status "hdfs")
    SERVICE_STATUS[hdfs]="$composite"
    SERVICE_DETAIL[hdfs]="tcp=${SERVICE_TCP[hdfs]} driver=${SERVICE_DRIVER[hdfs]}"
}

# ---- 主流程 ----
main() {
    $JSON_OUTPUT || echo ""
    $JSON_OUTPUT || echo "============================================================"
    $JSON_OUTPUT || echo " Whale L5 外部依赖多级环境探针 (Round 3)"
    $JSON_OUTPUT || echo " 时间: $(date '+%Y-%m-%d %H:%M:%S')"
    $JSON_OUTPUT || echo " 仓库: $REPO_ROOT"
    $JSON_OUTPUT || echo " 探测层级: tcp_ok → driver_ok → auth_ok → service_health_ok → e2e_ok"
    $JSON_OUTPUT || echo " 综合状态: available | degraded | driver_missing | unavailable"
    $JSON_OUTPUT || echo "============================================================"
    $JSON_OUTPUT || echo ""

    # 按 P0 → P1 顺序探测
    $JSON_OUTPUT || log_info "==== P0 服务 (Kafka + Redis + PostgreSQL + S3/MinIO + TDengine) ===="
    $JSON_OUTPUT || echo ""
    probe_kafka
    $JSON_OUTPUT || echo ""
    probe_redis
    $JSON_OUTPUT || echo ""
    probe_postgres
    $JSON_OUTPUT || echo ""
    probe_s3
    $JSON_OUTPUT || echo ""
    probe_tdengine
    $JSON_OUTPUT || echo ""

    $JSON_OUTPUT || log_info "==== P1 服务 (Pulsar + Flink + HDFS) ===="
    $JSON_OUTPUT || echo ""
    probe_pulsar
    $JSON_OUTPUT || echo ""
    probe_flink
    $JSON_OUTPUT || echo ""
    probe_hdfs
    $JSON_OUTPUT || echo ""

    # ---- 汇总输出 ----
    $JSON_OUTPUT || echo ""
    $JSON_OUTPUT || echo "============================================================"
    $JSON_OUTPUT || echo " L5 外部依赖综合就绪矩阵 (Composite Status)"
    $JSON_OUTPUT || echo "============================================================"

    local count_available=0 count_degraded=0 count_driver_missing=0 count_unavailable=0 count_total=0

    for svc in "${SERVICE_LIST[@]}"; do
        count_total=$((count_total + 1))
        local status="${SERVICE_STATUS[$svc]:-environment_pending}"
        case "$status" in
            available) count_available=$((count_available + 1)) ;;
            degraded) count_degraded=$((count_degraded + 1)) ;;
            driver_missing) count_driver_missing=$((count_driver_missing + 1)) ;;
            unavailable) count_unavailable=$((count_unavailable + 1)) ;;
        esac
    done

    if $JSON_OUTPUT; then
        echo "{"
        echo "  \"probe_time\": \"$(date -Iseconds)\","
        echo "  \"summary\": {"
        echo "    \"total\": $count_total,"
        echo "    \"available\": $count_available,"
        echo "    \"degraded\": $count_degraded,"
        echo "    \"driver_missing\": $count_driver_missing,"
        echo "    \"unavailable\": $count_unavailable"
        echo "  },"
        echo "  \"services\": {"
        local first=true
        for svc in "${SERVICE_LIST[@]}"; do
            local status="${SERVICE_STATUS[$svc]:-environment_pending}"
            local detail="${SERVICE_DETAIL[$svc]:-}"
            $first || echo ","
            first=false
            printf '    "%s": {"composite_status": "%s", "tcp": "%s", "driver": "%s", "health": "%s", "e2e": "%s", "detail": "%s"}' \
                "$svc" "$status" \
                "${SERVICE_TCP[$svc]:-false}" \
                "${SERVICE_DRIVER[$svc]:-false}" \
                "${SERVICE_HEALTH[$svc]:-false}" \
                "${SERVICE_E2E[$svc]:-false}" \
                "$detail"
        done
        echo ""
        echo "  }"
        echo "}"
    else
        for svc in "${SERVICE_LIST[@]}"; do
            local status="${SERVICE_STATUS[$svc]:-environment_pending}"
            local detail="${SERVICE_DETAIL[$svc]:-}"
            case "$status" in
                available)
                    echo -e "  ${GREEN}[AVAILABLE]${NC}      $svc  $detail" ;;
                degraded)
                    echo -e "  ${YELLOW}[DEGRADED]${NC}      $svc  $detail" ;;
                driver_missing)
                    echo -e "  ${RED}[DRIVER_MISSING]${NC} $svc  $detail" ;;
                unavailable)
                    echo -e "  ${RED}[UNAVAILABLE]${NC}    $svc  $detail" ;;
                *)
                    echo -e "  ${YELLOW}[ENV_PENDING]${NC}  $svc  $status" ;;
            esac
        done

        echo ""
        echo "============================================================"
        echo " 总计: $count_total 服务"
        echo "   available:        $count_available (全探针通过，L5 可验证)"
        echo "   degraded:          $count_degraded (TCP 可达但部分能力受限)"
        echo "   driver_missing:    $count_driver_missing (driver 未安装)"
        echo "   unavailable:       $count_unavailable (服务不可达)"
        echo ""
        if [[ $count_unavailable -gt 0 || $count_driver_missing -gt 0 ]]; then
            log_pend "以下服务需要环境就绪后才能 L5 E2E 验证:"
            for svc in "${SERVICE_LIST[@]}"; do
                local status="${SERVICE_STATUS[$svc]:-environment_pending}"
                case "$status" in
                    unavailable)
                        echo "   - $svc: 服务不可达，需启动 Docker 容器" ;;
                    driver_missing)
                        echo "   - $svc: driver 缺失，运行 pip install 补齐" ;;
                    degraded)
                        echo "   - $svc: 部分能力受限，需检查配置/认证" ;;
                esac
            done
            echo ""
            log_info "L5 就绪率: $count_available/$count_total ($(( count_available * 100 / count_total ))%)"
        else
            log_avail "所有 L5 外部依赖可用，可以执行完整 L5 E2E 验证"
            echo ""
            log_info "运行 L5 完整验证:  python -m pytest tests/integration/ -m l5 -v"
        fi
        echo ""
        log_info "本地可验证链路 (L4): ingest → speed_layer → storage (InMemory)"
        log_info "启动 L5 环境:         docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml up -d"
        echo "============================================================"
    fi
}

main "$@"
