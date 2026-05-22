# source_lab access

## Layout

- `common/`: shared access-mode types and helpers.
  - `access_model.py`: normalized batch and worker-summary rows shared by `read_once`, polling, and subscribe.
  - `cpu.py`, `io.py`, `scheduling.py`, `utils.py`: shared field-input, scheduling, and CLI utilities.
- `polling/`: polling-only capacity orchestration.
  - `model.py`, `capacity.py`, `worker.py`, `metrics.py`, `reporter.py`
- `subscribe/`: subscribe-only scan orchestration.
  - `model.py`, `scan.py`, `worker.py`, `metrics.py`, `reporter.py`, `capacity_scan.py`
- `capacity.py`: public façade for capacity scan/service entrypoints.
- `field_capacity.py`: field-capacity request/result models, summary-table rendering, artifact writing, and field-capacity orchestration.
- `providers/`: source providers shared by polling and subscribe.
- `runners/`: protocol runner interfaces plus native open62541 adapters.
- `probe.py`: standalone `read_once` probe path.

## Polling

- Polling uses `access/runners/open62541_serial_polling.py` backed by native `open62541_client_runner`.
- Polling capacity rows now include unified delivery metrics:
  - `expected_values`
  - `values`
  - `value_ratio`
  - `value_miss`
  - `points_per_server`
  - `point_total`
  - `reads` / `batches`
- Polling `data_period_*` is derived from adjacent `ReadResponse.responseHeader.timestamp` values exposed as `response_timestamp_s`.
- Polling capacity summary uses:
  - `data_period_p95_ms`
  - `data_period_max_ms`
- Polling `data_period_*` still represents adjacent `response_timestamp_s` periods.
- Polling keeps per-read scheduling offsets inside the native polling runner.
- Polling does not call probe/preflight and does not restore Python schedulers, backend selector logic, or legacy `PREPARE/READ`.

## Subscribe

- Subscribe uses `access/runners/open62541_subscription.py` backed by native `open62541_subscription_runner`.
- Subscribe metrics currently report:
  - `notification_count`
  - `value_count`
  - `bad_count`
  - `missing_ts_count`
  - `publish_gap_mean_ms`
  - `publish_gap_p95_ms`
  - `publish_gap_p99_ms`
  - `publish_gap_max_ms`
  - `data_age_mean_ms`
  - `data_age_p95_ms`
  - `data_age_max_ms`
  - `data_period_p95_ms`
  - `data_period_max_ms`
  - `keepalive_count`
  - `reserved_sequence_gap_count`
  - `reserved_queue_overflow_count`
- Subscribe summary `p95_ms` / `max_ms` always map to `data_period_p95_ms` / `data_period_max_ms`.
- Subscribe `data_period_*` is the client-side data-notify cadence derived from adjacent `notify_timestamp_ns` values and falls back to `received_ns` only when native notify timestamps are unavailable.
- Subscribe `source_period_*` is derived from adjacent source/server timestamps and remains diagnostic only.
- Subscribe capacity rows now also include:
  - `expected_values`
  - `values`
  - `value_ratio`
  - `value_miss`
  - `expected_items`
  - `created_items`
  - `points_per_server`
  - `point_total`
