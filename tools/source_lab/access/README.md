# source_lab access

## Current architecture

- `capacity.py` is the protocol-agnostic capacity orchestration layer.
- Runner-specific logic is outside capacity core.
- The current implemented capacity runner is OPC UA `open62541`.
- `open62541_serial_polling.py` is a runner adapter, not the capacity core.
- `field_probe.py` is a standalone field connectivity and latency probe tool.
- `field_capacity.py` is a standalone file-driven field capacity scan tool.

## Field input model

- Field input is loaded from `field_servers.tsv` and `signal_profile_items.tsv`.
- `profile_id` is the binding key from server rows to profile item rows.
- Different servers may share one `profile_id`.
- Different servers may use different `profile_id` values.
- File loading validates required fields and enabled filtering before execution.
- `FieldFileSourceProvider` is the main field provider for the `profile_id`-bound现场 path.
- `FieldSourceProvider` is only a simple static `endpoints + points` provider for basic scenarios and compatibility tests.

## Protocol boundary

- Multi-protocol file models are supported at the loader/provider boundary.
- Current execution support is only for OPC UA `open62541`.
- Non-OPC UA protocols are reported as `SKIP unsupported_protocol` in phase 1.
- Protocol-filtered rows are reported explicitly by `field_probe` and `field_capacity`; unsupported requested protocols are skipped without fake execution.
- Capacity core does not perform protocol probing or TCP checks.
- Probe is independent from capacity and is never called by `capacity.py`.

## Output behavior

- `field_capacity.py` writes CSV and JSONL reports with a timestamped filename by default.
- `field_capacity.py --run-id <value>` can be used to keep a caller-provided run identifier in report filenames.

## Explicitly unsupported

- `asyncua`
- Python high-frequency scheduler
- backend selector envs
- legacy C runner `PREPARE/READ` protocol
- Python async source reader path
