"""Single-configuration subscribe profile service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from tools.source_lab.access.providers.base import SourceProvider
from tools.source_lab.access.runners.base import SubscriptionRunner
from tools.source_lab.access.subscribe.model import SubscribeScanConfig, SubscribeScanResult
from tools.source_lab.access.subscribe.scan import scan_source_subscriptions


class _ProfilerLike(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def output_text(self, *, unicode: bool, color: bool, show_all: bool) -> str: ...


@dataclass(frozen=True, slots=True)
class SubscribeProfileResult:
    """Single subscribe profile run plus optional profiler output."""

    result: SubscribeScanResult
    pyinstrument_text: str | None


def _new_profiler() -> _ProfilerLike | None:
    try:
        from pyinstrument import Profiler  # type: ignore[import-not-found, import-untyped]
    except ImportError:
        return None
    return cast(_ProfilerLike, Profiler(async_mode="enabled"))


def run_subscribe_profile(
    config: SubscribeScanConfig,
    *,
    provider: SourceProvider,
    runner: SubscriptionRunner,
    pyinstrument: bool = False,
    show_all: bool = False,
    max_lines: int = 80,
) -> SubscribeProfileResult:
    """Run one subscribe profile configuration."""

    profiler = _new_profiler() if pyinstrument else None
    if profiler is not None:
        profiler.start()
        try:
            result = scan_source_subscriptions(config, provider=provider, runner=runner)
        finally:
            profiler.stop()
    else:
        result = scan_source_subscriptions(config, provider=provider, runner=runner)

    profiler_text: str | None = None
    if profiler is not None:
        lines = profiler.output_text(unicode=True, color=True, show_all=show_all).splitlines()
        if max_lines > 0 and len(lines) > max_lines:
            lines = lines[:max_lines]
        profiler_text = "\n".join(lines)
    return SubscribeProfileResult(result=result, pyinstrument_text=profiler_text)
