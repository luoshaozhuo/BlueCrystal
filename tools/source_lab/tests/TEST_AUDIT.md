# source_lab Test Audit

> 最后更新：2026-06-03（Round 2 治理，添加生命周期术语对齐说明）
> 状态：本文档内容由历史审计积累而成。文件级审计表在 Round 2 中未全量重写，
> 仅添加生命周期术语对齐说明和边界声明。部分条目仍使用旧 `L1-L4` 证据等级术语，
> 建议第 3 轮治理时统一迁移。

## 生命周期术语对齐

本文件在历史 rounds 中使用了 `L1 (unit/mock)`、`L2 (contract/stub)`、`L3 (simulator)`、
`L4 (integration)`、`L4+` 等证据等级术语。这些术语已迁移为 ``ai_shared/rules/testing.md``
定义的七个生命周期阶段。

旧术语与生命周期阶段的对应关系（仅用于理解本文件中的历史表述）：

| 历史证据等级 | 当前生命周期阶段 | 说明 |
|---|---|---|
| L1 (unit/mock) | 开发期验证 | mock/fake/stub，无外部依赖 |
| L2 (contract/stub) | 开发期验证 | 接口契约验证，stub 闭环 |
| L3 (simulator) | 模块集成期验证 | subprocess simulator 或 in-memory 全链路 |
| L4 (integration) | 跨模块联调期验证 或 准生产依赖验证期 | docker-compose 或 real external services |
| environment-pending | NOT_RUN: MISSING_ENVIRONMENT | 标记环境不满足时的跳过 |

**注意**：上述对应关系是近似的。部分文件中的 L4 可能对应模块集成期（SQLite/TestClient），
也可能对应准生产依赖验证期（真实 Kafka/PG/Redis）。以 `ai_shared/memory/test_index.md`
和测试文件头的当前说明为准。

## source_lab 测试边界

source_lab 测试只证明 source_lab **工具自身** 的行为（parser、metrics、reporter、
runner、factory、CLI、facade、simulator、native runner 协议）。
不证明 Whale 主平台的生产链路行为。

如果 source_lab 变更影响 ``src/whale/shared/source/`` 或 ``src/whale/ingest/``，
需在 Whale 侧额外验证。扩跑条件见 ``tools/source_lab/tests/README.md`` 和
``ai_shared/memory/test_index.md`` 第 6 节。

## 测试结果术语

本审计文件的后续审计工作使用 PASS / FAIL / NOT_RUN 三元结果，不再使用 ``pending``、
``skipped`` 或 ``env-pending`` 作为测试执行结果。pytest skip/xfail 在报告中转写为 NOT_RUN。

## 第 3 轮治理建议

以下项建议在第 3 轮处理：

1. 审计表中 ``L1``-``L4`` 术语统一替换为生命周期阶段名称。
2. ``env-pending`` 标记统一转写为 ``NOT_RUN: MISSING_ENVIRONMENT``。
3. 清理或标注不再维持的测试文件（如 ``test_field_subscribe_cli.py`` 已删除的记录）。
4. 补充 `keep/rewritten/strengthened/new/deleted` 等 Action 字段与当前文件真实状态的一致性校验。

## 文件级审计表

