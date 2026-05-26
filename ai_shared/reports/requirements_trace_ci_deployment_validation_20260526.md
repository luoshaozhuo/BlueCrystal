# requirements_trace_ci_deployment_validation_20260526

## 1. 本次范围

- source_lab + ingest 的剩余 CI / 部署态验证归档：
  - Kafka true E2E
  - GOOSE/SV true PASS 条件确认
  - ingest lightweight load gate
  - observability / audit sink smoke
  - security partition deployment/config smoke

## 2. 环境探测

- `id -u` -> `1000`
- `capsh --print` -> 当前进程无生效 `CAP_NET_RAW`
- `ip link` -> 可用接口：`lo`, `eth0`, `loopback0`
- `docker --version` -> 可用
- `docker info` -> `DOCKER_OK`
- `sudo -n true` -> 返回 `1`，当前无免密 sudo

## 3. Kafka true E2E 结果

- 先补测试依赖：
  - `pyproject.toml` 增加 `testcontainers[kafka]>=4.13,<5.0`（dev/test 依赖）
  - 当前环境执行：`python -m pip install 'testcontainers[kafka]>=4.13,<5.0'`
- 执行：
  - `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q`
- 结果：
  - `1 passed`
- 结论：
  - Kafka true E2E 已从 CI pending 推进到真实归档通过。
  - 已验证消息真实写入 Kafka topic，consumer 可消费，payload 包含 envelope / schema_version / trace_id / message_id / item_count / value / quality / timestamp。

## 4. GOOSE/SV true PASS 结果

- 探测结果：
  - 当前不是 root，且当前进程无生效 `CAP_NET_RAW`
- 本轮补 native target 构建：
  - `cmake -S tools/source_lab/native -B tools/source_lab/native/build`
  - `cmake --build tools/source_lab/native/build --target iec61850_goose_subscriber_runner iec61850_sv_subscriber_runner iec61850_goose_publisher_simulator iec61850_sv_publisher_simulator`
- 执行：
  - `pytest -k "goose or sv" tools/source_lab/tests/access -q -rs`
- 结果：
  - `54 passed, 12 skipped, 577 deselected`
  - skip 原因统一收敛为 `raw_socket_permission_missing`
- 结论：
  - GOOSE/SV 仍是 CI pending，不能写 true PASS。
  - 本轮已确认不是功能失败，而是权限条件缺失。
- CI 命令：
  - `sudo -E env SOURCE_LAB_L2_INTERFACE=lo pytest -k "goose or sv" tools/source_lab/tests/access -q`

## 5. ingest load gate 结果

- 新增：
  - `tests/integration/test_ingest_lightweight_load_gate.py`
- 执行：
  - `pytest tests/integration/test_ingest_lightweight_load_gate.py -q`
- 结果：
  - `1 passed`
- 覆盖：
  - `source -> cache` batch N
  - `cache -> message` batch N
  - `write command dry_run` batch N
- 记录：
  - 通过 `IngestMetricsPort` 采集 `duration_ms`
  - 校验 `batch_count / item_count / values/sec / max duration / failure_count`
- 结论：
  - 已完成 lightweight load gate 归档；
  - 不等同重型 performance/stress 验证。

## 6. observability/audit sink smoke 结果

- 新增：
  - `src/whale/ingest/adapters/observability/file_sinks.py`
  - `tests/unit/test_ingest_observability_sink.py`
  - `tests/integration/test_ingest_observability_sink_smoke.py`
- 结果：
  - `pytest tests/unit/test_ingest_observability_sink.py -q` -> `2 passed`
  - `pytest tests/integration/test_ingest_observability_sink_smoke.py -q` -> `1 passed`
- 结论：
  - JSONL/file sink 作为 deployment-ready 示例已验证。
  - 这表示“可替换 sink 已验证”，不表示 Prometheus/OTel/正式审计平台已接入。

## 7. security partition deployment/config smoke 结果

