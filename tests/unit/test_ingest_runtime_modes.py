"""Runtime mode parsing tests."""

from __future__ import annotations

import pytest

from whale.ingest.runtime.modes import RuntimeMode


def test_runtime_mode_parse_known_values() -> None:
    assert RuntimeMode.parse("standalone") is RuntimeMode.STANDALONE
    assert RuntimeMode.parse("ACTIVE_STANDBY") is RuntimeMode.ACTIVE_STANDBY
    assert RuntimeMode.parse("dual_active_partitioned") is RuntimeMode.DUAL_ACTIVE_PARTITIONED
    assert RuntimeMode.parse("cluster") is RuntimeMode.CLUSTER


def test_runtime_mode_parse_rejects_unknown_value() -> None:
    with pytest.raises(ValueError):
        RuntimeMode.parse("invalid-mode")
