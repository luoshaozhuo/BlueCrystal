"""Tests for subscribe source update policy validation."""

from __future__ import annotations

import pytest

from tools.source_lab.access.polling.model import CapacityMode
from tools.source_lab.access.subscribe.model import SubscribeScanConfig


def test_subscribe_config_allows_update_hz_below_sample_hz() -> None:
    config = SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=200.0,
        sampling_interval_ms=200.0,
        queue_size=1,
        duration_s=1.0,
        source_update_enabled=True,
        source_update_hz=4.0,
        progress_enabled=False,
    )

    assert config.source_update_hz == 4.0


def test_subscribe_config_allows_lower_update_hz_when_updates_disabled() -> None:
    config = SubscribeScanConfig(
        mode=CapacityMode.FIELD,
        protocol="opcua",
        server_count_start=1,
        server_count_step=1,
        server_count_max=1,
        process_count=1,
        publishing_interval_ms=200.0,
        sampling_interval_ms=200.0,
        queue_size=1,
        duration_s=1.0,
        source_update_enabled=False,
        source_update_hz=1.0,
        progress_enabled=False,
    )

    assert config.source_update_enabled is False
    assert config.source_update_hz == 1.0
