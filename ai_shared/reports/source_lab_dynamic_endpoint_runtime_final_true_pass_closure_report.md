# source_lab Dynamic EndpointRuntime Final True PASS Closure Report

## A. 收口范围

本报告仅归档 `tools/source_lab` 动态 EndpointRuntime 的最终 true PASS 证据链，不改变 `ingest` / `shared_source` 边界，不将 `source_lab` 提升为生产 runtime。

## B. 分轮证据链

- Round 1
  - 建立 endpoint-level runtime 骨架
  - 完成 Modbus TCP / HTTP REST / MQTT 的局部调整验证
  - 完成 partial fleet lifecycle、continuity metrics、operation journal、runtime state recovery
- Round 2
  - 接入 OPC UA polling / subscription endpoint isolation
  - 补齐 audit / rollback / patch matrix
  - 完成 state store resilience
- Round 3
  - 接入 IEC61850 Report endpoint runtime
  - 建立 GOOSE/SV streaming runtime 框架
  - 完成 accepted-state CLI、interactive boundary 归档
- Round 4
  - 完成 permission gate
  - 完成 accepted-state redaction、state store retention / repair
- Round 5 / 6
  - after-setcap 后进入真实 raw-socket 分支
  - 诊断宿主机 `lo/eth0` 同机 L2 闭环失败
  - 定位 GOOSE subscriber crash 与 raw-socket event/sample 不增长问题
- Round 7
  - 建立 `unshare -Urn + veth pair` 受控 L2 环境
  - 修复 GOOSE subscriber crash
  - 完成 GOOSE/SV standalone、E2E、dynamic isolation true PASS

## C. 最终能力矩阵

| 能力 | 协议/模式 | 状态 | 关键证据 |
|---|---|---|---|
| endpoint registry CRUD | all dynamic modes | true PASS | `tools/source_lab/access/runtime/endpoint_registry.py`; `test_dynamic_operation_journal_audit.py` |
| polling dynamic isolation | modbus/http/opcua | true PASS | `test_dynamic_polling_endpoint_adjustment.py`; `test_dynamic_opcua_polling_endpoint_adjustment.py` |
| subscription dynamic isolation | mqtt/opcua | true PASS | `test_dynamic_subscription_endpoint_adjustment.py`; `test_dynamic_opcua_subscription_endpoint_adjustment.py` |
| report dynamic isolation | iec61850_report | true PASS | `test_dynamic_iec61850_report_endpoint_adjustment.py` |
| streaming dynamic isolation | goose/sv | true PASS | `test_dynamic_goose_sv_streaming_endpoint_adjustment.py`; `source_lab_goose_sv_l2_env_and_native_subscriber_closure_report.md` |
| continuity metrics | polling/sub/report/streaming | true PASS | `continuity_monitor.py`; `continuity_model.py`; dynamic tests |
| operation journal | all dynamic operations | true PASS | `operation_journal.py`; `test_dynamic_operation_journal_audit.py` |
| state store | local tool persistence | true PASS | `state_store.py`; `test_dynamic_runtime_state_store_integrity.py`; `test_dynamic_runtime_state_store_retention.py`; `test_dynamic_runtime_state_store_repair_cli.py` |
| CLI accepted state | export/import/validate/schema | true PASS | `dynamic_cli.py`; `test_dynamic_cli.py`; `test_dynamic_cli_accepted_state.py` |

## D. GOOSE/SV 特殊环境说明

- GOOSE/SV 的最终 true PASS 不是在宿主机 `lo/eth0` 上取得。
- 最终 true PASS 运行环境为：
  - `unshare -Urn`
  - `veth pair: sl_pub0 <-> sl_sub0`
- 宿主机 `lo/eth0` 失败结论仍保留：
  - 它们不是可靠的同机 GOOSE/SV 闭环验证环境。
- 后续 GOOSE/SV CI 推荐环境：
  - 受控 `veth/netns`
  - 或具备真实 L2 可达性的 runner
- rebuild 后如果直接在宿主机 binary 上跑 raw socket：
  - 仍可能需要重新 `setcap`
  - 或使用 `root/CAP_NET_RAW`

## E. 最终测试结果归档

- `pytest tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py -q` -> `5 passed`
- `bash scripts/run_source_lab_l2_standalone_gate.sh` -> `GOOSE_STANDALONE_PASS`, `SV_STANDALONE_PASS`
- `pytest tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py -q` -> `2 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> `6 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs` -> `7 passed`
- `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> `3 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access -q` -> `734 passed, 3 skipped`
- `unshare -Urn ... pytest tools/source_lab/tests -q` -> `743 passed, 12 skipped`

## F. 最终剩余风险

1. GOOSE/SV 深层 payload 字段断言仍可后续增强；当前以最小 L2 frame filter + APPID 匹配满足 event/sample continuity。
2. `source_lab` RuntimeStateStore 是工具级本地持久化，不是生产 secret storage。
3. GOOSE/SV CI 应优先使用受控 `veth/netns`；直接使用宿主机 `lo/eth0` 不稳定。
