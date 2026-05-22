# source_lab tests

This package covers the access helpers, facade wiring, and the smoke wrappers used by source_lab field-capacity commands.

Subscribe capacity expectations:

- `p95_ms` / `max_ms` on the capacity summary map to subscribe `data_period_*` verdict fields.
- `response_period_*` stays diagnostic-only and does not trigger default FAIL.
- `sample_hz < source_update_hz` no longer causes a synthetic precheck `FAIL`; those combos must still execute and be judged by runtime verdict fields such as `max_ms`.
- `value_ratio` stays observational and does not force a default failure.

Smoke checks should keep the distinction visible:

- `source_update_hz=10`, `sample_hz=5` should remain runnable and be judged by runtime verdict metrics.
- `source_update_hz=10`, `sample_hz=10` should remain runnable and eligible for `PASS`.

## Active access paths

- Polling core lives in `tools/source_lab/access/polling/`.
- Subscribe core lives in `tools/source_lab/access/subscribe/`.
- Shared helpers live in `tools/source_lab/access/common/`.
- Probe stays in `tools/source_lab/access/probe.py`.
- Polling uses `access/runners/open62541_serial_polling.py` plus native `open62541_client_runner`.
- Subscribe uses `access/runners/open62541_subscription.py` plus native `open62541_subscription_runner`.
- `field_probe.py`, `field_capacity.py`, and `field_profile.py` all read `field_servers.tsv` + `signal_profile_items.tsv` using `profile_id` as the binding key.
- `field_capacity.py --access-mode subscribe` is the only supported subscribe-capacity CLI entrypoint.
- `field_profile.py --access-mode subscribe` is the only supported subscribe-profile CLI entrypoint.
- `field_subscribe.py` has been deleted and is no longer supported.

## Fixture semantics

- `tools/source_lab/tests/fixtures/db_export/` holds schema-contract fixtures for parser and loader tests. These files are not expected to be live-reachable endpoints.
- `tools/source_lab/tests/fixtures/simulator/` holds simulator-backed fixtures for smoke and multi-server execution tests. These rows declare `source_lab_runtime=simulator` so field providers auto-expand into localhost fleets.
- Do not point live smoke commands at the `db_export` fixtures. They intentionally preserve export shape, not runnable connectivity.
- Top-level multi-server capacity/profile smoke tests are thin wrappers around the formal production CLIs. Pytest is responsible only for fixtures, env, subprocess execution, stdout/stderr replay, and artifact assertions.
- `tools/source_lab/tests/access/` remains the lightweight unit/service validation layer for parser, metrics, reporter, runner, and CLI argument wiring.
- Simulator-backed field providers allocate runtime ports via bind-probing and skip occupied ports inside `SOURCE_SIM_PORT_START..SOURCE_SIM_PORT_END`.
- Fleet startup can be throttled with `SOURCE_SIM_FLEET_START_CONCURRENCY` and `SOURCE_SIM_FLEET_START_STAGGER_MS` when high server counts are unstable.
- Capacity wrappers are intentionally thin:
  - running on a TTY shows one single-line progress bar on stderr
  - non-TTY runs stay silent during execution
  - completion prints one summary table on stdout
- Polling and subscribe capacity wrappers print the same summary table:
  - `proc`, `srv`, `hz`, `period_ms`, `value_ratio`, `p95_ms`, `max_ms`, `status`, `reason`
- Those summary fields come from the final selected attempt for the row:
  - `PASS` uses the passing attempt
  - `FLAKY` uses the recovered attempt
  - `FAIL` uses the final failed attempt
- Capacity no longer has a console detail table. `SOURCE_LAB_CAPACITY_TABLE_MODE=detail` is deprecated; diagnostics belong to profile.
- Polling summary `p95_ms` / `max_ms` comes from adjacent `response_timestamp_s` values.
- Subscribe summary `p95_ms` / `max_ms` comes from adjacent native notify-event timestamps per server/endpoint.
- Subscribe falls back to `received_ns` only when `notify_ts_s` / `notify_timestamp_ns` is absent, and records warning `notify_timestamp_missing_fallback_received_ns`.
- Subscribe `source_period_*` comes from adjacent source/server timestamps carried in values and is diagnostic only.
- Subscribe `recv_period_*` comes from adjacent `received_ns` values and is diagnostic only.
- Subscribe `callback_to_flush_lag_*` comes only from monotonic `flush_timestamp_ns - notify_timestamp_ns` and is diagnostic only.
- Subscribe profile also carries endpoint dispatch diagnostics from the native runner:
  - `dispatch_gap_max_ms`
  - `run_iterate_duration_max_ms`
  - `top_dispatch_gap_traces`
- Missing monotonic flush timestamps produce warning `callback_to_flush_lag_unavailable`; negative monotonic lag samples produce warning `negative_callback_to_flush_lag`.
- Capacity thresholds must be recorded explicitly when comparing runs:
  - polling:
    - `SOURCE_SIM_POLL_PERIOD_MAX_TOLERANCE_RATIO`
    - `SOURCE_SIM_POLL_PERIOD_MEAN_ERROR_RATIO`
  - subscribe:

- `0.2` is the strict default boundary.
- `0.5` may be useful for rough field scouting.
- Results collected under different tolerance values are not directly comparable.

## Protocol support

