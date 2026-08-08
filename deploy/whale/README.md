# Whale 现场部署

Whale 是能源数据统一平台核心模块，负责数据采集（ingest）、消息管道（message_pipeline）、
实时写入（speed_layer）和多层存储（storage）。完整数据链路：

```text
ingest -> Kafka -> speed_layer -> S3/TDengine/Redis
                  (raw_archive)  (raw_index/standardized/serving_cache)
```

## 部署目录

- `ingest/` -- 数据采集运行时部署说明
- `message_pipeline/` -- 消息管道（Kafka/Pulsar）部署说明
- `speed_layer/` -- 速度层 writers 部署说明
- `storage/` -- raw_archive / raw_index / standardized 存储层部署说明

## 前置依赖

| 依赖 | 最低版本 | 说明 |
| --- | --- | --- |
| Docker | 24.0+ | 用于运行外部依赖容器 |
| Docker Compose | v2 | `docker compose` 子命令或 `docker-compose` |
| Python | CPython 3.13 | 项目运行基线；当前不支持 3.14 |
| pip | 23.0+ | 依赖安装 |

## 快速启动

### 1. 复制环境变量模板

```bash
cp deploy/whale/.env.whale.field.example deploy/whale/.env.whale.field
```

### 2. 编辑环境变量

```bash
vim deploy/whale/.env.whale.field
```

关键变量：`WHALE_KAFKA_BOOTSTRAP_SERVERS`、`WHALE_REDIS_URL`、`WHALE_S3_ENDPOINT`、
`WHALE_TDENGINE_DSN`、`WHALE_POSTGRES_HOST`。

### 3. 启动准生产依赖验证期 外部环境

```bash
# 启动 P0 服务 (Kafka + Redis + MinIO + TDengine + PostgreSQL)
docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml up -d

# 验证所有服务健康
docker compose -f deploy/whale/message_pipeline/docker-compose.whale-l5.yaml ps
```

### 4. 安装 Python 驱动

```bash
pip install -e ".[dev,s3]"
# 如果使用 TDengine 原生驱动（可选，默认使用 REST API）
# pip install taos-ws-py
```

Starfish IEC104 runtime 需要单独启用：

```bash
pip install -e ".[dev,iec104]"
```

`iec104` extra 固定使用 `c104==2.2.1`。该扩展及其 lib60870-C 依赖采用
GPLv3；构建或分发包含该 extra 的镜像/安装包前，必须完成相应许可合规审查。

### Whale ingest 镜像状态

当前 ingest Dockerfile 已使用 Python 3.13。真实构建已通过，镜像中未发现
CPython 3.14 字节码，因此 Python 3.13 构建基线本身已验证。

但镜像默认入口 `python -m whale.ingest.runtime.entrypoint` 目前仍不能完成
运行启动。Git 历史中的 `9bbc3dc` 删除了原有分模块 runtime ORM 文件，而当前
`src/` 中仍有 20 多个路径引用这些旧 ORM 模块或导出，入口在导入阶段失败。
这是本轮 Python/Starfish 变更之前已经存在的 Whale ORM 迁移阻塞，不能通过
简单补环境变量或 `export` 修复；因此只能记录“镜像构建通过”，不得记录
“Whale ingest 镜像运行闭环通过”。

### 5. 一键预检验证

```bash
# 完整预检（环境 + 准生产依赖 E2E + 跨模块联调 smoke + marker 审计）
bash scripts/run_whale_field_ready_smoke.sh

# 仅环境检查，跳过测试
bash scripts/run_whale_field_ready_smoke.sh --skip-tests

# JSON 输出
bash scripts/run_whale_field_ready_smoke.sh --json
```

## 准生产依赖验证期 单独运行

```bash
# 准生产依赖验证期 外部依赖环境探测（8 服务，多级探针）
bash scripts/run_whale_l5_external_dependency_probe.sh --json

# Kafka pipeline 准生产依赖 E2E
pytest tests/e2e/test_whale_l5_kafka_pipeline_e2e.py -m l5 -v

# Storage 准生产依赖 E2E（S3/MinIO + TDengine + Redis）
pytest tests/e2e/test_whale_l5_storage_e2e.py -m l5 -v

# 准生产依赖验证期 外部依赖综合验证
pytest tests/integration/test_l5_external_dependency_verification.py -m l5 -v

# 跨模块联调期 现场最小链路 smoke（InMemory，无需 Docker）
pytest tests/e2e/test_whale_field_minimal_smoke.py -v
```