| Test file | Status | Action | Reason | Coverage |
| --- | --- | --- | --- | --- |
| tools/source_lab/tests/test_factory.py | keep | keep | Directly validates simulator factory protocol dispatch path. | tools/source_lab/factory.py protocol normalization and build selection. |
| tools/source_lab/tests/test_fleet_startup_controls.py | keep | keep | Still validates fleet startup throttling controls used by simulator-backed tests. | tools/source_lab/fleet.py start concurrency and stagger behavior. |
| tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py | keep | keep | Still exercises native single-server smoke path. | open62541 simulator/server/client end-to-end smoke path. |
| tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py | rewritten | route through formal CLI | Pytest now prepares simulator env/output-dir and executes `python -m tools.source_lab.field_capacity --access-mode polling` via subprocess. | Polling capacity CLI, service chain, summary-table stdout contract, and simulator-backed environment capacity. |
| tools/source_lab/tests/test_source_simulation_multi_server_polling_profile.py | rewritten | route through formal CLI | Pytest now executes `python -m tools.source_lab.field_profile --access-mode polling` and replays diagnostics stdout/stderr. | Polling profile CLI, diagnostics report stdout contract, artifact emission, and simulator-backed environment profiling. |
| tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py | rewritten | route through formal CLI | Pytest now executes `python -m tools.source_lab.field_capacity --access-mode subscribe` with source-update/sample-hz matrix args and warmup. | Subscribe capacity CLI, source-update-hz ramp wiring, summary-table stdout contract, and simulator-backed environment capacity. |
| tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py | rewritten | route through formal CLI | Pytest now executes `python -m tools.source_lab.field_profile --access-mode subscribe` and replays diagnostics stdout/stderr. | Subscribe profile CLI, diagnostics report stdout contract, artifact emission, and simulator-backed environment profiling. |
| tools/source_lab/tests/access/test_access_config.py | keep | keep | Covers env parsing, tolerance limits, and subscribe source-update configuration semantics. | tools/source_lab/access/config.py env contracts. |
| tools/source_lab/tests/access/test_access_facades.py | strengthened | update subscribe matrix verdict expectations | Facade tests now assert that low sample-hz combos still execute and are judged by runtime results instead of synthetic precheck FAILs. | tools/source_lab/access/capacity.py and tools/source_lab/access/profile.py dispatch behavior. |
| tools/source_lab/tests/access/test_access_metrics.py | keep | keep | Validates shared polling metrics helpers including SKIP builder behavior for probe/unsupported paths. | tools/source_lab/access/polling/metrics.py shared result builders. |
| tools/source_lab/tests/access/test_access_probe.py | keep | keep | Still validates probe contract and failure reason shaping. | tools/source_lab/access/probe.py read-once path. |
| tools/source_lab/tests/access/test_access_progress_reporting.py | keep | keep | Verifies progress reporting integration and non-regression for scan flows. | tools/source_lab/access/common/progress.py and scan reporting integration. |
| tools/source_lab/tests/access/test_access_reporter.py | keep | keep | Exercises report rendering semantics used by profile/capacity outputs. | tools/source_lab/access reporter-level formatting and trace rendering. |
| tools/source_lab/tests/access/test_access_scheduling.py | keep | keep | Validates scheduling helpers used by polling/subscribe scans. | tools/source_lab/access/common/scheduling.py. |
| tools/source_lab/tests/access/test_access_structure.py | strengthened | update supported CLI list | Structure checks now assert only the active root CLIs remain importable. | Structural constraints for access package decomposition and legacy CLI absence. |
| tools/source_lab/tests/access/test_access_worker.py | keep | keep | Covers worker-level execution path and aggregation contracts. | access worker orchestration behavior in active polling/subscribe paths. |
| tools/source_lab/tests/access/test_capacity_progress.py | keep | keep | Not legacy shim; validates active progress bar behavior for capacity runs. | tools/source_lab/access/common/progress.py tty/non-tty semantics. |
| tools/source_lab/tests/access/test_capacity_reporter.py | keep | keep | Not legacy shim; validates active summary-only table output and subscribe p95/max mapping to data_period fields. | tools/source_lab/access/field_capacity.py table rendering contract. |
| tools/source_lab/tests/access/test_capacity_rows.py | keep | keep | Not legacy shim; validates selected-attempt metric mapping for PASS/FLAKY/FAIL rows. | build_polling_capacity_rows/build_subscribe_capacity_rows behavior. |
| tools/source_lab/tests/access/test_capacity_service.py | strengthened | expand subscribe request coverage | Service tests continue validating orchestration while now covering explicit CLI-driven request fields such as warmup/ramp through upstream tests. | run_field_capacity orchestration and warning/reason propagation. |
| tools/source_lab/tests/access/test_field_capacity_cli.py | strengthened | expand CLI wiring assertions | Added subscribe warmup propagation and source-update-hz ramp parsing coverage; removed wrapper assumptions. | tools/source_lab/field_capacity.py request construction and service dispatch contract. |
| tools/source_lab/tests/access/test_field_profile_cli.py | strengthened | align with full report stdout | Verifies diagnostics report printing plus summary line for polling and subscribe profile CLI runs. | tools/source_lab/field_profile.py request construction and stdout/report contract. |
| tools/source_lab/tests/access/test_field_probe_cli.py | new | add CLI wiring test | Added direct probe CLI argument and TSV stdout coverage without native runner startup. | tools/source_lab/field_probe.py parser, request construction, and TSV output contract. |
| tools/source_lab/tests/access/test_field_provider.py | keep | keep | Still validates runtime source building and provider behavior used by production scans. | build_field_runtime_sources and providers/* runtime expansion. |
| tools/source_lab/tests/access/test_field_subscribe_cli.py | deleted | remove obsolete wrapper test | `field_subscribe.py` was removed; subscribe capacity must now go through `field_capacity.py --access-mode subscribe`. | Obsolete compatibility wrapper removed from supported surface. |
| tools/source_lab/tests/access/test_opcua_access_adapter.py | keep | keep | Adapter integration test remains aligned with current OPC UA access adapter path. | OPC UA adapter behavior under access mode infrastructure. |
| tools/source_lab/tests/access/test_open62541_serial_polling_runner.py | keep | keep | Covers parser and zero-noise/overflow behavior for polling native runner. | tools/source_lab/access/runners/open62541_serial_polling.py protocol handling. |
| tools/source_lab/tests/access/test_open62541_subscription_runner.py | keep | keep | Parser coverage remains aligned with current native subscribe runner protocol contract. | tools/source_lab/access/runners/open62541_subscription.py summary parser and protocol contract. |
| tools/source_lab/tests/access/test_polling_metrics.py | keep | keep | Polling metric semantics still aligned and unaffected by subscribe changes. | tools/source_lab/access/polling/metrics.py evaluation logic. |
| tools/source_lab/tests/access/test_port_allocator.py | keep | keep | Still validates dynamic port allocation behavior used by simulator provider startup. | tools/source_lab/sources.py port allocation logic. |
| tools/source_lab/tests/access/test_profile_service.py | keep | keep | Service-level profile behavior remains production-aligned for polling and subscribe. | tools/source_lab/access/profile.py service orchestration and artifacts. |
| tools/source_lab/tests/access/test_subscribe_capacity_entrypoint.py | keep | keep | Keeps subscribe-specific capacity entrypoint contract explicit. | tools/source_lab/access/subscribe/capacity.py entrypoint contract. |
| tools/source_lab/tests/access/test_subscribe_capacity_reporter.py | keep | keep | Validates subscribe capacity wrapper path and summary table adapter behavior. | subscribe capacity wrapper and table/report pipeline. |
| tools/source_lab/tests/access/test_subscribe_scan.py | keep | keep | Validates attempt-selection semantics in subscribe scan core. | tools/source_lab/access/subscribe/scan.py confirmation-attempt logic. |
| tools/source_lab/tests/access/test_subscribe_update_policy.py | keep | keep | Covers source update policy behavior for subscribe scan config and outcomes. | subscribe update policy and related decision logic. |
| tools/source_lab/tests/access/test_subscription_metrics.py | keep | keep | Already covers independent source_update_hz/sample_hz semantics, data/source split, response warning-only, keepalive exclusion, value_ratio observational, unrecovered FAIL, resubscribe warning-only. | tools/source_lab/access/subscribe/metrics.py core subscribe verdict and diagnostics semantics. |

## CLI Entry Decision

- Decision: top-level multi-server smoke/load tests now validate the formal CLIs instead of calling service helpers directly.
- Actions:
  - rewrote the four top-level multi-server polling/subscribe capacity/profile tests to use subprocess-driven CLI execution
  - preserved `tools/source_lab/tests/access/` as the lightweight service/unit layer
  - removed the deprecated `field_subscribe.py` compatibility surface

## Notes

- `field_subscribe.py` and `tools/source_lab/tests/access/test_field_subscribe_cli.py` were intentionally deleted.
- Legacy forbidden root shim paths remain asserted absent by structure tests, and root CLI imports now cover `field_probe`, `field_capacity`, and `field_profile`.