- Phase 1 field execution support is OPC UA only.
- Non-OPC UA rows remain visible and are reported as `SKIP unsupported_protocol`.
- `protocol_filtered` rows remain explicit in field CLIs and probe output.
- `asyncua`, backend selector envs, Python async polling/subscription schedulers, and legacy native `PREPARE/READ` remain unsupported.

## Subscribe test notes

- Subscribe tests now cover:
  - stdout protocol noise diagnostics and overflow failure
  - immediate `ERROR` row failure
  - stderr summaries being attached to runner failures
  - `data_age_*` naming instead of `latency_*`
  - unified `data_period_*` naming
  - reserved sequence/queue counters not causing false FAIL
- Simulator subscribe tests keep a lighter point subset than polling to stay reviewable.
- Keep source updates enabled when you expect sustained data-change notifications.
- When source updates are disabled intentionally, expected failures should still report the real reason and include `source_update_disabled` only as a warning.
- Subscribe `value_ratio` is observational by default and must not be treated as the default FAIL/stop criterion in capacity smoke tests.
- Subscribe default FAIL uses notify-period `data_period_max_ms`, not `source_period_max_ms`.
- Capacity table reasons now shorten notify/period threshold failures to `max=...>limit`, and that value must match the summary `max_ms` field from the same selected attempt.
- Subscribe `max_ms` is the hard PASS criterion. `p95_ms` is observation only.
- Subscribe profile diagnostics must not be used as the PASS/FAIL verdict:
  - `recv_period_*` is receive/emit cadence
  - `callback_to_flush_lag_*` is local callback-to-flush overhead
  - `max_ms` remains the verdict field
- Subscribe capacity modes:
  - auto-match simulator mode: leave `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ` unset so each sample-hz combo runs the simulator at the same update rate
  - explicit-source-rate mode: set `SOURCE_SIM_SUB_SOURCE_UPDATE_HZ`; combos still run even when `sample_hz < source_update_hz`, and verdicts come from runtime metrics rather than a synthetic precheck
- `SOURCE_SIM_SUB_SOURCE_UPDATE_ENABLED=false` disables source-rate validation and adds warning `source_update_disabled`; use it only for observation against an externally updated server.
- Native subscribe heartbeat/reconnect follow-up remains per-endpoint by design:
  - detect stale endpoints independently
  - reconnect only the affected endpoint
  - continue honoring `reconnect_stagger_ms`

## Output and artifacts

- Native runner `stdout` remains reserved for protocol rows; diagnostics belong on `stderr`.
- Capacity CLI/service runs write CSV and JSONL artifacts.
- Subscribe capacity artifacts record `effective_source_update_hz` and the tolerance settings; compare runs only when both match.
- Profile runs write a text report, optional pyinstrument text output, and a JSON summary when an output directory is provided.
- `field_profile.py` now prints the full diagnostics report to stdout first, then prints the one-line artifact summary.
- Use profile for diagnostics such as `expected_values`, `values`, `value_miss`, `notify`, `created_items`, `publish_gap_*`, `data_age_*`, `recv_period_*`, `source_period_*`, `callback_to_flush_lag_*`, `top_period_gap_traces`, `top_flush_lag_traces`, `top_dispatch_gap_traces`, CPU/RSS, and runner traces.
- Prefer short subscribe smoke runs in this test layer; formal long-duration capacity sweeps should be executed separately.
- Use subscribe profile/report output to inspect top notify gaps, top callback-to-flush lag, and endpoint dispatch diagnostics when `max_ms` fails.
- Single-config subscribe profile still requires `source_update_hz >= sample_hz`.
- Subscribe capacity derives `sampling_interval_ms` from `sample_hz`; `--sampling-interval-ms` is intentionally rejected by `field_capacity.py`.
- Subscribe capacity CLI supports both fixed and ramped source update rates:
  - fixed: `--source-update-hz 50`
  - ramp: `--source-update-hz-start 10 --source-update-hz-step 20 --source-update-hz-max 50`
- Capacity/profile command examples should always record the intended `warmup` value.

## Recommended validation

```bash
cmake -S tools/source_lab/native -B tools/source_lab/native/build -DCMAKE_PREFIX_PATH=$HOME/.local/open62541
cmake --build tools/source_lab/native/build
python -m py_compile tools/source_lab/access/**/*.py tools/source_lab/*.py
python -m pytest tools/source_lab/tests/access -q
python -m pytest tools/source_lab/tests/test_factory.py -q
python -m pytest tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py -q
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_capacity.py -q -s
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_polling_profile.py -q -s
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_capacity.py -q -s
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_subscribe_profile.py -q -s
python -m mypy tools/source_lab/access tools/source_lab/field_probe.py tools/source_lab/field_capacity.py tools/source_lab/field_profile.py
```

### Simulator env naming guidance

- Polling runs should prefer `SOURCE_SIM_POLL_*` envs.
- `SOURCE_SIM_LOAD_*` is deprecated and rejected for polling paths.
- Subscribe runs should use `SOURCE_SIM_SUB_*` envs.
- Subscribe `value_ratio` is observational by default and should not be treated as a hard fail metric unless explicit policy is added.
- Capacity progress mode env switches such as `SOURCE_LAB_PROGRESS_MODE` are no longer part of the supported interface.