- Subscribe capacity summary `response_period_*` is receive-side diagnostic cadence only and does not drive default PASS/FAIL.
- `data_period_*` is the capacity verdict series and may legitimately be lower-frequency than `sample_hz` when `source_update_hz < sample_hz`.
- `notify_ts_s` is captured in the native open62541 data-change callback using a monotonic clock, then parsed into `AccessBatch.notify_timestamp_ns`.
- `flush_ts_s` is captured when the native runner flushes the `NOTIFY` line using the same monotonic clock, then parsed into `AccessBatch.flush_timestamp_ns`.
- Native subscribe emits at most one notify event per endpoint per `UA_Client_run_iterate()` call. Multiple callbacks inside one iterate are aggregated into one publish-cycle-like event, and events are not merged across multiple `run_iterate()` calls.
- The native open62541 client path does not currently expose separate keepalive or empty-publish stdout events. `keepalive_count` is available only in the native summary row, not as a per-event stream.
- `recv_ts_s` is retained as a compatibility receive/emit timestamp for diagnostics and should not be mixed with monotonic notify/flush timestamps.
- If `notify_ts_s` is unavailable, subscribe metrics fall back to `received_ns` and add warning `notify_timestamp_missing_fallback_received_ns`.
- Subscribe detail `recv_period_*` is derived from adjacent `received_ns` values and is diagnostic only.
- Subscribe detail `callback_to_flush_lag_*` is derived only from `flush_timestamp_ns - notify_timestamp_ns` and is diagnostic only.
- If monotonic flush timestamps are unavailable, subscribe metrics record warning `callback_to_flush_lag_unavailable` instead of fabricating a lag value.
- If a monotonic flush sample is negative, that sample is excluded and warning `negative_callback_to_flush_lag` is recorded.
- `publish_gap_*` is still the interval between received `NOTIFY` rows observed by this tool. It is diagnostic only and is not the main capacity stop criterion.
- `data_age_ms` is `receive_time - newest source/server timestamp`. It depends on source/server clocks and must not be interpreted as network latency.
- First-version subscribe does not detect real OPC UA `PublishResponse` sequence gaps. `reserved_sequence_gap_count` is reserved only and does not trigger PASS/FAIL.
- First-version subscribe does not detect real monitored-item queue overflow. `reserved_queue_overflow_count` is reserved only and does not trigger PASS/FAIL.
- Subscribe startup staggering is for connect/session/subscription/monitored-item creation, not per-read offsets.
- Subscribe does not use `asyncua`, backend selector envs, Python async callbacks, or legacy `PREPARE/READ`.
- Capacity console output is intentionally narrow:
  - during capacity scans, only one single-line progress bar is shown on TTY stderr
  - non-TTY runs stay silent during execution
  - after the scan completes, capacity prints only one summary table on stdout
- Capacity no longer supports a console detail table. `SOURCE_LAB_CAPACITY_TABLE_MODE=detail` is deprecated and ignored for stdout; use profile for diagnostics instead.
- Capacity summary table columns are fixed:
  - `proc`, `srv`, `hz`, `period_ms`, `value_ratio`, `p95_ms`, `max_ms`, `status`, `reason`
- Capacity summary rows always show metrics from the final selected attempt:
  - `PASS`: the passing attempt
  - `FLAKY`: the recovered attempt
  - `FAIL`: the final failed attempt
- Subscribe `value_ratio` is an observation metric by default. It is not used as the default FAIL/stop criterion.
- Subscribe capacity stop logic uses:
  - hard failures such as `created_items != expected_items`, `bad > 0`, `miss_ts > 0`, protocol noise, and publish/create failures
  - `data_period_max_ms <= (1000 / source_update_hz) * (1 + SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO)` when source updates are enabled
- Subscribe `response_period_max_ms` is diagnostic only. It may produce warning `high_response_period_max` but does not by itself fail a run.
- Subscribe does not use `source_period_max_ms` as the default FAIL criterion.
- Capacity CSV/JSONL artifacts keep both long internal field families for downstream compatibility: `response_period_p95_ms` / `response_period_max_ms` for verdicts, and `data_period_p95_ms` / `data_period_max_ms` for diagnostics.
- Native subscribe diagnostics also expose `dispatch_gap_max_ms`, `run_iterate_duration_max_ms`, and `top_dispatch_gap_traces` so client-dispatch jitter can be separated from source/publish jitter.
- Profile is the diagnostics entrypoint. Use profile for:
  - `expected_values`, `values`, `value_miss`
  - `notify`, `created_items`, `publish_gap_*`, `data_age_*`, `response_p95_ms`, `response_max_ms`, `data_p95_ms`, `data_max_ms`, `recv_period_*`, `source_period_*`, `callback_to_flush_lag_*`
  - `dispatch_gap_max_ms`, `run_iterate_duration_max_ms`, `top_dispatch_gap_traces`
  - CPU/RSS, runner traces, top notify gaps, top flush lags, top ages, and deeper performance analysis
- Formal CLI entrypoints are:
  - `python -m tools.source_lab.field_probe`
  - `python -m tools.source_lab.field_capacity --access-mode polling`
  - `python -m tools.source_lab.field_capacity --access-mode subscribe`
  - `python -m tools.source_lab.field_profile --access-mode polling`
  - `python -m tools.source_lab.field_profile --access-mode subscribe`
- `field_subscribe.py` has been deleted and must not be used for subscribe capacity runs.

