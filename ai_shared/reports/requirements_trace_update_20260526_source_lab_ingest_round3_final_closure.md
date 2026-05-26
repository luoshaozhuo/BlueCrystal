# requirements_trace_update_20260526_source_lab_ingest_round3_final_closure

## 1. 本次范围

- Round3 最终收口：运行态与部署态证据补齐、最终需求跟踪表更新、闭环结论输出。

## 2. 读取文件

- `CLAUDE.md`, `AGENTS.md`, `.claude/skills/requirement-trace/SKILL.md`
- `ai_shared/memory/Whale_REQ_SourceLab.md`, `ai_shared/memory/Whale_REQ_Ingest.md`
- `ai_shared/reports/requirements_trace_update_20260525_source_lab_ingest_round1.md`
- `ai_shared/reports/requirements_trace_update_20260526_source_lab_ingest_round2.md`
- `ai_shared/reports/ingest_security_partition_boundary.md`
- ingest use case/role/port/adapter/tests 相关源码

## 3. 更新文件

- `src/whale/ingest/ports/metrics.py`
- `src/whale/ingest/ports/__init__.py`
- `src/whale/ingest/usecases/source_command_use_case.py`
- `src/whale/ingest/usecases/state_snapshot_publish_use_case.py`
- `src/whale/ingest/usecases/roles/polling_acquisition_role.py`
- `src/whale/ingest/usecases/roles/subscription_acquisition_role.py`
- `config/ingest/security_partition.example.yaml`
- `tests/unit/test_subscription_reconnect_runtime.py`
- `tests/unit/test_ingest_metrics_events.py`
- `tests/unit/test_ingest_security_partition_config.py`
- `tests/integration/test_ingest_source_cache_message_kafka_e2e.py`
- `ai_shared/memory/Whale_REQ_Ingest.md`
- `ai_shared/memory/Whale_REQ_SourceLab.md`

## 4. 新增/修改实现

- 新增 `IngestMetricsPort/IngestMetricEvent`，并在四类链路发射结构化指标事件：
  - polling read（`PollingAcquisitionRole`）
  - subscription baseline/reconnect/start（`SubscriptionAcquisitionRole`）
  - snapshot publish（`StateSnapshotPublishUseCase`）
  - source command（`SourceCommandUseCase`）
- `SubscriptionAcquisitionRole` 增加轻量重连参数：
  - `subscription_max_retry`
  - `subscription_backoff_ms`
- 新增 Kafka container 级 E2E 测试（环境缺依赖则 skip，并给 CI 命令）。
- 新增安全分区配置样例 + 配置门禁测试。

## 5. 执行测试

- 必测命令全部执行：
  - `pytest tests/unit/test_source_acquisition_use_case.py -q` -> 12 passed
  - `pytest tests/unit/test_state_snapshot_publish_use_case.py -q` -> 17 passed
  - `pytest tests/unit/test_subscription_acquisition_role.py -q` -> 2 passed
  - `pytest tests/unit/test_polling_acquisition_role.py -q` -> 8 passed
  - `pytest tests/unit/test_source_command_use_case.py -q` -> 9 passed
  - `pytest tests/unit/test_source_command_audit.py -q` -> 2 passed
  - `pytest tests/unit/test_ingest_source_adapter_capability_matrix.py -q` -> 2 passed
  - `pytest tests/unit/test_ingest_no_source_lab_imports.py -q` -> 1 passed
  - `pytest tests/unit/test_subscription_reconnect_baseline.py -q` -> 1 passed
  - `pytest tests/integration/test_ingest_cache_to_kafka_pipeline.py -q` -> 5 passed
  - `pytest tests/integration/test_ingest_source_cache_message_e2e.py -q` -> 2 passed
  - `pytest tests/integration/test_ingest_opcua_source_write.py -q` -> 3 passed
  - `pytest tests/integration -q` -> 37 passed, 1 skipped
  - `pytest tests/unit -q` -> 316 passed
- 新增测试执行：
  - `pytest tests/unit/test_subscription_reconnect_runtime.py -q` -> 2 passed
  - `pytest tests/unit/test_ingest_metrics_events.py -q` -> 1 passed
  - `pytest tests/unit/test_ingest_security_partition_config.py -q` -> 1 passed
  - `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q -rs` -> 1 skipped  
    skip 原因：缺 `testcontainers/kafka-python`；CI 命令已输出。

## 6. SourceLab 最终状态

- 本轮不改 source_lab 主线功能，保持 Round5-5 结论。
- GOOSE/SV 仍是 framework closure + CI pending（未误标运行闭环）。
- gateway mode 限制（IEC101/Modbus RTU）保持不变。

## 7. Ingest 最终状态

- `source -> cache -> message` 组合链路证据完整（L3）。
- Kafka true E2E 测试用例已具备，但当前环境因依赖缺失 skip，状态为 CI pending。
- reconnect/backoff/max-retry 已有 role runtime 证据（L2）。
- observability/metrics/audit 已有可替换 sink 与门禁，不夸大为部署级 sink 完成。
- 安全分区已有配置级门禁，不夸大为部署级合规完成。

## 8. 状态上调

- `I-NFR-002`：补齐 reconnect/backoff/max-retry runtime 证据。
- `I-NFR-003`：补齐采集/发布/写入/reconnect 指标事件门禁。
- `I-SCR-001`：由文档+边界提升到配置级门禁。

## 9. 状态下调

- `I-FR-002` 从“运行闭环通过”校正为“测试通过（Kafka true E2E CI pending）”。

## 10. 暂不支持

- ingest production adapter 仍未支持：`iec101/modbus_rtu/mqtt/http_rest/goose/sv`。

## 11. CI pending

- `tests/integration/test_ingest_source_cache_message_kafka_e2e.py`：
  - 当前环境缺 `testcontainers/kafka-python`。
  - CI 建议命令：`pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q`

## 12. 证据不足

- ingest performance/load gate 本轮未执行（保留“测试未执行”）。
- 生产级 observability/audit sink 部署验证仍缺。
- 安全分区部署态（非样例配置）验证仍缺。

## 13. 是否完成需求验证闭环

- 结论：**是（按需求核验闭环标准）**。
- 说明：需求表已全部更新并无“待核实”；未完成项已明确标注为“部分实现/CI pending/测试未执行”，无状态夸大。

## 14. 剩余风险

- Kafka true E2E 依赖容器环境，当前仅 CI pending。
- 生产部署级 sink 与安全分区仍需环境化验证。
- ingest 性能压测结果未归档。

## 15. 后续建议

- 在 CI 补跑 Kafka container E2E 并归档消费断言结果。
- 增加部署配置驱动的安全分区 smoke。
- 补一组 ingest 轻量 load gate（采集/发布/写入 dry_run）。
