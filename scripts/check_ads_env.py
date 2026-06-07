#!/usr/bin/env python3
"""
Beckhoff ADS 环境预检脚本。

检查 OS、.NET/TwinCAT/ADS Router、port 48898、AdsLib binary，
输出 environment-pending 明细。

本脚本只读检查，不得修改系统状态，不得要求 root 权限。
需要 Windows+TwinCAT+ADS Router 时为 environment-pending。
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """单条检查结果。"""
    component: str
    status: str
    detail: str
    suggestion: str = ""


@dataclass
class EnvReport:
    """环境预检报告。"""
    results: list[CheckResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    pending: int = 0
    skipped: int = 0

    def add(self, result: CheckResult) -> None:
        self.results.append(result)
        if result.status == "passed":
            self.passed += 1
        elif result.status == "failed":
            self.failed += 1
        elif result.status == "pending":
            self.pending += 1
        elif result.status == "skipped":
            self.skipped += 1

    def summary(self) -> str:
        total = self.passed + self.failed + self.pending + self.skipped
        lines = [
            f"总检查项: {total}, passed: {self.passed}, failed: {self.failed}, "
            f"pending: {self.pending}, skipped: {self.skipped}",
        ]
        for r in self.results:
            lines.append(f"  [{r.status}] {r.component}: {r.detail}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.passed + self.failed + self.pending + self.skipped,
            "passed": self.passed,
            "failed": self.failed,
            "pending": self.pending,
            "skipped": self.skipped,
            "results": [
                {
                    "component": r.component,
                    "status": r.status,
                    "detail": r.detail,
                    "suggestion": r.suggestion,
                }
                for r in self.results
            ],
        }


def _check_os(env_report: EnvReport) -> None:
    """检查操作系统。"""
    system = platform.system()
    if system == "Windows":
        env_report.add(
            CheckResult(
                component="操作系统",
                status="passed",
                detail=f"Windows ({platform.release()}) -- TwinCAT/ADS Router 仅 Windows 原生支持",
            )
        )
    elif system == "Linux":
        env_report.add(
            CheckResult(
                component="操作系统",
                status="pending",
                detail=f"Linux ({platform.release()}) -- TwinCAT/ADS Router 仅 Windows 原生支持",
                suggestion="需要 Windows+TwinCAT 或通过 AdsLib cross-compile 在 Linux 运行",
            )
        )
    else:
        env_report.add(
            CheckResult(
                component="操作系统",
                status="pending",
                detail=f"{system} ({platform.release()}) -- 非预期平台",
            )
        )


def _check_dotnet(env_report: EnvReport) -> None:
    """检查 .NET runtime。"""
    dotnet_path = shutil.which("dotnet")
    if dotnet_path:
        try:
            result = subprocess.run(
                ["dotnet", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                env_report.add(
                    CheckResult(
                        component=".NET Runtime",
                        status="passed",
                        detail=f"已安装: {result.stdout.strip()} (path: {dotnet_path})",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component=".NET Runtime",
                        status="pending",
                        detail=f"dotnet 命令存在但返回非零: {result.stderr.strip()}",
                    )
                )
        except subprocess.TimeoutExpired:
            env_report.add(
                CheckResult(
                    component=".NET Runtime",
                    status="pending",
                    detail="dotnet --version 超时",
                )
            )
    else:
        env_report.add(
            CheckResult(
                component=".NET Runtime",
                status="pending",
                detail="dotnet 未安装或不在 PATH 中",
                suggestion="安装 .NET SDK/Runtime (https://dotnet.microsoft.com/)",
            )
        )


def _check_twincat_ads_router(env_report: EnvReport) -> None:
    """检查 TwinCAT ADS Router 端口。"""
    # ADS Router 默认端口
    ads_ports = [48898, 8016]

    if platform.system() == "Windows":
        # 在 Windows 上尝试检查 TwinCAT 服务
        try:
            result = subprocess.run(
                ["sc", "query", "TcSysSrv"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if "RUNNING" in result.stdout:
                env_report.add(
                    CheckResult(
                        component="TwinCAT ADS Router (TcSysSrv)",
                        status="passed",
                        detail="服务正在运行",
                    )
                )
            elif "STOPPED" in result.stdout:
                env_report.add(
                    CheckResult(
                        component="TwinCAT ADS Router (TcSysSrv)",
                        status="pending",
                        detail="服务已安装但已停止",
                        suggestion="启动 TcSysSrv 服务",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component="TwinCAT ADS Router (TcSysSrv)",
                        status="pending",
                        detail=f"服务状态不明确: {result.stdout[:200]}",
                    )
                )
        except Exception as e:
            env_report.add(
                CheckResult(
                    component="TwinCAT ADS Router",
                    status="pending",
                    detail=f"检查失败: {e}",
                )
            )
    else:
        env_report.add(
            CheckResult(
                component="TwinCAT ADS Router",
                status="pending",
                detail="非 Windows 平台，TwinCAT ADS Router 不可用",
                suggestion="需要 Windows+TwinCAT 3 Runtime 环境",
            )
        )

    # 端口检查
    for port in ads_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("127.0.0.1", port))
            sock.close()
            if result == 0:
                env_report.add(
                    CheckResult(
                        component=f"ADS 端口 {port}",
                        status="passed",
                        detail=f"127.0.0.1:{port} 可达",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component=f"ADS 端口 {port}",
                        status="pending",
                        detail=f"127.0.0.1:{port} 不可达",
                        suggestion="确认 TwinCAT ADS Router 正在运行",
                    )
                )
        except OSError as e:
            env_report.add(
                CheckResult(
                    component=f"ADS 端口 {port}",
                    status="pending",
                    detail=f"检查 {port} 失败: {e}",
                )
            )


def _check_pyads(env_report: EnvReport) -> None:
    """检查 pyads Python 库。"""
    try:
        from importlib import util as importlib_util
        spec = importlib_util.find_spec("pyads")
        if spec is not None:
            env_report.add(
                CheckResult(
                    component="pyads (Python ADS client)",
                    status="passed",
                    detail=f"已安装 (path: {spec.origin})",
                )
            )
        else:
            env_report.add(
                CheckResult(
                    component="pyads (Python ADS client)",
                    status="pending",
                    detail="pyads 未安装",
                    suggestion="pip install pyads",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="pyads (Python ADS client)",
                status="pending",
                detail=f"检查失败: {e}",
            )
        )


def _check_adslib_binary(env_report: EnvReport) -> None:
    """检查 AdsLib binary (native C runner)。"""
    possible_paths = [
        "src/starfish/native/bin/beckhoff_ads_polling_runner",
        "src/starfish/native/bin/Release/beckhoff_ads_polling_runner.exe",
    ]

    # 以 Whale 项目根目录为基准
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = False
    for rel_path in possible_paths:
        abs_path = os.path.join(repo_root, rel_path)
        if os.path.isfile(abs_path) and os.access(abs_path, os.X_OK):
            env_report.add(
                CheckResult(
                    component=f"AdsLib binary ({rel_path})",
                    status="passed",
                    detail=f"存在且可执行: {abs_path}",
                )
            )
            found = True

    if not found:
        env_report.add(
            CheckResult(
                component="AdsLib binary",
                status="pending",
                detail="未找到编译后的 AdsLib binary (beckhoff_ads_polling_runner)",
                suggestion=(
                    "在 Windows 上编译: cd src/starfish/native && "
                    "mkdir bin && cd bin && cmake .. && cmake --build . --target beckhoff_ads_polling_runner"
                ),
            )
        )


def main() -> None:
    """Beckhoff ADS 环境预检入口。"""
    parser = argparse.ArgumentParser(
        description="Beckhoff ADS 环境预检 -- 只读检查，不修改系统",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="dry-run 模式（默认开启），只检查不操作",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="输出 JSON 格式报告",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="",
        help="输出 JSON 报告到文件",
    )
    args = parser.parse_args()

    env_report = EnvReport()

    _check_os(env_report)
    _check_dotnet(env_report)
    _check_twincat_ads_router(env_report)
    _check_pyads(env_report)
    _check_adslib_binary(env_report)

    # 综合状态
    env_report.add(
        CheckResult(
            component="Beckhoff ADS 综合状态",
            status="pending",
            detail=(
                "environment-pending -- "
                "7 tests skipped，需 Windows+TwinCAT+ADS Router 或 AdsLib binary"
            ),
        )
    )

    if args.json:
        print(json.dumps(env_report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("Beckhoff ADS 环境预检报告")
        print("=" * 60)
        print(env_report.summary())
        print("=" * 60)
        print("Beckhoff ADS status: environment-pending")
        print("需要 Windows+TwinCAT+ADS Router 或 AdsLib binary 方可解除 environment-pending。")
        print("=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(env_report.to_dict(), f, ensure_ascii=False, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
