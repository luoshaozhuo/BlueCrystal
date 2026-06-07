"""source_lab native components.

Native layout:

- `open62541/open62541_simulator_server.c`
- `open62541/open62541_client_runner.c`
- `open62541/open62541_subscription_runner.c`

Current contract:

- simulator, polling, and subscribe are `open62541` only
- no backend selector is provided
- Python talks to native runners over stdin/stdout text protocols
- native runners stay executables, not shared libraries
- polling and subscribe keep separate runner protocols
- Python keeps orchestration, CLI, report writing, and metrics aggregation
- source_lab does not provide a Python async reader or Python async subscription callback path
- legacy native `PREPARE/READ` has been deleted
- simulator server internal update cadence comes from runtime config records written by Python (`update_enabled`, `update_interval_ms`); it must not rely on a fixed native default when subscribe capacity changes sample rate per combo

Polling protocol rows from `open62541_client_runner`:

- `READY`
- `START_SERIAL_POLL`
- `ENDPOINT`
- `END_SERIAL_POLL`
- `RESULT`
- `RUNNER_SUMMARY`
- `POLL_DONE`
- `STOP_POLL`
- `QUIT`

Subscribe protocol rows from `open62541_subscription_runner`:

- `READY`
- `START_SUBSCRIBE`
- `ENDPOINT`
- `END_SUBSCRIBE`
- `NOTIFY`
- `SUB_SUMMARY`
- `SUB_DONE`
- `STOP_SUBSCRIBE`
- `QUIT`
- `ERROR`

Subscribe notes:

- subscribe startup staggering focuses on connect/session/subscription/monitored-item creation, not per-read offsets
- native subscribe stdout must stay protocol-only; open62541 logging is disabled instead of being parsed from stdout
- zero stdout noise is the normal target; Python's stdout noise handling is defensive only and should stay at `runner_protocol_noise_count == 0` in normal integration tests
- Python keeps native stderr for diagnostics only and does not parse protocol from stderr
- `NOTIFY` is a data-change event emitted after the native data-change callback has run and the runner flushes the batch. It is not a separate publish-response stream.
- `NOTIFY` exposes a local notification sequence, `data_age_ms`, a callback-time monotonic `notify_ts_s`, and a later flush/adapter `recv_ts_s`
- `NOTIFY` also exposes `flush_ts_s`, a monotonic timestamp captured when the native runner flushes the protocol row
- `notify_ts_s` and `flush_ts_s` share the same monotonic clock basis and are the only valid source for callback-to-flush lag
- `recv_ts_s` is retained for receive/emit diagnostics and must not be mixed with monotonic timestamps for lag math
- native subscribe emits at most one `NOTIFY` event per endpoint per `UA_Client_run_iterate()` call
- callbacks inside one `run_iterate()` are aggregated into one publish-cycle-like notify event
- callbacks are not merged across multiple `run_iterate()` calls
- open62541 client subscriptions in this runner do not currently expose standalone stdout events for keepalive, empty publish, or publish timeout. The runner only observes those indirectly through summary counters and timing gaps.
- `SUB_ENDPOINT_DIAG` exposes per-endpoint native scheduling diagnostics:
  - `notification_count`
  - `run_iterate_count`
  - `max_dispatch_gap_ms`
  - `max_run_iterate_duration_ms`
  - revised publishing/sampling intervals reported by open62541
- native subscribe scheduling is deadline-based rather than fixed `for`-loop busy polling:
  - endpoints are revisited on a short due-time cadence
  - short sleeps prevent CPU busy loops from starving the simulator/source processes
  - event flush still happens after each `run_iterate()` to preserve notify boundaries
- simulator internal source updates are also deadline-based so `source_update_hz` does not drift just because a `1ms` tick loop slipped
- first-version subscribe does not detect real OPC UA publish sequence gaps
- first-version subscribe does not detect real queue overflow
- when the Python capacity layer cannot observe a response cadence independent of data-change cadence, it must fail the combo with explicit reason `feedback_period_unobservable;source_update_hz=...<sample_hz=...`

Memory ownership notes:

- each monitored item allocates one `MonitoredItemContext`
- successful monitored items are owned by the endpoint until native delete callback or endpoint cleanup
- delete callbacks unlink and free the context
- endpoint cleanup performs fallback context freeing after client disconnect/delete in case library shutdown paths skip callbacks

Generated output:

- `tools/source_lab/native/build/` is the local CMake build directory
- it should not be committed

Build:

```bash
cmake -S tools/source_lab/native \
  -B tools/source_lab/native/build \
  -DCMAKE_PREFIX_PATH=$HOME/.local/open62541

cmake --build tools/source_lab/native/build
```
"""
