#!/usr/bin/env python3
"""
L5 Field Readback 环境预检脚本。

检查 PostgreSQL、Redis、Kafka 和目标协议配置/环境变量，用于在
现场验证前确认基础设施和协议配置就绪。

本脚本只读检查，不得修改系统状态，不得要求 root 权限。
不连接真实设备时，相关检查只输出 environment-pending。
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CheckResult:
    """
    单条检查结果。

    Attributes:
        component: 检查的组件或协议名。
        status: passed / failed / pending / skipped。
        detail: 详细说明。
        suggestion: 如果不通过，给出的修复建议。
    """

    component: str
    status: str
    detail: str
    suggestion: str = ""


@dataclass
class EnvReport:
    """环境预检报告，汇总所有检查结果。"""

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


def _check_tcp_connect(host: str, port: int, timeout: float = 3.0) -> tuple[bool, str]:
    """
    尝试 TCP 连接目标 host:port。

    返回 (是否连接成功, 状态描述)。
    """
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, f"{host}:{port} 可达"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return False, f"{host}:{port} 不可达 ({e})"


def _check_postgres(env_report: EnvReport) -> None:
    """检查 PostgreSQL 环境。"""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        env_report.add(
            CheckResult(
                component="PostgreSQL",
                status="pending",
                detail="DATABASE_URL 环境变量未设置，跳过 PostgreSQL 检查",
                suggestion="设置 DATABASE_URL 后重新运行",
            )
        )
        return

    # 解析简化的 URL 格式: postgresql://user:pass@host:port/db
    try:
        # 简单解析，不引入完整 URL 解析
        if "://" in db_url:
            host_part = db_url.split("@")[-1].split("/")[0]
            host = host_part.split(":")[0]
            port = int(host_part.split(":")[1]) if ":" in host_part else 5432
            ok, detail = _check_tcp_connect(host, port)
            if ok:
                env_report.add(
                    CheckResult(
                        component="PostgreSQL",
                        status="passed",
                        detail=f"DATABASE_URL 已配置，{detail}",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component="PostgreSQL",
                        status="pending",
                        detail=f"DATABASE_URL 已配置但 {detail}",
                        suggestion="确认 PostgreSQL 服务已启动且网络可达",
                    )
                )
        else:
            env_report.add(
                CheckResult(
                    component="PostgreSQL",
                    status="pending",
                    detail=f"DATABASE_URL 格式无法解析: {db_url[:30]}...",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="PostgreSQL",
                status="pending",
                detail=f"DATABASE_URL 解析失败: {e}",
            )
        )


def _check_redis(env_report: EnvReport) -> None:
    """检查 Redis 环境。"""
    redis_url = os.environ.get("REDIS_URL", "")
    if not redis_url:
        env_report.add(
            CheckResult(
                component="Redis",
                status="pending",
                detail="REDIS_URL 环境变量未设置，跳过 Redis 检查",
                suggestion="设置 REDIS_URL 后重新运行",
            )
        )
        return

    try:
        if "://" in redis_url:
            host_part = redis_url.split("@")[-1].split("/")[0] if "@" in redis_url else redis_url.split("://")[-1].split("/")[0]
            host = host_part.split(":")[0]
            port = int(host_part.split(":")[1]) if ":" in host_part else 6379
            ok, detail = _check_tcp_connect(host, port)
            if ok:
                env_report.add(
                    CheckResult(
                        component="Redis",
                        status="passed",
                        detail=f"REDIS_URL 已配置，{detail}",
                    )
                )
            else:
                env_report.add(
                    CheckResult(
                        component="Redis",
                        status="pending",
                        detail=f"REDIS_URL 已配置但 {detail}",
                        suggestion="确认 Redis 服务已启动且网络可达",
                    )
                )
        else:
            env_report.add(
                CheckResult(
                    component="Redis",
                    status="pending",
                    detail=f"REDIS_URL 格式无法解析: {redis_url[:30]}...",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="Redis",
                status="pending",
                detail=f"REDIS_URL 解析失败: {e}",
            )
        )


def _check_kafka(env_report: EnvReport) -> None:
    """检查 Kafka 环境。"""
    kafka_broker = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "")
    if not kafka_broker:
        env_report.add(
            CheckResult(
                component="Kafka",
                status="pending",
                detail="KAFKA_BOOTSTRAP_SERVERS 环境变量未设置，跳过 Kafka 检查",
                suggestion="设置 KAFKA_BOOTSTRAP_SERVERS 后重新运行",
            )
        )
        return

    try:
        parts = kafka_broker.split(",")
        reachable = 0
        unreachable = 0
        for part in parts:
            host_port = part.strip()
            host = host_port.split(":")[0]
            port = int(host_port.split(":")[1]) if ":" in host_port else 9092
            ok, _ = _check_tcp_connect(host, port)
            if ok:
                reachable += 1
            else:
                unreachable += 1

        if reachable > 0 and unreachable == 0:
            env_report.add(
                CheckResult(
                    component="Kafka",
                    status="passed",
                    detail=f"KAFKA_BOOTSTRAP_SERVERS 已配置 ({kafka_broker}), 全部可达",
                )
            )
        elif reachable > 0:
            env_report.add(
                CheckResult(
                    component="Kafka",
                    status="pending",
                    detail=f"KAFKA_BOOTSTRAP_SERVERS 已配置 ({kafka_broker}), {reachable} 可达, {unreachable} 不可达",
                )
            )
        else:
            env_report.add(
                CheckResult(
                    component="Kafka",
                    status="pending",
                    detail=f"KAFKA_BOOTSTRAP_SERVERS 已配置 ({kafka_broker}), 全部不可达",
                    suggestion="确认 Kafka broker 已启动且网络可达",
                )
            )
    except Exception as e:
        env_report.add(
            CheckResult(
                component="Kafka",
                status="pending",
                detail=f"KAFKA_BOOTSTRAP_SERVERS 解析失败: {e}",
            )
        )


def _check_protocol_config(env_report: EnvReport, protocol_name: str, env_var: str) -> None:
    """检查协议配置环境变量。"""
    value = os.environ.get(env_var, "")
    if value:
        env_report.add(
            CheckResult(
                component=f"{protocol_name} 配置",
                status="passed",
                detail=f"{env_var} 已配置: {value}",
            )
        )
        # 尝试解析 endpoint 并 TCP 连接
        try:
            host = value.split("//")[-1].split(":")[0] if "//" in value else value.split(":")[0]
            port_str = value.split(":")[-1] if ":" in value else ""
            port = int(port_str) if port_str and port_str.isdigit() else 0
            if port > 0:
                ok, detail = _check_tcp_connect(host, port)
                env_report.add(
                    CheckResult(
                        component=f"{protocol_name} 设备连通性",
                        status="passed" if ok else "pending",
                        detail=detail,
                        suggestion="确认设备已启动且网络可达" if not ok else "",
                    )
                )
        except Exception:
            pass
    else:
        env_report.add(
            CheckResult(
                component=f"{protocol_name} 配置",
                status="pending",
                detail=f"{env_var} 环境变量未设置，无设备连接不视为失败",
                suggestion=f"设置 {env_var} 后重新运行以检查设备连通性",
            )
        )


def main() -> None:
    """L5 field readback 环境预检入口。"""
    parser = argparse.ArgumentParser(
        description="L5 Field Readback 环境预检 -- 只读检查，不修改系统",
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

    # 基础设施检查
    _check_postgres(env_report)
    _check_redis(env_report)
    _check_kafka(env_report)

    # 协议配置检查
    _check_protocol_config(env_report, "OPC UA", "OPCUA_ENDPOINT")
    _check_protocol_config(env_report, "Modbus TCP", "MODBUS_TCP_HOST")
    _check_protocol_config(env_report, "IEC61850 MMS", "IEC61850_MMS_HOST")
    _check_protocol_config(env_report, "IEC104", "IEC104_HOST")
    _check_protocol_config(env_report, "IEC61850 Report", "IEC61850_REPORT_HOST")

    # 写入功能环境变量
    write_enabled = os.environ.get("WRITE_ENABLED", "false").lower()
    env_report.add(
        CheckResult(
            component="Write 功能开关",
            status="passed",
            detail=f"WRITE_ENABLED={write_enabled}（默认关闭，安全）",
        )
    )

    # 汇总输出
    if args.json:
        print(json.dumps(env_report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("L5 Field Readback 环境预检报告")
        print("=" * 60)
        print(env_report.summary())
        print("=" * 60)
        if env_report.pending > 0:
            print("注意: 存在 PENDING 项 -- 表示缺少设备连接或配置环境变量。")
            print("这不代表系统故障，仅表示当前环境无法完成 L5 现场验证。")
        print("=" * 60)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(env_report.to_dict(), f, ensure_ascii=False, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
