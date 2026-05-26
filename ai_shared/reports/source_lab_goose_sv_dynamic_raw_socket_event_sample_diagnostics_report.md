# source_lab GOOSE/SV Dynamic Raw Socket Event Sample Diagnostics Report

## A. 执行环境与 capability 证据

- 日期：`2026-05-26`
- 工作目录：`/home/luosh/Whale`
- 当前用户：
  - `uid=1000`
  - `euid=1000`
  - `CapEff=0000000000000000`
- 4 个 native binary 已显式具备 file capability：
  - `iec61850_sv_publisher_simulator cap_net_raw=ep`
  - `iec61850_sv_subscriber_runner cap_net_raw=ep`
  - `iec61850_goose_subscriber_runner cap_net_raw=ep`
  - `iec61850_goose_publisher_simulator cap_net_raw=ep`
- 可用接口：
  - `lo`：`UP`
  - `eth0`：`UP`
  - `loopback0`：`UP`
  - `eth1`：`DOWN`

结论：

- 本轮不再是 `raw_socket_permission_missing`。
- gate 已经进入真实 raw-socket runtime 分支。

## B. 接口诊断：lo / eth0 / 如有 veth

- `lo`
  - dynamic isolation：进入真实分支，但 GOOSE/SV unaffected endpoint 均未出现 `event/sample` 增长
  - E2E：GOOSE `3 failed, 3 passed`；SV 在 `lo` 下未形成稳定闭环
  - 典型报错：
    - `event/sample did not grow for goose-dyn-1`
    - `event/sample did not grow for sv-dyn-2`
    - `received no GOOSE event`
- `eth0`
  - dynamic isolation：进入真实分支，但 GOOSE/SV unaffected endpoint 均未出现 `event/sample` 增长
  - E2E：`6 failed`
  - 典型报错：
    - `received no GOOSE event`
    - `received no SV sample`
    - `received zero events/samples`
- `veth`
  - 本机无免密 `sudo`，无法在本轮自动创建 veth pair/bridge 进行额外二层回环试验

结论：

- 当前 `lo` 与 `eth0` 都不能形成稳定的同机 raw-socket GOOSE/SV 可观测闭环。
- 根因更接近“接口/二层环境不支持同机 publisher/subscriber 闭环”而不是 pytest/permission 问题。

## C. native publisher/subscriber 参数核对

### GOOSE

- publisher
  - interface：跟随 `SOURCE_LAB_L2_INTERFACE`
  - app_id：`1000 + index`
  - multicast MAC：`01:0C:CD:01:00:<app_id low byte>`
  - VLAN：`enabled=true`
  - goID：`GOOSESimulator`
  - GoCbRef：`Simulator/LLN0$GO$gcbEvents`
  - DataSetRef：`Simulator/LLN0$Events`
- subscriber
  - interface：跟随 `SOURCE_LAB_L2_INTERFACE`
  - app_id filter：与 publisher 一致
  - observer mode：开启

### SV

- publisher
  - interface：跟随 `SOURCE_LAB_L2_INTERFACE`
  - app_id：`4000 + index`
  - multicast MAC：`01:0C:CD:04:00:<app_id low byte>`
  - VLAN：`enabled=false`
  - smpRate：跟随 sample_rate
- subscriber
  - interface：跟随 `SOURCE_LAB_L2_INTERFACE`
  - app_id filter：与 publisher 一致

结论：

- 经过第6轮最小修复后，dynamic/E2E fixture 已不再把 `l2_interface` 硬编码为 `lo`。
- 从代码静态核对看，publisher/subscriber 的 `interface / app_id` 已一致。
- 当前没有证据表明是 GOOSE/SV 混用 EtherType 或 app_id 冲突。

## D. standalone/E2E/dynamic 分层诊断

### standalone

- `iec61850_goose_publisher_simulator eth0 1000 1000`
  - 连续输出 `SAMPLE`，说明 publisher 至少在运行和调用发布 API
- `iec61850_sv_publisher_simulator eth0 4000 1`
  - 连续输出 `SAMPLE`
- `iec61850_sv_subscriber_runner eth0 4000 20`
  - 输出 `READY`，结束时 `STREAM_SUMMARY 0 0`
  - 说明 subscriber 运行了，但没有收到任何 SV sample
- `iec61850_goose_subscriber_runner eth0 1000 5`
  - standalone 下出现 `Segmentation fault`

结论：

- standalone 层已经能证明：
  - publisher 不是完全没启动
  - SV subscriber 能运行但没收到帧
  - GOOSE subscriber 存在 native crash 风险

### E2E

- `lo`
  - `pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs`
  - 结果：`3 failed, 3 passed`
  - 失败集中在 GOOSE `received no GOOSE event`
- `eth0`
  - 同一测试结果：`6 failed`
  - GOOSE/SV 都表现为 `received no ...` / `zero events/samples`

