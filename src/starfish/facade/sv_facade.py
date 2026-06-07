"""Starfish IEC 61850 Sampled Values 协议 facade —— environment-pending stub。

SV（Sampled Values，IEC 61850-9-2）是变电站过程层的二层多播采样值
发布协议，用于传输 CT/PT（电流/电压互感器）数字化采样数据。
SV 需 L2 veth 网络环境（raw socket / CAP_NET_RAW）和硬件 PTP
（IEEE 1588）时间同步，不可在 localhost 回环测试。

C runner 二进制 (iec61850_sv_publisher_simulator) 已编译就绪，
但 L2 veth 网络环境 + PTP 硬件时间同步缺失，mode 恒为 "environment-pending"。

NOT_IMPLEMENTED（所有模式）：
- write() / subscribe() / report() 明确抛出 UnsupportedOperation。
  待 L2 veth + PTP 时间同步环境就绪后补齐。

安全边界：
- 不得 import seahorse / whale.ingest / whale.shared.source。
- 所有数据标注 synthetic。
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starfish.models.plan import StarfishServerPlan, UnsupportedOperation


def probe_sv_binary() -> tuple[bool, str]:
    """探测 SV C runner 二进制及 L2/PTP 环境可用性。

    检查项：
        1. iec61850_sv_publisher_simulator 可执行文件是否存在。
        2. L2 veth 网络环境 + PTP IEEE 1588 时间同步是否就绪。

    SV 不可在 localhost 回环测试，始终因 L2/PTP 环境缺失返回 (False, reason)。

    Returns:
        (False, reason) —— binary 状态 + L2/PTP 环境缺失说明。
    """
    starfish_root = Path(__file__).resolve().parents[1]
    binary_path = starfish_root / "native" / "bin" / "iec61850_sv_publisher_simulator"

    binary_status: str
    if binary_path.exists() and os.access(binary_path, os.X_OK):
        binary_status = f"SV C runner 已编译: {binary_path}"
    else:
        binary_status = f"SV C runner 未编译 (预期路径: {binary_path})"

    return (
        False,
        f"{binary_status}。但 SV (Sampled Values) 需 L2 veth 网络环境"
        " + 硬件 PTP IEEE 1588 时间同步。状态：environment-pending",
    )


class SvFacade:
    """IEC 61850-9-2 Sampled Values 协议 server 模拟门面 —— environment-pending。

    SV 以 80 点/周期（50Hz 系统）或更高采样率通过二层多播帧发布
    数字化采样值，延迟要求 < 2ms，依赖 PTP 时间同步保证采样对齐。

    本 facade 以 in-memory 模式维护点位值，mode="environment-pending"，
    表示实现代码可能已就绪但运行环境不满足要求，不等同真实 SV 发布者。

    不负责：ASDU 采样值编解码、PTP 时间同步、采样率控制。
    """

    def __init__(self) -> None:
        self._plan: StarfishServerPlan | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "SV"

    @property
    def mode(self) -> str:
        """返回运行模式，恒为 "environment-pending"。

        L2 veth 网络环境 + PTP 时间同步未就绪，无法运行 SV 采样值发布器。
        """
        return "environment-pending"

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 SV facade（in-memory stub）。

        仅设置内存状态，不启动任何协议 server。
        重复调用安全（幂等）。
        """
        if self._started:
            return
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 SV facade。

        重置 in-memory 状态。不删除已加载的 plan 和 values。
        重复调用安全（幂等）。
        """
        if not self._started:
            return
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态。

        始终报告 mode="environment-pending"，不进行任何网络探测。

        Returns:
            包含 health 信息的 dict。
        """
        return {
            "status": "started" if self._started else "stopped",
            "plan_loaded": self._plan is not None,
            "point_count": len(self._plan.points) if self._plan else 0,
            "endpoint_count": len(self._plan.endpoints) if self._plan else 0,
            "capabilities": list(self._plan.capabilities) if self._plan else [],
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "synthetic": self._plan.synthetic if self._plan else True,
            "protocol": self.protocol,
            "mode": self.mode,
            "running": False,
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerPlan) -> None:
        """加载点位定义和初始值到内存存储。

        Args:
            plan: 已校验的 StarfishServerPlan 实例。
        """
        self._plan = plan
        self._values = dict(plan.initial_values)

    def read(self, point_ids: list[str] | None = None) -> dict[str, Any]:
        """从内存读取当前点位值。

        Args:
            point_ids: 要读取的点位 ID 列表，None 表示全部。

        Returns:
            point_id -> 当前值 的 dict。不存在的点位置为 None。
        """
        if point_ids is None:
            return dict(self._values)
        return {pid: self._values.get(pid) for pid in point_ids}

    def update_values(self, values: dict[str, Any]) -> None:
        """批量更新内存中的点位值。

        Args:
            values: point_id -> 新值 的 dict。
        """
        self._values.update(values)

    def capabilities(self) -> list[str]:
        """返回当前已加载 plan 的能力声明列表。

        Returns:
            能力声明字符串列表，未加载时返回空列表。
        """
        if self._plan is None:
            return []
        return list(self._plan.capabilities)

    # ── NOT_IMPLEMENTED ───────────────────────────────────────────────────────

    def write(self, point_id: str, value: Any) -> None:
        """写入单个点位值 —— 当前未实现。

        SV 协议本身不支持单播写入（仅多播发布采样值）。

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "SvFacade.write 尚未实现，SV 协议仅支持多播发布采样值",
        )

    def subscribe(self, point_ids: list[str]) -> None:
        """订阅点位数据变更通知 —— 当前未实现。

        Args:
            point_ids: 要订阅的点位 ID 列表。

        Raises:
            UnsupportedOperation: 订阅操作尚未实现。
        """
        raise UnsupportedOperation(
            "subscribe",
            "SvFacade.subscribe 尚未实现，"
            "待 L2 veth + PTP 时间同步环境就绪后实现",
        )

    def report(self) -> dict[str, Any]:
        """上报门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "SvFacade.report 尚未实现，"
            "待 L2 veth + PTP 时间同步环境就绪后实现",
        )


__all__ = ["SvFacade", "probe_sv_binary"]