## Runner protocol

- Native runner stdout must only emit structured protocol rows:
  - `READY`
  - `NOTIFY`
  - `SUB_ENDPOINT_DIAG`
  - `SUB_SUMMARY`
  - `SUB_DONE`
  - `ERROR`
- open62541 client logging is disabled in the native subscribe runner so library lifecycle logs do not pollute stdout.
- Python keeps `stderr` on a pipe for diagnostics only.
- Native stdout target is zero non-protocol output during normal operation.
- Python accepts a small amount of unexpected stdout noise only as a defensive guard, records `runner_protocol_noise`, retains the first few samples, and fails once noise exceeds a fixed threshold.
- Normal simulator-backed subscribe integration tests are expected to observe `runner_protocol_noise_count == 0`.
- `ERROR` protocol rows fail immediately.
- If a row is `FLAKY`, the summary still shows the recovered attempt's `data_period_*` values rather than the first failed attempt.
- Capacity console output stops at the single summary table; deeper diagnostics belong to profile or CSV/JSONL artifacts.
- Simulator-backed field providers now allocate runtime ports through bind-probing, so occupied ports in the configured range are skipped automatically instead of failing on first collision.
- Port allocation range is controlled by `SOURCE_SIM_PORT_START` and `SOURCE_SIM_PORT_END`.
- Fleet startup pressure can be tuned with `SOURCE_SIM_FLEET_START_CONCURRENCY` and `SOURCE_SIM_FLEET_START_STAGGER_MS` to reduce 20-server startup bursts.

## Field input model

## CLI contracts

## CLI examples

- `read_once` / probe:
  `python -m tools.source_lab.field_probe --servers field_servers.tsv --profile-items signal_profile_items.tsv --protocol opcua --samples 5`
- Polling capacity:
  `env SOURCE_SIM_FLEET_START_CONCURRENCY=4 SOURCE_SIM_FLEET_START_STAGGER_MS=15 SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=30 python -m tools.source_lab.field_capacity --access-mode polling --servers field_servers.tsv --profile-items signal_profile_items.tsv --protocol opcua --process-counts 1 --server-counts 10,30 --hz 10,30 --duration 6 --warmup 1 --output-dir reports`
- Subscribe capacity:
  `env SOURCE_SIM_FLEET_START_CONCURRENCY=4 SOURCE_SIM_FLEET_START_STAGGER_MS=15 SOURCE_SIM_FLEET_STARTUP_TIMEOUT_S=30 python -m tools.source_lab.field_capacity --access-mode subscribe --servers field_servers.tsv --profile-items signal_profile_items.tsv --protocol opcua --process-counts 1 --server-counts 10,20 --sample-hz 20,40 --source-update-hz-start 10 --source-update-hz-step 20 --source-update-hz-max 30 --duration 6 --warmup 1 --queue-size 1 --output-dir reports`
- Polling profile:
  `python -m tools.source_lab.field_profile --access-mode polling --servers field_servers.tsv --profile-items signal_profile_items.tsv --protocol opcua --process-count 1 --server-count 50 --hz 20 --duration 10 --warmup 2 --runner-trace true --runner-trace-top-n 5 --output-dir reports`
- Subscribe profile:
  `python -m tools.source_lab.field_profile --access-mode subscribe --servers field_servers.tsv --profile-items signal_profile_items.tsv --protocol opcua --process-count 1 --server-count 50 --sample-hz 50 --source-update-hz 50 --duration 20 --warmup 3 --runner-trace true --runner-trace-top-n 5 --queue-size 1 --output-dir reports`

## Simulator env recommendations

- Polling capacity scan recommended env namespace: `SOURCE_SIM_POLL_*`.
  - `SOURCE_SIM_POLL_PROCESS_COUNT_START/STEP/MAX`
  - `SOURCE_SIM_POLL_SERVER_COUNT_START/STEP/MAX`
  - `SOURCE_SIM_POLL_HZ_START/STEP/MAX`
  - `SOURCE_SIM_POLL_DURATION_S`
  - `SOURCE_SIM_POLL_SOURCE_UPDATE_ENABLED`
  - `SOURCE_SIM_POLL_SOURCE_UPDATE_HZ`
  - `SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO`
  - `SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO`
