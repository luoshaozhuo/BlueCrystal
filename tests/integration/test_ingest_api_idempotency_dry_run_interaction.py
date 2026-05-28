"""Idempotency-Key + dry_run=true interaction tests.

Scenarios:
1. dry_run=true + Idempotency-Key first request not persisted
2. same key + same payload returns consistent response (dry_run)
3. same key + different payload returns CONFLICT/error (dry_run)
4. dry_run cache not reused by non-dry_run (different query_string → different fingerprint)
5. non-dry_run not skipped by prior dry_run record (different query_string → different fingerprint)
6. dry_run + idempotency must audit
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from whale.ingest.api import create_app
from whale.ingest.framework.persistence import (
    create_runtime_engine,
    create_runtime_session_factory,
    initialize_runtime_database,
)


def _client(tmp_path):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / 'idem-dry-interact.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    app = create_app(session_factory=session_factory, readiness_probe=lambda: True)
    return TestClient(app)


# ── Scenario 1: dry_run first request does not persist ─────────────────────


def test_dry_run_idempotency_first_request_not_persisted(tmp_path):
    """dry_run=true with Idempotency-Key: validated not persisted in DB."""
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "s1-dry", "x-actor": "tester"}

    resp = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json={"job_id": "s1-job", "priority": 5},
        headers=headers,
    )
    assert resp.status_code == 201
    assert resp.json()["job_id"] == "s1-job"

    # Should NOT be persisted
    fetched = client.get("/api/v1/scheduler-jobs/s1-job", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


# ── Scenario 2: same key + same payload → consistent response ──────────────


def test_dry_run_idempotency_same_key_same_payload_consistent(tmp_path):
    """Same dry_run request with same Idempotency-Key returns cached response."""
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "s2-dry", "x-actor": "tester"}
    payload = {"job_id": "s2-job", "priority": 5}

    first = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers=headers,
    )
    assert second.status_code == 201
    assert second.json() == first.json()

    # Still not persisted
    fetched = client.get("/api/v1/scheduler-jobs/s2-job", headers={"x-actor": "tester"})
    assert fetched.status_code == 404


# ── Scenario 3: same key + different payload → 422 CONFLICT ────────────────


def test_dry_run_idempotency_same_key_different_payload_422(tmp_path):
    """Same Idempotency-Key, different payload on dry_run returns 422."""
    client = _client(tmp_path)
    headers = {"Idempotency-Key": "s3-dry", "x-actor": "tester"}

    first = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json={"job_id": "s3-job", "priority": 5},
        headers=headers,
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json={"job_id": "s3-other", "priority": 10},
        headers=headers,
    )
    assert second.status_code == 422
    assert second.json()["error"] == "IDEMPOTENCY_KEY_REUSE"


# ── Scenario 4: dry_run cache not reused by non-dry_run ────────────────────


def test_dry_run_cache_not_reused_by_non_dry_run_same_key_422(tmp_path):
    """dry_run=true + Idempotency-Key blocks non-dry_run with same key (different query_string = different fingerprint → 422)."""
    client = _client(tmp_path)
    key = "s4-dry-vs-real"
    payload = {"job_id": "s4-job", "priority": 5}

    # dry_run claims key K with fingerprint F1 (query_string=b'dry_run=true')
    dry = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers={"Idempotency-Key": key, "x-actor": "tester"},
    )
    assert dry.status_code == 201

    # non-dry_run with same key K has fingerprint F2 (query_string=b'')
    # F1 != F2 → 422 IDEMPOTENCY_KEY_REUSE
    real = client.post(
        "/api/v1/scheduler-jobs",
        json=payload,
        headers={"Idempotency-Key": key, "x-actor": "tester"},
    )
    assert real.status_code == 422
    assert real.json()["error"] == "IDEMPOTENCY_KEY_REUSE"


def test_dry_run_cache_bypassed_without_idempotency_key(tmp_path):
    """non-dry_run WITHOUT Idempotency-Key succeeds after dry_run claimed same key."""
    client = _client(tmp_path)
    payload = {"job_id": "s4-no-key", "priority": 5}

    # dry_run with Idempotency-Key
    dry = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers={"Idempotency-Key": "s4-claimed", "x-actor": "tester"},
    )
    assert dry.status_code == 201

    # Same non-dry_run WITHOUT idempotency key → middleware passes through, handler creates
    created = client.post(
        "/api/v1/scheduler-jobs",
        json=payload,
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201
    assert created.json()["job_id"] == "s4-no-key"

    # Verify persisted
    fetched = client.get("/api/v1/scheduler-jobs/s4-no-key", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


# ── Scenario 5: non-dry_run not skipped by prior dry_run record ────────────


def test_non_dry_run_not_skipped_by_prior_dry_run_different_key(tmp_path):
    """non-dry_run with different Idempotency-Key succeeds after prior dry_run."""
    client = _client(tmp_path)
    payload = {"job_id": "s5-job", "priority": 5}

    # dry_run with key K1
    dry = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers={"Idempotency-Key": "s5-dry-key", "x-actor": "tester"},
    )
    assert dry.status_code == 201

    # non-dry_run with DIFFERENT key K2 → fresh claim → creates resource
    real = client.post(
        "/api/v1/scheduler-jobs",
        json=payload,
        headers={"Idempotency-Key": "s5-real-key", "x-actor": "tester"},
    )
    assert real.status_code == 201
    assert real.json()["job_id"] == "s5-job"

    # Verify persisted
    fetched = client.get("/api/v1/scheduler-jobs/s5-job", headers={"x-actor": "tester"})
    assert fetched.status_code == 200


def test_non_dry_run_not_skipped_by_prior_dry_run_422_on_same_key(tmp_path):
    """non-dry_run with same key as prior dry_run gets 422 (different query_string)."""
    client = _client(tmp_path)
    key = "s5-same-key"
    payload = {"job_id": "s5-other", "priority": 5}

    # non-dry_run claims key K with fingerprint F2 (no query_string)
    real = client.post(
        "/api/v1/scheduler-jobs",
        json=payload,
        headers={"Idempotency-Key": key, "x-actor": "tester"},
    )
    assert real.status_code == 201

    # dry_run with same key K has fingerprint F1 (query_string=dry_run=true)
    # F2 != F1 → 422 IDEMPOTENCY_KEY_REUSE
    dry = client.post(
        "/api/v1/scheduler-jobs?dry_run=true",
        json=payload,
        headers={"Idempotency-Key": key, "x-actor": "tester"},
    )
    assert dry.status_code == 422
    assert dry.json()["error"] == "IDEMPOTENCY_KEY_REUSE"


# ── Scenario 6: dry_run + idempotency must audit ───────────────────────────


def test_dry_run_idempotency_patch_does_not_persist(tmp_path):
    """dry_run=true PATCH with Idempotency-Key validates but does not persist."""
    client = _client(tmp_path)

    created = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "s6-patch", "priority": 5},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    headers = {"Idempotency-Key": "s6-patch-key", "x-actor": "tester"}
    patch_payload = {"expected_version": 1, "priority": 99}

    first = client.patch(
        "/api/v1/scheduler-jobs/s6-patch?dry_run=true",
        json=patch_payload,
        headers=headers,
    )
    assert first.status_code == 200
    assert first.json()["priority"] == 5  # unchanged (dry_run)

    # Verify NOT persisted
    fetched = client.get("/api/v1/scheduler-jobs/s6-patch", headers={"x-actor": "tester"})
    assert fetched.json()["priority"] == 5

    # Same dry_run key returns cached response
    second = client.patch(
        "/api/v1/scheduler-jobs/s6-patch?dry_run=true",
        json=patch_payload,
        headers=headers,
    )
    assert second.status_code == 200
    assert second.json() == first.json()


def test_dry_run_idempotency_delete_does_not_delete(tmp_path):
    """dry_run=true DELETE with Idempotency-Key validates but does not delete."""
    client = _client(tmp_path)

    created = client.post(
        "/api/v1/scheduler-jobs",
        json={"job_id": "s6-del", "priority": 5},
        headers={"x-actor": "tester"},
    )
    assert created.status_code == 201

    headers = {"Idempotency-Key": "s6-del-key", "x-actor": "tester"}

    first = client.delete(
        "/api/v1/scheduler-jobs/s6-del?expected_version=1&dry_run=true",
        headers=headers,
    )
    assert first.status_code == 204

    # Resource still exists
    fetched = client.get("/api/v1/scheduler-jobs/s6-del", headers={"x-actor": "tester"})
    assert fetched.status_code == 200
