# source_lab tests

## Active access path

- `tools/source_lab/access` capacity core is protocol-agnostic orchestration.
- The current implemented capacity runner is OPC UA `open62541`.
- `field_probe.py` and `field_capacity.py` use file-based field inputs.
- Capacity no longer performs preflight.
- `open62541_serial_polling.py` is a runner adapter, not the capacity core.
- `FieldFileSourceProvider` is the primary field `profile_id` provider.
- `FieldSourceProvider` is retained only for simple static endpoint/points cases and compatibility tests.

## Field input notes

- `field_servers.tsv` and `signal_profile_items.tsv` are the field input pair.
- `profile_id` binds server rows to point rows.
- Non-OPC UA protocols are loaded but phase-1 execution reports `SKIP unsupported_protocol`.
- `field_capacity.py` writes timestamped or `--run-id`-tagged report filenames to avoid overwriting prior field runs.

## Explicitly unsupported

- `asyncua`
- Python high-frequency scheduler
- backend selector envs
- legacy C runner `PREPARE/READ` protocol

## Recommended validation

```bash
python -m py_compile tools/source_lab/access/*.py tools/source_lab/access/runners/*.py tools/source_lab/access/providers/*.py tools/source_lab/*.py
python -m pytest tools/source_lab/tests/access -q
python -m pytest tools/source_lab/tests/test_factory.py -q
python -m pytest tools/source_lab/tests/test_open62541_source_simulation_single_server_smoke.py -q
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_capacity.py -q
python -m pytest tools/source_lab/tests/test_source_simulation_multi_server_profile.py -q
python -m mypy tools/source_lab/access tools/source_lab/field_probe.py tools/source_lab/field_capacity.py
```
