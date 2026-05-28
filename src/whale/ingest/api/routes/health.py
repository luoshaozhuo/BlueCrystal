"""Health and readiness routes."""

from __future__ import annotations

from fastapi import APIRouter, Request

from whale.ingest.api.audit_middleware import build_audit_event

router = APIRouter()


@router.get("/healthz")
def healthz(request: Request) -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
def readyz(request: Request) -> dict[str, str]:
    request.app.state.readiness_probe()
    audit_sink = request.app.state.audit_sink
    if audit_sink is not None:
        audit_sink.emit(
            build_audit_event(
                request,
                action="readyz.read",
                resource_type="health",
                resource_id="readyz",
                decision="ALLOW",
                result="SUCCESS",
                http_status=200,
            )
        )
    return {"status": "ready"}