- 执行：
  - `pytest tests/unit/test_ingest_security_partition_config.py -q`
  - `pytest tests/integration/test_ingest_security_partition_smoke.py -q`
- 结果：
  - `1 passed`
  - `1 passed`
- 结论：
  - 样例配置门禁与 smoke 已通过。
  - 仍只能写“样例配置/配置级验证通过”，不能写“生产部署态完全通过”。

## 8. 更新文件

- `pyproject.toml`
- `src/whale/ingest/adapters/observability/__init__.py`
- `src/whale/ingest/adapters/observability/file_sinks.py`
- `tests/unit/test_ingest_observability_sink.py`
- `tests/integration/test_ingest_observability_sink_smoke.py`
- `tests/integration/test_ingest_lightweight_load_gate.py`
- `tests/integration/test_ingest_security_partition_smoke.py`
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py`
- `tools/source_lab/tests/access/test_server_simulator_facade_real_protocol_smoke.py`
- `ai_shared/memory/Whale_REQ_SourceLab.md`
- `ai_shared/memory/Whale_REQ_Ingest.md`
- `ai_shared/memory/project_tree.md`

## 9. 执行测试

- `pytest tests/integration/test_ingest_source_cache_message_kafka_e2e.py -q` -> `1 passed`
- `pytest tests/unit/test_ingest_metrics_events.py -q` -> `1 passed`
- `pytest tests/unit/test_source_command_audit.py -q` -> `2 passed`
- `pytest tests/unit/test_ingest_security_partition_config.py -q` -> `1 passed`
- `pytest tests/unit/test_ingest_observability_sink.py -q` -> `2 passed`
- `pytest tests/integration/test_ingest_observability_sink_smoke.py -q` -> `1 passed`
- `pytest tests/integration/test_ingest_lightweight_load_gate.py -q` -> `1 passed`
- `pytest tests/integration/test_ingest_security_partition_smoke.py -q` -> `1 passed`
- `pytest tests/unit -q` -> `318 passed`
- `pytest tests/integration -q` -> `41 passed`
- `pytest -k "goose or sv" tools/source_lab/tests/access -q -rs` -> `54 passed, 12 skipped`

## 10. 需求状态变化

- 上调：
  - `I-FR-002` -> Kafka true E2E 真实通过，更新为 `运行闭环通过`
  - `I-FR-006` -> Kafka container 级完整链路归档通过，更新为 `运行闭环通过`
  - `I-NFR-001` -> lightweight load gate 已执行，更新为 `L2 / 测试通过`
  - `I-NFR-003` -> file/JSONL sink smoke 已验证，保持 `L2 / 测试通过` 但证据增强
  - `I-SCR-001` -> 样例配置 smoke 已验证，保持 `L2` 但证据增强
- 保持：
  - `SL-FR-002`, `SL-NFR-001`, `SL-NFR-002` 保持 CI pending 边界，不夸大
- 测试路径治理：
  - 修正 GOOSE/SV 两个 access 测试文件的 native build 目录定位，消除错误的 `dependency_missing` 噪音

## 11. CI pending

- GOOSE/SV true PASS：
  - 需 root 或生效 `CAP_NET_RAW`
  - CI 命令：`sudo -E env SOURCE_LAB_L2_INTERFACE=lo pytest -k "goose or sv" tools/source_lab/tests/access -q`
- source_lab load gate：
  - `pytest -m load tools/source_lab/tests -q`
- ingest heavy performance/stress：
  - `pytest tests/performance -q`

## 12. 剩余风险

- GOOSE/SV 仍未获得 true PASS 归档。
- observability/audit 仍是 JSONL/file sink 级验证，不是正式生产平台接入。
- security partition 仍是样例配置/配置级 smoke，不是生产部署 profile 验证。

## 13. 后续建议

- 在具备权限的 runner 上补 GOOSE/SV true PASS 归档。
- 为 ingest 增加 production profile 驱动的安全分区 smoke。
- 把 JSONL/file sink 进一步对接到部署环境中的正式审计/指标后端。
