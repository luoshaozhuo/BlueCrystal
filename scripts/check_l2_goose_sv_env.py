#!/usr/bin/env python3
"""
GOOSE/SV L2 网络环境预检脚本。

检查 CAP_NET_RAW 权限、网卡、veth/netns、tcpdump 权限、VLAN 能力，
输出 GOOSE/SV L2 环境状态。

本脚本只读检查，不得修改系统状态，不得要求 root 执行。
需要 root/CAP_NET_RAW 时只报告，不要求实际具有。
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
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


def _has_cap_net_raw() -> bool:
    """检查当前进程是否有 CAP_NET_RAW capability（Linux）。"""
    if sys.platform != "linux":
        return False

    # 尝试通过 /proc/self/status 检查
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("CapEff:"):
                    cap_eff = int(line.split(":")[1].strip(), 16)
                    # CAP_NET_RAW = 13 (bit 13)
                    return (cap_eff & (1 << 13)) != 0
    except (OSError, ValueError, IndexError):
        pass

    # fallback: 尝试通过 ctypes 调用 capget
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        # _LINUX_CAPABILITY_VERSION_3 = 0x20080522
        class cap_user_header(ctypes.Structure):
            _fields_ = [
                ("version", ctypes.c_uint32),
                ("pid", ctypes.c_int),
            ]

        class cap_user_data(ctypes.Structure):
            _fields_ = [
                ("effective", ctypes.c_uint32),
                ("permitted", ctypes.c_uint32),
                ("inheritable", ctypes.c_uint32),
            ]

        header = cap_user_header(version=0x20080522, pid=0)
        data = cap_user_data()
        ret = libc.capget(ctypes.byref(header), ctypes.byref(data))
        if ret == 0:
            return (data.effective & (1 << 13)) != 0
    except Exception:
        pass

    return False


def _check_cap_net_raw(env_report: EnvReport) -> None:
    """检查 CAP_NET_RAW 权限。"""
    if sys.platform != "linux":
        env_report.add(
            CheckResult(
                component="CAP_NET_RAW",
                status="pending",
                detail=f"非 Linux 平台 ({sys.platform})，CAP_NET_RAW 不适用",
            )
        )
        return

    has_cap = _has_cap_net_raw()
    if has_cap:
        env_report.add(
            CheckResult(
                component="CAP_NET_RAW",
                status="passed",
                detail="当前进程具有 CAP_NET_RAW capability",
            )
        )
    else:
        env_report.add(
            CheckResult(
                component="CAP_NET_RAW",
                status="pending",
                detail="当前进程不具有 CAP_NET_RAW -- raw socket 将无法创建",
                suggestion=(
                    "GOOSE/SV L2 验证需要 CAP_NET_RAW。授予方式:\n"
                    "  1. sudo setcap cap_net_raw+ep $(which python3)  (推荐)\n"
                    "  2. 在受控 veth/netns 环境中使用 root 用户\n"
                    "  3. 使用 unshare -Urn 创建网络命名空间"
                ),
            )
        )


def _check_network_interfaces(env_report: EnvReport) -> None:
    """检查可用网卡。"""
    try:
        import socket as sock_mod
        import fcntl
        import struct

        # 获取所有接口
        try:
            SIOCGIFCONF = 0x8912

            sock = sock_mod.socket(sock_mod.AF_INET, sock_mod.SOCK_DGRAM)
            try:
                # 获取接口列表
                ifconf = struct.pack("i", 4096)
                try:
                    result = fcntl.ioctl(sock.fileno(), SIOCGIFCONF, ifconf)
                except OSError:
                    result = None

                if result:
                    ifaces = []
                    data = result[16:]  # skip length field
                    for i in range(0, len(data), 40):
                        name = data[i : i + 16].split(b"\0")[0].decode("utf-8", errors="replace")
                        if name and name != "lo":
                            ifaces.append(name)

                    if ifaces:
                        env_report.add(
                            CheckResult(
                                component="网卡",
                                status="passed",
                                detail=f"可用网卡: {', '.join(ifaces[:10])}",
                            )
                        )

                        # 检查和报告 VLAN 能力提示
                        env_report.add(
                            CheckResult(
                                component="VLAN 能力",
                                status="pending",
                                detail=(
                                    "GOOSE 通常 VLAN 0/1，SV 独立 VLAN 2-3。"
                                    "需要支持 VLAN 的网卡或 veth/netns 环境。"
                                    "宿主机 eth0 通常不可作为 L2 raw socket 验证环境。"
                                ),
                            )
                        )
                    else:
                        env_report.add(
                            CheckResult(
                                component="网卡",
                                status="pending",
                                detail="未发现非 lo 网卡",
                            )
                        )
                else:
                    env_report.add(
                        CheckResult(
                            component="网卡",
                            status="pending",
                            detail="无法获取网卡列表 (ioctl 失败)",
                        )
                    )
            finally:
                sock.close()
        except (OSError, ImportError) as e:
            env_report.add(
                CheckResult(
                    component="网卡",
                    status="pending",
                    detail=f"检查失败: {e}",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="网卡",
                status="pending",
                detail=f"检查失败: {e}",
            )
        )


def _check_veth_netns(env_report: EnvReport) -> None:
    """检查 veth/netns 能力。"""
    if sys.platform != "linux":
        env_report.add(
            CheckResult(
                component="veth/netns",
                status="pending",
                detail=f"非 Linux 平台 ({sys.platform})，veth/netns 不可用",
            )
        )
        return

    ip_path = shutil.which("ip")
    if not ip_path:
        env_report.add(
            CheckResult(
                component="veth/netns",
                status="pending",
                detail="ip 命令未找到",
                suggestion="安装 iproute2 包",
            )
        )
        return

    # 尝试列出 network namespace
    try:
        result = subprocess.run(
            ["ip", "netns", "list"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            if result.stdout.strip():
                env_report.add(
                    CheckResult(
                        component="veth/netns",
                        status="passed",
                        detail=f"可用 network namespace:\n{result.stdout.strip()[:200]}",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component="veth/netns",
                        status="pending",
                        detail="无 network namespace（可手动创建用于 L2 验证）",
                        suggestion="参考 scripts/source_lab_l2_test_env.sh 创建 veth/netns 环境",
                    )
                )
        else:
            env_report.add(
                CheckResult(
                    component="veth/netns",
                    status="pending",
                    detail=f"ip netns list 失败: {result.stderr.strip()[:200]}",
                )
            )
    except subprocess.TimeoutExpired:
        env_report.add(
            CheckResult(
                component="veth/netns",
                status="pending",
                detail="ip netns list 超时",
            )
        )


def _check_tcpdump(env_report: EnvReport) -> None:
    """检查 tcpdump 可用性。"""
    tcpdump_path = shutil.which("tcpdump")
    if tcpdump_path:
        env_report.add(
            CheckResult(
                component="tcpdump",
                status="passed",
                detail=f"已安装: {tcpdump_path}",
            )
        )
    else:
        env_report.add(
            CheckResult(
                component="tcpdump",
                status="pending",
                detail="tcpdump 未安装（可选工具，用于 L2 流量分析）",
                suggestion="sudo apt-get install tcpdump 或等价命令",
            )
        )


def _check_l2_test_env_script(env_report: EnvReport) -> None:
    """检查 L2 测试环境脚本。"""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(repo_root, "scripts", "source_lab_l2_test_env.sh")
    if os.path.isfile(script_path):
        env_report.add(
            CheckResult(
                component="L2 测试环境脚本",
                status="passed",
                detail=f"存在: {script_path}（source_lab_l2_test_env.sh）",
            )
        )
    else:
        env_report.add(
            CheckResult(
                component="L2 测试环境脚本",
                status="pending",
                detail="source_lab_l2_test_env.sh 不存在",
            )
        )


def main() -> None:
    """GOOSE/SV L2 环境预检入口。"""
    parser = argparse.ArgumentParser(
        description="GOOSE/SV L2 网络环境预检 -- 只读检查，不修改系统",
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

    _check_cap_net_raw(env_report)
    _check_network_interfaces(env_report)
    _check_veth_netns(env_report)
    _check_tcpdump(env_report)
    _check_l2_test_env_script(env_report)

    # 综合状态
    env_report.add(
        CheckResult(
            component="GOOSE status",
            status="pending",
            detail="tool-ready-only -- 需受控 L2 环境（veth/netns + CAP_NET_RAW）",
        )
    )
    env_report.add(
        CheckResult(
            component="SV status",
            status="pending",
            detail="tool-ready-only -- 需受控 L2 环境（veth/netns + CAP_NET_RAW）",
        )
    )
    env_report.add(
        CheckResult(
            component="GOOSE/SV L2 安全",
            status="pending",
            detail=(
                "生产网络隔离要求: GOOSE/SV traffic 不进入 WAN；"
                "订阅端口不对外暴露；raw socket 应为 L2 只读监听；"
                "若需发送帧需额外审计论证"
            ),
        )
    )

    if args.json:
        print(json.dumps(env_report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("GOOSE/SV L2 网络环境预检报告")
        print("=" * 60)
        print(env_report.summary())
        print("=" * 60)
        print("GOOSE/SV status: tool-ready-only")
        print("需要受控 veth/netns + CAP_NET_RAW 环境。")
        print("推荐执行方式: unshare -Urn ... 或 sudo scripts/source_lab_l2_test_env.sh")
        print("=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(env_report.to_dict(), f, ensure_ascii=False, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
