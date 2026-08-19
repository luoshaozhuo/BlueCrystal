"""FastAPI：HTTP Log + HTTP Metrics + HTTP Trace。"""
from __future__ import annotations
from time import perf_counter
import structlog
from fastapi import FastAPI, Request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from ..shared import bind_observation_context, new_request_id
from ..trace import TracePolicy
logger=structlog.get_logger(__name__)
def install_http_observability(app:FastAPI,*,trace_policy:TracePolicy,excluded_trace_urls:str="health,metrics",expose_metrics:bool=True)->None:
    @app.middleware("http")
    async def observation_context_middleware(request:Request,call_next):
        started=perf_counter(); request_id=request.headers.get("x-request-id",new_request_id())
        with bind_observation_context(request_id=request_id,task_id=None,connection_id=None,actor=None,source="http",operation=None,target_type=None,target_id=None):
            logger.info("http_request_started",method=request.method,path=request.url.path)
            try: response=await call_next(request)
            except Exception:
                logger.exception("http_request_failed",method=request.method,path=request.url.path,duration_seconds=perf_counter()-started); raise
            logger.info("http_request_finished",method=request.method,path=request.url.path,status_code=response.status_code,duration_seconds=perf_counter()-started)
            response.headers["x-request-id"]=request_id; return response
    instrumentator=Instrumentator().instrument(app)
    if expose_metrics: instrumentator.expose(app,endpoint="/metrics",include_in_schema=False)
    if trace_policy.enabled and trace_policy.trace_http:
        FastAPIInstrumentor.instrument_app(app,excluded_urls=excluded_trace_urls)
