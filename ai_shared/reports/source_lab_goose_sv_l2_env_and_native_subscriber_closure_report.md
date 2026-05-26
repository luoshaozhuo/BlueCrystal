# source_lab GOOSE/SV L2 Env And Native Subscriber Closure Report

## A. 执行环境与 capability

- 日期：2026-05-26
- 工作目录：`/home/luosh/Whale`
- 宿主机用户：`uid=1000`, `euid=1000`
- 宿主机 `CapEff`：`0000000000000000`
- 受控 L2 环境：`unshare -Urn` 私有 network namespace + `veth` pair
- 测试接口：`sl_pub0`（publisher），`sl_sub0`（subscriber）
- 说明：
  - 宿主机 `lo/eth0` 在前序轮次已证明不能稳定形成同机 GOOSE/SV 可观测闭环。
  - 本轮通过 rootless user namespace 获取私有 netns 内的 `root` 权限，并在 netns 内建立 `veth` 对打环境。
  - 该环境用于验证真实 raw-socket event/sample，不将宿主机 `lo/eth0` failed 改写为 pending。

## B. GOOSE subscriber crash 根因与修复

- 根因：
  - 原 `iec61850_goose_subscriber_runner` 依赖 `libiec61850` receiver/subscriber 接收路径，在宿主机接口上存在启动早期崩溃风险。
  - 该路径在无流量、接口不可用或权限不足时无法稳定给出 `ERROR + non-zero exit`，而是直接 `Segmentation fault`。
- 修复：
  - 将 `GOOSE/SV subscriber` 收包逻辑改为更薄的 `AF_PACKET` raw socket 解析。
  - 保留真实 L2 帧接收，不伪造 event/sample。
  - 增加参数校验、接口存在校验、`READY / NOTIFY / STREAM_SUMMARY / DONE / ERROR` 明确输出协议。
  - 无权限或接口错误时返回明确 `ERROR`，不再崩溃。
- 回归：
  - `pytest tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py -q` -> `5 passed`

## C. L2 测试环境方案

- 方案：`unshare -Urn` + `veth` pair
- 脚本：
  - `scripts/source_lab_l2_test_env.sh`
  - `scripts/run_source_lab_l2_standalone_gate.sh`
- 接口：
  - `sl_pub0 <-> sl_sub0`
  - `setup` 时额外执行 `ip link set lo up`，避免 netns 内 TCP/HTTP 本地测试受影响。
- 清理：
  - `teardown` 删除 `sl_pub0` 或 `sl_sub0`
  - 幂等，重复调用不会报错退出

## D. Standalone publisher/subscriber 结果

- GOOSE：
  - `bash scripts/run_source_lab_l2_standalone_gate.sh`
  - 结果：`GOOSE_STANDALONE_PASS app_id=1000 publisher_iface=sl_pub0 subscriber_iface=sl_sub0 count=6`
- SV：
  - 同上
  - 结果：`SV_STANDALONE_PASS app_id=4000 publisher_iface=sl_pub0 subscriber_iface=sl_sub0 count=3`
- 结论：
  - 在可控 L2 环境中，standalone native publisher/subscriber 已可产生真实 `EVENT/SAMPLE`。
  - `GOOSE subscriber` 不再 crash。

## E. E2E 结果

- 命令：
  - `unshare -Urn bash -lc 'cd /home/luosh/Whale && source <(bash scripts/source_lab_l2_test_env.sh setup) && trap "bash scripts/source_lab_l2_test_env.sh teardown >/dev/null 2>&1 || true" EXIT && pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs'`
- 结果：
  - `6 passed in 38.96s`
- 说明：
  - `GOOSE/SV facade subscribe`
  - `GOOSE/SV streaming capacity`
  - `GOOSE/SV streaming profile`
  - 均已在受控 L2 环境里拿到 true PASS。

## F. Dynamic isolation 结果

- 命令：
  - `unshare -Urn bash -lc 'cd /home/luosh/Whale && source <(bash scripts/source_lab_l2_test_env.sh setup) && trap "bash scripts/source_lab_l2_test_env.sh teardown >/dev/null 2>&1 || true" EXIT && pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs'`
- 结果：
  - `7 passed in 26.36s`
- 覆盖：
  - `GOOSE stop/pause/update params`
  - `SV stop/pause/update params`
  - unaffected endpoint continuity
  - `affected_endpoints / unaffected_endpoints` journal

## G. Continuity 证据

- true PASS 判据已满足：
  - unaffected endpoint 的 `endpoint_event_count / endpoint_sample_count` 持续增长
  - unaffected endpoint 的 `endpoint_stream_restart_count` 不增加
  - `stagger_offset_changed=false`
  - `endpoint_callback_gap_count` 不越出测试容差
- 本轮对 GOOSE stop 场景补了更符合 1s 发布周期的 callback gap 容差：
  - `endpoint_callback_gap_count <= previous + 1`
  - `endpoint_callback_max_gap_ms <= 2500`

## H. Journal 证据

- dynamic isolation 测试继续校验：
  - `STOP_ENDPOINT` / `PAUSE_ENDPOINT` / `UPDATE_ENDPOINT`
  - `affected_endpoints`
  - `unaffected_endpoints`
  - `dynamic_operation_result=SUCCESS`

## I. 修改文件

- `tools/source_lab/native/libiec61850/iec61850_goose_subscriber_runner.c`
- `tools/source_lab/native/libiec61850/iec61850_sv_subscriber_runner.c`
- `tools/source_lab/access/runners/iec61850_l2_streaming.py`
- `tools/source_lab/protocols/iec61850/simulator.py`
- `tools/source_lab/tests/access/_dynamic_runtime_test_utils.py`
- `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py`
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py`
- `scripts/source_lab_l2_test_env.sh`
- `scripts/run_source_lab_l2_standalone_gate.sh`
- `tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py`

## J. 测试结果

- `pytest tools/source_lab/tests/access/test_iec61850_l2_native_runner_failure_modes.py -q` -> `5 passed`
- `bash scripts/run_source_lab_l2_standalone_gate.sh` -> `GOOSE_STANDALONE_PASS`, `SV_STANDALONE_PASS`
- `pytest tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py -q` -> `2 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs` -> `6 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs` -> `7 passed`
- `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> `3 passed`
- `unshare -Urn ... pytest tools/source_lab/tests/access -q` -> `734 passed, 3 skipped`
- `unshare -Urn ... pytest tools/source_lab/tests -q` -> `743 passed, 12 skipped`

## K. 判定

- GOOSE standalone：true PASS
- SV standalone：true PASS
- GOOSE E2E：true PASS
- SV E2E：true PASS
- GOOSE dynamic isolation：true PASS
- SV dynamic isolation：true PASS

## L. 剩余风险与下一步

- 宿主机 `lo/eth0` 仍不应作为 GOOSE/SV 同机闭环的默认通过环境；应优先使用受控 `veth/netns`。
- rebuild 后 file capability 可能丢失；若在宿主机直接跑 raw-socket gate，仍需重新 `setcap` 或使用具备权限的 runner。
- 当前 subscriber 以最小 L2 帧过滤和 APPID 匹配为主，已满足 event/sample continuity 验证；若未来需要更深的 GOOSE/SV 负载字段断言，可继续增强 frame parser。
