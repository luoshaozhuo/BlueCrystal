"""保留应用装配入口；当前骨架不定义依赖或启动流程."""

from __future__ import annotations

import asyncio
from enum import StrEnum
import signal

class RuntimeMode(StrEnum):
    STANDALONE = "standalone"
    ACTIVE_STANDBY = "active_standby"
    DUAL_ACTIVE_PARTITIONED = "dual_active"
    CLUSTER = "cluster"

class StandaloneApplication:
    """独立应用装配入口."""

    def __init__(self) -> None:
        """初始化."""
        self._stop_event = asyncio.Event()

    async def _start_components(self) -> None:
        """启动组件"""
        print("StandaloneApplication started")

    async def _stop_components(self) -> None:
        """关闭组件"""
        print("StandaloneApplication stopped")

    def stop(self) -> None:
        """停止应用."""
        self._stop_event.set()
        print("Stop event received, shutting down...")

    async def run(self, **kwargs) -> None:
        """运行."""
        self._stop_event.clear()
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.stop)

        try:
            await self._start_components()
            await self._stop_event.wait()
        finally:
            await self._stop_components()

def app_factory(mode: RuntimeMode):
    """应用工厂函数."""
    if mode == RuntimeMode.STANDALONE:
        return StandaloneApplication()
    else:
        raise ValueError(f"Unknown application type: {mode}")

if __name__ == "__main__":
    asyncio.run(app_factory(RuntimeMode.STANDALONE).run())