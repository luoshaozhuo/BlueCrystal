"""验证 FastAPI OTel 安装与卸载的成对生命周期。"""

from __future__ import annotations

from types import SimpleNamespace

from fastapi import FastAPI
import pytest

from observability.instrumentation import fastapi as fastapi_module


def test_uninstall_reverses_installed_otel_instrumentation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """成功安装 OTel 后，adapter 卸载时必须调用对应的 uninstrument。"""
    calls: list[str] = []

    class FakeOTelFastAPIInstrumentor:
        """记录第三方 instrumentation 生命周期调用的最小替身。"""

        @staticmethod
        def instrument_app(app: FastAPI, **_: object) -> None:
            """记录安装调用。"""
            calls.append("instrument")

        @staticmethod
        def uninstrument_app(app: FastAPI) -> None:
            """记录卸载调用。"""
            calls.append("uninstrument")

    monkeypatch.setattr(
        fastapi_module,
        "OTelFastAPIInstrumentor",
        FakeOTelFastAPIInstrumentor,
    )
    adapter = fastapi_module.FastAPIInstrumentation(FastAPI())
    runtime = SimpleNamespace(
        metrics=None,
        tracing=SimpleNamespace(tracer_provider=object()),
    )

    adapter.install(runtime)
    adapter.uninstall()

    assert calls == ["instrument", "uninstrument"]