### dynamic runtime

- `lo`
  - `4 failed, 3 passed`
- `eth0`
  - `6 failed, 1 passed`
- 失败发生在 unaffected endpoint continuity 断言阶段，不是 permission gate，也不是 registry 未启动

## E. 修改文件

- `tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py`
- `tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py`
- `tools/source_lab/access/runtime/endpoint_registry.py`
- `tools/source_lab/tests/access/_dynamic_runtime_test_utils.py`
- `tools/source_lab/tests/access/test_server_simulator_facade_capacity_profile_e2e.py`
- `ai_shared/memory/Whale_REQ_SourceLab.md`
- `ai_shared/memory/project_tree.md`

## F. GOOSE dynamic isolation 结果

- `lo`：`3 failed, 4 passed`
- `eth0`：`3 failed, 4 passed`
- 失败项：
  - `stop one app_id`
  - `pause one app_id`
  - `replace params`
- 失败证据：
  - `event/sample did not grow for goose-dyn-1`
- 判定：`failed`

## G. SV dynamic isolation 结果

- `lo`：`4 failed, 3 passed`
- `eth0`：`6 failed, 1 passed`
- 失败项：
  - `stop one app_id`
  - `pause one app_id`
  - `replace params`
- 失败证据：
  - `event/sample did not grow for sv-dyn-1`
  - `event/sample did not grow for sv-dyn-2`
- 判定：`failed`

## H. GOOSE/SV E2E 结果

- `lo`
  - `3 failed, 3 passed`
- `eth0`
  - `6 failed`
- 典型失败：
  - `received no GOOSE event`
  - `received no SV sample`
  - `received zero events/samples`
- 判定：
  - GOOSE E2E：`failed`
  - SV E2E：`failed`

## I. event/sample continuity 证据

- 本轮没有任何一条 GOOSE/SV dynamic 或 E2E 路径拿到可接受的 true PASS continuity 证据。
- 没有达到以下条件：
  - unaffected endpoint 的 `endpoint_event_count / endpoint_sample_count` 持续增长
  - unaffected endpoint 的 `endpoint_stream_restart_count` 不增加
  - unaffected endpoint 的 `endpoint_callback_gap_count` 不新增

## J. affected/unaffected journal 证据

- dynamic tests 已经进入真实 runtime 执行分支。
- 但由于 continuity 断言失败，没有形成可接受的 true PASS journal 证据。
- 只能确认：
  - 失败不是 permission skip
  - 失败发生在 start 后的真实运行阶段

## K. 测试结果

- 环境检查
  - `id`
  - `grep CapEff /proc/self/status`
  - 4 个 `getcap`
  - `ip link`
- gate
  - `SOURCE_LAB_L2_INTERFACE=lo bash scripts/run_source_lab_raw_socket_dynamic_gate.sh`
  - `SOURCE_LAB_L2_INTERFACE=eth0 bash scripts/run_source_lab_raw_socket_dynamic_gate.sh`
- 单测
  - `pytest tools/source_lab/tests/access/test_dynamic_goose_sv_permission_gate.py -q` -> `2 passed`
  - `pytest tools/source_lab/tests/access/test_dynamic_goose_sv_streaming_endpoint_adjustment.py -q -rs`
  - `pytest tools/source_lab/tests/access/test_iec61850_goose_sv_streaming_e2e.py -q -rs`
  - `pytest tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py -q` -> `3 passed`
- standalone 诊断
  - GOOSE publisher：持续 `SAMPLE`
  - SV publisher：持续 `SAMPLE`
  - SV subscriber：`STREAM_SUMMARY 0 0`
  - GOOSE subscriber：`Segmentation fault`

## L. true PASS 或 failed 判定

- GOOSE dynamic isolation：`failed`
- SV dynamic isolation：`failed`
- GOOSE E2E：`failed`
- SV E2E：`failed`

## M. 若 failed，根因分类与下一步

根因分类：

- `C. native subscriber 未收到帧`
- `B. native publisher 未证明同机同接口闭环可见`
- `G. 其他：GOOSE subscriber standalone 存在 native crash 风险`

更具体地说：

- GOOSE：
  - subscriber 有 crash 风险
  - 即使不 crash，也没有形成 `event_count` 增长
- SV：
  - subscriber 能运行，但 `STREAM_SUMMARY=0`
  - 更像是同机同接口二层帧没有回到 receiver

下一步建议：

- 在具备专用二层测试网络的 runner 上执行：
  - publisher / subscriber 位于可确认互通的 L2 环境
  - 或由用户提供可用的 veth/bridge/namespace 方案
- 若继续在本机推进：
  - 优先定位 `iec61850_goose_subscriber_runner` 的 crash
  - 然后验证 libiec61850 对“同机同接口自发自收”的支持边界
- 在拿到真实 `event/sample` 增长前，不得把 GOOSE/SV 状态上调为 true PASS。
