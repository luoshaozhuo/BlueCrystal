"""Security partition sample-config smoke."""

from __future__ import annotations

from pathlib import Path

import yaml


def test_security_partition_example_config_declares_required_zones_and_flows() -> None:
    path = Path(__file__).resolve().parents[2] / "config" / "ingest" / "security_partition.example.yaml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert config["zones"]["ingest"] == "zone_ingest"
    assert config["zones"]["source"] == "zone_source"
    assert config["zones"]["cache"] == "zone_cache"
    assert config["zones"]["mq"] == "zone_mq"

    flows = {(entry["from"], entry["to"], entry["purpose"]) for entry in config["flows"]}
    assert ("zone_source", "zone_ingest", "acquisition") in flows
    assert ("zone_ingest", "zone_cache", "state_cache_write") in flows
    assert ("zone_cache", "zone_ingest", "snapshot_read") in flows
    assert ("zone_ingest", "zone_mq", "publish") in flows

    policy = config["policy"]
    assert policy["write_control_requires_separate_approval"] is True
    assert policy["simulator_forbidden_in_production"] is True
    assert policy["production_forbid_tools_source_lab_import"] is True
