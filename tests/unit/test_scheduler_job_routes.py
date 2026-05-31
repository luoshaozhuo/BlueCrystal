"""QA-5: scheduler_job stagger_offset_ms 持久化端到端测试。

验证 create_scheduler_job API 中的 stagger_offset_ms 通过 config_json 正确持久化，
patch 操作也正确更新该值。现有测试完全未覆盖该 API。
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _build_client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'scheduler-job.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app), session_factory


def test_create_scheduler_job_persists_stagger_offset(tmp_path) -> None:
    """创建 scheduler job 时 stagger_offset_ms 应通过 config 持久化。"""
    client, _ = _build_client(tmp_path)

    create_resp = client.post(
        "/api/v1/scheduler-jobs",
        json={
            "job_id": "job-stagger-1",
            "job_type": "acquisition",
            "enabled": True,
            "priority": 100,
            "config": {"interval_ms": 1000},
            "stagger_offset_ms": 500,
        },
        headers={"x-actor": "tester"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["stagger_offset_ms"] == 500
    # config 中不应包含 stagger_offset_ms（已从 config 分离）
    assert "stagger_offset_ms" not in created["config"]

    # 重新读取验证持久化
    get_resp = client.get(
        f"/api/v1/scheduler-jobs/{created['job_id']}",
        headers={"x-actor": "tester"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["stagger_offset_ms"] == 500


def test_create_scheduler_job_no_stagger_offset(tmp_path) -> None:
    """不传 stagger_offset_ms 时响应中应为 null。"""
    client, _ = _build_client(tmp_path)

    create_resp = client.post(
        "/api/v1/scheduler-jobs",
        json={
            "job_id": "job-no-stagger",
            "job_type": "acquisition",
            "enabled": True,
            "priority": 100,
            "config": {"interval_ms": 1000},
        },
        headers={"x-actor": "tester"},
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["stagger_offset_ms"] is None


def test_patch_scheduler_job_updates_stagger_offset(tmp_path) -> None:
    """PATCH scheduler job 应能更新 stagger_offset_ms。"""
    client, _ = _build_client(tmp_path)

    create_resp = client.post(
        "/api/v1/scheduler-jobs",
        json={
            "job_id": "job-patch-stagger",
            "job_type": "acquisition",
            "enabled": True,
            "priority": 100,
            "config": {"interval_ms": 1000},
        },
        headers={"x-actor": "tester"},
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["job_id"]
    version = create_resp.json()["version"]

    patch_resp = client.patch(
        f"/api/v1/scheduler-jobs/{job_id}",
        json={"expected_version": version, "stagger_offset_ms": 300},
        headers={"x-actor": "tester"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["stagger_offset_ms"] == 300


def test_patch_scheduler_job_clears_stagger_offset(tmp_path) -> None:
    """PATCH 如果不传 stagger_offset_ms，现有值应保持不变（不是清除）。"""
    client, _ = _build_client(tmp_path)

    create_resp = client.post(
        "/api/v1/scheduler-jobs",
        json={
            "job_id": "job-clear-stagger",
            "job_type": "acquisition",
            "enabled": True,
            "priority": 100,
            "config": {"interval_ms": 1000},
            "stagger_offset_ms": 200,
        },
        headers={"x-actor": "tester"},
    )
    assert create_resp.status_code == 201
    job_id = create_resp.json()["job_id"]
    version = create_resp.json()["version"]
    assert create_resp.json()["stagger_offset_ms"] == 200

    # 不传 stagger_offset_ms 的 PATCH
    patch_resp = client.patch(
        f"/api/v1/scheduler-jobs/{job_id}",
        json={"expected_version": version, "priority": 99},
        headers={"x-actor": "tester"},
    )
    assert patch_resp.status_code == 200
    # stagger_offset_ms 不应被清除
    assert patch_resp.json()["stagger_offset_ms"] == 200
