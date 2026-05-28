"""Short-duration endurance smoke for the prodlike ingest compose profile."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.support.ingest_prodlike_runtime import docker_available


@pytest.mark.integration
def test_endurance_smoke_script_emits_report(tmp_path: Path) -> None:
    if not docker_available():
        pytest.skip("Docker environment unavailable for endurance smoke")

    report_dir = tmp_path / "endurance-report"
    result = subprocess.run(
        [
            "bash",
            "scripts/run_ingest_prodlike_endurance_smoke.sh",
            "--duration-seconds",
            "30",
            "--job-count",
            "4",
            "--poll-interval-ms",
            "500",
            "--failure-profile",
            "none",
            "--report-dir",
            str(report_dir),
        ],
        cwd=Path(__file__).resolve().parents[2],
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout

    report_path = report_dir / "ingest_prodlike_endurance_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert report["duration_seconds"] == 30
    assert report["job_started_count"] >= 1
    assert report["job_completed_count"] >= 1
    assert report["redis_write_success_count"] >= 1
    assert report["kafka_publish_success_count"] >= 1
    assert report["audit_event_count"] >= 1
    assert report["graceful_shutdown_result"] == "SUCCESS"
