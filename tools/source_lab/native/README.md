"""source_lab native components.

Native layout:

- `open62541/open62541_simulator_server.c`
- `open62541/open62541_client_runner.c`

Current contract:

- simulator and access capacity are `open62541` only
- no backend selector is provided
- Python talks to the client runner over stdin/stdout text protocol
- the client runner stays an executable, not a shared library
- the client runner only supports the serial polling protocol
- capacity polling runs inside the C runner as serial absolute fixed-rate polling
- Python keeps orchestration and metrics only
- source_lab does not provide a Python async reader layer
- legacy single-read prepare/read mode has been deleted
- warmup may perform reads, but warmup does not contribute to formal `total/ok/bad/read_errors`
- each endpoint executes at most one read per main loop iteration; overdue periods become `missed_ticks`

Protocol rows emitted by `open62541_client_runner`:

- `READY`
- `START_SERIAL_POLL`
- `ENDPOINT`
- `END_SERIAL_POLL`
- `RESULT` with both `local_index` and `global_index`
- `RUNNER_SUMMARY` with measurement-only counts plus warmup-only counts and maxima
- `POLL_DONE`
- `STOP_POLL`
- `QUIT`

Generated output:

- `tools/source_lab/native/build/` is a local build directory used for CMake builds
- it should not be committed

Build:

```bash
cmake -S tools/source_lab/native \
  -B tools/source_lab/native/build \
  -DCMAKE_PREFIX_PATH=$HOME/.local/open62541

cmake --build tools/source_lab/native/build
```
"""
