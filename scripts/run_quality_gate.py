#!/usr/bin/env python3
"""
CI/本地质量门禁聚合脚本。

聚合 compileall、ruff、mypy（production+tools 和 test-typing-debt 分离）、
关键 pytest、import boundary 检查，输出 JSON summary 和 human-readable summary。

Tests mypy 历史债务单独归类为 test-typing-debt，不阻塞 production gate。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# 仓库根目录（脚本位于 scripts/ 下）
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass
class GateItem:
    """单条门禁检查结果。"""
    name: str
    description: str
    status: str  # passed / failed / skipped / debt
    detail: str
    duration_sec: float = 0.0


@dataclass
class GateReport:
    """质量门禁汇总报告。"""
    items: list[GateItem] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    debt: int = 0

    def add(self, item: GateItem) -> None:
        self.items.append(item)
        if item.status == "passed":
            self.passed += 1
        elif item.status == "failed":
            self.failed += 1
        elif item.status == "skipped":
            self.skipped += 1
        elif item.status == "debt":
            self.debt += 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.passed + self.failed + self.skipped + self.debt,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "debt": self.debt,
            "production_gate_passed": self.failed == 0,
            "items": [
                {
                    "name": i.name,
                    "description": i.description,
                    "status": i.status,
                    "detail": i.detail,
                    "duration_sec": i.duration_sec,
                }
                for i in self.items
            ],
        }


def _run_cmd(cmd: list[str], timeout: int = 300) -> tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout_tail, stderr_tail)。"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=REPO_ROOT,
        )
        stdout_tail = "\n".join(result.stdout.splitlines()[-15:]) if result.stdout else ""
        stderr_tail = "\n".join(result.stderr.splitlines()[-15:]) if result.stderr else ""
        return result.returncode, stdout_tail, stderr_tail
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except FileNotFoundError:
        return -2, "", f"command not found: {cmd[0]}"
    except Exception as e:
        return -3, "", str(e)


def _run_compileall(report: GateReport) -> None:
    """执行 compileall 检查。"""
    import time
    start = time.time()
    ret, stdout, stderr = _run_cmd(
        [sys.executable, "-m", "compileall", "-q", "src", "tools", "tests", "scripts"],
        timeout=120,
    )
    elapsed = time.time() - start

    if ret == 0:
        report.add(GateItem(
            name="compileall",
            description="全仓 Python 语法编译检查 (src+tools+tests+scripts)",
            status="passed",
            detail="全仓语法通过",
            duration_sec=elapsed,
        ))
    else:
        report.add(GateItem(
            name="compileall",
            description="全仓 Python 语法编译检查",
            status="failed",
            detail=f"语法错误:\n{stdout}\n{stderr}" if stdout or stderr else f"returncode={ret}",
            duration_sec=elapsed,
        ))


def _run_ruff(report: GateReport) -> None:
    """执行 ruff lint 检查。"""
    import time
    start = time.time()
    # 尝试多种方式运行 ruff
    cmd: list[str] = ["ruff", "check", "src", "tools", "tests", "scripts"]
    ret, stdout, stderr = _run_cmd(cmd, timeout=120)
    # 如果 ruff 命令未找到但可通过 python -m ruff 运行
    if ret == -2:
        ret, stdout, stderr = _run_cmd(
            [sys.executable, "-m", "ruff", "check", "src", "tools", "tests", "scripts"],
            timeout=120,
        )
    elapsed = time.time() - start

    if ret == 0:
        report.add(GateItem(
            name="ruff",
            description="全仓 ruff lint 检查 (src+tools+tests+scripts)",
            status="passed",
            detail="All checks passed",
            duration_sec=elapsed,
        ))
    else:
        report.add(GateItem(
            name="ruff",
            description="全仓 ruff lint 检查",
            status="failed",
            detail=f"ruff 发现错误:\n{stdout}\n{stderr}" if stdout or stderr else f"returncode={ret}",
            duration_sec=elapsed,
        ))


def _run_mypy_production(report: GateReport) -> None:
    """执行 mypy production+tools 检查。"""
    import time
    start = time.time()
    ret, stdout, stderr = _run_cmd(
        [sys.executable, "-m", "mypy", "src/whale/shared/source", "src/whale/ingest", "tools/source_lab"],
        timeout=300,
    )
    elapsed = time.time() - start

    if ret == 0:
        report.add(GateItem(
            name="mypy-production-tools",
            description="mypy production+tools 类型检查 (402 files)",
            status="passed",
            detail="Success: no issues found",
            duration_sec=elapsed,
        ))
    else:
        detail = stdout + "\n" + stderr if stdout or stderr else f"returncode={ret}"
        report.add(GateItem(
            name="mypy-production-tools",
            description="mypy production+tools 类型检查",
            status="failed",
            detail=detail,
            duration_sec=elapsed,
        ))


def _run_mypy_tests_debt(report: GateReport) -> None:
    """执行 mypy tests 检查（归类为 test-typing-debt）。"""
    import time
    start = time.time()
    ret, stdout, stderr = _run_cmd(
        [sys.executable, "-m", "mypy", "tests"],
        timeout=300,
    )
    elapsed = time.time() - start

    if ret == 0:
        report.add(GateItem(
            name="mypy-tests",
            description="mypy tests 类型检查",
            status="passed",
            detail="Success: no issues found",
            duration_sec=elapsed,
        ))
    else:
        # tests mypy 错误归类为 debt，不阻塞 production gate
        error_count = stdout.count("error:") if stdout else 0
        detail = f"mypy tests 返回 {ret}，发现约 {error_count} 个错误（历史债务，不阻塞 production gate）"
        if stdout:
            detail += f"\n首行: {stdout.splitlines()[0] if stdout.splitlines() else ''}"
        report.add(GateItem(
            name="mypy-tests",
            description="mypy tests 类型检查（test-typing-debt -- 不阻塞 production gate）",
            status="debt",
            detail=detail,
            duration_sec=elapsed,
        ))


def _run_import_boundary(report: GateReport) -> None:
    """执行 import boundary 检查：生产路径不得导入 tools.source_lab。"""
    import time
    start = time.time()

    # 使用 grep 检查
    try:
        result = subprocess.run(
            [
                "grep", "-rn", "--include=*.py",
                "tools.source_lab",
                os.path.join(REPO_ROOT, "src", "whale", "ingest"),
                os.path.join(REPO_ROOT, "src", "whale", "shared", "source"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        elapsed = time.time() - start

        if result.returncode == 1:  # grep 无匹配
            report.add(GateItem(
                name="import-boundary",
                description="生产路径 import boundary: 零 tools.source_lab 导入",
                status="passed",
                detail="src/whale/ingest 和 src/whale/shared/source 无 tools.source_lab 导入",
                duration_sec=elapsed,
            ))
        elif result.returncode == 0:  # grep 有匹配
            report.add(GateItem(
                name="import-boundary",
                description="生产路径 import boundary",
                status="failed",
                detail=f"发现 tools.source_lab 导入:\n{result.stdout[:500]}",
                duration_sec=elapsed,
            ))
        else:
            report.add(GateItem(
                name="import-boundary",
                description="生产路径 import boundary",
                status="failed",
                detail=f"grep 异常: {result.stderr[:200]}",
                duration_sec=elapsed,
            ))
    except Exception as e:
        elapsed = time.time() - start
        report.add(GateItem(
            name="import-boundary",
            description="生产路径 import boundary",
            status="failed",
            detail=str(e),
            duration_sec=elapsed,
        ))


def _run_core_pytest(report: GateReport) -> None:
    """执行关键 pytest 检查。"""
    import time
    start = time.time()

    test_files = [
        "tools/source_lab/tests/access/test_protocol_production_readiness_gate.py",
        "tools/source_lab/tests/access/test_source_lab_final_protocol_matrix.py",
        "tests/unit/test_source_acquisition_port_registry.py",
        "tests/unit/test_source_write_port_registry.py",
        "tests/unit/test_ingest_composition_injection.py",
    ]

    all_passed = True
    total_passed = 0
    total_failed = 0
    detail_lines = []

    for tf in test_files:
        tf_path = os.path.join(REPO_ROOT, tf)
        if not os.path.isfile(tf_path):
            detail_lines.append(f"  [skipped] {tf}: 文件不存在")
            continue

        ret, stdout, stderr = _run_cmd(
            [sys.executable, "-m", "pytest", tf_path, "-q"],
            timeout=120,
        )

        if ret == 0:
            total_passed += 1
            detail_lines.append(f"  [passed] {tf}: ok")
        else:
            total_failed += 1
            all_passed = False
            tail = (stdout + stderr)[:200]
            detail_lines.append(f"  [failed] {tf}: {tail}")

    elapsed = time.time() - start

    detail = "\n".join(detail_lines)
    if all_passed:
        report.add(GateItem(
            name="core-pytest",
            description=f"关键 pytest 检查 ({len(test_files)} files, {total_passed} passed)",
            status="passed",
            detail=detail,
            duration_sec=elapsed,
        ))
    else:
        report.add(GateItem(
            name="core-pytest",
            description="关键 pytest 检查",
            status="failed",
            detail=detail,
            duration_sec=elapsed,
        ))


def main() -> None:
    """质量门禁聚合入口。"""
    parser = argparse.ArgumentParser(
        description="Whale CI/本地质量门禁聚合 -- compileall/ruff/mypy/pytest/import boundary",
    )
    parser.add_argument(
        "--summary-json",
        type=str,
        default="",
        help="输出 JSON 格式汇总报告到文件",
    )
    parser.add_argument(
        "--full-pytest",
        action="store_true",
        help="运行全量 pytest（默认仅运行关键检查）",
    )
    parser.add_argument(
        "--skip-mypy-tests",
        action="store_true",
        help="跳过 mypy tests（默认会检查但归类为 debt）",
    )
    args = parser.parse_args()

    report = GateReport()

    print("=" * 70)
    print("Whale Quality Gate Runner")
    print("=" * 70)

    # Gate 1: compileall
    print("\n[1/6] compileall ...")
    _run_compileall(report)

    # Gate 2: ruff
    print("[2/6] ruff ...")
    _run_ruff(report)

    # Gate 3: mypy production+tools
    print("[3/6] mypy production+tools ...")
    _run_mypy_production(report)

    # Gate 4: mypy tests (debt)
    if not args.skip_mypy_tests:
        print("[4/6] mypy tests (归类为 test-typing-debt) ...")
        _run_mypy_tests_debt(report)
    else:
        report.add(GateItem(
            name="mypy-tests",
            description="mypy tests (--skip-mypy-tests)",
            status="skipped",
            detail="使用 --skip-mypy-tests 跳过",
        ))

    # Gate 5: import boundary
    print("[5/6] import boundary ...")
    _run_import_boundary(report)

    # Gate 6: core pytest
    print("[6/6] core pytest ...")
    _run_core_pytest(report)

    # --------
    # 输出汇总
    # --------
    print("\n" + "=" * 70)
    print("Quality Gate Summary")
    print("=" * 70)

    for item in report.items:
        icon = {
            "passed": "[PASS]",
            "failed": "[FAIL]",
            "skipped": "[SKIP]",
            "debt": "[DEBT]",
        }.get(item.status, "[???]")
        print(f"  {icon} {item.name} ({item.duration_sec:.1f}s)")
        if item.status in ("failed", "debt"):
            # 截断输出保持可读
            detail_short = item.detail[:300].replace("\n", "\n    ")
            print(f"    {detail_short}")

    print("-" * 70)
    print(f"  production gate: {'PASSED' if report.failed == 0 else 'FAILED'}")
    print(f"  test-typing-debt: {report.debt} 项（不阻塞 production gate）")
    print(f"  passed: {report.passed}, failed: {report.failed}, skipped: {report.skipped}, debt: {report.debt}")

    if report.failed > 0:
        print(f"\n  警告: production gate 未通过！存在 {report.failed} 个失败项。")
    else:
        print("\n  production gate 通过（test-typing-debt 不计入阻塞）。")

    print("=" * 70)

    # JSON 输出
    if args.summary_json:
        summary = report.to_dict()
        with open(args.summary_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nJSON 汇总已输出到: {args.summary_json}")

    sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
