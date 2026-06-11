"""Starfish Beckhoff ADS 协议 facade —— codebase-pending stub。

Beckhoff ADS 是 Beckhoff TwinCAT runtime 的自动化设备规范通信协议。
当前无可用 C/Python 原生实现，依赖 .NET runtime 和 TwinCAT ADS 库。
本模块以 in-memory stub 模式提供基础点位管理能力，mode 恒为 "codebase-pending"。

探针增强说明（Round 13）：
    probe_ads_binary() 现在会检查 native/bin/ 下 ADS binary、
    探测 .NET runtime 可用性、检查 TwinCAT 相关环境变量。
    但无 Python 原生 ADS 实现，始终返回 (False, reason)。

NOT_IMPLEMENTED（所有模式）：
    - write() / subscribe() / report() 明确抛出 UnsupportedOperation。
      待 .NET runtime 环境或 Python 原生实现就绪后补齐。

安全边界：
    - 不得 import seahorse / whale.ingest / whale.shared.source。
    - 所有数据标注 synthetic。
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from starfish.domain import StarfishServerMemberConfig, UnsupportedOperation


def probe_ads_binary() -> tuple[bool, str]:
    """探测 Beckhoff ADS 二进制或 runtime 可用性。

    探测步骤（增强）：
        1. 检查 src/starfish/native/bin/ 下是否有 ADS 相关 binary。
        2. 探测 .NET runtime（dotnet CLI）可用性。
        3. 检查 TwinCAT 相关环境变量。

    始终返回 (False, reason)，因为无 Python 原生 ADS 实现。

    Returns:
        (False, reason) —— 无可用 ADS 实现。
    """
    reasons: list[str] = []

    # 1. 检查 native/bin/ 下 ADS binary
    starfish_root = Path(__file__).resolve().parents[1]
    native_bin = starfish_root / "native" / "bin"
    ads_files: list[str] = []
    if native_bin.exists():
        for fname in native_bin.iterdir():
            if fname.is_file() and "ads" in fname.name.lower():
                ads_files.append(fname.name)
    if ads_files:
        reasons.append(f"发现 ADS 相关文件: {ads_files}")
    else:
        reasons.append("native/bin/ 下无 ADS 相关 binary")

    # 2. 探测 .NET runtime
    dotnet_path = shutil.which("dotnet")
    if dotnet_path:
        reasons.append(
            f".NET runtime 可用: {dotnet_path}"
            "（可运行 TwinCAT ADS .NET 库，"
            "但当前无 Python 原生 ADS 实现）"
        )
    else:
        reasons.append(".NET runtime (dotnet) 不可用")

    # 3. 检查 TwinCAT 环境变量
    twincat_env_vars: list[str] = []
    for env_name in ("TWINCAT_DIR", "TWINCAT3_DIR", "TC_REGISTRY", "ADS_AMS_NET_ID"):
        if os.environ.get(env_name):
            twincat_env_vars.append(f"{env_name}={os.environ[env_name]}")
    if twincat_env_vars:
        reasons.append(f"TwinCAT 环境变量已设置: {twincat_env_vars}")
    else:
        reasons.append("无 TwinCAT 相关环境变量设置")

    full_reason = (
        "Beckhoff ADS 需 .NET/TwinCAT runtime，"
        "当前无可用原生 Python ADS 实现。"
        "检测结果: " + "; ".join(reasons)
        + "。状态：codebase-pending"
    )
    return (False, full_reason)


class AdsFacade:
    """Beckhoff ADS 协议 server 模拟门面 —— codebase-pending stub。

    ADS（Automation Device Specification）是 Beckhoff 自动化控制器通信协议，
    通常运行在 TwinCAT runtime 环境中，需 .NET framework 支持。

    本 facade 以 in-memory 模式维护点位值，mode="codebase-pending"，
    表示协议实现处于待开发状态，不等同真实 ADS server。

    不负责：TwinCAT runtime 管理、AMS NetId 配置、ADS 路由。
    """

    def __init__(self) -> None:
        self._plan: StarfishServerMemberConfig | None = None
        self._started: bool = False
        self._values: dict[str, Any] = {}
        self._started_at: datetime | None = None

    # ── 属性 ──────────────────────────────────────────────────────────────────

    @property
    def protocol(self) -> str:
        """返回归一化协议名。"""
        return "BECKHOFF_ADS"

    @property
    def mode(self) -> str:
        """返回运行模式，恒为 "codebase-pending"。

        .NET/TwinCAT runtime 依赖未就绪，无 Python 原生实现。
        """
        return "codebase-pending"

    # ── 生命周期 ──────────────────────────────────────────────────────────────

    def start(self) -> None:
        """启动 ADS facade（in-memory stub）。

        仅设置内存状态，不启动任何协议 server。
        重复调用安全（幂等）。
        """
        if self._started:
            return
        self._started = True
        self._started_at = datetime.now(timezone.utc)

    def stop(self) -> None:
        """停止 ADS facade。

        重置 in-memory 状态。不删除已加载的 plan 和 values。
        重复调用安全（幂等）。
        """
        if not self._started:
            return
        self._started = False

    # ── 可观测性 ──────────────────────────────────────────────────────────────

    def health(self) -> dict[str, Any]:
        """返回当前 facade 的可观测健康状态（含 ADS 特定诊断信息）。

        包含 .NET runtime 可用性和环境变量诊断信息。

        Returns:
            包含 health 信息的 dict。
        """
        # ADS 特定诊断
        diagnosis: dict[str, Any] = {}

        dotnet_path = shutil.which("dotnet")
        diagnosis["dotnet_available"] = dotnet_path is not None
        if dotnet_path:
            diagnosis["dotnet_path"] = dotnet_path

        twincat_env_vars: dict[str, str] = {}
        for env_name in (
            "TWINCAT_DIR", "TWINCAT3_DIR", "TC_REGISTRY", "ADS_AMS_NET_ID",
        ):
            val = os.environ.get(env_name)
            if val:
                twincat_env_vars[env_name] = val
        diagnosis["twincat_env_vars"] = twincat_env_vars

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
            "diagnosis": diagnosis,
            "reason": (
                "Beckhoff ADS 需 .NET/TwinCAT runtime，"
                "当前无 Python 原生 ADS 实现。"
                "需 AMS NetId 配置、ADS 路由、TwinCAT ADS 库"
            ),
        }

    # ── 数据操作 ──────────────────────────────────────────────────────────────

    def load_points(self, plan: StarfishServerMemberConfig) -> None:
        """加载点位定义和初始值到内存存储。

        Args:
            plan: 已校验的 StarfishServerMemberConfig 实例。
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

        Args:
            point_id: 目标点位 ID。
            value: 要写入的值。

        Raises:
            UnsupportedOperation: 写入操作尚未实现。
        """
        raise UnsupportedOperation(
            "write",
            "AdsFacade.write 尚未实现，"
            "待 Beckhoff ADS Python 原生实现就绪后实现",
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
            "AdsFacade.subscribe 尚未实现，"
            "待 Beckhoff ADS Python 原生实现就绪后实现",
        )

    def report(self) -> dict[str, Any]:
        """上报门面状态摘要 —— 当前未实现。

        Raises:
            UnsupportedOperation: report 操作尚未实现。
        """
        raise UnsupportedOperation(
            "report",
            "AdsFacade.report 尚未实现，"
            "待 Beckhoff ADS Python 原生实现就绪后实现",
        )


__all__ = ["AdsFacade", "probe_ads_binary"]
