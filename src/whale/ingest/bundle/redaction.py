"""Bundle redaction helpers."""

from __future__ import annotations

from whale.ingest.bundle.model import AcquisitionTaskBundleItem, IngestBundle
from whale.ingest.domain.audit_event import redact_value


def redact_bundle(bundle: IngestBundle) -> IngestBundle:
    """Return one redacted copy of a bundle."""

    tasks = [
        AcquisitionTaskBundleItem(
            **{
                **item.model_dump(),
                "protocol_params": redact_value(item.protocol_params),
            }
        )
        for item in bundle.acquisition_tasks
    ]
    return IngestBundle(
        **{
            **bundle.model_dump(),
            "redacted": True,
            "acquisition_tasks": tasks,
        }
    )
