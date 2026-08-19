"""FastAPI 声明式 Audit 事实产生适配."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.routing import APIRoute

from observability_reference.instrumentation import InstrumentationHooks, safe_observe
from observability_reference.shared import bind_operation_context

from .decorators import get_audit_spec
from .models import AuditSpec


def install_fastapi_audit(
    app: FastAPI,
    hooks: InstrumentationHooks,
) -> None:
    """安装声明式 Audit Route Adapter.

    actor/source 已由统一 HTTP Observability Middleware 注入 Context。
    本适配器只负责：
    1. 读取 AuditSpec；
    2. 绑定 operation/target；
    3. 根据最终结果产生 audit_operation_* Hook。
    """

    app.router.route_class = _create_audited_route_class(hooks)


def _create_audited_route_class(
    hooks: InstrumentationHooks,
) -> type[APIRoute]:
    class AuditedAPIRoute(APIRoute):
        def get_route_handler(self):
            original_handler = super().get_route_handler()
            spec = get_audit_spec(self.endpoint)

            if spec is None:
                return original_handler

            async def audited_handler(request: Request) -> Response:
                target_id = _resolve_target_id(request, spec)

                with bind_operation_context(
                    operation=spec.operation,
                    target_type=spec.target_type,
                    target_id=target_id,
                ):
                    try:
                        response = await original_handler(request)
                    except BaseException as exc:
                        safe_observe(
                            hooks.audit_operation_failed,
                            exception=exc,
                        )
                        raise

                    if response.status_code >= 400:
                        safe_observe(
                            hooks.audit_operation_failed,
                            status_code=response.status_code,
                        )
                    else:
                        safe_observe(
                            hooks.audit_operation_succeeded,
                            status_code=response.status_code,
                        )

                    return response

            return audited_handler

    AuditedAPIRoute.__name__ = "AuditedAPIRoute"
    return AuditedAPIRoute


def _resolve_target_id(
    request: Request,
    spec: AuditSpec,
) -> str | None:
    if spec.target_arg is None:
        return None

    value: Any = request.path_params.get(spec.target_arg)

    if value is None:
        value = request.query_params.get(spec.target_arg)

    return None if value is None else str(value)
