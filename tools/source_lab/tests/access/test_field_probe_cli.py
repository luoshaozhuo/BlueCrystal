"""Tests for the formal ``field_probe`` CLI wiring."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.source_lab.access.polling.model import CapacityStatus, ProbeConfig, ProbeLatencyStats, ProbeResult, ServerProbeResult
from tools.source_lab.field_probe import main


def _write(path: Path, text: str) -> None:
    """Write one UTF-8 fixture file used by CLI tests.

    Args:
        path: Target file path.
        text: File content without the final newline requirement.
    """

    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_input_files(tmp_path: Path) -> tuple[Path, Path]:
    """Create minimal field input files for CLI tests.

    Args:
        tmp_path: Temporary test directory.

    Returns:
        Tuple of ``servers`` and ``items`` file paths.
    """

    servers = tmp_path / "field_servers.tsv"
    items = tmp_path / "signal_profile_items.tsv"
    _write(
        servers,
        "endpoint_id\tprofile_id\tapplication_protocol\ttransport\thost\tport\nep-1\tpf-1\topcua\ttcp\t127.0.0.1\t4840",
    )
    _write(
        items,
        "profile_id\trelative_path\tdata_type_id\tln_name\tdo_name\npf-1\tIED1.LD0.WPPD1.TotW\tFLOAT64\tWPPD1\tTotW",
    )
    return servers, items


def test_field_probe_cli_builds_probe_config_and_prints_tsv(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify probe CLI forwards config and prints the expected TSV columns."""

    servers, items = _write_input_files(tmp_path)
    observed: list[ProbeConfig] = []

    def _fake_run_probe(config: ProbeConfig, sources: tuple[object, ...]) -> ProbeResult:
        """Capture the probe config and return one stable result row."""

        del sources
        observed.append(config)
        return ProbeResult(
            config=config,
            rows=(
                ServerProbeResult(
                    endpoint_id="ep-1",
                    profile_id="pf-1",
                    protocol="opcua",
                    host="127.0.0.1",
                    port=4840,
                    point_count=1,
                    tcp_status="PASS",
                    protocol_status="PASS",
                    readable_count=1,
                    expected_count=1,
                    latency=ProbeLatencyStats(
                        min_ms=1.0,
                        mean_ms=2.0,
                        p95_ms=3.0,
                        p99_ms=4.0,
                        max_ms=5.0,
                    ),
                    missing_ts=False,
                    status=CapacityStatus.PASS,
                    reason="",
                ),
            ),
        )

    monkeypatch.setattr("tools.source_lab.field_probe.build_field_runtime_sources", lambda *args, **kwargs: ())
    monkeypatch.setattr("tools.source_lab.field_probe.run_probe", _fake_run_probe)

    exit_code = main(
        [
            "--servers", str(servers),
            "--profile-items", str(items),
            "--protocol", "opcua",
            "--samples", "5",
            "--timeout", "6",
            "--tcp-timeout", "4",
            "--concurrency", "8",
        ]
    )

    stdout = capsys.readouterr().out
    config = observed[0]
    assert exit_code == 0
    assert config.protocol == "opcua"
    assert config.samples == 5
    assert config.timeout_s == 6.0
    assert config.tcp_timeout_s == 4.0
    assert config.concurrency == 8
    assert "endpoint_id\tprofile_id\tprotocol" in stdout
    assert "latency_mean_ms" in stdout
    assert "ep-1\tpf-1\topcua" in stdout
