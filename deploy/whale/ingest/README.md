# Whale Ingest 现场部署说明

## 职责

Whale Ingest 负责多协议数据采集（IEC 104、Modbus、OPC UA、MQTT、HTTP REST、
IEC 101、IEC 61850 MMS/GOOSE/SV 等），将采集到的原始数据通过 message_pipeline
发布到 Kafka topic，同时维护 Redis 状态缓存和 PostgreSQL 运行时数据库。

## 部署拓扑

```
┌─────────────────────────────────────────────────┐
│  ingest-api (FastAPI + uvicorn)                 │
│  端口: 8000 → 18000 (host)                      │
│  职责: 配置管理、采集任务调度、健康检查           │
├─────────────────────────────────────────────────┤
│  ingest-worker-a / ingest-worker-b              │
│  职责: 双活分区采集执行 (dual_active_partitioned) │
│  每个 worker 负责一半 source_id 分区的采集任务    │
├─────────────────────────────────────────────────┤
│  PostgreSQL (runtime DB)                        │
│  Redis (state cache + lease fencing)            │
│  Kafka (message publish)                        │
└─────────────────────────────────────────────────┘
```

## 环境变量

参考 `.env.whale.field.example` 中 `WHALE_INGEST_*` 前缀的变量。

## 启动命令

```bash
# 方式 1: docker compose (prodlike)
docker compose -f docker-compose.ingest-prodlike.yaml up -d

# 方式 2: 直接运行 (dev)
WHALE_INGEST_DATABASE_BACKEND=sqlite \
WHALE_INGEST_STATE_CACHE_BACKEND=memory \
WHALE_INGEST_MESSAGE_BACKEND=inmemory \
    whale api

# worker 单独启动
WHALE_INGEST_RUNTIME_MODE=dual_active_partitioned \
WHALE_INGEST_NODE_KEY=worker-a \
    whale worker
```

## 健康检查

```bash
# ingest API 健康检查
curl -f http://localhost:8000/healthz

# Kafka topic 可用性检查
kafka-topics.sh --bootstrap-server localhost:9092 --describe --topic whale.ingest.state
```

## 切换注意事项

- 停止 ingest-api 前，确保所有 worker 已完成当前采集周期。
- 新 worker 启动后由 scheduler 自动分配 partition。
- 旧 worker 延迟停止（保持 consumer group 用于回滚）。