- `SOURCE_SIM_LOAD_*` is deprecated and rejected for polling paths.
- Subscribe capacity scan namespace remains `SOURCE_SIM_SUB_*`.
- Subscribe frequency semantics are split deliberately:
  - `sample_hz` is the client subscription sampling/publishing target.
  - `source_update_hz` is the server/source data update rate.
  - subscribe capacity verdict targets `subscription feedback period`.
  - current native runner exposes only data-change-driven `NOTIFY` rows; it does not expose standalone keepalive/empty-publish events.
- Subscribe simulator mode is fail-fast by default:
  - if `SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED=true`, `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ` must be set explicitly
  - leaving `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ` unset raises a config error to prevent implicit auto-match behavior
- Subscribe capacity treats `source_update_hz` as an independent scan dimension:
  - use `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_VALUES` or `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_START/STEP/MAX`
  - each scan combination records `effective_source_update_hz`
- Subscribe no longer short-circuits `sample_hz < source_update_hz` combos with a synthetic precheck failure.
- Those combinations still execute and are judged by runtime verdict metrics such as `data_period_max_ms`.
- If `SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED=false`, subscribe capacity skips source-rate validation and records warning `source_update_disabled`; those results are observation-only and are not directly comparable with source-update-enabled runs.
- Subscribe capacity scans should explicitly record:
  - `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ` or `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ_*`
  - `SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO`
- `value_ratio` for subscribe is an observation metric by default, not a hard fail threshold. If simulator updates are not full-rate for every point, do not interpret subscribe `value_ratio` as packet-loss rate.
- Polling failure reasons now use `data_period_max_ms=...>limit` so the reason text matches the summary field semantics.
- Polling console summary `p95_ms` / `max_ms` still comes from adjacent `response_timestamp_s` periods.
- Subscribe console summary `p95_ms` / `max_ms` comes from adjacent native notify-event timestamps and is the response-period verdict series.
- Because keepalive/empty publish events are not exposed today, `response_period_*` is currently `data_notify_proxy` when observable.
- `data_period_*` remains source/server timestamp diagnostics only and must not be used as the subscribe verdict.
- Subscribe profile diagnostics never affect capacity PASS/FAIL:
  - `recv_period_*` is receive/emit cadence only
  - `callback_to_flush_lag_*` is callback-to-flush local overhead only
  - `max_ms` remains the subscribe hard verdict
- When subscribe `max_ms` fails, inspect diagnostics in this order:
  - `top_period_gap_traces` for the real notify gaps
  - `top_flush_lag_traces` to rule out callback-to-flush or stdout lag
  - `top_dispatch_gap_traces` and `dispatch_gap_max_ms` for client endpoint scheduling / `run_iterate()` cadence
  - `source_period_*` plus revised interval diagnostics to determine whether the simulator/source loop, not the client runner, slipped
- Subscribe CSV/JSONL artifacts record `effective_source_update_hz`; keep that value together with tolerance when comparing runs.
- Capacity output stays summary-only; use profile, not capacity detail tables, for diagnostics.
- Prefer short subscribe smoke runs for this loop; reserve formal long capacity sweeps for separate execution.
- Capacity progress env mode switches such as `SOURCE_LAB_PROGRESS_MODE` are no longer part of the supported capacity interface.
- Capacity thresholds should be treated as explicit recorded inputs, not hidden assumptions:
  - strict boundary scans usually use `0.2`
  - rough field scouting may use `0.5`
  - results collected under different tolerance values are not directly comparable
- Recommended explicit threshold examples:
  - polling:
    - `SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO=0.2`
    - `SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO=0.05`
  - subscribe:
    - `SOURCE_SIM_SUB_DATA_PERIOD_MAX_TOLERANCE_RATIO=0.2`
- Current native subscribe runner already exposes per-endpoint `keepalive_count`, `publish_timeout_count`, and `last_notify_ns`-derived gaps. Per-endpoint heartbeat/reconnect remains a follow-up task:
  - detect stale endpoints independently
  - reconnect only the stale endpoint
  - honor `reconnect_stagger_ms`
- Subscribe capacity public entrypoints are:
  - `tools.source_lab.access.capacity` (cross-mode facade)
  - `tools.source_lab.access.subscribe.capacity` (subscribe-specific service facade)
  - `tools.source_lab.access.subscribe.capacity_scan` (low-level matrix execution)
