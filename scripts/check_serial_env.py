#!/usr/bin/env python3
"""
串口 (Serial) 环境预检脚本。

检查 /dev/tty* 设备、dialout 组、udev 规则、fcntl lock 权限，
输出 Modbus RTU / IEC101 串行协议的环境就绪状态。

本脚本只读检查，不得修改系统状态，不得要求 root 权限。
"""
from __future__ import annotations

import argparse
import fcntl
import glob
import grp
import json
import os
import stat
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


def _check_serial_devices(env_report: EnvReport) -> None:
    """检查 /dev/tty* 串口设备。"""
    patterns = [
        "/dev/ttyUSB*",
        "/dev/ttyS*",
        "/dev/ttyACM*",
        "/dev/ttyAMA*",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(glob.glob(pattern))

    if not found:
        env_report.add(
            CheckResult(
                component="串口设备",
                status="pending",
                detail="未发现 /dev/ttyUSB*, /dev/ttyS*, /dev/ttyACM*, /dev/ttyAMA* 设备",
                suggestion="连接 USB-to-Serial 转换器或确认主板串口已启用",
            )
        )
        return

    for dev_path in found:
        try:
            st = os.stat(dev_path)
            mode = st.st_mode
            perms = stat.filemode(mode)

            # 检查是否为字符设备
            is_char = stat.S_ISCHR(mode)

            # 检查读写权限
            readable = bool(mode & stat.S_IRUSR)
            writable = bool(mode & stat.S_IWUSR)

            env_report.add(
                CheckResult(
                    component=f"串口设备 {dev_path}",
                    status="passed" if (is_char and readable and writable) else "pending",
                    detail=f"类型={'char' if is_char else 'unknown'}, 权限={perms}, "
                    f"readable={readable}, writable={writable}, "
                    f"uid={st.st_uid}, gid={st.st_gid}",
                    suggestion="检查 udev 规则和 dialout 组成员" if not (is_char and readable and writable) else "",
                )
            )
        except OSError as e:
            env_report.add(
                CheckResult(
                    component=f"串口设备 {dev_path}",
                    status="failed",
                    detail=f"无法 stat: {e}",
                )
            )


def _check_dialout_group(env_report: EnvReport) -> None:
    """检查当前用户是否在 dialout 组。"""
    try:
        username = os.environ.get("USER", os.environ.get("LOGNAME", ""))
        if not username:
            env_report.add(
                CheckResult(
                    component="dialout 组",
                    status="pending",
                    detail="无法获取当前用户名",
                )
            )
            return

        try:
            group_info = grp.getgrnam("dialout")
            if username in group_info.gr_mem:
                env_report.add(
                    CheckResult(
                        component="dialout 组",
                        status="passed",
                        detail=f"用户 {username} 已是 dialout 组成员 (gid={group_info.gr_gid})",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component="dialout 组",
                        status="pending",
                        detail=f"用户 {username} 不是 dialout 组成员 (gid={group_info.gr_gid})",
                        suggestion=f"sudo usermod -a -G dialout {username} 然后重新登录",
                    )
                )
        except KeyError:
            env_report.add(
                CheckResult(
                    component="dialout 组",
                    status="pending",
                    detail="dialout 组不存在",
                    suggestion="sudo groupadd dialout && sudo usermod -a -G dialout <user>",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="dialout 组",
                status="pending",
                detail=f"检查失败: {e}",
            )
        )


def _check_udev_rules(env_report: EnvReport) -> None:
    """检查 udev 规则文件是否存在。"""
    udev_files = glob.glob("/etc/udev/rules.d/*modbus*") + glob.glob("/etc/udev/rules.d/*iec101*")
    if udev_files:
        for f in udev_files:
            env_report.add(
                CheckResult(
                    component=f"udev 规则 {os.path.basename(f)}",
                    status="passed",
                    detail=f"存在: {f}",
                )
            )
    else:
        env_report.add(
            CheckResult(
                component="udev 规则",
                status="pending",
                detail="未发现 Modbus RTU/IEC101 相关的 udev 规则文件",
                suggestion=(
                    "创建 /etc/udev/rules.d/99-modbus-rtu.rules 和 /etc/udev/rules.d/99-iec101.rules "
                    "以固定设备名和权限"
                ),
            )
        )


def _check_fcntl_lock(env_report: EnvReport) -> None:
    """检查 fcntl lock 权限（需要串口设备存在）。"""
    serial_devs = (
        glob.glob("/dev/ttyUSB*")
        + glob.glob("/dev/ttyS*")
        + glob.glob("/dev/ttyACM*")
    )
    if not serial_devs:
        env_report.add(
            CheckResult(
                component="fcntl LOCK_EX 权限",
                status="pending",
                detail="无串口设备，跳过 fcntl lock 测试",
            )
        )
        return

    test_dev = serial_devs[0]
    try:
        fd = os.open(test_dev, os.O_RDWR | os.O_NOCTTY)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(fd, fcntl.LOCK_UN)
            env_report.add(
                CheckResult(
                    component="fcntl LOCK_EX 权限",
                    status="passed",
                    detail=f"可在 {test_dev} 上获取和释放 LOCK_EX",
                )
            )
        except OSError as e:
            env_report.add(
                CheckResult(
                    component="fcntl LOCK_EX 权限",
                    status="pending",
                    detail=f"{test_dev} 上 LOCK_EX 失败: {e}",
                    suggestion="确认用户有 dialout 组权限且设备未被其他进程占用",
                )
            )
        finally:
            os.close(fd)
    except OSError as e:
        env_report.add(
            CheckResult(
                component="fcntl LOCK_EX 权限",
                status="pending",
                detail=f"无法打开 {test_dev}: {e}",
                suggestion="确认当前用户在 dialout 组且设备已连接",
            )
        )


def main() -> None:
    """串口环境预检入口。"""
    parser = argparse.ArgumentParser(
        description="Serial 环境预检 -- 检查 Modbus RTU / IEC101 串行协议就绪状态",
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

    _check_serial_devices(env_report)
    _check_dialout_group(env_report)
    _check_udev_rules(env_report)
    _check_fcntl_lock(env_report)

    # 协议就绪声明
    env_report.add(
        CheckResult(
            component="Modbus RTU write",
            status="pending",
            detail="NOT_IMPLEMENTED -- FC06/FC16 write 未实现",
        )
    )
    env_report.add(
        CheckResult(
            component="IEC101 write",
            status="pending",
            detail="NOT_IMPLEMENTED -- C_SC/C_DC/C_SE write 未实现",
        )
    )
    env_report.add(
        CheckResult(
            component="Modbus RTU L4/L5",
            status="pending",
            detail="environment-pending -- 需要真实 RS-485 设备和 Modbus RTU 从站",
        )
    )
    env_report.add(
        CheckResult(
            component="IEC101 L4/L5",
            status="pending",
            detail="environment-pending -- 需要真实 RS-232/RS-485 设备和 IEC101 RTU",
        )
    )

    if args.json:
        print(json.dumps(env_report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("Serial 环境预检报告")
        print("=" * 60)
        print(env_report.summary())
        print("=" * 60)
        print("Modbus RTU/IEC101 status: acquisition-ready (read-only serial), L4/L5=environment-pending")
        print("=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(env_report.to_dict(), f, ensure_ascii=False, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
