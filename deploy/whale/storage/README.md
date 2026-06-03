# Whale Storage 现场部署说明

## 三层存储架构

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: raw_archive (原始事实层，不可变)                    │
│   格式: .jsonl.gz / .jsonl.zst                              │
│   存储: 本地文件系统 / HDFS / S3/MinIO                       │
│   保留: 按配置 TTL (默认无限期)                              │
│   职责: 保存 ingest 输出的原始消息副本，用于审计和重放        │
├─────────────────────────────────────────────────────────────┤
│ Layer 2: raw_index (原始时序索引层)                          │
│   存储: TDengine (environment-pending) / Memory (dev)       │
│   索引: source_id + device_id + timestamp                   │
│   职责: 快速查询原始消息位置，不保存完整内容                  │
├─────────────────────────────────────────────────────────────┤
│ Layer 3: standardized (标准时序层)                           │
│   存储: TDengine (environment-pending) / Memory (dev)       │
│   字段: node_key + variable_key + value + quality_code      │
│   职责: 清洗标准化后的时序数据，支撑 warehouse/mart 聚合      │
├─────────────────────────────────────────────────────────────┤
│ Layer 4: warehouse / mart (聚合服务层)                       │
│   状态: port+stub (未实现)                                  │
│   职责: 按时间周期聚合、业务模型计算                          │
│   不负责: 实时查询（由 serving_cache 负责）                   │
├─────────────────────────────────────────────────────────────┤
│ Serving Cache (近实时 KV)                                   │
│   存储: InMemory (dev) / Redis (field, environment-pending)  │
│   职责: 低延迟实时数据查询                                    │
│   TTL: 60s (可配置)                                         │
└─────────────────────────────────────────────────────────────┘
```

重要：raw_archive 绝不使用 TDengine 替代。raw_archive 是长期不可变原始事实层。

## 配置模板

- `config/whale/storage.raw_archive.example.yaml` — 归档配置
- `config/whale/storage.tdengine.example.yaml` — raw_index + standardized TDengine 配置

## 关键配置项

### raw_archive

| 配置 | 说明 | 默认值 |
|---|---|---|
| base_path | 归档根目录 | /data/whale/raw_archive |
| backend | 归档后端 (local/hdfs/s3) | local |
| compression | 压缩算法 (gzip/zstd) | gzip |
| batch_size | 每批消息数 | 100 |
| retention_days | 保留天数（0 为无限） | 0 |

### raw_index / standardized (TDengine)

| 配置 | 说明 | 默认值 |
|---|---|---|
| host | TDengine 主机 | localhost |
| port | TDengine 端口 | 6041 |
| database | 数据库名 | whale_raw_index / whale_standardized |
| user | 用户名 | root |
| password | 密码 | taosdata |
| ttl_days | 自动过期天数 | 90 / 365 |

## 环境依赖状态

| 存储后端 | 状态 | 开发替代 |
|---|---|---|
| 本地 raw_archive | 已验证 (L3) | — |
| HDFS raw_archive | environment-pending | LocalCompressedArchiveSink |
| S3/MinIO raw_archive | environment-pending | LocalCompressedArchiveSink |
| TDengine raw_index | environment-pending | MemoryRawIndexSink |
| TDengine standardized | environment-pending | MemoryStandardizedSink |
| Redis serving_cache | environment-pending | InMemoryServingCache |
