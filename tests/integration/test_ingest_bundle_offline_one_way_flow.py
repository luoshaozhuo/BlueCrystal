"""Offline one-way bundle flow tests."""

from __future__ import annotations

from sqlalchemy import select

from whale.ingest.adapters.audit.db_audit_sink import DbIngestAuditSink
from whale.ingest.bundle.service import BundleService
from whale.ingest.framework.persistence import create_runtime_engine, create_runtime_session_factory, initialize_runtime_database
from whale.shared.persistence.orm import AcquisitionTask, IngestAuditEventOrm


def _service(tmp_path, name: str):
    engine = create_runtime_engine(f"sqlite:///{tmp_path / f'{name}.sqlite'}")
    initialize_runtime_database(engine)
    session_factory = create_runtime_session_factory(engine)
    return session_factory, BundleService(session_factory, audit_sink=DbIngestAuditSink(session_factory), node_id=name)


def test_offline_raw_bundle_export_import_roundtrip(tmp_path) -> None:
    manager_sf, manager = _service(tmp_path, "manager")
    target_sf, target = _service(tmp_path, "target")

    session = manager_sf()
    try:
        session.add(AcquisitionTask(task_name="task-1", ld_instance_id=1, acquisition_mode="POLLING", task_status="STOPPED"))
        session.commit()
    finally:
        session.close()

    bundle = manager.export_bundle(source="manager", actor="ops", redacted=False, bundle_version="bundle-1")
    result = target.import_bundle(bundle, actor="ops", dry_run=False)

    assert result.imported_count == 1
    session = target_sf()
    try:
        imported = session.execute(select(AcquisitionTask).where(AcquisitionTask.task_name == "task-1")).scalar_one()
    finally:
        session.close()
    assert imported.task_name == "task-1"


def test_redacted_bundle_cannot_be_imported_as_accepted_config(tmp_path) -> None:
    manager_sf, manager = _service(tmp_path, "manager")
    _, target = _service(tmp_path, "target")
    session = manager_sf()
    try:
        session.add(AcquisitionTask(task_name="task-1", ld_instance_id=1, acquisition_mode="POLLING", task_status="STOPPED"))
        session.commit()
    finally:
        session.close()

    redacted = manager.export_bundle(source="manager", actor="ops", redacted=True, bundle_version="bundle-2")
    try:
        target.import_bundle(redacted, actor="ops", dry_run=False)
    except ValueError as exc:
        assert "Redacted bundle" in str(exc)
    else:
        raise AssertionError("redacted bundle should not import")


def test_corrupt_checksum_import_rolls_back(tmp_path) -> None:
    manager_sf, manager = _service(tmp_path, "manager")
    target_sf, target = _service(tmp_path, "target")
    session = manager_sf()
    try:
        session.add(AcquisitionTask(task_name="task-1", ld_instance_id=1, acquisition_mode="POLLING", task_status="STOPPED"))
        session.commit()
    finally:
        session.close()

    bundle = manager.export_bundle(source="manager", actor="ops", redacted=False, bundle_version="bundle-3")
    corrupt = bundle.model_copy(update={"checksum": "bad"})
    try:
        target.import_bundle(corrupt, actor="ops", dry_run=False)
    except ValueError:
        pass
    else:
        raise AssertionError("checksum mismatch should fail")

    session = target_sf()
    try:
        assert session.execute(select(AcquisitionTask).where(AcquisitionTask.task_name == "task-1")).scalar_one_or_none() is None
    finally:
        session.close()


def test_bundle_import_success_and_failure_are_audited(tmp_path) -> None:
    manager_sf, manager = _service(tmp_path, "manager")
    target_sf, target = _service(tmp_path, "target")
    session = manager_sf()
    try:
        session.add(AcquisitionTask(task_name="task-1", ld_instance_id=1, acquisition_mode="POLLING", task_status="STOPPED"))
        session.commit()
    finally:
        session.close()

    ok_bundle = manager.export_bundle(source="manager", actor="ops", redacted=False, bundle_version="bundle-4")
    target.import_bundle(ok_bundle, actor="ops", dry_run=False)

    bad_bundle = ok_bundle.model_copy(update={"checksum": "bad"})
    try:
        target.import_bundle(bad_bundle, actor="ops", dry_run=False)
    except ValueError:
        pass

    session = target_sf()
    try:
        results = [row.result for row in session.scalars(select(IngestAuditEventOrm).order_by(IngestAuditEventOrm.audit_id))]
    finally:
        session.close()
    assert "SUCCESS" in results
    assert "FAILED" in results