## 环境依赖状态

### 准生产依赖验证期 验证通过（真实外部依赖验证通过，Round 5）

| 组件 | 端口 | 状态 | 证据 |
| --- | --- | --- | --- |
| Kafka | 9092 | **准生产依赖验证期 验证通过** | 4 E2E + 2 integration, real pub/consume + consumer group isolation |
| PostgreSQL | 5432 | **准生产依赖验证期 验证通过** | 1 integration, connect + SELECT 1 |
| Redis | 16379 | **准生产依赖验证期 验证通过** | 4 E2E + 1 integration, SET/GET/TTL/stale/out-of-order |
| S3/MinIO | 9000 | **准生产依赖验证期 验证通过** | 3 E2E + 2 integration, write gzip JSONL + readback + manifest |
| TDengine | 6041 | **准生产依赖验证期 验证通过** | 3 E2E + 2 integration, REST API write + readback 10 fields |

### MISSING_ENVIRONMENT（环境未就绪）

| 组件 | 端口 | 状态 | 备注 |
| --- | --- | --- | --- |
| Pulsar | 6650 | MISSING_ENVIRONMENT | contract-only adapter, P1 可选 |
| Flink | 8081 | MISSING_ENVIRONMENT | contract-only adapter, P1 可选 |
| HDFS | 9870 | MISSING_ENVIRONMENT | contract-only adapter, P1 可选 |

### stub/未实现

| 模块 | 状态 | 备注 |
| --- | --- | --- |
| batch_layer | 未实现 | Lambda 架构批处理链路缺失 |
| warehouse | stub | InMemoryWarehouseSink 仅端口定义 |
| mart | stub | InMemoryMartSink 仅端口定义 |

### 本地可用

| 组件 | 状态 | 说明 |
| --- | --- | --- |
| 本地 raw_archive | 跨模块联调期验证 | LocalCompressedArchiveSink，gzip 压缩本地文件 |
| InMemory 全链路 | 跨模块联调期验证 | 7 smoke tests，无外部依赖 |

## 配置参考路径

| 配置 | 文件 |
| --- | --- |
| Kafka broker / topic | `config/whale/message_pipeline.kafka.example.yaml` |
| Pulsar broker | `config/whale/message_pipeline.pulsar.example.yaml` (MISSING_ENVIRONMENT) |
| Speed layer writers | `config/whale/speed_layer.writers.example.yaml` |
| S3/MinIO raw_archive | `config/whale/storage.raw_archive.example.yaml` |
| TDengine raw_index/standardized | `config/whale/storage.tdengine.example.yaml` |
| Redis serving_cache | `config/whale/storage.serving_cache.example.yaml` |
| 环境变量模板 | `deploy/whale/.env.whale.field.example` |
| Docker compose | `deploy/whale/message_pipeline/docker-compose.whale-l5.yaml` |

所有配置示例使用环境变量占位符 `${VAR_NAME}`，不硬编码敏感凭据。

## 治理与安全

治理和安全基础能力由 Turtle 提供（`src/turtle/`），Whale 通过 `turtle.*` 包导入。
运维编排能力由 Octopus 提供（`src/octopus/`）。

## 测试汇总

Round 5 最终收口: **120 tests passed, 0 failed, 4 skipped** (Pulsar/Flink/HDFS MISSING_ENVIRONMENT)

| 测试类别 | 测试数 | 结果 |
| --- | --- | --- |
| 开发期验证 (unit) | 全量 | all passed |
| 跨模块/准生产联调验证 (integration) | 全量 | all passed |
| Kafka pipeline E2E (准生产依赖验证期) | 4 | all passed |
| Storage E2E (准生产依赖验证期) | 10 (S3:3, TD:3, Redis:4) | all passed |
| Field minimal smoke (跨模块联调期验证) | 7 | all passed |
| HDFS (准生产依赖验证期) | 1 | skipped (MISSING_ENVIRONMENT) |
| Pulsar + Flink | 3 | skipped (MISSING_ENVIRONMENT) |
