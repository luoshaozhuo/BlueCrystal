# source_lab Test Audit

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
