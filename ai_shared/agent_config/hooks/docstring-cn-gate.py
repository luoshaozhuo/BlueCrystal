#!/usr/bin/env python3
"""轻量检查 public Python 接口 docstring 与 type ignore 风险。"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def changed_python_files() -> list[Path]:
    """返回当前工作区内发生变化的 Python 文件。"""
    names: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "--", "*.py"],
        ["git", "diff", "--cached", "--name-only", "--", "*.py"],
    ):
        try:
            out = subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)
        except Exception:
            continue
        names.update(line.strip() for line in out.splitlines() if line.strip())
    return [Path(name) for name in sorted(names) if Path(name).exists()]


def main() -> int:
    """执行轻量 docstring 检查。"""
    failures: list[str] = []
    warnings: list[str] = []

    for path in changed_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append(f"{path}: 无法解析 Python AST: {exc}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name.startswith("_") or node.name.startswith("test_"):
                    continue
                doc = ast.get_docstring(node)
                arg_count = len(getattr(getattr(node, "args", None), "args", []))
                if isinstance(node, ast.ClassDef) or arg_count >= 2:
                    if not doc:
                        warnings.append(f"{path}:{node.lineno} public `{node.name}` 缺少 docstring。")

        text = path.read_text(encoding="utf-8", errors="ignore")
        if "type: ignore" in text and "type: ignore[" not in text and "原因" not in text and "reason" not in text.lower():
            failures.append(f"{path}: 存在无说明 type: ignore。")

    if warnings:
        print("Docstring gate warnings:", file=sys.stderr)
        for item in warnings:
            print(f"- {item}", file=sys.stderr)

    if failures:
        print("Docstring gate failures:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
